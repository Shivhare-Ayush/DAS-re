"""agent/memory/store.py - SurrealDB Multi-Model Vector & Graph Incident Store."""
import json
import logging
import math
import re
import time
from pathlib import Path
from typing import List, Optional, Dict, Any
from core.schemas import IncidentPostmortem, ServiceGraphNode

logger = logging.getLogger(__name__)


def _cosine_similarity(vec1: List[float], vec2: List[float]) -> float:
    """Computes cosine similarity between two float vectors with float precision clamping."""
    if not vec1 or not vec2 or len(vec1) != len(vec2):
        return 0.0
    dot = sum(a * b for a, b in zip(vec1, vec2))
    norm_a = math.sqrt(sum(a * a for a in vec1))
    norm_b = math.sqrt(sum(b * b for b in vec2))
    if norm_a == 0.0 or norm_b == 0.0 or math.isnan(norm_a) or math.isnan(norm_b):
        return 0.0
    sim = dot / (norm_a * norm_b)
    return max(-1.0, min(1.0, sim))


class SurrealMemoryStore:
    """Production SurrealDB Client for Multi-Model Incident Memory & Blast Radius."""

    def __init__(
        self,
        url: Optional[str] = None,
        user: Optional[str] = None,
        password: Optional[str] = None,
        namespace: Optional[str] = None,
        database: Optional[str] = None,
    ):
        from core.config import get_settings
        settings = get_settings()

        self.url = url or settings.SURREALDB_URL or "ws://localhost:8000/rpc"
        self.user = user or settings.SURREALDB_USER or "root"
        self.password = password or settings.SURREALDB_PASS or "root"
        self.namespace = namespace or settings.SURREALDB_NS or "aegis"
        self.database = database or settings.SURREALDB_DB or "incidents"
        self._db = None
        self._fallback_store: Optional["MockSurrealMemoryStore"] = None

        if not settings.IS_MOCK_MODE:
            try:
                from surrealdb import Surreal
                db = Surreal(self.url)
                db.signin({"username": self.user, "password": self.password})
                db.use(self.namespace, self.database)
                self._db = db
                logger.info(f"Connected to SurrealDB at {self.url} (ns={self.namespace}, db={self.database})")
            except Exception as e:
                logger.debug(f"SurrealDB live connection unavailable ({e}). Initializing in-memory simulator.")
                self._db = None
                self._fallback_store = MockSurrealMemoryStore()
        else:
            self._fallback_store = MockSurrealMemoryStore()

    def query_similar_incidents(
        self, service_name: str, embedding: Optional[List[float]] = None
    ) -> List[IncidentPostmortem]:
        """Fuses Vector HNSW cosine similarity with service filtering."""
        if self._db is not None:
            try:
                if embedding is not None:
                    query = """
                    SELECT *, vector::similarity::cosine(embedding, $embedding) AS score
                    FROM postmortem
                    WHERE service_name = $service_name
                    ORDER BY score DESC
                    LIMIT 3;
                    """
                    result = self._db.query(query, {"service_name": service_name, "embedding": embedding})
                else:
                    query = "SELECT * FROM postmortem WHERE service_name = $service_name LIMIT 3;"
                    result = self._db.query(query, {"service_name": service_name})

                # Handle SurrealQL query return formats
                items = result if isinstance(result, list) else []
                if items and isinstance(items[0], dict) and "result" in items[0]:
                    items = items[0]["result"]
                if not isinstance(items, list):
                    items = []

                postmortems = []
                for p in items:
                    if not isinstance(p, dict):
                        continue
                    postmortems.append(
                        IncidentPostmortem(
                            incident_id=p.get("incident_id", "INC-000"),
                            service_name=p.get("service_name", service_name),
                            root_cause=p.get("root_cause", ""),
                            resolution_diff=p.get("resolution_diff", ""),
                            verified_in_daytona=p.get("verified_in_daytona", True),
                            phoenix_trace_id=p.get("phoenix_trace_id"),
                            phoenix_span_id=p.get("phoenix_span_id"),
                            phoenix_ui_url=p.get("phoenix_ui_url"),
                        )
                    )
                if postmortems:
                    return postmortems
            except Exception as e:
                logger.warning(f"SurrealDB live vector query failed: {e}. Delegating to fallback store.")

        # In-memory fallback
        store = self._fallback_store or MockSurrealMemoryStore()
        return store.query_similar_incidents(service_name, embedding)

    def get_service_dependencies(self, service_id: str, direction: str = "out") -> List[str]:
        """Performs directional graph traversal (->depends_on-> downstream or <-depends_on<- upstream)."""
        clean_id = service_id if service_id.startswith("service:") else f"service:{service_id}"
        # Validate identifier format to prevent query injection
        if not re.match(r"^[a-zA-Z0-9_\-:]+$", clean_id):
            logger.warning(f"Invalid service identifier rejected: {service_id}")
            return []

        if self._db is not None:
            try:
                if direction == "in":
                    # Upstream callers / blast radius impact
                    query = f"SELECT <-depends_on<-service.name AS callers FROM {clean_id};"
                else:
                    # Downstream dependencies
                    query = f"SELECT ->depends_on->service.name AS deps FROM {clean_id};"

                result = self._db.query(query)
                items = result if isinstance(result, list) else []
                if items and isinstance(items[0], dict) and "result" in items[0]:
                    items = items[0]["result"]
                if not isinstance(items, list):
                    items = []

                deps: List[str] = []
                for item in items:
                    if not isinstance(item, dict):
                        continue
                    vals = item.get("callers" if direction == "in" else "deps", [])
                    if isinstance(vals, list):
                        deps.extend(vals)
                if deps:
                    return list(dict.fromkeys(deps))
            except Exception as e:
                logger.warning(f"SurrealDB graph traversal failed: {e}. Delegating to fallback store.")

        # In-memory fallback
        store = self._fallback_store or MockSurrealMemoryStore()
        return store.get_service_dependencies(clean_id, direction=direction)

    def calculate_blast_radius(self, service_id: str) -> Dict[str, Any]:
        """Fuses graph relations to compute upstream impacted services and blast radius severity."""
        clean_id = service_id if service_id.startswith("service:") else f"service:{service_id}"
        svc_name = clean_id.replace("service:", "")

        downstream = self.get_service_dependencies(clean_id, direction="out")
        upstream = self.get_service_dependencies(clean_id, direction="in")

        # Deduplicate upstream callers and exclude self to avoid double counting
        unique_upstream = list(set(upstream) - {svc_name})
        total_impacted = len(unique_upstream) + 1

        critical_services = {"auth-gateway", "payment-vault", "user-db"}
        has_critical = any(s in critical_services for s in [svc_name] + unique_upstream)

        score = min(1.0, 0.35 + (0.30 * len(unique_upstream)) + (0.10 * len(downstream)))

        return {
            "target_service": svc_name,
            "downstream_dependencies": downstream,
            "upstream_impacted_services": unique_upstream,
            "total_impacted_services": total_impacted,
            "criticality": "CRITICAL" if has_critical else "MEDIUM",
            "blast_radius_score": round(score, 2),
        }

    def save_postmortem(self, postmortem: IncidentPostmortem) -> bool:
        """Persists verified incident postmortem into SurrealDB postmortem table."""
        if self._db is not None:
            try:
                data = postmortem.model_dump()
                query = "UPSERT type::thing('postmortem', $id) MERGE $data;"
                self._db.query(query, {"id": postmortem.incident_id, "data": data})
                return True
            except Exception as e:
                logger.warning(f"SurrealDB live save_postmortem failed: {e}. Saving to fallback.")

        store = self._fallback_store or MockSurrealMemoryStore()
        return store.save_postmortem(postmortem)

    def get_active_on_call_shift(self) -> Dict[str, Any]:
        """Retrieves active SRE shift information and predecessor handover notes."""
        if self._db is not None:
            try:
                query = "SELECT * FROM shift ORDER BY shift_start DESC LIMIT 1;"
                result = self._db.query(query)
                items = result if isinstance(result, list) else []
                if items and isinstance(items[0], dict) and "result" in items[0]:
                    items = items[0]["result"]
                if items and isinstance(items[0], dict):
                    s = items[0]
                    return {
                        "engineer_name": s.get("engineer_name", "On-Call SRE"),
                        "role": s.get("role", "Primary On-Call"),
                        "shift_id": s.get("shift_id", "shift:active"),
                        "handover_notes": s.get("handover_notes_from_previous", "All systems nominal."),
                    }
            except Exception as e:
                logger.warning(f"SurrealDB live shift query failed: {e}. Falling back.")

        store = self._fallback_store or MockSurrealMemoryStore()
        return store.get_active_on_call_shift()

    def query_open_uncertainties(self, service_name: Optional[str] = None) -> List[Dict[str, Any]]:
        """Retrieves open SRE uncertainties and hypotheses to guide safe remediation."""
        if self._db is not None:
            try:
                if service_name:
                    query = "SELECT * FROM uncertainty WHERE status = 'OPEN' AND service = $svc;"
                    result = self._db.query(query, {"svc": service_name})
                else:
                    query = "SELECT * FROM uncertainty WHERE status = 'OPEN';"
                    result = self._db.query(query)

                items = result if isinstance(result, list) else []
                if items and isinstance(items[0], dict) and "result" in items[0]:
                    items = items[0]["result"]
                return items if isinstance(items, list) else []
            except Exception as e:
                logger.warning(f"SurrealDB uncertainty query failed: {e}. Falling back.")

        store = self._fallback_store or MockSurrealMemoryStore()
        return store.query_open_uncertainties(service_name)

    def save_uncertainty(self, uncertainty: Dict[str, Any]) -> bool:
        """Records an operational hypothesis or uncertainty into SurrealDB."""
        if self._db is not None:
            try:
                uid = uncertainty.get("id") or f"uncertainty:{int(time.time())}"
                clean_uid = uid.replace("uncertainty:", "")
                query = "UPSERT type::thing('uncertainty', $id) MERGE $data;"
                self._db.query(query, {"id": clean_uid, "data": uncertainty})
                return True
            except Exception as e:
                logger.warning(f"SurrealDB live save_uncertainty failed: {e}.")

        store = self._fallback_store or MockSurrealMemoryStore()
        return store.save_uncertainty(uncertainty)


