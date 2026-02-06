"""
COW CLI - Review Commands

CLI commands for the Human-in-the-Loop review workflow.
"""
from typing import Optional
from pathlib import Path
import json
import typer
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text
from rich import box

from cow_cli.review import (
    ReviewDatabase,
    ReviewStatus,
    ReviewDecision,
    RoutingDecision,
    ReviewRouter,
    PriorityScorer,
    get_database,
    configure_database,
)

# Create Typer app for review commands
app = typer.Typer(
    name="review",
    help="Human-in-the-Loop review commands",
    no_args_is_help=True,
)

console = Console()


def get_db() -> ReviewDatabase:
    """Get or create database instance."""
    return get_database()


@app.command("list")
def list_items(
    status: Optional[str] = typer.Option(
        None,
        "--status", "-s",
        help="Filter by status (pending, claimed, approved, rejected, modified)",
    ),
    element_type: Optional[str] = typer.Option(
        None,
        "--type", "-t",
        help="Filter by element type (math, text, diagram, etc.)",
    ),
    confidence_below: Optional[float] = typer.Option(
        None,
        "--confidence-below", "-c",
        help="Filter items below confidence threshold",
    ),
    limit: int = typer.Option(
        20,
        "--limit", "-n",
        help="Maximum items to show",
    ),
    reviewer: Optional[str] = typer.Option(
        None,
        "--reviewer", "-r",
        help="Filter by reviewer",
    ),
    json_output: bool = typer.Option(
        False,
        "--json",
        help="Output as JSON",
    ),
) -> None:
    """List review items with optional filters."""
    db = get_db()

    # Get items
    items = db.list_review_items(
        status=status,
        element_type=element_type,
        reviewer=reviewer,
        limit=limit,
    )

    # Filter by confidence if specified
    if confidence_below is not None:
        items = [
            item for item in items
            if item.confidence is not None and item.confidence < confidence_below
        ]

    if json_output:
        output = [item.to_dict() for item in items]
        console.print_json(data=output)
        return

    if not items:
        console.print("[yellow]No review items found.[/yellow]")
        return

    # Create table
    table = Table(
        title="Review Items",
        box=box.ROUNDED,
        show_header=True,
        header_style="bold cyan",
    )
    table.add_column("ID", style="dim", width=10)
    table.add_column("Type", width=12)
    table.add_column("Confidence", justify="right", width=12)
    table.add_column("Status", width=12)
    table.add_column("Priority", justify="right", width=10)
    table.add_column("Reviewer", width=12)

    for item in items:
        conf_str = f"{item.confidence:.1%}" if item.confidence else "N/A"
        status_style = _get_status_style(item.status)
        priority_str = f"{item.priority:.1f}" if item.priority else "0.0"

        table.add_row(
            item.id,
            item.element_type,
            conf_str,
            f"[{status_style}]{item.status}[/{status_style}]",
            priority_str,
            item.reviewer or "-",
        )

    console.print(table)
    console.print(f"\n[dim]Total: {len(items)} items[/dim]")


