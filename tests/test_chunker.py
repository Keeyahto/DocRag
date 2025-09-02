from kits.kit_chunker import split_text, split_markdown


def test_split_text_respects_max_tokens_and_overlap():
    text = " ".join([f"tok{i}" for i in range(50)])
    chunks = split_text(text, max_tokens=10, overlap=2)
    assert len(chunks) >= 5
    # No empty chunks and each chunk length <= 10 tokens
    for c in chunks:
        assert c
        assert len(c.split()) <= 10
    # Overlap means step = 8, so the second chunk should start with last 2 tokens of first chunk
    first = chunks[0].split()
    second = chunks[1].split()
    assert first[-2:] == second[:2]


def test_split_markdown_prefers_headings_then_tokens():
    md = """# Title\npara words here\n\n## Section\nmore words in section repeated words words"""
    chunks = split_markdown(md, max_tokens=5, overlap=1)
    assert chunks, "no chunks returned"
    # Ensure heading marker remains on a chunk
    assert any(c.lstrip().startswith("# ") for c in chunks)
