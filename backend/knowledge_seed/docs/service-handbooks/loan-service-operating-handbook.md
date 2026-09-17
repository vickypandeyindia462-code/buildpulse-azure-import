# Loan Service Operating Handbook

## Purpose and architecture
Loan Service owns loan eligibility and application decisions. FastAPI request handlers call domain rules and a bounded database connection pool; Payments API is a downstream dependency. Changes to pool capacity, decision rules, or the Payments contract require staged validation.

## Roles and responsibilities
- Primary owner: Meera Kulkarni. Backup owner: Arjun Rao. Team: Lending Platform.
- Developers own tests, operational documentation, dashboards, safe rollout plans, and incident follow-up for their changes.
- The primary owner approves critical configuration and contract changes; the backup owner covers incident escalation and release review.
- New joiners pair with an owner for their first production change and must not modify connection-pool limits without capacity evidence.

## Current progress and future plan
- Current: connection-pool contract tests and saturation monitoring are active; rollback verification and early-warning alerts are Release 24.3 work.
- Next: consolidate pool configuration into one source, automate rollback verification, and add dependency-budget dashboards.
- Success measures: p95 below 350 ms, dependency errors below 2%, and no runtime/configuration drift.

## Historical issues
- A pool configuration change exceeded downstream limits, causing dependency timeouts and an 18% error rate.
- Resolution restored one configuration source, capped concurrency, rolled back, and load-tested at 80%, 90%, and 100% utilization.
- Search Jira for the resolved Loan Service saturation incident and use its verification evidence before similar changes.

## New-joiner tools
- Git and GitHub; Python 3.11; pytest; Docker Desktop; curl or an API client; Jira; Confluence; application logs and service dashboards.
- Local validation: install `requirements.txt` and run the Loan Service test suite before requesting review.

## Entitlement requests
- Request read access to the repository, GitHub Actions logs, Jira project, Confluence engineering space, non-production logs, and read-only dashboards.
- Production write, database administration, secret access, and deployment approval require separate least-privilege requests and owner approval.

## Risk profile
- Critical risks: pool-capacity drift, downstream saturation, release changes without load evidence, and inconsistent configuration sources.
- Treat pool, timeout, retry, database, and Payments API contract changes as elevated risk.

## Rules and regulations
- Never place credentials or customer data in logs, prompts, tickets, or documentation.
- Use approved synthetic data outside production. Preserve audit evidence and rollback steps. Require owner review for critical changes.
- AI recommendations are advisory; a human owner approves production actions.