@app.command("show")
def show_item(
    item_id: str = typer.Argument(..., help="Review item ID"),
    json_output: bool = typer.Option(
        False,
        "--json",
        help="Output as JSON",
    ),
) -> None:
    """Show detailed information about a review item."""
    db = get_db()
    item = db.get_review_item(item_id)

    if not item:
        console.print(f"[red]Error: Item '{item_id}' not found.[/red]")
        raise typer.Exit(1)

    if json_output:
        console.print_json(data=item.to_dict())
        return

    # Create detailed view
    status_style = _get_status_style(item.status)

    panel_content = Text()
    panel_content.append("ID: ", style="bold")
    panel_content.append(f"{item.id}\n")
    panel_content.append("Status: ", style="bold")
    panel_content.append(f"{item.status}\n", style=status_style)
    panel_content.append("Element Type: ", style="bold")
    panel_content.append(f"{item.element_type}\n")
    panel_content.append("Confidence: ", style="bold")
    panel_content.append(f"{item.confidence:.2%}\n" if item.confidence else "N/A\n")
    panel_content.append("Priority: ", style="bold")
    panel_content.append(f"{item.priority:.1f}\n" if item.priority else "0.0\n")
    panel_content.append("\nImage Path: ", style="bold")
    panel_content.append(f"{item.image_path}\n")
    panel_content.append("Element ID: ", style="bold")
    panel_content.append(f"{item.element_id}\n")

    if item.reason:
        panel_content.append("\nReason: ", style="bold")
        panel_content.append(f"{item.reason}\n")

    if item.reviewer:
        panel_content.append("\nReviewer: ", style="bold")
        panel_content.append(f"{item.reviewer}\n")

    if item.decision:
        panel_content.append("Decision: ", style="bold")
        panel_content.append(f"{item.decision}\n")

    if item.comment:
        panel_content.append("Comment: ", style="bold")
        panel_content.append(f"{item.comment}\n")

    if item.modifications:
        panel_content.append("\nModifications: ", style="bold")
        panel_content.append(f"{item.modifications}\n")

    panel_content.append("\nCreated: ", style="bold dim")
    panel_content.append(f"{item.created_at.isoformat() if item.created_at else 'N/A'}\n")

    if item.claimed_at:
        panel_content.append("Claimed: ", style="bold dim")
        panel_content.append(f"{item.claimed_at.isoformat()}\n")

    if item.reviewed_at:
        panel_content.append("Reviewed: ", style="bold dim")
        panel_content.append(f"{item.reviewed_at.isoformat()}\n")

    console.print(Panel(
        panel_content,
        title=f"Review Item: {item_id}",
        border_style="cyan",
    ))

    # Show element data if available
    if item.element_data:
        try:
            data = json.loads(item.element_data)
            console.print("\n[bold]Element Data:[/bold]")
            console.print_json(data=data)
        except json.JSONDecodeError:
            console.print(f"\n[bold]Element Data:[/bold] {item.element_data}")


@app.command("approve")
def approve_item(
    item_id: str = typer.Argument(..., help="Review item ID"),
    comment: Optional[str] = typer.Option(
        None,
        "--comment", "-c",
        help="Optional approval comment",
    ),
    reviewer: str = typer.Option(
        "cli-user",
        "--reviewer", "-r",
        help="Reviewer name",
    ),
) -> None:
    """Approve a review item."""
    db = get_db()

    item = db.submit_review(
        item_id=item_id,
        decision=ReviewDecision.APPROVED.value,
        reviewer=reviewer,
        comment=comment,
    )

    if not item:
        console.print(f"[red]Error: Item '{item_id}' not found.[/red]")
        raise typer.Exit(1)

    console.print(f"[green]Item '{item_id}' approved successfully.[/green]")
    if comment:
        console.print(f"[dim]Comment: {comment}[/dim]")


@app.command("reject")
def reject_item(
    item_id: str = typer.Argument(..., help="Review item ID"),
    reason: str = typer.Option(
        ...,
        "--reason", "-r",
        help="Rejection reason (required)",
    ),
    reviewer: str = typer.Option(
        "cli-user",
        "--reviewer",
        help="Reviewer name",
    ),
) -> None:
    """Reject a review item."""
    db = get_db()

    item = db.submit_review(
        item_id=item_id,
        decision=ReviewDecision.REJECTED.value,
        reviewer=reviewer,
        comment=reason,
    )

    if not item:
        console.print(f"[red]Error: Item '{item_id}' not found.[/red]")
        raise typer.Exit(1)

    console.print(f"[yellow]Item '{item_id}' rejected.[/yellow]")
    console.print(f"[dim]Reason: {reason}[/dim]")


@app.command("modify")
def modify_item(
    item_id: str = typer.Argument(..., help="Review item ID"),
    field: str = typer.Option(
        ...,
        "--field", "-f",
        help="Field to modify (e.g., latex_content, text)",
    ),
    value: str = typer.Option(
        ...,
        "--value", "-v",
        help="New value for the field",
    ),
    comment: Optional[str] = typer.Option(
        None,
        "--comment", "-c",
        help="Modification comment",
    ),
    reviewer: str = typer.Option(
        "cli-user",
        "--reviewer", "-r",
        help="Reviewer name",
    ),
) -> None:
    """Modify a review item with corrections."""
    db = get_db()

    modifications = {field: value}

    item = db.submit_review(
        item_id=item_id,
        decision=ReviewDecision.MODIFIED.value,
        reviewer=reviewer,
        modifications=modifications,
        comment=comment,
    )

    if not item:
        console.print(f"[red]Error: Item '{item_id}' not found.[/red]")
        raise typer.Exit(1)

    console.print(f"[blue]Item '{item_id}' modified successfully.[/blue]")
    console.print(f"[dim]Modified field: {field}[/dim]")


