"""Target Microservice: auth-gateway FastAPI Application."""
import time
from fastapi import FastAPI, HTTPException, status
from scenarios.incident_01_redis_lock.target_repo.locks import DefectiveRedisLock, RedisLockError

app = FastAPI(title="auth-gateway", version="1.0.0")
lock_manager = DefectiveRedisLock()


@app.get("/health")
def health_check():
    return {"status": "ok", "service": "auth-gateway"}


@app.post("/auth/verify-token")
def verify_token(user_id: str, trigger_failure: bool = False):
    """Simulates authenticating a user with distributed lock synchronization."""
    lock_key = f"auth:user:{user_id}"
    try:
        lock_manager.process_critical_section(lock_key, should_fail=trigger_failure)
        return {"authenticated": True, "user_id": user_id, "timestamp": time.time()}
    except RedisLockError as e:
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail=f"Distributed Lock Timeout on Redis cluster: {str(e)}",
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database Network Blip: {str(e)}",
        )


@app.post("/admin/reset-locks")
def reset_locks():
    lock_manager.locked_keys.clear()
    return {"status": "cleared", "active_locks": 0}
