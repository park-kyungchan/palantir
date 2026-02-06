"""
COW CLI - Main CLI Application

Typer-based CLI framework with subcommand groups.
"""
from typing import Optional
from dataclasses import dataclass
import typer
from rich.console import Console

# Import version from package root to avoid duplication
try:
    from cow_cli import __version__
except ImportError:
    __version__ = "0.1.0"

# Initialize console for rich output
console = Console()


@dataclass
class GlobalState:
    """Global state container for CLI options."""

    verbose: bool = False
    config_path: Optional[str] = None
    no_cache: bool = False

    def __post_init__(self):
        """Apply global settings."""
        if self.verbose:
            import logging
            logging.getLogger("cow-cli").setLevel(logging.DEBUG)


# Global state singleton
_global_state: Optional[GlobalState] = None


def get_global_state() -> GlobalState:
    """Get the global state, creating default if not initialized."""
    global _global_state
    if _global_state is None:
        _global_state = GlobalState()
    return _global_state


def set_global_state(verbose: bool = False, config_path: Optional[str] = None, no_cache: bool = False) -> GlobalState:
    """Initialize and set global state."""
    global _global_state
    _global_state = GlobalState(verbose=verbose, config_path=config_path, no_cache=no_cache)
    return _global_state

# Main application
app = typer.Typer(
    name="cow",
    help="COW Pipeline CLI - Layout/Content Separation with Claude Agent SDK",
    add_completion=True,
    rich_markup_mode="rich",
)

# Import subcommand modules
from cow_cli.commands.review import app as review_app
from cow_cli.commands.export import app as export_app
from cow_cli.commands.process import app as process_app

# Config subcommand group
config_app = typer.Typer(help="Configuration management")

# Register subcommand groups
app.add_typer(process_app, name="process")
app.add_typer(review_app, name="review")
app.add_typer(export_app, name="export")
app.add_typer(config_app, name="config")


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
        "-V",
        callback=version_callback,
        is_eager=True,
        help="Show version and exit.",
    ),
    verbose: bool = typer.Option(
        False,
        "--verbose",
        "-v",
        help="Enable verbose output.",
    ),
    config_path: Optional[str] = typer.Option(
        None,
        "--config",
        "-c",
        help="Path to configuration file.",
    ),
    no_cache: bool = typer.Option(
        False,
        "--no-cache",
        help="Disable response caching.",
    ),
) -> None:
    """
    COW Pipeline CLI - Layout/Content Separation with Claude Agent SDK.

    Process math/science images through Mathpix OCR, separate layout and content,
    and enable human-in-the-loop review workflow.
    """
    # Initialize global state with CLI options
    state = set_global_state(
        verbose=verbose,
        config_path=config_path,
        no_cache=no_cache,
    )

    if verbose:
        console.print("[dim]Verbose mode enabled[/dim]")
    if no_cache:
        console.print("[dim]Response caching disabled[/dim]")


# Process commands are implemented in cow_cli/commands/process.py
# Review commands are implemented in cow_cli/commands/review.py
# Export commands are implemented in cow_cli/commands/export.py


