import logging
from pathlib import Path

from pydantic import BaseModel

from src.agents.pr_generator import generate_commit_and_pr_body
from src.agents.pre_commit_fixer import try_fix_pre_commit as try_fix_pre_commit_agent
from src.agents.tests_agents import try_fix_tests
from src.agents.ticket_solver import try_solve_ticket
from src.branch_creator import create_branch_from_jira_issue
from src.clients.github_client import GitHubClient
from src.clients.jira_client import JiraClient
from src.enhanced_git import EnhancedGit
from src.pr_content import generate_pr_title_from_jira_issue
from src.shell.pre_commit_runner import (
    has_pre_commit_config,
    is_pre_commit_installed,
    run_pre_commit,
)

logger = logging.getLogger(__name__)


class WorkflowResult(BaseModel):
    branch_name: str
    pr_number: int
    pr_url: str
    jira_issue_permalink: str


async def try_fix_pre_commit(
    git: EnhancedGit, mcp_config_path: Path | None = None, retries: int = 3
) -> bool:
    """
    Try to run pre-commit and fix any failures with retries.

    Returns:
        True if pre-commit passes, False if it still fails after all retries.
    """
    result = run_pre_commit(git.repo_path)

    if result.success:
        logger.info("pre-commit passed on first run")
        return True

    for attempt in range(1, retries + 1):
        logger.info(
            "pre-commit failed (attempt %d/%d). Trying to fix it (workspace: %s)",
            attempt,
            retries,
            git.repo_path,
        )
        await try_fix_pre_commit_agent(
            git.repo_path,
            pre_commit_output=result.output,
            mcp_config_path=mcp_config_path,
        )

        result = run_pre_commit(git.repo_path)
        if result.success:
            logger.info("pre-commit passed after fix attempt %d", attempt)
            return True

        logger.warning("pre-commit still failing after fix attempt %d/%d", attempt, retries)

    logger.warning(
        "pre-commit verification failed after %d fix attempts. Will commit with --no-verify",
        retries,
    )
    return False


async def workflow(
    github_client: GitHubClient,
    jira_client: JiraClient,
    jira_issue_key: str,
    git: EnhancedGit,
    base_branch: str,
    mcp_config_path: Path | None = None,
    commit_no_verify: bool = False,
    fix_tests: bool = False,
) -> WorkflowResult:
    logger.info("Fetching Jira issue: %s", jira_issue_key)
    issue = jira_client.fetch_issue(jira_issue_key)
    logger.info("Creating branch for issue %s from base branch: %s", issue.key, base_branch)
    branch_name = create_branch_from_jira_issue(
        jira_issue=issue,
        jira_client=jira_client,
        github_client=github_client,
        base_branch=base_branch,
    )
    logger.info("Fetching and checking out branch: %s", branch_name)
    git.fetch_and_checkout_branch(branch_name)
    logger.info("Solving ticket: %s (workspace: %s)", issue.key, git.repo_path)
    session_id = await try_solve_ticket(
        issue, workspace_path=git.repo_path, mcp_config_path=mcp_config_path
    )
    if fix_tests:
        logger.info("Running and fixing tests from staged changes.")
        await try_fix_tests(
            workspace_path=git.repo_path,
            mcp_config_path=mcp_config_path,
        )
    if commit_no_verify:
        logger.info("Skipping pre-commit verification: --commit-no-verify flag is set")
    elif not has_pre_commit_config(git.repo_path):
        logger.info(
            "Skipping pre-commit verification: .pre-commit-config.yaml not found or not a file"
        )
    elif not is_pre_commit_installed():
        logger.info("Skipping pre-commit verification: pre-commit is not installed")
    else:
        logger.info("pre-commit is installed. Trying to run it and fix any failures.")
        await try_fix_pre_commit(git, mcp_config_path=mcp_config_path)
    logger.info("Generating commit message and PR body for branch: %s", branch_name)
    commit_message, pr_body = await generate_commit_and_pr_body(
        session_id=session_id, workspace_path=git.repo_path, mcp_config_path=mcp_config_path
    )
    logger.info(
        "Committing and pushing to branch: %s (commit message: %s)",
        branch_name,
        commit_message.split("\n")[0] if commit_message else "N/A",
    )
    git.commit_and_push(commit_message, no_verify=commit_no_verify)
    logger.info("Generating PR title for issue: %s", issue.key)
    pr_title = generate_pr_title_from_jira_issue(issue)
    logger.info("Creating PR: title='%s', head=%s, base=%s", pr_title, branch_name, base_branch)
    pr_number, pr_url = github_client.create_pull_request(
        title=pr_title,
        body=pr_body,
        head_branch=branch_name,
        base_branch=base_branch,
    )
    logger.info("PR created successfully: '%s' (branch: %s)", pr_title, branch_name)
    return WorkflowResult(
        branch_name=branch_name,
        pr_number=pr_number,
        pr_url=pr_url,
        jira_issue_permalink=issue.permalink,
    )

    # Get Pull request details from GitHub
    # Call to LLM to do local CR with jira ticket and github PR
    # Call to LLM to run relevant tests in the PR. if some. tests failed, fix them and add changes.
