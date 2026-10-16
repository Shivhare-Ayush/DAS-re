"""agent/evals/tracer.py - OpenTelemetry & OpenInference Tracing for Arize Phoenix."""
import os
import time
from contextlib import contextmanager
from typing import Optional, Dict, Any, Generator
from core.schemas import GuardrailEvaluation

# Graceful optional imports for OpenTelemetry and Phoenix
try:
    from opentelemetry import trace
    from opentelemetry.trace import StatusCode, Status, Span
    from openinference.semconv.trace import (
        SpanAttributes,
        OpenInferenceSpanKindValues,
    )
    from phoenix.otel import register
    from phoenix.client import Client
    HAS_PHOENIX = True
except ImportError:
    HAS_PHOENIX = False


class ArizePhoenixTracer:
    """Instruments DAS-re agent actions with OpenInference spans for Arize Phoenix."""

    def __init__(
        self,
        endpoint: str = "http://localhost:6006/v1/traces",
        project_name: str = "aegis-voice-sre",
        is_mock: bool = False,
    ):
        self.endpoint = endpoint
        self.project_name = project_name
        self.is_mock = is_mock or not HAS_PHOENIX
        self.base_url = endpoint.replace("/v1/traces", "")
        self.spans = []
        self.tracer = None
        self.client = None

        if not self.is_mock and HAS_PHOENIX:
            try:
                self.tracer_provider = register(
                    endpoint=self.endpoint,
                    project_name=self.project_name,
                    protocol="http/protobuf",
                    batch=False,
                    set_global_tracer_provider=True,
                    auto_instrument=True,
                )
                self.tracer = trace.get_tracer("das-re.tracer")
                try:
                    self.client = Client(base_url=self.base_url)
                except Exception:
                    self.client = None
            except Exception:
                self.is_mock = True

    @contextmanager
    def trace_incident(self, incident_id: str, service_name: str) -> Generator[Any, None, None]:
        """Root AGENT span encompassing the incident resolution lifecycle."""
        if not self.is_mock and self.tracer:
            with self.tracer.start_as_current_span(f"Incident-Triage: {service_name}") as span:
                span.set_attribute(
                    SpanAttributes.OPENINFERENCE_SPAN_KIND,
                    OpenInferenceSpanKindValues.AGENT.value,
                )
                span.set_attribute(SpanAttributes.SESSION_ID, incident_id)
                span.set_attribute("incident.service_name", service_name)
                span.set_attribute(SpanAttributes.INPUT_VALUE, f"Service outage on {service_name}")
                yield span
        else:
            mock_span = {"name": f"Incident-Triage: {service_name}", "session_id": incident_id}
            yield mock_span

    @contextmanager
    def evaluate_guardrail_span(self, command: str, incident_id: str = "INC-901") -> Generator[Any, None, None]:
        """Evaluates proposed remediation command against zero-trust policies."""
        if not self.is_mock and self.tracer:
            with self.tracer.start_as_current_span("guardrail_policy_gate") as span:
                span.set_attribute(
                    SpanAttributes.OPENINFERENCE_SPAN_KIND,
                    OpenInferenceSpanKindValues.GUARDRAIL.value,
                )
                span.set_attribute(SpanAttributes.SESSION_ID, incident_id)
                span.set_attribute(SpanAttributes.INPUT_VALUE, command)
                yield span
        else:
            mock_span = {"name": "guardrail_policy_gate", "command": command, "incident_id": incident_id}
            yield mock_span

    def record_guardrail_result(self, span: Any, evaluation: GuardrailEvaluation):
        """Attaches guardrail verdicts, triggers RED/GREEN UI rendering and badge annotations."""
        if not self.is_mock and HAS_PHOENIX and hasattr(span, "set_attribute"):
            span.set_attribute(SpanAttributes.OUTPUT_VALUE, evaluation.explanation)
            span.set_attribute("guardrail.is_safe", evaluation.is_safe)
            span.set_attribute("guardrail.risk_score", evaluation.risk_score)
            span.set_attribute("guardrail.policy_violation", evaluation.policy_violation or "NONE")
            span.set_attribute("guardrail.veto_triggered", evaluation.veto_triggered)
            span.set_attribute("guardrail.wrong_answer_returns_200", evaluation.veto_triggered)

            ctx = span.get_span_context()
            span_id_hex = format(ctx.span_id, "016x") if ctx.is_valid else None

            if evaluation.veto_triggered:
                # TURNS SPAN RED IN PHOENIX FLAME GRAPH
                span.set_status(Status(StatusCode.ERROR, description=f"VETO: {evaluation.policy_violation}"))
                label = "VETO"
                score = 0.0
            else:
                # TURNS GREEN IN PHOENIX FLAME GRAPH
                span.set_status(Status(StatusCode.OK, description="Policy verified"))
                label = "PASS"
                score = 1.0

            if self.client and span_id_hex:
                try:
                    self.client.spans.add_span_annotation(
                        span_id=span_id_hex,
                        annotation_name="Security Guardrail",
                        annotator_kind="CODE",
                        label=label,
                        score=score,
                        explanation=evaluation.explanation,
                        metadata={
                            "command": evaluation.command,
                            "risk_score": evaluation.risk_score,
                            "policy_violation": evaluation.policy_violation,
                            "wrong_answer_returns_200": evaluation.veto_triggered,
                        },
                        sync=False,
                    )
                except Exception:
                    pass
        elif isinstance(span, dict):
            span["is_safe"] = evaluation.is_safe
            span["veto_triggered"] = evaluation.veto_triggered
            span["status"] = "ERROR" if evaluation.veto_triggered else "OK"

    @contextmanager
    def record_daytona_execution(
        self, workspace_id: str, command: str, incident_id: str = "INC-901"
    ) -> Generator[Any, None, None]:
        """Instruments Daytona sandbox reproduction and patch verification."""
        if not self.is_mock and self.tracer:
            with self.tracer.start_as_current_span("daytona_sandbox_exec") as span:
                span.set_attribute(
                    SpanAttributes.OPENINFERENCE_SPAN_KIND,
                    OpenInferenceSpanKindValues.TOOL.value,
                )
                span.set_attribute(SpanAttributes.SESSION_ID, incident_id)
                span.set_attribute(SpanAttributes.TOOL_NAME, "daytona_cloud_sandbox")
                span.set_attribute(SpanAttributes.INPUT_VALUE, command)
                span.set_attribute("daytona.workspace_id", workspace_id)
                yield span
        else:
            mock_span = {"name": "daytona_sandbox_exec", "workspace_id": workspace_id, "command": command}
            yield mock_span

    def complete_daytona_execution(self, span: Any, exit_code: int, stdout: str, duration_ms: float):
        if not self.is_mock and HAS_PHOENIX and hasattr(span, "set_attribute"):
            span.set_attribute(SpanAttributes.OUTPUT_VALUE, stdout[:2000])
            span.set_attribute("daytona.exit_code", exit_code)
            span.set_attribute("daytona.duration_ms", duration_ms)

            if exit_code != 0:
                span.set_status(Status(StatusCode.ERROR, description=f"Sandbox test failed (exit {exit_code})"))
            else:
                span.set_status(Status(StatusCode.OK))
        elif isinstance(span, dict):
            span["exit_code"] = exit_code
            span["duration_ms"] = duration_ms
            span["status"] = "OK" if exit_code == 0 else "ERROR"

    def get_active_trace_context(self) -> Dict[str, str]:
        """Extracts current trace and span context with official Phoenix redirect URLs."""
        if not self.is_mock and HAS_PHOENIX:
            try:
                current_span = trace.get_current_span()
                ctx = current_span.get_span_context()
                if ctx.is_valid:
                    trace_id = format(ctx.trace_id, "032x")
                    span_id = format(ctx.span_id, "016x")
                    return {
                        "phoenix_trace_id": trace_id,
                        "phoenix_span_id": span_id,
                        "phoenix_ui_url": f"{self.base_url}/redirects/traces/{trace_id}",
                    }
            except Exception:
                pass
        return {
            "phoenix_trace_id": "trace-mock-8921a",
            "phoenix_span_id": "span-mock-001b",
            "phoenix_ui_url": "http://localhost:6006/redirects/traces/trace-mock-8921a",
        }

    # Backward compatibility helpers
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
