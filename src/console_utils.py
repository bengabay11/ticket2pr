"""Unified console printing utilities for consistent formatting across the application."""

from collections.abc import AsyncGenerator, Generator
from contextlib import contextmanager
from typing import Any

from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn

# Shared console instance for consistent styling
console = Console()

# Formatting constants (encapsulated)
_BOLD_CYAN = "[bold cyan]"
_BOLD_GREEN = "[bold green]"
_BOLD_RED = "[bold red]"
_BOLD = "[bold]"
_CYAN = "[cyan]"
_DIM = "[dim]"
_GREEN = "[green]"
_RED = "[red]"
_YELLOW = "[yellow]"
_RESET = "[/]"


def print_empty_line() -> None:
    """Print an empty line."""
    console.print()


def print_formatted(message: str, **kwargs: Any) -> None:
    """Print a formatted message with rich markup support.

    Args:
        message: The message to print (supports rich markup)
        **kwargs: Additional arguments to pass to console.print()
    """
    console.print(message, **kwargs)


def print_success(message: str, title: str | None = None) -> None:
    """Print a success message with green Panel.fit.

    Args:
        message: The success message to display (plain text, formatting applied internally)
        title: Optional title for the panel
    """
    formatted_message = f"{_BOLD_GREEN}{message}{_RESET}"
    console.print()
    console.print(
        Panel.fit(
            formatted_message,
            border_style="green",
            title=title,
        )
    )


def print_error(message: str, title: str = "Error") -> None:
    """Print an error message with red Panel.fit.

    Args:
        message: The error message to display (plain text, formatting applied internally)
        title: Title for the error panel (default: "Error")
    """
    formatted_message = f"{_BOLD_RED}{message}{_RESET}"
    console.print()
    console.print(
        Panel.fit(
            formatted_message,
            border_style="red",
            title=title,
        )
    )


def print_info(message: str) -> None:
    """Print an info/header message with cyan Panel.fit.

    Args:
        message: The info message to display (plain text, formatting applied internally)
    """
    formatted_message = f"{_BOLD_CYAN}{message}{_RESET}"
    console.print()
    console.print(
        Panel.fit(
            formatted_message,
            border_style="cyan",
        )
    )


def print_warning(message: str) -> None:
    """Print a warning message with yellow formatting.

    Args:
        message: The warning message to display (plain text, formatting applied internally)
    """
    console.print(f"{_YELLOW}{message}{_RESET}")


def print_section(title: str) -> None:
    """Print a section header with blue Panel.

    Args:
        title: The section title (plain text, formatting applied internally)
    """
    formatted_title = f"{_BOLD}{title}{_RESET}"
    console.print(Panel(formatted_title, border_style="blue"))
    console.print()


def print_summary(content: str) -> None:
    """Print a summary panel with green Panel.

    Args:
        content: The summary content to display (plain text, formatting applied internally)
    """
    console.print(
        Panel(
            content,
            border_style="green",
        )
    )
    console.print()


def print_error_inline(message: str) -> None:
    """Print an inline error message (no panel).

    Args:
        message: The error message to display (plain text, formatting applied internally)
    """
    console.print(f"{_RED}Error:{_RESET} {message}")


def print_label_value(label: str, value: Any) -> None:
    """Print a label-value pair with dimmed label.

    Args:
        label: The label text
        value: The value to display
    """
    console.print(f"{_DIM}{label}:{_RESET} {value}")


def format_success_with_checkmark(message: str) -> str:
    """Format a success message with a checkmark.

    Args:
        message: The success message

    Returns:
        Formatted string with checkmark and green styling
    """
    return f"{_BOLD_GREEN}✓ {message}{_RESET}"


def format_error_with_cross(message: str) -> str:
    """Format an error message with a cross mark.

    Args:
        message: The error message

    Returns:
        Formatted string with cross and red styling
    """
    return f"{_BOLD_RED}✗ {message}{_RESET}"


def format_info_header(message: str) -> str:
    """Format an info header message.

    Args:
        message: The info message

    Returns:
        Formatted string with cyan styling
    """
    return f"{_BOLD_CYAN}{message}{_RESET}"


def format_dim(message: str) -> str:
    """Format a message with dim styling.

    Args:
        message: The message to format

    Returns:
        Formatted string with dim styling
    """
    return f"{_DIM}{message}{_RESET}"


def format_cyan(message: str) -> str:
    """Format a message with cyan styling.

    Args:
        message: The message to format

    Returns:
        Formatted string with cyan styling
    """
    return f"{_CYAN}{message}{_RESET}"


def format_yellow(message: str) -> str:
    """Format a message with yellow styling.

    Args:
        message: The message to format

    Returns:
        Formatted string with yellow styling
    """
    return f"{_YELLOW}{message}{_RESET}"


def format_bold(message: str) -> str:
    """Format a message with bold styling.

    Args:
        message: The message to format

    Returns:
        Formatted string with bold styling
    """
    return f"{_BOLD}{message}{_RESET}"


def format_status_message(message: str) -> str:
    """Format a status message with green styling.

    Args:
        message: The status message

    Returns:
        Formatted string with green styling
    """
    return f"{_BOLD_GREEN}{message}{_RESET}"


@contextmanager
def get_status(message: str, spinner: str = "dots") -> Generator[None]:
    """Context manager for status indicators.

    Args:
        message: The status message to display (plain text, formatting applied internally)
        spinner: The spinner style (default: "dots")

    Yields:
        The console status context
    """
    formatted_message = format_status_message(message)
    with console.status(formatted_message, spinner=spinner):
        yield


@contextmanager
def get_progress() -> Generator[Progress]:
    """Context manager for progress bars.

    Yields:
        A Progress instance configured with spinner and text columns
    """
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        yield progress


def format_progress_task(message: str) -> str:
    """Format a progress task message with cyan styling.

    Args:
        message: The progress task message

    Returns:
        Formatted string with cyan styling
    """
    return f"{_CYAN}{message}{_RESET}"
