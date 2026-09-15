from backend.app.services.knowledge_base import KnowledgeBase


def test_repository_knowledge_search_returns_ranked_citations():
    from backend.app.services.repository_intelligence import RepositoryIntelligence

    knowledge = KnowledgeBase(RepositoryIntelligence().repository_path)
    results = knowledge.search("loan service connection pool recovery", "loan-service")
    assert results
    assert results[0]["title"]
    assert results[0]["content"]
    assert results[0]["score"] > 0
    assert any("runbook" in result["title"] for result in results)


def test_unrelated_query_returns_no_unsupported_evidence():
    from backend.app.services.repository_intelligence import RepositoryIntelligence

    knowledge = KnowledgeBase(RepositoryIntelligence().repository_path)
    assert knowledge.search("quantum astronomy nebula", "") == []
