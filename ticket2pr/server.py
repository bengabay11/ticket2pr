from __future__ import annotations

import asyncio
import logging

from fastapi import FastAPI
from pydantic import BaseModel

from ticket2pr import __version__
from ticket2pr.bootstrap import setup, setup_workspace
from ticket2pr.clients.github_client import GitHubClient
from ticket2pr.clients.jira_client import JiraClient
from ticket2pr.settings import AppSettings

logger = logging.getLogger(__name__)


class WebhookPayload(BaseModel):
    issue_key: str
    repo_full_name: str | None = None


class HealthResponse(BaseModel):
    status: str
    service: str
    version: str


class WebhookResponse(BaseModel):
    status: str
    issue_key: str


def _run_workflow_in_background(
    issue_key: str,
    settings: AppSettings,
    github_client: GitHubClient,
    jira_client: JiraClient,
    repo_full_name_override: str | None = None,
) -> None:
    """Run the full ticket2pr workflow for a single issue. Intended to be
    called from a background thread so it doesn't block the server."""
    from ticket2pr.workflow import workflow

    if repo_full_name_override:
        github_client = GitHubClient(
            github_token=settings.github.api_token,
            repo_full_name=repo_full_name_override,
        )

    with setup_workspace(None, settings.core.workspace_path, github_client) as (
        local_git,
        workspace_path,
    ):
        repo_name = repo_full_name_override or settings.github.repo_full_name
        logger.info(
            "Starting workflow for %s (repo: %s, base branch: %s, local workspace: %s)",
            issue_key,
            repo_name,
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
        logger.info(
            "Received webhook for issue: %s (repo: %s)",
            payload.issue_key,
            payload.repo_full_name,
        )
        loop = asyncio.get_running_loop()
        loop.run_in_executor(
            None,
            _run_workflow_in_background,
            payload.issue_key,
            settings,
            github_client,
            jira_client,
            payload.repo_full_name,
        )
        return WebhookResponse(status="accepted", issue_key=payload.issue_key)

    @fastapi_app.get("/health", response_model=HealthResponse)
    async def health() -> HealthResponse:
        return HealthResponse(status="ok", service="ticket2pr-server", version=__version__)

    return fastapi_app
