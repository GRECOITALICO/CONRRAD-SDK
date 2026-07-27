"""Tests for Quick Start / public vocabulary surface."""

from conrrad import Agent
from conrrad_sdk.quickstart.agent import RunResult


def test_agent_run_returns_result():
    agent = Agent()
    result = agent.run("hello task")
    assert isinstance(result, RunResult)
    assert "hello task" in result.answer
    assert len(result.audit_trail) >= 2
    assert result.cost == "Local execution"


def test_agent_run_rejects_empty_task():
    agent = Agent()
    try:
        agent.run("")
        assert False, "expected ValueError"
    except ValueError:
        pass
