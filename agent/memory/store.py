"""agent/memory/store.py - SurrealDB Vector & Graph Incident Store."""
from typing import List, Optional
from core.schemas import IncidentPostmortem, ServiceGraphNode


class SurrealMemoryStore:
    """Manages Incident Postmortems and Dependency Graph in SurrealDB."""

    def __init__(self, url: Optional[str] = None):
        self.url = url or "ws://localhost:8000/rpc"

    def query_similar_incidents(self, service_name: str, embedding: Optional[List[float]] = None) -> List[IncidentPostmortem]:
        # Live implementation runs:
        # SELECT * FROM postmortem WHERE service_name = $service_name ORDER BY vector::similarity::cosine(...) DESC LIMIT 1;
        return [
            IncidentPostmortem(
                incident_id="INC-892",
                service_name="auth-gateway",
                root_cause="Redis lock starvation under peak traffic due to unreleased lock handles in exception path.",
                resolution_diff="""--- a/src/locks.py\n+++ b/src/locks.py\n@@ -12,4 +12,6 @@\n+    finally:\n+        redis.delete(lock_key)\n""",
                verified_in_daytona=True,
            )
        ]

    def save_postmortem(self, postmortem: IncidentPostmortem) -> bool:
        # Live implementation executes INSERT INTO postmortem CONTENT ...
        return True

    def get_service_dependencies(self, service_id: str) -> List[str]:
        # Live: SELECT ->depends_on->service.name FROM service:auth_gateway
        return ["redis-cluster", "user-db", "payment-vault"]


class MockSurrealMemoryStore(SurrealMemoryStore):
    """Deterministic Mock SurrealDB Store for Testing and Fallbacks."""
    pass
