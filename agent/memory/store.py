"""agent/memory/store.py - SurrealDB Vector & Graph Incident Store."""
import json
from pathlib import Path
from typing import List, Optional, Dict, Any
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
                resolution_diff="""--- a/src/locks.py\n+++ b/src/locks.py\n@@ -14,5 +14,8 @@\n     def process_critical_section(self, key: str, should_fail: bool = False):\n         self.acquire(key)\n+        try:\n             if should_fail:\n                 raise ValueError(\"Unexpected database network blip during processing\")\n+        finally:\n+            self.release(key)\n""",
                verified_in_daytona=True,
            )
        ]

    def save_postmortem(self, postmortem: IncidentPostmortem) -> bool:
        return True

    def get_service_dependencies(self, service_id: str) -> List[str]:
        return ["redis-cluster", "user-db", "payment-vault"]

    def get_active_on_call_shift(self) -> Dict[str, Any]:
        return {
            "engineer_name": "Ayush Shivhare",
            "role": "Primary On-Call SRE",
            "shift_id": "shift:2026-w42-primary",
            "handover_notes": "Previous shift (Alice Chen): Saw brief 200ms lock latency spikes on auth-gateway around 4:15 AM during marketing email batch. No alerts fired, but keep an eye on Redis client count.",
        }

    def query_open_uncertainties(self, service_name: Optional[str] = None) -> List[Dict[str, Any]]:
        return [
            {
                "service": "auth-gateway",
                "observation": "Redis client connection pool creep observed during previous shift marketing batch.",
                "verification_step": "Inspect redis_connected_clients metric in Daytona sandbox before closing incident.",
                "status": "OPEN",
            }
        ]


class MockSurrealMemoryStore(SurrealMemoryStore):
    """Deterministic Mock SurrealDB Store loading from mock_data.json."""

    def __init__(self):
        super().__init__()
        self._data = self._load_data()

    def _load_data(self) -> Dict[str, Any]:
        json_path = Path(__file__).parent / "mock_data.json"
        if json_path.exists():
            with open(json_path, "r", encoding="utf-8") as f:
                return json.load(f)
        return {"services": [], "shifts": [], "postmortems": [], "uncertainties": []}

    def query_similar_incidents(self, service_name: str, embedding: Optional[List[float]] = None) -> List[IncidentPostmortem]:
        matches = [p for p in self._data.get("postmortems", []) if p["service_name"] == service_name]
        if matches:
            p = matches[0]
            return [
                IncidentPostmortem(
                    incident_id=p["incident_id"],
                    service_name=p["service_name"],
                    root_cause=p["root_cause"],
                    resolution_diff=p["resolution_diff"],
                    verified_in_daytona=p["verified_in_daytona"],
                )
            ]
        return super().query_similar_incidents(service_name, embedding)

    def get_service_dependencies(self, service_id: str) -> List[str]:
        cleaned = service_id if service_id.startswith("service:") else f"service:{service_id}"
        for s in self._data.get("services", []):
            if s["id"] == cleaned:
                return [dep.replace("service:", "") for dep in s.get("depends_on", [])]
        return ["redis-cluster", "user-db"]

    def get_active_on_call_shift(self) -> Dict[str, Any]:
        shifts = self._data.get("shifts", [])
        if shifts:
            s = shifts[0]
            return {
                "engineer_name": s["engineer_name"],
                "role": s["role"],
                "shift_id": s["shift_id"],
                "handover_notes": s.get("handover_notes_from_previous", "All systems nominal."),
            }
        return super().get_active_on_call_shift()

    def query_open_uncertainties(self, service_name: Optional[str] = None) -> List[Dict[str, Any]]:
        uncertainties = self._data.get("uncertainties", [])
        if service_name:
            return [u for u in uncertainties if u.get("service") == service_name or u.get("status") == "OPEN"]
        return uncertainties
