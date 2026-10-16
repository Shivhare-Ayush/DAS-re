"""agent/memory/decisions.py - Persist Arize gate decisions onto the partner Surreal graph.

Uses the same record-id style as agent/memory/seed_data.py:
shift:{id}, postmortem:{incident_id}. Safe to call when Surreal is down;
callers keep the in-memory mock path.
"""
from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Any, Dict, List, Optional

from core.schemas import AgentDecisionRecord, AgentRunSummary, ProcessControlAction

TRAIL_SCHEMA = Path(__file__).parent / "schema_agent_trail.surql"


def agent_run_id(trace_id: str) -> str:
    return f"agent_run:{_key(trace_id)}"


def agent_decision_id(decision_id: str) -> str:
    return f"agent_decision:{_key(decision_id)}"


def postmortem_id(incident_id: str) -> str:
    key = incident_id if incident_id.startswith("postmortem:") else incident_id
    if key.startswith("postmortem:"):
        return key
    return f"postmortem:{key}"


def _key(value: str) -> str:
    return value.split(":")[-1].replace("`", "")


def decision_document(decision: AgentDecisionRecord) -> Dict[str, Any]:
    payload = decision.model_dump(mode="json")
    payload["step"] = decision.step.value
    payload["control_action"] = decision.control_action.value
    payload["recorded_at"] = payload.pop("timestamp", None)
    payload["metrics"] = payload.get("metrics") or {}
    return payload


def run_document(summary: AgentRunSummary, phoenix_project: str = "aegis-voice-sre") -> Dict[str, Any]:
    return {
        "trace_id": summary.trace_id,
        "incident_id": summary.incident_id,
        "engineer_name": summary.engineer_name,
        "shift_id": summary.shift_id,
        "pipeline_completed": summary.pipeline_completed,
        "final_action": summary.final_action.value,
        "daytona_workspace_id": summary.daytona_workspace_id,
        "phoenix_project": phoenix_project,
        "recorded_at": summary.decisions[-1].timestamp.isoformat() if summary.decisions else None,
    }


def summary_from_row(row: Dict[str, Any]) -> AgentRunSummary:
    action = row.get("final_action") or ProcessControlAction.CONTINUE.value
    return AgentRunSummary(
        trace_id=row.get("trace_id", ""),
        incident_id=row.get("incident_id", ""),
        engineer_name=row.get("engineer_name", ""),
        shift_id=row.get("shift_id", ""),
        pipeline_completed=bool(row.get("pipeline_completed")),
        final_action=ProcessControlAction(action),
        daytona_workspace_id=row.get("daytona_workspace_id"),
    )


def apply_trail_schema(db) -> None:
    if not TRAIL_SCHEMA.exists():
        return
    script = TRAIL_SCHEMA.read_text(encoding="utf-8")
    return db.query(script)


async def save_decision(db, decision: AgentDecisionRecord) -> str:
    record_id = agent_decision_id(decision.decision_id)
    await db.upsert(record_id, decision_document(decision))
    run_id = agent_run_id(decision.trace_id)
    await _relate_if_present(db, f"RELATE {run_id}->produced->{record_id};")
    return record_id


async def save_run(db, summary: AgentRunSummary, phoenix_project: str = "aegis-voice-sre") -> str:
    record_id = agent_run_id(summary.trace_id)
    await db.upsert(record_id, run_document(summary, phoenix_project))
    shift_id = summary.shift_id if summary.shift_id.startswith("shift:") else f"shift:{summary.shift_id}"
    await _relate_if_present(db, f"RELATE {record_id}->during->{shift_id};")
    await _relate_if_present(
        db,
        f"RELATE {record_id}->concerns->{postmortem_id(summary.incident_id)};",
    )
    return record_id


async def _relate_if_present(db, statement: str) -> None:
    try:
        await db.query(statement)
    except Exception:
        return


async def fetch_recent_runs(db, limit: int) -> List[AgentRunSummary]:
    result = await db.query(
        "SELECT * FROM agent_run ORDER BY recorded_at DESC LIMIT $limit;",
        {"limit": limit},
    )
    rows = _unwrap_rows(result)
    return [summary_from_row(row) for row in rows if isinstance(row, dict)]


def _unwrap_rows(result: Any) -> List[Dict[str, Any]]:
    if isinstance(result, list) and result and isinstance(result[0], dict) and "result" in result[0]:
        inner = result[0]["result"]
        return inner if isinstance(inner, list) else []
    if isinstance(result, list):
        return [row for row in result if isinstance(row, dict)]
    return []


def run_against_surreal(url: str, user: str, password: str, namespace: str, database: str, operation):
    try:
        from surrealdb import AsyncSurreal as SurrealClient
    except ImportError:
        from surrealdb import Surreal as SurrealClient

    async def _go():
        async with SurrealClient(url) as db:
            await db.signin({"username": user, "password": password})
            await db.use(namespace, database)
            return await operation(db)

    return asyncio.run(_go())
