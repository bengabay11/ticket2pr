from __future__ import annotations

import asyncio
import logging
import sys
from pathlib import Path
from typing import TYPE_CHECKING

import typer

from ticket2pr.bootstrap import setup, setup_workspace
from ticket2pr.console_utils import (
    format_dim,
    format_success_with_checkmark,
    format_yellow,
    print_empty_line,
    print_error,
    print_info,
    print_label_value,
    print_success,
    print_warning,
)

logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    from ticket2pr.clients.github_client import GitHubClient
    from ticket2pr.clients.jira_client import JiraClient
    from ticket2pr.enhanced_git import EnhancedGit

app = typer.Typer(
    name="ticket2pr",
    help="Automate Jira ticket to GitHub PR workflow",
    add_completion=False,
    rich_markup_mode="rich",
    context_settings={"help_option_names": ["-h", "--help"]},
)


def _init() -> None:
    from ticket2pr.settings import DEFAULT_CONFIG_DIR
    from ticket2pr.settings_init import initialize_settings

    config_path = DEFAULT_CONFIG_DIR / "config.toml"
    initialize_settings(config_path)


async def workflow_with_prints(
    jira_issue_key: str,
    workspace_path: Path,
    base_branch: str,
    github_client: GitHubClient,
    jira_client: JiraClient,
    local_git: EnhancedGit,
    mcp_config_path: Path | None = None,
    commit_no_verify: bool = False,
    fix_tests: bool = False,
) -> None:
    header_msg = f"Running workflow for {format_yellow(jira_issue_key)}"
    print_info(header_msg)
    print_label_value("Workspace", workspace_path)
    print_label_value("Base branch", base_branch)
    print_label_value("Github repository", github_client.repo.full_name)
    print_empty_line()

    from ticket2pr.workflow import workflow

    result = await workflow(
        github_client=github_client,
        jira_client=jira_client,
        jira_issue_key=jira_issue_key,
        git=local_git,
        base_branch=base_branch,
        mcp_config_path=mcp_config_path,
        commit_no_verify=commit_no_verify,
        fix_tests=fix_tests,
    )

    success_msg = format_success_with_checkmark("Workflow completed successfully!")
    issue_msg = format_dim(f"Issue: {result.jira_issue_permalink}")
    pr_msg = format_dim(f"Pull Request: {result.pr_url}")
    branch_msg = format_dim(f"Branch: {result.branch_name}")
    base_branch_msg = format_dim(f"Base Branch: {base_branch}")

    final_msg = "\n".join([success_msg, issue_msg, pr_msg, branch_msg, base_branch_msg])
    print_success(final_msg)


@app.command()
def run(
    jira_issue_key: str = typer.Argument(..., help="Jira issue key (e.g., PROJ-123)"),
    workspace_path: Path | None = typer.Option(  # noqa: B008
        None, "--workspace-path", "-w", help="Workspace path (overrides settings)"
    ),
    base_branch: str | None = typer.Option(
        None, "--base-branch", "-b", help="Base branch (overrides settings)"
    ),
    mcp_config_path: Path | None = typer.Option(  # noqa: B008
        None, "--mcp-config-path", "-m", help="Path to mcp.json config file for Claude agents"
    ),
    commit_no_verify: bool = typer.Option(
        False,
        "--commit-no-verify",
        "-c",
        help="bypass pre-commit and commit-msg hooks when committing (git commit --no-verify)",
    ),
    fix_tests: bool = typer.Option(
        False,
        "--fix-tests",
        "-t",
        help="plan and run tests from staged changes, fix failures, then stage only fix changes",
    ),
) -> None:
    """Execute the workflow for a specific Jira ticket."""
    settings, github_client, jira_client = setup()
    final_base_branch = base_branch or settings.core.base_branch

    with setup_workspace(workspace_path, settings.core.workspace_path, github_client) as (
        local_git,
        final_workspace_path,
    ):
        try:
            asyncio.run(
                workflow_with_prints(
                    jira_issue_key,
                    final_workspace_path,
                    final_base_branch,
                    github_client,
                    jira_client,
                    local_git,
                    mcp_config_path,
                    commit_no_verify,
                    fix_tests,
                )
            )
        except KeyboardInterrupt:
            print_empty_line()
            print_warning("Workflow interrupted by user")
            sys.exit(1)
        except Exception as e:
            print_error(str(e), title="Error")
            sys.exit(1)


@app.command()
def init() -> None:
    """Initialize settings configuration."""
    _init()


@app.command()
def server(
    host: str = typer.Option("127.0.0.1", "--host", help="Bind host"),
    port: int = typer.Option(8000, "--port", "-p", help="Bind port"),
) -> None:
    """Start the webhook server for Jira Automation."""
    import uvicorn

    from ticket2pr.server import create_app

    uvicorn.run(create_app(), host=host, port=port)


@app.command(name="help")
def help_command(ctx: typer.Context) -> None:
    """Show help information."""
    typer.echo(ctx.find_root().get_help())


def settings_exist() -> bool:
    config_file_path = Path.home() / ".ticket2pr" / "config.toml"
    return config_file_path.exists()


@app.callback(invoke_without_command=True)
def main(ctx: typer.Context) -> None:
    if not settings_exist():
        _init()
        sys.exit(0)

    if ctx.invoked_subcommand is None:
        typer.echo(ctx.get_help())


def cli_main() -> None:
    """Entry point for the CLI."""
    app()


if __name__ == "__main__":
    cli_main()
