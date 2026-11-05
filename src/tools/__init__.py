"""Read-only Azure tools shared by the agent (``agent``), the API, and the MCP server.

This package must not import from ``agent``, ``api``, or ``mcp_server``
(enforced by tests/unit/tools/test_independence.py).
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from tools.base import ToolError, ToolResult, ToolSpec
from tools.config import ToolSettings

if TYPE_CHECKING:
    from azure.core.credentials import TokenCredential

__all__ = ["ToolError", "ToolResult", "ToolSettings", "ToolSpec", "build_tools"]


def build_tools(
    settings: ToolSettings | None = None, credential: TokenCredential | None = None
) -> list[ToolSpec]:
    """Build every available tool from the environment, or from explicit settings."""
    from azure.mgmt.resourcegraph import ResourceGraphClient

    from tools import activity_log, defender, resource_graph
    from tools.auth import get_credential
    from tools.cache import FileResponseCache

    settings = settings or ToolSettings.from_env()
    rg = resource_graph.ResourceGraph(
        ResourceGraphClient(credential or get_credential()),
        settings.subscription_ids,
        max_rows=settings.max_rows,
        page_size=settings.page_size,
        cache=FileResponseCache(settings.cache_dir) if settings.cache_dir else None,
    )
    return [
        *resource_graph.build_tools(rg),
        *activity_log.build_tools(),
        *defender.build_tools(),
    ]
