-- SurrealQL Knowledge Graph Schema & Data Seed for DAS-re SRE
-- Load via: surreal import --conn ws://localhost:8000/rpc --user root --pass root --ns aegis --db incidents scripts/surreal_seed.surql
-- Or execute directly in Surrealist (https://surrealist.app/)

DEFINE NAMESPACE aegis;
DEFINE DATABASE incidents;
USE NS aegis DB incidents;

-- Define Service Nodes
UPSERT service:auth_gateway CONTENT {
    id: service:auth_gateway,
    name: "auth-gateway",
    tier: "gateway",
    repo_url: "https://github.com/Shivhare-Ayush/auth-gateway-demo.git"
};

UPSERT service:redis_cluster CONTENT {
    id: service:redis_cluster,
    name: "redis-cluster",
    tier: "cache",
    repo_url: "https://github.com/aegis-sre/redis-infra.git"
};

UPSERT service:user_db CONTENT {
    id: service:user_db,
    name: "user-db",
    tier: "database",
    repo_url: "https://github.com/aegis-sre/user-db-cluster.git"
};

UPSERT service:payment_vault CONTENT {
    id: service:payment_vault,
    name: "payment-vault",
    tier: "backend",
    repo_url: "https://github.com/aegis-sre/payment-vault.git"
};

-- Define Graph Relations (Edges)
RELATE service:payment_vault->depends_on->service:auth_gateway SET criticality = "CRITICAL", created_at = time::now();
RELATE service:auth_gateway->depends_on->service:redis_cluster SET criticality = "HIGH", created_at = time::now();
RELATE service:auth_gateway->depends_on->service:user_db SET criticality = "CRITICAL", created_at = time::now();

-- Define Shift Handover
UPSERT shift:active CONTENT {
    shift_id: "shift:2026-w42-primary",
    engineer_name: "Ayush Shivhare",
    role: "Primary On-Call SRE",
    shift_start: "2026-10-16T08:00:00Z",
    shift_end: "2026-10-23T08:00:00Z",
    iam_role: "sre-elevated-triage",
    handover_notes_from_previous: "Previous shift (Alice Chen): Saw brief 200ms lock latency spikes on auth-gateway around 4:15 AM during marketing email batch. No alerts fired, but keep an eye on Redis client count."
};

-- Define Past Incident Postmortem with Embeddings
UPSERT postmortem:INC_892 CONTENT {
    incident_id: "INC-892",
    service_name: "auth-gateway",
    severity: "SEV-1",
    title: "Redis lock starvation under peak traffic spike",
    root_cause: "Redis lock starvation: Critical section in locks.py threw unhandled database blip exception before reaching release() handle, causing locks to remain allocated indefinitely until Redis TTL expired.",
    resolution_diff: "--- a/src/locks.py\n+++ b/src/locks.py\n@@ -14,5 +14,8 @@\n     def process_critical_section(self, key: str, should_fail: bool = False):\n         self.acquire(key)\n+        try:\n             if should_fail:\n                 raise ValueError(\"Unexpected database network blip during processing\")\n+        finally:\n+            self.release(key)\n",
    verified_in_daytona: true,
    embedding: [0.92, 0.12, 0.05, 0.01, 0.02, 0.22, 0.11, 0.31]
};

-- Define Operational Uncertainty
UPSERT uncertainty:001 CONTENT {
    id: "uncertainty:001",
    service: "auth-gateway",
    observation: "Spike in HTTP 504s could be caused by either Redis maxclients saturation (4096) or application-level deadlock in locks.py.",
    verification_step: "Run 'pytest tests/test_locks.py' inside Daytona isolated sandbox to verify if locks leak locally without touching live Redis cluster.",
    status: "OPEN"
};
