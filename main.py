"""main.py - Aegis Autonomous Voice SRE Live Demo Runner."""
import argparse
import sys
import time

# Ensure UTF-8 output on Windows terminals
if sys.stdout.encoding != "utf-8":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

from core.schemas import IncidentAlert, TelemetrySnapshot
from agent.orchestrator import AegisOrchestrator


def run_demo():
    print("=" * 65)
    print("[AEGIS] AUTONOMOUS VOICE SRE & ZERO-TRUST CLOUD OPERATOR")
    print("        Daytona HackSprint #6 | JFK27 Basement, New York City")
    print("=" * 65)
    print()

    orchestrator = AegisOrchestrator()

    # Step 1: Inbound Incident Alert
    print("[02:15 AM] PagerDuty Incident Alert Inbound...")
    alert = IncidentAlert(
        incident_id="INC-901",
        service_name="auth-gateway",
        severity="CRITICAL",
        summary="auth-gateway is erroring at 94.2% on AWS. Blast radius detected.",
    )
    time.sleep(0.3)

    # Step 2: Telemetry Ingestion & SurrealDB Memory Lookup
    print("[TELEMETRY] Ingesting CloudWatch & Prometheus Metrics via Incident Webhook...")
    print("[MEMORY] Querying SurrealDB Multi-Model Engine (HNSW Vector + Dependency Graph)...")
    recon_res = orchestrator.handle_incident_alert(alert)
    print(f"[VOICE] ElevenLabs Audio Stream: \"{recon_res['voice_alert']}\"")
    print()

    # Step 2b: SurrealDB Knowledge Graph & Blast Radius
    blast = recon_res.get("blast_radius", {})
    shift = recon_res.get("shift", {})
    upstream_list = ", ".join(blast.get("upstream_impacted_services", []))
    downstream_list = ", ".join(blast.get("downstream_dependencies", []))

    print("[SURREALDB KNOWLEDGE GRAPH] Multi-Model Graph Traversal & Blast Radius:")
    print("  +--------------------------------------------------------------------+")
    print("  | [Graph Traversal] Directional Service Dependency Mapping           |")
    print("  |                                                                    |")
    print("  |   payment-vault (tier: backend)                                    |")
    print("  |         |                                                          |")
    print("  |         v  <-depends_on<-                                          |")
    print(f"  |   {alert.service_name} (tier: gateway)  <-- [TARGET OUTAGE: {alert.severity:<8}]     |")
    print("  |         +--> ->depends_on-> redis-cluster (tier: cache)            |")
    print("  |         +--> ->depends_on-> user-db (tier: database)               |")
    print("  |                                                                    |")
    print(f"  | Upstream Impacted: [{upstream_list}]                              |")
    print(f"  | Downstream Deps  : [{downstream_list}]                      |")
    print(f"  | Criticality      : {blast.get('criticality', 'N/A'):<8} (Blast Radius Score: {blast.get('blast_radius_score', 0.0)})          |")
    print("  +--------------------------------------------------------------------+")
    print(f"[SURREALDB SHIFT MEMORY] Active On-Call: {shift.get('engineer_name')} ({shift.get('role')})")
    print(f"                         Handover Notes : \"{shift.get('handover_notes')}\"")
    print()

    from agent.memory.arize_csv import graph_edges_from_spans, load_arize_spans

    print("[ARIZE -> SURREAL GRAPH] Phoenix span CSV linked onto the service graph:")
    for edge in graph_edges_from_spans(load_arize_spans()):
        if edge["span_kind"] not in ("AGENT", "CHAIN"):
            continue
        print(
            f"  {edge['engineer']} ({edge['timezone']}) -[{edge['control_action']}]-> "
            f"{edge['service']}  trace={edge['trace_id']}  "
            f"latency={edge['latency_ms']}ms  error_rate={edge['error_rate']}%"
        )
        print(f"    phoenix:{edge['span_name']} status={edge['status_code']} | {edge['output']}")
    print()

    # Step 3: Zero-Trust Guardrail Veto
    time.sleep(0.3)
    dangerous_cmd = "redis-cli -h prod-redis FLUSHALL && chmod 777 /etc/auth"
    print(f"[THREAT] Agent proposes uncontained fix: '{dangerous_cmd}'")
    print("[EVALS] Evaluating command with Arize AI Phoenix Zero-Trust Guardrails...")
    guard_res = orchestrator.evaluate_remediation(dangerous_cmd)
    if guard_res.veto_triggered:
        print(f"[VETO TRIGGERED] Risk Score: {guard_res.risk_score} | Rule: {guard_res.policy_violation}")
        print(f"                 Explanation: {guard_res.explanation}")
        print("[VOICE] ElevenLabs Audio Stream: \"Safety Warning: Dangerous command vetoed by Arize guardrails. Switching to surgical key release.\"")
    print()

    # Step 4: Daytona Ephemeral Sandbox Execution
    time.sleep(0.3)
    print("[SANDBOX] Provisioning ephemeral cloud sandbox via Daytona SDK (daytona.create)...")
    repo = "https://github.com/aegis-sre/auth-gateway.git"
    patch = "finally: self.release(key)"
    
    print("[TEST] Reproducing defect in isolated Daytona workspace...")
    print("[PATCH] Applying surgical patch to src/locks.py inside Daytona...")
    print("[VERIFY] Running regression test suite in Daytona...")
    remed_res = orchestrator.execute_safe_remediation(repo, "src/locks.py", patch)
    print(f"[CLEANUP] Daytona workspace '{remed_res['workspace_id']}' destroyed cleanly (Zero host risk).")
    print(f"[VOICE] ElevenLabs Audio Stream: \"{remed_res['voice_signoff']}\"")
    print()
    print("=" * 65)
    print("[SUCCESS] DEMO COMPLETE: 100% Deterministic Walkthrough Verified.")
    print("=" * 65)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Aegis Voice SRE")
    parser.add_argument("--demo", action="store_true", help="Run deterministic live pitch demo")
    args = parser.parse_args()

    run_demo()
