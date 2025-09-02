from kits.kit_common import normalize_text, gen_request_id


def test_normalize_text_compacts_whitespace_and_strips():
    s = "  hello\u00a0world\n\n  test\t\t"
    out = normalize_text(s)
    assert out == "hello world test"


def test_gen_request_id_unique_and_hex():
    a = gen_request_id()
    b = gen_request_id()
    assert a != b
    assert len(a) == 32 and all(c in "0123456789abcdef" for c in a)
