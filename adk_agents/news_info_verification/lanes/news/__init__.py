"""Lane definitions for the News verification flow."""

from __future__ import annotations

from google.adk.agents.parallel_agent import ParallelAgent
from google.adk.agents.sequential_agent import SequentialAgent

from .sub_agents import (
    news_api_agent,
    news_fact_checker_agent,
    news_perplexity_agent,
)
from .merge import news_merge_agent


news_parallel_agent = ParallelAgent(
    name="NewsParallelFanout",
    description="Runs the news verification workers in parallel.",
    sub_agents=[news_api_agent, news_fact_checker_agent, news_perplexity_agent],
)


news_check_agent = SequentialAgent(
    name="NewsCheckAgent",
    description="Validates breaking news claims across multiple data sources.",
    sub_agents=[news_parallel_agent, news_merge_agent],
)


__all__ = ["news_check_agent", "news_parallel_agent"]
