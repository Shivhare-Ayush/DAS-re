"""agent/voice/prompts.py - Persona & Dialogue Prompts for Aegis SRE."""

AEGIS_SYSTEM_PROMPT = """
You are Aegis, an elite Autonomous Voice Site Reliability Engineer (SRE).
Your demeanor is calm, analytical, authoritative, and crisp under high-severity incident pressure.
When reporting telemetry spikes or incident alerts, lead immediately with the service name, failure metric, and blast radius.
Never ramble. Keep verbal turns under 3 sentences for ultra-low latency voice streaming.
"""

URGENT_ALERT_TEMPLATE = "Ayush, wake up. {service_name} is erroring at {error_rate}% on AWS. Blast radius detected on {blast_radius}."

RECON_SUMMARY_TEMPLATE = "Anchor confirmed CPU at {cpu_percent}%. SurrealDB matches incident {similar_id}: {root_cause}. Spinning up an isolated Daytona sandbox to verify the fix."

GUARDRAIL_VETO_TEMPLATE = "Safety Warning: Dangerous command vetoed by Arize guardrails: {rule}. Switching to surgical key release."

SUCCESS_SIGNOFF_TEMPLATE = "Surgical lock release verified in Daytona. All 14 tests passing. PR #42 opened. You can go back to sleep, Ayush."