class MockSurrealMemoryStore(SurrealMemoryStore):
    """Deterministic In-Memory SurrealDB Simulator loading from mock_data.json."""

    def __init__(self):
        # Initialize internal in-memory store without triggering live socket connection
        self._data = self._load_data()
        self._db = None
        self._fallback_store = None

    def _load_data(self) -> Dict[str, Any]:
        json_path = Path(__file__).parent / "mock_data.json"
        if json_path.exists():
            with open(json_path, "r", encoding="utf-8") as f:
                return json.load(f)
        return {"services": [], "shifts": [], "postmortems": [], "uncertainties": []}

    def query_similar_incidents(
        self, service_name: str, embedding: Optional[List[float]] = None
    ) -> List[IncidentPostmortem]:
        candidates = [p for p in self._data.get("postmortems", []) if p["service_name"] == service_name]
        if not candidates:
            candidates = self._data.get("postmortems", [])

        if embedding is not None and candidates:
            # Score each candidate using cosine similarity
            scored = []
            for c in candidates:
                c_emb = c.get("embedding")
                sim = _cosine_similarity(embedding, c_emb) if c_emb else 0.5
                scored.append((sim, c))
            scored.sort(key=lambda x: x[0], reverse=True)
            candidates = [x[1] for x in scored]

        results = []
        for p in candidates[:3]:
            results.append(
                IncidentPostmortem(
                    incident_id=p["incident_id"],
                    service_name=p["service_name"],
                    root_cause=p["root_cause"],
                    resolution_diff=p["resolution_diff"],
                    verified_in_daytona=p["verified_in_daytona"],
                    phoenix_trace_id=p.get("phoenix_trace_id"),
                    phoenix_span_id=p.get("phoenix_span_id"),
                    phoenix_ui_url=p.get("phoenix_ui_url"),
                )
            )
        return results

    def get_service_dependencies(self, service_id: str, direction: str = "out") -> List[str]:
        cleaned = service_id if service_id.startswith("service:") else f"service:{service_id}"
        if direction == "in":
            # Upstream callers: services whose 'depends_on' includes cleaned
            callers = []
            for s in self._data.get("services", []):
                if cleaned in s.get("depends_on", []):
                    callers.append(s["name"])
            return callers

        # Downstream dependencies (out)
        for s in self._data.get("services", []):
            if s["id"] == cleaned:
                return [dep.replace("service:", "") for dep in s.get("depends_on", [])]
        return []

    def calculate_blast_radius(self, service_id: str) -> Dict[str, Any]:
        cleaned = service_id if service_id.startswith("service:") else f"service:{service_id}"
        svc_name = cleaned.replace("service:", "")

        downstream = self.get_service_dependencies(cleaned, direction="out")
        upstream = self.get_service_dependencies(cleaned, direction="in")

        unique_upstream = list(set(upstream) - {svc_name})
        total_impacted = len(unique_upstream) + 1

        critical_services = {"auth-gateway", "payment-vault", "user-db"}
        has_critical = any(s in critical_services for s in [svc_name] + unique_upstream)

        score = min(1.0, 0.35 + (0.30 * len(unique_upstream)) + (0.10 * len(downstream)))

        return {
            "target_service": svc_name,
            "downstream_dependencies": downstream,
            "upstream_impacted_services": unique_upstream,
            "total_impacted_services": total_impacted,
            "criticality": "CRITICAL" if has_critical else "MEDIUM",
            "blast_radius_score": round(score, 2),
        }

    def save_postmortem(self, postmortem: IncidentPostmortem) -> bool:
        self._data.setdefault("postmortems", [])
        for idx, existing in enumerate(self._data["postmortems"]):
            if existing.get("incident_id") == postmortem.incident_id:
                self._data["postmortems"][idx] = postmortem.model_dump()
                return True
        self._data["postmortems"].append(postmortem.model_dump())
        return True

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
        return {
            "engineer_name": "Ayush Shivhare",
            "role": "Primary On-Call SRE",
            "shift_id": "shift:2026-w42-primary",
            "handover_notes": "All systems nominal.",
        }

    def query_open_uncertainties(self, service_name: Optional[str] = None) -> List[Dict[str, Any]]:
        uncertainties = self._data.get("uncertainties", [])
        if service_name:
            return [u for u in uncertainties if u.get("status") == "OPEN" and u.get("service") == service_name]
        return [u for u in uncertainties if u.get("status") == "OPEN"]

    def save_uncertainty(self, uncertainty: Dict[str, Any]) -> bool:
        self._data.setdefault("uncertainties", [])
        self._data["uncertainties"].append(uncertainty)
        return True
