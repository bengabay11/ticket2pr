from pathlib import Path

from claude_agent_sdk import TextBlock

from src.agents.base import print_agent_message, run_agent_query

SYSTEM_PROMPT = """
You are an expert Software Engineer. You write clear, concise, and helpful git commit messages.
You strictly follow the "Conventional Commits" specification.

CRITICAL OUTPUT RULES:
- Output ONLY the commit message text itself
- Do NOT include any explanations, markdown formatting, code blocks, or conversational text
- Do NOT include headers like "Suggested Commit Message:" or "Here's the commit message:"
- Do NOT wrap the message in quotes or code blocks
- Start directly with the subject line
- End after the footer (if any) - no additional text

CRITICAL CONTENT RULES:
1. **Completeness:** Do NOT omit any staged changes, no matter how small.
2. **Separation:** If two changes are technically unrelated (even if in the same file), separate
 them into distinct bullet points.
3. **No Grouping:** Avoid vague grouping like "Update config files." Instead, specify exactly what
 changed in which config file.

FORMATTING STRUCTURE:
- **Subject Line:** `<type>(<scope>): <subject>`
  - Types: feat, fix, docs, style, refactor, perf, test, build, ci, chore, revert.
  - Scope: Optional (e.g., auth, navbar).
  - Subject: Imperative mood ("add" not "added"), < 50 chars, no trailing period.
  - *Logic:* If the diff contains mixed types, use the most significant change for the Subject.

- **Body:**
  - Leave one blank line after the Subject.
  - **MANDATORY:** If the diff contains multiple distinct changes, you MUST list them here as
  bullet points to satisfy the "Completeness" rule.
  - Wrap lines at 72 chars.

- **Footer:** (Optional) Reference breaking changes or issue numbers.
"""

PROMPT = """Check staged changes and generate a commit message. Output ONLY the commit message
text, nothing else. No explanations, no markdown, no code blocks, no headers.
"""


async def generate_ai_commit_message(workspace_path: Path) -> str:
    full_message = ""
    async for message in run_agent_query(
        prompt=PROMPT,
        system_prompt=SYSTEM_PROMPT,
        allowed_tools=["Glob", "Bash", "Read", "Grep"],
        cwd=workspace_path,
    ):
        # Skip session_id (first yielded item)
        if isinstance(message, str):
            continue

        print_agent_message(message)

        if hasattr(message, "content"):
            for block in message.content:
                if isinstance(block, TextBlock):
                    full_message += block.text

    return full_message
