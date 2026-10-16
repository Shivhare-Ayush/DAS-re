"""scripts/seed_surreal_graph.py - Python utility to seed SurrealDB Knowledge Graph."""
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("seed_graph")


def seed_database():
    from core.config import get_settings
    settings = get_settings()

    surql_file = Path(__file__).parent / "surreal_seed.surql"
    if not surql_file.exists():
        logger.error(f"SurrealQL seed file not found: {surql_file}")
        return False

    surql_content = surql_file.read_text(encoding="utf-8")

    try:
        from surrealdb import Surreal
        url = settings.SURREALDB_URL or "ws://localhost:8000/rpc"
        user = settings.SURREALDB_USER or "root"
        password = settings.SURREALDB_PASS or "root"
        namespace = settings.SURREALDB_NS or "aegis"
        database = settings.SURREALDB_DB or "incidents"

        logger.info(f"Connecting to SurrealDB at {url}...")
        db = Surreal(url)
        db.signin({"username": user, "password": password})
        db.use(namespace, database)

        logger.info(f"Executing SurrealQL seed statements from {surql_file.name}...")
        # Split statements by semicolon and execute non-empty ones
        statements = [stmt.strip() for stmt in surql_content.split(";") if stmt.strip() and not stmt.strip().startswith("--")]
        for stmt in statements:
            if stmt.upper().startswith("USE "):
                continue
            try:
                db.query(stmt + ";")
            except Exception as e:
                logger.warning(f"Statement executed with warning ({stmt[:40]}...): {e}")

        logger.info("Successfully seeded SurrealDB Knowledge Graph!")
        logger.info("You can now view this graph in Surrealist (http://localhost:8000 or https://surrealist.app/)")
        return True
    except ImportError:
        logger.warning("surrealdb Python SDK not installed or failed to import. In-memory fallback is active.")
        return False
    except Exception as e:
        logger.warning(f"Could not connect to live SurrealDB ({e}). Check if surreal is running.")
        logger.info("To start a local SurrealDB server: surreal start --user root --pass root memory")
        return False


if __name__ == "__main__":
    seed_database()
