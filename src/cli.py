import asyncio
import sys
from pathlib import Path

import typer
from dotenv import load_dotenv

from src.clients.github_client import GitHubClient
from src.clients.jira_client import JiraClient
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
from src.logging_setup import LoggerHandlerType, SetupLoggerParams, setup_logger
from src.settings import DEFAULT_CONFIG_DIR, AppSettings
from src.settings_init import initialize_settings, settings_exist
from src.workflow import workflow

app = typer.Typer(
    name="ticket2pr",
    help="Automate Jira ticket to GitHub PR workflow",
    add_completion=False,
    rich_markup_mode="rich",
    context_settings={"help_option_names": ["-h", "--help"]},
)


def _load_settings() -> AppSettings:
    load_dotenv()
    try:
        return AppSettings()
    except Exception as e:
        print_error_inline(f"loading settings: {e}")
        sys.exit(1)


def _initialize_clients(settings: AppSettings) -> tuple[GitHubClient, JiraClient]:
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
    config_path = DEFAULT_CONFIG_DIR / "config.toml"
    initialize_settings(config_path)


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
            github_client, jira_client = _initialize_clients(settings)
        except Exception as e:
            print_error_inline(f"initializing clients: {e}")
            sys.exit(1)

    header_msg = f"Running workflow for {format_yellow(jira_issue_key)}"
    print_info(header_msg)
    print_label_value("Workspace", final_workspace_path)
    print_label_value("Base branch", final_base_branch)
    print_empty_line()

    try:
        asyncio.run(
            workflow(
                github_client=github_client,
                jira_client=jira_client,
                jira_issue_key=jira_issue_key,
                workspace_path=final_workspace_path,
                base_branch=final_base_branch,
            )
        )

        success_msg = format_success_with_checkmark("Workflow completed successfully!")
        issue_msg = format_dim(f"Issue: {jira_issue_key}")
        branch_msg = format_dim(f"Branch: Created from {final_base_branch}")
        print_success(f"{success_msg}\n{issue_msg}\n{branch_msg}")
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


@app.callback(invoke_without_command=True)
def main(ctx: typer.Context) -> None:
    if not settings_exist():
        _init()
        print_empty_line()
        sys.exit(0)

    if ctx.invoked_subcommand is None:
        typer.echo(ctx.get_help())


if __name__ == "__main__":
    app()
