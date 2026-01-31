from github import Github
from github.GithubException import GithubException
from github.GitRef import GitRef
from pydantic import BaseModel

from src.exceptions import (
    GithubBranchCreationError,
    GithubBranchNotFoundError,
    GithubPRCreationError,
    GithubPRFetchError,
)


class FileDiff(BaseModel):
    """Pydantic model for a single file diff."""

    filename: str
    status: str  # added, removed, modified, renamed
    patch: str | None
    additions: int
    deletions: int
    changes: int


class PullRequestDetails(BaseModel):
    """Pydantic model for pull request details."""

    title: str
    body: str | None
    file_diff: list[FileDiff]


class GitHubClient:
    def __init__(
        self, github_token: str, repo_full_name: str, github_base_url: str | None = None
    ) -> None:
        if github_base_url:
            self.client = Github(base_url=github_base_url, login_or_token=github_token)
        else:
            self.client = Github(github_token)
        self.repo = self.client.get_repo(repo_full_name)

    def get_base_branch_ref(self, base_branch: str) -> GitRef:
        try:
            return self.repo.get_git_ref(f"heads/{base_branch}")
        except GithubException as e:
            raise GithubBranchNotFoundError(base_branch) from e

    def create_branch(self, branch_name: str, base_ref: GitRef) -> str:
        branch_url = f"{self.repo.html_url}/tree/{branch_name}"

        try:
            self.repo.create_git_ref(ref=f"refs/heads/{branch_name}", sha=base_ref.object.sha)
        except GithubException as e:
            if e.status == 422:  # Branch already exists
                pass
            else:
                raise GithubBranchCreationError(branch_name) from e

        return branch_url

    def create_pull_request(
        self,
        title: str,
        body: str,
        head_branch: str,
        base_branch: str,
        draft: bool = True,
    ) -> tuple[int, str]:
        try:
            pr = self.repo.create_pull(
                title=title,
                body=body,
                head=head_branch,
                base=base_branch,
                draft=draft,
            )
        except GithubException as e:
            raise GithubPRCreationError from e
        else:
            return pr.number, pr.html_url

    def get_pull_request(self, pr_number: int) -> PullRequestDetails:
        """
        Get details of a pull request by its number.

        Args:
            pr_number: The pull request number

        Returns:
            PullRequestDetails: A Pydantic model containing:
            - title: PR title
            - body: PR description
            - file_diff: List of FileDiff objects for each changed file
        """
        try:
            pr = self.repo.get_pull(pr_number)

            # Get all files changed in the PR
            files = pr.get_files()

            # Collect file diffs
            file_diffs = []

            for file in files:
                file_diffs.append(
                    FileDiff(
                        filename=file.filename,
                        status=file.status,
                        patch=file.patch,
                        additions=file.additions,
                        deletions=file.deletions,
                        changes=file.changes,
                    )
                )

            return PullRequestDetails(
                title=pr.title,
                body=pr.body,
                file_diff=file_diffs,
            )
        except GithubException as e:
            raise GithubPRFetchError(pr_number) from e
