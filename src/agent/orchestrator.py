"""Tool-calling loop. TODO (week 2): implement on top of ModelClient and tools.ToolSpec."""

from __future__ import annotations

from collections.abc import Sequence

from agent.model_client import ModelClient
from tools import ToolSpec


class Orchestrator:
    def __init__(self, model: ModelClient, tools: Sequence[ToolSpec], max_steps: int = 8) -> None:
        self.model = model
        self.tools = {t.name: t for t in tools}
        self.max_steps = max_steps

    def answer(self, question: str) -> str:
        raise NotImplementedError("The agent loop lands in week 2.")
