# Fetches a real, public, comms-shaped corpus: Cloudflare's own developer docs
# (product reference pages) plus its own blog announcement posts, standing in for
# an internal company wiki and its announcement channel. Both hosts' robots.txt
# publish an explicit Content-Signal directive (ai-input=yes, search=yes) as of
# the fetch date below, so this use is within what the site operator has stated
# it permits; see README Honest framing for the exact lines quoted.
#
# This script writes only data/raw/*.txt (gitignored, regenerable) and
# corpus_manifest.json (committed: url, title, sha256, fetched_at). The
# extracted text itself is not committed, the same precedent the base repo
# uses for the copyrighted CXL/PCI-SIG spec PDFs, even though this content's
# own Content-Signal is more permissive.
from __future__ import annotations

import concurrent.futures as cf
import hashlib
import json
import re
import time
import urllib.request
import xml.etree.ElementTree as ET
from dataclasses import asdict, dataclass
from pathlib import Path

from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = ROOT / "data" / "raw"
MANIFEST_PATH = ROOT / "corpus_manifest.json"

USER_AGENT = "Mozilla/5.0 (compatible; job-application-portfolio-research/1.0; +https://github.com/Manas103)"
FETCH_DATE = "2026-11-20"

DOCS_SITEMAP = "https://developers.cloudflare.com/sitemap-0.xml"
BLOG_SITEMAP = "https://blog.cloudflare.com/sitemap-posts.xml"

DOCS_PREFIXES = (
    "https://developers.cloudflare.com/workers-ai/",
    "https://developers.cloudflare.com/vectorize/",
    "https://developers.cloudflare.com/workers/",
    "https://developers.cloudflare.com/ai-search/",
    "https://developers.cloudflare.com/autorag/",
    "https://developers.cloudflare.com/r2/",
    "https://developers.cloudflare.com/pages/",
    "https://developers.cloudflare.com/d1/",
)
DOCS_TARGET = 150
BLOG_TARGET = 250


def _get(url: str, timeout: int = 20) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.read()


def _sitemap_urls(sitemap_url: str) -> list[str]:
    xml_bytes = _get(sitemap_url)
    root = ET.fromstring(xml_bytes)
    ns = {"sm": "http://www.sitemaps.org/schemas/sitemap/0.9"}
    return [loc.text.strip() for loc in root.findall(".//sm:loc", ns) if loc.text]


def _pick_docs_urls() -> list[str]:
    all_urls = _sitemap_urls(DOCS_SITEMAP)
    matched = [u for u in all_urls if any(u.startswith(p) for p in DOCS_PREFIXES)]
    # Deterministic selection: stride through the matched list rather than
    # take a prefix, so the sample isn't biased toward one product's
    # alphabetically-first subpages.
    if len(matched) <= DOCS_TARGET:
        return matched
    stride = len(matched) / DOCS_TARGET
    return [matched[int(i * stride)] for i in range(DOCS_TARGET)]


def _pick_blog_urls() -> list[str]:
    urls = _sitemap_urls(BLOG_SITEMAP)
    # sitemap-posts.xml is in reverse-chronological order already (most
    # recent first); taking the front of the list gives the most recent
    # announcement posts, which is the comms-relevant slice.
    return urls[:BLOG_TARGET]


_STRIP_TAGS = ("script", "style", "nav", "header", "footer", "aside", "noscript", "svg", "form")


def extract_main_text(html: bytes) -> tuple[str, str]:
    soup = BeautifulSoup(html, "lxml")
    title_tag = soup.find("title")
    title = title_tag.get_text(strip=True) if title_tag else ""
    for tag_name in _STRIP_TAGS:
        for tag in soup.find_all(tag_name):
            tag.decompose()
    main = soup.find("main") or soup.find("article") or soup.body or soup
    text = main.get_text(separator=" ", strip=True) if main else ""
    text = re.sub(r"\s+", " ", text).strip()
    return title, text


@dataclass(frozen=True)
class PageRecord:
    page_id: str
    url: str
    title: str
    source_type: str  # "docs" or "blog"
    sha256: str
    word_count: int
    fetched_at: str


def _page_id_for(url: str) -> str:
    # Full path, not just the last segment: developers.cloudflare.com reuses leaf
    # names ("binding", "examples", "rest-api") across unrelated product trees.
    host = "docs" if "developers.cloudflare.com" in url else "blog"
    path = re.sub(r"^https?://[^/]+/", "", url).rstrip("/")
    slug = re.sub(r"[^a-z0-9]+", "-", path.lower()).strip("-") or "index"
    if len(slug) > 90:
        slug = slug[:70] + "-" + hashlib.sha1(slug.encode()).hexdigest()[:8]
    return f"{host}-{slug}"


def fetch_one(url: str, source_type: str) -> PageRecord | None:
    try:
        html = _get(url)
    except Exception:
        return None
    title, text = extract_main_text(html)
    if len(text.split()) < 80:
        return None  # too thin to be a real audit page (stub/redirect/empty)
    page_id = _page_id_for(url)
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    (RAW_DIR / f"{page_id}.txt").write_text(text, encoding="utf-8")
    return PageRecord(
        page_id=page_id,
        url=url,
        title=title,
        source_type=source_type,
        sha256=hashlib.sha256(text.encode("utf-8")).hexdigest(),
        word_count=len(text.split()),
        fetched_at=FETCH_DATE,
    )


def main() -> None:
    docs_urls = _pick_docs_urls()
    blog_urls = _pick_blog_urls()
    print(f"candidate docs URLs: {len(docs_urls)}, candidate blog URLs: {len(blog_urls)}")

    jobs = [(u, "docs") for u in docs_urls] + [(u, "blog") for u in blog_urls]
    records: list[PageRecord] = []
    with cf.ThreadPoolExecutor(max_workers=8) as pool:
        futures = {pool.submit(fetch_one, url, kind): url for url, kind in jobs}
        for fut in cf.as_completed(futures):
            rec = fut.result()
            if rec is not None:
                records.append(rec)

    records.sort(key=lambda r: r.page_id)
    manifest = {
        "fetch_date": FETCH_DATE,
        "docs_candidates": len(docs_urls),
        "blog_candidates": len(blog_urls),
        "pages_fetched": len(records),
        "pages": [asdict(r) for r in records],
    }
    MANIFEST_PATH.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(f"fetched {len(records)} real pages (target 400); manifest written to {MANIFEST_PATH}")


if __name__ == "__main__":
    main()
