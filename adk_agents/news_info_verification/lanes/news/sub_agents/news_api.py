"""Agent definition for the NewsApiAgent."""

from __future__ import annotations

from google.adk.agents.llm_agent import LlmAgent

from ....config import MODEL, STATE_KEYS
from ....tools import NEWS_API_TOOL


news_api_agent = LlmAgent(
    name="NewsApiAgent",
    model=MODEL,
    description="Queries licensed news APIs and normalizes evidence for the claim.",
    instruction=(
        "Call the fetch_news_evidence tool with the current claim text to gather coverage."
        " When the tool returns, respond with its JSON payload verbatim."
        " Do not fabricate fields or alter confidence values."
    ),
    tools=[NEWS_API_TOOL],
    output_key=STATE_KEYS.NEWS_API,
)


__all__ = ["news_api_agent"]
