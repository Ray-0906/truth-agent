"""FunctionTools that wrap Perplexity API research calls."""

from __future__ import annotations

import math
from typing import Any

from google.adk.tools import FunctionTool, ToolContext

from ..services import context_helpers, perplexity_client, text_utils


def _fallback_confidence(num_sources: int, default: float = 0.5) -> float:
    if num_sources <= 0:
        return default
    return round(min(0.9, default + num_sources * 0.1), 2)


def _citations_from_results(results: list[perplexity_client.PerplexitySearchResult]) -> list[str]:
    citations: list[str] = []
    for item in results:
        label = item.title or item.url
        citations.append(f"{label} — {item.url}")
    return citations


def _references_from_results(results: list[perplexity_client.PerplexitySearchResult]) -> list[dict[str, str]]:
    references: list[dict[str, str]] = []
    for idx, item in enumerate(results, start=1):
        references.append(
            {
                "title": item.title or f"Source {idx}",
                "url": item.url,
                "published": item.published or "unspecified",
                "snippet": item.snippet or "",
            }
        )
    return references


def _safe_confidence(value: Any, fallback: float) -> float:
    try:
        numeric = float(value)
    except (TypeError, ValueError):
        return fallback
    if math.isnan(numeric):
        return fallback
    return round(max(0.0, min(1.0, numeric)), 2)


def research_news_with_perplexity(claim: str, *, tool_context: ToolContext) -> dict[str, Any]:
    """Investigate a breaking news claim using Perplexity's web-grounded research."""

    query = claim or context_helpers.extract_latest_user_text(tool_context)
    if not query:
        return {
            "status": "error",
            "verdict": "unknown",
            "confidence": 0.0,
            "reasoning_bullets": [],
            "citations": [],
            "notes": "No claim text provided for Perplexity research.",
        }

    schema = (
        "{"
        '"status": "ok" | "no_data" | "error", '
        '"verdict": "true" | "false" | "mixed" | "unknown", '
        '"confidence": number, "reasoning_bullets": string[], "citations": string[], '
        '"notes": string'
        "}"
    )
    system = (
        "Assess the accuracy of a reported news event using real-time search. "
        "Summarize converging or conflicting coverage, prioritizing reputable outlets." \
        " Confidence should rise with multiple corroborating sources and fall with disagreements."
    )

    try:
        payload, response = perplexity_client.complete_json(
            user_prompt=(
                "You must decide whether this news claim is supported by current reporting. "
                "Focus on concrete details like who, what, when, and where.\n\nClaim: " + query
            ),
            schema_description=schema,
            system_prompt=system,
            max_tokens=900,
        )
    except perplexity_client.PerplexityClientError as exc:
        return {
            "status": "error",
            "verdict": "unknown",
            "confidence": 0.0,
            "reasoning_bullets": [],
            "citations": [],
            "notes": f"Perplexity request failed: {exc}",
        }

    citations = payload.get("citations") or []
    if not citations:
        citations = _citations_from_results(response.search_results)

    confidence = _safe_confidence(payload.get("confidence"), _fallback_confidence(len(citations)))

    return {
        "status": payload.get("status", "ok"),
        "verdict": payload.get("verdict", "unknown"),
        "confidence": confidence,
        "reasoning_bullets": payload.get("reasoning_bullets") or text_utils.truncate_sentences(
            [payload.get("notes", "")], limit=200
        ).split("\n"),
        "citations": citations,
        "notes": payload.get("notes", ""),
        "token_usage": response.token_usage,
    }


