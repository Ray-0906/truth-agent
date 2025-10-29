"""Client utilities for interacting with the Perplexity API."""

from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass
from typing import Any, Iterable, Optional

import requests

PERPLEXITY_API_URL = "https://api.perplexity.ai/chat/completions"


class PerplexityClientError(RuntimeError):
    """Raised when the Perplexity API returns an error response."""


@dataclass(frozen=True)
class PerplexitySearchResult:
    """Represents a search result returned by Perplexity."""

    title: str
    url: str
    snippet: Optional[str]
    published: Optional[str]


@dataclass(frozen=True)
class PerplexityResponse:
    """Structured completion payload returned from Perplexity."""

    message: str
    search_results: list[PerplexitySearchResult]
    token_usage: dict[str, Any]


_JSON_PATTERN = re.compile(r"\{.*\}", re.DOTALL)


def _extract_json(content: str) -> str:
    """Extract a JSON object from the model response."""
    match = _JSON_PATTERN.search(content)
    if not match:
        raise PerplexityClientError("Perplexity response did not contain JSON payload.")
    return match.group(0)


def _coerce_search_results(raw: Optional[Iterable[dict[str, Any]]]) -> list[PerplexitySearchResult]:
    if not raw:
        return []
    results: list[PerplexitySearchResult] = []
    for entry in raw:
        url = (entry or {}).get("url") or ""
        if not url:
            continue
        results.append(
            PerplexitySearchResult(
                title=(entry.get("title") or "").strip(),
                url=url.strip(),
                snippet=(entry.get("snippet") or entry.get("highlight")),
                published=entry.get("date") or entry.get("published_at"),
            )
        )
    return results


def _build_headers(api_key: str) -> dict[str, str]:
    return {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }


def _post_payload(payload: dict[str, Any], *, timeout: int = 30) -> dict[str, Any]:
    api_key = os.getenv("PERPLEXITY_API_KEY")
    if not api_key:
        raise PerplexityClientError("PERPLEXITY_API_KEY environment variable is not configured.")

    try:
        response = requests.post(
            PERPLEXITY_API_URL,
            headers=_build_headers(api_key),
            json=payload,
            timeout=timeout,
        )
    except requests.RequestException as exc:  # pragma: no cover - network error handling
        raise PerplexityClientError(str(exc)) from exc

    if response.status_code != requests.codes.ok:
        raise PerplexityClientError(f"HTTP {response.status_code}: {response.text}")

    return response.json()


def complete_json(
    *,
    user_prompt: str,
    schema_description: str,
    system_prompt: str,
    model: str = "sonar-pro",
    temperature: float = 0.1,
    max_tokens: int = 800,
) -> tuple[dict[str, Any], PerplexityResponse]:
    """Request a JSON-formatted completion from Perplexity.

    Returns a tuple of the parsed JSON payload defined by the schema description and
    the raw Perplexity response metadata.
    """
    system_directive = (
        "You are a meticulous research assistant. Respond ONLY with a JSON object that conforms to "
        "the provided schema. Do not include code fences, prose, or explanations outside the JSON."
    )
    if system_prompt:
        system_directive += "\n" + system_prompt.strip()
    if schema_description:
        system_directive += "\nSchema:\n" + schema_description.strip()

    payload = {
        "model": model,
        "messages": [
            {
                "role": "system",
                "content": system_directive,
            },
            {"role": "user", "content": user_prompt},
        ],
        "temperature": temperature,
        "top_p": 0.8,
        "max_tokens": max_tokens,
        "search_mode": "web",
        "return_related_questions": False,
        "return_images": False,
    }

    raw = _post_payload(payload)
    choices = raw.get("choices") or []
    if not choices:
        raise PerplexityClientError("Perplexity response did not include choices.")

    message_content = choices[0].get("message", {}).get("content", "")
    json_payload = json.loads(_extract_json(message_content))

    response = PerplexityResponse(
        message=message_content,
        search_results=_coerce_search_results(raw.get("search_results")),
        token_usage=raw.get("usage", {}),
    )
    return json_payload, response