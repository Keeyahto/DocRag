from __future__ import annotations

import asyncio
import json
import os
from dataclasses import dataclass
from typing import AsyncGenerator, Iterable, List, Optional

try:
    from openai import AsyncOpenAI
except Exception:  # pragma: no cover
    AsyncOpenAI = None  # type: ignore

try:
    import httpx
except Exception:  # pragma: no cover
    httpx = None  # type: ignore


@dataclass
class EmbedConfig:
    backend: str = os.getenv("EMBED_BACKEND", "sentence_transformers")
    model: str = os.getenv("EMBED_MODEL", "sentence-transformers/all-MiniLM-L6-v2")
    batch_size: int = int(os.getenv("EMBED_BATCH_SIZE", "64"))


class EmbeddingBackend:
    def __init__(self, cfg: Optional[EmbedConfig] = None):
        self.cfg = cfg or EmbedConfig()
        self._st_model = None

    def _ensure_st(self):
        if self._st_model is None:
            from sentence_transformers import SentenceTransformer

            self._st_model = SentenceTransformer(self.cfg.model)

    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        if self.cfg.backend == "hash":
            # Lightweight deterministic embedding for tests/offline
            def _vec(t: str) -> List[float]:
                acc = 0
                for b in t.encode("utf-8"):
                    acc = (acc * 131 + b) % 1000003
                return [((acc + i * 9973) % 10007) / 10007.0 for i in range(8)]
            return [_vec(t) for t in texts]
        if self.cfg.backend == "openai":
            # Use OpenAI embeddings endpoint
            if AsyncOpenAI is None:
                raise RuntimeError("openai package not installed")
            model = self.cfg.model
            client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"), base_url=os.getenv("OPENAI_BASE_URL"))

            async def _run() -> List[List[float]]:
                out: List[List[float]] = []
                for i in range(0, len(texts), self.cfg.batch_size):
                    batch = texts[i : i + self.cfg.batch_size]
                    resp = await client.embeddings.create(model=model, input=batch)
                    out.extend([d.embedding for d in resp.data])
                return out

            return asyncio.get_event_loop().run_until_complete(_run())
        # sentence-transformers default
        self._ensure_st()
        arr = self._st_model.encode(texts, batch_size=self.cfg.batch_size, show_progress_bar=False, normalize_embeddings=True)
        # Try to coerce to list without requiring numpy
        if hasattr(arr, "tolist"):
            try:
                return arr.tolist()
            except Exception:
                pass
        return [list(v) for v in arr]  # pragma: no cover

    def embed_query(self, text: str) -> List[float]:
        return self.embed_texts([text])[0]


@dataclass
class ChatConfig:
    backend: str = os.getenv("LLM_BACKEND", "ollama")
    model: str = os.getenv("LLM_MODEL", "llama3:8b")
    temperature: float = float(os.getenv("LLM_TEMPERATURE", "0.2"))
    max_tokens: int = int(os.getenv("LLM_MAX_TOKENS", "512"))


async def chat_stream(prompt: str, cfg: Optional[ChatConfig] = None) -> AsyncGenerator[str, None]:
    cfg = cfg or ChatConfig()
    if cfg.backend == "openai":
        if AsyncOpenAI is None:
            raise RuntimeError("openai package not installed")
        client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"), base_url=os.getenv("OPENAI_BASE_URL"))
        stream = await client.chat.completions.create(
            model=cfg.model,
            temperature=cfg.temperature,
            max_tokens=cfg.max_tokens,
            messages=[{"role": "user", "content": prompt}],
            stream=True,
        )
        async for chunk in stream:
            if chunk.choices and chunk.choices[0].delta and chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content
        return

    # Ollama streaming via HTTP
    if httpx is None:
        raise RuntimeError("httpx not installed")
    base = os.getenv("OLLAMA_HOST", "http://localhost:11434")
    url = base.rstrip("/") + "/api/generate"
    try:
        async with httpx.AsyncClient(timeout=None) as client:
            req = {
                "model": cfg.model,
                "prompt": prompt,
                "stream": True,
                "options": {"temperature": cfg.temperature, "num_predict": cfg.max_tokens},
            }
            async with client.stream("POST", url, json=req) as resp:
                resp.raise_for_status()
                async for line in resp.aiter_lines():
                    if not line:
                        continue
                    try:
                        data = json.loads(line)
                    except Exception:
                        continue
                    if "response" in data and data["response"]:
                        yield data["response"]
                    if data.get("done"):
                        break
    except Exception:
        # Fallback: no tokens yielded on error to keep API responsive in tests
        return
