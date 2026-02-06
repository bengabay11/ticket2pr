from pathlib import Path

from src.agents.base import print_agent_message, run_agent_query

SYSTEM_PROMPT = """
You are an expert Software Engineer specializing in fixing pre-commit hook failures.

Your role is to:
1. Analyze pre-commit hook failures and error messages
2. Fix the issues without changing the original intent of the code changes
3. Apply fixes that satisfy the pre-commit hooks (formatting, linting, type checking, etc.)
4. Preserve the original functionality and purpose of the changes

CRITICAL RULES:
- You MUST address ALL pre-commit issues reported - do not miss any errors or warnings
- Carefully parse the entire pre-commit output and fix every single issue mentioned
- Only fix formatting, linting, type errors, and other pre-commit hook violations
- DO NOT change the logic or functionality of the code
- DO NOT add new features or remove existing functionality
- DO NOT modify code that wasn't part of the original changes
- Fix issues exactly as the pre-commit hooks require (e.g., black formatting, flake8 linting, mypy
type checking)
- Apply fixes to the files that failed the pre-commit checks
- Be precise and minimal - only change what's necessary to pass the hooks
- NEVER run pre-commit with --all-files flag. ONLY run on staged files.

WORKFLOW:
1. Read the error messages carefully to understand what needs to be fixed
2. Apply the exact fixes required (e.g., if black wants a line reformatted, reformat it exactly as
black expects)
3. If multiple files have issues, fix all of them
4. After making fixes, you MUST stage the changed files using `git add <file_path>` for each file
you modified
5. Only stage the files you actually fixed - do not stage unrelated changes
6. After staging fixes, run `pre-commit run` again to verify your fixes worked
   (NEVER use --all-files)
7. If pre-commit still fails, analyze the new errors and fix them
8. Retry this fix-and-verify cycle up to {max_retries} times total
9. If pre-commit passes, you're done - stop retrying
"""

PROMPT_TEMPLATE = """Fix the pre-commit hook failures.

Pre-commit output:
{pre_commit_output}
"""


async def try_fix_pre_commit(
    workspace_path: Path,
    pre_commit_output: str,
    max_retries: int = 5,
    mcp_config_path: Path | None = None,
) -> None:
    """
    Attempt to fix pre-commit hook failures using AI.

    This function uses AI to analyze pre-commit failures and apply fixes.
    The caller is responsible for running pre-commit before and after to verify.

    Args:
        workspace_path: Path to the workspace root
        pre_commit_output: The output from a failed pre-commit run
        max_retries: Maximum number of retry attempts for the AI (default: 5)
        mcp_config_path: Optional path to MCP config file
    """
    system_prompt = SYSTEM_PROMPT.format(max_retries=max_retries)
    prompt = PROMPT_TEMPLATE.format(
        pre_commit_output=pre_commit_output,
    )

    async for message in run_agent_query(
        prompt=prompt,
        system_prompt=system_prompt,
        allowed_tools=["Glob", "Bash", "Read", "Grep", "Write"],
        permission_mode="acceptEdits",
        cwd=workspace_path,
        mcp_config_path=mcp_config_path,
    ):
        print_agent_message(message)
