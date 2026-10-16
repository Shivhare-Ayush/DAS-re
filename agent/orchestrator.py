"""agent/orchestrator.py - Core Aegis Decision & Event Orchestrator."""
from typing import Dict, Any, Optional
from core.schemas import (
    IncidentAlert,
    TelemetrySnapshot,
    GuardrailEvaluation,
    SandboxExecutionResult,
    IncidentPostmortem,
    VoiceTurnEvent,
)
from agent.voice.client import ElevenLabsVoiceClient, MockElevenLabsVoiceClient
from agent.evals.guardrail import ArizeGuardrail, MockArizeGuardrail
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
    ):
        self.voice = voice_client or MockElevenLabsVoiceClient()
        self.guardrails = guardrails or MockArizeGuardrail()
        self.sandbox = sandbox or MockDaytonaSandboxClient()
        self.browser = browser or MockAnchorReconClient()
        self.memory = memory or MockSurrealMemoryStore()

    def handle_incident_alert(self, alert: IncidentAlert) -> Dict[str, Any]:
        """Step 1 & 2: Recons cloud telemetry & matches past postmortems over voice."""
        # 1. Anchor Browser extracts live metrics from Grafana/AWS console
        dashboard_url = alert.telemetry.dashboard_url if alert.telemetry else "https://grafana.internal/d/auth"
        telemetry = self.browser.scrape_dashboard(dashboard_url)

        # 2. SurrealDB finds similar past incidents via vector search
        similar_incidents = self.memory.query_similar_incidents(service_name=alert.service_name)
        past_fix = similar_incidents[0] if similar_incidents else None

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
            "voice_alert": recon_text,
            "voice_event": voice_event,
        }

    def evaluate_remediation(self, command: str) -> GuardrailEvaluation:
        """Step 3: Intercepts dangerous commands via Arize Phoenix Guardrails."""
        eval_result = self.guardrails.evaluate_command(command)
        if eval_result.veto_triggered:
            veto_speech = GUARDRAIL_VETO_TEMPLATE.format(rule=eval_result.policy_violation)
            self.voice.synthesize_speech(veto_speech)
        return eval_result

    def execute_safe_remediation(
        self, repo_url: str, file_to_patch: str, patch_code: str
    ) -> Dict[str, Any]:
        """Step 4 & 5: Ephemeral Daytona reproduction, surgical patch & clean teardown."""
        # 1. Spin up isolated Daytona cloud workspace
        ws = self.sandbox.create_workspace(repo_url)

        # 2. Reproduce Defect inside Daytona
        initial_test = self.sandbox.exec_command(ws.workspace_id, "pytest tests/test_locks.py")

        # 3. Apply surgical patch inside Daytona
        self.sandbox.apply_patch(ws.workspace_id, file_to_patch, patch_code)
        verified_test = self.sandbox.exec_command(ws.workspace_id, "pytest tests/test_locks.py")

        # 4. Clean Teardown
        self.sandbox.destroy_workspace(ws.workspace_id)

        # 5. Save verified postmortem to SurrealDB
        postmortem = IncidentPostmortem(
            incident_id="INC-901",
            service_name="auth-gateway",
            root_cause="Redis lock starvation under peak traffic",
            resolution_diff=patch_code,
            verified_in_daytona=verified_test.passed,
        )
        self.memory.save_postmortem(postmortem)

        # 6. Reassuring ElevenLabs voice signoff to Ayush
        signoff = SUCCESS_SIGNOFF_TEMPLATE
        voice_event = self.voice.synthesize_speech(signoff)

        return {
            "workspace_id": ws.workspace_id,
            "reproduced": not initial_test.passed,
            "tests_passed": verified_test.passed,
            "postmortem_saved": True,
            "voice_signoff": signoff,
            "voice_event": voice_event,
        }
