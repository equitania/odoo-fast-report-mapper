# -*- coding: utf-8 -*-
# Copyright 2014-now Equitania Software GmbH - Pforzheim - Germany
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

"""
Centralized logging configuration for odoo-fast-report-mapper.

This module provides:
- Structured logging with configurable levels
- Colored console output for better readability
- Log rotation to manage file sizes
- Progress bar integration for long operations
"""

import logging
import logging.handlers
import sys
from pathlib import Path
from typing import Optional
import os


# ANSI color codes for console output
class LogColors:
    """ANSI escape codes for colored terminal output."""
    RESET = '\033[0m'
    BOLD = '\033[1m'

    # Standard colors
    BLACK = '\033[0;30m'
    RED = '\033[0;31m'
    GREEN = '\033[0;32m'
    YELLOW = '\033[0;33m'
    BLUE = '\033[0;34m'
    MAGENTA = '\033[0;35m'
    CYAN = '\033[0;36m'
    WHITE = '\033[0;37m'

    # Bold colors
    BOLD_RED = '\033[1;31m'
    BOLD_GREEN = '\033[1;32m'
    BOLD_YELLOW = '\033[1;33m'
    BOLD_BLUE = '\033[1;34m'


class ColoredFormatter(logging.Formatter):
    """Custom formatter that adds colors to log levels."""

    COLORS = {
        'DEBUG': LogColors.CYAN,
        'INFO': LogColors.GREEN,
        'WARNING': LogColors.YELLOW,
        'ERROR': LogColors.RED,
        'CRITICAL': LogColors.BOLD_RED,
    }

    def format(self, record):
        """Format log record with color."""
        # Save original levelname
        levelname = record.levelname

        # Add color to levelname
        if levelname in self.COLORS:
            record.levelname = f"{self.COLORS[levelname]}{levelname}{LogColors.RESET}"

        # Format the message
        result = super().format(record)

        # Restore original levelname for other handlers
        record.levelname = levelname

        return result


class LoggerManager:
    """
    Centralized logger management for the application.

    Features:
    - Configurable log levels
    - Console and file handlers
    - Automatic log rotation
    - Colored console output
    """

    _instance: Optional['LoggerManager'] = None
    _loggers: dict = {}

    def __new__(cls):
        """Singleton pattern to ensure only one instance exists."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        """Initialize the logger manager."""
        if self._initialized:
            return

        self._initialized = True
        self._log_dir = Path.home() / '.odoo-fast-report-mapper' / 'logs'
        self._log_level = logging.INFO
        self._console_handler = None
        self._file_handler = None

    def setup_logger(
        self,
        name: str = 'odoo_fast_report_mapper',
        level: int = logging.INFO,
        log_to_file: bool = True,
        log_to_console: bool = True,
        max_bytes: int = 10 * 1024 * 1024,  # 10MB
        backup_count: int = 5,
        colored_output: bool = True
    ) -> logging.Logger:
        """
        Setup and configure a logger instance.

        Args:
            name: Logger name
            level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
            log_to_file: Enable file logging
            log_to_console: Enable console logging
            max_bytes: Maximum size of log file before rotation
            backup_count: Number of backup files to keep
            colored_output: Enable colored console output

        Returns:
            Configured logger instance
        """
        # Return existing logger if already configured
        if name in self._loggers:
            return self._loggers[name]

        # Create logger
        logger = logging.getLogger(name)
        logger.setLevel(level)
        logger.propagate = False

        # Remove existing handlers
        logger.handlers.clear()

        # Create formatters
        console_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        file_format = '%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s'
        date_format = '%H:%M:%S %d.%m.%Y'

        # Console handler
        if log_to_console:
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setLevel(level)

            if colored_output and sys.stdout.isatty():
                formatter = ColoredFormatter(console_format, datefmt=date_format)
            else:
                formatter = logging.Formatter(console_format, datefmt=date_format)

            console_handler.setFormatter(formatter)
            logger.addHandler(console_handler)
            self._console_handler = console_handler

        # File handler with rotation
        if log_to_file:
            # Create log directory if it doesn't exist
            self._log_dir.mkdir(parents=True, exist_ok=True)

            log_file = self._log_dir / f'{name}.log'
            file_handler = logging.handlers.RotatingFileHandler(
                log_file,
                maxBytes=max_bytes,
                backupCount=backup_count,
                encoding='utf-8'
            )
            file_handler.setLevel(level)
            file_formatter = logging.Formatter(file_format, datefmt=date_format)
            file_handler.setFormatter(file_formatter)
            logger.addHandler(file_handler)
            self._file_handler = file_handler

        # Store logger
        self._loggers[name] = logger

        return logger

    def get_logger(self, name: str = 'odoo_fast_report_mapper') -> logging.Logger:
        """
        Get or create a logger instance.

        Args:
            name: Logger name

        Returns:
            Logger instance
        """
        if name not in self._loggers:
            return self.setup_logger(name)
        return self._loggers[name]

    def set_level(self, level: int):
        """
        Set logging level for all loggers.

        Args:
            level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        """
        self._log_level = level
        for logger in self._loggers.values():
            logger.setLevel(level)
            for handler in logger.handlers:
                handler.setLevel(level)

    def get_log_file_path(self) -> Path:
        """Get the path to the current log file."""
        return self._log_dir / 'odoo_fast_report_mapper.log'


# Singleton instance
_manager = LoggerManager()


def get_logger(name: str = 'odoo_fast_report_mapper') -> logging.Logger:
    """
    Get a configured logger instance.

    This is the main function to use for getting loggers in the application.

    Args:
        name: Logger name (default: 'odoo_fast_report_mapper')

    Returns:
        Configured logger instance

    Example:
        >>> from odoo_fast_report_mapper.logging_config import get_logger
        >>> logger = get_logger(__name__)
        >>> logger.info("Processing report...")
        >>> logger.error("Failed to process report")
    """
    return _manager.get_logger(name)


def setup_logging(
    level: int = logging.INFO,
    log_to_file: bool = True,
    log_to_console: bool = True,
    colored_output: bool = True
) -> logging.Logger:
    """
    Setup logging configuration for the application.

    Args:
        level: Logging level
        log_to_file: Enable file logging
        log_to_console: Enable console logging
        colored_output: Enable colored console output

    Returns:
        Root logger instance
    """
    return _manager.setup_logger(
        'odoo_fast_report_mapper',
        level=level,
        log_to_file=log_to_file,
        log_to_console=log_to_console,
        colored_output=colored_output
    )


def set_log_level(level: int):
    """
    Set the logging level globally.

    Args:
        level: Logging level (logging.DEBUG, INFO, WARNING, ERROR, CRITICAL)
    """
    _manager.set_level(level)


def get_log_file_path() -> Path:
    """Get the path to the current log file."""
    return _manager.get_log_file_path()


# Convenience functions for common log levels
def enable_debug_logging():
    """Enable DEBUG level logging."""
    set_log_level(logging.DEBUG)


def enable_verbose_logging():
    """Enable INFO level logging (verbose)."""
    set_log_level(logging.INFO)


def enable_quiet_logging():
    """Enable WARNING level logging (quiet mode)."""
    set_log_level(logging.WARNING)
