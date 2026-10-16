---
incident_id: INC-892
title: "Redis Lock Starvation Under Peak Traffic Spike"
service: auth-gateway
severity: SEV-1
status: RESOLVED
date: 2026-09-21T03:14:00Z
verified_in_daytona: true
daytona_workspace_id: ws-daytona-dtn-892
phoenix_trace_id: tr-arize-892-lock-starvation
phoenix_span_id: span-guard-veto-01
tags: [redis, distributed-locks, concurrency, auth-gateway, sev-1]
---

# Incident Postmortem: INC-892 — Redis Lock Starvation

## 1. Incident Overview
* **Incident ID:** INC-892
* **Impacted Service:** `auth-gateway` (tier: gateway)
* **Severity Level:** SEV-1 (Critical)
* **Start Time:** 2026-09-21 03:14:00 UTC
* **Resolution Time:** 2026-09-21 03:18:49 UTC (MTTR: 4m 49s)
* **Primary On-Call:** Ayush Shivhare (Shift: `shift:2026-w42-primary`)

## 2. Impact & Blast Radius
* **Symptoms:** HTTP 504 Gateway Timeout spike reaching 94.2% error rate across US-East-1.
* **Upstream Impacted Services:** `payment-vault` (Stripe charge authorization queues stalled; checkout drop-off exceeded $140k/hr).
* **Downstream Dependencies:** `redis-cluster`, `user-db`.
* **Blast Radius Criticality Score:** 0.85 (CRITICAL).

## 3. Root Cause Analysis
During high-concurrency token authentication in `src/locks.py`, `process_critical_section` acquired a distributed Redis key lock. When an intermittent database network blip occurred during internal payload validation, an unhandled `ValueError` exception was raised prior to calling `self.release(key)`. The distributed lock remained held indefinitely in Redis until the default TTL expired, causing all subsequent client requests for that authentication key to queue and timeout.

## 4. Surgical Code Diff
```diff
--- a/src/locks.py
+++ b/src/locks.py
@@ -14,5 +14,8 @@
     def process_critical_section(self, key: str, should_fail: bool = False):
         self.acquire(key)
+        try:
             if should_fail:
                 raise ValueError("Unexpected database network blip during processing")
+        finally:
+            self.release(key)
```

## 5. Daytona Cloud Sandbox Verification
* **Container Lifecycle:** Ephemeral cloud workspace spawned in 4.1 seconds via official Daytona SDK (`daytona.create`).
* **Defect Reproduction:** Cloned `auth-gateway`, injected failure test scenario: `pytest tests/test_locks.py` terminated with **Exit Code 1 (Defect Confirmed)**.
* **Surgical Patching:** Applied safe base64-decoded patch to `src/locks.py`.
* **Regression Testing:** Re-ran `pytest tests/test_locks.py` with **14/14 tests passing in 4.82s (Exit Code 0)**.
* **Teardown Deprecation Hook:** Harvested execution trace metrics and git diff into SurrealDB postmortem before deleting the workspace. Workspace `ws-daytona-dtn-892` destroyed cleanly with **0 residual host resources**.

## 6. Arize Phoenix Guardrail Interception
* **Trace ID:** `tr-arize-892-lock-starvation`
* **Veto Event:** Autonomous remediation agent initially proposed `redis-cli -h prod-redis FLUSHALL && chmod 777 /etc/auth`.
* **Policy Triggered:** `DESTRUCTIVE_REDIS_FLUSHALL` (Risk Score: 0.99).
* **Action:** Hard veto applied. Red span emitted in Phoenix UI. Agent automatically rerouted to surgical lock release.
