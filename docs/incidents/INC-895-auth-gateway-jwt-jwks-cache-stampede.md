---
incident_id: INC-895
title: "JWT Public Key Cache Stampede on Token Verification Burst"
service: auth-gateway
severity: SEV-2
status: RESOLVED
date: 2026-09-28T16:42:00Z
verified_in_daytona: true
daytona_workspace_id: ws-daytona-dtn-895
phoenix_trace_id: tr-arize-895-jwks-stampede
phoenix_span_id: span-guard-pass-02
tags: [jwt, jwks, cache-stampede, singleflight, auth-gateway, sev-2]
---

# Incident Postmortem: INC-895 — JWT Public Key Cache Stampede

## 1. Incident Overview
* **Incident ID:** INC-895
* **Impacted Service:** `auth-gateway` (tier: gateway)
* **Severity Level:** SEV-2 (High)
* **Start Time:** 2026-09-28 16:42:00 UTC
* **Resolution Time:** 2026-09-28 16:45:21 UTC (MTTR: 3m 21s)

## 2. Impact & Blast Radius
* **Symptoms:** Intermittent 502 Bad Gateway responses and p99 latency spike to 4,200ms following marketing push notification.
* **Upstream Impacted Services:** `order-router`, `payment-vault`.
* **Downstream Dependencies:** External Identity Provider (OIDC / Auth0 JWKS endpoint).
* **Blast Radius Criticality Score:** 0.65 (HIGH).

## 3. Root Cause Analysis
When the in-memory cache for the Identity Provider's JSON Web Key Set (`JWKS`) expired, 2,400 concurrent inbound requests simultaneously discovered a cache miss. In `src/jwks.py`, every thread immediately initiated an outbound HTTPS request to the IdP endpoint without synchronization (cache stampede / thundering herd), triggering strict HTTP 429 rate-limiting from the IdP.

## 4. Surgical Code Diff
```diff
--- a/src/jwks.py
+++ b/src/jwks.py
@@ -8,2 +8,4 @@
+from singleflight import Group
+g = Group()
-def get_key(kid): return fetch_key(kid)
+def get_key(kid): return g.do(kid, lambda: fetch_key(kid))
```

## 5. Daytona Cloud Sandbox Verification
* **Reproduction:** Simulated 500 concurrent key requests on cold cache using `pytest tests/test_jwks.py` inside an ephemeral Daytona sandbox. Defect confirmed: 429 rate limit exceeded.
* **Verification:** Applied Singleflight mutex patch. Re-ran test suite: exactly 1 outbound HTTPS request made; all 500 requests resolved from leader promise with 0 errors.
* **Teardown:** Sandbox destroyed cleanly in 2.1s.
