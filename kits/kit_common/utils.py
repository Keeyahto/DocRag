import re
import time
import uuid

_whitespace_re = re.compile(r"\s+")

def normalize_text(text: str) -> str:
    if not text:
        return ""
    # Normalize whitespace and strip
    text = text.replace("\u00a0", " ")
    text = _whitespace_re.sub(" ", text)
    return text.strip()

def now_ms() -> int:
    return int(time.time() * 1000)

def gen_request_id() -> str:
    return uuid.uuid4().hex

