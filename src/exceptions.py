from pathlib import Path


class TicketToPRError(Exception):
    pass


class EnhancedGitError(TicketToPRError):
    pass


class GitFetchCheckoutError(EnhancedGitError):
    def __init__(self) -> None:
        super().__init__("Failed to fetch and checkout branch")


class GitPushError(EnhancedGitError):
    def __init__(self) -> None:
        super().__init__("Failed to commit and push changes")


class InvalidGitRepositoryError(EnhancedGitError):
    def __init__(self) -> None:
        super().__init__("Error: The directory provided is not a valid Git repository.")


class NoStagedChangesError(EnhancedGitError):
    pass


class ClientError(TicketToPRError):
    pass


class GithubClientError(ClientError):
    pass


class GithubBranchNotFoundError(GithubClientError):
    def __init__(self, branch_name: str):
        super().__init__(f"Failed to find base branch '{branch_name}'")


class GithubBranchCreationError(GithubClientError):
    def __init__(self, branch_name: str):
        super().__init__(f"Failed to create branch '{branch_name}'")


class GithubPRCreationError(GithubClientError):
    def __init__(self) -> None:
        super().__init__("Failed to create pull request")


class GithubPRFetchError(GithubClientError):
    def __init__(self, pr_number: int):
        super().__init__(f"Failed to get pull request #{pr_number}")


class JiraClientError(ClientError):
    pass


class JiraIssueFetchError(JiraClientError):
    def __init__(self, issue_key: str):
        super().__init__(f"Failed to fetch Jira issue {issue_key}")


class PlanNotFoundError(TicketToPRError):
    def __init__(self, plan_path: Path):
        super().__init__(f"PLAN.md not found at {plan_path}.")


class PreCommitNotFoundError(TicketToPRError):
    def __init__(self) -> None:
        super().__init__("pre-commit executable not found in PATH.")
