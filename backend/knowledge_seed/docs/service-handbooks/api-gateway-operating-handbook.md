# API Gateway Operating Handbook

## Purpose and architecture
API Gateway owns external routing, request contracts, and correlation-ID propagation. Its route registry maps supported paths to downstream services, including Identity Service, while middleware preserves tracing context.

## Roles and responsibilities
- Primary owner: Jose Nair. Backup owner: Asha Rao. Team: Platform Engineering.
- Developers own route contracts, compatibility tests, trace propagation, dashboards, documentation, and safe rollout checks.
- Owners approve public contract changes and coordinate validation with every affected downstream team.

## Current progress and future plan
- Current: correlation-ID propagation, downstream contract validation, and route-level SLO reporting are Release 24.3 work.
- Next: automated route-registry contract checks, consumer compatibility gates, and per-route latency/error budgets.
- Success measures: every request is traceable and every supported route has a tested downstream mapping.

## Historical issues
- The `/identity` mapping was absent from the route registry, causing requests and contract tests to fail with a missing-route error.
- Resolution restores the mapping, verifies existing routes, and adds a registry contract check to CI.

## New-joiner tools
- Git/GitHub, Python 3.11, pytest, Docker Desktop, curl/API client, Jira, Confluence, distributed tracing, gateway logs, and SLO dashboards.

## Entitlement requests
- Request repository read, CI logs, Jira, Confluence, non-production gateway access, tracing search, and read-only dashboards.
- Route deployment, production configuration, certificates, secrets, and traffic-control permissions require Platform owner approval.

## Risk profile
- High risks: missing routes, breaking contracts, lost correlation IDs, unsafe header forwarding, and gateway-wide rollout impact.
- Public route, schema, authentication, and traffic-policy changes require consumer and staged rollout verification.

## Rules and regulations
- Do not log credentials or unrestricted request payloads. Preserve correlation IDs without exposing sensitive data.
- Maintain backward compatibility unless an approved migration exists. Human approval is required for production routing changes.

