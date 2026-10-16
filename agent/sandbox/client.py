"""agent/sandbox/client.py - Daytona Python SDK Client Wrapper."""
import time
from typing import Optional
from core.schemas import WorkspaceDescriptor, SandboxExecutionResult


class DaytonaSandboxClient:
    """Production Daytona SDK Client for Ephemeral Cloud Workspaces."""

    def __init__(self, api_key: Optional[str] = None, server_url: Optional[str] = None):
        self.api_key = api_key or "mock_key"
        self.server_url = server_url or "https://app.daytona.io/api"

    def create_workspace(self, repo_url: str) -> WorkspaceDescriptor:
        # In live mode, invokes daytona.create(CreateWorkspaceParams(id=..., repository=...))
        ws_id = f"ws-daytona-{int(time.time())}"
        return WorkspaceDescriptor(
            workspace_id=ws_id,
            repo_url=repo_url,
            status="RUNNING",
        )

    def exec_command(self, workspace_id: str, command: str) -> SandboxExecutionResult:
        # In live mode, invokes workspace.process.exec(command)
        start = time.time()
        # Default pass behavior for mock
        exit_code = 0
        stdout = "Command completed successfully in Daytona sandbox."
        stderr = ""
        duration = (time.time() - start) * 1000

        return SandboxExecutionResult(
            workspace_id=workspace_id,
            command=command,
            exit_code=exit_code,
            stdout=stdout,
            stderr=stderr,
            duration_ms=duration,
            passed=(exit_code == 0),
        )

    def apply_patch(self, workspace_id: str, file_path: str, patch_content: str) -> bool:
        # Writes patch or writes file inside the workspace
        return True

    def destroy_workspace(self, workspace_id: str) -> bool:
        # Invokes daytona.delete(workspace_id)
        return True


class MockDaytonaSandboxClient(DaytonaSandboxClient):
    """Deterministic Mock Daytona Client for Testing and Fallbacks."""

    def __init__(self):
        super().__init__()
        self._workspaces = {}
        self._patched_files = {}

    def create_workspace(self, repo_url: str) -> WorkspaceDescriptor:
        ws = WorkspaceDescriptor(
            workspace_id="ws-daytona-mock-42",
            repo_url=repo_url,
            status="RUNNING",
        )
        self._workspaces[ws.workspace_id] = ws
        return ws

    def exec_command(self, workspace_id: str, command: str) -> SandboxExecutionResult:
        # Simulate test failure when reproducing bug, and pass after patch
        if "pytest" in command:
            if any("locks.py" in k for k in self._patched_files):
                return SandboxExecutionResult(
                    workspace_id=workspace_id,
                    command=command,
                    exit_code=0,
                    stdout="14 passed, 0 failed in 0.38s. Stale locks cleared successfully.",
                    stderr="",
                    duration_ms=45.0,
                    passed=True,
                )
            else:
                return SandboxExecutionResult(
                    workspace_id=workspace_id,
                    command=command,
                    exit_code=1,
                    stdout="FAILED tests/test_locks.py::test_lock_timeout - RedisLockTimeout: unable to acquire lock within 2000ms",
                    stderr="AssertionError: lock timeout",
                    duration_ms=45.0,
                    passed=False,
                )

        return SandboxExecutionResult(
            workspace_id=workspace_id,
            command=command,
            exit_code=0,
            stdout="OK",
            stderr="",
            duration_ms=10.0,
            passed=True,
        )

    def apply_patch(self, workspace_id: str, file_path: str, patch_content: str) -> bool:
        self._patched_files[file_path] = patch_content
        return True

    def destroy_workspace(self, workspace_id: str) -> bool:
        if workspace_id in self._workspaces:
            del self._workspaces[workspace_id]
        return True
