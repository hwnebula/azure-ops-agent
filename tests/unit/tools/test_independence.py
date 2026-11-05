"""src/tools must stay independent of the agent so the API and the MCP server can share it."""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

TOOLS_DIR = Path(__file__).resolve().parents[3] / "src" / "tools"
FORBIDDEN = ("agent", "api", "mcp_server")


@pytest.mark.parametrize("path", sorted(TOOLS_DIR.rglob("*.py")), ids=lambda p: p.name)
def test_tools_do_not_import_agent_api_or_mcp(path):
    tree = ast.parse(path.read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names = [a.name for a in node.names]
        elif isinstance(node, ast.ImportFrom):
            names = [node.module or ""]
        else:
            continue
        for name in names:
            assert name.split(".")[0] not in FORBIDDEN, f"{path.name} imports {name}"
