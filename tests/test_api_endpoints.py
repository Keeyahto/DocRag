import json
from typing import List

import pytest

pytest.importorskip("fastapi")
from fastapi.testclient import TestClient  # type: ignore

from apps.api.main import app, index_path


class FakeEmbBackend:
    def __init__(self, dim: int = 8):
        self.dim = dim

    def _vec(self, text: str) -> List[float]:
        # simple deterministic embedding
        acc = 0
        for i, c in enumerate(text.encode("utf-8")):
            acc = (acc * 131 + c) % 1000003
        # map into dim values
        return [((acc + i * 9973) % 10000) / 10000.0 for i in range(self.dim)]

    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        return [self._vec(t) for t in texts]

    def embed_query(self, text: str) -> List[float]:
        return self._vec(text)


def make_index(tenant: str, texts: List[str], metas: List[dict], dim: int = 8):
    from langchain_community.vectorstores import FAISS
    from langchain_core.embeddings import Embeddings

    class _Emb(Embeddings):
        def embed_documents(self, docs: List[str]) -> List[List[float]]:
            return FakeEmbBackend(dim).embed_texts(docs)

        def embed_query(self, text: str) -> List[float]:
            return FakeEmbBackend(dim).embed_query(text)

    vs = FAISS.from_texts(texts, _Emb(), metas)
    vs.save_local(str(index_path(tenant)))


@pytest.fixture(autouse=True)
def _clean_data(tmp_path, monkeypatch):
    # Use a temp data dir by monkeypatching app paths
    base = tmp_path / "data"
    (base / "faiss").mkdir(parents=True, exist_ok=True)
    (base / "uploads").mkdir(parents=True, exist_ok=True)
    monkeypatch.setenv("TOP_K", "3")
    yield


def test_health_and_tenant_new():
    client = TestClient(app)
    r = client.get("/health")
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "ok"
    r2 = client.post("/tenant/new")
    assert r2.status_code == 200
    assert "tenant" in r2.json()


def test_index_validation_errors(tmp_path):
    client = TestClient(app)
    # Missing tenant
    files = {"files": ("a.txt", b"hello")}
    r = client.post("/index", files=files)
    assert r.status_code == 400
    # Too many files
    files = [
        ("files", ("a.txt", b"1")),
        ("files", ("b.txt", b"2")),
        ("files", ("c.txt", b"3")),
        ("files", ("d.txt", b"4")),
    ]
    r2 = client.post("/index", headers={"X-Tenant-ID": "t1"}, files=files)
    assert r2.status_code == 413


def test_answer_and_stream_with_fake_index(monkeypatch, tmp_path):
    tenant = "test-tenant"
    # Create small FAISS index
    texts = [
        "hello world document one",
        "another text mentioning world and context",
        "final piece unrelated",
    ]
    metas = [
        {"source": "f1.txt", "page": 1, "id": "c1"},
        {"source": "f2.txt", "page": 2, "id": "c2"},
        {"source": "f3.txt", "page": 3, "id": "c3"},
    ]
    make_index(tenant, texts, metas)

    # Patch embeddings used by API to match index dimension
    from apps import api as api_pkg
    from apps.api import main as api_main

    fake = FakeEmbBackend(dim=8)

    def _fake_get_embeddings():
        return fake

    async def _fake_chat_stream(prompt, cfg=None):
        for t in ["Hello", " ", "world!"]:
            yield t

    monkeypatch.setattr(api_main, "get_embeddings", _fake_get_embeddings, raising=True)
    monkeypatch.setattr(api_main, "chat_stream", _fake_chat_stream, raising=True)

    client = TestClient(app)

    # Non-streaming
    r = client.post("/answer", headers={"X-Tenant-ID": tenant}, json={"question": "What about world?"})
    assert r.status_code == 200
    body = r.json()
    assert body["answer"].startswith("Hello")
    assert body["sources"] and len(body["sources"]) >= 1

    # Streaming SSE
    with client.stream(
        "POST",
        "/answer/stream",
        headers={"X-Tenant-ID": tenant, "Accept": "text/event-stream"},
        json={"question": "world?"},
    ) as r:
        buf = ""
        for chunk in r.iter_text():
            buf += chunk
            if "event: done" in buf:
                break
    assert "event: context" in buf
    assert "event: token" in buf
    assert "event: done" in buf


def test_reset_deletes_index(monkeypatch, tmp_path):
    tenant = "tenant-reset"
    make_index(tenant, ["hello"], [{"source": "a.txt", "page": 1, "id": "x"}])
    from apps.api import main as api_main

    fake = FakeEmbBackend(dim=8)

    def _fake_get_embeddings():
        return fake

    async def _fake_chat_stream(prompt, cfg=None):
        yield "ok"

    monkeypatch.setattr(api_main, "get_embeddings", _fake_get_embeddings, raising=True)
    monkeypatch.setattr(api_main, "chat_stream", _fake_chat_stream, raising=True)

    client = TestClient(app)
    # Ensure answer works first
    r1 = client.post("/answer", headers={"X-Tenant-ID": tenant}, json={"question": "hello?"})
    assert r1.status_code == 200

    # Reset
    r2 = client.post("/reset", headers={"X-Tenant-ID": tenant})
    assert r2.status_code == 200
    assert r2.json().get("deleted") is True

    # Now answer should 404
    r3 = client.post("/answer", headers={"X-Tenant-ID": tenant}, json={"question": "hello?"})
    assert r3.status_code == 404
