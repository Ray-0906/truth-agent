"""Tools for evaluating URLs against VirusTotal."""

from __future__ import annotations

import os
from typing import Any

from google.adk.tools import FunctionTool
from google.adk.tools import ToolContext

from ..services import context_helpers, text_utils, virustotal_client


def _risk_level(report: virustotal_client.VirusTotalUrlReport) -> str:
    if report.malicious > 0:
        return "high"
    if report.suspicious > 0:
        return "medium"
    return "low"


def _confidence(level: str) -> float:
    return {"low": 0.4, "medium": 0.65, "high": 0.9}[level]


def _recommendation(level: str) -> str:
    if level == "high":
        return "Block the link and escalate to security for manual review."
    if level == "medium":
        return "Treat with caution; validate in a sandbox before opening."
    return "No malicious verdicts detected; continue to monitor."


def _format_issue(report: virustotal_client.VirusTotalUrlReport) -> str:
    parts: list[str] = []
    if report.malicious:
        parts.append(f"{report.malicious} engines flagged malicious")
    if report.suspicious:
        parts.append(f"{report.suspicious} engines flagged suspicious")
    if report.timeout:
        parts.append(f"{report.timeout} engines timed out")
    if not parts:
        parts.append("No engines flagged the URL")
    return ", ".join(parts)


def scan_urls_with_virustotal(
    claim: str, *, tool_context: ToolContext
) -> dict[str, Any]:
    """Check up to five URLs in the claim text against VirusTotal and return risk annotations."""
    text = claim or context_helpers.extract_latest_user_text(tool_context)
    urls = text_utils.extract_urls(text)
    api_key = os.getenv("VT_API_KEY")

    if not urls:
        return {
            "status": "no_data",
            "risk_level": "low",
            "confidence": 0.0,
            "flagged_urls": [],
            "recommended_action": "No URLs were provided in the submission.",
        }

    if not api_key:
        return {
            "status": "error",
            "risk_level": "medium",
            "confidence": 0.0,
            "flagged_urls": [],
            "recommended_action": "VT_API_KEY environment variable is missing.",
        }

    issues: list[dict[str, str]] = []
    highest_level = "low"

    for url in urls[:5]:
        try:
            report = virustotal_client.fetch_url_report(url=url, api_key=api_key)
            level = _risk_level(report)
            if level == "high" or (level == "medium" and highest_level == "low"):
                highest_level = level
            issues.append(
                {
                    "url": url,
                    "issue": _format_issue(report),
                    "recommendation": _recommendation(level),
                }
            )
        except virustotal_client.VirusTotalClientError as exc:
            issues.append(
                {
                    "url": url,
                    "issue": f"Lookup failed: {exc}",
                    "recommendation": "Fallback to manual scanning before trusting this link.",
                }
            )
            if highest_level == "low":
                highest_level = "medium"

    return {
        "status": "ok",
        "risk_level": highest_level,
        "confidence": round(_confidence(highest_level), 2),
        "flagged_urls": issues,
        "recommended_action": _recommendation(highest_level),
    }


VIRUSTOTAL_URL_TOOL = FunctionTool(func=scan_urls_with_virustotal)
