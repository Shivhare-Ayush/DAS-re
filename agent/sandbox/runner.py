"""agent/sandbox/runner.py - Orchestrates reproduction, patching, and verification."""
from typing import Dict, Any
from agent.sandbox.client import DaytonaSandboxClient


class SandboxRunner:
    """Manages the full ephemeral lifecycle of incident reproduction and fix."""

    def __init__(self, client: DaytonaSandboxClient):
        self.client = client

    def verify_remediation(self, repo_url: str, test_command: str, file_path: str, patch_code: str) -> Dict[str, Any]:
        # 1. Ephemeral Sandbox Creation
        ws = self.client.create_workspace(repo_url)

        # 2. Reproduce Defect
        pre_test = self.client.exec_command(ws.workspace_id, test_command)

        # 3. Apply Patch
        self.client.apply_patch(ws.workspace_id, file_path, patch_code)

        # 4. Re-run tests to confirm pass
        post_test = self.client.exec_command(ws.workspace_id, test_command)

        # 5. Teardown Sandbox
        self.client.destroy_workspace(ws.workspace_id)

        return {
            "workspace_id": ws.workspace_id,
            "defect_reproduced": not pre_test.passed,
            "fix_verified": post_test.passed,
            "duration_ms": pre_test.duration_ms + post_test.duration_ms,
        }
