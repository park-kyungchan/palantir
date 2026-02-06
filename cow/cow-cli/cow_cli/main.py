"""
COW CLI - Layout/Content Separation Pipeline with Claude Agent SDK

Main entry point for the CLI application.
"""
import typer
from rich.console import Console

# Version info
__version__ = "0.1.0"

# Initialize Typer app
app = typer.Typer(
    name="cow",
    help="COW Pipeline CLI - Layout/Content Separation with Claude Agent SDK",
    add_completion=True,
    rich_markup_mode="rich",
)

# Console for rich output
console = Console()


def version_callback(value: bool) -> None:
    """Show version and exit."""
    if value:
        console.print(f"[bold blue]COW CLI[/bold blue] version {__version__}")
        raise typer.Exit()


@app.callback()
def main(
    version: bool = typer.Option(
        None,
        "--version",
        "-v",
        callback=version_callback,
        is_eager=True,
        help="Show version and exit.",
    ),
) -> None:
    """
    COW Pipeline CLI - Layout/Content Separation with Claude Agent SDK.

    Process math/science images through Mathpix OCR, separate layout and content,
    and enable human-in-the-loop review workflow.
    """
    pass


@app.command()
def process(
    image_path: str = typer.Argument(..., help="Path to image file to process"),
    output_dir: str = typer.Option("./output", "-o", "--output", help="Output directory"),
    skip_review: bool = typer.Option(False, "--skip-review", help="Skip HITL review queue"),
) -> None:
    """Process an image through the COW pipeline."""
    console.print(f"[green]Processing:[/green] {image_path}")
    console.print(f"[blue]Output directory:[/blue] {output_dir}")
    console.print("[yellow]Status:[/yellow] Not yet implemented - Phase 7")


@app.command()
def review(
    action: str = typer.Argument("list", help="Review action: list, approve, reject, skip"),
    item_id: str = typer.Option(None, "-i", "--id", help="Review item ID"),
) -> None:
    """Human-in-the-loop review commands."""
    console.print(f"[green]Review action:[/green] {action}")
    if item_id:
        console.print(f"[blue]Item ID:[/blue] {item_id}")
    console.print("[yellow]Status:[/yellow] Not yet implemented - Phase 5")


@app.command()
def export(
    item_id: str = typer.Argument(..., help="Item ID to export"),
    format: str = typer.Option("docx", "-f", "--format", help="Export format: docx, latex, pdf"),
) -> None:
    """Export processed content to various formats."""
    console.print(f"[green]Exporting:[/green] {item_id}")
    console.print(f"[blue]Format:[/blue] {format}")
    console.print("[yellow]Status:[/yellow] Not yet implemented - Phase 6")


@app.command()
def config(
    action: str = typer.Argument("show", help="Config action: show, set, get"),
    key: str = typer.Option(None, "-k", "--key", help="Configuration key"),
    value: str = typer.Option(None, "-v", "--value", help="Configuration value"),
) -> None:
    """Manage COW CLI configuration."""
    console.print(f"[green]Config action:[/green] {action}")
    if key:
        console.print(f"[blue]Key:[/blue] {key}")
    if value:
        console.print(f"[blue]Value:[/blue] {value}")
    console.print("[yellow]Status:[/yellow] Not yet implemented - Phase 1")


if __name__ == "__main__":
    app()
