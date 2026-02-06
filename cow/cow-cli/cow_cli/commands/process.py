"""
COW CLI - Process Commands

CLI commands for processing images, batches, and PDFs through the COW pipeline.
"""
from typing import Optional, List
from pathlib import Path
import asyncio
import json
from datetime import datetime

import typer
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn, TimeElapsedColumn
from rich.table import Table
from rich import box

from cow_cli.pipeline.processor import (
    PipelineProcessor,
    PipelineResult,
    process_image as pipeline_process_image,
    process_batch as pipeline_process_batch,
)
from cow_cli.export import (
    ExportFormat,
    ExportOptions,
    get_exporter,
)


console = Console()
app = typer.Typer(name="process", help="Process images through the COW pipeline")


def _format_duration(ms: float) -> str:
    """Format duration in human-readable format."""
    if ms < 1000:
        return f"{ms:.0f}ms"
    elif ms < 60000:
        return f"{ms/1000:.1f}s"
    else:
        return f"{ms/60000:.1f}min"


def _display_result(result: PipelineResult) -> None:
    """Display processing result."""
    if result.success:
        console.print(f"[green]✓[/green] {result.image_path}")
        console.print(f"  Duration: {_format_duration(result.total_duration_ms)}")

        if result.document:
            doc = result.document
            console.print(f"  Layout elements: {len(doc.layout.elements)}")
            console.print(f"  Content elements: {len(doc.content.elements)}")

            # Quality summary
            if doc.content.quality_summary.total_elements > 0:
                qs = doc.content.quality_summary
                console.print(f"  Confidence: avg={qs.average_confidence:.1%}" if qs.average_confidence else "  Confidence: N/A")

        # Stage timings
        if result.stages:
            timings = ", ".join(
                f"{s.stage}={_format_duration(s.duration_ms)}"
                for s in result.stages
            )
            console.print(f"  [dim]Stages: {timings}[/dim]")
    else:
        console.print(f"[red]✗[/red] {result.image_path}: {result.error}")


def _export_result(
    result: PipelineResult,
    output_dir: Path,
    export_formats: List[str],
) -> None:
    """Export result to specified formats."""
    if not result.success or not result.document:
        return

    for fmt_str in export_formats:
        try:
            fmt = ExportFormat(fmt_str.lower())
            exporter = get_exporter(fmt)

            # Determine output filename
            stem = Path(result.image_path).stem
            ext = exporter.get_default_extension()
            output_path = output_dir / f"{stem}{ext}"

            export_result = exporter.export(result.document, output_path)

            if export_result.success:
                console.print(f"  [blue]→[/blue] Exported to {output_path}")
            else:
                console.print(f"  [yellow]⚠[/yellow] Export failed ({fmt_str}): {export_result.error}")

        except ValueError:
            console.print(f"  [yellow]⚠[/yellow] Unknown format: {fmt_str}")
        except Exception as e:
            console.print(f"  [yellow]⚠[/yellow] Export error ({fmt_str}): {e}")


