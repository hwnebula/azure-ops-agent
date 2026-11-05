"""Run one tool locally against real Azure (uses az login).

    python scripts/run_tool.py --list
    python scripts/run_tool.py resource_graph_named_query "{\"name\": \"public_storage_accounts\"}"

Reads AZURE_SUBSCRIPTION_IDS from the environment.
"""

from __future__ import annotations

import argparse
import json
import sys

from tools import build_tools


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("tool", nargs="?", help="Tool name")
    parser.add_argument("arguments", nargs="?", default="{}", help="JSON arguments")
    parser.add_argument("--list", action="store_true", help="List the tools and their schemas")
    ns = parser.parse_args()

    tools = {t.name: t for t in build_tools()}
    if ns.list or not ns.tool:
        for spec in tools.values():
            print(
                f"## {spec.name}\n{spec.description}\n{json.dumps(spec.input_schema, indent=2)}\n"
            )
        return 0
    if ns.tool not in tools:
        print(f"Unknown tool {ns.tool!r}. Available: {', '.join(tools)}", file=sys.stderr)
        return 2

    result = tools[ns.tool].invoke(json.loads(ns.arguments))
    print(
        json.dumps(
            {**result.to_model_payload(), "metadata": result.metadata}, indent=2, default=str
        )
    )
    return 0 if result.ok else 1


if __name__ == "__main__":
    sys.exit(main())
