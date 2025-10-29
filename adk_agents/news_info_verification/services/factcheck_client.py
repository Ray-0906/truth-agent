"""Client for the Google Fact Check Tools API."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

import requests

API_URL = "https://factchecktools.googleapis.com/v1alpha1/claims:search"


class FactCheckClientError(RuntimeError):
    """Raised when the Fact Check API request fails."""


@dataclass(frozen=True)
class FactCheckReview:
    """Normalized fact-check review details."""

    claim_text: str
    publisher: str
    url: str
    title: str
    textual_rating: str
    summary: str
    review_date: Optional[str]


def search_fact_checks(query: str, api_key: str, *, max_results: int = 6) -> list[FactCheckReview]:
    """Search for fact checks matching the provided query."""
    params = {
        "key": api_key,
        "languageCode": "en-US",
        "pageSize": max(1, min(max_results, 10)),
        "query": query,
    }

    try:
        response = requests.get(API_URL, params=params, timeout=10)
    except requests.RequestException as exc:  # pragma: no cover - network error handling
        raise FactCheckClientError(str(exc)) from exc

    if response.status_code != requests.codes.ok:
        raise FactCheckClientError(f"HTTP {response.status_code}: {response.text}")

    data = response.json()
    claims = data.get("claims") or []
    reviews: list[FactCheckReview] = []

    for claim in claims:
        claim_text = (claim.get("text") or "").strip()
        for review in claim.get("claimReview") or []:
            publisher = (review.get("publisher") or {}).get("name") or "Unknown"
            url = (review.get("url") or "").strip()
            title = (review.get("title") or "").strip() or claim_text
            textual_rating = (review.get("textualRating") or "").strip()
            summary = (review.get("text") or "").strip()
            review_date = review.get("reviewDate")
            reviews.append(
                FactCheckReview(
                    claim_text=claim_text,
                    publisher=publisher,
                    url=url,
                    title=title,
                    textual_rating=textual_rating,
                    summary=summary,
                    review_date=review_date,
                )
            )
    return reviews[: params["pageSize"]]
