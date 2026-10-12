from assistant.ingest import Passage, _clean_wikitext, _extract_wiki_pages


def test_clean_wikitext_strips_templates_links_and_refs():
    raw = "{{Infobox|name=X}} PCIe is a '''bus standard''' [[Peripheral Component Interconnect|PCI]] <ref>cite</ref> link."
    cleaned = _clean_wikitext(raw)
    assert "{{" not in cleaned
    assert "<ref" not in cleaned
    assert "'''" not in cleaned
    assert "PCI" in cleaned
    assert "bus standard" in cleaned


def test_clean_wikitext_strips_tables_and_comments():
    raw = "Intro text. {| class=wikitable\n|-\n| a || b\n|}\n<!-- a comment -->More text."
    cleaned = _clean_wikitext(raw)
    assert "wikitable" not in cleaned
    assert "a comment" not in cleaned
    assert "Intro text." in cleaned
    assert "More text." in cleaned


def test_extract_wiki_pages_chunks_into_fixed_word_count_pages(tmp_path):
    words = " ".join(f"word{i}" for i in range(1000))
    p = tmp_path / "doc.wikitext"
    p.write_text(words, encoding="utf-8")
    passages = _extract_wiki_pages(p, "Test Doc", "test-doc")
    assert len(passages) == 3  # 1000 words / 450-word pages -> pages of 450, 450, 100
    assert all(isinstance(pg, Passage) for pg in passages)
    assert [pg.page_number for pg in passages] == [1, 2, 3]
