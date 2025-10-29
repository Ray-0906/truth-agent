"""Exports for News lane sub-agent definitions."""

from .news_api import news_api_agent
from .news_fact_checker import news_fact_checker_agent
from .news_perplexity import news_perplexity_agent

__all__ = [
    "news_api_agent",
    "news_fact_checker_agent",
    "news_perplexity_agent",
]
