"""Load Arize Phoenix trace-export CSV into Surreal graph edges."""
import csv
from pathlib import Path
from typing import Any, Dict, List

CSV_PATH = Path(__file__).parent / "arize_phoenix_spans.csv"


def load_arize_spans(path: Path = CSV_PATH) -> List[Dict[str, Any]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def graph_edges_from_spans(spans: List[Dict[str, Any]]) -> List[Dict[str, str]]:
    """Edges Ayush's knowledge graph can render: engineer -> service -> phoenix span."""
    edges = []
    for row in spans:
        engineer = row.get("attributes.metadata.engineer", "unknown")
        service = row.get("attributes.metadata.service", "unknown")
        action = row.get("attributes.metadata.control_action", "CONTINUE")
        edges.append({
            "engineer": engineer,
            "timezone": row.get("attributes.metadata.timezone", "UTC"),
            "service": service,
            "span_name": row.get("name", "span"),
            "span_kind": row.get("span_kind", "AGENT"),
            "status_code": row.get("status_code", "OK"),
            "control_action": action,
            "latency_ms": row.get("attributes.metadata.latency_ms", "0"),
            "error_rate": row.get("attributes.metadata.error_rate", "0"),
            "trace_id": row.get("context.trace_id", ""),
            "output": row.get("attributes.output.value", ""),
        })
    return edges
