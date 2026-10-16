---
incident_id: INC-654
title: "OOM Eviction Cascade: allkeys-lru Evicted Master Replica Heartbeats"
service: redis-cluster
severity: SEV-1
status: RESOLVED
date: 2026-07-29T04:51:00Z
verified_in_daytona: true
daytona_workspace_id: ws-daytona-dtn-654
phoenix_trace_id: tr-arize-654-redis-oom-storm
phoenix_span_id: span-guard-veto-05
tags: [redis, maxmemory, eviction-policy, cluster, redis-cluster, sev-1]
---

# Incident Postmortem: INC-654 — Redis OOM Eviction Cascade

## 1. Incident Overview
* **Incident ID:** INC-654
* **Impacted Service:** `redis-cluster` (tier: cache)
* **Severity Level:** SEV-1 (Critical)
* **Start Time:** 2026-07-29 04:51:00 UTC
* **Resolution Time:** 2026-07-29 04:57:01 UTC (MTTR: 6m 01s)

## 2. Impact & Blast Radius
* **Symptoms:** Redis cluster nodes oscillating between Master and Sentinel election states; all cache reads rejected with `CLUSTERDOWN The cluster is down`.
* **Upstream Impacted Services:** `auth-gateway`, `inventory-sync`.
* **Blast Radius Criticality Score:** 0.88 (CRITICAL).

## 3. Root Cause Analysis
A new high-volume analytics caching feature populated volatile session keys without TTLs, consuming available RAM up to `maxmemory 16gb`. Because `maxmemory-policy` was set to `allkeys-lru`, Redis began evicting internal replication metadata and cluster gossip heartbeats, triggering false node failure detections and an cascading cluster failover storm.

## 4. Surgical Code Diff
```text
CONFIG SET maxmemory-policy volatile-lru;
CONFIG SET maxmemory 14gb;
```

## 5. Daytona Cloud Sandbox Verification
* **Reproduction:** Loaded 100,000 keys into 3-node Redis cluster in Daytona workspace under memory pressure with `allkeys-lru`. Replication link dropped; cluster down state triggered.
* **Verification:** Applied `volatile-lru` policy change. Re-tested: replication link preserved, master elections stabilized, zero cluster dropouts.
