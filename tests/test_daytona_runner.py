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


def test_daytona_live_client_fallback_mode():
    from agent.sandbox.client import DaytonaSandboxClient

    # Test with mock key (default fallback simulator)
    client = DaytonaSandboxClient(api_key="mock_key")
    ws = client.create_workspace("https://github.com/aegis-sre/auth-gateway.git")
    assert ws.workspace_id.startswith("ws-daytona-")
    assert ws.status == "RUNNING"

    cmd_res = client.exec_command(ws.workspace_id, "pytest tests/")
    assert cmd_res.passed is True
    assert cmd_res.exit_code == 0

    assert client.apply_patch(ws.workspace_id, "src/test.py", "x = 1") is True
    assert client.destroy_workspace(ws.workspace_id) is True


def test_daytona_sdk_lifecycle_mocked():
    from unittest.mock import MagicMock, patch
    from agent.sandbox.client import DaytonaSandboxClient

    # Mock Daytona SDK
    mock_sandbox = MagicMock()
    mock_sandbox.id = "sbx-cloud-12345"
    mock_sandbox.state = "RUNNING"

    mock_exec_response = MagicMock()
    mock_exec_response.exit_code = 0
    mock_exec_response.result = "10 passed in 0.2s"
    mock_exec_response.artifacts = None
    mock_sandbox.process.exec.return_value = mock_exec_response

    mock_daytona_cls = MagicMock()
    mock_daytona_instance = MagicMock()
    mock_daytona_instance.create.return_value = mock_sandbox
    mock_daytona_cls.return_value = mock_daytona_instance

    with patch("daytona.Daytona", mock_daytona_cls):
        client = DaytonaSandboxClient(api_key="dtn_live_test_key_abc", target="us")
        assert client._sdk is not None

        # 1. Create Workspace
        ws = client.create_workspace("https://github.com/aegis-sre/auth-gateway.git")
        assert ws.workspace_id == "sbx-cloud-12345"
        assert ws.status == "RUNNING"
        mock_sandbox.git.clone.assert_called_once_with(
            url="https://github.com/aegis-sre/auth-gateway.git", path="workspace"
        )

        # 2. Exec Command
        cmd_res = client.exec_command(ws.workspace_id, "pytest tests/test_locks.py")
        assert cmd_res.passed is True
        assert cmd_res.exit_code == 0
        assert cmd_res.stdout == "10 passed in 0.2s"
        mock_sandbox.process.exec.assert_called_once_with(
            command="pytest tests/test_locks.py", cwd=None, timeout=60
        )

        # 3. Apply Patch
        patch_ok = client.apply_patch(ws.workspace_id, "src/locks.py", "fixed code")
        assert patch_ok is True
        mock_sandbox.fs.upload_file.assert_called_once()

        # 4. Destroy Workspace
        destroyed = client.destroy_workspace(ws.workspace_id)
        assert destroyed is True
        mock_sandbox.delete.assert_called_once()
        assert ws.workspace_id not in client._sandboxes

