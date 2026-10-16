---
incident_id: INC-741
title: "Migration Exclusive Table Lock Timeout on Accounts Schema"
service: user-db
severity: SEV-2
status: RESOLVED
date: 2026-08-14T11:22:00Z
verified_in_daytona: true
daytona_workspace_id: ws-daytona-dtn-741
phoenix_trace_id: tr-arize-741-ddl-lock-timeout
phoenix_span_id: span-guard-pass-04
tags: [postgres, ddl, lock-timeout, migration, user-db, sev-2]
---

# Incident Postmortem: INC-741 — Migration Exclusive Table Lock Timeout

## 1. Incident Overview
* **Incident ID:** INC-741
* **Impacted Service:** `user-db` (tier: database)
* **Severity Level:** SEV-2 (High)
* **Start Time:** 2026-08-14 11:22:00 UTC
* **Resolution Time:** 2026-08-14 11:26:10 UTC (MTTR: 4m 10s)

## 2. Impact & Blast Radius
* **Symptoms:** PostgreSQL max connections (500) reached; all upstream services unable to acquire database pool connections.
* **Upstream Impacted Services:** `auth-gateway`, `payment-vault`, `inventory-sync`.
* **Blast Radius Criticality Score:** 0.90 (CRITICAL).

## 3. Root Cause Analysis
An automated Alembic database migration executed `ALTER TABLE accounts ADD COLUMN flags INT DEFAULT 0;` without setting a local lock timeout. The DDL transaction queued behind a 45-minute analytical aggregate query on `accounts`. While waiting for an `AccessExclusiveLock`, it blocked all subsequent `SELECT` and `UPDATE` queries on `accounts`, queuing up all incoming connection threads until Postgres connection pool starvation occurred.

## 4. Surgical Code Diff
```sql
-- migration 0042_add_flags.sql
SET LOCAL lock_timeout = '2s';
ALTER TABLE accounts ADD COLUMN flags INT DEFAULT 0;
```

## 5. Daytona Cloud Sandbox Verification
* **Reproduction:** Spun up local PostgreSQL container inside Daytona sandbox, simulated long-running background reader, attempted naked ALTER TABLE: connection pool stalled.
* **Verification:** Prepended `SET LOCAL lock_timeout = '2s'`. Re-ran migration: statement gracefully timed out after 2s without blocking transactional reads, succeeded cleanly on subsequent retry.
