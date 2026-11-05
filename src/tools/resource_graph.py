"""Azure Resource Graph tools.

Two tools are exposed to the agent and the MCP server:

- ``resource_graph_named_query``: curated, reviewed queries with typed parameters (preferred).
- ``resource_graph_query``: model-written KQL, limited to allowlisted tables (fallback).

Both run through ``ResourceGraph``, which scopes every call to the configured subscriptions,
pages with skip tokens up to a hard row cap, maps Azure errors to ``ToolError`` codes the model
can act on, and can cache responses for eval development.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import replace
from typing import Any, Protocol

from azure.core.exceptions import ClientAuthenticationError, HttpResponseError
from azure.mgmt.resourcegraph.models import QueryRequest, QueryRequestOptions, ResultFormat
from pydantic import BaseModel, ConfigDict, Field

from tools.base import ToolError, ToolResult, ToolSpec
from tools.cache import ResponseCache, cache_key
from tools.kql import ALLOWED_TABLES, MAX_QUERY_LEN, validate_query
from tools.resource_graph_queries import NAMED_QUERIES, NamedQueryName, describe_named_queries

MAX_ERROR_LEN = 2000


class ResourcesClient(Protocol):
    """The one method of ``azure.mgmt.resourcegraph.ResourceGraphClient`` this module uses."""

    def resources(self, query: QueryRequest, **kwargs: Any) -> Any: ...


class ResourceGraph:
    def __init__(
        self,
        client: ResourcesClient,
        subscription_ids: Sequence[str],
        *,
        max_rows: int = 1000,
        page_size: int = 200,
        cache: ResponseCache | None = None,
    ) -> None:
        self._client = client
        self._subscriptions = tuple(subscription_ids)
        self._max_rows = max_rows
        self._page_size = page_size
        self._cache = cache

    # -- public API ---------------------------------------------------------------------------

    def query(
        self,
        kql: str,
        *,
        max_rows: int | None = None,
        subscription_ids: Sequence[str] | None = None,
        tool_name: str = "resource_graph_query",
    ) -> ToolResult:
        validate_query(kql)
        subs = self._resolve_subscriptions(subscription_ids)
        limit = min(max_rows or self._max_rows, self._max_rows)

        key = cache_key("resource_graph", kql, sorted(subs), limit)
        if self._cache is not None and (hit := self._cache.get(key)) is not None:
            return ToolResult(
                tool=tool_name,
                ok=True,
                rows=hit["rows"],
                truncated=hit["truncated"],
                total_records=hit["total_records"],
                metadata={"query": kql, "subscriptions": list(subs), "cache": "hit"},
            )

        rows, truncated, total = self._fetch(kql, subs, limit)
        if self._cache is not None:
            self._cache.set(key, {"rows": rows, "truncated": truncated, "total_records": total})
        return ToolResult(
            tool=tool_name,
            ok=True,
            rows=rows,
            truncated=truncated,
            total_records=total,
            metadata={
                "query": kql,
                "subscriptions": list(subs),
                "cache": "miss" if self._cache is not None else "off",
            },
        )

    def named_query(
        self,
        name: str,
        parameters: dict[str, Any] | None = None,
        *,
        max_rows: int | None = None,
        subscription_ids: Sequence[str] | None = None,
    ) -> ToolResult:
        named = NAMED_QUERIES.get(name)
        if named is None:
            raise ToolError("unknown_query", f"Unknown named query '{name}'.")
        try:
            kql = named.render(parameters)
        except ValueError as exc:  # pydantic ValidationError is a ValueError
            raise ToolError("invalid_arguments", f"Invalid parameters for {name}: {exc}") from exc
        result = self.query(
            kql,
            max_rows=max_rows,
            subscription_ids=subscription_ids,
            tool_name="resource_graph_named_query",
        )
        return replace(result, metadata={**result.metadata, "named_query": name})

    # -- internals ----------------------------------------------------------------------------

    def _resolve_subscriptions(self, requested: Sequence[str] | None) -> tuple[str, ...]:
        if not self._subscriptions:
            raise ToolError(
                "not_configured", "No subscriptions configured (set AZURE_SUBSCRIPTION_IDS)."
            )
        if not requested:
            return self._subscriptions
        allowed = {s.lower() for s in self._subscriptions}
        outside = [s for s in requested if s.lower() not in allowed]
        if outside:
            raise ToolError(
                "invalid_arguments",
                f"Subscription(s) not in the configured scope: {', '.join(outside)}.",
            )
        return tuple(requested)

    def _fetch(
        self, kql: str, subs: tuple[str, ...], limit: int
    ) -> tuple[list[dict[str, Any]], bool, int | None]:
        rows: list[dict[str, Any]] = []
        skip_token: str | None = None
        total: int | None = None
        truncated = False

        while True:
            request = QueryRequest(
                subscriptions=list(subs),
                query=kql,
                options=QueryRequestOptions(
                    top=min(self._page_size, limit - len(rows)),
                    skip_token=skip_token,
                    result_format=ResultFormat.OBJECT_ARRAY,
                ),
            )
            response = self._call(request)
            rows.extend(response.data or [])
            total = response.total_records
            skip_token = response.skip_token
            if _is_true(getattr(response, "result_truncated", None)):
                truncated = True  # Service-side truncation, e.g. `id` not projected for paging.
            if not skip_token:
                break
            if len(rows) >= limit:
                truncated = True
                break

        if total is not None and total > len(rows):
            truncated = True
        return rows[:limit], truncated, total

    def _call(self, request: QueryRequest) -> Any:
        try:
            return self._client.resources(request)
        except ClientAuthenticationError as exc:
            raise ToolError(
                "auth_failed",
                "Could not authenticate to Azure. Check the managed identity or az login.",
            ) from exc
        except HttpResponseError as exc:
            raise _map_http_error(exc) from exc


def _is_true(value: Any) -> bool:
    return str(getattr(value, "value", value)).lower() == "true"


def _map_http_error(exc: HttpResponseError) -> ToolError:
    status = exc.status_code or 0
    message = (exc.message or str(exc))[:MAX_ERROR_LEN]
    if status == 400:
        return ToolError("invalid_query", f"Resource Graph rejected the query: {message}")
    if status == 403:
        return ToolError("forbidden", "The identity lacks read access to the requested scope.")
    if status == 429:
        return ToolError("throttled", "Resource Graph throttled the request.", retryable=True)
    if status >= 500:
        return ToolError("service_error", f"Resource Graph error ({status}).", retryable=True)
    return ToolError("azure_error", f"Resource Graph error ({status}): {message}")


# -- tool specs -------------------------------------------------------------------------------


class _CommonArgs(BaseModel):
    model_config = ConfigDict(extra="forbid")

    max_rows: int = Field(
        default=200, ge=1, le=1000, description="Maximum rows to return (results are paged)."
    )
    subscription_ids: list[str] | None = Field(
        default=None,
        description="Optional subset of the configured subscriptions. Omit to query all of them.",
    )


class ResourceGraphNamedQueryInput(_CommonArgs):
    name: NamedQueryName = Field(description="Which curated query to run.")
    parameters: dict[str, str | int] = Field(
        default_factory=dict, description="Parameters for the chosen query, if it takes any."
    )


class ResourceGraphQueryInput(_CommonArgs):
    query: str = Field(
        min_length=1,
        max_length=MAX_QUERY_LEN,
        description=(
            "Read-only KQL for Azure Resource Graph. Must start with one of these tables: "
            + ", ".join(sorted(ALLOWED_TABLES))
            + ". Project `id` so results can be paged."
        ),
    )


def build_tools(rg: ResourceGraph) -> list[ToolSpec]:
    def named(args: ResourceGraphNamedQueryInput) -> ToolResult:
        return rg.named_query(
            args.name,
            args.parameters,
            max_rows=args.max_rows,
            subscription_ids=args.subscription_ids,
        )

    def freeform(args: ResourceGraphQueryInput) -> ToolResult:
        return rg.query(args.query, max_rows=args.max_rows, subscription_ids=args.subscription_ids)

    return [
        ToolSpec(
            name="resource_graph_named_query",
            description=(
                "Run a curated, read-only Azure Resource Graph query across the configured "
                "subscriptions. Use this first when one of these fits the question:\n"
                + describe_named_queries()
            ),
            input_model=ResourceGraphNamedQueryInput,
            handler=named,
        ),
        ToolSpec(
            name="resource_graph_query",
            description=(
                "Run a read-only Azure Resource Graph KQL query across the configured "
                "subscriptions. Use this only when no named query fits. Only these tables are "
                "allowed: " + ", ".join(sorted(ALLOWED_TABLES)) + "."
            ),
            input_model=ResourceGraphQueryInput,
            handler=freeform,
        ),
    ]
