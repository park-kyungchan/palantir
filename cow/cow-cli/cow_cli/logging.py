"""
COW CLI - Logging System

Rich console output and structured file logging.
"""
from typing import Optional, Any
from pathlib import Path
from datetime import datetime
import logging
import sys

from rich.console import Console
from rich.logging import RichHandler
from rich.progress import (
    Progress,
    SpinnerColumn,
    TextColumn,
    BarColumn,
    TaskProgressColumn,
    TimeElapsedColumn,
    TimeRemainingColumn,
)
from rich.table import Table
from rich.panel import Panel
from rich.syntax import Syntax
from rich import box

# Default paths
DEFAULT_LOG_DIR = Path.home() / ".cow" / "logs"

# Global console instance
console = Console()

# Logger instance
logger = logging.getLogger("cow-cli")


class COWLogger:
    """Structured logging with Rich console output."""

    def __init__(
        self,
        verbose: bool = False,
        log_dir: Optional[Path] = None,
        log_to_file: bool = True
    ):
        self.verbose = verbose
        self.log_dir = log_dir or DEFAULT_LOG_DIR
        self.log_to_file = log_to_file
        self._setup_logging()

    def _setup_logging(self) -> None:
        """Configure logging handlers."""
        # Clear existing handlers
        logger.handlers.clear()

        # Set base level
        level = logging.DEBUG if self.verbose else logging.INFO
        logger.setLevel(level)

        # Console handler with Rich
        console_handler = RichHandler(
            console=console,
            rich_tracebacks=True,
            tracebacks_show_locals=self.verbose,
            show_time=True,
            show_path=self.verbose,
        )
        console_handler.setLevel(level)
        console_handler.setFormatter(logging.Formatter("%(message)s"))
        logger.addHandler(console_handler)

        # File handler
        if self.log_to_file:
            self.log_dir.mkdir(parents=True, exist_ok=True)
            log_file = self.log_dir / f"cow-cli-{datetime.now():%Y%m%d}.log"
            file_handler = logging.FileHandler(log_file, encoding="utf-8")
            file_handler.setLevel(logging.DEBUG)
            file_handler.setFormatter(
                logging.Formatter(
                    "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
                )
            )
            logger.addHandler(file_handler)

    def debug(self, message: str, **kwargs: Any) -> None:
        """Log debug message."""
        logger.debug(message, **kwargs)

    def info(self, message: str, **kwargs: Any) -> None:
        """Log info message."""
        logger.info(message, **kwargs)

    def warning(self, message: str, **kwargs: Any) -> None:
        """Log warning message."""
        logger.warning(message, **kwargs)

    def error(self, message: str, **kwargs: Any) -> None:
        """Log error message."""
        logger.error(message, **kwargs)

    def exception(self, message: str, **kwargs: Any) -> None:
        """Log exception with traceback."""
        logger.exception(message, **kwargs)


# Error codes for structured error messages
class ErrorCode:
    """Standard error codes for COW CLI."""
    # Configuration errors (1xx)
    CONFIG_NOT_FOUND = "E101"
    CONFIG_INVALID = "E102"
    API_KEY_MISSING = "E103"
    API_KEY_INVALID = "E104"

    # Processing errors (2xx)
    FILE_NOT_FOUND = "E201"
    FILE_INVALID = "E202"
    IMAGE_CORRUPT = "E203"
    OCR_FAILED = "E204"

    # API errors (3xx)
    API_TIMEOUT = "E301"
    API_RATE_LIMITED = "E302"
    API_ERROR = "E303"
    NETWORK_ERROR = "E304"

    # Review errors (4xx)
    REVIEW_ITEM_NOT_FOUND = "E401"
    REVIEW_INVALID_ACTION = "E402"

    # Export errors (5xx)
    EXPORT_FAILED = "E501"
    FORMAT_UNSUPPORTED = "E502"


