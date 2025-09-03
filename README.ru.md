# DocRAG

**DocRAG** — небольшой демонстрационный RAG (Retrieval-Augmented Generation) по локальным документам. Он показывает типовой сценарий: загрузили файлы → проиндексировали в FAISS → задали вопрос → получили потоковый ответ LLM с подсветкой релевантных фрагментов. Есть простой веб-интерфейс и Telegram-бот.

https://github.com/user-attachments/assets/68e92673-f93f-4838-871b-997720037ced


## Что умеет

* Форматы: **PDF**, **Markdown**, **TXT**, **DOCX**
* Векторное хранилище: **FAISS** на диске (`data/faiss`)
* Эмбеддинги: локально через **sentence-transformers** (по умолчанию) или **OpenAI**
* LLM: **Ollama** (по умолчанию) или **OpenAI Chat API**; ответ приходит **стримом (SSE)**
* Чанкинг: разбиение по токенам с учётом markdown-заголовков
* Мульти-тенантность: разделение по заголовку `X-Tenant-ID`
* Индексация: асинхронно через **RQ + Redis** (есть синхронный фолбэк)
* Интерфейсы: **Next.js** веб-панель и **Telegram-бот**

## Состав

* **API** (`apps/api`): FastAPI — загрузка, индексация, поиск, Q\&A, SSE
* **Worker** (`apps/worker`): обрабатывает файлы, делает эмбеддинги и пишет в FAISS
* **Redis**: очередь заданий
* **Web** (`apps/web`): Next.js — загрузка документов и страница с вопросами
* **Bot** (`apps/bot`): Telegram-бот (опционально)

Директории данных:

* `data/uploads/<tenant>` — загруженные файлы
* `data/faiss/<tenant>` — индексы FAISS

## Быстрый старт (Docker)

Нужны Docker и Docker Compose. Опционально — Ollama или OpenAI.

1. Заполните `.env` в корне. Минимально полезные переменные:

   * `EMBED_BACKEND` (`sentence_transformers` | `openai`)
   * `EMBED_MODEL` (например `sentence-transformers/all-MiniLM-L6-v2`)
   * `LLM_BACKEND` (`ollama` | `openai`)
   * `LLM_MODEL` (например `llama3:8b` для Ollama или `gpt-4o-mini` для OpenAI)
   * `OPENAI_API_KEY`, `OPENAI_BASE_URL` — если используете OpenAI
   * `OLLAMA_HOST` (например `http://host.docker.internal:11434`)
   * `TELEGRAM_BOT_TOKEN` — если нужен бот

2. Запустите бэкенд-часть:

```bash
docker compose up --build
```

Поднимутся `api`, `worker`, `redis` и (если указан токен) `bot`. API: `http://localhost:8000`.

3. Веб-интерфейс (Next.js) отдельно:

```bash
cd apps/web
cp .env.example .env.local
# NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
npm install
npm run dev
# откройте http://localhost:3000
```

## Примеры API

Создать tenant:

```bash
curl -s -X POST http://localhost:8000/tenant/new
```

Загрузить файлы:

```bash
TENANT=... # из /tenant/new
curl -s -X POST \
  -H "X-Tenant-ID: $TENANT" \
  -F "files=@/path/to/doc1.pdf" \
  -F "files=@/path/to/doc2.md" \
  http://localhost:8000/index
```

Проверить статус (если индексация асинхронная):

```bash
curl -s http://localhost:8000/status/<job_id>
```

Задать вопрос (цельный ответ):

```bash
curl -s -X POST \
  -H "X-Tenant-ID: $TENANT" \
  -H "Content-Type: application/json" \
  -d '{"question":"О чём документ?","top_k":5}' \
  http://localhost:8000/answer
```

Стриминговый ответ (SSE):

```bash
curl -N \
  -H "X-Tenant-ID: $TENANT" \
  -H "Accept: text/event-stream" \
  -H "Content-Type: application/json" \
  -d '{"question":"Кратко изложи ключевые пункты"}' \
  http://localhost:8000/answer/stream
```

Сбросить данные tenant:

```bash
curl -s -X POST -H "X-Tenant-ID: $TENANT" http://localhost:8000/reset
```

## Локальная разработка (без Docker)

1. Поднимите Redis (например контейнер `redis:7-alpine` на 6379)
2. Python 3.11 + виртуальное окружение
3. Зависимости:

   * API: `pip install -r apps/api/requirements.txt`
   * Worker: `pip install -r apps/worker/requirements.txt`
4. Запуск:

   * Worker: `python -m apps.worker.worker`
   * API: `uvicorn apps.api.main:app --reload --port 8000`

Переменные читаются из `.env`. Каталоги `data/` создаются автоматически.

## Настройки

* `EMBED_*`: выбор бэкенда/модели эмбеддингов (для OpenAI нужен `OPENAI_API_KEY`)
* `LLM_*`: выбор модели/провайдера LLM (для Ollama укажите `OLLAMA_HOST`, если не `localhost:11434`)
* `CHUNK_MAX_TOKENS`, `CHUNK_OVERLAP`: размер чанков
* `TOP_K`: число фрагментов в контексте
* `MAX_FILE_MB`, `MAX_FILES_PER_REQUEST`: ограничения загрузки
* `INDEX_SYNC=1`: принудительно синхронная индексация (удобно на демо/в тестах)

## Telegram-бот (опционально)


https://github.com/user-attachments/assets/7d08ede9-5552-4a7c-8cd2-6d3fd2224ac9


Задайте `TELEGRAM_BOT_TOKEN` в `.env`. В `docker compose` бот ходит в API по `http://api:8000`. Команды: `/upload` (пришлите файл), `/ask <вопрос>`, `/reset`.

## Тесты

* Python (API/worker):

```bash
pytest -q
```

* Web (из `apps/web`):

```bash
npm run test
```

## Ограничения

* Проект предназначен для демонстраций: нет аутентификации; сегрегация — заголовком `X-Tenant-ID`.
* FAISS хранится локально; внешняя векторная БД не используется.
* Для продакшна потребуется расширение: авторизация, персистентные метаданные, наблюдаемость и т. п.
