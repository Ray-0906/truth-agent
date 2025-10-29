"""Exports for Fact verification sub-agent definitions."""

from .fact_primary import fact_primary_agent
from .fact_perplexity import fact_perplexity_agent

__all__ = [
    "fact_primary_agent",
    "fact_perplexity_agent",
]
