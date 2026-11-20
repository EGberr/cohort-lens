from app.retrieval.bm25 import tokenize


def test_tokenize_stems_and_splits_compounds():
    toks = tokenize("Plant-based snacks and the trends")
    assert "plant" in toks and "snack" in toks and "trend" in toks and "the" not in toks


def test_every_mode_finds_the_obvious_document(retriever):
    for mode in retriever.available_modes():
        hits = retriever.search("pre-loved clothing resale apps", k=5, mode=mode)
        assert any(h.chunk.doc_id == "cat-secondhand-fashion" for h in hits), mode


def test_category_filter_is_respected(retriever):
    hits = retriever.search("purchase drivers", k=8, categories=["sneakers"])
    assert hits
    assert all("sneakers" in h.chunk.categories or h.chunk.doc_type == "thematic_report" for h in hits)


def test_chunks_carry_context(retriever):
    c = retriever.chunk_by_id["cat-skincare#path-to-purchase"]
    assert c.contextual_text.startswith("Skincare: Gen Z Category Report 2026")
