-- SurrealDB Multi-Model Schema for Aegis Incident Topology

DEFINE NAMESPACE aegis;
DEFINE DATABASE incidents;

-- 1. Microservice Knowledge Graph
DEFINE TABLE service SCHEMAFULL;
DEFINE FIELD name ON TABLE service TYPE string;
DEFINE FIELD tier ON TABLE service TYPE string;

DEFINE TABLE depends_on SCHEMAFULL;
DEFINE FIELD in ON TABLE depends_on TYPE record<service>;
DEFINE FIELD out ON TABLE depends_on TYPE record<service>;

-- 2. Incident Postmortems with Vector Search
DEFINE TABLE postmortem SCHEMAFULL;
DEFINE FIELD incident_id ON TABLE postmortem TYPE string;
DEFINE FIELD service_name ON TABLE postmortem TYPE string;
DEFINE FIELD root_cause ON TABLE postmortem TYPE string;
DEFINE FIELD resolution_diff ON TABLE postmortem TYPE string;
DEFINE FIELD verified_in_daytona ON TABLE postmortem TYPE bool;
DEFINE FIELD embedding ON TABLE postmortem TYPE array<float>;

-- HNSW Vector Index for Instant Postmortem Matching
DEFINE INDEX postmortem_embedding_idx ON TABLE postmortem FIELDS embedding HNSW DIMENSION 1536 DIST COSINE;
