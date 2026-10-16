-- ==============================================================================
-- SurrealQL Knowledge Graph Schema & Synthetic Incident Memory Seed for DAS-re
-- Database: aegis / incidents
-- Visualizable in Surrealist: https://surrealist.app/ (or http://localhost:8000)
-- ==============================================================================

DEFINE NAMESPACE aegis;
DEFINE DATABASE incidents;
USE NS aegis DB incidents;

-- ------------------------------------------------------------------------------
-- 1. Service Nodes (Topology)
-- ------------------------------------------------------------------------------
UPSERT service:auth_gateway CONTENT {
    id: service:auth_gateway,
    name: "auth-gateway",
    tier: "gateway",
    repo_url: "https://github.com/Shivhare-Ayush/auth-gateway-demo.git",
    runtime: "python:3.12-slim",
    slo_p99_latency_ms: 250
};

UPSERT service:payment_vault CONTENT {
    id: service:payment_vault,
    name: "payment-vault",
    tier: "backend",
    repo_url: "https://github.com/aegis-sre/payment-vault.git",
    runtime: "golang:1.22",
    slo_p99_latency_ms: 120
};

UPSERT service:order_router CONTENT {
    id: service:order_router,
    name: "order-router",
    tier: "router",
    repo_url: "https://github.com/aegis-sre/order-router.git",
    runtime: "rust:1.78",
    slo_p99_latency_ms: 50
};

UPSERT service:inventory_sync CONTENT {
    id: service:inventory_sync,
    name: "inventory-sync",
    tier: "worker",
    repo_url: "https://github.com/aegis-sre/inventory-sync.git",
    runtime: "python:3.12-slim",
    slo_p99_latency_ms: 500
};

UPSERT service:redis_cluster CONTENT {
    id: service:redis_cluster,
    name: "redis-cluster",
    tier: "cache",
    repo_url: "https://github.com/aegis-sre/redis-infra.git",
    cluster_nodes: 6,
    maxmemory: "16gb"
};

UPSERT service:user_db CONTENT {
    id: service:user_db,
    name: "user-db",
    tier: "database",
    repo_url: "https://github.com/aegis-sre/user-db-cluster.git",
    engine: "PostgreSQL 16.2",
    read_replicas: 3
};

-- ------------------------------------------------------------------------------
-- 2. Graph Relations (Service Dependency Mesh)
-- ------------------------------------------------------------------------------
-- Order Router calls Payment Vault & Inventory Sync
RELATE service:order_router->depends_on->service:payment_vault SET protocol = "gRPC", timeout_ms = 800, criticality = "CRITICAL", created_at = time::now();
RELATE service:order_router->depends_on->service:inventory_sync SET protocol = "Kafka", timeout_ms = 2000, criticality = "HIGH", created_at = time::now();

-- Payment Vault calls Auth Gateway & User DB
RELATE service:payment_vault->depends_on->service:auth_gateway SET protocol = "HTTP/2", timeout_ms = 500, criticality = "CRITICAL", created_at = time::now();
RELATE service:payment_vault->depends_on->service:user_db SET protocol = "pgwire", timeout_ms = 1000, criticality = "CRITICAL", created_at = time::now();

-- Auth Gateway calls Redis Cluster & User DB
RELATE service:auth_gateway->depends_on->service:redis_cluster SET protocol = "RESP3", timeout_ms = 200, criticality = "CRITICAL", created_at = time::now();
RELATE service:auth_gateway->depends_on->service:user_db SET protocol = "pgwire", timeout_ms = 1000, criticality = "HIGH", created_at = time::now();

-- Inventory Sync calls Redis & User DB
RELATE service:inventory_sync->depends_on->service:redis_cluster SET protocol = "RESP3", timeout_ms = 300, criticality = "MEDIUM", created_at = time::now();
RELATE service:inventory_sync->depends_on->service:user_db SET protocol = "pgwire", timeout_ms = 1500, criticality = "HIGH", created_at = time::now();

-- ------------------------------------------------------------------------------
-- 3. Incident Postmortems (Vector Embeddings + Daytona Verification Proofs)
-- ------------------------------------------------------------------------------
UPSERT postmortem:INC_892 CONTENT {
    incident_id: "INC-892",
    service_name: "auth-gateway",
    severity: "SEV-1",
    title: "Redis lock starvation under peak traffic spike",
    root_cause: "Redis lock starvation: Critical section in locks.py threw unhandled database blip exception before reaching release() handle, causing locks to remain allocated indefinitely until Redis TTL expired.",
    resolution_diff: "--- a/src/locks.py\n+++ b/src/locks.py\n@@ -14,5 +14,8 @@\n     def process_critical_section(self, key: str, should_fail: bool = False):\n         self.acquire(key)\n+        try:\n             if should_fail:\n                 raise ValueError(\"Unexpected database network blip during processing\")\n+        finally:\n+            self.release(key)\n",
    verified_in_daytona: true,
    daytona_workspace_id: "ws-daytona-dtn-892",
    daytona_test_duration_s: 4.82,
    phoenix_trace_id: "tr-arize-892-lock-starvation",
    phoenix_span_id: "span-guard-veto-01",
    phoenix_ui_url: "http://localhost:6006/projects/aegis-sre/traces/tr-arize-892",
    embedding: [0.92, 0.12, 0.05, 0.01, 0.02, 0.22, 0.11, 0.31],
    date: "2026-09-21T03:14:00Z"
};

