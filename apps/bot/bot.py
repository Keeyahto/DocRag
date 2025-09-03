from __future__ import annotations

import asyncio
import os
from io import BytesIO
from typing import AsyncIterator, Dict, Optional, Tuple
import json

import httpx
from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command
from aiogram.enums import ChatAction
from aiogram.types import (
    Message,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    ReplyKeyboardMarkup,
    KeyboardButton,
    CallbackQuery,
)
from aiogram.exceptions import TelegramBadRequest


API_BASE = os.getenv("API_BASE_URL", "http://localhost:8000")
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

# In-memory storage for thoughts to show via callbacks
THOUGHTS: Dict[Tuple[int, int], str] = {}


async def safe_edit_text(msg: Message, text: str, reply_markup: InlineKeyboardMarkup | None = None) -> bool:
    """Edit message text only when content/markup changed. Ignores 'message is not modified'.
    Returns True if edited.
    """
    key = (msg.chat.id, msg.message_id)
    
    # Нормализуем текст (убираем лишние пробелы)
    text = text.strip()
    
    # Создаем уникальный ключ для сравнения
    current_content = getattr(msg, '_current_content', '')
    current_markup = getattr(msg, '_current_markup', None)
    
    # Проверяем, действительно ли что-то изменилось
    if text == current_content and reply_markup == current_markup:
        return False
    
    try:
        await msg.edit_text(text, reply_markup=reply_markup)
        # Обновляем локальные атрибуты сообщения
        msg._current_content = text
        msg._current_markup = reply_markup
        return True
    except TelegramBadRequest as e:
        if "message is not modified" in str(e):
            # Если сообщение не изменилось, обновляем кэш
            msg._current_content = text
            msg._current_markup = reply_markup
            return False
        # Для других ошибок - пробрасываем исключение
        raise


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


async def ask_stream(
    tenant: str,
    q: str,
) -> AsyncIterator[tuple[str, dict]]:
    """Yield (event, obj) tuples from SSE stream: events: context, token, done, error"""
    headers = {"X-Tenant-ID": tenant, "Accept": "text/event-stream", "Content-Type": "application/json"}
    async with httpx.AsyncClient(timeout=None) as client:
        async with client.stream("POST", f"{API_BASE}/answer/stream", headers=headers, json={"question": q}) as r:
            r.raise_for_status()
            buffer = ""
            async for chunk in r.aiter_text():
                if not chunk:
                    continue
                buffer += chunk.replace("\r\n", "\n")
                while "\n\n" in buffer:
                    block, buffer = buffer.split("\n\n", 1)
                    event = "message"
                    data = ""
                    for line in block.split("\n"):
                        if line.startswith("event:"):
                            event = line[6:].strip()
                        if line.startswith("data:"):
                            data += line[5:].strip()
                    obj = {}
                    try:
                        obj = json.loads(data) if data else {}
                    except Exception:
                        # ignore json errors
                        pass
                    yield (event, obj)


def main_menu_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        resize_keyboard=True,
        keyboard=[
            [KeyboardButton(text="📄 Загрузка"), KeyboardButton(text="❓ Спросить")],
            [KeyboardButton(text="🗑️ Сброс")],
        ],
    )


async def cmd_start(message: Message):
    await message.answer(
        "Я бот DocRAG. Загрузите документ и задайте вопрос.\n\nКоманды: /upload, /ask <вопрос>, /reset",
        reply_markup=main_menu_keyboard(),
    )


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
    await message.answer("✅ Индекс и файлы сброшены.")


def _format_sources(sources: list[dict]) -> str:
    sources = (sources or [])[:3]
    if not sources:
        return "(источники не найдены)"
    return "\n".join([f"• {s.get('filename')} (стр.{s.get('page')})" for s in sources])


def _progress_bar(pct: int, width: int = 10) -> str:
    fill = int(pct / 100 * width)
    return "█" * fill + "░" * (width - fill)


