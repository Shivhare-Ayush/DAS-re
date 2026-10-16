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

        # 2. Exec Command (cwd defaults to 'workspace' for cloned repos)
        cmd_res = client.exec_command(ws.workspace_id, "pytest tests/test_locks.py")
        assert cmd_res.passed is True
        assert cmd_res.exit_code == 0
        assert cmd_res.stdout == "10 passed in 0.2s"
        mock_sandbox.process.exec.assert_called_once_with(
            command="pytest tests/test_locks.py", cwd="workspace", timeout=60
        )

        # 3. Apply Patch (targets 'workspace/src/locks.py' for cloned repos)
        patch_ok = client.apply_patch(ws.workspace_id, "src/locks.py", "fixed code")
        assert patch_ok is True
        mock_sandbox.fs.upload_file.assert_called_once_with(
            src=b"fixed code", dst="workspace/src/locks.py"
        )

        # 4. Destroy Workspace
        destroyed = client.destroy_workspace(ws.workspace_id)
        assert destroyed is True
        mock_sandbox.delete.assert_called_once()
        assert ws.workspace_id not in client._sandboxes


def test_daytona_patch_base64_fallback():
    from unittest.mock import MagicMock, patch
    from agent.sandbox.client import DaytonaSandboxClient

    mock_sandbox = MagicMock()
    mock_sandbox.id = "sbx-fallback-1"
    # Force upload_file to fail to trigger base64 fallback
    mock_sandbox.fs.upload_file.side_effect = RuntimeError("SDK upload failed")

    mock_daytona_cls = MagicMock()
    mock_daytona_instance = MagicMock()
    mock_daytona_instance.create.return_value = mock_sandbox
    mock_daytona_cls.return_value = mock_daytona_instance

    with patch("daytona.Daytona", mock_daytona_cls):
        client = DaytonaSandboxClient(api_key="dtn_live_key")
        ws = client.create_workspace("")

        # Apply patch with tricky heredoc token "EOF"
        patch_with_eof = "def test():\n    token = 'EOF'\n"
        res = client.apply_patch(ws.workspace_id, "src/code.py", patch_with_eof)
        assert res is True
        # Verify process.exec was called with base64 decode
        mock_sandbox.process.exec.assert_called_once()
        call_cmd = mock_sandbox.process.exec.call_args[1]["command"] if "command" in mock_sandbox.process.exec.call_args[1] else mock_sandbox.process.exec.call_args[0][0]
        assert "base64 -d" in call_cmd


def test_daytona_zombie_cleanup_on_exception():
    from unittest.mock import MagicMock, patch
    from agent.sandbox.client import DaytonaSandboxClient

    mock_sandbox = MagicMock()
    mock_sandbox.id = "sbx-zombie-1"
    # Throw an exception during post-create git clone
    mock_sandbox.git.clone.side_effect = RuntimeError("Fatal git network partition")

    # Patch WorkspaceDescriptor to raise validation error inside try block
    mock_daytona_cls = MagicMock()
    mock_daytona_instance = MagicMock()
    mock_daytona_instance.create.return_value = mock_sandbox
    mock_daytona_cls.return_value = mock_daytona_instance

    from core.schemas import WorkspaceDescriptor

    with patch("daytona.Daytona", mock_daytona_cls), patch(
        "agent.sandbox.client.WorkspaceDescriptor",
        side_effect=[
            ValueError("Validation explosion on live state"),
            WorkspaceDescriptor(
                workspace_id="ws-daytona-fallback-1",
                repo_url="https://github.com/repo.git",
                status="RUNNING",
            ),
        ],
    ):
        client = DaytonaSandboxClient(api_key="dtn_live_key")
        ws = client.create_workspace("https://github.com/repo.git")

        # Verify orphan cloud sandbox was deleted immediately
        mock_sandbox.delete.assert_called_once()
        assert "sbx-zombie-1" not in client._sandboxes
        assert ws.workspace_id.startswith("ws-daytona-")


def test_daytona_destroy_retries_on_failure():
    from unittest.mock import MagicMock, patch
    from agent.sandbox.client import DaytonaSandboxClient

    mock_sandbox = MagicMock()
    mock_sandbox.id = "sbx-retry-1"
    # First delete call fails (503), second succeeds
    mock_sandbox.delete.side_effect = [RuntimeError("503 Service Unavailable"), None]

    mock_daytona_cls = MagicMock()
    mock_daytona_instance = MagicMock()
    mock_daytona_instance.create.return_value = mock_sandbox
    mock_daytona_cls.return_value = mock_daytona_instance

    with patch("daytona.Daytona", mock_daytona_cls):
        client = DaytonaSandboxClient(api_key="dtn_live_key")
        ws = client.create_workspace("")

        # Attempt 1: Fails -> remains in map
        assert client.destroy_workspace(ws.workspace_id) is False
        assert ws.workspace_id in client._sandboxes

        # Attempt 2: Succeeds -> evicted from map
        assert client.destroy_workspace(ws.workspace_id) is True
        assert ws.workspace_id not in client._sandboxes


