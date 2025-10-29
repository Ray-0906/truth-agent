"""Merge agent for the Scam detection lane."""

from __future__ import annotations

from google.adk.agents.llm_agent import LlmAgent

from ...config import MODEL, STATE_KEYS


def create_scam_merge_agent(model: str = MODEL) -> LlmAgent:
    """Builds the agent that consolidates scam detection signals."""

    return LlmAgent(
        name="ScamMergeAgent",
        model=model,
        description="Combines scam signals into a consolidated risk assessment.",
        instruction=(
            f"Fuse the structured results in state[{STATE_KEYS.SCAM_SENTIMENT!r}], state[{STATE_KEYS.SCAM_PERPLEXITY!r}], and "
            f"state[{STATE_KEYS.SCAM_LINK!r}]. Preserve any error messages by surfacing them before conclusions.\n\n"
            "Output Markdown:\n"
            "## Scam Risk Summary\n"
            "- overall_risk: <low|medium|high|unknown>\n"
            "- confidence_range: <min-max>\n"
            "- immediate_action_required: <yes|no>\n\n"
            "### Triggers\n"
            "* <Trigger from sentiment>\n"
            "* <Trigger from pattern match or link audit>\n\n"
            "### Recommended Actions\n"
        "* <Action 1>\n"
        "* <Action 2>.\n\n"
        "### Sources\n"
        "1. <Signal — URL or descriptor>\n"
        "Enumerate any links returned by the link audit tool and keep the full URL path for fidelity."
        ),
        output_key=STATE_KEYS.SCAM_SUMMARY,
    )