async def cmd_ask(message: Message):
    tenant = str(message.chat.id)
    text = message.text or ""
    q = text.partition(" ")[2].strip()
    if not q:
        await message.answer("Использование: /ask ваш вопрос")
        return
    # Message placeholder and typing
    await message.bot.send_chat_action(message.chat.id, ChatAction.TYPING)
    status_msg = await message.answer("⏳ Генерация ответа началась…")

    # Streaming with hidden <think> support
    mode = "pending"  # pending | in_think | visible
    think_buf: Optional[str] = None
    answer_buf = ""
    sources: list[dict] = []
    last_edit = 0.0

    try:
        async for event, obj in ask_stream(tenant, q):
            if event == "context":
                sources = obj.get("sources", []) or sources
            elif event == "token":
                t = obj.get("t", "")
                if not t:
                    continue
                # accumulate and parse think
                if mode == "pending":
                    # Wait to see if starts with <think>
                    tmp = (t or "")
                    if (think_buf or "") == "" and tmp.lstrip().startswith("<think>"):
                        # entering think: drop opening
                        idx = tmp.index("<think>")
                        after = tmp[idx + 7 :]
                        mode = "in_think"
                        think_buf = (think_buf or "") + after
                    else:
                        answer_buf += t
                        mode = "visible"
                elif mode == "in_think":
                    if "</think>" in t:
                        before, after = t.split("</think>", 1)
                        think_buf = (think_buf or "") + before
                        answer_buf += after
                        mode = "visible"
                    else:
                        think_buf = (think_buf or "") + t
                else:
                    answer_buf += t

                # throttle edits
                now = asyncio.get_event_loop().time()
                if now - last_edit > 0.5:
                    last_edit = now
                    # Отправляем typing action реже, чтобы избежать flood control
                    if now - getattr(message, '_last_typing', 0) > 3.0:
                        try:
                            await message.bot.send_chat_action(message.chat.id, ChatAction.TYPING)
                            message._last_typing = now
                        except Exception:
                            # Игнорируем ошибки typing action
                            pass
                    
                    preview = answer_buf[-3800:]
                    preview_text = f"💬 Ответ (черновик):\n{preview}"
                    await safe_edit_text(status_msg, preview_text)
            elif event == "error":
                err_msg = obj.get("message", "stream error")
                await safe_edit_text(status_msg, f"❌ Ошибка: {err_msg}")
                return
            elif event == "done":
                break

        # Finalize
        src_txt = _format_sources(sources)
        text = f"{answer_buf}\n\nИсточники:\n{src_txt}"
        if think_buf:
            key = (message.chat.id, status_msg.message_id)
            THOUGHTS[key] = think_buf
            kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="🧠 Показать процесс размышлений", callback_data=f"show_think:{status_msg.message_id}")]])
            await safe_edit_text(status_msg, text[:4000], reply_markup=kb)
        else:
            await safe_edit_text(status_msg, text[:4000])
    except Exception as e:
        await safe_edit_text(status_msg, f"❌ Ошибка: {e}")


async def on_document(message: Message):
    tenant = str(message.chat.id)
    doc = message.document
    if not doc:
        return
    if doc.file_name and not any(doc.file_name.lower().endswith(ext) for ext in (".pdf", ".md", ".txt", ".docx")):
        await message.answer("Поддерживаются только PDF/MD/TXT/DOCX")
        return
    await message.answer("Скачиваю файл…")
    bot: Bot = message.bot
    file = await bot.get_file(doc.file_id)
    file_bytes = await bot.download_file(file.file_path)
    content = file_bytes.getvalue() if isinstance(file_bytes, BytesIO) else file_bytes.read()
    try:
        job_id = await post_index(tenant, doc.file_name or "upload", content)
    except Exception as e:
        await message.answer(f"Ошибка загрузки: {e}")
        return
    # Progress message
    prog_msg = await message.answer("📥 Индексация началась… 0%")
    # Poll status and update message
    try:
        last_update = 0
        while True:
            await asyncio.sleep(2.0)  # Увеличиваем интервал
            s = await get_status(job_id)
            pct = int(s.get("progress", 0))
            status = s.get("status", "queued")
            
            # Обновляем только если прогресс изменился или прошло достаточно времени
            now = asyncio.get_event_loop().time()
            if pct != getattr(prog_msg, '_last_pct', 0) or now - last_update > 5.0:
                bar = _progress_bar(pct)
                txt = f"📥 Индексация: {pct}% {bar}\nСтатус: {status}"
                if s.get("error"):
                    txt += f"\nОшибка: {s['error']}"
                await safe_edit_text(prog_msg, txt[:4000])
                prog_msg._last_pct = pct
                last_update = now
            
            if status in ("done", "error"):
                break
        
        if s.get("status") == "done":
            await safe_edit_text(prog_msg, "✅ Индексация завершена. Можете задавать вопросы через /ask …")
    except Exception:
        # best-effort: leave the last text
        pass


async def cb_show_think(call: CallbackQuery):
    chat_id = call.message.chat.id if call.message else None
    if not chat_id or not call.data:
        return
    try:
        _, mid = call.data.split(":", 1)
        mid_int = int(mid)
    except Exception:
        return
    key = (chat_id, mid_int)
    think = THOUGHTS.get(key)
    if not think:
        await call.answer("Данные раздумий не найдены", show_alert=True)
        return
    kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="🗑️ Закрыть", callback_data="close")]])
    await call.message.reply(f"🧠 Раздумья:\n{think[:3900]}")
    await call.answer()


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
    dp.callback_query.register(cb_show_think, F.data.startswith("show_think:"))
    # UX: map menu buttons to actions
    dp.message.register(cmd_upload, F.text == "📄 Загрузка")
    async def _ask_hint(m: Message):
        await m.answer("Отправьте команду вида:\n/ask ваш вопрос")
    dp.message.register(_ask_hint, F.text == "❓ Спросить")
    dp.message.register(cmd_reset, F.text == "🗑️ Сброс")
    bot = Bot(token=BOT_TOKEN)
    asyncio.run(dp.start_polling(bot))


if __name__ == "__main__":
    main()
