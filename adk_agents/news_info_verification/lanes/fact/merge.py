"""Merge agent for the Fact verification lane."""

from __future__ import annotations

from google.adk.agents.llm_agent import LlmAgent

from ...config import MODEL, STATE_KEYS


fact_merge_agent = LlmAgent(
    name="FactMergeAgent",
    model=MODEL,
    description="Consolidates fact-check signals into a unified assessment.",
    instruction=(
        f"You receive structured JSON from state[{STATE_KEYS.FACT_PRIMARY!r}] and state[{STATE_KEYS.FACT_PERPLEXITY!r}]. "
        "Treat them as authoritative evidence packets—quote their status fields when relevant and never overwrite a reported "
        "error.\n\n"
        "Output Markdown:\n"
        "## Fact Verification\n"
        "- consensus_verdict: <true|false|mixed|unknown>\n"
        "- confidence_range: <min-max>\n"
        "- registry_alignment: <matches|conflicts|no_data>\n\n"
        "### Key Evidence\n"
        "* <Combine fact_primary + index references>\n"
        "* <Highlight gaps if any>\n\n"
    "### References\n"
    "1. <Organization — URL>\n"
    "2. <Title — URL>\n"
    "Maintain consistent numbering with the upstream references arrays. Keep the full URL strings from the input JSON"
    " so downstream reports link to the exact ruling page."
    ),
    output_key=STATE_KEYS.FACT_SUMMARY,
)


__all__ = ["fact_merge_agent"]
