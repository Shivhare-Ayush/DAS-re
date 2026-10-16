"""scripts/start_phoenix.py - Launch Arize Phoenix UI Server."""
import time
import phoenix as px

print("=" * 60)
print("[ARIZE PHOENIX] Starting Observability Server...")
print("=" * 60)

try:
    session = px.launch_app(host="127.0.0.1", port=6006)
    print(f"\n>>> Arize Phoenix UI is RUNNING at: {session.url}")
    print(">>> Endpoint for traces: http://127.0.0.1:6006/v1/traces")
    print(">>> Press Ctrl+C in this terminal to stop the server.\n")
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    print("\nShutting down Arize Phoenix server...")
except Exception as e:
    print(f"\n[ERROR] Failed to start Arize Phoenix: {e}")
