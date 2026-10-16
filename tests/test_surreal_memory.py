"""tests/test_surreal_memory.py - Tests for SurrealDB Multi-Model Incident Memory."""
from unittest.mock import MagicMock, patch
from agent.memory.decisions import agent_decision_id, agent_run_id, decision_document, run_document
from agent.memory.store import SurrealMemoryStore, MockSurrealMemoryStore
from core.schemas import (
    AgentDecisionRecord,
    AgentRunSummary,
    AgentStepKind,
    IncidentPostmortem,
    ProcessControlAction,
)


def test_surreal_memory_matching():
    store = MockSurrealMemoryStore()
    results = store.query_similar_incidents(service_name="auth-gateway")

    assert len(results) >= 1
    postmortem = results[0]
    assert postmortem.incident_id == "INC-892"
    assert "Redis lock starvation" in postmortem.root_cause
    assert postmortem.verified_in_daytona is True


def test_surreal_vector_similarity_matching():
    store = MockSurrealMemoryStore()
    # Query vector very close to INC-892 (Redis lock starvation)
    query_vector = [0.90, 0.10, 0.04, 0.02, 0.01, 0.20, 0.10, 0.30]
    results = store.query_similar_incidents(service_name="auth-gateway", embedding=query_vector)

    assert len(results) >= 1
    assert results[0].incident_id == "INC-892"


def test_surreal_service_dependencies():
    store = MockSurrealMemoryStore()
    # Downstream dependencies (out)
    deps = store.get_service_dependencies("service:auth-gateway", direction="out")
    assert "redis-cluster" in deps
    assert "user-db" in deps


def test_surreal_upstream_callers():
    store = MockSurrealMemoryStore()
    # Upstream callers / dependents (in)
    callers = store.get_service_dependencies("service:auth-gateway", direction="in")
    assert "payment-vault" in callers


def test_surreal_calculate_blast_radius():
    store = MockSurrealMemoryStore()
    blast = store.calculate_blast_radius("service:auth-gateway")

    assert blast["target_service"] == "auth-gateway"
    assert "payment-vault" in blast["upstream_impacted_services"]
    assert "redis-cluster" in blast["downstream_dependencies"]
    assert blast["total_impacted_services"] >= 2
    assert blast["criticality"] == "CRITICAL"
    assert blast["blast_radius_score"] >= 0.5


def test_surreal_shift_handover():
    store = MockSurrealMemoryStore()
    shift = store.get_active_on_call_shift()

    assert shift["engineer_name"] == "Ayush Shivhare"
    assert "Primary On-Call SRE" in shift["role"]
    assert "Alice Chen" in shift["handover_notes"]


def test_surreal_uncertainties():
    store = MockSurrealMemoryStore()
    uncertainties = store.query_open_uncertainties(service_name="auth-gateway")

    assert len(uncertainties) >= 1
    u = uncertainties[0]
    assert u["service"] == "auth-gateway"
    assert "deadlock" in u["observation"] or "connection pool" in u["observation"]

    # Test saving new uncertainty
    new_u = {
        "id": "uncertainty:002",
        "service": "payment-vault",
        "observation": "Downstream timeouts during auth-gateway lock starvation.",
        "verification_step": "Run synthetic transaction check post-remediation.",
        "status": "OPEN",
    }
    assert store.save_uncertainty(new_u) is True
    updated = store.query_open_uncertainties("payment-vault")
    assert any(x["id"] == "uncertainty:002" for x in updated)


def test_surreal_save_postmortem():
    store = MockSurrealMemoryStore()
    pm = IncidentPostmortem(
        incident_id="INC-999",
        service_name="payment-vault",
        root_cause="Cascading gateway 504 timeout",
        resolution_diff="increase timeout to 5s",
        verified_in_daytona=True,
    )
    assert store.save_postmortem(pm) is True
    res = store.query_similar_incidents(service_name="payment-vault")
    assert any(p.incident_id == "INC-999" for p in res)


