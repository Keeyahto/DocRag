from kits.kit_common.highlight import extract_snippet_and_highlights


def test_extract_snippet_and_highlights_offsets_within_snippet():
    text = "Lorem ipsum dolor sit amet, consectetur adipiscing elit. Sed do eiusmod tempor incididunt ut labore et dolore magna aliqua."
    query = "eiusmod tempor"
    snippet, highlights = extract_snippet_and_highlights(text, query, window=20)
    assert snippet
    # highlights within snippet bounds
    for s, e in highlights:
        assert 0 <= s < e <= len(snippet)
    # Expect at least one highlight for 'tempor'
    assert any(snippet[s:e].lower() == "tempor" for s, e in highlights)
