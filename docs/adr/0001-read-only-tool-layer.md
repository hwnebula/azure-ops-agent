# 0001. Read-only tool layer: curated queries first, guarded KQL as fallback

- Status: Accepted
- Date: 2026-11-05

## Context
The agent answers operations and security questions by calling tools over Azure Resource Graph, the Activity Log, and Defender for Cloud. Three requirements shape the tool layer:

1. Both the FastAPI agent and a future MCP server must use the same tools (`src/tools/` has no dependency on `src/agent/`).
2. A security team must be able to review exactly what the agent can read.
3. Data the tools return (tags, names, alert text) can be written by anyone with write access to a resource, so it is a prompt-injection channel.

## Decision
- **Provider-neutral contract.** Each tool is a `ToolSpec`: a name, a description, a Pydantic input model (which supplies the JSON schema for Claude, Azure OpenAI, or MCP), and a handler that returns a `ToolResult`. `ToolSpec.invoke` validates arguments, never raises, and writes one structured `tool_call` audit record for each call.
- **Curated named queries first.** `resource_graph_named_query` runs reviewed KQL templates with typed, regex-validated parameters inserted as escaped literals. These give the evals stable result shapes.
- **Guarded free-form KQL as fallback.** `resource_graph_query` accepts model-written KQL only when the query starts with an allowlisted table and every `join`/`union` target is also allowlisted. Control commands, `externaldata`, `evaluate`, and `invoke` are rejected. The check fails closed, so a leading `let` or a leading comment is rejected too.
- **Scope and volume limits.** Every call is limited to `AZURE_SUBSCRIPTION_IDS`. A caller may narrow that set but never widen it. Results are paged with skip tokens up to a hard row cap, and truncation is reported explicitly.
- **Untrusted output.** `ToolResult.to_model_payload()` labels rows as untrusted data and trims long strings (1024 characters by default).
- **Actionable errors.** Azure failures map to stable codes (`invalid_query`, `forbidden`, `throttled`, ...). For `invalid_query`, Resource Graph's message is passed back so the model can fix its KQL.
- **Defender through Resource Graph.** Defender alerts and assessments are in the `securityresources` table, so the Defender tools will be named queries on the same executor rather than a new SDK client.

## Consequences
- Reader on the subscription is enough. No permission expansion is needed.
- The query allowlist is defense in depth, not the security boundary. Resource Graph is read-only and the identity is Reader. The allowlist keeps what the agent reads predictable and easy to review.
- Named queries need upkeep as questions are added, but each one is a small, testable template.
- The table check is a regex, not a KQL parser. It can reject some valid queries (for example, ones that start with `let`). That is an acceptable trade-off for an LLM caller, which can rewrite the query.

## Alternatives considered
- **Free-form KQL only:** most flexible, but harder to review and evaluate, and gives a larger injection surface.
- **One tool per question:** too many tools for the model to choose between well. A single named-query tool with an enum scales better.
- **Full KQL parser:** no maintained Python parser covers Resource Graph's KQL dialect, so the extra complexity buys little.
