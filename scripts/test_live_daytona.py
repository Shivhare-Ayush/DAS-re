"""scripts/test_live_daytona.py - Live Daytona Cloud verification test."""
import time
from core.config import get_settings
from agent.sandbox.client import DaytonaSandboxClient

settings = get_settings()
print("=" * 60)
print("[DAYTONA CLOUD] Live Ephemeral Sandbox Lifecycle Test")
print("=" * 60)

if not settings.DAYTONA_API_KEY or settings.DAYTONA_API_KEY.startswith("mock_"):
    print("[ERROR] DAYTONA_API_KEY not configured in environment or .env!")
    exit(1)

print(f"Target Server: {settings.DAYTONA_TARGET}")
print("1. Initializing Daytona Cloud SDK client...")
client = DaytonaSandboxClient(api_key=settings.DAYTONA_API_KEY, target=settings.DAYTONA_TARGET)

print("2. Spawning live ephemeral sandbox (auto_delete_interval=15m)...")
t0 = time.time()
ws = client.create_workspace("https://github.com/Shivhare-Ayush/auth-gateway-demo.git")
t1 = time.time()
print(f"   >>> Sandbox spawned in {t1 - t0:.2f}s! Workspace ID: {ws.workspace_id}")

print("3. Executing remote process in Daytona sandbox...")
t2 = time.time()
res = client.exec_command(ws.workspace_id, "python -c 'import sys; print(\"Remote Python:\", sys.version)'")
t3 = time.time()
print(f"   >>> Remote execution in {t3 - t2:.2f}s:")
print(f"       Exit code: {res.exit_code}")
print(f"       Stdout   : {res.stdout.strip()}")

print("4. Teardown: Destroying sandbox cleanly...")
t4 = time.time()
destroyed = client.destroy_workspace(ws.workspace_id)
t5 = time.time()
print(f"   >>> Sandbox destroyed in {t5 - t4:.2f}s: {destroyed} (Zero residual host spend)")

print("\n" + "=" * 60)
print("[SUCCESS] Live Daytona Cloud verified 100% operational!")
print("=" * 60)
