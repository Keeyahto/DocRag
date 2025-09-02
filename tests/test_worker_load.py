from pathlib import Path

import pytest

pytest.importorskip("langchain_community")
from apps.worker.worker import _load_documents, _chunk_documents


def test_worker_loads_and_normalizes_txt(tmp_path):
    p = tmp_path / "sample.txt"
    p.write_text("Hello   world\nNew\tline", encoding="utf-8")
    docs = _load_documents(p)
    assert docs and docs[0].page_content == "Hello world New line"


def test_chunk_documents_not_empty(tmp_path):
    p = tmp_path / "a.txt"
    p.write_text("word " * 100, encoding="utf-8")
    docs = _load_documents(p)
    chunks = _chunk_documents(docs, max_tokens=20, overlap=5)
    assert chunks and all(isinstance(t, tuple) and t[0] for t in chunks)
