from __future__ import annotations

import logging
from pathlib import Path

import pytest
from pydantic import BaseModel

from tools.base import ToolError, ToolResult, ToolSpec, truncate_strings
from tools.cache import FileResponseCache, cache_key
from tools.config import ToolSettings
from tools.kql import kql_string


class _Args(BaseModel):
    x: int


def test_invoke_never_raises_and_logs_audit_record(caplog):
    def boom(_: _Args) -> ToolResult:
        raise RuntimeError("secret internals")

    spec = ToolSpec("t", "d", _Args, boom)
    with caplog.at_level(logging.INFO, logger="opsagent.tools"):
        result = spec.invoke({"x": 1})

    assert result.error_code == "internal_error"
    assert "secret internals" not in (result.error_message or "")
    audit = [r for r in caplog.records if r.msg == "tool_call"]
    assert audit and audit[0].tool == "t" and audit[0].ok is False
    assert "duration_ms" in result.metadata


def test_invoke_maps_tool_error_and_validation_error():
    def fail(_: _Args) -> ToolResult:
        raise ToolError("nope", "denied", retryable=True)

    spec = ToolSpec("t", "d", _Args, fail)
    assert spec.invoke({"x": "not-int"}).error_code == "invalid_arguments"
    res = spec.invoke({"x": 1})
    assert (res.error_code, res.retryable) == ("nope", True)


def test_truncate_strings_recurses():
    data = {"a": ["x" * 10, {"b": "y" * 3}], "n": 5}
    out = truncate_strings(data, 4)
    assert out["a"][0].startswith("xxxx...[truncated 6")
    assert out["a"][1]["b"] == "yyy"
    assert out["n"] == 5


@pytest.mark.parametrize(
    ("raw", "literal"),
    [("abc", "'abc'"), ("it's", "'it\\'s'"), ("a\\b", "'a\\\\b'")],
)
def test_kql_string_escaping(raw, literal):
    assert kql_string(raw) == literal


def test_settings_from_env():
    s = ToolSettings.from_env(
        {
            "AZURE_SUBSCRIPTION_IDS": " 11111111-1111-1111-1111-111111111111 ,",
            "OPSAGENT_MAX_ROWS": "50",
            "OPSAGENT_TOOL_CACHE_DIR": ".cache/tools",
        }
    )
    assert s.subscription_ids == ("11111111-1111-1111-1111-111111111111",)
    assert s.max_rows == 50
    assert s.cache_dir == Path(".cache/tools")


def test_settings_reject_bad_subscription_id():
    with pytest.raises(ValueError, match="Invalid subscription"):
        ToolSettings.from_env({"AZURE_SUBSCRIPTION_IDS": "not-a-guid"})


def test_file_cache_roundtrip(tmp_path):
    cache = FileResponseCache(tmp_path / "c")
    key = cache_key("q", ["s"], 5)
    assert cache.get(key) is None
    cache.set(key, {"rows": [{"id": 1}]})
    assert cache.get(key) == {"rows": [{"id": 1}]}
    assert cache_key("q", ["s"], 5) == key != cache_key("q", ["s"], 6)
