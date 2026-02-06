import logging
import re
from datetime import datetime

from src.clients.github_client import GitHubClient
from src.clients.jira_client import JiraClient, JiraIssue

logger = logging.getLogger(__name__)


def sanitize_branch_name(name: str, max_length: int = 100) -> str:
    name = name.lower()
    # Replace any character that's not a lowercase letter, digit, or hyphen with a hyphen
    name = re.sub(r"[^a-z0-9-]", "-", name)
    # Replace one or more consecutive hyphens with a single hyphen
    name = re.sub(r"-+", "-", name)
    name = name.strip("-")
    if len(name) > max_length:
        name = name[:max_length].rstrip("-")
    return name


def generate_branch_name(
    issue_key: str,
    issue_summary: str,
    issue_type: str | None = None,
    max_length: int = 255,
) -> str:
    sanitized_summary = sanitize_branch_name(issue_summary)
    branch_name = f"{issue_key}-{sanitized_summary}"
    if issue_type:
        branch_name = f"{issue_type.lower()}/{branch_name}"

    # Add timestamp suffix to ensure uniqueness and avoid an extra
    # API call to check if branch exists
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    suggested_branch_name = f"{branch_name}-{timestamp}"
    if len(suggested_branch_name) > max_length:
        chars_count_to_remove = len(suggested_branch_name) - max_length
        branch_name = branch_name[:-chars_count_to_remove]

    return f"{branch_name}-{timestamp}"


def create_branch_from_jira_issue(
    jira_issue: JiraIssue,
    jira_client: JiraClient,
    github_client: GitHubClient,
    base_branch: str = "main",
) -> str:
    branch_name = generate_branch_name(jira_issue.key, jira_issue.summary, jira_issue.type)
    # TODO: Consider replacing the 2 next lines with local git client
    base_ref = github_client.get_base_branch_ref(base_branch)

    branch_url = github_client.create_branch(branch_name, base_ref)
    jira_client.link_branch(jira_issue.key, branch_url, branch_name)

    return branch_name
