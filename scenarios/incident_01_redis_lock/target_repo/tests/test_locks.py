"""Unit Tests for Target Microservice Lock Manager."""
import pytest
from scenarios.incident_01_redis_lock.target_repo.locks import (
    DefectiveRedisLock,
    FixedRedisLock,
    RedisLockError,
)


def test_defective_lock_leaks_under_exception():
    lock = DefectiveRedisLock()
    # First call fails and leaves lock key locked
    with pytest.raises(ValueError):
        lock.process_critical_section("auth:user:491", should_fail=True)

    # Second call fails with RedisLockTimeout because key wasn't freed
    with pytest.raises(RedisLockError, match="RedisLockTimeout"):
        lock.acquire("auth:user:491")


def test_fixed_lock_releases_cleanly():
    lock = FixedRedisLock()
    # First call fails, but finally block releases the key
    with pytest.raises(ValueError):
        lock.process_critical_section("auth:user:491", should_fail=True)

    # Second call succeeds immediately!
    assert lock.acquire("auth:user:491") is True
