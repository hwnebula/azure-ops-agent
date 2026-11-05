"""Guardrails around the agent loop.

Planned for week 2 and tested by evals/injection/:
- Tool allowlist: only tools from ``tools.build_tools`` are callable, and none of them write.
- Untrusted-content fencing: tool output reaches the model only through
  ``ToolResult.to_model_payload``.
- Output checks: flag answers that repeat instructions found in tool output.
- Step and token budgets per question.
"""
