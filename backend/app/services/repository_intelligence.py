"""Read-only service, dependency, and branch-diff intelligence for BuildPulse."""

from __future__ import annotations

import os
import re
import subprocess
from pathlib import Path
from typing import Any

import yaml


DEFAULT_BRANCHES = {
    1: {"branch": "feature/payments-retry-policy", "review_status": "pending", "test_status": "passed"},
    2: {"branch": "feature/gateway-contract-header", "review_status": "pending", "test_status": "passed"},
    3: {"branch": "feature/loan-pool-capacity", "review_status": "pending", "test_status": "passed"},
}


class RepositoryIntelligence:
    def __init__(self, repository_path: str | Path | None = None) -> None:
        default_path = Path(__file__).resolve().parents[3].parent / "buildpulse-demo-services"
        self.repository_path = Path(repository_path or os.getenv("DEMO_SERVICES_REPO_PATH", default_path))

    def _catalog(self) -> dict[str, Any]:
        catalog_path = self.repository_path / "service-catalog.yaml"
        if not catalog_path.exists():
            raise FileNotFoundError(f"Service catalog not found at {catalog_path}. Set DEMO_SERVICES_REPO_PATH.")
        with catalog_path.open(encoding="utf-8") as file:
            return yaml.safe_load(file) or {"services": []}

    def services(self) -> list[dict[str, Any]]:
        return self._catalog().get("services", [])

    def service(self, service_id: str) -> dict[str, Any]:
        for service in self.services():
            if service["id"].lower() == service_id.lower() or service["name"].lower() == service_id.lower():
                profile = dict(service)
                profile["depended_on_by"] = [candidate["name"] for candidate in self.services() if service["id"] in candidate.get("depends_on", [])]
                profile["architecture_document"] = "docs/architecture.md"
                return profile
        raise KeyError(service_id)

    def _git_diff_files(self, branch: str) -> list[str]:
        result = subprocess.run(
            ["git", "-C", str(self.repository_path), "diff", "--name-only", f"main...{branch}"],
            check=True, capture_output=True, text=True, timeout=10,
        )
        return [line for line in result.stdout.splitlines() if line]

    def _git_diff_text(self, branch: str) -> str:
        result = subprocess.run(
            ["git", "-C", str(self.repository_path), "diff", "--unified=0", f"main...{branch}"],
            check=True, capture_output=True, text=True, timeout=10,
        )
        return result.stdout

    def _service_for_files(self, files: list[str]) -> dict[str, Any]:
        for service in self.services():
            if any(file.startswith(f"{service['path']}/") for file in files):
                return service
        raise ValueError("Changed files are not associated with a catalogued service")

    @staticmethod
    def _risk_level(score: int) -> str:
        return "high" if score >= 65 else "medium" if score >= 35 else "low"

    def assess_change(self, branch: str, *, pr_number: int | None = None, review_status: str = "pending", test_status: str = "passed") -> dict[str, Any]:
        files = self._git_diff_files(branch)
        diff_text = self._git_diff_text(branch)
        service = self._service_for_files(files)
        changed = " ".join(files).lower()
        drivers: list[dict[str, Any]] = []
        score = 0
        if service["tier"] == "critical":
            score += 20; drivers.append({"factor": "Critical service changed", "points": 20})
        elif service["tier"] == "high":
            score += 10; drivers.append({"factor": "High-criticality service changed", "points": 10})
        if any(token in changed for token in ("connection_pool", "retry", "config")):
            score += 20; drivers.append({"factor": "Resilience configuration changed", "points": 20})
        if any(token in changed for token in ("contract", "openapi", "schema")):
            score += 15; drivers.append({"factor": "API contract changed", "points": 15})
        dependency_points = min(15, len(service.get("depends_on", [])) * 5)
        if dependency_points:
            score += dependency_points
            drivers.append({"factor": "Downstream dependency impact", "points": dependency_points, "dependencies": service["depends_on"]})
        if review_status != "approved":
            score += 15; drivers.append({"factor": "Required owner approval pending", "points": 15})
        if test_status != "passed":
            score += 10; drivers.append({"factor": "Tests missing or pending", "points": 10})
        secret_patterns = {
            "GitHub token": r"gh[pousr]_[A-Za-z0-9_]{20,}",
            "API key": r"\bsk-[A-Za-z0-9_-]{20,}\b",
            "Credential assignment": r"(?i)(?:password|secret|api[_-]?key)\s*[:=]\s*['\"][^'\"]{12,}['\"]",
        }
        secret_types = [name for name, pattern in secret_patterns.items() if re.search(pattern, diff_text)]
        if secret_types:
            score += 40
            drivers.append({"factor": "Secret detected in changed content", "points": 40, "finding_types": secret_types})
        if files and all(file.endswith((".md", ".txt")) for file in files):
            score = max(0, score - 15); drivers.append({"factor": "Documentation-only change", "points": -15})
        checks = ["Obtain approval from the primary and backup service owners."]
        if "connection_pool" in changed or "retry" in changed:
            checks.append("Run timeout, retry, and dependency regression tests.")
        if "contract" in changed:
            checks.append("Confirm dependent services accept the contract change.")
        if service.get("depends_on"):
            checks.append("Validate the listed dependencies during staged rollout.")
        if secret_types:
            checks.insert(0, "Block merge, remove the credential from the branch history, and rotate it if it was ever real.")
        return {
            "pr_number": pr_number, "branch": branch, "service": service["name"], "service_id": service["id"],
            "changed_files": files, "risk_score": score, "risk_level": self._risk_level(score),
            "owners": {"primary": service["primary_owner"], "backup": service["backup_owner"], "team": service["team"], "review_status": review_status},
            "affected_dependencies": service.get("depends_on", []), "drivers": drivers, "test_status": test_status,
            "recommended_checks": checks, "source": "local-synthetic-repository",
            "security": {"secret_detected": bool(secret_types), "finding_count": len(secret_types), "finding_types": secret_types, "redacted": True},
        }

    def pull_request_risk(self, pr_number: int) -> dict[str, Any]:
        try:
            metadata = DEFAULT_BRANCHES[pr_number]
        except KeyError as error:
            raise KeyError(f"No configured demo PR: {pr_number}") from error
        return self.assess_change(pr_number=pr_number, **metadata)

    def portfolio_overview(self) -> dict[str, Any]:
        changes = [self.pull_request_risk(pr_number) for pr_number in DEFAULT_BRANCHES]
        services = self.services()
        return {
            "service_count": len(services), "open_change_count": len(changes),
            "high_risk_change_count": sum(change["risk_level"] == "high" for change in changes),
            "changes_awaiting_approval": sum(change["owners"]["review_status"] != "approved" for change in changes),
            "services": [{"id": service["id"], "name": service["name"], "tier": service["tier"], "primary_owner": service["primary_owner"], "backup_owner": service["backup_owner"], "dependencies": service.get("depends_on", [])} for service in services],
            "changes": changes,
        }
