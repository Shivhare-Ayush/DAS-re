-- Additive Arize decision trail for the SurrealDB memory partner.
-- Apply AFTER schema.surql. Does not redefine service, shift, postmortem, or uncertainty.
--
-- Record ids written by agent.memory.decisions:
--   agent_run:{trace_id}
--   agent_decision:{decision_key}
-- Graph edges:
--   agent_run -> during -> shift          (their shift:{id})
--   agent_run -> concerns -> postmortem   (their postmortem:{incident_id})
--   agent_run -> produced -> agent_decision

DEFINE TABLE agent_run SCHEMAFULL;
DEFINE FIELD trace_id ON agent_run TYPE string;
DEFINE FIELD incident_id ON agent_run TYPE string;
DEFINE FIELD engineer_name ON agent_run TYPE string;
DEFINE FIELD shift_id ON agent_run TYPE string;
DEFINE FIELD pipeline_completed ON agent_run TYPE bool;
DEFINE FIELD final_action ON agent_run TYPE string;
DEFINE FIELD daytona_workspace_id ON agent_run TYPE option<string>;
DEFINE FIELD phoenix_project ON agent_run TYPE string DEFAULT "aegis-voice-sre";
DEFINE FIELD recorded_at ON agent_run TYPE option<string>;

DEFINE TABLE agent_decision SCHEMAFULL;
DEFINE FIELD decision_id ON agent_decision TYPE string;
DEFINE FIELD trace_id ON agent_decision TYPE string;
DEFINE FIELD incident_id ON agent_decision TYPE string;
DEFINE FIELD engineer_name ON agent_decision TYPE string;
DEFINE FIELD shift_id ON agent_decision TYPE string;
DEFINE FIELD step ON agent_decision TYPE string;
DEFINE FIELD gate ON agent_decision TYPE string;
DEFINE FIELD control_action ON agent_decision TYPE string;
DEFINE FIELD continue_pipeline ON agent_decision TYPE bool;
DEFINE FIELD reason ON agent_decision TYPE string;
DEFINE FIELD phoenix_span_id ON agent_decision TYPE string;
DEFINE FIELD daytona_workspace_id ON agent_decision TYPE option<string>;
DEFINE FIELD metrics ON agent_decision TYPE object;
DEFINE FIELD recorded_at ON agent_decision TYPE option<string>;

DEFINE TABLE during SCHEMAFULL TYPE RELATION IN agent_run OUT shift;
DEFINE TABLE concerns SCHEMAFULL TYPE RELATION IN agent_run OUT postmortem;
DEFINE TABLE produced SCHEMAFULL TYPE RELATION IN agent_run OUT agent_decision;
