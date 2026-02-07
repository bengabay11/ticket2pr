import logging
from pathlib import Path

from src.agents.base import print_agent_message, run_agent_query

logger = logging.getLogger(__name__)

TESTS_PLAN_FILENAME = "TESTS_PLAN.md"


TESTS_PLANNER_SYSTEM_PROMPT = """
You are an expert Software Engineer in the TEST PLANNING phase.

CRITICAL: You must ONLY identify EXISTING tests. Do NOT suggest, create, or write
any new tests. If there are no existing tests that clearly relate to the staged
changes, do NOT write {plan_filename}—exit without creating any file.

Workflow:
1. Run `git diff --cached --name-only` (and optionally `git diff --cached`) to
   see staged changes.
2. Find EXISTING tests related to those files (test dirs, naming, imports; use
   Grep/Glob as needed). Only list tests that already exist in the repo.
3. If you find no relevant existing tests for the staged changes, do nothing
   and do not write {plan_filename}.
4. If you do find relevant existing tests: inspect package/config and CI
   (e.g. package.json, Makefile, go.mod, .github/workflows) to discover how
   tests are run and how to set up. Then write {plan_filename} only. Do not
   modify other files or add the plan to git. Use Read, Glob, Grep, Bash for
   exploration; run only read-only or non-destructive commands.

Plan contents when you write the file (be specific so another agent can run and
fix tests from it):
- **Staged changes summary**
- **Related tests** (paths and/or names of EXISTING tests only)
- **Setup** (how to prepare the environment)
- **Run commands** (exact test command(s) for this project)
"""

TESTS_PLANNER_PROMPT_TEMPLATE = """
Analyze the staged git changes and produce a test plan in {plan_filename}.
"""


async def plan_tests(
    workspace_path: Path | None = None,
    mcp_config_path: Path | None = None,
    plan_filename: str = TESTS_PLAN_FILENAME,
) -> Path | None:
    """
    Analyze staged changes and create a test plan (related existing tests + how to run them).

    Only creates a plan if there are existing tests related to the staged changes.
    Never suggests or creates new tests.

    Args:
        workspace_path: Path to the workspace root. Defaults to current directory.
        mcp_config_path: Optional path to MCP config file.
        plan_filename: Name of the plan file to write. Defaults to TESTS_PLAN.md.

    Returns:
        Path to the created plan file, or None if no relevant existing tests were found
        (plan file is not written in that case).
    """
    cwd = Path(workspace_path).expanduser() if workspace_path else Path.cwd()
    plan_path = cwd / plan_filename

    system_prompt = TESTS_PLANNER_SYSTEM_PROMPT.format(plan_filename=plan_filename)
    prompt = TESTS_PLANNER_PROMPT_TEMPLATE.format(plan_filename=plan_filename)

    async for message in run_agent_query(
        prompt=prompt,
        system_prompt=system_prompt,
        allowed_tools=["Glob", "Bash", "Read", "Grep", "Write"],
        cwd=cwd,
        mcp_config_path=mcp_config_path,
    ):
        print_agent_message(message)

    if not plan_path.exists():
        return None
    return plan_path


TESTS_FIXER_SYSTEM_PROMPT = """
You are an expert Software Engineer in the TEST FIXING phase.

CRITICAL: Do NOT write or add any new tests. Only fix existing failing tests
or the implementation under test. If the only way to "fix" would be to add new
tests, do not do it—leave things as they are.

Workflow:
1. Run the plan test command(s) first (skip setup; env may already be ready).
   Only if the run fails due to env/setup (e.g. missing deps), run the plan
   setup then retry.
2. If tests fail for other reasons, analyze and fix ONLY existing code or
   existing tests as appropriate. Repeat until all planned tests pass (up to
   {max_retries} attempts). Never add new test cases or new test files.
3. When all pass, run `git add` only for files you modified. Do not stage
   {plan_filename}, unrelated files, or the whole repo. Delete any temporary
   helper files and do not add them to git.

Behavior:
- Fix only what is needed to make existing tests pass; correct existing tests
  when they are wrong, implementation when it is wrong. Do not create new tests.
- Use Read, Write, Grep, Glob, and Bash as needed.
"""

TESTS_FIXER_PROMPT_TEMPLATE = """
Run and fix tests according to the plan below until they pass, then stage only
your changes.

{plan_content}
"""


async def fix_tests(
    plan_content: str,
    plan_filename: str = TESTS_PLAN_FILENAME,
    workspace_path: Path | None = None,
    mcp_config_path: Path | None = None,
    max_retries: int = 10,
) -> None:
    """
    Run tests from the plan and fix failures until passing; then stage only the
    fixer's changes.

    Args:
        plan_content: Contents of the test plan (e.g. from plan_tests output).
        plan_filename: Name of the plan file (for "do not stage" instruction).
        workspace_path: Path to the workspace root. Defaults to current directory.
        mcp_config_path: Optional path to MCP config file.
        max_retries: Maximum number of fix-and-rerun cycles. Default 10.
    """
    cwd = Path(workspace_path).expanduser() if workspace_path else Path.cwd()

    system_prompt = TESTS_FIXER_SYSTEM_PROMPT.format(
        max_retries=max_retries,
        plan_filename=plan_filename,
    )
    prompt = TESTS_FIXER_PROMPT_TEMPLATE.format(
        plan_content=plan_content,
        max_retries=max_retries,
    )

    async for message in run_agent_query(
        prompt=prompt,
        system_prompt=system_prompt,
        allowed_tools=["Glob", "Bash", "Read", "Grep", "Write"],
        permission_mode="acceptEdits",
        cwd=cwd,
        mcp_config_path=mcp_config_path,
    ):
        print_agent_message(message)


async def try_fix_tests(
    workspace_path: Path | None = None,
    mcp_config_path: Path | None = None,
    max_retries: int = 10,
) -> None:
    """
    Plan tests from staged changes, run and fix until passing, then stage only
    the fixer's changes. Never writes new tests. If no relevant existing tests
    are found, does nothing and returns.

    Args:
        workspace_path: Path to the workspace root. Defaults to current directory.
        mcp_config_path: Optional path to MCP config file.
        max_retries: Maximum number of fix-and-rerun cycles for the fixer.
    """
    plan_path = await plan_tests(
        workspace_path=workspace_path,
        mcp_config_path=mcp_config_path,
    )
    if plan_path is None:
        logger.info("No relevant existing tests found for staged changes. Skipping test run.")
        return
    plan_content = plan_path.read_text()
    plan_path.unlink(missing_ok=True)
    await fix_tests(
        plan_content=plan_content,
        plan_filename=plan_path.name,
        workspace_path=workspace_path,
        mcp_config_path=mcp_config_path,
        max_retries=max_retries,
    )
