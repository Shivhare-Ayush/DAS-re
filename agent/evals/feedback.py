"""agent/evals/feedback.py - Arize-informed agent process control (continue vs terminate)."""
import math
from enum import Enum
from typing import Any, Dict, List, Optional

from core.schemas import AgentFeedbackVerdict, AgentStepKind, AgentStepMetric, ProcessControlAction


class FeedbackGate(str, Enum):
    POST_RECON = "POST_RECON"
    POST_GUARDRAIL = "POST_GUARDRAIL"
    POST_DAYTONA_REPRO = "POST_DAYTONA_REPRO"
    POST_DAYTONA_VERIFY = "POST_DAYTONA_VERIFY"
    POST_MEMORY_WRITE = "POST_MEMORY_WRITE"


def evaluate_gate(
    gate: FeedbackGate,
    metrics: Dict[str, Any],
) -> AgentFeedbackVerdict:
    """
    Maps OpenInference / guardrail / Daytona metrics to a continue-or-terminate decision.
    TERMINATE stops the autonomous pipeline; CONTINUE advances to the next orchestrator step.
    """
    reasons: List[str] = []

    if gate == FeedbackGate.POST_RECON:
        raw_error = metrics.get("error_rate_percent")
        try:
            error_rate = float(raw_error) if raw_error is not None else 0.0
            if math.isnan(error_rate):
                error_rate = 0.0
        except (ValueError, TypeError):
            error_rate = 0.0

        if error_rate < 5.0 and not metrics.get("force_triage", False):
            return AgentFeedbackVerdict(
                gate=gate.value,
                action=ProcessControlAction.TERMINATE,
                continue_pipeline=False,
                reason="Telemetry below triage threshold; treating as ambient noise.",
                metrics_snapshot=metrics,
            )
        reasons.append("Critical telemetry or forced triage.")
        return _continue(gate, metrics, reasons)

    if gate == FeedbackGate.POST_GUARDRAIL:
        if metrics.get("veto_triggered"):
            if metrics.get("sandbox_only_remediation_available", True):
                reasons.append("Production command vetoed; continuing on Daytona-isolated path only.")
                return _continue(gate, metrics, reasons, override_action=ProcessControlAction.CONTINUE)
            return AgentFeedbackVerdict(
                gate=gate.value,
                action=ProcessControlAction.TERMINATE,
                continue_pipeline=False,
                reason="Destructive command vetoed with no sandbox fallback.",
                metrics_snapshot=metrics,
            )
        if metrics.get("requires_voice_confirmation"):
            return AgentFeedbackVerdict(
                gate=gate.value,
                action=ProcessControlAction.STEP_UP_HUMAN,
                continue_pipeline=False,
                reason="Unclassified command requires on-call voice authorization.",
                metrics_snapshot=metrics,
            )
        return _continue(gate, metrics, reasons)

    if gate == FeedbackGate.POST_DAYTONA_REPRO:
        if not metrics.get("workspace_active"):
            return AgentFeedbackVerdict(
                gate=gate.value,
                action=ProcessControlAction.TERMINATE,
                continue_pipeline=False,
                reason="Daytona workspace failed to provision.",
                metrics_snapshot=metrics,
            )
        raw_uncertainties = metrics.get("open_uncertainty_count")
        try:
            uncertainty_count = int(raw_uncertainties) if raw_uncertainties is not None else 0
        except (ValueError, TypeError):
            uncertainty_count = 0

        if uncertainty_count > 0 and not metrics.get("defect_reproduced"):
            reasons.append("Open uncertainty requires local reproduction; continuing to patch attempt.")
            return _continue(gate, metrics, reasons)
        if not metrics.get("defect_reproduced") and metrics.get("require_reproduction", True):
            return AgentFeedbackVerdict(
                gate=gate.value,
                action=ProcessControlAction.TERMINATE,
                continue_pipeline=False,
                reason="Defect not reproduced in Daytona; cannot verify fix safely.",
                metrics_snapshot=metrics,
            )
        return _continue(gate, metrics, reasons)

    if gate == FeedbackGate.POST_DAYTONA_VERIFY:
        if not metrics.get("fix_verified"):
            return AgentFeedbackVerdict(
                gate=gate.value,
                action=ProcessControlAction.TERMINATE,
                continue_pipeline=False,
                reason="Regression tests still failing after patch in Daytona sandbox.",
                metrics_snapshot=metrics,
            )
        return _continue(gate, metrics, ["Daytona verification passed."])

    if gate == FeedbackGate.POST_MEMORY_WRITE:
        if not metrics.get("postmortem_saved"):
            return AgentFeedbackVerdict(
                gate=gate.value,
                action=ProcessControlAction.TERMINATE,
                continue_pipeline=False,
                reason="Failed to persist decision trail to SurrealDB.",
                metrics_snapshot=metrics,
            )
        return _continue(gate, metrics, ["Decision trail persisted for next on-call engineer."])

    return _continue(gate, metrics, ["Default continue."])


def _continue(
    gate: FeedbackGate,
    metrics: Dict[str, Any],
    reasons: List[str],
    override_action: Optional[ProcessControlAction] = None,
) -> AgentFeedbackVerdict:
    action = override_action or ProcessControlAction.CONTINUE
    return AgentFeedbackVerdict(
        gate=gate.value,
        action=action,
        continue_pipeline=True,
        reason=" ".join(reasons) if reasons else "Gate passed.",
        metrics_snapshot=metrics,
    )


def build_step_metric(
    step: AgentStepKind,
    *,
    trace_id: str,
    span_id: str,
    duration_ms: float,
    continue_pipeline: bool,
    action: ProcessControlAction,
    attributes: Optional[Dict[str, Any]] = None,
) -> AgentStepMetric:
    return AgentStepMetric(
        step=step,
        trace_id=trace_id,
        span_id=span_id,
        duration_ms=duration_ms,
        continue_pipeline=continue_pipeline,
        control_action=action,
        attributes=attributes or {},
    )
