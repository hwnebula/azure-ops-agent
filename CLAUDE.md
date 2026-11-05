# azure-ops-agent

A read-only Azure operations agent that answers questions like "which storage accounts are publicly exposed?" or "what changed in this subscription yesterday?". Built as a public portfolio project for Forward-Deployed Engineer roles, so it should look like something an enterprise customer's security team would approve.

## Owner context
- Owner: Harold Williams, Azure architect with a security and networking background (Terraform, Entra ID, private networking).
- Goal: demonstrate software engineering, AI application, and evaluation skills on top of enterprise deployment credibility.

## Decisions already made
- **Language/backend:** Python, FastAPI for the API layer.
- **Agent:** tool-calling loop. Tools wrap Azure Resource Graph, Activity Log, and Defender for Cloud alerts.
- **Model:** Claude API or Azure OpenAI (not yet decided). Keep the model client behind an interface so it can be swapped.
- **Identity:** managed identity with Reader role only. Any permission expansion requires a written justification in `docs/adr/`.
- **Hosting:** Azure Container Apps (consumption), private endpoints for model and data services, private DNS zones, Key Vault, Container Registry (Basic), Log Analytics.
- **Region and naming:** West US 2, using `wus2` short codes in resource names (for example `rg-opsagent-dev-wus2`).
- **IaC:** Terraform, reusable modules under `infra/modules/`, environments under `infra/envs/` (first: `dev-wus2`).
- **CI/CD:** GitHub Actions on a public GitHub repo. Authenticate to Azure with OIDC workload identity federation; no stored secrets.
- **Private-network smoke tests:** run from a Container Apps job inside the VNet, because GitHub-hosted runners can't reach private endpoints. Record this as an ADR.
- **Audit:** every tool call and answer logged to Log Analytics.

## Cost constraints
- Target about $40-90/month while running, less when torn down. Budget alert at $50.
- Do NOT add Azure Firewall, Bastion, Application Gateway/WAF, or paid Defender plans.
- Infrastructure must be fully reproducible with `terraform destroy` / `apply`.
- Cache tool responses during eval development; use a smaller model for routine eval runs.

## Quality bar (what makes this FDE-grade)
1. **Evals:** 30-50 questions with known answers in `evals/datasets/questions.jsonl`, scored automatically in CI on every PR. Fail the build if the pass rate drops. Commit results history to `evals/results/`.
2. **Guardrails:** read-only by design; prompt-injection test cases (for example, a malicious resource tag trying to redirect the agent) in `evals/injection/`.
3. **Security-review packet:** `docs/security-review.md` with data flow diagram, threat model, and permissions list.
4. **Demo:** a 3-minute walkthrough of one real scenario (recorded at the end).
5. **Stretch:** expose the tools as an MCP server in `src/mcp_server/`, reusing `src/tools/`.

## Repo structure
```
azure-ops-agent/
├── README.md
├── CLAUDE.md
├── docs/
│   ├── security-review.md
│   ├── architecture.md
│   ├── diagrams/
│   └── adr/
├── src/
│   ├── agent/        # orchestrator.py, prompts.py, guardrails.py
│   ├── tools/        # resource_graph.py, activity_log.py, defender.py
│   ├── mcp_server/   # stretch goal
│   ├── api/          # FastAPI backend, Entra ID auth
│   └── web/          # minimal chat UI
├── evals/
│   ├── datasets/questions.jsonl
│   ├── injection/
│   ├── run_evals.py
│   └── results/
├── tests/
│   ├── unit/
│   └── integration/
├── infra/
│   ├── modules/      # network, identity, app, ai, monitoring
│   └── envs/dev-wus2/
├── .github/workflows/ # ci.yml (lint, tests, evals), deploy.yml (terraform)
├── scripts/
├── .env.example
├── pyproject.toml
└── Makefile
```
Keep `src/tools/` independent of `src/agent/` so the API and MCP server share the same tools.

## Timeline
- **Weeks 1-2:** tool layer and a basic agent working locally.
- **Weeks 3-4:** Terraform deployment with private networking and Entra ID auth.
- **Weeks 5-6:** evals, injection testing, docs, demo video.

## Working preferences
- Prefer single-line CLI commands in instructions.
- Least privilege first: start with Reader and justify anything more.
- Write an ADR for each significant design decision.
