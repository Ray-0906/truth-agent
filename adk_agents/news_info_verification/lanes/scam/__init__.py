"""Builder for the Scam detection lane."""

from __future__ import annotations

from google.adk.agents.parallel_agent import ParallelAgent
from google.adk.agents.sequential_agent import SequentialAgent

from ...config import MODEL
from .merge import create_scam_merge_agent
from .sub_agents import (
    create_scam_link_agent,
    create_scam_perplexity_agent,
    create_scam_sentiment_agent,
)


def create_scam_check_agent(model: str = MODEL) -> SequentialAgent:
    """Constructs the Scam detection SequentialAgent with parallel fan-out."""

    scam_sentiment = create_scam_sentiment_agent(model=model)
    scam_perplexity = create_scam_perplexity_agent(model=model)
    scam_link = create_scam_link_agent(model=model)

    fanout = ParallelAgent(
        name="ScamParallelFanout",
        description="Runs scam detection agents in parallel.",
        sub_agents=[scam_sentiment, scam_perplexity, scam_link],
    )

    merger = create_scam_merge_agent(model=model)

    return SequentialAgent(
        name="ScamCheckAgent",
        description="Screens for fraud and phishing characteristics.",
        sub_agents=[fanout, merger],
    )
