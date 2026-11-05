"""Activity Log tools. TODO (week 1, after Resource Graph).

Planned design:
- ``activity_log_events``: subscription Activity Log via ``azure-mgmt-monitor``
  (``activity_logs.list``) with a required time window (at most 90 days), optional resource
  group, resource ID, caller, and operation filters, and only the fields we need.
- Works with Reader. Same ``ToolSpec``/``ToolResult`` contract and row cap as Resource Graph.
- ``resource_graph_named_query`` with ``recent_changes`` already answers "what changed?" for
  resource state. The Activity Log adds failed operations and control-plane calls that don't
  change state.
"""

from __future__ import annotations

from tools.base import ToolSpec


def build_tools() -> list[ToolSpec]:
    return []
