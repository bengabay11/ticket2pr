from pathlib import Path

from src.agents.base import run_agent_query
from src.shell.pre_commit_runner import run_pre_commit

SYSTEM_PROMPT = """
You are an expert Software Engineer specializing in fixing pre-commit hook failures.

Your role is to:
1. Analyze pre-commit hook failures and error messages
2. Fix the issues without changing the original intent of the code changes
3. Apply fixes that satisfy the pre-commit hooks (formatting, linting, type checking, etc.)
4. Preserve the original functionality and purpose of the changes

CRITICAL RULES:
- Only fix formatting, linting, type errors, and other pre-commit hook violations
- DO NOT change the logic or functionality of the code
- DO NOT add new features or remove existing functionality
- DO NOT modify code that wasn't part of the original changes
- Fix issues exactly as the pre-commit hooks require (e.g., black formatting, flake8 linting, mypy
type checking)
- Apply fixes to the files that failed the pre-commit checks
- Be precise and minimal - only change what's necessary to pass the hooks

WORKFLOW:
1. Read the error messages carefully to understand what needs to be fixed
2. Apply the exact fixes required (e.g., if black wants a line reformatted, reformat it exactly as
black expects)
3. If multiple files have issues, fix all of them
4. After making fixes, you MUST stage the changed files using `git add <file_path>` for each file
you modified
5. Only stage the files you actually fixed - do not stage unrelated changes
6. After staging fixes, run `pre-commit run` again to verify your fixes worked
7. If pre-commit still fails, analyze the new errors and fix them
8. Retry this fix-and-verify cycle up to {max_retries} times total
9. If pre-commit passes, you're done - stop retrying
"""

PROMPT_TEMPLATE = """Fix the pre-commit hook failures.

Pre-commit output:
{pre_commit_output}
"""


async def verify_pre_commit_and_fix(workspace_path: Path, max_retries: int = 5) -> bool:
    """
    Verify pre-commit hooks pass, fixing issues if needed.

    This function:
    1. Runs pre-commit hooks on staged files
    2. If successful, returns True
    3. If failed, uses AI to fix the issues (AI will stage its own fixes and retry)

    Args:
        git: EnhancedGit instance for staging changes
        workspace_path: Path to the workspace root
        max_retries: Maximum number of retry attempts to tell the AI (default: 5)

    Returns:
        True if pre-commit passes, False otherwise
    """
    result = run_pre_commit(workspace_path)

    if result.success:
        return True

    system_prompt = SYSTEM_PROMPT.format(max_retries=max_retries)

    prompt = PROMPT_TEMPLATE.format(
        pre_commit_output=result.output,
    )

    async for message in run_agent_query(
        prompt=prompt,
        system_prompt=system_prompt,
        allowed_tools=["Glob", "Bash", "Read", "Grep", "Write"],
        permission_mode="acceptEdits",
        cwd=workspace_path,
    ):
        print(message)

    final_result = run_pre_commit(workspace_path)
    return final_result.success
