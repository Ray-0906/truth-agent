"""Tools for querying official fact-check registries."""

from __future__ import annotations

import os
from typing import Any

from google.adk.tools import FunctionTool
from google.adk.tools import ToolContext

from ..services import context_helpers, factcheck_client, text_utils


_RATING_FALSE_KEYWORDS = {"false", "pants on fire", "fiction", "fake", "incorrect", "scam"}
_RATING_TRUE_KEYWORDS = {"true", "accurate", "legit", "correct", "verified"}


def _map_rating_to_verdict(rating: str) -> str:
    label = rating.lower()
    if any(token in label for token in _RATING_FALSE_KEYWORDS):
        return "false"
    if any(token in label for token in _RATING_TRUE_KEYWORDS):
        return "true"
    return "inconclusive"


def _aggregate_verdict(reviews: list[factcheck_client.FactCheckReview]) -> str:
    totals = {"true": 0, "false": 0, "inconclusive": 0}
    for review in reviews:
        totals[_map_rating_to_verdict(review.textual_rating)] += 1
    if totals["false"] > totals["true"] and totals["false"]:
        return "false"
    if totals["true"] > totals["false"] and totals["true"]:
        return "true"
    return "inconclusive"


def _summarize_reviews(reviews: list[factcheck_client.FactCheckReview]) -> str:
    sentences: list[str] = []
    for review in reviews[:2]:
        rating = review.textual_rating or "Unrated"
        publisher = review.publisher or "Unknown organization"
        title = review.title or review.claim_text
        sentences.append(f"{publisher} rated '{title}' as {rating}.")
    return text_utils.truncate_sentences(sentences, limit=240)


def lookup_fact_checks(
    claim: str, *, tool_context: ToolContext
) -> dict[str, Any]:
    """Query Google Fact Check Tools for reviews addressing the given claim."""
    query = claim or context_helpers.extract_latest_user_text(tool_context)
    api_key = os.getenv("GOOGLE_FACT_CHECK_API_KEY")

    if not query:
        return {
            "status": "error",
            "verdict": "inconclusive",
            "confidence": 0.0,
            "fact_checks": [],
            "notes": "No claim text was supplied for fact-check lookup.",
        }

    if not api_key:
        return {
            "status": "error",
            "verdict": "inconclusive",
            "confidence": 0.0,
            "fact_checks": [],
            "notes": "GOOGLE_FACT_CHECK_API_KEY environment variable is not configured.",
        }

    try:
        reviews = factcheck_client.search_fact_checks(query=query, api_key=api_key, max_results=6)
    except factcheck_client.FactCheckClientError as exc:
        return {
            "status": "error",
            "verdict": "inconclusive",
            "confidence": 0.0,
            "fact_checks": [],
            "notes": f"Fact Check API failure: {exc}",
        }

    if not reviews:
        return {
            "status": "no_data",
            "verdict": "inconclusive",
            "confidence": 0.2,
            "fact_checks": [],
            "notes": "No fact-check entries matched the submitted claim.",
        }

    fact_checks = [
        {
            "organization": review.publisher or "Unknown",
            "url": review.url,
            "snippet": review.summary or review.claim_text,
            "rating": review.textual_rating or "Unrated",
        }
        for review in reviews
    ]

    verdict = _aggregate_verdict(reviews)
    confidence = round(0.6 + min(len(reviews), 5) * 0.05, 2)
    return {
        "status": "ok",
        "verdict": verdict,
        "confidence": confidence,
        "fact_checks": fact_checks,
        "notes": _summarize_reviews(reviews),
    }


FACT_CHECK_TOOL = FunctionTool(func=lookup_fact_checks)
