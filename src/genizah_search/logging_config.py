"""
Centralized logging configuration for the Genizah Search application.

This module provides a consistent logging setup across all modules with support for:
- File and console logging handlers
- Rotating log files to prevent disk space issues
- Configurable log levels for development and production
- Structured logging with timestamps and context
- Performance tracking and error reporting
"""

import logging
import logging.handlers
import os
from pathlib import Path
from typing import Optional


def setup_logging(
    log_level: Optional[str] = None,
    log_file: Optional[str] = None,
    log_to_console: bool = True,
    log_to_file: bool = True,
    max_file_size: int = 10 * 1024 * 1024,  # 10 MB
    backup_count: int = 5,
) -> None:
    """
    Configure logging for the application.

    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL).
                  Defaults to environment variable LOG_LEVEL or INFO.
        log_file: Path to log file. Defaults to logs/genizah_search.log
        log_to_console: Whether to output logs to console (default: True)
        log_to_file: Whether to output logs to file (default: True)
        max_file_size: Maximum size of each log file in bytes (default: 10MB)
        backup_count: Number of backup log files to keep (default: 5)
    """
    # Determine log level from environment or parameter
    if log_level is None:
        log_level = os.getenv("LOG_LEVEL", "INFO").upper()
    else:
        log_level = log_level.upper()

    # Validate log level
    valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
    if log_level not in valid_levels:
        log_level = "INFO"

    # Convert string to logging constant
    numeric_level = getattr(logging, log_level)

    # Create logs directory if it doesn't exist
    if log_file is None:
        log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)
        log_file = log_dir / "genizah_search.log"
    else:
        log_file = Path(log_file)
        log_file.parent.mkdir(parents=True, exist_ok=True)

    # Create formatter with detailed information
    formatter = logging.Formatter(
        fmt="%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Get root logger and configure it
    root_logger = logging.getLogger()
    root_logger.setLevel(numeric_level)

    # Remove existing handlers to avoid duplicates
    root_logger.handlers.clear()

    # Add console handler if requested
    if log_to_console:
        console_handler = logging.StreamHandler()
        console_handler.setLevel(numeric_level)
        console_handler.setFormatter(formatter)
        root_logger.addHandler(console_handler)

    # Add rotating file handler if requested
    if log_to_file:
        file_handler = logging.handlers.RotatingFileHandler(
            log_file,
            maxBytes=max_file_size,
            backupCount=backup_count,
            encoding="utf-8",
        )
        file_handler.setLevel(numeric_level)
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)

    # Log the initialization
    logging.info(
        f"Logging initialized: level={log_level}, console={log_to_console}, "
        f"file={log_to_file}, file_path={log_file}"
    )


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance for a specific module.

    Args:
        name: Name of the module (typically __name__)

    Returns:
        logging.Logger: Configured logger instance
    """
    return logging.getLogger(name)


def log_performance(logger: logging.Logger, operation: str, duration: float) -> None:
    """
    Log performance metrics for an operation.

    Args:
        logger: Logger instance to use
        operation: Name/description of the operation
        duration: Duration in seconds
    """
    logger.info(f"Performance: {operation} completed in {duration:.3f}s")


def log_error_with_context(logger: logging.Logger, error: Exception, context: dict) -> None:
    """
    Log an error with additional context information.

    Args:
        logger: Logger instance to use
        error: Exception that occurred
        context: Dictionary with contextual information
    """
    context_str = ", ".join(f"{k}={v}" for k, v in context.items())
    logger.error(f"Error: {type(error).__name__}: {error} | Context: {context_str}")


def log_search_query(
    logger: logging.Logger,
    query: str,
    search_type: str,
    result_count: int,
    duration: float,
) -> None:
    """
    Log a search query with its results and performance.

    Args:
        logger: Logger instance to use
        query: Search query string
        search_type: Type of search (fulltext, docid, regex)
        result_count: Number of results returned
        duration: Query execution time in seconds
    """
    logger.info(
        f"Search: type={search_type}, query='{query}', "
        f"results={result_count}, duration={duration:.3f}s"
    )


def log_http_request(
    logger: logging.Logger,
    method: str,
    path: str,
    status_code: int,
    duration: Optional[float] = None,
) -> None:
    """
    Log an HTTP request with response details.

    Args:
        logger: Logger instance to use
        method: HTTP method (GET, POST, etc.)
        path: Request path
        status_code: HTTP status code
        duration: Request processing time in seconds (optional)
    """
    duration_str = f", duration={duration:.3f}s" if duration else ""
    logger.info(f"HTTP: {method} {path} - {status_code}{duration_str}")