@app.command("skip")
def skip_item(
    item_id: str = typer.Argument(..., help="Review item ID"),
    reason: Optional[str] = typer.Option(
        None,
        "--reason", "-r",
        help="Reason for skipping",
    ),
    reviewer: str = typer.Option(
        "cli-user",
        "--reviewer",
        help="Reviewer name",
    ),
) -> None:
    """Skip a review item for later."""
    db = get_db()

    item = db.submit_review(
        item_id=item_id,
        decision=ReviewDecision.SKIPPED.value,
        reviewer=reviewer,
        comment=reason,
    )

    if not item:
        console.print(f"[red]Error: Item '{item_id}' not found.[/red]")
        raise typer.Exit(1)

    console.print(f"[dim]Item '{item_id}' skipped.[/dim]")


@app.command("claim")
def claim_item(
    item_id: str = typer.Argument(..., help="Review item ID"),
    reviewer: str = typer.Option(
        "cli-user",
        "--reviewer", "-r",
        help="Reviewer name",
    ),
) -> None:
    """Claim a pending item for review."""
    db = get_db()

    item = db.claim_item(item_id, reviewer)

    if not item:
        console.print(f"[red]Error: Item '{item_id}' not found or already claimed.[/red]")
        raise typer.Exit(1)

    console.print(f"[green]Item '{item_id}' claimed by '{reviewer}'.[/green]")


@app.command("release")
def release_item(
    item_id: str = typer.Argument(..., help="Review item ID"),
) -> None:
    """Release a claimed item back to pending."""
    db = get_db()

    item = db.release_item(item_id)

    if not item:
        console.print(f"[red]Error: Item '{item_id}' not found or not claimed.[/red]")
        raise typer.Exit(1)

    console.print(f"[yellow]Item '{item_id}' released back to pending.[/yellow]")


@app.command("stats")
def show_stats(
    json_output: bool = typer.Option(
        False,
        "--json",
        help="Output as JSON",
    ),
) -> None:
    """Show review queue statistics."""
    db = get_db()

    queue_stats = db.get_queue_stats()
    reviewer_stats = db.get_all_reviewer_stats()

    if json_output:
        output = {
            "queue": queue_stats,
            "reviewers": [s.to_dict() for s in reviewer_stats],
        }
        console.print_json(data=output)
        return

    # Queue stats table
    queue_table = Table(
        title="Queue Statistics",
        box=box.ROUNDED,
        show_header=True,
        header_style="bold cyan",
    )
    queue_table.add_column("Metric", style="bold")
    queue_table.add_column("Value", justify="right")

    queue_table.add_row("Total Items", str(queue_stats["total"]))
    queue_table.add_row("Pending", f"[yellow]{queue_stats['pending']}[/yellow]")
    queue_table.add_row("Claimed", f"[blue]{queue_stats['claimed']}[/blue]")
    queue_table.add_row("Reviewed", f"[green]{queue_stats['reviewed']}[/green]")
    queue_table.add_row("  - Approved", str(queue_stats["approved"]))
    queue_table.add_row("  - Rejected", str(queue_stats["rejected"]))
    queue_table.add_row("  - Modified", str(queue_stats["modified"]))

    if queue_stats["avg_pending_confidence"]:
        queue_table.add_row(
            "Avg Pending Confidence",
            f"{queue_stats['avg_pending_confidence']:.1%}"
        )

    console.print(queue_table)

    # Reviewer stats
    if reviewer_stats:
        console.print()
        reviewer_table = Table(
            title="Reviewer Statistics",
            box=box.ROUNDED,
            show_header=True,
            header_style="bold cyan",
        )
        reviewer_table.add_column("Reviewer")
        reviewer_table.add_column("Total", justify="right")
        reviewer_table.add_column("Approved", justify="right")
        reviewer_table.add_column("Rejected", justify="right")
        reviewer_table.add_column("Modified", justify="right")
        reviewer_table.add_column("Approval Rate", justify="right")
        reviewer_table.add_column("Avg Time (s)", justify="right")

        for stats in reviewer_stats:
            avg_time = f"{stats.avg_review_time_sec:.1f}" if stats.avg_review_time_sec else "-"
            approval_rate = f"{stats.approval_rate:.0%}"

            reviewer_table.add_row(
                stats.reviewer,
                str(stats.total_reviews),
                str(stats.approved),
                str(stats.rejected),
                str(stats.modified),
                approval_rate,
                avg_time,
            )

        console.print(reviewer_table)