# =============================================================================
# CONFIG COMMANDS
# =============================================================================
@config_app.command("show")
def config_show(
    format: str = typer.Option("table", "-f", "--format", help="Output format: table, json, yaml"),
    show_secrets: bool = typer.Option(False, "--show-secrets", help="Show API keys (masked by default)"),
) -> None:
    """Show current configuration."""
    from cow_cli.config import load_config, get_api_key, DEFAULT_CONFIG_FILE
    from cow_cli.logging import print_table, print_json, print_yaml, log_warning
    from pathlib import Path

    try:
        config = load_config()
    except FileNotFoundError:
        log_warning(f"Config file not found: {DEFAULT_CONFIG_FILE}")
        console.print("[yellow]Run 'cow config init' to create configuration.[/yellow]")
        raise typer.Exit(1)

    # Get API key status
    mathpix_key = get_api_key("mathpix")
    key_status = "✓ Set (keyring)" if mathpix_key else "✗ Not set"
    if show_secrets and mathpix_key:
        key_display = mathpix_key[:8] + "..." + mathpix_key[-4:]
    else:
        key_display = key_status

    if format == "json":
        config_dict = config.model_dump()
        config_dict["mathpix"]["app_key"] = key_display
        print_json(config_dict, "Configuration")
    elif format == "yaml":
        import yaml
        config_dict = config.model_dump()
        config_dict["mathpix"]["app_key"] = key_display
        def convert_paths(obj):
            if isinstance(obj, Path):
                return str(obj)
            elif isinstance(obj, dict):
                return {k: convert_paths(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [convert_paths(i) for i in obj]
            return obj
        config_dict = convert_paths(config_dict)
        print_yaml(yaml.dump(config_dict, default_flow_style=False), "Configuration")
    else:
        console.print("[bold]COW CLI Configuration[/bold]\n")
        print_table("Mathpix API", ["Setting", "Value"], [
            ["App ID", config.mathpix.app_id or "(not set)"],
            ["App Key", key_display],
            ["Endpoint", config.mathpix.endpoint],
            ["Timeout", f"{config.mathpix.timeout}s"],
        ])
        console.print()
        print_table("Cache", ["Setting", "Value"], [
            ["Enabled", "Yes" if config.cache.enabled else "No"],
            ["Directory", str(config.cache.directory)],
            ["TTL", f"{config.cache.ttl_days} days"],
            ["Max Size", f"{config.cache.max_size_mb} MB"],
        ])


@config_app.command("set")
def config_set(
    key: str = typer.Argument(..., help="Configuration key (e.g., 'mathpix.timeout')"),
    value: str = typer.Argument(..., help="Configuration value"),
) -> None:
    """Set a configuration value."""
    from cow_cli.config import load_config, save_config, Config
    from cow_cli.logging import log_success, log_error, ErrorCode

    try:
        config = load_config()
    except Exception as e:
        log_error(ErrorCode.CONFIG_NOT_FOUND, str(e))
        raise typer.Exit(1)

    keys = key.split(".")
    config_dict = config.model_dump()
    obj = config_dict
    for k in keys[:-1]:
        if k not in obj:
            log_error(ErrorCode.CONFIG_INVALID, f"Unknown config key: {key}")
            raise typer.Exit(1)
        obj = obj[k]

    final_key = keys[-1]
    if final_key not in obj:
        log_error(ErrorCode.CONFIG_INVALID, f"Unknown config key: {key}")
        raise typer.Exit(1)

    old_value = obj[final_key]
    if isinstance(old_value, bool):
        new_value = value.lower() in ("true", "1", "yes")
    elif isinstance(old_value, int):
        new_value = int(value)
    elif isinstance(old_value, float):
        new_value = float(value)
    else:
        new_value = value

    obj[final_key] = new_value
    new_config = Config(**config_dict)
    save_config(new_config)
    log_success(f"Set {key} = {new_value}")


@config_app.command("get")
def config_get(
    key: str = typer.Argument(..., help="Configuration key (e.g., 'mathpix.endpoint')"),
) -> None:
    """Get a configuration value."""
    from cow_cli.config import load_config
    from cow_cli.logging import log_error, ErrorCode

    try:
        config = load_config()
    except Exception as e:
        log_error(ErrorCode.CONFIG_NOT_FOUND, str(e))
        raise typer.Exit(1)

    keys = key.split(".")
    config_dict = config.model_dump()
    obj = config_dict
    for k in keys:
        if isinstance(obj, dict) and k in obj:
            obj = obj[k]
        else:
            log_error(ErrorCode.CONFIG_INVALID, f"Unknown config key: {key}")
            raise typer.Exit(1)

    console.print(f"[cyan]{key}[/cyan] = [green]{obj}[/green]")


@config_app.command("init")
def config_init(
    force: bool = typer.Option(False, "-f", "--force", help="Overwrite existing config"),
    no_interactive: bool = typer.Option(False, "--no-interactive", help="Skip interactive setup"),
) -> None:
    """Initialize configuration with defaults."""
    from cow_cli.config import init_config, set_api_key, DEFAULT_CONFIG_FILE, Config, save_config
    from cow_cli.logging import log_success, log_warning, log_info
    from rich.prompt import Prompt, Confirm

    interactive = not no_interactive

    if DEFAULT_CONFIG_FILE.exists() and not force:
        log_warning(f"Config already exists: {DEFAULT_CONFIG_FILE}")
        if interactive and not Confirm.ask("Overwrite existing configuration?"):
            raise typer.Exit(0)

    console.print("[bold blue]COW CLI Setup Wizard[/bold blue]\n")

    if interactive:
        log_info("Setting up Mathpix API credentials...")
        console.print("[dim]Get your credentials at: https://accounts.mathpix.com[/dim]\n")

        app_id = Prompt.ask("Mathpix App ID", default="")
        app_key = Prompt.ask("Mathpix App Key", password=True, default="")

        config = Config()
        if app_id:
            config.mathpix.app_id = app_id
        save_config(config)

        if app_key:
            if set_api_key("mathpix", app_key):
                log_success("Mathpix credentials stored securely in keyring")
            else:
                log_warning("Could not store API key in keyring.")
    else:
        init_config(force=True)

    log_success(f"Configuration created: {DEFAULT_CONFIG_FILE}")


@config_app.command("mathpix")
def config_mathpix(
    app_id: Optional[str] = typer.Option(None, "--app-id", help="Mathpix App ID"),
    app_key: Optional[str] = typer.Option(None, "--app-key", help="Mathpix App Key"),
) -> None:
    """Configure Mathpix API credentials."""
    from cow_cli.config import load_config, save_config, set_api_key, get_api_key
    from cow_cli.logging import log_success, log_error, ErrorCode

    config = load_config()

    if app_id:
        config.mathpix.app_id = app_id
        save_config(config)
        log_success(f"Mathpix App ID set: {app_id[:8]}...")

    if app_key:
        if set_api_key("mathpix", app_key):
            log_success("Mathpix App Key stored in keyring")
        else:
            log_error(ErrorCode.API_KEY_INVALID, "Failed to store API key")

    if not app_id and not app_key:
        stored_key = get_api_key("mathpix")
        console.print("[bold]Mathpix Configuration[/bold]")
        console.print(f"  App ID:   {config.mathpix.app_id or '[red]Not set[/red]'}")
        console.print(f"  App Key:  {'[green]✓ Stored[/green]' if stored_key else '[red]Not set[/red]'}")


@config_app.command("validate")
def config_validate() -> None:
    """Validate configuration and test connections."""
    from cow_cli.config import load_config, get_api_key, DEFAULT_CONFIG_FILE
    from cow_cli.logging import log_success, log_error, log_warning, ErrorCode

    console.print("[bold]Validating Configuration[/bold]\n")
    errors = 0

    if DEFAULT_CONFIG_FILE.exists():
        log_success(f"Config file: {DEFAULT_CONFIG_FILE}")
    else:
        log_error(ErrorCode.CONFIG_NOT_FOUND, "Config file not found")
        errors += 1

    try:
        config = load_config()
        log_success("Config schema valid")
    except Exception as e:
        log_error(ErrorCode.CONFIG_INVALID, str(e))
        raise typer.Exit(1)

    if config.mathpix.app_id:
        log_success(f"Mathpix App ID: {config.mathpix.app_id[:8]}...")
    else:
        log_warning("Mathpix App ID not set")
        errors += 1

    if get_api_key("mathpix"):
        log_success("Mathpix App Key in keyring")
    else:
        log_warning("Mathpix App Key not found")
        errors += 1

    if errors == 0:
        log_success("All validations passed!")
    else:
        log_warning(f"{errors} issue(s) found")


if __name__ == "__main__":
    app()
