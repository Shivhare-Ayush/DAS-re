"""agent/evals/tracer.py - OpenInference Tracing & Arize Phoenix Exporter."""
import time
from typing import Dict, Any, Optional
from core.schemas import GuardrailEvaluation


class ArizePhoenixTracer:
    """Instruments agent calls with OpenInference spans for Arize AX / Phoenix UI."""

    def __init__(self, endpoint: str = "http://localhost:6006", project_name: str = "aegis-voice-sre"):
        self.endpoint = endpoint
        self.project_name = project_name
        self.spans = []

    def start_span(self, name: str, span_kind: str = "AGENT") -> Dict[str, Any]:
        span = {
            "name": name,
            "span_kind": span_kind,
            "start_time": time.time(),
            "attributes": {},
            "status": "UNSET",
        }
        self.spans.append(span)
        return span

    def record_guardrail_eval(self, span: Dict[str, Any], evaluation: GuardrailEvaluation):
        span["attributes"]["command"] = evaluation.command
        span["attributes"]["is_safe"] = evaluation.is_safe
        span["attributes"]["risk_score"] = evaluation.risk_score
        span["attributes"]["policy_violation"] = evaluation.policy_violation or "NONE"
        span["attributes"]["veto_triggered"] = evaluation.veto_triggered
        span["status"] = "ERROR" if evaluation.veto_triggered else "OK"
        span["end_time"] = time.time()

    def record_daytona_execution(self, span: Dict[str, Any], workspace_id: str, command: str, exit_code: int, duration_ms: float):
        span["attributes"]["workspace_id"] = workspace_id
        span["attributes"]["command"] = command
        span["attributes"]["exit_code"] = exit_code
        span["attributes"]["duration_ms"] = duration_ms
        span["status"] = "OK" if exit_code == 0 else "ERROR"
        span["end_time"] = time.time()
