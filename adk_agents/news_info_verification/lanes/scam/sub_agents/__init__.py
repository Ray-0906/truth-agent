"""Factories for Scam detection sub-agents."""

from .scam_link import create_scam_link_agent
from .scam_perplexity import create_scam_perplexity_agent
from .scam_sentiment import create_scam_sentiment_agent

__all__ = [
    "create_scam_sentiment_agent",
    "create_scam_perplexity_agent",
    "create_scam_link_agent",
]
