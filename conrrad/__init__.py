"""
Public import surface for Quick Start.

    from conrrad import Agent

    agent = Agent()
    result = agent.run("Analyze this inventory and find the cheapest supplier.")
    print(result)
"""

from conrrad_sdk.quickstart.agent import Agent, RunResult

__all__ = ["Agent", "RunResult"]
