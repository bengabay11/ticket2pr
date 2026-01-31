import logging
import os

from src.shell.base import run_command

logger = logging.getLogger(__name__)


def is_claude_logged_in() -> bool:
    try:
        result = run_command(["claude", "auth", "status"])
    except Exception:
        return False
    else:
        return result.return_code == 0 or "ANTHROPIC_API_KEY" in os.environ
