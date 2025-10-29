"""Factory for the NewsPerplexityAgent."""

from __future__ import annotations

from google.adk.agents.llm_agent import LlmAgent

from ....config import MODEL, STATE_KEYS
from ....tools import NEWS_PERPLEXITY_TOOL


news_perplexity_agent = LlmAgent(
    name="NewsPerplexityAgent",
    model=MODEL,
    description="Performs retrieval-augmented reasoning to spot inconsistencies in news content.",
    instruction=(
        "Call the research_news_with_perplexity tool with the current claim text. The tool returns structured JSON "
        "containing status, verdict, confidence, reasoning_bullets, and citations. Do not alter the payload—return it "
        "verbatim as your final response."
    ),
    tools=[NEWS_PERPLEXITY_TOOL],
    output_key=STATE_KEYS.NEWS_PERPLEXITY,
)


__all__ = ["news_perplexity_agent"]
