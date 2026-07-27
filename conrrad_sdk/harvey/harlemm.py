from __future__ import annotations

from typing import Any, Optional


def plan(question: str, prior: Optional[dict[str, Any]] = None) -> dict[str, Any]:
    """Harlemm — planner step (VS-03 layer 1)."""
    context_used = prior is not None
    prior_question = str(prior.get("question", "")) if prior else ""

    if context_used and _references_prior(question):
        summary = f"Follow-up on prior legal query: {prior_question[:120]}"
        intent = "recall_and_extend"
    else:
        summary = f"Analyze legal question: {question[:120]}"
        intent = "new_legal_analysis"

    return {
        "agent": "Harlemm",
        "role": "planner",
        "intent": intent,
        "summary": summary,
        "context_used": context_used,
        "prior_question": prior_question if context_used else None,
        "delegation": "Sully",
    }


def _references_prior(question: str) -> bool:
    q = question.lower()
    markers = (
        "anterior",
        "previous",
        "before",
        "resume",
        "resumen",
        "recuerda",
        "what did i ask",
        "consulta previa",
    )
    return any(m in q for m in markers)
