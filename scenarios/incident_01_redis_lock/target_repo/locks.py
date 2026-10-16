"""Target Microservice Component: Defective Redis Distributed Lock Manager."""
import time


class RedisLockError(Exception):
    pass


class DefectiveRedisLock:
    """Simulates a distributed lock that fails to release under exceptions."""

    def __init__(self):
        self.locked_keys = set()

    def acquire(self, key: str, timeout: float = 1.0) -> bool:
        if key in self.locked_keys:
            # Bug: Hangs/times out because previous lock was never released
            raise RedisLockError(f"RedisLockTimeout: unable to acquire lock for key '{key}'")
        self.locked_keys.add(key)
        return True

    def process_critical_section(self, key: str, should_fail: bool = False):
        self.acquire(key)
        # DEFECT: If an unhandled exception occurs here, release() is skipped!
        if should_fail:
            raise ValueError("Unexpected database network blip during processing")
        # Only reached on clean path:
        self.release(key)

    def release(self, key: str):
        if key in self.locked_keys:
            self.locked_keys.remove(key)


class FixedRedisLock(DefectiveRedisLock):
    """The surgical fix verified by Aegis inside Daytona."""

    def process_critical_section(self, key: str, should_fail: bool = False):
        self.acquire(key)
        try:
            if should_fail:
                raise ValueError("Unexpected database network blip during processing")
        finally:
            # Fixed: Always release the lock handle in the finally block!
            self.release(key)