UPSERT postmortem:INC_895 CONTENT {
    incident_id: "INC-895",
    service_name: "auth-gateway",
    severity: "SEV-2",
    title: "JWT public key cache stampede on token verification burst",
    root_cause: "Missing singleflight mutex around JWKS URL fetch caused 2,400 concurrent upstream HTTP requests to IdP upon cache TTL expiry.",
    resolution_diff: "--- a/src/jwks.py\n+++ b/src/jwks.py\n@@ -8,2 +8,4 @@\n+from singleflight import Group\n+g = Group()\n-def get_key(kid): return fetch_key(kid)\n+def get_key(kid): return g.do(kid, lambda: fetch_key(kid))\n",
    verified_in_daytona: true,
    daytona_workspace_id: "ws-daytona-dtn-895",
    daytona_test_duration_s: 3.41,
    phoenix_trace_id: "tr-arize-895-jwks-stampede",
    phoenix_span_id: "span-guard-pass-02",
    phoenix_ui_url: "http://localhost:6006/projects/aegis-sre/traces/tr-arize-895",
    embedding: [0.85, 0.18, 0.08, 0.02, 0.05, 0.19, 0.09, 0.28],
    date: "2026-09-28T16:42:00Z"
};

UPSERT postmortem:INC_812 CONTENT {
    incident_id: "INC-812",
    service_name: "payment-vault",
    severity: "SEV-1",
    title: "Idempotency key duplicate race condition under mobile retry flood",
    root_cause: "Insert-then-commit gap in idempotency table allowed two concurrent webhook deliveries with the same key to charge card twice.",
    resolution_diff: "--- a/src/idempotency.go\n+++ b/src/idempotency.go\n@@ -22,2 +22,3 @@\n-SELECT status FROM keys WHERE key = $1;\n-INSERT INTO keys (key, status) VALUES ($1, 'PENDING');\n+INSERT INTO keys (key, status) VALUES ($1, 'PENDING')\n+ON CONFLICT (key) DO NOTHING RETURNING id;\n",
    verified_in_daytona: true,
    daytona_workspace_id: "ws-daytona-dtn-812",
    daytona_test_duration_s: 5.12,
    phoenix_trace_id: "tr-arize-812-idempotency-race",
    phoenix_span_id: "span-guard-veto-03",
    phoenix_ui_url: "http://localhost:6006/projects/aegis-sre/traces/tr-arize-812",
    embedding: [0.15, 0.22, 0.10, 0.89, 0.78, 0.05, 0.08, 0.12],
    date: "2026-09-02T19:05:00Z"
};

UPSERT postmortem:INC_741 CONTENT {
    incident_id: "INC-741",
    service_name: "user-db",
    severity: "SEV-2",
    title: "Migration exclusive table lock timeout on accounts schema",
    root_cause: "DDL ALTER TABLE query executed without local lock_timeout queued behind long-running analytical report, starving connection pool.",
    resolution_diff: "SET LOCAL lock_timeout = '2s'; ALTER TABLE accounts ADD COLUMN flags INT DEFAULT 0;",
    verified_in_daytona: true,
    daytona_workspace_id: "ws-daytona-dtn-741",
    daytona_test_duration_s: 4.10,
    phoenix_trace_id: "tr-arize-741-ddl-lock-timeout",
    phoenix_span_id: "span-guard-pass-04",
    phoenix_ui_url: "http://localhost:6006/projects/aegis-sre/traces/tr-arize-741",
    embedding: [0.05, 0.88, 0.91, 0.12, 0.01, 0.04, 0.10, 0.02],
    date: "2026-08-14T11:22:00Z"
};

UPSERT postmortem:INC_654 CONTENT {
    incident_id: "INC-654",
    service_name: "redis-cluster",
    severity: "SEV-1",
    title: "OOM eviction cascade: allkeys-lru evicted master replica heartbeats",
    root_cause: "Session cache expansion exceeded maxmemory; allkeys-lru evicted internal replication offset keys, causing cluster failover storm.",
    resolution_diff: "CONFIG SET maxmemory-policy volatile-lru; CONFIG SET maxmemory 14gb;",
    verified_in_daytona: true,
    daytona_workspace_id: "ws-daytona-dtn-654",
    daytona_test_duration_s: 6.01,
    phoenix_trace_id: "tr-arize-654-redis-oom-storm",
    phoenix_span_id: "span-guard-veto-05",
    phoenix_ui_url: "http://localhost:6006/projects/aegis-sre/traces/tr-arize-654",
    embedding: [0.78, 0.09, 0.04, 0.03, 0.15, 0.88, 0.35, 0.20],
    date: "2026-07-29T04:51:00Z"
};

