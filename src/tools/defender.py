"""Defender for Cloud tools. TODO (week 1, after Activity Log).

Planned design: Defender alerts and recommendations are in Resource Graph's
``securityresources`` table (types ``microsoft.security/locations/alerts`` and
``microsoft.security/assessments``). So these tools will be named queries on the existing
``ResourceGraph`` executor rather than a new SDK client. That needs no new permissions
(Reader), adds no dependency, and gets the same paging, caching, and audit for free. They work
with the free Foundational CSPM tier, so no paid Defender plan is needed.
"""

from __future__ import annotations

from tools.base import ToolSpec


def build_tools() -> list[ToolSpec]:
    return []
