import logging
from pathlib import Path

from src.agents.commit_message import generate_ai_commit_message
from src.agents.pre_commit_fixer import verify_pre_commit_and_fix
from src.agents.ticket_solver import try_solve_ticket
from src.branch_creator import create_branch_from_jira_issue
from src.clients.github_client import GitHubClient
from src.clients.jira_client import JiraClient
from src.enhanced_git import EnhancedGit
from src.pr_content import generate_pr_title_from_jira_issue
from src.pre_commit_runner import is_pre_commit_installed

logger = logging.getLogger(__name__)


async def workflow(
    github_client: GitHubClient,
    jira_client: JiraClient,
    jira_issue_key: str,
    workspace_path: Path,
    base_branch: str,
) -> None:
    logger.info("Fetching Jira issue: %s", jira_issue_key)
    issue = jira_client.fetch_issue(jira_issue_key)
    logger.info("Creating branch for issue %s from base branch: %s", issue.key, base_branch)
    branch_name = create_branch_from_jira_issue(
        jira_issue=issue,
        jira_client=jira_client,
        github_client=github_client,
        base_branch=base_branch,
    )
    logger.info("Creating branch for issue %s from base branch: %s", issue.key, base_branch)
    branch_name = create_branch_from_jira_issue(
        jira_issue=issue,
        jira_client=jira_client,
        github_client=github_client,
        base_branch=base_branch,
    )
    logger.info("Fetching and checking out branch: %s", branch_name)
    git = EnhancedGit(workspace_path)
    git.fetch_and_checkout_branch(branch_name)
    logger.info("Solving ticket: %s (workspace: %s)", issue.key, workspace_path)
    await try_solve_ticket(issue, workspace_path=workspace_path)
    if is_pre_commit_installed():
        logger.info("Verifying pre-commit (workspace: %s)", workspace_path)
        await verify_pre_commit_and_fix(workspace_path)
    else:
        logger.info("Skipping pre-commit verification: pre-commit is not installed")
    logger.info("Generating commit message for branch: %s", branch_name)
    commit_message = await generate_ai_commit_message()
    logger.info(
        "Committing and pushing to branch: %s (commit message: %s)",
        branch_name,
        commit_message.split("\n")[0] if commit_message else "N/A",
    )
    git.commit_and_push(commit_message)
    logger.info("Generating PR title for issue: %s", issue.key)
    pr_title = generate_pr_title_from_jira_issue(issue)
    logger.info("Creating PR: title='%s', head=%s, base=%s", pr_title, branch_name, base_branch)
    pr_body = ""
    github_client.create_pull_request(
        title=pr_title,
        body=pr_body,
        head_branch=branch_name,
        base_branch=base_branch,
    )
    logger.info("PR created successfully: '%s' (branch: %s)", pr_title, branch_name)

    # Get Pull request details from GitHub
    # Call to LLM to do local CR with jira ticket and github PR
    # Call to LLM to run relevant tests in the PR. if some. tests failed, fix them and add changes.
