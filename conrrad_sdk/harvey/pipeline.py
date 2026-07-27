from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from conrrad_sdk.harvey import harlemm, sully
from conrrad_sdk.harvey.memory import MemoryStore

logger = logging.getLogger("conrrad.harvey.pipeline")


class HarveyPipeline:
    """POST /query → Harlemm → Sully → Memory → Response."""

    def __init__(self, workspace: Path) -> None:
        self.memory = MemoryStore(workspace / "memory.json")

    def query(self, question: str, session_id: str = "default") -> dict[str, Any]:
        prior = self.memory.last_turn(session_id)

        plan = harlemm.plan(question, prior=prior)
        logger.info("[Harlemm] plan intent=%s context_used=%s", plan["intent"], plan["context_used"])

        answer = sully.respond(question, plan)
        logger.info("[Sully] answer_len=%d", len(answer))

        turn = {
            "question": question,
            "plan": plan,
            "answer": answer,
        }
        self.memory.append(session_id, turn)

        return {
            "status": "ok",
            "answer": answer,
            "session_id": session_id,
            "turn": self.memory.turn_count(session_id),
            "context_used": bool(plan.get("context_used")),
            "pipeline": {
                "Harlemm": plan,
                "Sully": {"agent": "Sully", "role": "inference", "answer_chars": len(answer)},
            },
        }