def research_fact_with_perplexity(claim: str, *, tool_context: ToolContext) -> dict[str, Any]:
    """Cross-check factual statements against authoritative references."""

    query = claim or context_helpers.extract_latest_user_text(tool_context)
    if not query:
        return {
            "status": "error",
            "verdict": "unknown",
            "confidence": 0.0,
            "reasoning": [],
            "references": [],
            "notes": "No claim text provided for Perplexity fact research.",
        }

    schema = (
        "{"
        '"status": "ok" | "no_data" | "error", '
        '"verdict": "true" | "false" | "mixed" | "unknown", '
        '"confidence": number, "reasoning": string[], '
        '"references": [{"title": string, "url": string, "published": string}], '
        '"notes": string'
        "}"
    )
    system = (
        "Validate the factual accuracy of the claim using authoritative and primary sources. "
        "When evidence conflicts, mark the verdict as mixed and explain each side succinctly. "
        "Return references with full URLs."
    )

    try:
        payload, response = perplexity_client.complete_json(
            user_prompt=(
                "Evaluate this factual assertion. Highlight corroborating or conflicting evidence and prefer primary sources.\n\n"
                "Claim: " + query
            ),
            schema_description=schema,
            system_prompt=system,
            max_tokens=900,
        )
    except perplexity_client.PerplexityClientError as exc:
        return {
            "status": "error",
            "verdict": "unknown",
            "confidence": 0.0,
            "reasoning": [],
            "references": [],
            "notes": f"Perplexity request failed: {exc}",
        }

    references = payload.get("references") or _references_from_results(response.search_results)
    confidence = _safe_confidence(payload.get("confidence"), _fallback_confidence(len(references)))

    reasoning = payload.get("reasoning")
    if not reasoning:
        summary = payload.get("notes") or "Perplexity summary unavailable."
        reasoning = text_utils.split_sentences(summary)[:3]

    return {
        "status": payload.get("status", "ok"),
        "verdict": payload.get("verdict", "unknown"),
        "confidence": confidence,
        "reasoning": reasoning,
        "references": references,
        "notes": payload.get("notes", ""),
        "token_usage": response.token_usage,
    }


def research_scam_with_perplexity(claim: str, *, tool_context: ToolContext) -> dict[str, Any]:
    """Compare the claim against known scam patterns using Perplexity."""

    query = claim or context_helpers.extract_latest_user_text(tool_context)
    if not query:
        return {
            "status": "error",
            "verdict": "unclear",
            "confidence": 0.0,
            "pattern_matches": [],
            "supporting_citations": [],
            "notes": "No message text provided for scam analysis.",
        }

    schema = (
        "{"
        '"status": "ok" | "no_match" | "error", '
        '"verdict": "likely_scam" | "unclear" | "benign", '
        '"confidence": number, '
        '"pattern_matches": [{"pattern": string, "explanation": string}], '
        '"supporting_citations": string[], '
        '"notes": string'
        "}"
    )
    system = (
        "Identify whether the message resembles common scam archetypes (phishing, advance-fee fraud, account suspension, "
        "investment fraud). Focus on red flags like urgency, payment requests, and suspicious links."
    )

    try:
        payload, response = perplexity_client.complete_json(
            user_prompt=(
                "Analyse this message for scam indicators. Explain any matching patterns succinctly and cite reputable "
                "sources that describe similar scams.\n\nMessage: " + query
            ),
            schema_description=schema,
            system_prompt=system,
            max_tokens=750,
        )
    except perplexity_client.PerplexityClientError as exc:
        return {
            "status": "error",
            "verdict": "unclear",
            "confidence": 0.0,
            "pattern_matches": [],
            "supporting_citations": [],
            "notes": f"Perplexity request failed: {exc}",
        }

    citations = payload.get("supporting_citations") or _citations_from_results(response.search_results)
    confidence = _safe_confidence(payload.get("confidence"), _fallback_confidence(len(citations), default=0.4))

    return {
        "status": payload.get("status", "ok"),
        "verdict": payload.get("verdict", "unclear"),
        "confidence": confidence,
        "pattern_matches": payload.get("pattern_matches") or [],
        "supporting_citations": citations,
        "notes": payload.get("notes", ""),
        "token_usage": response.token_usage,
    }


NEWS_PERPLEXITY_TOOL = FunctionTool(func=research_news_with_perplexity)
FACT_PERPLEXITY_TOOL = FunctionTool(func=research_fact_with_perplexity)
SCAM_PERPLEXITY_TOOL = FunctionTool(func=research_scam_with_perplexity)


__all__ = [
    "NEWS_PERPLEXITY_TOOL",
    "FACT_PERPLEXITY_TOOL",
    "SCAM_PERPLEXITY_TOOL",
]