UPSERT postmortem:INC_709 CONTENT {
    incident_id: "INC-709",
    service_name: "order-router",
    severity: "SEV-2",
    title: "gRPC deadline propagation cascade causing thread pool starvation",
    root_cause: "Missing timeout budget subtraction on downstream payment calls caused gateway threads to wait 30s while client already disconnected.",
    resolution_diff: "--- a/src/client.rs\n+++ b/src/client.rs\n@@ -15,1 +15,2 @@\n-let mut req = Request::new(payload);\n+let remaining = ctx.deadline().saturating_duration_since(Instant::now());\n+let mut req = Request::new(payload).set_timeout(remaining);\n",
    verified_in_daytona: true,
    daytona_workspace_id: "ws-daytona-dtn-709",
    daytona_test_duration_s: 3.88,
    phoenix_trace_id: "tr-arize-709-grpc-deadlines",
    phoenix_span_id: "span-guard-pass-06",
    phoenix_ui_url: "http://localhost:6006/projects/aegis-sre/traces/tr-arize-709",
    embedding: [0.32, 0.15, 0.22, 0.65, 0.81, 0.12, 0.15, 0.40],
    date: "2026-08-03T14:19:00Z"
};

-- ------------------------------------------------------------------------------
-- 4. Rotating SRE Shift Handover Memory (Institutional Context)
-- ------------------------------------------------------------------------------
UPSERT shift:active CONTENT {
    shift_id: "shift:2026-w42-primary",
    engineer_name: "Ayush Shivhare",
    role: "Primary On-Call SRE",
    shift_start: "2026-10-16T08:00:00Z",
    shift_end: "2026-10-23T08:00:00Z",
    iam_role: "sre-elevated-triage",
    handover_notes_from_previous: "Previous shift (Alice Chen): Saw brief 200ms lock latency spikes on auth-gateway around 4:15 AM during marketing email batch. No alerts fired, but keep an eye on Redis client count."
};

UPSERT shift:w41 CONTENT {
    shift_id: "shift:2026-w41-previous",
    engineer_name: "Alice Chen",
    role: "Previous On-Call SRE",
    shift_start: "2026-10-09T08:00:00Z",
    shift_end: "2026-10-16T08:00:00Z",
    iam_role: "sre-read-only",
    handover_notes_from_previous: "Previous shift (Marcus Vance): Completed failover rehearsal on user-db replica 2. All connection pooling normalized."
};

UPSERT shift:w40 CONTENT {
    shift_id: "shift:2026-w40-historical",
    engineer_name: "Marcus Vance",
    role: "Senior Staff SRE",
    shift_start: "2026-10-02T08:00:00Z",
    shift_end: "2026-10-09T08:00:00Z",
    iam_role: "sre-admin",
    handover_notes_from_previous: "Quarterly disaster recovery drill concluded. Re-indexed SurrealDB HNSW vector index on postmortems."
};

-- ------------------------------------------------------------------------------
-- 5. Operational Uncertainties & Active Hypotheses
-- ------------------------------------------------------------------------------
UPSERT uncertainty:001 CONTENT {
    id: "uncertainty:001",
    service: "auth-gateway",
    observation: "Spike in HTTP 504s could be caused by either Redis maxclients saturation (4096) or application-level deadlock in locks.py.",
    verification_step: "Run 'pytest tests/test_locks.py' inside Daytona isolated sandbox to verify if locks leak locally without touching live Redis cluster.",
    status: "OPEN",
    created_at: "2026-10-16T02:20:00Z"
};

UPSERT uncertainty:002 CONTENT {
    id: "uncertainty:002",
    service: "payment-vault",
    observation: "Transient Stripe webhook 429 rate limit backoff might be masquerading as database connection pool exhaustion in worker threads.",
    verification_step: "Inspect pg_stat_activity active worker count vs external HTTP egress latency in Grafana dashboard.",
    status: "OPEN",
    created_at: "2026-10-16T03:15:00Z"
};

UPSERT uncertainty:003 CONTENT {
    id: "uncertainty:003",
    service: "user-db",
    observation: "Autovacuum worker freeze risk on high-throughput ledger table.",
    verification_step: "Check pg_stat_user_tables n_dead_tup percentage.",
    status: "RESOLVED",
    created_at: "2026-10-15T18:00:00Z"
};
