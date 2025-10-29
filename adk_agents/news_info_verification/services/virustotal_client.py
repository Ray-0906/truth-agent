"""Client utilities for the VirusTotal v3 API."""

from __future__ import annotations

import base64
from dataclasses import dataclass
from typing import Optional

import requests

API_URL = "https://www.virustotal.com/api/v3/urls"


class VirusTotalClientError(RuntimeError):
    """Raised when the VirusTotal API call fails."""


@dataclass(frozen=True)
class VirusTotalUrlReport:
    """Normalized VirusTotal URL intelligence snapshot."""

    url: str
    harmless: int
    malicious: int
    suspicious: int
    undetected: int
    timeout: int
    last_analysis_date: Optional[int]


def _url_id(url: str) -> str:
    """Encode a URL using URL-safe base64 without padding."""
    encoded = base64.urlsafe_b64encode(url.encode("utf-8"))
    return encoded.decode("ascii").strip("=")


def fetch_url_report(url: str, api_key: str) -> VirusTotalUrlReport:
    """Fetch the latest VirusTotal verdict summary for a URL."""
    url_identifier = _url_id(url)
    headers = {"x-apikey": api_key}

    try:
        response = requests.get(f"{API_URL}/{url_identifier}", headers=headers, timeout=10)
    except requests.RequestException as exc:  # pragma: no cover - network error handling
        raise VirusTotalClientError(str(exc)) from exc

    if response.status_code == requests.codes.not_found:
        raise VirusTotalClientError("No VirusTotal record for URL")

    if response.status_code != requests.codes.ok:
        raise VirusTotalClientError(f"HTTP {response.status_code}: {response.text}")

    data = response.json().get("data") or {}
    attributes = data.get("attributes") or {}
    stats = attributes.get("last_analysis_stats") or {}

    return VirusTotalUrlReport(
        url=url,
        harmless=int(stats.get("harmless", 0)),
        malicious=int(stats.get("malicious", 0)),
        suspicious=int(stats.get("suspicious", 0)),
        undetected=int(stats.get("undetected", 0)),
        timeout=int(stats.get("timeout", 0)),
        last_analysis_date=attributes.get("last_analysis_date"),
    )
