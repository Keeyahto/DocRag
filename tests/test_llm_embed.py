import types

from kits.kit_llm import EmbeddingBackend, EmbedConfig


class _StubST:
    def __init__(self, model):
        self.model = model

    def encode(self, texts, batch_size=32, show_progress_bar=False, normalize_embeddings=True):
        # Deterministic 4-d vectors based on text length
        def vec(t):
            s = sum(ord(c) for c in t) or 1
            return [s % 7 / 7.0, s % 11 / 11.0, s % 13 / 13.0, s % 17 / 17.0]
        return [vec(t) for t in texts]


def test_embedding_backend_sentence_transformers_monkeypatched(monkeypatch):
    # Monkeypatch SentenceTransformer used inside backend
    import kits.kit_llm as kit_llm

    def _fake_ensure(self):
        self._st_model = _StubST(self.cfg.model)

    monkeypatch.setattr(kit_llm.EmbeddingBackend, "_ensure_st", _fake_ensure, raising=True)

    be = EmbeddingBackend(EmbedConfig(backend="sentence_transformers", model="fake-model", batch_size=3))
    texts = ["a", "bb", "ccc", "dddd", "eeeee"]
    vecs = be.embed_texts(texts)
    assert len(vecs) == len(texts)
    assert len(vecs[0]) == 4
    # embed_query uses same path
    vq = be.embed_query("hi")
    assert len(vq) == 4
