"""
Centralized Logging Configuration for Math Image Parsing Pipeline v2.0.

Provides unified logging setup with optional structlog support for
structured logging in production environments.

Features:
    - Standard logging with configurable level and format
    - Optional structlog integration for structured logging
    - JSON output mode for production/containerized environments
    - Thread-safe logger retrieval
    - Contextual logging with bound values

Usage:
    from mathpix_pipeline.logging_config import configure_logging, get_logger

    # Basic setup
    configure_logging(level="INFO")
    logger = get_logger(__name__)
    logger.info("Pipeline started")

    # Production setup with JSON output
    configure_logging(level="INFO", use_structlog=True, json_output=True)
    logger = get_logger(__name__)
    logger.info("Processing image", image_id="img_001", stage="ingestion")

    # Debug mode
    configure_logging(level="DEBUG")
"""

from __future__ import annotations

import logging
import sys
from datetime import datetime, timezone
from typing import Any, Optional

# Default configuration
DEFAULT_LEVEL = "INFO"
DEFAULT_FORMAT = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
DEFAULT_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

# Module-level state
_configured = False
_use_structlog = False
_json_output = False


def _get_structlog():
    """Attempt to import structlog, return None if not available."""
    try:
        import structlog
        return structlog
    except ImportError:
        return None


def configure_logging(
    level: str = DEFAULT_LEVEL,
    use_structlog: bool = False,
    json_output: bool = False,
    stream: Any = None,
) -> None:
    """
    Configure centralized logging for the pipeline.

    This function sets up logging configuration for the entire pipeline.
    It should be called once at application startup.

    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL).
            Defaults to INFO.
        use_structlog: If True, configure structlog for structured logging.
            Falls back to standard logging if structlog is not installed.
            Defaults to False.
        json_output: If True, output logs in JSON format (requires structlog).
            Useful for production environments with log aggregation.
            Defaults to False.
        stream: Output stream for logs. Defaults to sys.stdout.

    Raises:
        ValueError: If an invalid log level is provided.

    Example:
        # Development setup
        configure_logging(level="DEBUG")

        # Production setup
        configure_logging(level="INFO", use_structlog=True, json_output=True)

        # Test setup (capture logs)
        import io
        buffer = io.StringIO()
        configure_logging(level="DEBUG", stream=buffer)
    """
    global _configured, _use_structlog, _json_output

    # Validate log level
    numeric_level = getattr(logging, level.upper(), None)
    if not isinstance(numeric_level, int):
        raise ValueError(f"Invalid log level: {level}")

    stream = stream or sys.stdout
    _json_output = json_output

    structlog = _get_structlog() if use_structlog else None

    if structlog and use_structlog:
        _configure_structlog(structlog, level, json_output, stream)
        _use_structlog = True
    else:
        _configure_standard_logging(level, stream)
        _use_structlog = False
        if use_structlog and structlog is None:
            # Log warning about missing structlog
            logging.getLogger(__name__).warning(
                "structlog not installed, falling back to standard logging. "
                "Install with: pip install structlog"
            )

    _configured = True


def _configure_standard_logging(level: str, stream: Any) -> None:
    """Configure standard Python logging."""
    # Remove existing handlers from root logger
    root_logger = logging.getLogger()
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    # Create handler
    handler = logging.StreamHandler(stream)
    handler.setFormatter(
        logging.Formatter(fmt=DEFAULT_FORMAT, datefmt=DEFAULT_DATE_FORMAT)
    )

    # Configure root logger
    root_logger.setLevel(getattr(logging, level.upper()))
    root_logger.addHandler(handler)

    # Configure pipeline logger specifically
    pipeline_logger = logging.getLogger("mathpix_pipeline")
    pipeline_logger.setLevel(getattr(logging, level.upper()))


def _configure_structlog(
    structlog: Any,
    level: str,
    json_output: bool,
    stream: Any,
) -> None:
    """Configure structlog for structured logging."""
    # Configure standard logging first (structlog wraps it)
    _configure_standard_logging(level, stream)

    # Build processor chain
    processors = [
        # Add log level
        structlog.stdlib.add_log_level,
        # Add logger name
        structlog.stdlib.add_logger_name,
        # Add timestamp
        structlog.processors.TimeStamper(fmt="iso"),
        # Process stack info
        structlog.processors.StackInfoRenderer(),
        # Process exceptions
        structlog.processors.format_exc_info,
        # Convert to unicode
        structlog.processors.UnicodeDecoder(),
    ]

    if json_output:
        # JSON output for production
        processors.append(structlog.processors.JSONRenderer())
    else:
        # Console output for development
        processors.append(
            structlog.dev.ConsoleRenderer(
                colors=stream == sys.stdout and hasattr(stream, "isatty") and stream.isatty()
            )
        )

    structlog.configure(
        processors=processors,
        wrapper_class=structlog.stdlib.BoundLogger,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )


