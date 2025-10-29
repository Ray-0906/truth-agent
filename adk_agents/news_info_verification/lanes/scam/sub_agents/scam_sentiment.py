"""Factory for the ScamSentimentAgent."""

from __future__ import annotations

from google.adk.agents.llm_agent import LlmAgent

from ....config import MODEL, STATE_KEYS


def create_scam_sentiment_agent(model: str = MODEL) -> LlmAgent:
    """Builds the agent that detects manipulative sentiment."""

    return LlmAgent(
        name="ScamSentimentAgent",
        model=model,
        description="Detects persuasive or manipulative sentiment indicating scams.",
        instruction=(
            "Evaluate tone cues that typically indicate scams: urgency, fear appeals, authority impersonation, reward framing. "
            "Cite the exact phrases you relied upon.\n\n"
            "Return JSON: {\"status\": \"ok|no_data|error\", \"risk_level\": \"low|medium|high\", \"confidence\": <float>, "
            "\"triggers\": [{\"excerpt\": str, \"pattern\": str}], \"notes\": \"<=60 words\"}."
        ),
        output_key=STATE_KEYS.SCAM_SENTIMENT,
    )
