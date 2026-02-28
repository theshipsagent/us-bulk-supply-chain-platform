"""
Logging configuration for the Interactive Barge Dashboard.

Provides structured logging with rotation, different levels per module,
and performance tracking.
"""

import logging
import logging.handlers
import sys
from pathlib import Path
from datetime import datetime
from typing import Optional

from src.config.settings import settings


def setup_logging(
    log_level: Optional[str] = None,
    log_file: Optional[str] = None,
    enable_console: bool = True,
    enable_file: bool = True
) -> logging.Logger:
    """
    Configure application logging.

    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Path to log file (defaults to settings.LOG_FILE)
        enable_console: Enable console (stdout) logging
        enable_file: Enable file logging with rotation

    Returns:
        Configured root logger
    """
    # Get log level from settings or parameter
    level_str = log_level or settings.LOG_LEVEL
    level = getattr(logging, level_str.upper(), logging.INFO)

    # Get log file path
    log_path = Path(log_file or settings.LOG_FILE)
    log_path.parent.mkdir(parents=True, exist_ok=True)

    # Create root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(level)

    # Remove existing handlers
    root_logger.handlers.clear()

    # Create formatter
    formatter = logging.Formatter(
        fmt='%(asctime)s | %(levelname)-8s | %(name)s:%(lineno)d | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # Console handler
    if enable_console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(level)
        console_handler.setFormatter(formatter)
        root_logger.addHandler(console_handler)

    # File handler with rotation
    if enable_file:
        # Rotating file handler: 10MB max, keep 5 backups
        file_handler = logging.handlers.RotatingFileHandler(
            filename=log_path,
            maxBytes=10 * 1024 * 1024,  # 10 MB
            backupCount=5,
            encoding='utf-8'
        )
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)

    return root_logger


def setup_module_loggers(custom_levels: Optional[dict[str, str]] = None):
    """
    Configure log levels for specific modules.

    Args:
        custom_levels: Dictionary mapping module names to log levels
                      e.g., {'src.engines': 'DEBUG', 'sqlalchemy': 'WARNING'}
    """
    default_levels = {
        'sqlalchemy.engine': 'WARNING',  # Reduce SQL query noise
        'urllib3': 'WARNING',  # Reduce HTTP noise
        'src.data_loaders': 'INFO',
        'src.engines': 'INFO',
        'src.api': 'INFO',
    }

    levels = {**default_levels, **(custom_levels or {})}

    for module_name, level_str in levels.items():
        logger = logging.getLogger(module_name)
        logger.setLevel(getattr(logging, level_str.upper(), logging.INFO))


class PerformanceLogger:
    """Context manager for logging execution time."""

    def __init__(self, operation_name: str, logger: Optional[logging.Logger] = None):
        """
        Initialize performance logger.

        Args:
            operation_name: Name of the operation to time
            logger: Logger instance (defaults to root logger)
        """
        self.operation_name = operation_name
        self.logger = logger or logging.getLogger(__name__)
        self.start_time: Optional[datetime] = None

    def __enter__(self):
        """Start timing."""
        self.start_time = datetime.now()
        self.logger.debug(f"Starting: {self.operation_name}")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """End timing and log duration."""
        if self.start_time:
            duration = (datetime.now() - self.start_time).total_seconds()
            if exc_type:
                self.logger.error(
                    f"Failed: {self.operation_name} (duration: {duration:.3f}s) - {exc_val}"
                )
            else:
                self.logger.info(
                    f"Completed: {self.operation_name} (duration: {duration:.3f}s)"
                )

        # Don't suppress exceptions
        return False


class StructuredLogger:
    """Logger with structured data support."""

    def __init__(self, name: str):
        """
        Initialize structured logger.

        Args:
            name: Logger name (usually __name__)
        """
        self.logger = logging.getLogger(name)

    def log_event(
        self,
        level: str,
        event: str,
        **kwargs
    ):
        """
        Log an event with structured data.

        Args:
            level: Log level (debug, info, warning, error, critical)
            event: Event description
            **kwargs: Additional structured data
        """
        # Format structured data
        extra_data = " | ".join(f"{k}={v}" for k, v in kwargs.items())
        message = f"{event} | {extra_data}" if extra_data else event

        # Log at appropriate level
        log_method = getattr(self.logger, level.lower(), self.logger.info)
        log_method(message)

    def debug(self, event: str, **kwargs):
        """Log debug event."""
        self.log_event('debug', event, **kwargs)

    def info(self, event: str, **kwargs):
        """Log info event."""
        self.log_event('info', event, **kwargs)

    def warning(self, event: str, **kwargs):
        """Log warning event."""
        self.log_event('warning', event, **kwargs)

    def error(self, event: str, **kwargs):
        """Log error event."""
        self.log_event('error', event, **kwargs)

    def critical(self, event: str, **kwargs):
        """Log critical event."""
        self.log_event('critical', event, **kwargs)


# Initialize default logging
def init_logging():
    """Initialize logging with default configuration."""
    setup_logging()
    setup_module_loggers()
    logging.getLogger(__name__).info("Logging initialized")


# Convenience function
def get_logger(name: str, structured: bool = False) -> logging.Logger | StructuredLogger:
    """
    Get a logger instance.

    Args:
        name: Logger name (usually __name__)
        structured: Return StructuredLogger instead of standard logger

    Returns:
        Logger instance
    """
    if structured:
        return StructuredLogger(name)
    return logging.getLogger(name)


if __name__ == "__main__":
    """Test logging configuration."""
    print("=" * 80)
    print("LOGGING CONFIGURATION TEST")
    print("=" * 80)

    # Initialize logging
    setup_logging(log_level='DEBUG')
    setup_module_loggers()

    logger = logging.getLogger(__name__)

    # Test different log levels
    print("\nTesting log levels:")
    logger.debug("This is a DEBUG message")
    logger.info("This is an INFO message")
    logger.warning("This is a WARNING message")
    logger.error("This is an ERROR message")

    # Test performance logger
    print("\nTesting performance logger:")
    with PerformanceLogger("test_operation", logger):
        import time
        time.sleep(0.1)

    # Test structured logger
    print("\nTesting structured logger:")
    structured = StructuredLogger(__name__)
    structured.info("route_computed", distance_miles=150.5, num_locks=3, cost_usd=1250.0)

    print("\n" + "=" * 80)
    print("✓ Logging test complete")
    print(f"✓ Log file: {settings.LOG_FILE}")
    print("=" * 80)
