"""Thin client for interacting with the GNews API."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional
from urllib.parse import urlparse

import requests

API_URL = "https://gnews.io/api/v4/search"

_INVALID_URL_SENTINELS = {"", "invalid url", "null", "none", "n/a"}


class GNewsClientError(RuntimeError):
    """Raised when the GNews API returns an error response."""


@dataclass(frozen=True)
class GNewsArticle:
    """Normalized article metadata returned from GNews."""

    title: str
    url: str
    source: str
    description: str
    published_at: Optional[str]


def _clean_url(value: Optional[str]) -> str:
    if not value or not isinstance(value, str):
        return ""
    candidate = value.strip()
    if not candidate or candidate.lower() in _INVALID_URL_SENTINELS:
        return ""
    if candidate.startswith("//"):
        candidate = "https:" + candidate
    parsed = urlparse(candidate)
    if not parsed.scheme:
        candidate = f"https://{candidate}"
        parsed = urlparse(candidate)
    if parsed.scheme in ("http", "https") and parsed.netloc:
        return candidate
    return ""


def _extract_article_url(entry: dict) -> str:
    direct_keys = ("url", "article_url", "source_url", "weblink")
    for key in direct_keys:
        url = _clean_url(entry.get(key))
        if url:
            return url

    source = entry.get("source") or {}
    source_keys = ("url", "origin", "domain")
    for key in source_keys:
        url = _clean_url(source.get(key))
        if url:
            return url

    link = entry.get("link") or entry.get("redirect")
    url = _clean_url(link)
    if url:
        return url

    return ""


def fetch_articles(query: str, api_key: str, *, max_results: int = 5) -> list[GNewsArticle]:
    """Fetch relevant news articles for the query."""
    params = {
        "q": query,
        "token": api_key,
        "lang": "en",
        "max": max(1, min(max_results, 10)),
        "sortby": "publishedAt",
    }

    try:
        response = requests.get(API_URL, params=params, timeout=10)
    except requests.RequestException as exc:  # pragma: no cover - network error handling
        raise GNewsClientError(str(exc)) from exc

    if response.status_code != requests.codes.ok:
        raise GNewsClientError(f"HTTP {response.status_code}: {response.text}")

    data = response.json()
    raw_articles = data.get("articles") or []
    normalized: list[GNewsArticle] = []
    for entry in raw_articles[: params["max"]]:
        title = (entry.get("title") or "").strip()
        url = _extract_article_url(entry)
        source_name = (entry.get("source") or {}).get("name") or "Unknown"
        description = (entry.get("description") or "").strip()
        published_at = entry.get("publishedAt")
        if not url:
            continue
        normalized.append(
            GNewsArticle(
                title=title,
                url=url,
                source=source_name,
                description=description,
                published_at=published_at,
            )
        )
    return normalized
