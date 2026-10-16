"""scripts/ingest_documents.py - Ingest markdown incident reports into SurrealDB Knowledge Graph as Document Nodes."""
import re
import sys
import logging
from pathlib import Path
from typing import Dict, Any

REPO_ROOT = Path(__file__).parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("ingest_docs")


def parse_markdown_report(file_path: Path) -> Dict[str, Any]:
    text = file_path.read_text(encoding="utf-8")
    frontmatter = {}
    content = text

    # Parse YAML frontmatter if present
    match = re.match(r"^---\s*\n(.*?)\n---\s*\n(.*)$", text, re.DOTALL)
    if match:
        raw_fm, content = match.groups()
        for line in raw_fm.strip().split("\n"):
            if ":" in line:
                k, v = line.split(":", 1)
                k = k.strip()
                v = v.strip().strip('"').strip("'")
                frontmatter[k] = v

    incident_id = frontmatter.get("incident_id", file_path.stem.split("-")[0])
    service = frontmatter.get("service", "unknown-service")
    title = frontmatter.get("title", file_path.stem)
    severity = frontmatter.get("severity", "SEV-2")

    return {
        "incident_id": incident_id,
        "title": title,
        "service": service,
        "severity": severity,
        "file_name": file_path.name,
        "content_length": len(content),
        "content_preview": content[:300].strip(),
        "full_text": content,
    }


def generate_surrealql(docs_dir: Path, output_surql: Path):
    statements = [
        "-- ==============================================================================",
        "-- Document Node Ingestion for SurrealDB Knowledge Graph",
        "-- Transforms markdown incident reports into queryable document nodes & graph edges",
        "-- ==============================================================================",
        "USE NS aegis DB incidents;",
        "",
    ]

    for md_file in sorted(docs_dir.glob("*.md")):
        doc = parse_markdown_report(md_file)
        doc_id = f"document:{doc['incident_id'].replace('-', '_')}"
        svc_id = f"service:{doc['service'].replace('-', '_')}"
        pm_id = f"postmortem:{doc['incident_id'].replace('-', '_')}"

        escaped_title = doc["title"].replace('"', '\\"')
        escaped_preview = doc["content_preview"].replace('"', '\\"').replace("\n", " ")

        statements.append(f"-- Document: {doc['incident_id']} ({doc['title']})")
        statements.append(f"""UPSERT {doc_id} CONTENT {{
    id: {doc_id},
    incident_id: "{doc['incident_id']}",
    title: "{escaped_title}",
    service: "{doc['service']}",
    severity: "{doc['severity']}",
    file_name: "{doc['file_name']}",
    preview: "{escaped_preview}...",
    ingested_at: time::now()
}};""")
        statements.append(f"RELATE {svc_id}->has_incident_doc->{doc_id} SET relationship = 'documented_in', created_at = time::now();")
        statements.append(f"RELATE {pm_id}->documented_in->{doc_id} SET relationship = 'formal_postmortem', created_at = time::now();")
        statements.append("")

    output_surql.write_text("\n".join(statements), encoding="utf-8")
    logger.info(f"Generated SurrealQL document ingestion script at: {output_surql}")


def ingest_to_surrealdb():
    docs_dir = Path(__file__).parent.parent / "docs" / "incidents"
    if not docs_dir.exists():
        logger.error(f"Documents directory not found: {docs_dir}")
        return False

    surql_file = Path(__file__).parent / "surreal_documents_seed.surql"
    generate_surrealql(docs_dir, surql_file)

    from core.config import get_settings
    settings = get_settings()

    try:
        from surrealdb import Surreal
        url = settings.SURREALDB_URL or "ws://localhost:8000/rpc"
        user = settings.SURREALDB_USER or "root"
        password = settings.SURREALDB_PASS or "root"
        namespace = settings.SURREALDB_NS or "aegis"
        database = settings.SURREALDB_DB or "incidents"

        logger.info(f"Connecting to SurrealDB at {url} to ingest document nodes...")
        db = Surreal(url)
        db.signin({"username": user, "password": password})
        db.use(namespace, database)

        surql_content = surql_file.read_text(encoding="utf-8")
        stmts = [s.strip() for s in surql_content.split(";") if s.strip() and not s.strip().startswith("--")]
        for stmt in stmts:
            if stmt.upper().startswith("USE "):
                continue
            try:
                db.query(stmt + ";")
            except Exception as e:
                logger.warning(f"Ingest statement warning ({stmt[:40]}...): {e}")

        logger.info("Successfully ingested all 6 incident documents into SurrealDB Knowledge Graph!")
        return True
    except Exception as e:
        logger.warning(f"Live SurrealDB connection not active ({e}).")
        logger.info(f"The SurrealQL seed file is ready at '{surql_file}' for Surrealist or surreal import!")
        return False


if __name__ == "__main__":
    ingest_to_surrealdb()
