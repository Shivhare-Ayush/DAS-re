"""tests/conftest.py - Pytest Fixtures and Mock Client Providers."""
import pytest
from core.config import Settings
from core.schemas import TelemetrySnapshot, IncidentAlert
from agent.voice.client import MockElevenLabsVoiceClient
from agent.evals.guardrail import MockArizeGuardrail
from agent.sandbox.client import MockDaytonaSandboxClient
from agent.browser.scrapers import MockAnchorReconClient
from agent.memory.store import MockSurrealMemoryStore
from agent.orchestrator import AegisOrchestrator


@pytest.fixture
def mock_settings():
    return Settings(
        DAYTONA_API_KEY="mock_daytona",
        ELEVENLABS_API_KEY="mock_elevenlabs",
        PHOENIX_COLLECTOR_ENDPOINT="http://localhost:6006",
        ANCHOR_API_KEY="mock_anchor",
        SURREALDB_URL="ws://localhost:8000/rpc",
        IS_MOCK_MODE=True,
    )


@pytest.fixture
def sample_alert():
    return IncidentAlert(
        incident_id="INC-101",
        service_name="auth-gateway",
        severity="CRITICAL",
        summary="Redis lock starvation under 94% error rate.",
        telemetry=TelemetrySnapshot(
            service_name="auth-gateway",
            dashboard_url="https://grafana.internal/d/auth",
            cpu_percent=98.5,
            error_rate_percent=94.2,
            active_connections=4200,
        ),
    )


@pytest.fixture
def orchestrator():
    return AegisOrchestrator(
        voice_client=MockElevenLabsVoiceClient(),
        guardrails=MockArizeGuardrail(),
        sandbox=MockDaytonaSandboxClient(),
        browser=MockAnchorReconClient(),
        memory=MockSurrealMemoryStore(),
    )
