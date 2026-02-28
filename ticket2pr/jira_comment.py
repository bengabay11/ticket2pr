import logging
import traceback

from ticket2pr.clients.jira_client import JiraClient

logger = logging.getLogger(__name__)


def build_started_comment(
    repo_name: str,
    repo_url: str,
    base_branch: str,
) -> str:
    return (
        f"h3. (i) ticket2pr - Workflow Started\n"
        f"\n"
        f"||Detail||Value||\n"
        f"|Repository|[{repo_name}|{repo_url}]|\n"
        f"|Base Branch|{{{{{base_branch}}}}}|\n"
    )


def build_success_comment(
    repo_name: str,
    repo_url: str,
    branch_name: str,
    base_branch: str,
    pr_url: str,
    duration: str,
) -> str:
    return (
        f"h3. (/) ticket2pr - Workflow Succeeded\n"
        f"\n"
        f"||Detail||Value||\n"
        f"|Repository|[{repo_name}|{repo_url}]|\n"
        f"|Branch|{{{{{branch_name}}}}}|\n"
        f"|Base Branch|{{{{{base_branch}}}}}|\n"
        f"|Pull Request|[View PR|{pr_url}]|\n"
        f"|Duration|{duration}|\n"
    )


def build_failure_comment(
    repo_name: str,
    repo_url: str,
    base_branch: str,
    duration: str,
    error: Exception,
) -> str:
    error_type = type(error).__name__
    error_msg = str(error)
    tb_str = "".join(traceback.format_exception(type(error), error, error.__traceback__))

    return (
        f"h3. (x) ticket2pr - Workflow Failed\n"
        f"\n"
        f"||Detail||Value||\n"
        f"|Repository|[{repo_name}|{repo_url}]|\n"
        f"|Base Branch|{{{{{base_branch}}}}}|\n"
        f"|Duration|{duration}|\n"
        f"\n"
        f"*Error:* {error_type}: {error_msg}\n"
        f"{{noformat:title=Full Traceback}}\n"
        f"{tb_str}"
        f"{{noformat}}\n"
    )


def post_jira_comment(jira_client: JiraClient, issue_key: str, comment: str) -> None:
    try:
        preview = comment[:50].replace("\n", " ")
        logger.info("Posting Jira comment to %s: %s...", issue_key, preview)
        jira_client.add_comment(issue_key, comment)
    except Exception:
        logger.exception("Failed to post Jira comment for %s", issue_key)
