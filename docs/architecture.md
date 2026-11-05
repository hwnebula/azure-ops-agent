# Architecture

TODO: component diagram (`diagrams/`), request flow, and hosting topology.

## Components
- `src/tools/`: read-only wrappers over Azure Resource Graph, Activity Log, and Defender for Cloud. The API and the MCP server share them.
- `src/agent/`: tool-calling loop behind a provider-neutral `ModelClient`.
- `src/api/`: FastAPI backend with Entra ID auth.
- `infra/`: Terraform for Container Apps, private endpoints, Key Vault, ACR, and Log Analytics in West US 2.
