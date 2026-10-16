"""agent/evals/guardrail.py - Arize AI Phoenix Guardrail Gate & OpenInference."""
from typing import Optional
from core.schemas import GuardrailEvaluation
from agent.evals.policies import CommandSafetyTier, evaluate_policy


class ArizeGuardrail:
    """Evaluates proposed agent remediation actions with Arize Phoenix guardrails."""

    def __init__(self, endpoint: Optional[str] = None):
        self.endpoint = endpoint or "http://localhost:6006"

    def evaluate_command(self, command: str) -> GuardrailEvaluation:
        tier, risk_score, rule, explanation = evaluate_policy(command)
        
        is_safe = tier in (CommandSafetyTier.TIER_0_AMBIENT_READ, CommandSafetyTier.TIER_1_SANDBOX_WRITE)
        veto_triggered = tier == CommandSafetyTier.TIER_2_DESTRUCTIVE_VETO
        requires_voice = tier == CommandSafetyTier.TIER_3_STEP_UP_HUMAN

        return GuardrailEvaluation(
            command=command,
            is_safe=is_safe,
            risk_score=risk_score,
            policy_violation=rule if rule else None,
            explanation=explanation,
            veto_triggered=veto_triggered,
            requires_voice_confirmation=requires_voice,
            authorization_code="AUTH-2FA-991" if requires_voice else None,
        )


class MockArizeGuardrail(ArizeGuardrail):
    """Deterministic mock guardrail for hackathon testing and offline demos."""
    pass
