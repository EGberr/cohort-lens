from pathlib import Path

from app import ingest
from app.retrieval.chunking import chunk_document, parse_document


def test_add_markdown_creates_external_document(tmp_path, monkeypatch):
    monkeypatch.setattr(ingest.settings, "data_dir", tmp_path)
    src = tmp_path / "lip-oil-note.md"
    src.write_text("# Retail note\n\n## Lip oil trend\n\nLip oils are replacing glosses among teenagers.\n")
    (out,) = ingest.add([src], ["color-cosmetics"], "Lip oil note")
    doc = parse_document(out, tmp_path / "corpus")
    assert doc.doc_type == "external" and doc.categories == ["color-cosmetics"]
    chunks = chunk_document(doc)
    assert chunks[0].section == "Lip oil trend"
    assert "Lip oils" in chunks[0].text


def test_html_to_markdown_strips_scripts():
    md = ingest.html_to_markdown("<script>x()</script><h2>Title</h2><p>Hello <b>world</b></p>")
    assert "x()" not in md and "## Title" in md and "Hello" in md


def test_unknown_category_exits(tmp_path):
    import pytest

    with pytest.raises(SystemExit):
        ingest.add([Path("x.md")], ["nope"], None)
