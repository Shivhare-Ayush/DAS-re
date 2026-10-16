"""tests/test_surreal_memory.py - Tests for SurrealDB Multi-Model Incident Memory."""
from agent.memory.store import MockSurrealMemoryStore
from core.schemas import IncidentPostmortem


def test_surreal_memory_matching():
    store = MockSurrealMemoryStore()
    results = store.query_similar_incidents(service_name="auth-gateway")

    assert len(results) == 1
    postmortem = results[0]
    assert postmortem.incident_id == "INC-892"
    assert "Redis lock starvation" in postmortem.root_cause
    assert postmortem.verified_in_daytona is True


def test_surreal_service_dependencies():
    store = MockSurrealMemoryStore()
    deps = store.get_service_dependencies("service:auth-gateway")
    assert "redis-cluster" in deps
    assert "user-db" in deps
