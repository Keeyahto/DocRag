from __future__ import annotations

import os
import uuid
from pathlib import Path
from typing import List

from redis import Redis
from rq import Queue, Worker

from kits.kit_common import normalize_text
from kits.kit_chunker import split_text, split_markdown
from kits.kit_llm import EmbeddingBackend, EmbedConfig

from langchain_community.document_loaders import PyPDFLoader, TextLoader
from langchain_community.document_loaders.word_document import Docx2txtLoader
from langchain_community.vectorstores import FAISS


APP_ROOT = Path(__file__).resolve().parents[2]
import os as _os
DATA_DIR = Path(_os.getenv("DOC_RAG_DATA_DIR", str(APP_ROOT / "data")))
FAISS_DIR = DATA_DIR / "faiss"
UPLOADS_DIR = DATA_DIR / "uploads"


def _load_documents(path: Path):
    ext = path.suffix.lower()
    if ext == ".pdf":
        loader = PyPDFLoader(str(path))
    elif ext in {".md", ".txt"}:
        loader = TextLoader(str(path), encoding="utf-8")
    elif ext == ".docx":
        loader = Docx2txtLoader(str(path))
    else:
        raise ValueError(f"Unsupported file: {path.name}")
    docs = loader.load()
    # normalize
    for d in docs:
        d.page_content = normalize_text(d.page_content)
    return docs


def _chunk_documents(docs, max_tokens: int, overlap: int):
    chunks = []
    for d in docs:
        text = d.page_content
        if not text:
            continue
        if d.metadata and d.metadata.get("source", "").lower().endswith(".md"):
            parts = split_markdown(text, max_tokens=max_tokens, overlap=overlap)
        else:
            parts = split_text(text, max_tokens=max_tokens, overlap=overlap)
        for p in parts:
            md = dict(d.metadata or {})
            md["id"] = uuid.uuid4().hex
            chunks.append((p, md))
    return chunks


def _save_to_faiss(tenant: str, chunks: List[tuple[str, dict]]):
    vs_dir = FAISS_DIR / tenant
    vs_dir.mkdir(parents=True, exist_ok=True)
    emb_backend = EmbeddingBackend(EmbedConfig())
    from langchain_core.embeddings import Embeddings as LCEmb

    class _LCEmb(LCEmb):
        def embed_documents(self, texts: List[str]) -> List[List[float]]:
            return emb_backend.embed_texts(texts)

        def embed_query(self, text: str) -> List[float]:
            return emb_backend.embed_query(text)

    emb = _LCEmb()

    texts = [t for t, _ in chunks]
    metas = [m for _, m in chunks]

    # If there is nothing to add, skip creating an empty index
    if not texts:
        return

    if (vs_dir / "index.faiss").exists():
        vs = FAISS.load_local(str(vs_dir), emb, allow_dangerous_deserialization=True)
        vs.add_texts(texts, metas)
        vs.save_local(str(vs_dir))
    else:
        vs = FAISS.from_texts(texts, emb, metas)
        vs.save_local(str(vs_dir))


def index_files_job(tenant: str, file_paths: List[str]):
    from rq import get_current_job

    job = get_current_job()
    if job is not None:
        job.meta["tenant"] = tenant
        job.meta["progress"] = 0
        job.save_meta()

    max_tokens = int(os.getenv("CHUNK_MAX_TOKENS", "512"))
    overlap = int(os.getenv("CHUNK_OVERLAP", "64"))

    all_chunks: List[tuple[str, dict]] = []
    n = len(file_paths)
    for i, p in enumerate(file_paths):
        try:
            docs = _load_documents(Path(p))
            chunks = _chunk_documents(docs, max_tokens=max_tokens, overlap=overlap)
            all_chunks.extend(chunks)
        except Exception as e:
            if job is not None:
                job.meta["error"] = str(e)
                job.save_meta()
            raise
        finally:
            if job is not None:
                job.meta["progress"] = int(((i + 1) / n) * 80)
                job.save_meta()

    # Embed + save to FAISS
    _save_to_faiss(tenant, all_chunks)
    if job is not None:
        job.meta["progress"] = 100
        job.save_meta()


def main():
    redis_url = os.getenv("REDIS_URL", "redis://redis:6379/0")
    r = Redis.from_url(redis_url)
    w = Worker([Queue()])
    w.work()


if __name__ == "__main__":
    main()
