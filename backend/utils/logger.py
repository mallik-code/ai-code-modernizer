"""Unified structured logging for the AI Code Modernizer."""
import structlog
import logging
from rich.logging import RichHandler
from pathlib import Path
import atexit


# Global configuration to ensure logging is set up only once
_logs_dir = Path("logs")
_logs_dir.mkdir(exist_ok=True)

# Set up a single file handler for all application logs
_file_handler = logging.FileHandler(_logs_dir / "application.log")
_file_formatter = logging.Formatter(
    "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
_file_handler.setFormatter(_file_formatter)

# Set up console handler for real-time output
_console_handler = RichHandler(rich_tracebacks=True)

# Configure the root logger with both handlers
logging.basicConfig(
    level="INFO",
    format="%(message)s",
    handlers=[_console_handler, _file_handler],
    force=True  # Ensure we override any previous configuration
)

# Configure structlog with our unified logging approach
structlog.configure(
    processors=[
        structlog.contextvars.merge_contextvars,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.add_log_level,
        structlog.processors.StackInfoRenderer(),
        structlog.dev.ConsoleRenderer()
    ],
    wrapper_class=structlog.make_filtering_bound_logger(logging.INFO),
    context_class=dict,
    logger_factory=structlog.PrintLoggerFactory(),
)


def setup_logger(name: str, level: str = "INFO"):
    """Setup structured logger with unified output to single log file."""
    logger = structlog.get_logger(name)
    return logger