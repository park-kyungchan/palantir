"""
Orion ODA V3 - Tools CLI
=========================
Typer CLI for IDT commands.

Maps to IndyDevDan's idt command structure.

Usage:
    python -m scripts.tools sps list
    python -m scripts.tools yt transcribe video.mp4
"""

import asyncio
import logging
from pathlib import Path
from typing import List, Optional

import typer

# Create main app
app = typer.Typer(
    name="idt",
    help="IndyDevTools for Orion ODA",
    no_args_is_help=True,
)

# Create subcommand groups
sps_app = typer.Typer(help="Simple Prompt System")
yt_app = typer.Typer(help="YouTube Automation")

app.add_typer(sps_app, name="sps")
app.add_typer(yt_app, name="yt")


# ==============================================================================
# SPS Commands
# ==============================================================================

@sps_app.command("list")
def sps_list(
    prompts_dir: str = typer.Option("./prompts", help="Prompts directory"),
):
    """List all available prompts."""
    from scripts.tools.sps import PromptManager
    
    manager = PromptManager(prompts_dir)
    prompts = manager.list()
    
    if not prompts:
        typer.echo("No prompts found.")
        typer.echo(f"Create prompts in: {prompts_dir}")
        return
    
    typer.echo(f"\n📝 Found {len(prompts)} prompts:\n")
    for name in prompts:
        prompt = manager.get(name)
        typer.echo(f"  • {typer.style(name, bold=True)}")
        if prompt.description:
            typer.echo(f"    {prompt.description}")
        if prompt.variables:
            typer.echo(f"    Variables: {', '.join(prompt.variables)}")


@sps_app.command("run")
def sps_run(
    name: str = typer.Argument(..., help="Prompt name"),
    variables: List[str] = typer.Option([], "--var", "-v", help="Variables (key=value)"),
    stream: bool = typer.Option(False, "--stream", "-s", help="Stream output"),
    prompts_dir: str = typer.Option("./prompts", help="Prompts directory"),
):
    """Run a prompt."""
    from scripts.tools.sps import PromptManager, PromptRunner
    
    # Parse variables
    var_dict = {}
    for v in variables:
        if "=" not in v:
            typer.echo(f"Invalid variable format: {v} (use key=value)")
            raise typer.Exit(1)
        key, value = v.split("=", 1)
        var_dict[key] = value
    
    manager = PromptManager(prompts_dir)
    runner = PromptRunner(manager)
    
    typer.echo(f"🔄 Running prompt: {name}")
    
    try:
        result = asyncio.run(runner.run(name, var_dict, stream=stream))
        
        if not stream:
            typer.echo("\n" + "="*50)
            typer.echo(result)
    except ValueError as e:
        typer.echo(f"❌ Error: {e}")
        raise typer.Exit(1)


@sps_app.command("create")
def sps_create(
    name: str = typer.Argument(..., help="Prompt name"),
    prompts_dir: str = typer.Option("./prompts", help="Prompts directory"),
):
    """Create a new prompt interactively."""
    from scripts.tools.sps import Prompt, PromptManager
    
    typer.echo(f"\n📝 Creating prompt: {name}\n")
    
    description = typer.prompt("Description")
    template = typer.prompt("Template (use {{variable}} for variables)")
    variables = typer.prompt("Variables (comma-separated)", default="")
    
    var_list = [v.strip() for v in variables.split(",") if v.strip()]
    
    prompt = Prompt(
        name=name,
        template=template,
        variables=var_list,
        description=description,
    )
    
    manager = PromptManager(prompts_dir)
    manager.add(prompt)
    
    typer.echo(f"\n✅ Created prompt: {name}")
    typer.echo(f"   Saved to: {prompts_dir}/{name}.yaml")


@sps_app.command("show")
def sps_show(
    name: str = typer.Argument(..., help="Prompt name"),
    prompts_dir: str = typer.Option("./prompts", help="Prompts directory"),
):
    """Show prompt details."""
    from scripts.tools.sps import PromptManager
    
    manager = PromptManager(prompts_dir)
    prompt = manager.get(name)
    
    if not prompt:
        typer.echo(f"❌ Prompt not found: {name}")
        raise typer.Exit(1)
    
    typer.echo(f"\n📝 Prompt: {prompt.name}")
    typer.echo(f"   Description: {prompt.description or '(none)'}")
    typer.echo(f"   Variables: {', '.join(prompt.variables) or '(none)'}")
    typer.echo(f"   Model: {prompt.model}")
    typer.echo(f"\n   Template:\n")
    typer.echo(prompt.template)


