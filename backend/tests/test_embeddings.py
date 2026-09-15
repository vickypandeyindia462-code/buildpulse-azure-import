from backend.app import embeddings


def test_mock_embedding_is_stable(monkeypatch):
    monkeypatch.delenv("AZURE_OPENAI_ENDPOINT", raising=False)
    monkeypatch.delenv("AZURE_OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("AZURE_OPENAI_EMBEDDING_DEPLOYMENT", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    first = embeddings.get_embedding("BuildPulse")
    second = embeddings.get_embedding("BuildPulse")
    assert first == second
    assert len(first) == embeddings.EMBEDDING_DIM
