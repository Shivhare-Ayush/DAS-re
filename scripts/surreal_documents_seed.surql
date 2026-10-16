-- ==============================================================================
-- Document Node Ingestion for SurrealDB Knowledge Graph
-- Transforms markdown incident reports into queryable document nodes & graph edges
-- ==============================================================================
USE NS aegis DB incidents;

-- Document: INC-654 (OOM Eviction Cascade: allkeys-lru Evicted Master Replica Heartbeats)
UPSERT document:INC_654 CONTENT {
    id: document:INC_654,
    incident_id: "INC-654",
    title: "OOM Eviction Cascade: allkeys-lru Evicted Master Replica Heartbeats",
    service: "redis-cluster",
    severity: "SEV-1",
    file_name: "INC-654-redis-cluster-oom-eviction-cascade.md",
    preview: "# Incident Postmortem: INC-654 — Redis OOM Eviction Cascade  ## 1. Incident Overview * **Incident ID:** INC-654 * **Impacted Service:** `redis-cluster` (tier: cache) * **Severity Level:** SEV-1 (Critical) * **Start Time:** 2026-07-29 04:51:00 UTC * **Resolution Time:** 2026-07-29 04:57:01 UTC (MTTR:...",
    ingested_at: time::now()
};
RELATE service:redis_cluster->has_incident_doc->document:INC_654 SET relationship = 'documented_in', created_at = time::now();
RELATE postmortem:INC_654->documented_in->document:INC_654 SET relationship = 'formal_postmortem', created_at = time::now();

-- Document: INC-709 (gRPC Deadline Propagation Cascade Causing Thread Starvation)
UPSERT document:INC_709 CONTENT {
    id: document:INC_709,
    incident_id: "INC-709",
    title: "gRPC Deadline Propagation Cascade Causing Thread Starvation",
    service: "order-router",
    severity: "SEV-2",
    file_name: "INC-709-order-router-grpc-deadline-cascade.md",
    preview: "# Incident Postmortem: INC-709 — gRPC Deadline Cascade  ## 1. Incident Overview * **Incident ID:** INC-709 * **Impacted Service:** `order-router` (tier: router) * **Severity Level:** SEV-2 (High) * **Start Time:** 2026-08-03 14:19:00 UTC * **Resolution Time:** 2026-08-03 14:22:48 UTC (MTTR: 3m 48s)...",
    ingested_at: time::now()
};
RELATE service:order_router->has_incident_doc->document:INC_709 SET relationship = 'documented_in', created_at = time::now();
RELATE postmortem:INC_709->documented_in->document:INC_709 SET relationship = 'formal_postmortem', created_at = time::now();

-- Document: INC-741 (Migration Exclusive Table Lock Timeout on Accounts Schema)
UPSERT document:INC_741 CONTENT {
    id: document:INC_741,
    incident_id: "INC-741",
    title: "Migration Exclusive Table Lock Timeout on Accounts Schema",
    service: "user-db",
    severity: "SEV-2",
    file_name: "INC-741-user-db-migration-exclusive-lock-timeout.md",
    preview: "# Incident Postmortem: INC-741 — Migration Exclusive Table Lock Timeout  ## 1. Incident Overview * **Incident ID:** INC-741 * **Impacted Service:** `user-db` (tier: database) * **Severity Level:** SEV-2 (High) * **Start Time:** 2026-08-14 11:22:00 UTC * **Resolution Time:** 2026-08-14 11:26:10 UTC (...",
    ingested_at: time::now()
};
RELATE service:user_db->has_incident_doc->document:INC_741 SET relationship = 'documented_in', created_at = time::now();
RELATE postmortem:INC_741->documented_in->document:INC_741 SET relationship = 'formal_postmortem', created_at = time::now();

-- Document: INC-812 (Idempotency Key Duplicate Race Condition Under Mobile Retry Flood)
UPSERT document:INC_812 CONTENT {
    id: document:INC_812,
    incident_id: "INC-812",
    title: "Idempotency Key Duplicate Race Condition Under Mobile Retry Flood",
    service: "payment-vault",
    severity: "SEV-1",
    file_name: "INC-812-payment-vault-idempotency-key-race.md",
    preview: "# Incident Postmortem: INC-812 — Idempotency Key Duplicate Race Condition  ## 1. Incident Overview * **Incident ID:** INC-812 * **Impacted Service:** `payment-vault` (tier: backend) * **Severity Level:** SEV-1 (Critical) * **Start Time:** 2026-09-02 19:05:00 UTC * **Resolution Time:** 2026-09-02 19:...",
    ingested_at: time::now()
};
RELATE service:payment_vault->has_incident_doc->document:INC_812 SET relationship = 'documented_in', created_at = time::now();
RELATE postmortem:INC_812->documented_in->document:INC_812 SET relationship = 'formal_postmortem', created_at = time::now();

-- Document: INC-892 (Redis Lock Starvation Under Peak Traffic Spike)
UPSERT document:INC_892 CONTENT {
    id: document:INC_892,
    incident_id: "INC-892",
    title: "Redis Lock Starvation Under Peak Traffic Spike",
    service: "auth-gateway",
    severity: "SEV-1",
    file_name: "INC-892-auth-gateway-redis-lock-starvation.md",
    preview: "# Incident Postmortem: INC-892 — Redis Lock Starvation  ## 1. Incident Overview * **Incident ID:** INC-892 * **Impacted Service:** `auth-gateway` (tier: gateway) * **Severity Level:** SEV-1 (Critical) * **Start Time:** 2026-09-21 03:14:00 UTC * **Resolution Time:** 2026-09-21 03:18:49 UTC (MTTR: 4m...",
    ingested_at: time::now()
};
RELATE service:auth_gateway->has_incident_doc->document:INC_892 SET relationship = 'documented_in', created_at = time::now();
RELATE postmortem:INC_892->documented_in->document:INC_892 SET relationship = 'formal_postmortem', created_at = time::now();

-- Document: INC-895 (JWT Public Key Cache Stampede on Token Verification Burst)
UPSERT document:INC_895 CONTENT {
    id: document:INC_895,
    incident_id: "INC-895",
    title: "JWT Public Key Cache Stampede on Token Verification Burst",
    service: "auth-gateway",
    severity: "SEV-2",
    file_name: "INC-895-auth-gateway-jwt-jwks-cache-stampede.md",
    preview: "# Incident Postmortem: INC-895 — JWT Public Key Cache Stampede  ## 1. Incident Overview * **Incident ID:** INC-895 * **Impacted Service:** `auth-gateway` (tier: gateway) * **Severity Level:** SEV-2 (High) * **Start Time:** 2026-09-28 16:42:00 UTC * **Resolution Time:** 2026-09-28 16:45:21 UTC (MTTR:...",
    ingested_at: time::now()
};
RELATE service:auth_gateway->has_incident_doc->document:INC_895 SET relationship = 'documented_in', created_at = time::now();
RELATE postmortem:INC_895->documented_in->document:INC_895 SET relationship = 'formal_postmortem', created_at = time::now();
