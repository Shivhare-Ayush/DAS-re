"""core/schemas.py - Canonical Typed Models for Aegis Voice SRE."""
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


# --- Incident & Telemetry Models ---
class TelemetryMetric(BaseModel):
    metric_name: str
    value: float
    unit: str
    timestamp: datetime = Field(default_factory=utc_now)
    anomaly_detected: bool = False


class TelemetrySnapshot(BaseModel):
    service_name: str
    dashboard_url: str
    cpu_percent: float
    error_rate_percent: float
    active_connections: int
    raw_metrics: List[TelemetryMetric] = Field(default_factory=list)
    screenshot_base64: Optional[str] = None


class IncidentAlert(BaseModel):
    incident_id: str
    service_name: str
    severity: str = "CRITICAL"  # CRITICAL | WARNING | INFO
    summary: str
    telemetry: Optional[TelemetrySnapshot] = None
    timestamp: datetime = Field(default_factory=utc_now)


# --- Arize AI Phoenix Guardrail & Eval Models ---
class GuardrailEvaluation(BaseModel):
    command: str
    is_safe: bool
    risk_score: float = Field(ge=0.0, le=1.0)  # 0.0 = safe, 1.0 = fatal blast radius
    policy_violation: Optional[str] = None
    explanation: str
    veto_triggered: bool = False
    requires_voice_confirmation: bool = False
    authorization_code: Optional[str] = None


# --- Daytona Sandbox Execution Models ---
class SandboxExecutionRequest(BaseModel):
    workspace_id: str
    command: str
    working_dir: str = "/workspaces/target"
    timeout_seconds: int = 60


class SandboxExecutionResult(BaseModel):
    workspace_id: str
    command: str
    exit_code: int
    stdout: str
    stderr: str
    duration_ms: float
    passed: bool


class WorkspaceDescriptor(BaseModel):
    workspace_id: str
    repo_url: str
    status: str  # CREATING | RUNNING | STOPPED | DESTROYED
    created_at: datetime = Field(default_factory=utc_now)


# --- SurrealDB Multi-Model Memory Models ---
class ServiceGraphNode(BaseModel):
    service_id: str
    name: str
    tier: str  # frontend | gateway | backend | database
    depends_on: List[str] = Field(default_factory=list)


class IncidentPostmortem(BaseModel):
    incident_id: str
    service_name: str
    root_cause: str
    resolution_diff: str
    verified_in_daytona: bool
    embedding: Optional[List[float]] = None
    phoenix_trace_id: Optional[str] = None
    phoenix_span_id: Optional[str] = None
    phoenix_ui_url: Optional[str] = None
    guardrail_verdict: Optional[str] = None
    timestamp: datetime = Field(default_factory=utc_now)


# --- ElevenLabs Voice Interaction Models ---
class VoiceTurnEvent(BaseModel):
    turn_id: str
    speaker: str  # "SRE" or "AEGIS"
    text: str
    audio_chunk: Optional[bytes] = None
    is_interruption: bool = False
    timestamp: datetime = Field(default_factory=utc_now)
