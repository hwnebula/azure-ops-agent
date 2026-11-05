"""Live checks that every named query is valid KQL to the real Resource Graph service.

Run with `pytest -m integration` after `az login` and with AZURE_SUBSCRIPTION_IDS set.
"""

from __future__ import annotations

import os

import pytest

from tools import ToolSettings, build_tools
from tools.resource_graph_queries import NAMED_QUERIES

pytestmark = [
    pytest.mark.integration,
    pytest.mark.skipif(
        not os.environ.get("AZURE_SUBSCRIPTION_IDS"), reason="AZURE_SUBSCRIPTION_IDS not set"
    ),
]

PARAMS = {
    "resources_by_type": {"resource_type": "microsoft.storage/storageaccounts"},
    "resources_missing_tag": {"tag_name": "owner"},
    "recent_changes": {"hours": 24},
}


@pytest.fixture(scope="module")
def named_query_tool():
    tools = {t.name: t for t in build_tools(ToolSettings.from_env())}
    return tools["resource_graph_named_query"]


@pytest.mark.parametrize("name", sorted(NAMED_QUERIES))
def test_named_query_executes(named_query_tool, name):
    result = named_query_tool.invoke(
        {"name": name, "parameters": PARAMS.get(name, {}), "max_rows": 5}
    )
    assert result.ok, f"{result.error_code}: {result.error_message}"
