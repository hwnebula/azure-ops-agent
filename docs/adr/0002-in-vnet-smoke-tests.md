# 0002. Run private-network smoke tests from a Container Apps job inside the VNet

- Status: Accepted
- Date: 2026-11-05

## Context
Model and data services sit behind private endpoints. GitHub-hosted runners have no route to them, so smoke tests run from those runners cannot reach the real endpoints.

## Decision
Smoke tests run as a Container Apps job in the same VNet. The deploy workflow starts the job with its OIDC identity and waits for the job's exit status.

## Consequences
- Tests use the same private DNS and network path as the app.
- There is no self-hosted runner to patch, and nothing is exposed publicly for testing.
- The deploy identity needs permission to start the job. That permission will be scoped to the job resource and listed in the security review.

## Alternatives considered
- Self-hosted runner in the VNet: always-on compute cost and more to maintain.
- Temporarily enabling public access: defeats the purpose of private endpoints.
