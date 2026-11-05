# 0003. Host in the Production subscription, isolated in its own resource group

- Status: Accepted
- Date: 2026-11-05

## Context
The agent needs a real environment with real resources to answer questions about. The owner chose the existing Production subscription rather than a dedicated sandbox subscription. The project repo is public.

## Decision
- All project resources go in one resource group, `rg-opsagent-dev-wus2`, in West US 2, managed by Terraform (`infra/envs/dev-wus2`). `terraform destroy` removes the group and touches nothing else in the subscription.
- The agent reads the subscription through Resource Graph using Reader only (see ADR 0001). It has no write role anywhere, including its own resource group.
- The `env` tag stays `dev`: it describes this project's lifecycle stage, not the subscription.

## Data handling (public repo)
Tool output from this subscription contains real resource names, IDs, IPs, and tags. None of it may be committed:
- The subscription ID lives only in `terraform.tfvars` and `.env`, both gitignored.
- The tool response cache (`OPSAGENT_TOOL_CACHE_DIR`) must point to a gitignored path such as `.cache/`.
- `evals/datasets/` and `evals/results/` hold only synthetic fixtures or scrubbed data. CI evals run against recorded, scrubbed tool responses, not live Production.

## Consequences
- Deploying and destroying is low-risk for the rest of the subscription, because everything lives in one group.
- Production-level controls (Azure Policy, required tags, change management) apply to this group and may block resources the plan assumes. These are handled as they come up.
- The deploy identity (GitHub OIDC) gets Contributor scoped to this resource group only, never the subscription. Details will be in the identity ADR.

## Alternatives considered
- Dedicated sandbox subscription: cleanest isolation, but no real workload to query.
- A resource group in Production queried only at RG scope: limits what the agent can show.
