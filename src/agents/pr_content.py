from clients.jira_client import JiraIssue


def generate_pr_title_from_jira_issue(jira_issue: JiraIssue) -> str:
    """
    Generate a deterministic PR title from a Jira issue.

    Args:
        jira_issue: The JiraIssue object containing issue details

    Returns:
        A string containing the PR title in format: [ISSUE-KEY] Summary
    """
    return f"[{jira_issue.key}] {jira_issue.summary}"
