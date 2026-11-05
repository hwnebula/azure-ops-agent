"""Optional response cache, so eval development doesn't call Azure on every run.

Turned off by default. Enable it with ``OPSAGENT_TOOL_CACHE_DIR``. Only successful responses
are cached.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Protocol


class ResponseCache(Protocol):
    def get(self, key: str) -> dict[str, Any] | None: ...
    def set(self, key: str, value: dict[str, Any]) -> None: ...


def cache_key(*parts: Any) -> str:
    blob = json.dumps(parts, sort_keys=True, default=str, separators=(",", ":"))
    return hashlib.sha256(blob.encode()).hexdigest()


class FileResponseCache:
    def __init__(self, directory: Path) -> None:
        self.directory = directory
        self.directory.mkdir(parents=True, exist_ok=True)

    def _path(self, key: str) -> Path:
        return self.directory / f"{key}.json"

    def get(self, key: str) -> dict[str, Any] | None:
        path = self._path(key)
        if not path.exists():
            return None
        data: dict[str, Any] = json.loads(path.read_text(encoding="utf-8"))
        return data

    def set(self, key: str, value: dict[str, Any]) -> None:
        self._path(key).write_text(json.dumps(value, default=str), encoding="utf-8")


class MemoryResponseCache:
    """In-process cache, used by tests."""

    def __init__(self) -> None:
        self.store: dict[str, dict[str, Any]] = {}

    def get(self, key: str) -> dict[str, Any] | None:
        return self.store.get(key)

    def set(self, key: str, value: dict[str, Any]) -> None:
        self.store[key] = value
