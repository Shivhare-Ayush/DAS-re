"""agent/evals/policies.py - Zero-Trust Execution Policies (IBM MCSP Heritage)."""
import re
from enum import Enum
from typing import Tuple


class CommandSafetyTier(str, Enum):
    TIER_0_AMBIENT_READ = "TIER_0_AMBIENT_READ"      # Safe (pytest, git diff, ps)
    TIER_1_SANDBOX_WRITE = "TIER_1_SANDBOX_WRITE"    # Safe in Daytona (git apply, patch)
    TIER_2_DESTRUCTIVE_VETO = "TIER_2_DESTRUCTIVE_VETO" # Hard Veto (FLUSHALL, rm -rf, DROP)
    TIER_3_STEP_UP_HUMAN = "TIER_3_STEP_UP_HUMAN"    # Requires Voice 2FA confirmation


# Prohibited destructive commands that trigger hard veto
VETO_PATTERNS = [
    (r"\bFLUSHALL\b", "DESTRUCTIVE_REDIS_FLUSHALL", "Full flush of production cache keys."),
    (r"\bFLUSHDB\b", "DESTRUCTIVE_REDIS_FLUSHDB", "Full flush of active database keys."),
    (r"\bDROP\s+TABLE\b", "DESTRUCTIVE_SQL_DROP", "Direct table dropping on live store."),
    (r"\bTRUNCATE\b", "DESTRUCTIVE_SQL_TRUNCATE", "Mass deletion of database rows."),
    (r"\brm\s+-rf\s+(?:/|\*|/etc|/var)(?:\s+|$|\S*)", "DESTRUCTIVE_SHELL_RM", "Recursive uncontained root file deletion."),
    (r"\bchmod\s+777\b", "INSECURE_PERMISSIONS", "Overly permissive world-writable file mode."),
    (r"\baws\s+iam\s+attach-admin\b", "PRIVILEGE_ESCALATION", "Unbounded IAM privilege escalation."),
]

# Read-only patterns that are always Tier 0
READ_ONLY_PREFIXES = ("pytest", "git status", "git diff", "git log", "cat", "grep", "ls", "ps")


def evaluate_policy(command: str) -> Tuple[CommandSafetyTier, float, str, str]:
    """
    Evaluates a command against Zero-Trust policies.
    Returns: (tier, risk_score, policy_violation, explanation)
    """
    cmd = command.strip()

    # Check for hard vetoes first
    for pattern, rule_id, desc in VETO_PATTERNS:
        if re.search(pattern, cmd, re.IGNORECASE):
            return (
                CommandSafetyTier.TIER_2_DESTRUCTIVE_VETO,
                0.99,
                rule_id,
                f"Blocked dangerous operation: {desc}",
            )

    # Check for read-only Tier 0
    if cmd.startswith(READ_ONLY_PREFIXES):
        return (
            CommandSafetyTier.TIER_0_AMBIENT_READ,
            0.05,
            "",
            "Read-only diagnostic or test execution.",
        )

    # Check for sandbox write Tier 1
    if "python scripts/" in cmd or "git apply" in cmd or "pytest" in cmd:
        return (
            CommandSafetyTier.TIER_1_SANDBOX_WRITE,
            0.25,
            "",
            "Scoped sandbox patch or test script.",
        )

    # Default to Tier 3 step-up
    return (
        CommandSafetyTier.TIER_3_STEP_UP_HUMAN,
        0.75,
        "UNCLASSIFIED_COMMAND",
        "Command alters state outside standard sandbox profiles; requires SRE verbal authorization.",
    )
