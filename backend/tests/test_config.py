from backend.app.config import Settings


def test_github_repository_configuration_accepts_owner_repo(monkeypatch):
    monkeypatch.setenv("GITHUB_OWNER", "ignored-owner")
    monkeypatch.setenv("GITHUB_REPO", "demo-owner/demo-repo")

    settings = Settings.from_env()

    assert settings.github_owner == "demo-owner"
    assert settings.github_repo == "demo-repo"


def test_settings_are_read_at_runtime(monkeypatch):
    monkeypatch.setenv("CI_SOURCE", "github")
    assert Settings.from_env().ci_source == "github"
    monkeypatch.setenv("CI_SOURCE", "fixture")
    assert Settings.from_env().ci_source == "fixture"