@app.command("add")
def add_item(
    image_path: str = typer.Argument(..., help="Path to source image"),
    element_id: str = typer.Option(
        ...,
        "--element-id", "-e",
        help="Element identifier",
    ),
    element_type: str = typer.Option(
        "text",
        "--type", "-t",
        help="Element type (math, text, diagram, etc.)",
    ),
    confidence: Optional[float] = typer.Option(
        None,
        "--confidence", "-c",
        help="Confidence score (0-1)",
    ),
    reason: Optional[str] = typer.Option(
        None,
        "--reason", "-r",
        help="Reason for review",
    ),
    priority: float = typer.Option(
        0.0,
        "--priority", "-p",
        help="Priority score",
    ),
) -> None:
    """Add a new item to the review queue."""
    db = get_db()

    item = db.add_review_item(
        image_path=image_path,
        element_id=element_id,
        element_type=element_type,
        confidence=confidence,
        reason=reason,
        priority=priority,
    )

    console.print(f"[green]Added review item: {item.id}[/green]")
    console.print(f"[dim]Image: {image_path}[/dim]")
    console.print(f"[dim]Type: {element_type}, Priority: {priority}[/dim]")


@app.command("delete")
def delete_item(
    item_id: str = typer.Argument(..., help="Review item ID"),
    force: bool = typer.Option(
        False,
        "--force", "-f",
        help="Skip confirmation",
    ),
) -> None:
    """Delete a review item."""
    db = get_db()

    if not force:
        confirm = typer.confirm(f"Delete item '{item_id}'?")
        if not confirm:
            console.print("[yellow]Cancelled.[/yellow]")
            raise typer.Exit(0)

    if db.delete_item(item_id):
        console.print(f"[green]Deleted item: {item_id}[/green]")
    else:
        console.print(f"[red]Error: Item '{item_id}' not found.[/red]")
        raise typer.Exit(1)


@app.command("expire")
def expire_stale(
    max_age: int = typer.Option(
        60,
        "--max-age", "-a",
        help="Maximum claim age in minutes",
    ),
) -> None:
    """Release stale claimed items."""
    db = get_db()

    count = db.expire_stale_claims(max_age_minutes=max_age)

    if count > 0:
        console.print(f"[yellow]Released {count} stale claims.[/yellow]")
    else:
        console.print("[dim]No stale claims found.[/dim]")


def _get_status_style(status: str) -> str:
    """Get Rich style for status."""
    styles = {
        ReviewStatus.PENDING.value: "yellow",
        ReviewStatus.CLAIMED.value: "blue",
        ReviewStatus.APPROVED.value: "green",
        ReviewStatus.REJECTED.value: "red",
        ReviewStatus.MODIFIED.value: "cyan",
        ReviewStatus.SKIPPED.value: "dim",
    }
    return styles.get(status, "white")


@app.command("interactive")
def interactive_review(
    reviewer: str = typer.Option(
        "tui-user",
        "--reviewer", "-r",
        help="Reviewer name",
    ),
    element_type: Optional[str] = typer.Option(
        None,
        "--type", "-t",
        help="Filter by element type",
    ),
) -> None:
    """Launch interactive TUI for batch review."""
    from cow_cli.commands.review_interactive import InteractiveReviewer

    tui = InteractiveReviewer(
        reviewer=reviewer,
        element_type=element_type,
    )
    session = tui.run()

    # Print session summary
    console.print("\n[bold]Session Summary:[/bold]")
    console.print(f"  Items reviewed: {session.items_reviewed}")
    console.print(f"  Approved: [green]{session.approved}[/green]")
    console.print(f"  Rejected: [red]{session.rejected}[/red]")
    console.print(f"  Modified: [cyan]{session.modified}[/cyan]")
    console.print(f"  Skipped: [dim]{session.skipped}[/dim]")
    console.print(f"  Time: {session.elapsed_seconds / 60:.1f} minutes")


if __name__ == "__main__":
    app()
