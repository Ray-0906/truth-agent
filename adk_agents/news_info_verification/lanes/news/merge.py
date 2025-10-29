"""Merge agent for the News lane."""

from __future__ import annotations

from google.adk.agents.llm_agent import LlmAgent

from ...config import MODEL, STATE_KEYS


news_merge_agent = LlmAgent(
    name="NewsMergeAgent",
    model=MODEL,
    description="Synthesizes the news verification outputs into a single verdict.",
    instruction=(
        f"You consolidate the outputs in state[{STATE_KEYS.NEWS_API!r}], state[{STATE_KEYS.NEWS_FACT!r}], and "
        f"state[{STATE_KEYS.NEWS_PERPLEXITY!r}]. Trust the JSON fields they expose—do not invent new evidence. If any agent "
        "returned status 'error', surface it verbatim before drawing conclusions.\n\n"
    "Produce Markdown with this template so downstream agents can parse it reliably:\n"
    "## News Verification\n"
    "- consensus_verdict: <true|false|mixed|unknown>\n"
    "- confidence_range: <min-max>\n"
    "- noted_gaps: <short sentence or 'none'>\n\n"
    "### Supporting Points\n"
    "* <Point 1 citing agent and source>\n"
    "* <Point 2>\n\n"
    "### Sources\n"
    "1. <Outlet — URL>\n"
    "2. <Outlet — URL>\n"
    "Deduplicate sources and call out disagreements explicitly. Preserve the exact URL strings provided by upstream"
    " agents—do not shorten them to domains or rewrite them."
    ),
    output_key=STATE_KEYS.NEWS_SUMMARY,
)


__all__ = ["news_merge_agent"]
