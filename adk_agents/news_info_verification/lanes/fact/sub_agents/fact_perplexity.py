"""Agent definition for the FactPerplexityAgent."""

from __future__ import annotations

from google.adk.agents.llm_agent import LlmAgent

from ....config import MODEL, STATE_KEYS
from ....tools import FACT_PERPLEXITY_TOOL


fact_perplexity_agent = LlmAgent(
    name="FactPerplexityAgent",
    model=MODEL,
    description="Performs reasoning over open web evidence to validate factual statements.",
    instruction=(
        "Call the research_fact_with_perplexity tool using the current claim text. The tool returns JSON with status, "
        "verdict, confidence, reasoning, and references. Relay the payload exactly without rewriting or summarizing it "
        "yourself."
    ),
    tools=[FACT_PERPLEXITY_TOOL],
    output_key=STATE_KEYS.FACT_PERPLEXITY,
)


__all__ = ["fact_perplexity_agent"]
