from __future__ import annotations

from typing import Any


def respond(question: str, plan: dict[str, Any]) -> str:
    """Sully — inference step (VS-03 layer 2). Produces useful dev-mode legal guidance."""
    if plan.get("intent") == "recall_and_extend" and plan.get("prior_question"):
        prior = plan["prior_question"]
        return (
            f"Sully (inference): Recalling your prior question about «{prior[:80]}». "
            f"In development mode, Harvey connects Harlemm's plan to a substantive answer. "
            f"For follow-ups, the Citizen Padre memory layer supplies the previous turn so "
            f"the pipeline can continue coherently without restarting the session."
        )

    topic = question.strip() or "general legal inquiry"
    return (
        f"Sully (inference): Regarding «{topic[:100]}», Harvey (Reference Application) "
        f"applies Harlemm's plan ({plan.get('intent', 'analysis')}) to produce actionable "
        f"legal-oriented guidance. In VS-03 dev mode this demonstrates the cognitive path "
        f"Planner → Inference → Memory without requiring external model APIs."
    )
