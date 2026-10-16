---
incident_id: INC-709
title: "gRPC Deadline Propagation Cascade Causing Thread Starvation"
service: order-router
severity: SEV-2
status: RESOLVED
date: 2026-08-03T14:19:00Z
verified_in_daytona: true
daytona_workspace_id: ws-daytona-dtn-709
phoenix_trace_id: tr-arize-709-grpc-deadlines
phoenix_span_id: span-guard-pass-06
tags: [grpc, deadline-propagation, timeouts, rust, order-router, sev-2]
---

# Incident Postmortem: INC-709 — gRPC Deadline Cascade

## 1. Incident Overview
* **Incident ID:** INC-709
* **Impacted Service:** `order-router` (tier: router)
* **Severity Level:** SEV-2 (High)
* **Start Time:** 2026-08-03 14:19:00 UTC
* **Resolution Time:** 2026-08-03 14:22:48 UTC (MTTR: 3m 48s)

## 2. Impact & Blast Radius
* **Symptoms:** Upstream API Gateway thread starvation with 504 timeouts; order checkout requests timing out after 30 seconds.
* **Upstream Impacted Services:** Public Web & Mobile storefronts.
* **Downstream Dependencies:** `payment-vault`, `inventory-sync`.
* **Blast Radius Criticality Score:** 0.75 (HIGH).

## 3. Root Cause Analysis
In `src/client.rs`, the router forwarded gRPC requests to `payment-vault` with fixed 30-second timeouts without subtracting the elapsed time already spent in the caller's deadline context. When client devices gave up after 5 seconds, downstream worker threads in `order-router` and `payment-vault` continued executing costly cryptographic operations for orphaned requests.

## 4. Surgical Code Diff
```diff
--- a/src/client.rs
+++ b/src/client.rs
@@ -15,1 +15,2 @@
-let mut req = Request::new(payload);
+let remaining = ctx.deadline().saturating_duration_since(Instant::now());
+let mut req = Request::new(payload).set_timeout(remaining);
```

## 5. Daytona Cloud Sandbox Verification
* **Reproduction:** Injected 100 canceled client contexts into `cargo test --test deadline_test` in Daytona. Orphaned requests continued running for 30s.
* **Verification:** Injected deadline propagation patch. Re-tested: all downstream calls canceled synchronously when parent deadline passed, freeing worker threads within 12ms.
