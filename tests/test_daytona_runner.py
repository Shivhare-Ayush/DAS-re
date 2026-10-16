"""tests/test_daytona_runner.py - Tests for Daytona Ephemeral Lifecycle."""
from agent.sandbox.client import MockDaytonaSandboxClient
from agent.sandbox.runner import SandboxRunner


def test_daytona_mock_lifecycle_reproduction_and_patch():
    client = MockDaytonaSandboxClient()
    runner = SandboxRunner(client)

    result = runner.verify_remediation(
        repo_url="https://github.com/aegis-sre/auth-gateway.git",
        test_command="pytest tests/test_locks.py",
        file_path="src/locks.py",
        patch_code="finally: self.release(key)",
    )

    assert result["defect_reproduced"] is True
    assert result["fix_verified"] is True
    assert result["duration_ms"] > 0
