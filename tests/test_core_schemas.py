"""tests/test_core_schemas.py - Unit Tests for Core Contracts."""
from core.schemas import (
    TelemetrySnapshot,
    IncidentAlert,
    GuardrailEvaluation,
    SandboxExecutionResult,
)
from core.config import Settings


def test_core_schemas_instantiation():
    telemetry = TelemetrySnapshot(
        service_name="auth-gateway",
        dashboard_url="https://grafana.internal/d/auth",
        cpu_percent=98.5,
        error_rate_percent=94.2,
        active_connections=4200,
    )
    assert telemetry.cpu_percent == 98.5

    alert = IncidentAlert(
        incident_id="INC-101",
        service_name="auth-gateway",
        severity="CRITICAL",
        summary="Redis lock exhaustion leading to 504 gateway timeouts",
        telemetry=telemetry,
    )
    assert alert.incident_id == "INC-101"
    assert alert.telemetry.error_rate_percent == 94.2

    guardrail = GuardrailEvaluation(
        command="redis-cli FLUSHALL",
        is_safe=False,
        risk_score=0.95,
        policy_violation="DESTRUCTIVE_FLUSH_DETECTED",
        explanation="Attempted full database wipe on production Redis cluster.",
        veto_triggered=True,
    )
    assert guardrail.veto_triggered is True
    assert guardrail.is_safe is False

    exec_result = SandboxExecutionResult(
        workspace_id="ws-daytona-99",
        command="pytest",
        exit_code=0,
        stdout="14 passed in 0.42s",
        stderr="",
        duration_ms=420.0,
        passed=True,
    )
    assert exec_result.passed is True


def test_settings_default_fallback():
    settings = Settings(
        DAYTONA_API_KEY="test_daytona",
        ELEVENLABS_API_KEY="test_eleven",
        PHOENIX_COLLECTOR_ENDPOINT="http://localhost:6006",
        SURREALDB_URL="ws://localhost:8000/rpc",
        ANCHOR_API_KEY="test_anchor",
    )
    assert settings.DAYTONA_API_KEY == "test_daytona"
