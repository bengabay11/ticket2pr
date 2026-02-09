from __future__ import annotations

import asyncio
import logging
import shutil
import sys
import tempfile
from collections.abc import Generator
from contextlib import contextmanager
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
from src.exceptions import GitCloneError
from src.logging_setup import LoggerHandlerType, SetupLoggerParams, setup_logger
from src.settings import AppSettings

logger = logging.getLogger(__name__)

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


def _initialize_clients(settings: AppSettings) -> tuple[GitHubClient, JiraClient]:
    from src.clients.github_client import GitHubClient
    from src.clients.jira_client import JiraClient

    github_client = GitHubClient(
        github_token=settings.github.api_token,
        repo_full_name=settings.github.repo_full_name,
    )
    jira_client = JiraClient(
        url=settings.jira.base_url,
        username=settings.jira.username,
        password=settings.jira.api_token,
    )
    return github_client, jira_client


def _init() -> None:
    from src.settings import DEFAULT_CONFIG_DIR
    from src.settings_init import initialize_settings

    config_path = DEFAULT_CONFIG_DIR / "config.toml"
    initialize_settings(config_path)


@contextmanager
def _setup_workspace(
    workspace_path_arg: Path | None,
    workspace_path_settings: Path | None,
    github_client: GitHubClient,
) -> Generator[tuple[EnhancedGit, Path]]:
    """
    Set up the workspace for the workflow.

    If no workspace_path is provided (neither arg nor settings), clones the repository
    to a temp directory and cleans it up when done.

    Yields:
        A tuple of (EnhancedGit instance, workspace_path)
    """
    workspace_path = workspace_path_arg or workspace_path_settings
    temp_dir: Path | None = None
    try:
        if workspace_path is None:
            shared_temp_dir = Path(tempfile.gettempdir()) / "ticket2pr"
            shared_temp_dir.mkdir(exist_ok=True)
            temp_dir = Path(
                tempfile.mkdtemp(dir=shared_temp_dir, prefix=f"{github_client.repo.name}_")
            )
            logger.info(
                "No workspace path provided, cloning repository to temp directory: %s", temp_dir
            )
            try:
                logger.info("Attempting to clone via SSH: %s", github_client.ssh_url)
                local_git = EnhancedGit.clone_repo(github_client.ssh_url, temp_dir)
            except GitCloneError:
                logger.warning(
                    "SSH clone failed, falling back to HTTPS: %s", github_client.clone_url
                )
                local_git = EnhancedGit.clone_repo(github_client.clone_url, temp_dir)
            logger.info("Repository cloned successfully")
            yield local_git, temp_dir
        else:
            yield EnhancedGit(workspace_path), workspace_path
    finally:
        if temp_dir and temp_dir.exists():
            logger.info("Cleaning up temp directory: %s", temp_dir)
            try:
                shutil.rmtree(temp_dir)
            except Exception as e:
                logger.warning("Failed to clean up temp directory '%s': %s", temp_dir, e)


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

    from src.workflow import workflow

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
    jira_issue: str = typer.Argument(
        ...,
        help="Jira issue key (e.g., PROJ-123) or Jira issue URL "
        "(e.g., https://company.atlassian.net/browse/PROJ-123)",
    ),
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
    from src.validators import parse_jira_input

    # Parse the input - could be a key or URL
    try:
        jira_issue_key = parse_jira_input(jira_issue)
    except ValueError as e:
        print_error_inline(f"Invalid Jira issue input: {e}")
        sys.exit(1)

    settings = _load_settings()

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
            github_client, jira_client = _initialize_clients(settings)
        except Exception as e:
            print_error(str(e))
            sys.exit(1)

    with _setup_workspace(workspace_path, settings.core.workspace_path, github_client) as (
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
