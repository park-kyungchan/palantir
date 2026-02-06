"""
COW CLI - Interactive Review TUI

Terminal User Interface for fast batch review workflow.
"""
from typing import Optional, List
from dataclasses import dataclass, field
from datetime import datetime, timezone
import sys
import json

from rich.console import Console
from rich.layout import Layout
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich.live import Live
from rich import box

from cow_cli.review import (
    ReviewDatabase,
    ReviewItem,
    ReviewStatus,
    ReviewDecision,
    get_database,
)

console = Console()


@dataclass
class ReviewSession:
    """Tracks review session statistics."""
    start_time: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    items_reviewed: int = 0
    approved: int = 0
    rejected: int = 0
    modified: int = 0
    skipped: int = 0
    reviewer: str = "tui-user"

    @property
    def elapsed_seconds(self) -> float:
        """Get elapsed time in seconds."""
        return (datetime.now(timezone.utc) - self.start_time).total_seconds()

    @property
    def avg_time_per_item(self) -> float:
        """Get average time per item in seconds."""
        if self.items_reviewed == 0:
            return 0.0
        return self.elapsed_seconds / self.items_reviewed

    @property
    def approval_rate(self) -> float:
        """Get approval rate."""
        if self.items_reviewed == 0:
            return 0.0
        return self.approved / self.items_reviewed

    def to_table(self) -> Table:
        """Create stats table."""
        table = Table(box=box.SIMPLE, show_header=False)
        table.add_column("Metric", style="bold")
        table.add_column("Value", justify="right")

        elapsed_min = self.elapsed_seconds / 60
        table.add_row("Session Time", f"{elapsed_min:.1f} min")
        table.add_row("Items Reviewed", str(self.items_reviewed))
        table.add_row("Approved", f"[green]{self.approved}[/green]")
        table.add_row("Rejected", f"[red]{self.rejected}[/red]")
        table.add_row("Modified", f"[cyan]{self.modified}[/cyan]")
        table.add_row("Skipped", f"[dim]{self.skipped}[/dim]")
        table.add_row("Approval Rate", f"{self.approval_rate:.0%}")
        table.add_row("Avg Time/Item", f"{self.avg_time_per_item:.1f}s")

        return table


