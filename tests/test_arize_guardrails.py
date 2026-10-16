"""tests/test_arize_guardrails.py - Tests for Arize Phoenix Guardrails."""
from agent.evals.guardrail import MockArizeGuardrail
from agent.evals.policies import CommandSafetyTier, evaluate_policy


def test_destructive_command_triggers_veto():
    guardrail = MockArizeGuardrail()
    eval_result = guardrail.evaluate_command("redis-cli -h prod-redis FLUSHALL")

    assert eval_result.is_safe is False
    assert eval_result.veto_triggered is True
    assert eval_result.risk_score >= 0.9
    assert eval_result.policy_violation == "DESTRUCTIVE_REDIS_FLUSHALL"


def test_safe_command_passes_tier_0():
    tier, risk, violation, _ = evaluate_policy("pytest tests/test_locks.py")
    assert tier == CommandSafetyTier.TIER_0_AMBIENT_READ
    assert risk < 0.1
    assert violation == ""


def test_rm_rf_hard_veto():
    guardrail = MockArizeGuardrail()
    eval_result = guardrail.evaluate_command("rm -rf /")
    assert eval_result.veto_triggered is True
    assert eval_result.policy_violation == "DESTRUCTIVE_SHELL_RM"
