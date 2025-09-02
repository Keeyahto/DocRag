from __future__ import annotations

import io
import json
import os
import shutil
import uuid
from pathlib import Path
from typing import AsyncGenerator, Dict, List, Literal, Optional

from fastapi import BackgroundTasks, Depends, FastAPI, File, Header, HTTPException, Request, Response, UploadFile
from fastapi.responses import JSONResponse, StreamingResponse
from sse_starlette.sse import EventSourceResponse

from pydantic import BaseModel
from redis import Redis
import redis
from rq import Queue

from kits.kit_common import normalize_text, gen_request_id
from kits.kit_common.highlight import extract_snippet_and_highlights

from langchain_community.vectorstores import FAISS
from langchain_community.docstore.document import Document

from kits.kit_llm import EmbeddingBackend, EmbedConfig, ChatConfig, chat_stream

import time
import logging

# ---------------- Config / Logging -----------------

APP_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = Path(os.getenv("DOC_RAG_DATA_DIR", str(APP_ROOT / "data")))
FAISS_DIR = DATA_DIR / "faiss"
UPLOADS_DIR = DATA_DIR / "uploads"
TMP_DIR = DATA_DIR / "tmp"
for p in (FAISS_DIR, UPLOADS_DIR, TMP_DIR):
    p.mkdir(parents=True, exist_ok=True)

LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
logging.basicConfig(level=getattr(logging, LOG_LEVEL, logging.INFO), format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("api")


class FileInfo(BaseModel):
    filename: str
    size_bytes: int
    mime: Optional[str] = None


class IndexJob(BaseModel):
    job_id: str
    tenant: str
    files: List[FileInfo]
    status: Literal["queued", "working", "done", "error"]
    progress: int = 0
    error: Optional[str] = None


class SourcePreview(BaseModel):
    id: str
    score: float
    filename: Optional[str] = None
    page: Optional[int] = None
    snippet: str
    highlights: List[tuple[int, int]] = []


class QAResponse(BaseModel):
    answer: str
    sources: List[SourcePreview]


def get_env_summary() -> Dict[str, str]:
    return {
        "env": os.getenv("APP_ENV", "local"),
        "embed_backend": os.getenv("EMBED_BACKEND", "sentence_transformers"),
        "embed_model": os.getenv("EMBED_MODEL", "sentence-transformers/all-MiniLM-L6-v2"),
        "llm_backend": os.getenv("LLM_BACKEND", "ollama"),
        "llm_model": os.getenv("LLM_MODEL", "llama3:8b"),
    }


def get_queue() -> Queue:
    redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    r = Redis.from_url(redis_url)
    return Queue(connection=r)


def ensure_tenant(tenant: Optional[str]) -> str:
    if not tenant:
        raise HTTPException(status_code=400, detail={"error": {"code": 400, "type": "validation_error", "message": "Missing tenant"}})
    return tenant


def allowed_ext(filename: str) -> bool:
    ext = filename.lower().rsplit(".", 1)[-1]
    return ext in {"pdf", "md", "txt", "docx"}


def index_path(tenant: str) -> Path:
    return FAISS_DIR / tenant


def has_index(tenant: str) -> bool:
    p = index_path(tenant)
    return (p / "index.faiss").exists() and (p / "index.pkl").exists()


def get_embeddings() -> EmbeddingBackend:
    cfg = EmbedConfig()
    # warnings if openai selected without keys
    if cfg.backend == "openai" and not os.getenv("OPENAI_API_KEY"):
        logger.warning("EMBED_BACKEND=openai but OPENAI_API_KEY is not set")
    return EmbeddingBackend(cfg)


def build_langchain_embeddings(backend: EmbeddingBackend):
    # Wrap into LangChain Embeddings interface
    from langchain_core.embeddings import Embeddings as LCEmb

    class _LCEmb(LCEmb):
        def embed_documents(self, texts: List[str]) -> List[List[float]]:
            return backend.embed_texts(texts)

        def embed_query(self, text: str) -> List[float]:
            return backend.embed_query(text)

    return _LCEmb()


def load_vectorstore(tenant: str) -> FAISS:
    if not has_index(tenant):
        raise HTTPException(status_code=404, detail={"error": {"code": 404, "type": "not_found", "message": "Index not found"}})
    vs_dir = str(index_path(tenant))
    emb = build_langchain_embeddings(get_embeddings())
    return FAISS.load_local(vs_dir, emb, allow_dangerous_deserialization=True)


def get_top_k() -> int:
    try:
        return int(os.getenv("TOP_K", "5"))
    except Exception:
        return 5



app = FastAPI()


@app.on_event("startup")
async def on_startup():
    cfg = get_env_summary()
    logger.info("Starting API with config: %s", cfg)
    if cfg["llm_backend"] == "openai" and not os.getenv("OPENAI_API_KEY"):
        logger.warning("LLM_BACKEND=openai but OPENAI_API_KEY is not set")
    if cfg["llm_backend"] == "ollama" and not os.getenv("OLLAMA_HOST"):
        logger.warning("LLM_BACKEND=ollama but OLLAMA_HOST is not set; defaulting to localhost:11434")


@app.get("/health")
def health():
    cfg = get_env_summary()
    return {"status": "ok", **cfg}


@app.post("/tenant/new")
def tenant_new():
    return {"tenant": str(uuid.uuid4())}


def _run_index_sync(tenant: str, saved_paths: List[str]):
    # Run indexing synchronously in-process (for tests/local fallback)
    from apps.worker.worker import index_files_job
    prev = os.getenv("EMBED_BACKEND")
    try:
        # Force lightweight deterministic backend to ensure fixed dimension
        os.environ["EMBED_BACKEND"] = "hash"
        index_files_job(tenant, saved_paths)
    finally:
        if prev is not None:
            os.environ["EMBED_BACKEND"] = prev
        else:
            os.environ.pop("EMBED_BACKEND", None)
    # Create a pseudo job id
    return {"job_id": "sync", "tenant": tenant}


@app.post("/index")
async def index(
    request: Request,
    files: List[UploadFile] = File(...),
    x_tenant_id: Optional[str] = Header(None, alias="X-Tenant-ID"),
):
    tenant = ensure_tenant(x_tenant_id)
    max_files = int(os.getenv("MAX_FILES_PER_REQUEST", "3"))
    max_mb = int(os.getenv("MAX_FILE_MB", "30"))
    if not files:
        raise HTTPException(status_code=400, detail={"error": {"code": 400, "type": "validation_error", "message": "No files"}})
    if len(files) > max_files:
        raise HTTPException(status_code=413, detail={"error": {"code": 413, "type": "payload_too_large", "message": "Too many files"}})
    saved_paths: List[str] = []
    up_dir = UPLOADS_DIR / tenant
    up_dir.mkdir(parents=True, exist_ok=True)
    infos: List[FileInfo] = []
    for uf in files:
        if not allowed_ext(uf.filename or ""):
            raise HTTPException(status_code=400, detail={"error": {"code": 400, "type": "validation_error", "message": f"Unsupported file: {uf.filename}"}})
        content = await uf.read()
        size_mb = len(content) / (1024 * 1024)
        if size_mb > max_mb:
            raise HTTPException(status_code=413, detail={"error": {"code": 413, "type": "payload_too_large", "message": f"File too big: {uf.filename}"}})
        dest = up_dir / (uf.filename or f"upload_{len(saved_paths)}")
        with open(dest, "wb") as f:
            f.write(content)
        saved_paths.append(str(dest))
        infos.append(FileInfo(filename=uf.filename or dest.name, size_bytes=len(content), mime=uf.content_type))

    # Decide sync vs async
    force_sync = os.getenv("INDEX_SYNC", "0") in {"1", "true", "True"}
    if force_sync:
        res = _run_index_sync(tenant, saved_paths)
        return JSONResponse(status_code=200, content={**res, "files": [i.model_dump() for i in infos]})

    try:
        q = get_queue()
        job = q.enqueue("apps.worker.worker.index_files_job", tenant, saved_paths)
        logger.info("Enqueued INDEX_FILES job=%s tenant=%s files=%d", job.id, tenant, len(saved_paths))
        # Optionally eager-run indexing too (for tests) while still returning 202
        if os.getenv("INDEX_EAGER", "0") in {"1", "true", "True"}:
            _run_index_sync(tenant, saved_paths)
        return JSONResponse(status_code=202, content={"job_id": job.id, "tenant": tenant, "files": [i.model_dump() for i in infos]})
    except Exception as e:
        logger.warning("Queue enqueue failed, falling back to sync indexing: %s", e)
        res = _run_index_sync(tenant, saved_paths)
        return JSONResponse(status_code=200, content={**res, "files": [i.model_dump() for i in infos]})


@app.get("/status/{job_id}")
def status(job_id: str):
    q = get_queue()
    job = q.fetch_job(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail={"error": {"code": 404, "type": "not_found", "message": "Job not found"}})
    rq_st = job.get_status(refresh=True)
    mapping = {"queued": "queued", "started": "working", "finished": "done", "failed": "error"}
    st = mapping.get(rq_st, rq_st)
    progress = int(job.meta.get("progress", 0)) if job.meta else 0
    err = job.meta.get("error") if job.meta else None
    # tenant saved in meta by worker
    tenant = job.meta.get("tenant") if job.meta else None
    return {"job_id": job.id, "tenant": tenant, "status": st, "progress": progress, "error": err}


class AskBody(BaseModel):
    question: str
    top_k: Optional[int] = None


def _search(tenant: str, query: str, k: int) -> List[SourcePreview]:
    emb = build_langchain_embeddings(get_embeddings())
    vs = load_vectorstore(tenant)
    # Fetch docs and distances
    results = vs.similarity_search_with_score(query, k=k)
    previews: List[SourcePreview] = []
    for doc, dist in results:
        meta = doc.metadata or {}
        snippet, hl = extract_snippet_and_highlights(doc.page_content, query)
        # Convert distance (lower better) to similarity [0..1], here assume cosine distance in [0..2] approx
        sim = 1.0 / (1.0 + float(dist))
        previews.append(
            SourcePreview(
                id=str(meta.get("id") or uuid.uuid4()),
                score=sim,
                filename=meta.get("source"),
                page=meta.get("page"),
                snippet=snippet,
                highlights=hl,
            )
        )
    return previews


@app.get("/search")
def search(tenant: str, q: str, k: Optional[int] = None):
    tenant = ensure_tenant(tenant)
    if not has_index(tenant):
        raise HTTPException(status_code=404, detail={"error": {"code": 404, "type": "not_found", "message": "Index not found"}})
    res = _search(tenant, q, k or get_top_k())
    return {"results": [r.model_dump() for r in res]}


@app.post("/answer")
async def answer(body: AskBody, x_tenant_id: Optional[str] = Header(None, alias="X-Tenant-ID")):
    tenant = ensure_tenant(x_tenant_id)
    if not body.question:
        raise HTTPException(status_code=400, detail={"error": {"code": 400, "type": "validation_error", "message": "Empty question"}})
    if not has_index(tenant):
        raise HTTPException(status_code=404, detail={"error": {"code": 404, "type": "not_found", "message": "Index not found"}})
    k = body.top_k or get_top_k()
    sources = _search(tenant, body.question, k)
    # Build prompt
    ctx = "\n\n".join([f"Source {i+1}: {s.snippet}" for i, s in enumerate(sources)])
    prompt = (
        "You are a helpful assistant. Answer the user based only on the sources.\n"
        "If unsure, say you don't know.\n\n"
        f"Question: {body.question}\n\n"
        f"Sources:\n{ctx}\n\n"
        "Answer in the language of the question."
    )
    chunks: List[str] = []
    async for tok in chat_stream(prompt, ChatConfig()):
        chunks.append(tok)
    return QAResponse(answer="".join(chunks), sources=sources)


@app.post("/answer/stream")
async def answer_stream(body: AskBody, request: Request, x_tenant_id: Optional[str] = Header(None, alias="X-Tenant-ID")):
    tenant = ensure_tenant(x_tenant_id)
    if not body.question:
        raise HTTPException(status_code=400, detail={"error": {"code": 400, "type": "validation_error", "message": "Empty question"}})
    if not has_index(tenant):
        raise HTTPException(status_code=404, detail={"error": {"code": 404, "type": "not_found", "message": "Index not found"}})
    k = body.top_k or get_top_k()
    sources = _search(tenant, body.question, k)
    ctx = "\n\n".join([f"Source {i+1}: {s.snippet}" for i, s in enumerate(sources)])
    prompt = (
        "You are a helpful assistant. Answer the user based only on the sources.\n"
        "If unsure, say you don't know.\n\n"
        f"Question: {body.question}\n\n"
        f"Sources:\n{ctx}\n\n"
        "Answer in the language of the question."
    )

    async def event_gen() -> AsyncGenerator[dict, None]:
        # Send context first
        yield {"event": "context", "data": json.dumps({"sources": [s.model_dump() for s in sources]})}
        try:
            async for tok in chat_stream(prompt, ChatConfig()):
                yield {"event": "token", "data": json.dumps({"t": tok})}
            yield {"event": "done", "data": json.dumps({"finish_reason": "stop"})}
        except Exception as e:
            logger.exception("Error during streaming")
            yield {"event": "error", "data": json.dumps({"message": str(e)})}

    return EventSourceResponse(event_gen())


@app.post("/reset")
def reset(x_tenant_id: Optional[str] = Header(None, alias="X-Tenant-ID")):
    tenant = ensure_tenant(x_tenant_id)
    # If indexing is in progress, could return 409; skipping for MVP
    # Delete index and uploads
    idx = index_path(tenant)
    up = UPLOADS_DIR / tenant
    for p in [idx, up]:
        if p.exists():
            shutil.rmtree(p, ignore_errors=True)
    return {"deleted": True}
