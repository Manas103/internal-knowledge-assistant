# Downloads the real public CSA CCM+CAIQ v4.1 bundle named in caiq/manifest.json into
# caiq/data/raw/ (gitignored) and verifies its sha256 against the manifest before anything
# downstream trusts it, the same contract scripts/fetch_corpus.py uses for the PCIe/CXL
# sources above. No account or login is required for this URL (see manifest.json).
from __future__ import annotations

import hashlib
import json
import urllib.request
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent
MANIFEST_PATH = ROOT / "manifest.json"
RAW_DIR = ROOT / "data" / "raw"


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def fetch_bundle(manifest_path: Path = MANIFEST_PATH, raw_dir: Path = RAW_DIR) -> Path:
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    source = manifest["source"]
    raw_dir.mkdir(parents=True, exist_ok=True)
    bundle_path = raw_dir / "ccm_caiq_v4_1_bundle.zip"

    if not bundle_path.exists():
        # Cloudflare (fronting cloudsecurityalliance.org) 403s urllib's default
        # "Python-urllib/x.y" user agent; a plain browser-style one is accepted, and no
        # cookies, account or login are needed beyond that (confirmed manually).
        request = urllib.request.Request(source["url"], headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(request) as response, bundle_path.open("wb") as out:
            out.write(response.read())

    actual_sha256 = _sha256(bundle_path)
    expected_sha256 = source["bundle_sha256"]
    if actual_sha256 != expected_sha256:
        raise ValueError(
            f"downloaded bundle sha256 {actual_sha256} does not match manifest's {expected_sha256}; "
            "refusing to trust it"
        )

    extract_dir = raw_dir / "extracted"
    if not extract_dir.exists():
        with zipfile.ZipFile(bundle_path) as z:
            z.extractall(extract_dir)
    return extract_dir


if __name__ == "__main__":
    out = fetch_bundle()
    print(f"bundle verified and extracted to {out}")
