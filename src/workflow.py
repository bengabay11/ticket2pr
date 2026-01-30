from pathlib import Path

from agents.commit_message import generate_ai_commit_message
from agents.pr_content import generate_pr_title_from_jira_issue
from agents.pre_commit_fixer import verify_pre_commit_and_fix
from agents.ticket_solver import try_solve_ticket
from branch_creator import create_branch_from_jira_issue
from clients.github_client import GitHubClient
from clients.jira_client import JiraClient
from enhanced_git import EnhancedGit


async def workflow(
    github_client: GitHubClient,
    jira_client: JiraClient,
    jira_issue_key: str,
    workspace_path: Path,
    base_branch: str,
) -> None:
    print("Fetching Jira issue...")
    issue = jira_client.fetch_issue(jira_issue_key)
    print("Creating branch...")
    branch_name = create_branch_from_jira_issue(
        jira_issue=issue,
        jira_client=jira_client,
        github_client=github_client,
        base_branch=base_branch,
    )
    print("Fetching Jira issue...")
    issue = jira_client.fetch_issue(jira_issue_key)
    print("Creating branch...")
    branch_name = create_branch_from_jira_issue(
        jira_issue=issue,
        jira_client=jira_client,
        github_client=github_client,
        base_branch=base_branch,
    )
    print("Fetching and checking out branch...")
    git = EnhancedGit(workspace_path)
    git.fetch_and_checkout_branch(branch_name)
    print("Solving ticket...")
    await try_solve_ticket(issue, workspace_path=workspace_path)
    print("Verifying pre-commit...")
    await verify_pre_commit_and_fix(workspace_path)
    print("Generating commit message...")
    commit_message = await generate_ai_commit_message(git)
    print("Committing and pushing...")
    git.commit_and_push(commit_message)
    print("Generating PR title...")
    pr_title = generate_pr_title_from_jira_issue(issue)
    print("Creating PR...")
    pr_body = ""
    github_client.create_pull_request(
        title=pr_title,
        body=pr_body,
        head_branch=branch_name,
        base_branch=base_branch,
    )
    print("PR created successfully")

    # Get Pull request details from GitHub
    # Call to LLM to do local CR with jira ticket and github PR
    # Call to LLM to run relevant tests in the PR. if some. tests failed, fix them and add changes.
