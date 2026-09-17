# Identity Service Operating Handbook

## Purpose and architecture
Identity Service validates demo tokens, claims, signatures, subjects, and expiry boundaries. API Gateway is the primary caller. Validation must fail closed for malformed, modified, empty-subject, or expired tokens.

## Roles and responsibilities
- Primary owner: Nisha Verma. Backup owner: Rohan Gupta. Team: Identity Platform.
- Developers own validation rules, security-contract tests, audit events, runbooks, dashboards, and incident remediation.
- Owners review authentication boundaries, security-sensitive code, and production rollout plans.

## Current progress and future plan
- Current: token expiry enforcement and validation audit events are open Release 24.3 work; empty-subject rejection is covered by CI.
- Next: constant-time verification coverage, automated malformed-token suites, and security-event dashboards.
- Success measures: all malformed and boundary-invalid tokens are rejected with no sensitive token content logged.

## Historical issues
- Prefix-only validation accepted an empty-subject demo token, and an expiry comparison mishandled the exact boundary.
- Resolution requires a non-empty subject, constant-time signature comparison, and rejection when expiry is less than or equal to current time.

## New-joiner tools
- Git/GitHub, Python 3.11, pytest, Docker Desktop, Jira, Confluence, API client, security scanners, audit-event search, and identity dashboards.

## Entitlement requests
- Request repository read, CI logs, Jira, Confluence, non-production identity access, redacted audit-event search, and read-only dashboards.
- Signing keys, production identity administration, secrets, and deployment approval require separate security-owner authorization.

## Risk profile
- Critical risks: accepting malformed tokens, incorrect expiry boundaries, non-constant-time comparisons, missing audit events, and credential exposure.
- Authentication and claims changes require negative tests, security review, and staged verification.

## Rules and regulations
- Never copy real tokens, secrets, or personal data into tickets, documentation, logs, or AI prompts.
- Apply least privilege, fail closed, preserve auditability, and require human security approval for production changes.

