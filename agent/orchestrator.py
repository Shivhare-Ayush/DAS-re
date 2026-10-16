"""agent/orchestrator.py - Core Aegis Decision & Event Orchestrator."""
import uuid
from typing import Dict, Any, List, Optional
from core.schemas import (
    AgentDecisionRecord,
    AgentRunSummary,
    AgentStepKind,
    IncidentAlert,
    GuardrailEvaluation,
    SandboxExecutionResult,
    IncidentPostmortem,
    ProcessControlAction,
)
from agent.evals.feedback import FeedbackGate, evaluate_gate
from agent.voice.client import ElevenLabsVoiceClient, MockElevenLabsVoiceClient
from agent.evals.guardrail import ArizeGuardrail, MockArizeGuardrail
from agent.evals.tracer import ArizePhoenixTracer
from agent.sandbox.client import DaytonaSandboxClient, MockDaytonaSandboxClient
from agent.browser.scrapers import AnchorReconClient, MockAnchorReconClient
from agent.memory.store import SurrealMemoryStore, MockSurrealMemoryStore
from agent.voice.prompts import (
    URGENT_ALERT_TEMPLATE,
    RECON_SUMMARY_TEMPLATE,
    GUARDRAIL_VETO_TEMPLATE,
    SUCCESS_SIGNOFF_TEMPLATE,
)


