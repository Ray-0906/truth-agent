"""Root routing agent that wires all sub-agents together."""

from __future__ import annotations

from typing import Any, Dict

from google.adk.agents.llm_agent import LlmAgent
from google.adk.tools.agent_tool import AgentTool


class NormalizedAgentTool(AgentTool):
    """AgentTool variant that tolerates nested request arguments."""

    @staticmethod
    def _extract_request(args: Any) -> str:
        if isinstance(args, dict):
            candidate = args.get("request")
            if isinstance(candidate, dict):
                for key in ("request", "claim", "text", "content"):
                    value = candidate.get(key)
                    if isinstance(value, str) and value.strip():
                        return value.strip()
                return str(candidate)
            if isinstance(candidate, str):
                return candidate
            if candidate is not None:
                return str(candidate)

            for key in ("claim", "text", "content"):
                value = args.get(key)
                if isinstance(value, str) and value.strip():
                    return value.strip()
                if value is not None:
                    return str(value)
            return ""

        if isinstance(args, str):
            return args
        if args is None:
            return ""
        return str(args)

    @classmethod
    def _normalize_args(cls, args: Any) -> Dict[str, str]:
        request = cls._extract_request(args)
        return {"request": request}

    async def run_async(self, *, args: Any, tool_context) -> Any:  # type: ignore[override]
        normalized = self._normalize_args(args)
        return await super().run_async(args=normalized, tool_context=tool_context)


class FinalReportAgentTool(NormalizedAgentTool):
    """AgentTool wrapper that avoids recomputing the final report."""

    async def run_async(self, *, args: Any, tool_context) -> Any:  # type: ignore[override]
        existing = tool_context.session.state.get(STATE_KEYS.FINAL_REPORT)
        if existing:
            return existing
        return await super().run_async(args=args, tool_context=tool_context)

from .config import MODEL, STATE_KEYS
from .lanes import fact_check_agent, news_check_agent, create_scam_check_agent
from .reporting import create_final_report_agent

news_lane_agent = news_check_agent
fact_lane_agent = fact_check_agent
scam_lane_agent = create_scam_check_agent(model=MODEL)
final_report_agent = create_final_report_agent(model=MODEL)

root_agent = LlmAgent(
        name="news_info_verification",
        model=MODEL,
        description="Routes incoming content to the appropriate verification sub-agents and returns the final report.",
        instruction=(
            "You triage every submission. Execute the checklist in order:\n"
            "1. Read the latest user message and gather any lane summaries already in session.state.\n"
            "2. Classify the submission into these intents (multiple may apply):\n"
            "   - 'news' if the user claims breaking news or cites media coverage.\n"
            "   - 'fact' if the user asserts or questions a factual statement needing confirmation.\n"
            "   - 'scam' if the message references links, payments, fraud, phishing, or suspicious outreach.\n"
            "3. For each selected intent, immediately call the matching tool by name (NewsCheckAgent, FactCheckAgent, "
            "ScamCheckAgent). Always invoke the tool with a JSON argument shaped exactly as {\"request\": \"<plain text>\"} "
            "where the request string is the user claim you want that lane to analyse. Do not pass nested JSON, prior lane "
            "outputs, or additional fields.\n"
            "4. If an intent does not apply, document the reason (e.g., 'no URLs provided' for scam) for later reporting.\n"
            "5. Once all chosen lanes finish, invoke FinalProcessingAgent exactly once using {\"request\": \"summarize\"} to build the final Markdown. Do not call it again if state already contains the final report.\n"
            f"6. After FinalProcessingAgent returns, respond to the user with session.state[{STATE_KEYS.FINAL_REPORT!r}] and nothing else.\n\n"
            "Guardrails:\n"
            "- Honor tool output verbatim; if a lane signals error or no_data, surface that in the final summary.\n"
            "- Do not invent sources, state keys, or additional evidence.\n"
            "- Keep the conversation grounded: explain skipped lanes and residual uncertainties explicitly."
        ),
        tools=[
            NormalizedAgentTool(news_lane_agent),
            NormalizedAgentTool(fact_lane_agent),
            NormalizedAgentTool(scam_lane_agent),
            FinalReportAgentTool(final_report_agent),
        ],
        output_key=STATE_KEYS.FINAL_REPORT,
    )
