from __future__ import annotations

import asyncio
import os
from io import BytesIO

import httpx
from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command
from aiogram.types import Message


API_BASE = os.getenv("API_BASE_URL", "http://localhost:8000")
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")


async def post_index(tenant: str, filename: str, content: bytes) -> str:
    async with httpx.AsyncClient(timeout=120) as client:
        files = {"files": (filename, content)}
        headers = {"X-Tenant-ID": tenant}
        r = await client.post(f"{API_BASE}/index", files=files, headers=headers)
        r.raise_for_status()
        return r.json()["job_id"]


async def get_status(job_id: str) -> dict:
    async with httpx.AsyncClient(timeout=30) as client:
        r = await client.get(f"{API_BASE}/status/{job_id}")
        r.raise_for_status()
        return r.json()


async def ask(tenant: str, q: str) -> dict:
    async with httpx.AsyncClient(timeout=120) as client:
        headers = {"X-Tenant-ID": tenant}
        r = await client.post(f"{API_BASE}/answer", headers=headers, json={"question": q})
        r.raise_for_status()
        return r.json()


async def cmd_start(message: Message):
    await message.answer("Я бот DocRAG. Команды: /upload, /ask <вопрос>, /status, /reset")


async def cmd_upload(message: Message):
    await message.answer("Пришлите PDF/MD/TXT/DOCX файлом в чат.")


async def cmd_status(message: Message):
    tenant = str(message.chat.id)
    await message.answer("Укажите job_id после загрузки. Пока упрощено: статус в Redis не сохраняем в боте.")


async def cmd_reset(message: Message):
    tenant = str(message.chat.id)
    async with httpx.AsyncClient(timeout=30) as client:
        headers = {"X-Tenant-ID": tenant}
        r = await client.post(f"{API_BASE}/reset", headers=headers)
        r.raise_for_status()
    await message.answer("Индекс и файлы сброшены.")


async def cmd_ask(message: Message):
    tenant = str(message.chat.id)
    text = message.text or ""
    q = text.partition(" ")[2].strip()
    if not q:
        await message.answer("Использование: /ask ваш вопрос")
        return
    try:
        res = await ask(tenant, q)
    except Exception as e:
        await message.answer(f"Ошибка: {e}")
        return
    answer = res.get("answer", "(пусто)")
    sources = res.get("sources", [])[:3]
    src_txt = "\n".join([f"• {s.get('filename')} (стр.{s.get('page')})" for s in sources]) or "(источники не найдены)"
    await message.answer(f"{answer}\n\nИсточники:\n{src_txt}")


async def on_document(message: Message):
    tenant = str(message.chat.id)
    doc = message.document
    if not doc:
        return
    if doc.file_name and not any(doc.file_name.lower().endswith(ext) for ext in (".pdf", ".md", ".txt", ".docx")):
        await message.answer("Поддерживаются только PDF/MD/TXT/DOCX")
        return
    await message.answer("Скачиваю файл...")
    bot: Bot = message.bot
    file = await bot.get_file(doc.file_id)
    file_bytes = await bot.download_file(file.file_path)
    content = file_bytes.getvalue() if isinstance(file_bytes, BytesIO) else file_bytes.read()
    try:
        job_id = await post_index(tenant, doc.file_name or "upload", content)
    except Exception as e:
        await message.answer(f"Ошибка загрузки: {e}")
        return
    await message.answer(f"Файл принят. job_id={job_id}. Подождите индексации и задайте вопрос через /ask ...")


def main():
    if not BOT_TOKEN:
        raise SystemExit("TELEGRAM_BOT_TOKEN is not set")
    dp = Dispatcher()
    dp.message.register(cmd_start, Command("start"))
    dp.message.register(cmd_upload, Command("upload"))
    dp.message.register(cmd_status, Command("status"))
    dp.message.register(cmd_reset, Command("reset"))
    dp.message.register(cmd_ask, Command("ask"))
    dp.message.register(on_document, F.document)
    bot = Bot(token=BOT_TOKEN)
    asyncio.run(dp.start_polling(bot))


if __name__ == "__main__":
    main()

