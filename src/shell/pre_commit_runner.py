import shutil
from pathlib import Path

from src.exceptions import PreCommitNotFoundError
from src.shell.base import CommandResult, run_command


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


def has_pre_commit_config(workspace_path: Path) -> bool:
    """
    Check if .pre-commit-config.yaml exists and is a file in the workspace.

    Returns:
        True if .pre-commit-config.yaml exists and is a file, False otherwise
    """
    config_path = workspace_path.expanduser() / ".pre-commit-config.yaml"
    return config_path.is_file()


def run_pre_commit(workspace_path: Path) -> CommandResult:
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

    return run_command([pre_commit_executable, "run"], expanded_path)
