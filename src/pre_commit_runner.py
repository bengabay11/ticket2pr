import shutil
import subprocess  # nosec B404: subprocess is required to run pre-commit tools
from pathlib import Path

from pydantic import BaseModel

from src.exceptions import PreCommitNotFoundError


class PreCommitResult(BaseModel):
    returncode: int
    stdout: str
    stderr: str

    @property
    def success(self) -> bool:
        return self.returncode == 0

    @property
    def output(self) -> str:
        return self.stdout + self.stderr


def find_pre_commit_executable() -> str | None:
    """
    Find the pre-commit executable in PATH.

    Returns:
        Path to the pre-commit executable if found, None otherwise
    """
    return shutil.which("pre-commit")


def is_pre_commit_installed() -> bool:
    """
    Check if pre-commit is installed and available in PATH.

    Returns:
        True if pre-commit is installed, False otherwise
    """
    return find_pre_commit_executable() is not None


def run_pre_commit(workspace_path: Path) -> PreCommitResult:
    """
    Run pre-commit hooks on staged files and return the result.

    Args:
        workspace_path: Path to the workspace root

    Returns:
        PreCommitResult with success status and output

    Raises:
        PreCommitNotFoundError: If pre-commit executable is not found in PATH
    """
    expanded_path = workspace_path.expanduser()

    # Resolving the full path to avoid Bandit B607 (start_process_with_partial_path)
    pre_commit_executable = find_pre_commit_executable()
    if not pre_commit_executable:
        raise PreCommitNotFoundError

    result = subprocess.run(
        [pre_commit_executable, "run"],  # nosec B603: pre_commit_executable is resolved via shutil.which and is trusted
        cwd=expanded_path,
        capture_output=True,
        text=True,
        check=False,
    )
    return PreCommitResult(
        returncode=result.returncode,
        stdout=result.stdout,
        stderr=result.stderr,
    )
