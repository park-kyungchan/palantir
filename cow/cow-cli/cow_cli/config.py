"""
COW CLI - Configuration Management

Handles config loading, environment variable overrides, and secure key storage.
"""
from typing import Optional, Any
from pathlib import Path
from pydantic import BaseModel, Field, field_validator
import yaml
import keyring
import os

# Default paths
DEFAULT_CONFIG_DIR = Path.home() / ".cow"
DEFAULT_CONFIG_FILE = DEFAULT_CONFIG_DIR / "config.yaml"
DEFAULT_CACHE_DIR = DEFAULT_CONFIG_DIR / "cache"

# Keyring service name
KEYRING_SERVICE = "cow-cli"


class MathpixConfig(BaseModel):
    """Mathpix API configuration."""
    app_id: str = Field(default="", description="Mathpix App ID")
    app_key: str = Field(default="", description="Mathpix App Key (stored in keyring)")
    endpoint: str = Field(
        default="https://api.mathpix.com",
        description="Mathpix API endpoint"
    )
    timeout: int = Field(default=30, description="API timeout in seconds")

    @field_validator("endpoint")
    @classmethod
    def validate_endpoint(cls, v: str) -> str:
        """Ensure endpoint doesn't have trailing slash."""
        return v.rstrip("/")


class CacheConfig(BaseModel):
    """Cache configuration."""
    enabled: bool = Field(default=True, description="Enable response caching")
    directory: Path = Field(
        default=DEFAULT_CACHE_DIR,
        description="Cache directory path"
    )
    ttl_days: int = Field(default=30, description="Cache TTL in days")
    max_size_mb: int = Field(default=500, description="Max cache size in MB")


class ReviewConfig(BaseModel):
    """HITL review configuration."""
    auto_approve_threshold: float = Field(
        default=0.95,
        ge=0.0,
        le=1.0,
        description="Confidence threshold for auto-approval"
    )
    require_review_threshold: float = Field(
        default=0.75,
        ge=0.0,
        le=1.0,
        description="Confidence threshold requiring manual review"
    )
    database_path: Path = Field(
        default=DEFAULT_CONFIG_DIR / "review.db",
        description="SQLite database path for review queue"
    )


class OutputConfig(BaseModel):
    """Output configuration."""
    default_directory: Path = Field(
        default=Path("./output"),
        description="Default output directory"
    )
    default_format: str = Field(
        default="docx",
        description="Default export format"
    )
    preserve_layout: bool = Field(
        default=True,
        description="Preserve layout in exports"
    )


class LoggingConfig(BaseModel):
    """Logging configuration."""
    level: str = Field(default="INFO", description="Log level")
    file: Optional[Path] = Field(
        default=None,
        description="Log file path (None for stderr only)"
    )
    format: str = Field(
        default="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        description="Log format"
    )


class Config(BaseModel):
    """Main configuration model."""
    mathpix: MathpixConfig = Field(default_factory=MathpixConfig)
    cache: CacheConfig = Field(default_factory=CacheConfig)
    review: ReviewConfig = Field(default_factory=ReviewConfig)
    output: OutputConfig = Field(default_factory=OutputConfig)
    logging: LoggingConfig = Field(default_factory=LoggingConfig)


def get_env_override(key: str, default: Any = None) -> Any:
    """Get environment variable with COW_ prefix."""
    env_key = f"COW_{key.upper()}"
    return os.environ.get(env_key, default)


def load_config(path: Optional[Path] = None) -> Config:
    """
    Load configuration from file with environment variable overrides.

    Priority (highest to lowest):
    1. Environment variables (COW_* prefix)
    2. Config file
    3. Default values

    Args:
        path: Optional config file path. Defaults to ~/.cow/config.yaml

    Returns:
        Config object with loaded settings
    """
    config_path = path or DEFAULT_CONFIG_FILE
    config_data: dict = {}

    # Load from file if exists
    if config_path.exists():
        with open(config_path, "r", encoding="utf-8") as f:
            config_data = yaml.safe_load(f) or {}

    # Apply environment variable overrides
    env_overrides = {
        "mathpix": {
            "app_id": get_env_override("MATHPIX_APP_ID"),
            "app_key": get_env_override("MATHPIX_APP_KEY"),
            "endpoint": get_env_override("MATHPIX_ENDPOINT"),
        },
        "cache": {
            "enabled": get_env_override("CACHE_ENABLED"),
            "ttl_days": get_env_override("CACHE_TTL_DAYS"),
        },
        "logging": {
            "level": get_env_override("LOG_LEVEL"),
        }
    }

    # Merge env overrides (remove None values)
    for section, values in env_overrides.items():
        if section not in config_data:
            config_data[section] = {}
        for key, value in values.items():
            if value is not None:
                config_data[section][key] = value

    return Config(**config_data)


