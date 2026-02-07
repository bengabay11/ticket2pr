from collections.abc import Callable
from functools import wraps
from pathlib import Path
from typing import Any

import tomli_w

from src.console_utils import (
    format_bold,
    format_cyan,
    format_dim,
    format_success_with_checkmark,
    print_empty_line,
    print_error_inline,
    print_info,
    print_section,
    print_success,
    print_summary,
    print_warning,
)
from src.validators import (
    validate_non_empty,
    validate_repo_format,
    validate_url,
)


def _show_welcome() -> None:
    welcome_msg = "Welcome to Ticket2PR Configuration"
    subtitle_msg = format_dim("Let's set up your configuration step by step.")
    print_info(f"{welcome_msg}\n\n{subtitle_msg}")


def _show_summary(
    base_branch: str,
    jira_base_url: str,
    jira_username: str,
    repo_full_name: str,
) -> None:
    summary_content = "\n".join(
        [
            format_bold("Configuration Summary"),
            "",
            f"{format_dim('Base branch:')} {base_branch!s}",
            f"{format_dim('Jira URL:')} {jira_base_url!s}",
            f"{format_dim('Jira username:')} {jira_username!s}",
            f"{format_dim('Repository:')} {repo_full_name!s}",
        ]
    )
    print_summary(summary_content)


def _confirm_save() -> bool:
    from rich.prompt import Confirm

    if not Confirm.ask(format_cyan("Save this configuration?"), default=True):
        print_warning("Configuration cancelled.")
        return False
    return True


def _show_success(config_path: Path) -> None:
    success_msg = format_success_with_checkmark("Configuration saved successfully!")
    config_msg = format_dim(f"Config file: {config_path!s}")
    print_success(f"{success_msg}\n\n{config_msg}\n")


def _prompt_with_validation[T](
    prompt_text: str,
    validator: Callable[[str], T],
    default: str | None = None,
    password: bool = False,
    hint: str | None = None,
) -> T:
    formatted_prompt = format_cyan(prompt_text)
    if hint:
        formatted_prompt += format_dim(hint)

    value = None
    while value is None:
        try:
            from rich.prompt import Prompt

            user_input = Prompt.ask(formatted_prompt, default=default, password=password)
            if user_input is not None:
                value = validator(user_input)
        except Exception as e:
            print_error_inline(str(e))
            print_empty_line()
    return value


def section_decorator(section_name: str) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            print_section(section_name)
            result = func(*args, **kwargs)
            print_empty_line()
            return result

        return wrapper

    return decorator


@section_decorator("Core Settings")
def _collect_core_settings() -> str:
    from src.validators import validate_branch_name

    base_branch = _prompt_with_validation(
        "Base branch",
        validate_branch_name,
        default="main",
    )

    return base_branch


@section_decorator("Jira Settings")
def _collect_jira_settings() -> tuple[str, str, str]:
    jira_base_url = _prompt_with_validation(
        "Jira base URL",
        validate_url,
        hint=" (e.g., https://your-company.atlassian.net)",
    )

    jira_username = _prompt_with_validation(
        "Jira username/email",
        lambda v: validate_non_empty(v, "Username"),
    )

    jira_api_token = _prompt_with_validation(
        "Jira API token",
        lambda v: validate_non_empty(v, "API token"),
        password=True,
        hint=" (generate at https://id.atlassian.com/manage-profile/security/api-tokens)",
    )

    return jira_base_url, jira_username, jira_api_token


@section_decorator("GitHub Settings")
def _collect_github_settings() -> tuple[str, str]:
    github_api_token = _prompt_with_validation(
        "GitHub personal access token",
        lambda v: validate_non_empty(v, "API token"),
        password=True,
        hint=" (generate at https://github.com/settings/tokens)",
    )

    repo_full_name = _prompt_with_validation(
        "Repository",
        validate_repo_format,
        hint=" (e.g., owner/repo)",
    )

    return github_api_token, repo_full_name


def _write_toml_config(
    config_path: Path,
    base_branch: str,
    jira_base_url: str,
    jira_username: str,
    jira_api_token: str,
    github_api_token: str,
    repo_full_name: str,
) -> None:
    # Create parent directory if needed
    config_path.parent.mkdir(parents=True, exist_ok=True)

    config = {
        "core": {
            "base_branch": base_branch,
        },
        "jira": {
            "base_url": jira_base_url,
            "username": jira_username,
            "api_token": jira_api_token,
        },
        "github": {
            "api_token": github_api_token,
            "repo_full_name": repo_full_name,
        },
    }

    with config_path.open("wb") as f:
        tomli_w.dump(config, f)


def initialize_settings(config_path: Path) -> None:
    try:
        _show_welcome()

        base_branch = _collect_core_settings()
        jira_base_url, jira_username, jira_api_token = _collect_jira_settings()
        github_api_token, repo_full_name = _collect_github_settings()

        _show_summary(
            base_branch,
            jira_base_url,
            jira_username,
            repo_full_name,
        )
        if _confirm_save():
            _write_toml_config(
                config_path,
                base_branch,
                jira_base_url,
                jira_username,
                jira_api_token,
                github_api_token,
                repo_full_name,
            )
            _show_success(config_path)

    except KeyboardInterrupt:
        print_empty_line()
        print_warning("Configuration cancelled by user.")
        raise
