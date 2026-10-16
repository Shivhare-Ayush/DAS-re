"""core/events.py - Asynchronous Event Bus Definitions for Aegis."""
from enum import Enum
from datetime import datetime
from typing import Any, Dict, Optional
from pydantic import BaseModel, Field


class EventType(str, Enum):
    INCIDENT_DETECTED = "incident.detected"
    TELEMETRY_SCRAPED = "telemetry.scraped"
    MEMORY_MATCHED = "memory.matched"
    GUARDRAIL_VETO = "guardrail.veto"
    GUARDRAIL_APPROVED = "guardrail.approved"
    SANDBOX_CREATED = "sandbox.created"
    SANDBOX_EXEC_COMPLETED = "sandbox.exec.completed"
    SANDBOX_DESTROYED = "sandbox.destroyed"
    VOICE_STREAM_IN = "voice.stream.in"
    VOICE_STREAM_OUT = "voice.stream.out"


class EventEnvelope(BaseModel):
    event_id: str
    event_type: EventType
    source: str
    payload: Dict[str, Any]
    timestamp: datetime = Field(default_factory=datetime.utcnow)
