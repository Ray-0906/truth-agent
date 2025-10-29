"""Agent definition for the FactPrimaryAgent."""

from __future__ import annotations

from google.adk.agents.llm_agent import LlmAgent

from ....config import MODEL, STATE_KEYS
from ....tools import FACT_CHECK_TOOL


fact_primary_agent = LlmAgent(
    name="FactPrimaryAgent",
    model=MODEL,
    description="Queries official fact-check APIs for claim verdicts.",
    instruction=(
        "Call the lookup_fact_checks tool with the current claim text to retrieve authoritative reviews."
        " When the tool responds, return its JSON payload without modification."
        " Do not synthesize new ratings or notes."
    ),
    tools=[FACT_CHECK_TOOL],
    output_key=STATE_KEYS.FACT_PRIMARY,
)


__all__ = ["fact_primary_agent"]