@app.command("image")
def process_image_cmd(
    image_path: Path = typer.Argument(..., help="Path to image file"),
    output_dir: Optional[Path] = typer.Option(
        None, "-o", "--output", help="Output directory"
    ),
    export_format: Optional[List[str]] = typer.Option(
        None, "-f", "--format", help="Export formats (json, markdown, latex, docx)"
    ),
    skip_validation: bool = typer.Option(
        False, "--skip-validation", help="Skip image validation"
    ),
    skip_review: bool = typer.Option(
        False, "--skip-review", help="Skip HITL review queue"
    ),
    confidence_threshold: Optional[float] = typer.Option(
        None, "--confidence", "-c", help="Confidence threshold override (0.0-1.0)"
    ),
    json_output: bool = typer.Option(
        False, "--json", help="Output result as JSON"
    ),
) -> None:
    """Process a single image through the COW pipeline."""
    # Validate input
    if not image_path.exists():
        console.print(f"[red]Error:[/red] File not found: {image_path}")
        raise typer.Exit(1)

    if not image_path.is_file():
        console.print(f"[red]Error:[/red] Not a file: {image_path}")
        raise typer.Exit(1)

    # Set default output directory
    if output_dir is None:
        output_dir = Path("./output")

    output_dir.mkdir(parents=True, exist_ok=True)

    # Build Mathpix options
    mathpix_options = {}
    if confidence_threshold is not None:
        mathpix_options["confidence_threshold"] = confidence_threshold

    # Process
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task(f"Processing {image_path.name}...", total=None)

        result = asyncio.run(
            pipeline_process_image(
                image_path=image_path,
                mathpix_options=mathpix_options if mathpix_options else None,
                output_dir=output_dir,
                skip_validation=skip_validation,
            )
        )

        progress.remove_task(task)

    # JSON output
    if json_output:
        output_data = {
            "success": result.success,
            "image_path": str(result.image_path),
            "duration_ms": result.total_duration_ms,
            "error": result.error,
            "stages": [
                {
                    "stage": s.stage,
                    "success": s.success,
                    "duration_ms": s.duration_ms,
                    "error": s.error,
                }
                for s in result.stages
            ],
        }

        if result.document:
            output_data["layout_elements"] = len(result.document.layout.elements)
            output_data["content_elements"] = len(result.document.content.elements)

        console.print_json(json.dumps(output_data, indent=2))
        return

    # Display result
    _display_result(result)

    # Export to formats
    if export_format and result.success:
        _export_result(result, output_dir, export_format)

    # Save JSON output
    if result.success and result.document:
        json_path = output_dir / f"{image_path.stem}.json"
        json_path.write_text(result.document.model_dump_json(indent=2))
        console.print(f"  [blue]→[/blue] Saved to {json_path}")

    if not result.success:
        raise typer.Exit(1)


@app.command("batch")
def process_batch_cmd(
    input_dir: Path = typer.Argument(..., help="Directory containing images"),
    output_dir: Optional[Path] = typer.Option(
        None, "-o", "--output", help="Output directory"
    ),
    pattern: str = typer.Option(
        "*.png", "-p", "--pattern", help="File glob pattern"
    ),
    export_format: Optional[List[str]] = typer.Option(
        None, "-f", "--format", help="Export formats"
    ),
    parallel: int = typer.Option(
        4, "-j", "--jobs", help="Number of parallel jobs"
    ),
    batch_size: int = typer.Option(
        20, "--batch-size", help="Process in batches of this size"
    ),
    skip_validation: bool = typer.Option(
        False, "--skip-validation", help="Skip image validation"
    ),
    skip_deduplication: bool = typer.Option(
        False, "--skip-dedup", help="Skip deduplication check"
    ),
    resume: bool = typer.Option(
        False, "--resume", help="Resume processing (skip already processed)"
    ),
    json_output: bool = typer.Option(
        False, "--json", help="Output results as JSON"
    ),
) -> None:
    """Process multiple images in batch mode."""
    # Validate input
    if not input_dir.exists():
        console.print(f"[red]Error:[/red] Directory not found: {input_dir}")
        raise typer.Exit(1)

    if not input_dir.is_dir():
        console.print(f"[red]Error:[/red] Not a directory: {input_dir}")
        raise typer.Exit(1)

    # Find images
    image_paths = list(input_dir.glob(pattern))

    if not image_paths:
        console.print(f"[yellow]No images found matching pattern:[/yellow] {pattern}")
        raise typer.Exit(0)

    # Set default output directory
    if output_dir is None:
        output_dir = Path("./output")

    output_dir.mkdir(parents=True, exist_ok=True)

    # Filter already processed if resume
    if resume:
        processed = set()
        for p in output_dir.glob("*/*.json"):
            processed.add(p.parent.name)

        original_count = len(image_paths)
        image_paths = [p for p in image_paths if p.stem not in processed]

        if len(image_paths) < original_count:
            console.print(f"[dim]Resuming: skipping {original_count - len(image_paths)} already processed[/dim]")

    if not image_paths:
        console.print("[green]All images already processed![/green]")
        return

    console.print(f"[bold]Batch Processing[/bold]")
    console.print(f"  Input: {input_dir}")
    console.print(f"  Images: {len(image_paths)}")
    console.print(f"  Parallel: {parallel}")
    console.print()

    # Process in batches
    all_results: List[PipelineResult] = []
    total_batches = (len(image_paths) + batch_size - 1) // batch_size

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TaskProgressColumn(),
        TimeElapsedColumn(),
        console=console,
    ) as progress:
        main_task = progress.add_task("Processing...", total=len(image_paths))

        for batch_idx in range(total_batches):
            start = batch_idx * batch_size
            end = min(start + batch_size, len(image_paths))
            batch_paths = image_paths[start:end]

            results = asyncio.run(
                pipeline_process_batch(
                    image_paths=batch_paths,
                    output_dir=output_dir,
                    skip_validation=skip_validation,
                    skip_deduplication=skip_deduplication,
                    max_concurrent=parallel,
                )
            )

            all_results.extend(results)
            progress.update(main_task, advance=len(batch_paths))

            # Export each result
            if export_format:
                for result in results:
                    if result.success:
                        img_output_dir = output_dir / Path(result.image_path).stem
                        _export_result(result, img_output_dir, export_format)

    # Summary
    successful = sum(1 for r in all_results if r.success)
    failed = len(all_results) - successful
    total_time = sum(r.total_duration_ms for r in all_results)

    console.print()

    if json_output:
        summary = {
            "total": len(all_results),
            "successful": successful,
            "failed": failed,
            "total_time_ms": total_time,
            "results": [
                {
                    "image_path": r.image_path,
                    "success": r.success,
                    "duration_ms": r.total_duration_ms,
                    "error": r.error,
                }
                for r in all_results
            ],
        }
        console.print_json(json.dumps(summary, indent=2))
    else:
        # Display summary table
        table = Table(title="Batch Processing Summary", box=box.ROUNDED)
        table.add_column("Metric", style="bold")
        table.add_column("Value", justify="right")

        table.add_row("Total Images", str(len(all_results)))
        table.add_row("Successful", f"[green]{successful}[/green]")
        table.add_row("Failed", f"[red]{failed}[/red]" if failed else "0")
        table.add_row("Total Time", _format_duration(total_time))
        table.add_row("Avg Time/Image", _format_duration(total_time / len(all_results)) if all_results else "N/A")

        console.print(table)

        # Show failed images
        if failed > 0:
            console.print("\n[red]Failed images:[/red]")
            for r in all_results:
                if not r.success:
                    console.print(f"  • {r.image_path}: {r.error}")

    if failed > 0:
        raise typer.Exit(1)


