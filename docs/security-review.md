# Security review packet

## 1. Data flow diagram
TODO (`diagrams/`).

## 2. Permissions
| Principal | Scope | Role | Justification |
|---|---|---|---|
| App managed identity | Target subscription(s) | Reader | Reads Resource Graph, Activity Log, and Defender alerts. |
| GitHub Actions (OIDC) | `rg-opsagent-dev-wus2` only | Contributor | Terraform deploys into the project's own group in the Production subscription (ADR 0003). |

Any permission beyond Reader requires an ADR in `adr/`.

## 3. Threat model
TODO (STRIDE). Known risk: prompt injection through Azure data (tags, names, alert text).

Mitigations so far (see ADR 0001):
- No write tools exist.
- Tool output is marked untrusted, and long strings are truncated before they reach the model.
- Queries are limited to allowlisted Resource Graph tables and the configured subscriptions.

## 4. Audit
Every tool call and answer is logged to Log Analytics.
