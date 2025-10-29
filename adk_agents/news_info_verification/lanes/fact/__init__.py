"""Lane definitions for the Fact verification flow."""

from __future__ import annotations

from google.adk.agents.parallel_agent import ParallelAgent
from google.adk.agents.sequential_agent import SequentialAgent

from .merge import fact_merge_agent
from .sub_agents import fact_perplexity_agent, fact_primary_agent


fact_parallel_agent = ParallelAgent(
    name="FactParallelFanout",
    description="Runs specialized fact-check workers in parallel.",
    sub_agents=[fact_primary_agent, fact_perplexity_agent],
)


fact_check_agent = SequentialAgent(
    name="FactCheckAgent",
    description="Performs deep fact verification.",
    sub_agents=[fact_parallel_agent, fact_merge_agent],
)


__all__ = ["fact_check_agent", "fact_parallel_agent"]
