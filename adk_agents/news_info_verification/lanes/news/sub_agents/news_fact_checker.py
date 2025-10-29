"""Agent definition for the NewsFactCheckerAgent."""

from __future__ import annotations

from google.adk.agents.llm_agent import LlmAgent

from ....config import MODEL, STATE_KEYS
from ....tools import FACT_CHECK_TOOL


news_fact_checker_agent = LlmAgent(
    name="NewsFactCheckerAgent",
    model=MODEL,
    description="Leverages official fact-checking feeds for news-specific validation.",
    instruction=(
        "Call the lookup_fact_checks tool with the current claim text to retrieve official verdicts relevant to the news"
        " claim. Do not guess at the schema; rely entirely on the JSON payload returned by the tool. After receiving the"
        " tool result, echo that JSON verbatim, without additional commentary or formatting."
    ),
    tools=[FACT_CHECK_TOOL],
    output_key=STATE_KEYS.NEWS_FACT,
)


__all__ = ["news_fact_checker_agent"]