class InteractiveReviewer:
    """
    Interactive TUI for batch review.

    Provides keyboard-driven review workflow with real-time statistics.
    """

    HELP_TEXT = """
[bold]Keyboard Shortcuts:[/bold]
  [green]A[/green] - Approve    [red]R[/red] - Reject
  [cyan]M[/cyan] - Modify     [dim]S[/dim] - Skip
  [yellow]N[/yellow] - Next       [yellow]P[/yellow] - Previous
  [bold]Q[/bold] - Quit
"""

    def __init__(
        self,
        db: Optional[ReviewDatabase] = None,
        reviewer: str = "tui-user",
        element_type: Optional[str] = None,
    ):
        """
        Initialize interactive reviewer.

        Args:
            db: Database instance
            reviewer: Reviewer name
            element_type: Filter by element type
        """
        self.db = db or get_database()
        self.reviewer = reviewer
        self.element_type = element_type
        self.session = ReviewSession(reviewer=reviewer)

        self.items: List[ReviewItem] = []
        self.current_index: int = 0
        self.running: bool = True
        self.message: str = ""
        self.modify_field: str = ""
        self.modify_value: str = ""

    def load_items(self, limit: int = 100) -> None:
        """Load pending items for review."""
        self.items = self.db.list_review_items(
            status=ReviewStatus.PENDING.value,
            element_type=self.element_type,
            limit=limit,
        )
        self.current_index = 0

    @property
    def current_item(self) -> Optional[ReviewItem]:
        """Get current item."""
        if not self.items or self.current_index >= len(self.items):
            return None
        return self.items[self.current_index]

    @property
    def items_remaining(self) -> int:
        """Get count of remaining items."""
        return max(0, len(self.items) - self.current_index)

    def make_layout(self) -> Layout:
        """Create the TUI layout."""
        layout = Layout()

        # Main split: content left, sidebar right
        layout.split_row(
            Layout(name="main", ratio=3),
            Layout(name="sidebar", ratio=1),
        )

        # Main area: item details top, help bottom
        layout["main"].split_column(
            Layout(name="item", ratio=4),
            Layout(name="message", ratio=1),
        )

        # Sidebar: stats top, help bottom
        layout["sidebar"].split_column(
            Layout(name="stats", ratio=2),
            Layout(name="help", ratio=1),
        )

        # Fill panels
        layout["item"].update(self._render_item_panel())
        layout["message"].update(self._render_message_panel())
        layout["stats"].update(self._render_stats_panel())
        layout["help"].update(self._render_help_panel())

        return layout

    def _render_item_panel(self) -> Panel:
        """Render current item panel."""
        item = self.current_item

        if not item:
            return Panel(
                "[yellow]No items to review.[/yellow]\n\n"
                "All pending items have been processed.\n"
                "Press [bold]Q[/bold] to quit.",
                title="Review Complete",
                border_style="green",
            )

        content = Text()

        # Header info
        content.append(f"Item: ", style="bold")
        content.append(f"{item.id}\n")
        content.append(f"Type: ", style="bold")
        content.append(f"{item.element_type}\n")
        content.append(f"Confidence: ", style="bold")
        if item.confidence:
            conf_style = "green" if item.confidence >= 0.9 else "yellow" if item.confidence >= 0.75 else "red"
            content.append(f"{item.confidence:.1%}\n", style=conf_style)
        else:
            content.append("N/A\n")
        content.append(f"Priority: ", style="bold")
        content.append(f"{item.priority:.1f}\n")

        content.append("\n")

        # Image path
        content.append("Image: ", style="bold cyan")
        content.append(f"{item.image_path}\n")

        # Element ID
        content.append("Element: ", style="bold cyan")
        content.append(f"{item.element_id}\n")

        # Reason
        if item.reason:
            content.append("\nReason: ", style="bold yellow")
            content.append(f"{item.reason}\n")

        # Element data
        if item.element_data:
            content.append("\n")
            content.append("Element Data:\n", style="bold")
            try:
                data = json.loads(item.element_data)
                for key, value in data.items():
                    content.append(f"  {key}: ", style="dim")
                    content.append(f"{value}\n")
            except (json.JSONDecodeError, TypeError):
                content.append(f"  {item.element_data}\n", style="dim")

        progress = f"[{self.current_index + 1}/{len(self.items)}]"
        title = f"Review Item {progress}"

        return Panel(
            content,
            title=title,
            subtitle=f"Remaining: {self.items_remaining}",
            border_style="cyan",
        )

    def _render_message_panel(self) -> Panel:
        """Render message panel."""
        if self.message:
            return Panel(
                self.message,
                title="Status",
                border_style="yellow",
            )
        return Panel(
            "[dim]Ready for input...[/dim]",
            title="Status",
            border_style="dim",
        )

    def _render_stats_panel(self) -> Panel:
        """Render session stats panel."""
        return Panel(
            self.session.to_table(),
            title=f"Session: {self.reviewer}",
            border_style="blue",
        )

    def _render_help_panel(self) -> Panel:
        """Render help panel."""
        return Panel(
            self.HELP_TEXT,
            title="Help",
            border_style="dim",
        )

    def handle_key(self, key: str) -> bool:
        """
        Handle keyboard input.

        Args:
            key: Key pressed

        Returns:
            True if should continue, False to quit
        """
        key = key.lower()

        if key == 'q':
            self.running = False
            return False

        if not self.current_item:
            return True

        item = self.current_item

        if key == 'a':
            self._approve(item)
        elif key == 'r':
            self._reject(item)
        elif key == 'm':
            self._modify(item)
        elif key == 's':
            self._skip(item)
        elif key == 'n':
            self._next()
        elif key == 'p':
            self._previous()

        return True

    def _approve(self, item: ReviewItem) -> None:
        """Approve current item."""
        self.db.submit_review(
            item_id=item.id,
            decision=ReviewDecision.APPROVED.value,
            reviewer=self.reviewer,
        )
        self.session.items_reviewed += 1
        self.session.approved += 1
        self.message = f"[green]Approved:[/green] {item.id}"
        self._remove_current()

    def _reject(self, item: ReviewItem) -> None:
        """Reject current item."""
        self.db.submit_review(
            item_id=item.id,
            decision=ReviewDecision.REJECTED.value,
            reviewer=self.reviewer,
            comment="Rejected via TUI",
        )
        self.session.items_reviewed += 1
        self.session.rejected += 1
        self.message = f"[red]Rejected:[/red] {item.id}"
        self._remove_current()

    def _modify(self, item: ReviewItem) -> None:
        """Mark item as modified (placeholder)."""
        self.db.submit_review(
            item_id=item.id,
            decision=ReviewDecision.MODIFIED.value,
            reviewer=self.reviewer,
            comment="Modified via TUI",
        )
        self.session.items_reviewed += 1
        self.session.modified += 1
        self.message = f"[cyan]Modified:[/cyan] {item.id} (use CLI for detailed edits)"
        self._remove_current()

    def _skip(self, item: ReviewItem) -> None:
        """Skip current item."""
        self.db.submit_review(
            item_id=item.id,
            decision=ReviewDecision.SKIPPED.value,
            reviewer=self.reviewer,
        )
        self.session.items_reviewed += 1
        self.session.skipped += 1
        self.message = f"[dim]Skipped:[/dim] {item.id}"
        self._remove_current()

    def _next(self) -> None:
        """Move to next item."""
        if self.current_index < len(self.items) - 1:
            self.current_index += 1
            self.message = ""

    def _previous(self) -> None:
        """Move to previous item."""
        if self.current_index > 0:
            self.current_index -= 1
            self.message = ""

    def _remove_current(self) -> None:
        """Remove current item from list."""
        if self.items and self.current_index < len(self.items):
            self.items.pop(self.current_index)
            # Adjust index if needed
            if self.current_index >= len(self.items) and self.current_index > 0:
                self.current_index = len(self.items) - 1

    def run(self) -> ReviewSession:
        """
        Run interactive review session.

        Returns:
            Session statistics
        """
        self.load_items()

        if not self.items:
            console.print("[yellow]No pending items to review.[/yellow]")
            return self.session

        console.print("[bold]Starting interactive review...[/bold]")
        console.print("[dim]Press any key to continue, Q to quit[/dim]\n")

        try:
            with Live(self.make_layout(), refresh_per_second=4, screen=True) as live:
                while self.running and self.items:
                    live.update(self.make_layout())

                    # Simple key input (blocking)
                    key = self._get_key()
                    if not self.handle_key(key):
                        break

        except KeyboardInterrupt:
            pass

        return self.session

    def _get_key(self) -> str:
        """Get single keypress."""
        try:
            import termios
            import tty

            fd = sys.stdin.fileno()
            old_settings = termios.tcgetattr(fd)
            try:
                tty.setraw(fd)
                ch = sys.stdin.read(1)
            finally:
                termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
            return ch
        except (ImportError, termios.error):
            # Fallback for non-Unix systems
            return input("Action (A/R/M/S/N/P/Q): ").strip()


def run_interactive_review(
    reviewer: str = "tui-user",
    element_type: Optional[str] = None,
    db_path: Optional[str] = None,
) -> ReviewSession:
    """
    Run interactive review session.

    Args:
        reviewer: Reviewer name
        element_type: Filter by element type
        db_path: Optional database path

    Returns:
        Session statistics
    """
    reviewer_tui = InteractiveReviewer(
        reviewer=reviewer,
        element_type=element_type,
    )
    return reviewer_tui.run()


__all__ = [
    "ReviewSession",
    "InteractiveReviewer",
    "run_interactive_review",
]
