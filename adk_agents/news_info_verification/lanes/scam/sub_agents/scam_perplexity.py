"""Factory for the ScamPerplexityAgent."""

from __future__ import annotations

from google.adk.agents.llm_agent import LlmAgent

from ....config import MODEL, STATE_KEYS
from ....tools import SCAM_PERPLEXITY_TOOL


def create_scam_perplexity_agent(model: str = MODEL) -> LlmAgent:
    """Builds the agent that compares the content against known scam patterns."""

    return LlmAgent(
        name="ScamPerplexityAgent",
        model=model,
        description="Compares the content against known scam patterns via retrieval reasoning.",
        instruction=(
            "Compare the claim and any embedded instructions/links against known scam signatures (advance-fee fraud, "
            "account suspension phishing, lottery scams, malware delivery). Emphasize similarities and differences explicitly.\n\n"
            "Call the research_scam_with_perplexity tool with the current message text. The tool performs retrieval against "
            "scam pattern documentation and returns JSON including status, verdict, confidence, pattern_matches, and "
            "supporting_citations. Return the JSON payload exactly as received."
        ),
        tools=[SCAM_PERPLEXITY_TOOL],
        output_key=STATE_KEYS.SCAM_PERPLEXITY,
    )
