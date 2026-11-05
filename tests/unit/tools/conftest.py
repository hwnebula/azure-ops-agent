from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import pytest

from tools.resource_graph import ResourceGraph

SUB_A = "11111111-1111-1111-1111-111111111111"
SUB_B = "22222222-2222-2222-2222-222222222222"


@dataclass
class FakeResponse:
    data: list[dict[str, Any]]
    skip_token: str | None = None
    total_records: int | None = None
    result_truncated: str = "false"


class FakeResourceGraphClient:
    """Returns the queued responses in order and records every QueryRequest."""

    def __init__(self, *responses: FakeResponse | Exception) -> None:
        self.responses = list(responses)
        self.requests: list[Any] = []

    def resources(self, query: Any, **_: Any) -> FakeResponse:
        self.requests.append(query)
        item = self.responses.pop(0)
        if isinstance(item, Exception):
            raise item
        return item


@pytest.fixture
def make_rg():
    def _make(*responses: FakeResponse | Exception, **kwargs: Any):
        client = FakeResourceGraphClient(*responses)
        kwargs.setdefault("page_size", 2)
        return ResourceGraph(client, [SUB_A, SUB_B], **kwargs), client

    return _make
