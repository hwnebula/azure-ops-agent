# azure-ops-agent

A **read-only** Azure operations agent that answers questions like *"Which storage accounts are publicly exposed?"* or *"What changed in this subscription yesterday?"*. It runs as a managed identity with **Reader only**, in Azure Container Apps behind private endpoints, and every tool call is audited.

> Status: week 1. The tool layer is in progress (Resource Graph done; Activity Log and Defender next). See [CLAUDE.md](CLAUDE.md) for the full plan.

## Tools

| Tool | What it does |
|---|---|
| `resource_graph_named_query` | Curated, reviewed KQL: public storage, public IPs, NSG rules open to the internet, resource counts, resources by type, missing tags, recent changes. |
| `resource_graph_query` | Model-written KQL, limited to allowlisted Resource Graph tables and the configured subscriptions. |

Design and guardrails: [ADR 0001](docs/adr/0001-read-only-tool-layer.md).

## Quick start

```bash
python -m venv .venv
```
```bash
.venv/Scripts/python -m pip install -e ".[dev]"
```
```bash
.venv/Scripts/python -m pytest
```

Run a tool against your own subscription (uses `az login`):

```bash
AZURE_SUBSCRIPTION_IDS=<sub-id> .venv/Scripts/python scripts/run_tool.py resource_graph_named_query '{"name": "public_storage_accounts"}'
```

Live integration tests: `pytest -m integration` (requires `AZURE_SUBSCRIPTION_IDS`).

## Layout

- `src/tools/`: read-only Azure tools, shared by the agent API and the MCP server.
- `src/agent/`: tool-calling loop behind a swappable `ModelClient`.
- `src/api/`, `src/web/`: FastAPI backend (Entra ID auth) and a minimal chat UI.
- `evals/`: question set with known answers, injection cases, and a scored runner.
- `infra/`: Terraform modules and the `dev-wus2` environment.
- `docs/`: architecture, security-review packet, ADRs.
