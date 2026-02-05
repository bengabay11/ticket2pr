from collections.abc import AsyncGenerator
from pathlib import Path

from claude_agent_sdk import (
    AssistantMessage,
    ClaudeAgentOptions,
    ContentBlock,
    Message,
    PermissionMode,
    ResultMessage,
    SystemMessage,
    TextBlock,
    ThinkingBlock,
    ToolResultBlock,
    ToolUseBlock,
    UserMessage,
    query,
)

from src.exceptions import AgentQueryUnknownError


def extract_session_id(message: Message) -> str | None:
    """
    Extract session_id from an init message.

    Returns the session_id if the message is an init SystemMessage, None otherwise.
    """
    if isinstance(message, SystemMessage) and message.subtype == "init":
        session_id: str | None = message.data.get("session_id")
        return session_id
    return None


def _format_content_blocks(content: list[ContentBlock]) -> list[str]:
    output_parts = []

    for block in content:
        if isinstance(block, TextBlock):
            # Show LLM text responses
            if block.text.strip():
                output_parts.append(block.text)

        elif isinstance(block, ThinkingBlock):
            # Show LLM thinking/reasoning
            if block.thinking.strip():
                output_parts.append(f"💭 {block.thinking}")

        elif isinstance(block, ToolUseBlock):
            # Show tool usage in a friendly way
            tool_name = block.name
            tool_input = block.input

            if tool_name == "Read":
                file_path = tool_input.get("file_path", "unknown")
                output_parts.append(f"📖 Reading: {file_path}")

            elif tool_name == "Write":
                file_path = tool_input.get("file_path", "unknown")
                output_parts.append(f"✏️  Writing: {file_path}")

            elif tool_name == "Edit":
                file_path = tool_input.get("file_path", "unknown")
                output_parts.append(f"🔧 Editing: {file_path}")

            elif tool_name == "Glob":
                pattern = tool_input.get("pattern", "unknown")
                output_parts.append(f"🔍 Searching files: {pattern}")

            elif tool_name == "Grep":
                pattern = tool_input.get("pattern", "unknown")
                output_parts.append(f"🔍 Searching content: {pattern}")

            elif tool_name == "Bash":
                command = tool_input.get("command", "unknown")
                description = tool_input.get("description")
                if description:
                    output_parts.append(f"💻 Bash: {description}")
                    output_parts.append(f"   ↳ {command}")
                else:
                    output_parts.append(f"💻 Bash: {command}")

            else:
                output_parts.append(f"🔧 Using tool: {tool_name}")

        elif isinstance(block, ToolResultBlock):
            if block.is_error:
                output_parts.append("Error calling tool.")
            else:
                output_parts.append("Tool call succeeded.")
            output_parts.append(block.content)

    return output_parts


def format_message_for_display(message: Message) -> str | None:
    """
    Format a Message object for user-friendly display.

    Returns a formatted string to display, or None if the message should be skipped.

    Message types:
    - UserMessage: Skip (user's own input)
    - AssistantMessage: Process content blocks (text, thinking, tool use)
    - SystemMessage: Skip (internal metadata like init)
    - ResultMessage: Show completion summary
    - StreamEvent: Handle partial streaming updates
    """
    if isinstance(message, UserMessage):
        # Skip user messages - they already know what they sent
        return None

    elif isinstance(message, AssistantMessage):
        # Process content blocks from the assistant
        output_parts = _format_content_blocks(message.content)
        if output_parts:
            return "\n".join(output_parts)
        return None

    elif isinstance(message, SystemMessage):
        # Skip system messages (init, etc.) - internal metadata
        return None

    elif isinstance(message, ResultMessage):
        # Show completion summary with cost if available
        parts = [f"✅ Completed in {message.duration_ms / 1000:.1f}s"]
        if message.total_cost_usd is not None:
            parts.append(f"(${message.total_cost_usd:.4f})")
        return " ".join(parts)

    return None


def print_agent_message(message: Message) -> None:
    """Print a message in a user-friendly format."""
    formatted = format_message_for_display(message)
    if formatted:
        print(formatted)


async def run_agent_query(
    prompt: str,
    system_prompt: str,
    allowed_tools: list[str],
    permission_mode: PermissionMode = "bypassPermissions",
    cwd: Path | None = None,
    mcp_config_path: Path | None = None,
    session_id: str | None = None,
) -> AsyncGenerator[Message]:
    """
    Execute a Claude Agent SDK query with standardized message handling.

    This function encapsulates the common pattern of creating ClaudeAgentOptions,
    executing a query, and printing the results.

    Args:
        prompt: The user prompt to send to the agent
        system_prompt: The system prompt defining the agent's role and behavior
        allowed_tools: List of tool names the agent is allowed to use
        permission_mode: Permission mode for the agent. Defaults to bypassPermissions
                        to allow full access without prompts.
        cwd: Optional current working directory for the agent to run from.
        mcp_config_path: Optional path to mcp.json configuration file for MCP servers.
    """
    options_kwargs = {
        "allowed_tools": allowed_tools,
        "system_prompt": system_prompt,
        "permission_mode": permission_mode,
    }

    if cwd is not None:
        options_kwargs["cwd"] = str(cwd)

    if mcp_config_path is not None:
        options_kwargs["mcp_servers"] = mcp_config_path

    if session_id is not None:
        options_kwargs["resume"] = session_id
    options = ClaudeAgentOptions(**options_kwargs)
    try:
        async for message in query(prompt=prompt, options=options):
            yield message
    except Exception as e:
        raise AgentQueryUnknownError(str(e)) from e
