from __future__ import annotations

import asyncio
import logging
from pathlib import Path

import tomli
from fastapi import FastAPI
from pydantic import BaseModel

from ticket2pr.bootstrap import setup, setup_workspace
from ticket2pr.clients.github_client import GitHubClient
from ticket2pr.clients.jira_client import JiraClient
from ticket2pr.settings import AppSettings

logger = logging.getLogger(__name__)

PYPROJECT_PATH = Path(__file__).resolve().parent.parent / "pyproject.toml"


class WebhookPayload(BaseModel):
    issue_key: str


class HealthResponse(BaseModel):
    status: str
    service: str
    version: str


class WebhookResponse(BaseModel):
    status: str
    issue_key: str


def _run_workflow_in_background(
    issue_key: str, settings: AppSettings, github_client: GitHubClient, jira_client: JiraClient
) -> None:
    """Run the full ticket2pr workflow for a single issue. Intended to be
    called from a background thread so it doesn't block the server."""
    from ticket2pr.workflow import workflow

    with setup_workspace(None, settings.core.workspace_path, github_client) as (
        local_git,
        workspace_path,
    ):
        logger.info(
            "Starting workflow for %s (repo: %s, base branch: %s, local workspace: %s)",
            issue_key,
            settings.github.repo_full_name,
            settings.core.base_branch,
            workspace_path,
        )
        result = asyncio.run(
            workflow(
                github_client=github_client,
                jira_client=jira_client,
                jira_issue_key=issue_key,
                git=local_git,
                base_branch=settings.core.base_branch,
            )
        )
        logger.info(
            "Workflow completed for %s — PR: %s (branch: %s, base: %s)",
            issue_key,
            result.pr_url,
            result.branch_name,
            settings.core.base_branch,
        )


def create_app() -> FastAPI:
    settings, github_client, jira_client = setup()
    fastapi_app = FastAPI(title="ticket2pr webhook server")

    @fastapi_app.post("/webhook", status_code=202, response_model=WebhookResponse)
    async def webhook(payload: WebhookPayload) -> WebhookResponse:
        logger.info("Received webhook for issue: %s", payload.issue_key)
        loop = asyncio.get_running_loop()
        loop.run_in_executor(
            None,
            _run_workflow_in_background,
            payload.issue_key,
            settings,
            github_client,
            jira_client,
        )
        return WebhookResponse(status="accepted", issue_key=payload.issue_key)

    with PYPROJECT_PATH.open("rb") as f:
        pyproject_file_content = tomli.load(f)
    package_version = pyproject_file_content["project"]["version"]
    package_name = pyproject_file_content["project"]["name"]

    @fastapi_app.get("/health", response_model=HealthResponse)
    async def health() -> HealthResponse:
        return HealthResponse(status="ok", service=package_name, version=package_version)

    return fastapi_app