def test_surreal_live_client_mock_sdk():
    mock_db = MagicMock()
    mock_db.query.return_value = [
        {
            "result": [
                {
                    "incident_id": "INC-777",
                    "service_name": "auth-gateway",
                    "root_cause": "Database connection drop",
                    "resolution_diff": "pool_recycle=300",
                    "verified_in_daytona": True,
                }
            ]
        }
    ]

    mock_surreal_cls = MagicMock(return_value=mock_db)
    mock_settings = MagicMock()
    mock_settings.IS_MOCK_MODE = False
    mock_settings.SURREALDB_URL = "ws://localhost:8000/rpc"
    mock_settings.SURREALDB_USER = "root"
    mock_settings.SURREALDB_PASS = "root"
    mock_settings.SURREALDB_NS = "aegis"
    mock_settings.SURREALDB_DB = "incidents"

    with patch("surrealdb.Surreal", mock_surreal_cls), patch(
        "core.config.get_settings", return_value=mock_settings
    ):
        store = SurrealMemoryStore(url="ws://localhost:8000/rpc")
        assert store._db is not None

        # Test vector query
        results = store.query_similar_incidents("auth-gateway", embedding=[0.1, 0.2])
        assert len(results) == 1
        assert results[0].incident_id == "INC-777"
        mock_db.query.assert_called_once()

        # Test live save_postmortem uses parameterized UPSERT query
        pm = IncidentPostmortem(
            incident_id="INC-888",
            service_name="auth-gateway",
            root_cause="OOM",
            resolution_diff="fix",
            verified_in_daytona=True,
        )
        assert store.save_postmortem(pm) is True
        last_query = mock_db.query.call_args[0][0]
        assert "UPSERT type::thing('postmortem'" in last_query

        # Test live save_uncertainty uses parameterized UPSERT query
        u = {"id": "uncertainty:999", "service": "auth-gateway", "observation": "test", "status": "OPEN"}
        assert store.save_uncertainty(u) is True
        last_query_u = mock_db.query.call_args[0][0]
        assert "UPSERT type::thing('uncertainty'" in last_query_u


def test_surreal_unknown_service_and_sanitization():
    store = MockSurrealMemoryStore()
    # Unknown service must return empty list (not phantom defaults)
    assert store.get_service_dependencies("service:nonexistent-microservice") == []

    # Invalid characters rejected
    live_store = SurrealMemoryStore()
    assert live_store.get_service_dependencies("service:bad;DROP TABLE service;") == []


def test_surreal_uncertainty_filtering_exact_service():
    store = MockSurrealMemoryStore()
    # Add an uncertainty for user-db
    store.save_uncertainty({
        "id": "uncertainty:userdb-1",
        "service": "user-db",
        "observation": "Lock timeout on accounts table.",
        "status": "OPEN",
    })

    # Query for auth-gateway only -> must NOT contain user-db
    auth_uncertainties = store.query_open_uncertainties("auth-gateway")
    assert all(u["service"] == "auth-gateway" for u in auth_uncertainties)
    assert not any(u["service"] == "user-db" for u in auth_uncertainties)


def test_surreal_agent_decision_handover():
    store = MockSurrealMemoryStore()
    store.save_agent_decision(
        AgentDecisionRecord(
            decision_id="decision:test001",
            trace_id="trace-abc",
            incident_id="INC-901",
            engineer_name="Ayush Shivhare",
            shift_id="shift:2026-w42-primary",
            step=AgentStepKind.GUARDRAIL,
            gate="POST_GUARDRAIL",
            control_action=ProcessControlAction.CONTINUE,
            continue_pipeline=True,
            reason="Vetoed prod command; Daytona path only.",
            phoenix_span_id="span-1",
            daytona_workspace_id="ws-daytona-mock-42",
        )
    )
    store.save_agent_run_summary(
        AgentRunSummary(
            trace_id="trace-abc",
            incident_id="INC-901",
            engineer_name="Ayush Shivhare",
            shift_id="shift:2026-w42-primary",
            pipeline_completed=True,
            final_action=ProcessControlAction.CONTINUE,
        )
    )
    runs = store.get_agent_runs_for_handover(limit=1)
    assert runs[0].trace_id == "trace-abc"


def test_agent_trail_documents_match_partner_schema():
    decision = AgentDecisionRecord(
        decision_id="decision:test001",
        trace_id="abc123",
        incident_id="INC-901",
        engineer_name="Ayush Shivhare",
        shift_id="shift:2026-w42-primary",
        step=AgentStepKind.GUARDRAIL,
        gate="POST_GUARDRAIL",
        control_action=ProcessControlAction.CONTINUE,
        continue_pipeline=True,
        reason="Daytona path only.",
        phoenix_span_id="span-1",
    )
    doc = decision_document(decision)
    assert agent_decision_id(decision.decision_id) == "agent_decision:test001"
    assert agent_run_id(decision.trace_id) == "agent_run:abc123"
    assert doc["control_action"] == "CONTINUE"
    assert "timestamp" not in doc
    assert "recorded_at" in doc

    summary = AgentRunSummary(
        trace_id="abc123",
        incident_id="INC-901",
        engineer_name="Ayush Shivhare",
        shift_id="shift:2026-w42-primary",
        pipeline_completed=True,
        final_action=ProcessControlAction.CONTINUE,
        decisions=[decision],
    )
    run = run_document(summary)
    assert "decisions" not in run
    assert run["shift_id"] == "shift:2026-w42-primary"
    assert run["phoenix_project"] == "aegis-voice-sre"
