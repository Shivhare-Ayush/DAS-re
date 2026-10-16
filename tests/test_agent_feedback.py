"""tests/test_agent_feedback.py - Arize feedback gates and E2E pipeline decisions."""
from agent.evals.feedback import FeedbackGate, evaluate_gate
from core.schemas import IncidentAlert, ProcessControlAction, TelemetrySnapshot
from agent.evals.tracer import ArizePhoenixTracer


def test_feedback_terminates_low_error_rate():
    verdict = evaluate_gate(FeedbackGate.POST_RECON, {"error_rate_percent": 1.0, "force_triage": False})
    assert verdict.continue_pipeline is False
    assert verdict.action == ProcessControlAction.TERMINATE


def test_feedback_continues_critical_triage():
    verdict = evaluate_gate(FeedbackGate.POST_RECON, {"error_rate_percent": 1.0, "force_triage": True})
    assert verdict.continue_pipeline is True


def test_feedback_veto_continues_to_daytona_only():
    verdict = evaluate_gate(
        FeedbackGate.POST_GUARDRAIL,
        {"veto_triggered": True, "sandbox_only_remediation_available": True},
    )
    assert verdict.continue_pipeline is True


def test_feedback_terminates_failed_daytona_verify():
    verdict = evaluate_gate(FeedbackGate.POST_DAYTONA_VERIFY, {"fix_verified": False})
    assert verdict.continue_pipeline is False
    assert verdict.action == ProcessControlAction.TERMINATE


def test_orchestrator_pipeline_records_decisions(orchestrator, sample_alert):
    result = orchestrator.run_incident_pipeline(
        alert=sample_alert,
        proposed_command="redis-cli FLUSHALL",
        repo_url="https://github.com/aegis-sre/auth-gateway.git",
        file_to_patch="src/locks.py",
        patch_code="finally: self.release(key)",
    )

    assert result["trace_id"]
    assert len(result["decisions"]) >= 4
    assert result["pipeline_completed"] is True
    assert result["final_action"] == ProcessControlAction.CONTINUE
    assert result["phoenix_trace"]["span_count"] >= 4
    handover = orchestrator.memory.get_agent_runs_for_handover(limit=1)
    assert len(handover) == 1
    assert handover[0].trace_id == result["trace_id"]


def test_tracer_mock_context():
    tracer = ArizePhoenixTracer(is_mock=True)
    ctx = tracer.get_active_trace_context()
    assert ctx["phoenix_trace_id"]
    assert ctx["phoenix_ui_url"].startswith("http://localhost:6006")
