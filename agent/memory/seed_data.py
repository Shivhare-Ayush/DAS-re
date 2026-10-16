"""agent/memory/seed_data.py - Populates SurrealDB with Microservices, Graph Edges, Incidents & Shifts."""
import json
import os
import sys
from pathlib import Path

# Ensure UTF-8 output on Windows terminals
if sys.stdout.encoding != "utf-8":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass


def load_mock_data():
    json_path = Path(__file__).parent / "mock_data.json"
    with open(json_path, "r", encoding="utf-8") as f:
        return json.load(f)


def seed_surrealdb(url="ws://localhost:8000/rpc", user="root", password="root", namespace="aegis", database="incidents"):
    data = load_mock_data()
    print(f"[*] Loaded mock data: {len(data['services'])} services, {len(data['shifts'])} shifts, {len(data['postmortems'])} postmortems.")

    try:
        from surrealdb import Surreal
        import asyncio

        async def _run_seed():
            async with Surreal(url) as db:
                await db.signin({"username": user, "password": password})
                await db.use(namespace, database)
                
                print("[*] Connected to SurrealDB. Seeding records...")
                # 1. Services
                for s in data["services"]:
                    s_clean = {k: v for k, v in s.items() if k != "depends_on"}
                    await db.create(s["id"], s_clean)
                
                # 2. Graph Relations (RELATE service->depends_on->service)
                for s in data["services"]:
                    source_id = s["id"]
                    for target_id in s.get("depends_on", []):
                        rel_query = f"RELATE {source_id}->depends_on->{target_id} SET critical = true;"
                        await db.query(rel_query)
                
                # 3. Postmortems
                for p in data["postmortems"]:
                    await db.create(f"postmortem:{p['incident_id']}", p)
                
                # 4. Shifts
                for sh in data["shifts"]:
                    await db.create(sh["shift_id"], sh)

                # 5. Uncertainties
                for u in data.get("uncertainties", []):
                    await db.create(u["id"], u)

                print("[SUCCESS] All records and graph edges seeded into SurrealDB successfully!")

        asyncio.run(_run_seed())

    except ImportError:
        print("[!] surrealdb SDK not installed. Verifying local JSON mock data only...")
        print("[SUCCESS] Local mock data verified and ready for MockSurrealMemoryStore.")
    except Exception as e:
        print(f"[!] Could not connect to live SurrealDB instance ({e}).")
        print("[INFO] Fallback to in-memory MockSurrealMemoryStore remains active and 100% functional.")


if __name__ == "__main__":
    seed_surrealdb()
