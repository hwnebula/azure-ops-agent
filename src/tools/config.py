"""Tool-layer settings, read from environment variables (see .env.example)."""

from __future__ import annotations

import os
import re
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path

_GUID = re.compile(r"^[0-9a-fA-F]{8}-([0-9a-fA-F]{4}-){3}[0-9a-fA-F]{12}$")


@dataclass(frozen=True)
class ToolSettings:
    #: Subscriptions the tools may query. Calls cannot reach outside this set.
    subscription_ids: tuple[str, ...]
    #: Hard cap on rows returned to the model by any single call.
    max_rows: int = 1000
    #: Rows per Resource Graph page (the service maximum is 1000).
    page_size: int = 200
    #: When set, successful responses are cached on disk. For eval development only.
    cache_dir: Path | None = None

    def __post_init__(self) -> None:
        bad = [s for s in self.subscription_ids if not _GUID.match(s)]
        if bad:
            raise ValueError(f"Invalid subscription ID(s): {', '.join(bad)}")
        if not 1 <= self.page_size <= 1000:
            raise ValueError("page_size must be between 1 and 1000")
        if self.max_rows < 1:
            raise ValueError("max_rows must be at least 1")

    @classmethod
    def from_env(cls, env: Mapping[str, str] | None = None) -> ToolSettings:
        env = os.environ if env is None else env
        subs = tuple(
            s.strip() for s in env.get("AZURE_SUBSCRIPTION_IDS", "").split(",") if s.strip()
        )
        cache_dir = env.get("OPSAGENT_TOOL_CACHE_DIR", "").strip()
        return cls(
            subscription_ids=subs,
            max_rows=int(env.get("OPSAGENT_MAX_ROWS", "1000")),
            page_size=int(env.get("OPSAGENT_PAGE_SIZE", "200")),
            cache_dir=Path(cache_dir) if cache_dir else None,
        )