def save_config(config: Config, path: Optional[Path] = None) -> None:
    """
    Save configuration to file.

    Args:
        config: Config object to save
        path: Optional config file path. Defaults to ~/.cow/config.yaml
    """
    config_path = path or DEFAULT_CONFIG_FILE

    # Ensure directory exists
    config_path.parent.mkdir(parents=True, exist_ok=True)

    # Convert to dict, handling Path objects
    config_dict = config.model_dump()

    def convert_paths(obj: Any) -> Any:
        if isinstance(obj, Path):
            return str(obj)
        elif isinstance(obj, dict):
            return {k: convert_paths(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [convert_paths(item) for item in obj]
        return obj

    config_dict = convert_paths(config_dict)

    with open(config_path, "w", encoding="utf-8") as f:
        yaml.dump(config_dict, f, default_flow_style=False, allow_unicode=True)


def get_api_key(service: str) -> Optional[str]:
    """
    Get API key from keyring.

    Args:
        service: Service name (e.g., "mathpix")

    Returns:
        API key or None if not found
    """
    try:
        return keyring.get_password(KEYRING_SERVICE, service)
    except Exception:
        return None


def set_api_key(service: str, key: str) -> bool:
    """
    Store API key in keyring.

    Args:
        service: Service name (e.g., "mathpix")
        key: API key to store

    Returns:
        True if successful, False otherwise
    """
    try:
        keyring.set_password(KEYRING_SERVICE, service, key)
        return True
    except Exception:
        return False


def delete_api_key(service: str) -> bool:
    """
    Delete API key from keyring.

    Args:
        service: Service name (e.g., "mathpix")

    Returns:
        True if successful, False otherwise
    """
    try:
        keyring.delete_password(KEYRING_SERVICE, service)
        return True
    except Exception:
        return False


def get_mathpix_credentials() -> tuple[Optional[str], Optional[str]]:
    """
    Get Mathpix credentials from config and keyring.

    Returns:
        Tuple of (app_id, app_key)
    """
    config = load_config()

    # Get app_id from config or env
    app_id = config.mathpix.app_id or get_env_override("MATHPIX_APP_ID")

    # Get app_key from keyring, config, or env (in priority order)
    app_key = (
        get_api_key("mathpix") or
        config.mathpix.app_key or
        get_env_override("MATHPIX_APP_KEY")
    )

    return app_id, app_key


def init_config(force: bool = False) -> Path:
    """
    Initialize configuration with defaults.

    Args:
        force: Overwrite existing config if True

    Returns:
        Path to created config file

    Raises:
        FileExistsError: If config exists and force=False
    """
    if DEFAULT_CONFIG_FILE.exists() and not force:
        raise FileExistsError(f"Config already exists: {DEFAULT_CONFIG_FILE}")

    # Create default config
    config = Config()
    save_config(config)

    # Ensure cache directory exists
    DEFAULT_CACHE_DIR.mkdir(parents=True, exist_ok=True)

    return DEFAULT_CONFIG_FILE


# Default config template for reference
CONFIG_TEMPLATE = """
# COW CLI Configuration
# Location: ~/.cow/config.yaml

mathpix:
  app_id: ""  # Set via: cow config mathpix --app-id YOUR_ID
  # app_key is stored securely in system keyring
  endpoint: "https://api.mathpix.com"
  timeout: 30

cache:
  enabled: true
  directory: "~/.cow/cache"
  ttl_days: 30
  max_size_mb: 500

review:
  auto_approve_threshold: 0.95
  require_review_threshold: 0.75
  database_path: "~/.cow/review.db"

output:
  default_directory: "./output"
  default_format: "docx"
  preserve_layout: true

logging:
  level: "INFO"
  file: null  # Set to path for file logging
""".strip()