# Error suggestions mapping
ERROR_SUGGESTIONS = {
    ErrorCode.CONFIG_NOT_FOUND: "Run 'cow config init' to create a default configuration.",
    ErrorCode.API_KEY_MISSING: "Run 'cow config mathpix --app-id ID --app-key KEY' to set credentials.",
    ErrorCode.API_KEY_INVALID: "Verify your Mathpix credentials at https://accounts.mathpix.com",
    ErrorCode.FILE_NOT_FOUND: "Check if the file path is correct and the file exists.",
    ErrorCode.IMAGE_CORRUPT: "Try converting the image to PNG format.",
    ErrorCode.API_TIMEOUT: "Check your network connection or try again later.",
    ErrorCode.API_RATE_LIMITED: "Wait a few minutes before trying again.",
}


def setup_logging(
    verbose: bool = False,
    log_dir: Optional[Path] = None,
    log_to_file: bool = True
) -> COWLogger:
    """
    Setup logging with Rich console and file output.

    Args:
        verbose: Enable verbose (DEBUG) output
        log_dir: Directory for log files
        log_to_file: Enable file logging

    Returns:
        Configured COWLogger instance
    """
    return COWLogger(verbose=verbose, log_dir=log_dir, log_to_file=log_to_file)


def log_error(
    code: str,
    message: str,
    suggestion: Optional[str] = None,
    details: Optional[str] = None
) -> None:
    """
    Log structured error with code and suggestion.

    Args:
        code: Error code (e.g., "E101")
        message: Error message
        suggestion: Optional suggestion for resolution
        details: Optional technical details
    """
    console.print(f"[bold red]Error [{code}][/bold red]: {message}")

    if suggestion is None:
        suggestion = ERROR_SUGGESTIONS.get(code)

    if suggestion:
        console.print(f"[yellow]💡 Suggestion:[/yellow] {suggestion}")

    if details:
        console.print(f"[dim]Details: {details}[/dim]")

    logger.error(f"[{code}] {message}")


def log_success(message: str) -> None:
    """Log success message with checkmark."""
    console.print(f"[green]✓[/green] {message}")
    logger.info(f"SUCCESS: {message}")


def log_warning(message: str) -> None:
    """Log warning message."""
    console.print(f"[yellow]⚠[/yellow] {message}")
    logger.warning(message)


def log_info(message: str) -> None:
    """Log info message."""
    console.print(f"[blue]ℹ[/blue] {message}")
    logger.info(message)


def create_progress() -> Progress:
    """
    Create a Rich progress bar for long-running operations.

    Returns:
        Configured Progress instance
    """
    return Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TaskProgressColumn(),
        TimeElapsedColumn(),
        TimeRemainingColumn(),
        console=console,
    )


def print_table(
    title: str,
    columns: list[str],
    rows: list[list[Any]],
    show_header: bool = True
) -> None:
    """
    Print a formatted table.

    Args:
        title: Table title
        columns: Column headers
        rows: Row data
        show_header: Show column headers
    """
    table = Table(title=title, box=box.ROUNDED, show_header=show_header)

    for col in columns:
        table.add_column(col, style="cyan")

    for row in rows:
        table.add_row(*[str(cell) for cell in row])

    console.print(table)


def print_panel(
    content: str,
    title: Optional[str] = None,
    style: str = "blue"
) -> None:
    """
    Print content in a panel.

    Args:
        content: Panel content
        title: Optional panel title
        style: Border style/color
    """
    console.print(Panel(content, title=title, border_style=style))


def print_json(data: dict, title: Optional[str] = None) -> None:
    """
    Print JSON data with syntax highlighting.

    Args:
        data: Dictionary to print as JSON
        title: Optional title
    """
    import json
    json_str = json.dumps(data, indent=2, ensure_ascii=False)
    syntax = Syntax(json_str, "json", theme="monokai", line_numbers=False)

    if title:
        console.print(f"[bold]{title}[/bold]")
    console.print(syntax)


def print_yaml(data: str, title: Optional[str] = None) -> None:
    """
    Print YAML data with syntax highlighting.

    Args:
        data: YAML string
        title: Optional title
    """
    syntax = Syntax(data, "yaml", theme="monokai", line_numbers=False)

    if title:
        console.print(f"[bold]{title}[/bold]")
    console.print(syntax)


# Convenience exports
__all__ = [
    "console",
    "logger",
    "COWLogger",
    "ErrorCode",
    "setup_logging",
    "log_error",
    "log_success",
    "log_warning",
    "log_info",
    "create_progress",
    "print_table",
    "print_panel",
    "print_json",
    "print_yaml",
]
