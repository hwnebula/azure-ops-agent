"""KQL helpers: escaping string literals and a fail-closed check on free-form queries.

Resource Graph is read-only at the service level, and the identity is Reader. This check adds
defense in depth: it keeps model-written queries to known tables, so what the agent can see
stays predictable and easy to review.
"""

from __future__ import annotations

import re

from tools.base import ToolError

ALLOWED_TABLES: frozenset[str] = frozenset(
    {
        "resources",
        "resourcecontainers",
        "resourcechanges",
        "resourcecontainerchanges",
        "securityresources",
        "advisorresources",
        "policyresources",
        "healthresources",
    }
)

MAX_QUERY_LEN = 4000

_FIRST_IDENT = re.compile(r"^\s*([A-Za-z_][A-Za-z0-9_]*)")
# Tables referenced by `join (...)`, `join kind=x (...)`, `union t`, or `union kind=x t`.
_TABLE_REFS = re.compile(
    r"\bjoin\b[^(|]*\(\s*([\w*]+)|\bunion\s+(?:kind\s*=\s*\w+\s+)?([\w*]+)",
    re.IGNORECASE,
)
_FORBIDDEN = re.compile(r"\b(externaldata|evaluate|invoke)\b|^\s*\.", re.IGNORECASE | re.MULTILINE)


def kql_string(value: str) -> str:
    """Return ``value`` as a single-quoted KQL string literal."""
    return "'" + value.replace("\\", "\\\\").replace("'", "\\'") + "'"


def validate_query(query: str, allowed_tables: frozenset[str] = ALLOWED_TABLES) -> None:
    """Raise ToolError("invalid_query") unless the query only reads from allowed tables.

    This check fails closed: the query must start with an allowed table name (no leading
    ``let`` or comments), and every joined or unioned table must also be allowed.
    """
    allowed = ", ".join(sorted(allowed_tables))
    if not query.strip():
        raise ToolError("invalid_query", "Query is empty.")
    if len(query) > MAX_QUERY_LEN:
        raise ToolError("invalid_query", f"Query exceeds {MAX_QUERY_LEN} characters.")
    if _FORBIDDEN.search(query):
        raise ToolError(
            "invalid_query",
            "Control commands, externaldata, evaluate, and invoke are not allowed.",
        )

    first = _FIRST_IDENT.match(query)
    if not first or first.group(1).lower() not in allowed_tables:
        raise ToolError("invalid_query", f"Query must start with one of these tables: {allowed}.")

    for match in _TABLE_REFS.finditer(query):
        table = (match.group(1) or match.group(2)).lower()
        if table not in allowed_tables:
            raise ToolError(
                "invalid_query", f"Table '{table}' is not allowed. Allowed tables: {allowed}."
            )
