"""Final report aggregation agent."""

from __future__ import annotations

from google.adk.agents.llm_agent import LlmAgent

from ..config import MODEL, STATE_KEYS


def create_final_report_agent(model: str = MODEL) -> LlmAgent:
    """Construct the final processing agent that assembles the full report."""

    return LlmAgent(
        name="FinalProcessingAgent",
        model=model,
        description="Generates the final consolidated verification report.",
        instruction=(
            f"You are the final editor. Consume the lane summaries located in state[{STATE_KEYS.NEWS_SUMMARY!r}], "
            f"state[{STATE_KEYS.FACT_SUMMARY!r}], and state[{STATE_KEYS.SCAM_SUMMARY!r}]. Maintain their intent, especially "
            "when a lane surfaced an error or data gap.\n\n"
            "Bundle outputs by reusing their Markdown whenever possible. If a lane summary string is empty or missing, treat the"
            " lane as 'not requested'. Extract existing bullet lists and sources verbatim rather than rephrasing; this keeps"
            " traceability back to the tool output. Use those lane verdicts and confidences to populate the Report Summary"
            " section so it accurately reflects downstream content.\n\n"
            "Your response MUST match the exact Markdown skeleton below. Do not add extra prose before or after any heading."
            " Populate each placeholder with concrete values; if information is unavailable, write 'not requested' or 'none'.\n"
            "# Verification Report\n"
            "## Report Summary\n"
            "<Single paragraph of 1-3 sentences describing the overall verdict, confidence, key evidence or gaps, and any skipped lanes.>\n\n"
            "## Claim Overview\n"
            "- paraphrase: <20-40 word restatement of the user claim>\n"
            "- submission_time: <use session timestamp if available, otherwise 'unspecified'>\n\n"
            "## News Assessment\n"
            "- summary: <lane findings or 'not requested'>\n"
            "- confidence: <float or range from news lane>\n"
            "- sources:\n"
            "  * <Outlet - URL or 'none'>\n\n"
            "## Fact Assessment\n"
            "- summary: <lane findings or 'not requested'>\n"
            "- confidence: <float or range from fact lane>\n"
            "- sources:\n"
            "  * <Organization - URL or 'none'>\n\n"
            "## Scam Risk\n"
            "- summary: <lane findings or 'not requested'>\n"
            "- confidence: <float or range from scam lane>\n"
            "- sources:\n"
            "  * <Signal description - URL or 'n/a'>\n\n"
            "## Lane Execution\n"
            "- executed: <comma separated list of lanes whose summaries are populated>\n"
            "- skipped: <comma separated list with reason or 'none'>\n\n"
            "## Final Verdict\n"
            "- outcome: <true|false|mixed|unknown>\n"
            "- confidence: <float or range>\n"
            "- residual_risks:\n"
            "  * <bullet list citing underlying lanes or 'none'>\n\n"
            "## Sources\n"
            "1. <Source name — URL>\n"
            "List each unique source exactly once, preserving full URLs. Do not invent new evidence or alter lane text."
        ),
        output_key=STATE_KEYS.FINAL_REPORT,
    )
