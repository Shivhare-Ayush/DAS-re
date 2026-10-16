"""tests/test_orchestrator.py - End-to-End Orchestration Loop Tests."""
from core.schemas import IncidentAlert


def test_orchestrator_alert_handling(orchestrator, sample_alert):
    response = orchestrator.handle_incident_alert(sample_alert)

    assert response["telemetry"].cpu_percent == 98.5
    assert len(response["similar_incidents"]) > 0
    assert "INC-892" in response["voice_alert"]
    assert response["voice_event"].speaker == "AEGIS"


def test_orchestrator_guardrail_veto(orchestrator):
    eval_result = orchestrator.evaluate_remediation("redis-cli -h prod-redis FLUSHALL")
    assert eval_result.veto_triggered is True
    assert eval_result.is_safe is False


def test_orchestrator_safe_remediation_lifecycle(orchestrator):
    result = orchestrator.execute_safe_remediation(
        repo_url="https://github.com/aegis-sre/auth-gateway.git",
        file_to_patch="src/locks.py",
        patch_code="finally: self.release(key)",
    )

    assert result["reproduced"] is True
    assert result["tests_passed"] is True
    assert result["postmortem_saved"] is True
    assert "PR #42" in result["voice_signoff"]
    assert result["voice_event"].speaker == "AEGIS"
