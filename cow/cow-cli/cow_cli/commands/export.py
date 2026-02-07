"""
COW CLI - Export Commands

CLI commands for exporting documents to various formats.
"""
from typing import Optional
from pathlib import Path
import json

import typer
from rich.console import Console

from cow_cli.export import (
    ExportFormat,
    ExportOptions,
    ExportResult,
    get_exporter,
    JSONExporter,
    MarkdownExporter,
    MarkdownFlavor,
    LaTeXExporter,
    DocumentClass,
    DocxExporter,
    DOCX_AVAILABLE,
)
from cow_cli.semantic.schemas import SeparatedDocument


console = Console()
app = typer.Typer(name="export", help="Export documents to various formats")


def _load_document(input_path: Path) -> Optional[SeparatedDocument]:
    """Load a SeparatedDocument from JSON file."""
    try:
        if not input_path.exists():
            console.print(f"[red]Error:[/red] File not found: {input_path}")
            return None

        with open(input_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        # Handle different JSON structures
        if "layout" in data and "content" in data:
            # Full separated document format
            return SeparatedDocument(**data)
        elif "image_path" in data:
            # Minimal format
            return SeparatedDocument(**data)
        else:
            # Try to construct from raw data
            return SeparatedDocument(
                image_path=str(input_path),
                **data,
            )

    except json.JSONDecodeError as e:
        console.print(f"[red]Error:[/red] Invalid JSON: {e}")
        return None
    except Exception as e:
        console.print(f"[red]Error:[/red] Failed to load document: {e}")
        return None


def _handle_result(result: ExportResult) -> None:
    """Handle export result and display status."""
    if result.success:
        console.print(f"[green]✓[/green] Exported to: {result.output_path}")
        console.print(f"  Format: {result.format.value if result.format else 'unknown'}")
        console.print(f"  Size: {result.bytes_written:,} bytes")

        if result.warnings:
            console.print("[yellow]Warnings:[/yellow]")
            for warning in result.warnings:
                console.print(f"  • {warning}")
    else:
        console.print(f"[red]✗[/red] Export failed: {result.error}")
        raise typer.Exit(1)


@app.command("json")
def export_json(
    input_path: Path = typer.Argument(..., help="Input JSON file path"),
    output: Optional[Path] = typer.Option(
        None, "-o", "--output", help="Output file path"
    ),
    indent: int = typer.Option(2, "--indent", help="JSON indentation"),
    compact: bool = typer.Option(False, "--compact", help="Compact output (no indentation)"),
    include: Optional[str] = typer.Option(
        None, "--include", help="Comma-separated fields to include"
    ),
    exclude: Optional[str] = typer.Option(
        None, "--exclude", help="Comma-separated fields to exclude"
    ),
    with_quality: bool = typer.Option(
        False, "--with-quality", help="Include quality metrics"
    ),
) -> None:
    """Export to JSON format."""
    document = _load_document(input_path)
    if not document:
        raise typer.Exit(1)

    # Determine output path
    if output is None:
        output = input_path.with_suffix(".exported.json")

    # Parse include/exclude
    include_fields = include.split(",") if include else None
    exclude_fields = exclude.split(",") if exclude else None

    # Create exporter
    options = ExportOptions(include_quality_metrics=with_quality)
    exporter = JSONExporter(
        options=options,
        indent=None if compact else indent,
        include_fields=include_fields,
        exclude_fields=exclude_fields,
    )

    # Export
    result = exporter.export(document, output)
    _handle_result(result)


@app.command("markdown")
def export_markdown(
    input_path: Path = typer.Argument(..., help="Input JSON file path"),
    output: Optional[Path] = typer.Option(
        None, "-o", "--output", help="Output file path"
    ),
    flavor: str = typer.Option(
        "gfm", "--flavor", "-f",
        help="Markdown flavor: standard, gfm, mmd"
    ),
    no_frontmatter: bool = typer.Option(
        False, "--no-frontmatter", help="Omit YAML frontmatter"
    ),
    with_toc: bool = typer.Option(
        False, "--with-toc", help="Include table of contents"
    ),
    with_quality: bool = typer.Option(
        False, "--with-quality", help="Include quality metrics"
    ),
) -> None:
    """Export to Markdown format."""
    document = _load_document(input_path)
    if not document:
        raise typer.Exit(1)

    # Determine output path
    if output is None:
        output = input_path.with_suffix(".md")

    # Parse flavor
    try:
        md_flavor = MarkdownFlavor(flavor.lower())
    except ValueError:
        console.print(f"[red]Error:[/red] Invalid flavor: {flavor}")
        console.print("Valid options: standard, gfm, mmd")
        raise typer.Exit(1)

    # Create exporter
    options = ExportOptions(include_quality_metrics=with_quality)
    exporter = MarkdownExporter(
        options=options,
        flavor=md_flavor,
        include_frontmatter=not no_frontmatter,
        include_toc=with_toc,
    )

    # Export
    result = exporter.export(document, output)
    _handle_result(result)


@app.command("latex")
def export_latex(
    input_path: Path = typer.Argument(..., help="Input JSON file path"),
    output: Optional[Path] = typer.Option(
        None, "-o", "--output", help="Output file path"
    ),
    document_class: str = typer.Option(
        "article", "-d", "--document-class",
        help="LaTeX document class: article, report, book, standalone"
    ),
    class_options: str = typer.Option(
        "12pt,a4paper", "--class-options",
        help="Document class options"
    ),
    with_images: bool = typer.Option(
        False, "--with-images", help="Include image references"
    ),
    standalone: bool = typer.Option(
        False, "--standalone", help="Minimal standalone document"
    ),
) -> None:
    """Export to LaTeX format."""
    document = _load_document(input_path)
    if not document:
        raise typer.Exit(1)

    # Determine output path
    if output is None:
        output = input_path.with_suffix(".tex")

    # Parse document class
    try:
        doc_class = DocumentClass(document_class.lower())
    except ValueError:
        console.print(f"[red]Error:[/red] Invalid document class: {document_class}")
        console.print("Valid options: article, report, book, standalone")
        raise typer.Exit(1)

    # Create exporter
    exporter = LaTeXExporter(
        document_class=doc_class,
        class_options=class_options,
        include_images=with_images,
        standalone=standalone,
    )

    # Export
    result = exporter.export(document, output)
    _handle_result(result)


@app.command("docx")
def export_docx(
    input_path: Path = typer.Argument(..., help="Input JSON file path"),
    output: Optional[Path] = typer.Option(
        None, "-o", "--output", help="Output file path"
    ),
    template: Optional[Path] = typer.Option(
        None, "-t", "--template", help="DOCX template file"
    ),
    with_toc: bool = typer.Option(
        False, "--with-toc", help="Include table of contents placeholder"
    ),
    math_as_image: bool = typer.Option(
        False, "--math-as-image", help="Render math as image placeholders"
    ),
    with_quality: bool = typer.Option(
        False, "--with-quality", help="Include quality metrics"
    ),
) -> None:
    """Export to Microsoft Word (DOCX) format."""
    if not DOCX_AVAILABLE:
        console.print("[red]Error:[/red] python-docx not installed")
        console.print("Install with: pip install python-docx")
        raise typer.Exit(1)

    document = _load_document(input_path)
    if not document:
        raise typer.Exit(1)

    # Determine output path
    if output is None:
        output = input_path.with_suffix(".docx")

    # Validate template
    if template and not template.exists():
        console.print(f"[red]Error:[/red] Template not found: {template}")
        raise typer.Exit(1)

    # Create exporter
    options = ExportOptions(include_quality_metrics=with_quality)
    exporter = DocxExporter(
        options=options,
        template_path=template,
        include_toc=with_toc,
        math_as_image=math_as_image,
    )

    # Export
    result = exporter.export(document, output)
    _handle_result(result)


@app.command("formats")
def list_formats() -> None:
    """List available export formats."""
    console.print("[bold]Available Export Formats[/bold]\n")

    formats = [
        ("json", "JSON", "Full structured data export", "✓"),
        ("markdown", "Markdown", "GFM, MMD, Standard flavors", "✓"),
        ("latex", "LaTeX", "Compilable LaTeX document", "✓"),
        ("docx", "Microsoft Word", "DOCX with python-docx", "✓" if DOCX_AVAILABLE else "✗ (install python-docx)"),
    ]

    from rich.table import Table
    table = Table(show_header=True, header_style="bold")
    table.add_column("Format")
    table.add_column("Name")
    table.add_column("Description")
    table.add_column("Available")

    for fmt, name, desc, available in formats:
        table.add_row(fmt, name, desc, available)

    console.print(table)


__all__ = ["app"]