@app.command("pdf")
def process_pdf_cmd(
    pdf_path: Path = typer.Argument(..., help="Path to PDF file"),
    output_dir: Optional[Path] = typer.Option(
        None, "-o", "--output", help="Output directory"
    ),
    export_format: Optional[List[str]] = typer.Option(
        None, "-f", "--format", help="Export formats"
    ),
    json_output: bool = typer.Option(
        False, "--json", help="Output results as JSON"
    ),
) -> None:
    """Process a PDF document directly through Mathpix API."""
    import time

    # Validate input
    if not pdf_path.exists():
        console.print(f"[red]Error:[/red] File not found: {pdf_path}")
        raise typer.Exit(1)

    if pdf_path.suffix.lower() != ".pdf":
        console.print(f"[red]Error:[/red] Not a PDF file: {pdf_path}")
        raise typer.Exit(1)

    # Set default output directory
    if output_dir is None:
        output_dir = Path("./output") / pdf_path.stem

    output_dir.mkdir(parents=True, exist_ok=True)

    console.print(f"[bold]PDF Processing (Direct API)[/bold]")
    console.print(f"  File: {pdf_path}")
    console.print(f"  Size: {pdf_path.stat().st_size / 1024:.1f} KB")
    console.print()

    # Process PDF directly via Mathpix API
    from cow_cli.mathpix.client import MathpixClient
    from cow_cli.semantic.separator import LayoutContentSeparator

    async def process_pdf_direct():
        start_time = time.time()

        async with MathpixClient() as client:
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console,
            ) as progress:
                task = progress.add_task("Uploading PDF to Mathpix...", total=None)

                try:
                    response = await client.process_pdf(
                        pdf=pdf_path,
                        poll_interval=2.0,
                        max_wait=300.0,
                    )
                    progress.update(task, description="Processing complete!")

                except Exception as e:
                    progress.stop()
                    return None, str(e), time.time() - start_time

        elapsed = time.time() - start_time
        return response, None, elapsed

    response, error, elapsed = asyncio.run(process_pdf_direct())

    if error:
        console.print(f"\n[red]✗[/red] PDF processing failed: {error}")
        raise typer.Exit(1)

    # Separate layout/content using UnifiedResponse directly
    separator = LayoutContentSeparator()

    try:
        # response is already UnifiedResponse from process_pdf()
        document = separator.separate_unified(
            unified=response,
            source_path=str(pdf_path),
        )
    except Exception as e:
        console.print(f"\n[red]✗[/red] Layout/Content separation failed: {e}")
        raise typer.Exit(1)

    # Save results
    separated_path = output_dir / f"{pdf_path.stem}.json"
    layout_path = output_dir / "layout.json"
    content_path = output_dir / "content.json"

    separated_path.write_text(document.model_dump_json(indent=2))
    layout_path.write_text(document.layout.model_dump_json(indent=2))
    content_path.write_text(document.content.model_dump_json(indent=2))

    # Export to other formats
    if export_format:
        from cow_cli.pipeline.processor import PipelineResult, StageResult
        mock_result = PipelineResult(
            image_path=str(pdf_path),
            success=True,
            document=document,
            stages=[StageResult(stage="PDF", success=True, duration_ms=elapsed * 1000)],
            total_duration_ms=elapsed * 1000,
        )
        _export_result(mock_result, output_dir, export_format)

    # Summary
    layout_count = len(document.layout.elements)
    content_count = len(document.content.elements)

    console.print()

    if json_output:
        summary = {
            "pdf_path": str(pdf_path),
            "success": True,
            "duration_sec": round(elapsed, 2),
            "layout_elements": layout_count,
            "content_elements": content_count,
            "output_dir": str(output_dir),
            "request_id": document.request_id,
        }
        console.print_json(json.dumps(summary, indent=2))
    else:
        console.print(f"[green]✓[/green] {pdf_path.name}")
        console.print(f"  Duration: {elapsed:.1f}s")
        console.print(f"  Layout elements: {layout_count}")
        console.print(f"  Content elements: {content_count}")
        console.print(f"  Request ID: {document.request_id}")
        console.print(f"  → Saved to {output_dir}/")


