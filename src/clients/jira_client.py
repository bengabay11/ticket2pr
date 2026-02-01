from jira import JIRA, JIRAError
from pydantic import BaseModel

from src.exceptions import (
    JiraIssueFetchServerError,
    JiraIssueFetchUnknownError,
    JiraIssueNotFoundError,
)


class JiraIssue(BaseModel):
    key: str
    summary: str
    url: str
    permalink: str
    description: str | None = None
    type: str | None = None
    status: str | None = None


class JiraClient:
    def __init__(self, url: str, username: str, password: str) -> None:
        self._client: JIRA = JIRA(server=url, basic_auth=(username, password))
        self._url: str = url

    def fetch_issue(self, issue_key: str) -> JiraIssue:
        try:
            issue = self._client.issue(issue_key)
            issue_type = (
                issue.fields.issuetype.name
                if hasattr(issue.fields, "issuetype") and issue.fields.issuetype
                else None
            )
            status = (
                issue.fields.status.name
                if hasattr(issue.fields, "status") and issue.fields.status
                else None
            )
            return JiraIssue(
                key=issue_key,
                summary=issue.fields.summary,
                url=f"{self._url}/browse/{issue_key}",
                permalink=issue.permalink(),
                description=issue.fields.description or None,
                type=issue_type,
                status=status,
            )
        except JIRAError as e:
            if e.status_code == 404:
                raise JiraIssueNotFoundError(issue_key) from e
            else:
                raise JiraIssueFetchServerError(issue_key, str(e)) from e
        except Exception as e:
            raise JiraIssueFetchUnknownError(issue_key) from e

    def link_branch(self, issue_key: str, branch_url: str, branch_name: str) -> None:
        link_object = {
            "url": branch_url,
            "title": f"GitHub Branch: {branch_name}",
            "icon": {
                "title": "GitHub",
                "url16x16": "https://github.githubassets.com/favicons/favicon.png",
            },
        }
        unique_id = f"system=github&id={branch_url}"
        self._client.add_remote_link(
            issue=issue_key,
            destination=link_object,
            globalId=unique_id,
            relationship="source",
        )
