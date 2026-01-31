import re
from pathlib import Path

from pydantic import HttpUrl, ValidationError


def validate_workspace_path(path_str: str) -> Path:
    try:
        return Path(path_str).expanduser().resolve()
    except Exception as e:
        msg = f"Invalid workspace path: {e!s}"
        raise ValueError(msg) from e


def validate_branch_name(branch: str) -> str:
    import git

    branch = branch.strip()
    if not branch:
        msg = "Branch name cannot be empty"
        raise ValueError(msg)
    try:
        git.cmd.Git().check_ref_format("--branch", branch)
    except git.exc.GitCommandError:
        msg = f"Invalid branch name: {branch}"
        raise ValueError(msg) from None
    return branch


def validate_url(url_input: str) -> str:
    try:
        HttpUrl(url_input)  # Validate format
    except ValidationError as e:
        msg = f"Invalid URL format: {url_input}"
        raise ValueError(msg) from e
    return url_input.strip()


def validate_repo_format(repo: str) -> str:
    repo = repo.strip().strip("/")
    if not repo:
        msg = "Repository name cannot be empty"
        raise ValueError(msg)
    parts = repo.split("/")
    if len(parts) != 2:
        msg = "Repository must be in format 'owner/repo' (e.g., 'githubuser/my-repo')"
        raise ValueError(msg)
    owner, repo_name = parts
    if not owner or not repo_name:
        msg = "Both owner and repository name are required"
        raise ValueError(msg)
    if re.search(r"[^\w\-.]", owner) or re.search(r"[^\w\-.]", repo_name):
        msg = (
            "Repository name contains invalid characters. "
            "Only letters, numbers, hyphens, underscores, and dots are allowed."
        )
        raise ValueError(msg)
    return f"{owner}/{repo_name}"


def validate_non_empty(value: str, field_name: str = "Value") -> str:
    stripped = value.strip()
    if not stripped:
        msg = f"{field_name} cannot be empty"
        raise ValueError(msg)
    return stripped
