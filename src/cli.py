from __future__ import annotations

import asyncio
import sys
from pathlib import Path
from typing import TYPE_CHECKING

import typer

from src.console_utils import (
    format_dim,
    format_success_with_checkmark,
    format_yellow,
    get_status,
    print_empty_line,
    print_error,
    print_error_inline,
    print_info,
    print_label_value,
    print_success,
    print_warning,
)
from src.enhanced_git import EnhancedGit
from src.logging_setup import LoggerHandlerType, SetupLoggerParams, setup_logger
from src.settings import AppSettings
from src.shell.claude_auth_status import is_claude_logged_in

if TYPE_CHECKING:
    from src.clients.github_client import GitHubClient
    from src.clients.jira_client import JiraClient

app = typer.Typer(
    name="ticket2pr",
    help="Automate Jira ticket to GitHub PR workflow",
    add_completion=False,
    rich_markup_mode="rich",
    context_settings={"help_option_names": ["-h", "--help"]},
)


def _load_settings() -> AppSettings:
    from dotenv import load_dotenv

    load_dotenv()
    try:
        return AppSettings()
    except Exception as e:
        print_error_inline(f"loading settings: {e}")
        sys.exit(1)


def _initialize_clients(settings: AppSettings) -> tuple[GitHubClient, JiraClient, EnhancedGit]:
    from src.clients.github_client import GitHubClient
    from src.clients.jira_client import JiraClient
    from src.enhanced_git import EnhancedGit

    github_client = GitHubClient(
        github_token=settings.github.api_token,
        repo_full_name=settings.github.repo_full_name,
    )
    jira_client = JiraClient(
        url=settings.jira.base_url,
        username=settings.jira.username,
        password=settings.jira.api_token,
    )
    git = EnhancedGit(settings.core.workspace_path)
    return github_client, jira_client, git


def _init() -> None:
    from src.settings import DEFAULT_CONFIG_DIR
    from src.settings_init import initialize_settings

    config_path = DEFAULT_CONFIG_DIR / "config.toml"
    initialize_settings(config_path)


async def workflow_with_prints(
    jira_issue_key: str,
    workspace_path: Path,
    base_branch: str,
    github_client: GitHubClient,
    jira_client: JiraClient,
    local_git: EnhancedGit,
) -> None:
    header_msg = f"Running workflow for {format_yellow(jira_issue_key)}"
    print_info(header_msg)
    print_label_value("Workspace", workspace_path)
    print_label_value("Base branch", base_branch)
    print_label_value("Github repository", github_client.repo.full_name)
    print_empty_line()

    from src.workflow import workflow

    result = await workflow(
        github_client=github_client,
        jira_client=jira_client,
        jira_issue_key=jira_issue_key,
        git=local_git,
        base_branch=base_branch,
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
) -> None:
    """Execute the workflow for a specific Jira ticket."""

    settings = _load_settings()

    if not is_claude_logged_in():
        hint = "Run /login or set the 'ANTHROPIC_API_KEY' environment variable."
        message = "Claude Code authentication not found."
        print_error(message)
        print_label_value("Hint", hint)
        sys.exit(1)

    final_workspace_path = workspace_path or settings.core.workspace_path
    final_base_branch = base_branch or settings.core.base_branch

    setup_logger(
        SetupLoggerParams(
            level=settings.logging.min_log_level,
            handler_types={LoggerHandlerType.STREAM, LoggerHandlerType.FILE},
            file_path=settings.logging.log_file_path,
        )
    )

    with get_status("Initializing clients...", spinner="dots"):
        try:
            github_client, jira_client, local_git = _initialize_clients(settings)
        except Exception as e:
            print_error(str(e))
            sys.exit(1)

    try:
        asyncio.run(
            workflow_with_prints(
                jira_issue_key,
                final_workspace_path,
                final_base_branch,
                github_client,
                jira_client,
                local_git,
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


if __name__ == "__main__":
    app()
