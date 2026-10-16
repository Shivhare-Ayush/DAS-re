---
incident_id: INC-812
title: "Idempotency Key Duplicate Race Condition Under Mobile Retry Flood"
service: payment-vault
severity: SEV-1
status: RESOLVED
date: 2026-09-02T19:05:00Z
verified_in_daytona: true
daytona_workspace_id: ws-daytona-dtn-812
phoenix_trace_id: tr-arize-812-idempotency-race
phoenix_span_id: span-guard-veto-03
tags: [payment, idempotency, race-condition, stripe, payment-vault, sev-1]
---

# Incident Postmortem: INC-812 — Idempotency Key Duplicate Race Condition

## 1. Incident Overview
* **Incident ID:** INC-812
* **Impacted Service:** `payment-vault` (tier: backend)
* **Severity Level:** SEV-1 (Critical)
* **Start Time:** 2026-09-02 19:05:00 UTC
* **Resolution Time:** 2026-09-02 19:10:12 UTC (MTTR: 5m 12s)

## 2. Impact & Blast Radius
* **Symptoms:** 42 duplicate credit card charges reported across iOS mobile app checkout during flaky LTE cell handoffs.
* **Upstream Impacted Services:** `order-router` (duplicate order fulfillment initiated).
* **Downstream Dependencies:** `user-db`, Stripe API.
* **Blast Radius Criticality Score:** 0.95 (CRITICAL).

## 3. Root Cause Analysis
In `src/idempotency.go`, request handling checked key existence with `SELECT status FROM keys WHERE key = $1` and then executed a separate `INSERT INTO keys ...` statement. Under rapid mobile client retry bursts (< 15ms apart), two goroutines passed the `SELECT` check before either transaction committed, causing both workers to issue non-idempotent charge authorizations to the payment gateway.

## 4. Surgical Code Diff
```diff
--- a/src/idempotency.go
+++ b/src/idempotency.go
@@ -22,2 +22,3 @@
-SELECT status FROM keys WHERE key = $1;
-INSERT INTO keys (key, status) VALUES ($1, 'PENDING');
+INSERT INTO keys (key, status) VALUES ($1, 'PENDING')
+ON CONFLICT (key) DO NOTHING RETURNING id;
```

## 5. Daytona Cloud Sandbox Verification
* **Reproduction:** Ran parallel concurrency harness `go test -race ./tests/idempotency_test.go` in isolated Daytona workspace `ws-daytona-dtn-812`. Race condition reproduced: 2 duplicate charges created.
* **Verification:** Injected atomic `ON CONFLICT DO NOTHING` SQL patch. Re-ran test suite: exactly 1 charge created, duplicate rejected with clean HTTP 409 Conflict. All 18 tests passed.
* **Teardown:** Sandbox destroyed cleanly in 2.4s.
