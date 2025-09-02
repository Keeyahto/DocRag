from __future__ import annotations

from typing import List, Tuple
import re


def extract_snippet_and_highlights(text: str, query: str, window: int = 200) -> tuple[str, List[tuple[int, int]]]:
    """Return a snippet around best match and highlight offsets within the snippet.

    - Tokenize query into simple words (>=3 chars), ignoring basic RU/EN stop-words.
    - Find first occurrence of any token; build window around it.
    - Return up to 5 highlight spans [start, end] within snippet.
    """

    def tokenize(q: str) -> List[str]:
        words = re.findall(r"[\w\-]{3,}", q.lower(), flags=re.UNICODE)
        stop = {"the", "and", "for", "with", "have", "this", "that", "your", "from", "может", "когда", "если", "тогда", "так", "как"}
        return [w for w in words if w not in stop]

    q_tokens = tokenize(query)
    hay = text or ""
    best_pos = None
    highlights: List[Tuple[int, int]] = []
    for w in q_tokens:
        m = re.search(re.escape(w), hay, flags=re.IGNORECASE)
        if m and best_pos is None:
            best_pos = m.start()
    if best_pos is None:
        snippet = hay[: 2 * window]
        return snippet, []
    start = max(0, best_pos - window)
    end = min(len(hay), best_pos + window)
    snippet = hay[start:end]
    # compute up to 5 highlight ranges within snippet
    count = 0
    for w in q_tokens:
        for m in re.finditer(re.escape(w), snippet, flags=re.IGNORECASE):
            highlights.append((m.start(), m.end()))
            count += 1
            if count >= 5:
                break
        if count >= 5:
            break
    return snippet, highlights

