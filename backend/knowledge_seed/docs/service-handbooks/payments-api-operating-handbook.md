# Payments API Operating Handbook

## Purpose and architecture
Payments API authorises reservations and protects repeated requests with an idempotency ledger. Request validation must run before reservation creation; identical retries return the original result while conflicting reuse is rejected.

## Roles and responsibilities
- Primary owner: Dev Shah. Backup owner: Kavya Thomas. Team: Payments Platform.
- Developers own contract validation, ledger invariants, retry safety, tests, dashboards, and remediation documentation.
- Owners review changes affecting authorisation, idempotency, retry policy, or financial correctness.

## Current progress and future plan
- Current: idempotency contract strengthening, retry dashboards, and load-test scenarios are tracked in Release 24.3.
- Next: automate duplicate reconciliation, alert on conflicting key reuse, and publish retry-budget SLOs.
- Success measures: zero duplicate reservations for identical requests and complete auditability of authorisation outcomes.

## Historical issues
- Client timeout retries created duplicate reservations because creation occurred before the idempotency-ledger lookup.
- Resolution moved lookup before creation, returned the original response for identical payloads, rejected conflicting reuse, and reconciled duplicates.

## New-joiner tools
- Git/GitHub, Python 3.11, pytest, Docker Desktop, Jira, Confluence, API client, ledger inspection tools, logs, and retry dashboards.

## Entitlement requests
- Request repository read, GitHub Actions logs, Jira, Confluence, non-production API access, read-only ledger views, and observability dashboards.
- Production ledger writes, secrets, refunds, and deployment approval require explicit Payments owner approval and separation of duties.

## Risk profile
- Critical risks: duplicate reservations, non-positive amounts, conflicting idempotency reuse, unbounded retries, and sensitive payment data exposure.
- Changes to validation, ledger ordering, or retry behavior require contract and repeated-request tests.

## Rules and regulations
- Do not store payment credentials or customer identifiers in logs or AI prompts. Use synthetic test data.
- Preserve immutable audit records, enforce least privilege, and require human approval for financial or production actions.

