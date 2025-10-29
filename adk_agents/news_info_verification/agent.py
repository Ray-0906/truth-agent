"""Entry-point module exposing the root agent."""

from __future__ import annotations

from .router import create_content_routing_agent


root_agent = create_content_routing_agent()

__all__ = ["root_agent", "create_content_routing_agent"]