@app.command("status")
def process_status(
    output_dir: Path = typer.Option(
        Path("./output"), "-o", "--output", help="Output directory to check"
    ),
) -> None:
    """Check processing status of completed jobs."""
    if not output_dir.exists():
        console.print(f"[yellow]Output directory not found:[/yellow] {output_dir}")
        return

    # Find all processed results
    results = list(output_dir.glob("*/*.json"))

    if not results:
        console.print("[yellow]No processed results found.[/yellow]")
        return

    # Parse results
    processed = []
    for json_path in results:
        try:
            data = json.loads(json_path.read_text())
            processed.append({
                "name": json_path.parent.name,
                "path": json_path,
                "elements": len(data.get("content", {}).get("elements", [])),
            })
        except Exception:
            processed.append({
                "name": json_path.parent.name,
                "path": json_path,
                "elements": "?",
            })

    # Display table
    table = Table(title="Processing Status", box=box.ROUNDED)
    table.add_column("Name")
    table.add_column("Elements", justify="right")
    table.add_column("Output Path")

    for item in sorted(processed, key=lambda x: x["name"]):
        table.add_row(
            item["name"],
            str(item["elements"]),
            str(item["path"]),
        )

    console.print(table)
    console.print(f"\n[bold]Total:[/bold] {len(processed)} processed items")


def _parse_page_range(range_str: str) -> List[int]:
    """Parse page range string like '1-5,10,15-20' into list of page numbers."""
    pages = []

    for part in range_str.split(","):
        part = part.strip()
        if "-" in part:
            try:
                start, end = part.split("-", 1)
                start = int(start.strip())
                end = int(end.strip())
                pages.extend(range(start, end + 1))
            except ValueError:
                return []
        else:
            try:
                pages.append(int(part))
            except ValueError:
                return []

    return sorted(set(pages))


__all__ = ["app"]
