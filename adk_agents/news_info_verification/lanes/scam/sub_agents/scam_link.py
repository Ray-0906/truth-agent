"""Factory for the MaliciousLinkAgent."""

from __future__ import annotations

from google.adk.agents.llm_agent import LlmAgent

from ....config import MODEL, STATE_KEYS
from ....tools import VIRUSTOTAL_URL_TOOL


def create_scam_link_agent(model: str = MODEL) -> LlmAgent:
    """Build the agent that evaluates links for malicious signals via VirusTotal."""

    return LlmAgent(
        name="MaliciousLinkAgent",
        model=model,
        description="Evaluates links for malicious or suspicious signals using VirusTotal.",
        instruction=(
            "Use the scan_urls_with_virustotal tool to inspect URLs mentioned in the claim."
            " Return the JSON object produced by the tool without altering any fields."
        ),
        tools=[VIRUSTOTAL_URL_TOOL],
        output_key=STATE_KEYS.SCAM_LINK,
    )