# ==============================================================================
# YT Commands
# ==============================================================================

@yt_app.command("transcribe")
def yt_transcribe(
    source: str = typer.Argument(..., help="YouTube URL or file path"),
    output: str = typer.Option("transcript.txt", help="Output file"),
    language: str = typer.Option("en", help="Language code"),
    format: str = typer.Option("text", help="Output format: text, srt, vtt"),
):
    """Transcribe a video."""
    from scripts.tools.yt import Transcriber
    
    typer.echo(f"🎤 Transcribing: {source}")
    
    transcriber = Transcriber()
    
    try:
        result = asyncio.run(transcriber.transcribe(
            source,
            language=language,
            output_format=format,
        ))
        
        Path(output).write_text(result)
        typer.echo(f"\n✅ Saved to: {output}")
        typer.echo(f"   Length: {len(result)} characters")
    except Exception as e:
        typer.echo(f"❌ Error: {e}")
        raise typer.Exit(1)


@yt_app.command("generate")
def yt_generate(
    transcript_file: str = typer.Argument(..., help="Path to transcript file"),
    output_dir: str = typer.Option("./output", help="Output directory"),
    style: str = typer.Option("educational", help="Content style"),
):
    """Generate YouTube metadata from transcript."""
    from scripts.tools.yt import MetadataGenerator
    import json
    
    if not Path(transcript_file).exists():
        typer.echo(f"❌ File not found: {transcript_file}")
        raise typer.Exit(1)
    
    transcript = Path(transcript_file).read_text()
    
    typer.echo(f"🔄 Generating metadata from {len(transcript)} chars...")
    
    generator = MetadataGenerator()
    result = asyncio.run(generator.generate(transcript, style=style))
    
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    metadata_file = output_path / "metadata.json"
    metadata_file.write_text(json.dumps(result, indent=2))
    
    # Print summary
    typer.echo("\n📊 Generated Metadata:\n")
    typer.echo(f"  Titles: {len(result.get('titles', []))}")
    typer.echo(f"  Tags: {len(result.get('tags', []))}")
    typer.echo(f"  Chapters: {len(result.get('chapters', []))}")
    typer.echo(f"  Thumbnails: {len(result.get('thumbnails', []))}")
    typer.echo(f"\n✅ Saved to: {metadata_file}")


@yt_app.command("workflow")
def yt_workflow(
    source: str = typer.Argument(..., help="YouTube URL or file path"),
    output_dir: str = typer.Option("./output", help="Output directory"),
):
    """Run full YouTube automation workflow."""
    from scripts.tools.yt import YouTubeWorkflow
    
    typer.echo(f"🚀 Starting workflow for: {source}\n")
    
    workflow = YouTubeWorkflow(source, output_dir)
    result = asyncio.run(workflow.run())
    
    if result.state.value == "completed":
        typer.echo("\n✅ Workflow completed!")
        typer.echo(f"   Output: {output_dir}")
        typer.echo(f"   Files: transcript.txt, metadata.json")
    else:
        typer.echo(f"\n❌ Workflow failed: {result.error}")
        raise typer.Exit(1)


@yt_app.command("resume")
def yt_resume(
    output_dir: str = typer.Argument(..., help="Output directory with saved state"),
):
    """Resume a workflow from saved state."""
    from scripts.tools.yt import YouTubeWorkflow
    
    try:
        workflow = YouTubeWorkflow.resume(output_dir)
        typer.echo(f"🔄 Resuming workflow from state: {workflow.context.state.value}")
        
        result = asyncio.run(workflow.run())
        
        if result.state.value == "completed":
            typer.echo("\n✅ Workflow completed!")
        else:
            typer.echo(f"\n❌ Workflow failed: {result.error}")
            raise typer.Exit(1)
    except ValueError as e:
        typer.echo(f"❌ Error: {e}")
        raise typer.Exit(1)


# ==============================================================================
# Entry Point
# ==============================================================================

def main():
    """Main entry point."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)-7s | %(message)s",
        datefmt="%H:%M:%S",
    )
    app()


if __name__ == "__main__":
    main()
