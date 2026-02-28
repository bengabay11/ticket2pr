from __future__ import annotations

import logging
import shutil
import sys
import tempfile
from collections.abc import Generator
from contextlib import contextmanager
from pathlib import Path

from dotenv import load_dotenv

from ticket2pr.clients.github_client import GitHubClient
from ticket2pr.clients.jira_client import JiraClient
from ticket2pr.console_utils import get_status, print_error
from ticket2pr.enhanced_git import EnhancedGit
from ticket2pr.exceptions import GitCloneError
from ticket2pr.logging_setup import LoggerHandlerType, SetupLoggerParams, setup_logger
from ticket2pr.settings import AppSettings

logger = logging.getLogger(__name__)


def setup() -> tuple[AppSettings, GitHubClient, JiraClient]:
    try:
        load_dotenv()
        settings = AppSettings()
    except Exception as e:
        print_error(str(e))
        sys.exit(1)

    setup_logger(
        SetupLoggerParams(
            level=settings.logging.min_log_level,
            handler_types={LoggerHandlerType.STREAM, LoggerHandlerType.FILE},
            file_path=settings.logging.log_file_path,
        )
    )
    with get_status("Initializing clients...", spinner="dots"):
        try:
            github_client = GitHubClient(
                github_token=settings.github.api_token,
                repo_full_name=settings.github.repo_full_name,
            )
            jira_client = JiraClient(
                url=settings.jira.base_url,
                username=settings.jira.username,
                password=settings.jira.api_token,
            )
        except Exception as e:
            print_error(str(e))
            sys.exit(1)
    return settings, github_client, jira_client


@contextmanager
def setup_workspace(
    workspace_path_arg: Path | None,
    workspace_path_settings: Path | None,
    github_client: GitHubClient,
) -> Generator[tuple[EnhancedGit, Path]]:
    """Set up the workspace for the workflow.

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
