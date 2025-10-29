"""Helpers for extracting data from the invocation context."""

from __future__ import annotations

from typing import Iterable

from google.genai import types

from google.adk.agents.readonly_context import ReadonlyContext


def _parts_to_text(parts: Iterable[types.Part]) -> str:
    """Return the concatenated text from Content parts."""
    texts: list[str] = []
    for part in parts:
        if getattr(part, "text", None):
            text = part.text.strip()
            if text:
                texts.append(text)
    return " ".join(texts)


def extract_latest_user_text(ctx: ReadonlyContext) -> str:
    """Best-effort extraction of the latest user authored text."""
    if ctx.user_content and ctx.user_content.parts:
        primary = _parts_to_text(ctx.user_content.parts)
        if primary:
            return primary

    for event in reversed(ctx.session.events):
        if event.author != "user" or not event.content:
            continue
        if not event.content.parts:
            continue
        candidate = _parts_to_text(event.content.parts)
        if candidate:
            return candidate
    return ""
