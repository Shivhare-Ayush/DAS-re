-- SurrealDB Multi-Model Schema for DAS-re (Autonomous Voice SRE)

DEFINE NAMESPACE aegis;
DEFINE DATABASE incidents;

-- 1. Microservice Knowledge Graph
DEFINE TABLE service SCHEMAFULL;
DEFINE FIELD name ON service TYPE string;
DEFINE FIELD tier ON service TYPE string;
DEFINE FIELD repo_url ON service TYPE string;

-- Explicit relation table for directional graph traversal
DEFINE TABLE depends_on SCHEMAFULL TYPE RELATION IN service OUT service;
DEFINE FIELD critical ON depends_on TYPE bool DEFAULT true;

-- 2. Incident Postmortems with Vector Search
DEFINE TABLE postmortem SCHEMAFULL;
DEFINE FIELD incident_id ON postmortem TYPE string;
DEFINE FIELD service_name ON postmortem TYPE string;
DEFINE FIELD root_cause ON postmortem TYPE string;
DEFINE FIELD resolution_diff ON postmortem TYPE string;
DEFINE FIELD verified_in_daytona ON postmortem TYPE bool;
DEFINE FIELD embedding ON postmortem TYPE array<float, 1536>;

-- HNSW Vector Index for Instant Postmortem Matching
DEFINE INDEX postmortem_embedding_idx ON postmortem 
  FIELDS embedding 
  HNSW DIMENSION 1536 
  DIST COSINE 
  EFC 150 
  M 12;

-- 3. Rotating On-Call Shift Schemas & Scoped Access
DEFINE TABLE engineer SCHEMAFULL;
DEFINE FIELD name ON engineer TYPE string;
DEFINE FIELD email ON engineer TYPE string;
DEFINE FIELD iam_role ON engineer TYPE string;

DEFINE TABLE shift SCHEMAFULL;
DEFINE FIELD shift_id ON shift TYPE string;
DEFINE FIELD engineer_name ON shift TYPE string;
DEFINE FIELD role ON shift TYPE string;
DEFINE FIELD shift_start ON shift TYPE string;
DEFINE FIELD shift_end ON shift TYPE string;
DEFINE FIELD handover_notes_from_previous ON shift TYPE string;

DEFINE TABLE uncertainty SCHEMAFULL;
DEFINE FIELD service ON uncertainty TYPE string;
DEFINE FIELD observation ON uncertainty TYPE string;
DEFINE FIELD verification_step ON uncertainty TYPE string;
DEFINE FIELD status ON uncertainty TYPE string;

-- Agent continue/terminate trail is additive. Apply schema_agent_trail.surql
-- after this file. It only adds agent_run, agent_decision, and graph edges
-- onto shift / postmortem records defined above.
