import re
from pathlib import Path
from urllib.parse import urlparse

from pydantic import HttpUrl, ValidationError

# Jira issue key pattern: PROJECT-123 (letters/numbers for project, numbers for issue)
JIRA_ISSUE_KEY_PATTERN = re.compile(r"^[A-Z][A-Z0-9]+-\d+$", re.IGNORECASE)


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


def is_jira_url(input_str: str) -> bool:
    """Check if the input string looks like a Jira URL.

    Returns True if it matches the pattern of a Jira browse URL.
    Pattern: https://<domain>/browse/<issue-key>

    Args:
        input_str: The input string to check.

    Returns:
        True if the input looks like a Jira URL, False otherwise.
    """
    try:
        parsed = urlparse(input_str)
        # Must have a scheme (http/https) and netloc (domain)
        if not parsed.scheme or not parsed.netloc:
            return False
    except Exception:
        return False
    else:
        # Must have /browse/ in the path
        return "/browse/" in parsed.path


def extract_issue_key_from_url(url: str) -> str:
    """Extract the issue key from a Jira URL.

    Args:
        url: A Jira URL like https://company.atlassian.net/browse/PROJ-123

    Returns:
        The issue key (e.g., PROJ-123), normalized to uppercase.

    Raises:
        ValueError: If the URL format is invalid or doesn't contain a valid issue key.
    """
    try:
        parsed = urlparse(url)
        path = parsed.path
    except Exception as e:
        msg = f"Invalid URL format: {url}"
        raise ValueError(msg) from e

    # Find the issue key after /browse/
    if "/browse/" not in path:
        msg = f"URL does not contain '/browse/' path: {url}"
        raise ValueError(msg)

    # Extract the part after /browse/
    browse_index = path.find("/browse/")
    key_part = path[browse_index + len("/browse/") :]

    # Remove trailing slashes and get the issue key
    key_part = key_part.rstrip("/")

    # Handle case where there might be additional path segments
    if "/" in key_part:
        key_part = key_part.split("/")[0]

    # Validate the issue key format
    if not key_part or not JIRA_ISSUE_KEY_PATTERN.match(key_part):
        msg = f"Invalid Jira issue key in URL: '{key_part}'"
        raise ValueError(msg)

    # Return uppercase issue key
    return key_part.upper()


def parse_jira_input(input_str: str) -> str:
    """Parse the Jira input which can be either an issue key or a URL.

    Args:
        input_str: Either a Jira issue key (e.g., PROJ-123) or
                   a Jira URL (e.g., https://company.atlassian.net/browse/PROJ-123)

    Returns:
        The Jira issue key, normalized to uppercase.

    Raises:
        ValueError: If the input is neither a valid issue key nor a valid Jira URL.
    """
    input_str = input_str.strip()

    if not input_str:
        msg = "Jira input cannot be empty"
        raise ValueError(msg)

    # Check if it's a URL
    if is_jira_url(input_str):
        return extract_issue_key_from_url(input_str)

    # Otherwise, treat it as an issue key
    # Validate the issue key format
    if JIRA_ISSUE_KEY_PATTERN.match(input_str):
        return input_str.upper()

    # If it doesn't match the pattern, return as-is and let Jira API validate
    # This allows for flexibility with different Jira configurations
    return input_str
