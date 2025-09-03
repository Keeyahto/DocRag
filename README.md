
# DocRAG

_Читать на русском: [README.ru.md](./README.ru.md)_



https://github.com/user-attachments/assets/68e92673-f93f-4838-871b-997720037ced



**DocRAG** is a compact, demo-friendly RAG (Retrieval-Augmented Generation) you can run locally or in Docker. It indexes your documents (PDF/MD/TXT/DOCX) into FAISS and answers questions with an LLM via streaming, showing highlighted source snippets. It’s built for quick demos and local experiments.

## Features

* **Formats:** PDF, Markdown, TXT, DOCX
* **Vector store:** FAISS on local disk (`data/faiss`)
* **Embeddings:** `sentence-transformers` by default; OpenAI optional
* **LLMs:** Ollama by default; OpenAI Chat API optional; token streaming (SSE)
* **Chunking:** token-based splitting with markdown-aware mode
* **Multi-tenant:** simple header-based isolation (`X-Tenant-ID`)
* **Async indexing:** RQ worker + Redis (with a sync fallback)
* **Interfaces:** Next.js web UI and an optional Telegram bot

## Architecture

* **API** (`apps/api`): FastAPI endpoints for upload, indexing, search, Q\&A, and SSE streaming
* **Worker** (`apps/worker`): loads, normalizes, chunks, embeds, and writes FAISS (via RQ)
* **Redis:** job queue
* **Web** (`apps/web`): Next.js demo UI (upload & ask flows)
* **Bot** (`apps/bot`): Telegram bot (optional)

Data lives under `data/` (mounted into API/Worker):

* `data/uploads/<tenant>` — uploaded files
* `data/faiss/<tenant>` — FAISS index files

## Quick Start (Docker)

Prerequisites: Docker + Docker Compose. Optionally: Ollama or OpenAI.

1. Configure `.env` (root). Useful variables:

* `EMBED_BACKEND` (`sentence_transformers` | `openai`)
* `EMBED_MODEL` (e.g. `sentence-transformers/all-MiniLM-L6-v2`)
* `LLM_BACKEND` (`ollama` | `openai`)
* `LLM_MODEL` (e.g. `llama3:8b` for Ollama, or `gpt-4o-mini` for OpenAI)
* `OPENAI_API_KEY`, `OPENAI_BASE_URL` (if using OpenAI)
* `OLLAMA_HOST` (e.g. `http://host.docker.internal:11434`)
* `TELEGRAM_BOT_TOKEN` (if you want the bot)

2. Start services:

```bash
docker compose up --build
```

This starts `api`, `worker`, `redis`, and (if a token is set) `bot`. API: `http://localhost:8000`.

3. Start the Web UI (Next.js) separately:

```bash
cd apps/web
cp .env.example .env.local
# set NEXT_PUBLIC_API_BASE_URL=http://localhost:8000 if needed
npm install
npm run dev
# open http://localhost:3000
```

## API Usage (curl)

Create a tenant:

```bash
curl -s -X POST http://localhost:8000/tenant/new
```

Index files (single or multiple):

```bash
TENANT=... # from /tenant/new
curl -s -X POST \
  -H "X-Tenant-ID: $TENANT" \
  -F "files=@/path/to/doc1.pdf" \
  -F "files=@/path/to/doc2.md" \
  http://localhost:8000/index
```

If indexing is async, poll status:

```bash
curl -s http://localhost:8000/status/<job_id>
```

Ask a question (non-streaming):

```bash
curl -s -X POST \
  -H "X-Tenant-ID: $TENANT" \
  -H "Content-Type: application/json" \
  -d '{"question":"What is covered?","top_k":5}' \
  http://localhost:8000/answer
```

Ask with streaming (SSE):

```bash
curl -N \
  -H "X-Tenant-ID: $TENANT" \
  -H "Accept: text/event-stream" \
  -H "Content-Type: application/json" \
  -d '{"question":"Summarize key points"}' \
  http://localhost:8000/answer/stream
```

Reset tenant data:

```bash
curl -s -X POST -H "X-Tenant-ID: $TENANT" http://localhost:8000/reset
```

## Local Development (without Docker)

* Start Redis (e.g. `redis:7-alpine` on port 6379)
* Use Python 3.11 + a virtualenv
* Install deps:

  * API: `pip install -r apps/api/requirements.txt`
  * Worker: `pip install -r apps/worker/requirements.txt`
* Run worker: `python -m apps.worker.worker`
* Run API: `uvicorn apps.api.main:app --reload --port 8000`

Environment is read from the root `.env` (or process env). `data/` folders are created automatically.

## Configuration

* `EMBED_*`: embeddings backend/model (OpenAI requires `OPENAI_API_KEY`)
* `LLM_*`: LLM backend/model (set `OLLAMA_HOST` if Ollama isn’t on `localhost:11434`)
* `CHUNK_MAX_TOKENS`, `CHUNK_OVERLAP`: chunk sizing
* `TOP_K`: number of retrieved context items
* `MAX_FILE_MB`, `MAX_FILES_PER_REQUEST`: upload limits
* `INDEX_SYNC=1`: force synchronous indexing (handy for demos/tests)

## Telegram Bot (optional)


https://github.com/user-attachments/assets/b4dd7d02-57e5-4f72-9135-04d17c6c2b4e


Set `TELEGRAM_BOT_TOKEN` in `.env`. With docker compose, the bot connects to the API at `http://api:8000`. Commands: `/upload` (send a file), `/ask <question>`, `/reset`.

## Tests

* Python (API/worker):

```bash
pytest -q
```

* Web (from `apps/web`):

```bash
npm run test
```

## Notes / Limitations

* Demo-oriented: no authentication; tenant separation via the `X-Tenant-ID` header
* Local FAISS only; no external vector DB
* Not tuned for large-scale or multi-node setups out of the box
