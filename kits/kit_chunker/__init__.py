from typing import Iterable, List

import re


def _simple_tokenize(text: str) -> List[str]:
    # Very simple tokenization by splitting on whitespace
    return re.findall(r"\S+", text)


def split_text(text: str, max_tokens: int, overlap: int) -> List[str]:
    if not text:
        return []
    tokens = _simple_tokenize(text)
    if max_tokens <= 0:
        return [text]
    chunks: List[str] = []
    i = 0
    n = len(tokens)
    while i < n:
        j = min(i + max_tokens, n)
        chunk = " ".join(tokens[i:j])
        if chunk:
            chunks.append(chunk)
        if j >= n:
            break
        # step forward with overlap
        step = max(1, max_tokens - overlap)
        i += step
    return chunks


def split_markdown(text: str, max_tokens: int, overlap: int) -> List[str]:
    # Prefer splitting by markdown headings to keep context
    if not text:
        return []
    parts = re.split(r"(?m)^#{1,6} ", text)
    # Re-add heading markers where split removed them (except possibly the first, which may not have heading)
    rebuilt = []
    for idx, p in enumerate(parts):
        if not p:
            continue
        rebuilt.append(("# " if idx != 0 else "") + p)
    # For each section, further chunk by tokens
    chunks: List[str] = []
    for p in rebuilt:
        sub = split_text(p, max_tokens=max_tokens, overlap=overlap)
        chunks.extend(sub)
    return chunks

