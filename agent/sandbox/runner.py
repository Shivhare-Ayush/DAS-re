"""agent/sandbox/runner.py - Daytona-managed reproduction, patch, verify with metric gates."""
from typing import Any, Dict, Optional

from agent.sandbox.client import DaytonaSandboxClient


class SandboxRunner:
    """Manages the full ephemeral lifecycle of incident reproduction and fix under Daytona."""

    def __init__(self, client: DaytonaSandboxClient):
        self.client = client
        self._active_workspace_id: Optional[str] = None

    @property
    def active_workspace_id(self) -> Optional[str]:
        return self._active_workspace_id

    def provision_and_reproduce(self, repo_url: str, test_command: str) -> Dict[str, Any]:
        ws = self.client.create_workspace(repo_url)
        self._active_workspace_id = ws.workspace_id
        pre_test = self.client.exec_command(ws.workspace_id, test_command)
        return {
            "workspace_id": ws.workspace_id,
            "workspace_active": True,
            "defect_reproduced": not pre_test.passed,
            "pre_test_exit_code": pre_test.exit_code,
            "pre_test_duration_ms": pre_test.duration_ms,
            "pre_test_stdout": pre_test.stdout,
        }

    def apply_patch_and_verify(self, file_path: str, patch_code: str, test_command: str) -> Dict[str, Any]:
        if not self._active_workspace_id:
            raise RuntimeError("No active Daytona workspace; call provision_and_reproduce first.")
        ws_id = self._active_workspace_id
        self.client.apply_patch(ws_id, file_path, patch_code)
        post_test = self.client.exec_command(ws_id, test_command)
        return {
            "workspace_id": ws_id,
            "fix_verified": post_test.passed,
            "post_test_exit_code": post_test.exit_code,
            "post_test_duration_ms": post_test.duration_ms,
            "post_test_stdout": post_test.stdout,
            "total_duration_ms": post_test.duration_ms,
        }

    def teardown(self) -> bool:
        if not self._active_workspace_id:
            return True
        destroyed = self.client.destroy_workspace(self._active_workspace_id)
        self._active_workspace_id = None
        return destroyed

    def verify_remediation(self, repo_url: str, test_command: str, file_path: str, patch_code: str) -> Dict[str, Any]:
        repro = self.provision_and_reproduce(repo_url, test_command)
        verify = self.apply_patch_and_verify(file_path, patch_code, test_command)
        self.teardown()
        return {
            "workspace_id": repro["workspace_id"],
            "defect_reproduced": repro["defect_reproduced"],
            "fix_verified": verify["fix_verified"],
            "duration_ms": repro.get("pre_test_duration_ms", 0) + verify.get("post_test_duration_ms", 0),
        }