def get_logger(name: str) -> Any:
    """
    Get a configured logger for the given name.

    If logging has not been configured, automatically configures with defaults.

    Args:
        name: Logger name, typically __name__ of the calling module.

    Returns:
        A logger instance. Returns structlog.BoundLogger if structlog is
        configured, otherwise returns a standard logging.Logger.

    Example:
        logger = get_logger(__name__)
        logger.info("Processing started")
        logger.debug("Debug details", extra_key="extra_value")
    """
    global _configured

    if not _configured:
        configure_logging()

    if _use_structlog:
        structlog = _get_structlog()
        if structlog:
            return structlog.get_logger(name)

    return logging.getLogger(name)


class LoggerAdapter:
    """
    Adapter to provide consistent interface between standard and structlog loggers.

    This adapter wraps either a standard logging.Logger or a structlog.BoundLogger
    to provide a unified interface with structured logging capabilities.

    Example:
        adapter = LoggerAdapter(get_logger(__name__))
        adapter.info("Event occurred", user_id=123, action="login")
    """

    def __init__(self, logger: Any):
        """Initialize adapter with underlying logger."""
        self._logger = logger
        self._context: dict[str, Any] = {}

    def bind(self, **kwargs: Any) -> "LoggerAdapter":
        """
        Create a new adapter with bound context values.

        Args:
            **kwargs: Key-value pairs to bind to the logger context.

        Returns:
            New LoggerAdapter with bound values.
        """
        new_adapter = LoggerAdapter(self._logger)
        new_adapter._context = {**self._context, **kwargs}
        return new_adapter

    def _log(self, level: str, msg: str, **kwargs: Any) -> None:
        """Internal logging method."""
        combined = {**self._context, **kwargs}

        if _use_structlog:
            getattr(self._logger, level)(msg, **combined)
        else:
            if combined:
                extra_str = " ".join(f"{k}={v}" for k, v in combined.items())
                msg = f"{msg} [{extra_str}]"
            getattr(self._logger, level)(msg)

    def debug(self, msg: str, **kwargs: Any) -> None:
        """Log at DEBUG level."""
        self._log("debug", msg, **kwargs)

    def info(self, msg: str, **kwargs: Any) -> None:
        """Log at INFO level."""
        self._log("info", msg, **kwargs)

    def warning(self, msg: str, **kwargs: Any) -> None:
        """Log at WARNING level."""
        self._log("warning", msg, **kwargs)

    def error(self, msg: str, **kwargs: Any) -> None:
        """Log at ERROR level."""
        self._log("error", msg, **kwargs)

    def critical(self, msg: str, **kwargs: Any) -> None:
        """Log at CRITICAL level."""
        self._log("critical", msg, **kwargs)

    def exception(self, msg: str, **kwargs: Any) -> None:
        """Log at ERROR level with exception info."""
        self._log("exception", msg, **kwargs)


def get_adapted_logger(name: str) -> LoggerAdapter:
    """
    Get a LoggerAdapter for consistent structured logging interface.

    This provides a unified API regardless of whether structlog is enabled,
    allowing code to use structured logging patterns like:

        logger.info("Event", key=value)

    Args:
        name: Logger name, typically __name__ of the calling module.

    Returns:
        LoggerAdapter wrapping the configured logger.

    Example:
        logger = get_adapted_logger(__name__)
        logger = logger.bind(request_id="abc123")
        logger.info("Processing image", stage="ingestion", image_id="img_001")
    """
    return LoggerAdapter(get_logger(name))


def reset_logging() -> None:
    """
    Reset logging configuration to unconfigured state.

    Useful for testing or reconfiguring logging at runtime.
    """
    global _configured, _use_structlog, _json_output

    _configured = False
    _use_structlog = False
    _json_output = False

    # Reset root logger
    root_logger = logging.getLogger()
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)


__all__ = [
    # Configuration
    "configure_logging",
    "reset_logging",
    # Logger retrieval
    "get_logger",
    "get_adapted_logger",
    # Adapter
    "LoggerAdapter",
    # Constants
    "DEFAULT_LEVEL",
    "DEFAULT_FORMAT",
    "DEFAULT_DATE_FORMAT",
]
