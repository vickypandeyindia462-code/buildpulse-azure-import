"""Hermetic database setup for tests that must never mutate dev.db."""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.app.db.models import Base, SMEOwnership


@pytest.fixture(autouse=True)
def isolated_database(tmp_path, monkeypatch):
    # Unit tests must never make paid/network model calls because a developer's
    # local .env happens to contain credentials.
    for variable in (
        "AZURE_OPENAI_ENDPOINT",
        "AZURE_OPENAI_API_KEY",
        "AZURE_OPENAI_EMBEDDING_DEPLOYMENT",
        "OPENAI_API_KEY",
        "OPENAI_KEY",
        "GEMINI_API_KEY",
        "GOOGLE_API_KEY",
        "JIRA_API_TOKEN",
    ):
        monkeypatch.delenv(variable, raising=False)
    database_path = tmp_path / "buildpulse-test.db"
    engine = create_engine(f"sqlite:///{database_path}", connect_args={"check_same_thread": False})
    session_factory = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)

    session = session_factory()
    session.add_all(
        [
            SMEOwnership(system_name="Loan Service", owner_name="Asha Patel", owner_team="Payments", owner_email="asha@example.com", expertise_tags="loan,service,payments"),
            SMEOwnership(system_name="Kafka Platform", owner_name="Ravi Kumar", owner_team="Platform", owner_email="ravi@example.com", expertise_tags="kafka,streaming"),
            SMEOwnership(system_name="Auth Service", owner_name="Maria Lopez", owner_team="Auth", owner_email="maria@example.com", expertise_tags="auth,oauth"),
        ]
    )
    session.commit()
    session.close()

    from backend.app.db import database, seed
    from backend.app.routers import ingest, rag_router
    import backend.orchestrator as orchestrator_module

    monkeypatch.setattr(database, "engine", engine)
    monkeypatch.setattr(database, "SessionLocal", session_factory)
    monkeypatch.setattr(seed, "engine", engine)
    monkeypatch.setattr(ingest, "SessionLocal", session_factory)
    monkeypatch.setattr(rag_router, "SessionLocal", session_factory)
    monkeypatch.setattr(orchestrator_module, "SessionLocal", session_factory)
    yield session_factory
    engine.dispose()