class AegisOrchestrator:
    """The central intelligence engine that coordinates the 5-way sponsor workflow."""

    def __init__(
        self,
        voice_client: Optional[ElevenLabsVoiceClient] = None,
        guardrails: Optional[ArizeGuardrail] = None,
        sandbox: Optional[DaytonaSandboxClient] = None,
        browser: Optional[AnchorReconClient] = None,
        memory: Optional[SurrealMemoryStore] = None,
        tracer: Optional[ArizePhoenixTracer] = None,
    ):
        self.voice = voice_client or MockElevenLabsVoiceClient()
        self.guardrails = guardrails or MockArizeGuardrail()
        self.sandbox = sandbox or MockDaytonaSandboxClient()
        self.browser = browser or MockAnchorReconClient()
        self.memory = memory or MockSurrealMemoryStore()
        self.tracer = tracer or ArizePhoenixTracer(is_mock=True)

    def handle_incident_alert(self, alert: IncidentAlert) -> Dict[str, Any]:
        """Step 1 & 2: Recons cloud telemetry & matches past postmortems over voice."""
        # 1. Anchor Browser extracts live metrics from Grafana/AWS console
        dashboard_url = alert.telemetry.dashboard_url if alert.telemetry else "https://grafana.internal/d/auth"
        telemetry = self.browser.scrape_dashboard(dashboard_url)

        # 2. SurrealDB finds similar past incidents via vector search & graph traversal
        similar_incidents = self.memory.query_similar_incidents(service_name=alert.service_name)
        past_fix = similar_incidents[0] if similar_incidents else None
        blast_radius = self.memory.calculate_blast_radius(alert.service_name)
        shift = self.memory.get_active_on_call_shift()
        uncertainties = self.memory.query_open_uncertainties(alert.service_name)

        # 3. ElevenLabs speaks urgent alert & recon summary to SRE
        recon_text = RECON_SUMMARY_TEMPLATE.format(
            cpu_percent=telemetry.cpu_percent,
            similar_id=past_fix.incident_id if past_fix else "N/A",
            root_cause=past_fix.root_cause if past_fix else "unknown",
        )
        voice_event = self.voice.synthesize_speech(recon_text)

        return {
            "telemetry": telemetry,
            "similar_incidents": similar_incidents,
            "blast_radius": blast_radius,
            "shift": shift,
            "uncertainties": uncertainties,
            "voice_alert": recon_text,
            "voice_event": voice_event,
        }

    def evaluate_remediation(self, command: str, incident_id: str = "INC-901") -> GuardrailEvaluation:
        """Step 3: Intercepts dangerous commands via Arize Phoenix Guardrails."""
        with self.tracer.evaluate_guardrail_span(command, incident_id) as span:
            eval_result = self.guardrails.evaluate_command(command)
            self.tracer.record_guardrail_result(span, eval_result)
            if eval_result.veto_triggered:
                veto_speech = GUARDRAIL_VETO_TEMPLATE.format(rule=eval_result.policy_violation)
                self.voice.synthesize_speech(veto_speech)
            return eval_result

    def execute_safe_remediation(
        self, repo_url: str, file_to_patch: str, patch_code: str, incident_id: str = "INC-901"
    ) -> Dict[str, Any]:
        """Step 4 & 5: Ephemeral Daytona reproduction, surgical patch & clean teardown."""
        trace_meta = self.tracer.get_active_trace_context()

        # 1. Spin up isolated Daytona cloud workspace
        ws = self.sandbox.create_workspace(repo_url)

        # 2. Reproduce Defect inside Daytona
        with self.tracer.record_daytona_execution(ws.workspace_id, "pytest tests/test_locks.py", incident_id) as span:
            initial_test = self.sandbox.exec_command(ws.workspace_id, "pytest tests/test_locks.py")
            self.tracer.complete_daytona_execution(
                span, initial_test.exit_code, initial_test.stdout, initial_test.duration_ms
            )

        # 3. Apply surgical patch inside Daytona
        self.sandbox.apply_patch(ws.workspace_id, file_to_patch, patch_code)
        with self.tracer.record_daytona_execution(
            ws.workspace_id, "pytest tests/test_locks.py (verified)", incident_id
        ) as span:
            verified_test = self.sandbox.exec_command(ws.workspace_id, "pytest tests/test_locks.py")
            self.tracer.complete_daytona_execution(
                span, verified_test.exit_code, verified_test.stdout, verified_test.duration_ms
            )

        # 4. Daytona Teardown Hook: Generate Structured Incident Report for SurrealDB Intake
        postmortem = self.generate_incident_report(
            incident_id=incident_id,
            service_name="auth-gateway",
            root_cause="Redis lock starvation under peak traffic",
            patch_code=patch_code,
            verified_test=verified_test,
            trace_meta=trace_meta,
            initial_test=initial_test,
        )

        # 5. Clean Daytona Teardown (Ephemeral workspace destroyed, zero host footprint)
        self.sandbox.destroy_workspace(ws.workspace_id)

        # 6. SurrealDB Intake: Ingest verified postmortem into Agent Memory
        self.memory.save_postmortem(postmortem)

        # 7. Reassuring ElevenLabs voice signoff to Ayush
        signoff = SUCCESS_SIGNOFF_TEMPLATE
        voice_event = self.voice.synthesize_speech(signoff)

        return {
            "workspace_id": ws.workspace_id,
            "reproduced": not initial_test.passed,
            "tests_passed": verified_test.passed,
            "postmortem_saved": True,
            "phoenix_trace": trace_meta,
            "voice_signoff": signoff,
            "voice_event": voice_event,
        }

    def run_incident_pipeline(
        self,
        alert: IncidentAlert,
        proposed_command: str,
        repo_url: str,
        file_to_patch: str,
        patch_code: str,
    ) -> Dict[str, Any]:
        """Arize continue/terminate gates, persisted onto the partner Surreal handover log."""
        recon = self.handle_incident_alert(alert)
        shift = recon.get("shift") or {}
        engineer_name = shift.get("engineer_name", "unknown")
        shift_id = shift.get("shift_id", "shift:unknown")
        trace_meta = self.tracer.get_active_trace_context()
        trace_id = trace_meta.get("phoenix_trace_id") or uuid.uuid4().hex
        decisions: List[AgentDecisionRecord] = []

        recon_verdict = evaluate_gate(
            FeedbackGate.POST_RECON,
            {
                "error_rate_percent": recon["telemetry"].error_rate_percent,
                "force_triage": alert.severity == "CRITICAL",
            },
        )
        decisions.append(self._record_gate(trace_id, alert, engineer_name, shift_id, AgentStepKind.RECON, recon_verdict, trace_meta))
        if not recon_verdict.continue_pipeline:
            self._save_run(trace_id, alert, engineer_name, shift_id, False, recon_verdict.action, decisions)
            return self._pipeline_payload(trace_id, decisions, False, recon_verdict.action, recon, {})

        guard = self.evaluate_remediation(proposed_command, alert.incident_id)
        guard_verdict = evaluate_gate(
            FeedbackGate.POST_GUARDRAIL,
            {
                "veto_triggered": guard.veto_triggered,
                "requires_voice_confirmation": guard.requires_voice_confirmation,
                "risk_score": guard.risk_score,
                "sandbox_only_remediation_available": True,
            },
        )
        decisions.append(
            self._record_gate(
                trace_id,
                alert,
                engineer_name,
                shift_id,
                AgentStepKind.GUARDRAIL,
                guard_verdict,
                trace_meta,
                metrics={"veto_triggered": guard.veto_triggered, "risk_score": guard.risk_score},
            )
        )
        if not guard_verdict.continue_pipeline:
            self._save_run(trace_id, alert, engineer_name, shift_id, False, guard_verdict.action, decisions)
            return self._pipeline_payload(trace_id, decisions, False, guard_verdict.action, recon, {})

        remed = self.execute_safe_remediation(repo_url, file_to_patch, patch_code, alert.incident_id)
        verify_verdict = evaluate_gate(
            FeedbackGate.POST_DAYTONA_VERIFY,
            {"fix_verified": remed.get("tests_passed", False)},
        )
        decisions.append(
            self._record_gate(
                trace_id, alert, engineer_name, shift_id, AgentStepKind.DAYTONA_SANDBOX, verify_verdict, trace_meta,
                daytona_workspace_id=remed.get("workspace_id"),
            )
        )
        memory_verdict = evaluate_gate(
            FeedbackGate.POST_MEMORY_WRITE,
            {"postmortem_saved": remed.get("postmortem_saved", False)},
        )
        decisions.append(
            self._record_gate(
                trace_id, alert, engineer_name, shift_id, AgentStepKind.MEMORY_WRITE, memory_verdict, trace_meta
            )
        )
        completed = verify_verdict.continue_pipeline and memory_verdict.continue_pipeline
        final_action = ProcessControlAction.CONTINUE if completed else ProcessControlAction.TERMINATE
        self._save_run(trace_id, alert, engineer_name, shift_id, completed, final_action, decisions)
        return self._pipeline_payload(
            trace_id,
            decisions,
            completed,
            final_action,
            recon,
            remed,
            remed.get("voice_signoff"),
            remed.get("voice_event"),
        )

    def _record_gate(
        self,
        trace_id,
        alert,
        engineer_name,
        shift_id,
        step,
        verdict,
        trace_meta,
        metrics=None,
        daytona_workspace_id=None,
    ) -> AgentDecisionRecord:
        record = AgentDecisionRecord(
            decision_id=f"decision:{uuid.uuid4().hex[:12]}",
            trace_id=trace_id,
            incident_id=alert.incident_id,
            engineer_name=engineer_name,
            shift_id=shift_id,
            step=step,
            gate=verdict.gate,
            control_action=verdict.action,
            continue_pipeline=verdict.continue_pipeline,
            reason=verdict.reason,
            phoenix_span_id=trace_meta.get("phoenix_span_id", "span-mock"),
            daytona_workspace_id=daytona_workspace_id,
            metrics=metrics or verdict.metrics_snapshot,
        )
        self.memory.save_agent_decision(record)
        return record

    def _save_run(self, trace_id, alert, engineer_name, shift_id, completed, final_action, decisions):
        self.memory.save_agent_run_summary(
            AgentRunSummary(
                trace_id=trace_id,
                incident_id=alert.incident_id,
                engineer_name=engineer_name,
                shift_id=shift_id,
                pipeline_completed=completed,
                final_action=final_action,
                decisions=decisions,
            )
        )

    def _pipeline_payload(self, trace_id, decisions, completed, final_action, recon, remed, signoff=None, voice_event=None):
        return {
            "trace_id": trace_id,
            "decisions": decisions,
            "pipeline_completed": completed,
            "final_action": final_action,
            "phoenix_trace": {"trace_id": trace_id, "span_count": max(len(decisions), 1), "spans": []},
            "recon": recon,
            "remediation": remed,
            "voice_signoff": signoff,
            "voice_event": voice_event,
        }

    def generate_incident_report(
        self,
        incident_id: str,
        service_name: str,
        root_cause: str,
        patch_code: str,
        verified_test: SandboxExecutionResult,
        trace_meta: Dict[str, str],
        initial_test: Optional[SandboxExecutionResult] = None,
    ) -> IncidentPostmortem:
        """
        Teardown Deprecation Hook: As Daytona destroys the sandbox, synthesizes a
        structured Incident Report optimized for SurrealDB Vector & Graph intake.
        """
        return IncidentPostmortem(
            incident_id=incident_id,
            service_name=service_name,
            root_cause=root_cause,
            resolution_diff=patch_code,
            verified_in_daytona=verified_test.passed,
            phoenix_trace_id=trace_meta.get("phoenix_trace_id"),
            phoenix_span_id=trace_meta.get("phoenix_span_id"),
            phoenix_ui_url=trace_meta.get("phoenix_ui_url"),
            guardrail_verdict="PASS",
        )
