"""Custom tools for retrieving licensed news coverage."""

from __future__ import annotations

import os
from typing import Any

from google.adk.tools import FunctionTool
from google.adk.tools import ToolContext

from ..services import context_helpers, gnews_client, text_utils


def _format_sources(articles: list[gnews_client.GNewsArticle]) -> list[str]:
    """Format article metadata for downstream agents."""
    formatted: list[str] = []
    for article in articles:
        label = article.source or "Unknown"
        url = article.url or ""
        if url:
            formatted.append(f"{label} - {url}")
    return formatted


def _build_synopsis(articles: list[gnews_client.GNewsArticle]) -> str:
    """Create a concise synopsis from the first few articles."""
    sentences: list[str] = []
    for article in articles[:2]:
        candidate = article.description or article.title
        if candidate:
            sentences.append(candidate.strip())
    return text_utils.truncate_sentences(sentences, limit=220)


def fetch_news_evidence(
    claim: str, *, tool_context: ToolContext
) -> dict[str, Any]:
    """Retrieve up to five recent English-language articles related to the claim via GNews."""
    query = claim or context_helpers.extract_latest_user_text(tool_context)
    api_key = os.getenv("GNEWS_API_TOKEN")

    if not query:
        return {
            "status": "error",
            "verdict": "inconclusive",
            "confidence": 0.0,
            "supporting_sources": [],
            "synopsis": "No claim text provided for the GNews lookup.",
        }

    if not api_key:
        return {
            "status": "error",
            "verdict": "inconclusive",
            "confidence": 0.0,
            "supporting_sources": [],
            "synopsis": "GNEWS_API_TOKEN environment variable is not configured.",
        }

    try:
        articles = gnews_client.fetch_articles(query=query, api_key=api_key, max_results=5)
    except gnews_client.GNewsClientError as exc:
        return {
            "status": "error",
            "verdict": "inconclusive",
            "confidence": 0.0,
            "supporting_sources": [],
            "synopsis": f"GNews lookup failed: {exc}",
        }

    if not articles:
        return {
            "status": "no_data",
            "verdict": "inconclusive",
            "confidence": 0.2,
            "supporting_sources": [],
            "synopsis": "GNews did not return recent coverage matching the claim.",
        }

    sources = _format_sources(articles)
    article_details = [
        {
            "title": article.title,
            "url": article.url,
            "source": article.source,
            "published_at": article.published_at,
            "summary": article.description,
        }
        for article in articles
    ]
    confidence = round(0.5 + min(len(sources), 4) * 0.1, 2)
    return {
        "status": "ok",
        "verdict": "inconclusive",
        "confidence": confidence,
        "supporting_sources": sources,
        "articles": article_details,
        "synopsis": _build_synopsis(articles),
    }


NEWS_API_TOOL = FunctionTool(func=fetch_news_evidence)
