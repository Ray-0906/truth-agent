"""Text parsing utilities."""

from __future__ import annotations

import re
from typing import Iterable, Optional

_URL_REGEX = re.compile(
    r"(?P<url>(?:https?://|www\.)[\w\-._~:/?#\[\]@!$&'()*+,;=%]+)",
    re.IGNORECASE,
)
_SENTENCE_SPLIT_REGEX = re.compile(r"(?<=[.!?])\s+")


def extract_urls(text: str) -> list[str]:
    """Return a de-duplicated list of URLs discovered in text."""
    if not text:
        return []
    matches = _URL_REGEX.finditer(text)
    seen: set[str] = set()
    ordered: list[str] = []
    for match in matches:
        url = match.group("url")
        normalized = url if url.startswith("http") else f"https://{url}"
        if normalized not in seen:
            seen.add(normalized)
            ordered.append(normalized)
    return ordered


def truncate_sentences(sentences: Iterable[str], *, limit: int = 80) -> str:
    """Join sentences and enforce a soft character limit."""
    filtered = [s.strip() for s in sentences if s and s.strip()]
    if not filtered:
        return ""
    joined = " ".join(filtered)
    if len(joined) <= limit:
        return joined
    return joined[: limit - 3].rstrip() + "..."


def split_sentences(text: str, *, max_sentences: Optional[int] = None) -> list[str]:
    """Split text into sentences using basic punctuation heuristics."""
    if not text:
        return []
    chunks = _SENTENCE_SPLIT_REGEX.split(text.strip())
    sentences = [chunk.strip() for chunk in chunks if chunk and chunk.strip()]
    if max_sentences is None:
        return sentences
    return sentences[:max_sentences]
