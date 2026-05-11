# Copyright 2014-now Equitania Software GmbH - Pforzheim - Germany
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

"""Tests for odoo_fast_report_mapper/logging_config.py - Logging configuration."""

import logging

import pytest

from odoo_fast_report_mapper import logging_config as _logging_module
from odoo_fast_report_mapper.logging_config import (
    ColoredFormatter,
    LogColors,
    LoggerManager,
    enable_debug_logging,
    enable_quiet_logging,
    enable_verbose_logging,
    get_logger,
    set_log_level,
    setup_logging,
)

# ---------------------------------------------------------------------------
# Fixture to reset LoggerManager singleton between tests
# ---------------------------------------------------------------------------


def _clear_manager_loggers(manager):
    """Clear logger cache and any attached handlers on a LoggerManager instance."""
    if manager is None:
        return
    for _name, logger_obj in list(manager._loggers.items()):
        logger_obj.handlers.clear()
    manager._loggers.clear()


@pytest.fixture(autouse=True)
def reset_logger_manager():
    """Reset LoggerManager singleton state before each test."""
    _clear_manager_loggers(LoggerManager._instance)
    _clear_manager_loggers(_logging_module._manager)
    yield
    _clear_manager_loggers(LoggerManager._instance)
    _clear_manager_loggers(_logging_module._manager)


# ---------------------------------------------------------------------------
# get_logger() tests
# ---------------------------------------------------------------------------


class TestGetLogger:
    """Verify get_logger returns a properly configured logger."""

    def test_get_logger_returns_logger(self):
        """get_logger must return a logging.Logger instance."""
        logger = get_logger("test_module")
        assert isinstance(logger, logging.Logger)

    def test_get_logger_returns_same_logger_for_same_name(self):
        """get_logger must return the same logger for the same name."""
        logger1 = get_logger("test_module")
        logger2 = get_logger("test_module")
        assert logger1 is logger2

    def test_get_logger_returns_different_loggers_for_different_names(self):
        """get_logger must return different loggers for different names."""
        logger1 = get_logger("module_a")
        logger2 = get_logger("module_b")
        assert logger1 is not logger2

    def test_get_logger_default_name(self):
        """get_logger must use default name when none provided."""
        logger = get_logger()
        assert logger.name == "odoo_fast_report_mapper"


# ---------------------------------------------------------------------------
# setup_logging() tests
# ---------------------------------------------------------------------------


class TestSetupLogging:
    """Verify setup_logging configures logger correctly."""

    def test_setup_logging_returns_logger(self):
        """setup_logging must return a logging.Logger instance."""
        logger = setup_logging(level=logging.INFO, log_to_file=False)
        assert isinstance(logger, logging.Logger)

    def test_setup_logging_sets_correct_level(self):
        """setup_logging must set the requested logging level."""
        logger = setup_logging(level=logging.DEBUG, log_to_file=False)
        assert logger.level == logging.DEBUG

    def test_setup_logging_info_level(self):
        """setup_logging must configure INFO level correctly."""
        logger = setup_logging(level=logging.INFO, log_to_file=False)
        assert logger.level == logging.INFO

    def test_setup_logging_warning_level(self):
        """setup_logging must configure WARNING level correctly."""
        logger = setup_logging(level=logging.WARNING, log_to_file=False)
        assert logger.level == logging.WARNING

    def test_setup_logging_adds_console_handler(self):
        """setup_logging must add a console handler by default."""
        logger = setup_logging(log_to_file=False, log_to_console=True)
        handler_types = [type(h).__name__ for h in logger.handlers]
        assert "StreamHandler" in handler_types

    def test_setup_logging_no_console_handler_when_disabled(self):
        """setup_logging must not add console handler when disabled."""
        logger = setup_logging(log_to_file=False, log_to_console=False)
        assert len(logger.handlers) == 0


# ---------------------------------------------------------------------------
# set_log_level() tests
# ---------------------------------------------------------------------------


class TestSetLogLevel:
    """Verify set_log_level changes level for all loggers."""

    def test_set_log_level_changes_all_loggers(self):
        """set_log_level must change level for all registered loggers."""
        logger1 = get_logger("logger_a")
        logger2 = get_logger("logger_b")

        set_log_level(logging.ERROR)

        assert logger1.level == logging.ERROR
        assert logger2.level == logging.ERROR

    def test_set_log_level_changes_handler_levels(self):
        """set_log_level must also update handler levels."""
        logger = setup_logging(level=logging.INFO, log_to_file=False, log_to_console=True)

        set_log_level(logging.DEBUG)

        for handler in logger.handlers:
            assert handler.level == logging.DEBUG


# ---------------------------------------------------------------------------
# LoggerManager singleton tests
# ---------------------------------------------------------------------------


class TestLoggerManagerSingleton:
    """Verify LoggerManager singleton behavior."""

    def test_singleton_returns_same_instance(self):
        """LoggerManager must return the same instance each time."""
        manager1 = LoggerManager()
        manager2 = LoggerManager()
        assert manager1 is manager2

    def test_singleton_initialized_once(self):
        """LoggerManager must only initialize once."""
        manager1 = LoggerManager()
        manager1._test_marker = "initialized"
        manager2 = LoggerManager()
        assert hasattr(manager2, "_test_marker")
        assert manager2._test_marker == "initialized"

    def test_reset_singleton_allows_new_instance(self):
        """After resetting singleton state, a new instance can be created."""
        LoggerManager()
        LoggerManager._instance = None
        LoggerManager._loggers = {}
        manager2 = LoggerManager()
        # Both are LoggerManager instances but different objects
        assert isinstance(manager2, LoggerManager)


# ---------------------------------------------------------------------------
# ColoredFormatter tests
# ---------------------------------------------------------------------------


class TestColoredFormatter:
    """Verify ColoredFormatter adds color codes when applicable."""

    def test_colored_formatter_formats_info(self):
        """ColoredFormatter must add green color to INFO level."""
        formatter = ColoredFormatter("%(levelname)s - %(message)s")
        record = logging.LogRecord(
            name="test", level=logging.INFO, pathname="", lineno=0, msg="Test message", args=(), exc_info=None
        )

        result = formatter.format(record)

        assert "Test message" in result
        # The original levelname should be restored after formatting
        assert record.levelname == "INFO"

    def test_colored_formatter_formats_error(self):
        """ColoredFormatter must add red color to ERROR level."""
        formatter = ColoredFormatter("%(levelname)s - %(message)s")
        record = logging.LogRecord(
            name="test", level=logging.ERROR, pathname="", lineno=0, msg="Error message", args=(), exc_info=None
        )

        result = formatter.format(record)

        assert "Error message" in result
        assert record.levelname == "ERROR"

    def test_colored_formatter_formats_warning(self):
        """ColoredFormatter must add yellow color to WARNING level."""
        formatter = ColoredFormatter("%(levelname)s - %(message)s")
        record = logging.LogRecord(
            name="test", level=logging.WARNING, pathname="", lineno=0, msg="Warning message", args=(), exc_info=None
        )

        result = formatter.format(record)

        assert "Warning message" in result
        assert record.levelname == "WARNING"

    def test_colored_formatter_formats_debug(self):
        """ColoredFormatter must add cyan color to DEBUG level."""
        formatter = ColoredFormatter("%(levelname)s - %(message)s")
        record = logging.LogRecord(
            name="test", level=logging.DEBUG, pathname="", lineno=0, msg="Debug message", args=(), exc_info=None
        )

        result = formatter.format(record)

        assert "Debug message" in result
        assert record.levelname == "DEBUG"

    def test_colored_formatter_contains_color_codes(self):
        """ColoredFormatter output must contain ANSI color escape codes."""
        formatter = ColoredFormatter("%(levelname)s - %(message)s")
        record = logging.LogRecord(
            name="test", level=logging.INFO, pathname="", lineno=0, msg="Test", args=(), exc_info=None
        )

        result = formatter.format(record)

        # The formatted output should contain ANSI escape codes
        assert "\033[" in result
        assert LogColors.RESET in result

    def test_colored_formatter_restores_original_levelname(self):
        """ColoredFormatter must restore original levelname after formatting."""
        formatter = ColoredFormatter("%(levelname)s")
        record = logging.LogRecord(
            name="test", level=logging.CRITICAL, pathname="", lineno=0, msg="Critical", args=(), exc_info=None
        )

        formatter.format(record)

        assert record.levelname == "CRITICAL"


# ---------------------------------------------------------------------------
# Convenience function tests
# ---------------------------------------------------------------------------


class TestConvenienceFunctions:
    """Verify convenience logging level functions."""

    def test_enable_debug_logging_sets_debug(self):
        """enable_debug_logging must set level to DEBUG."""
        logger = get_logger("test_debug")
        enable_debug_logging()
        assert logger.level == logging.DEBUG

    def test_enable_verbose_logging_sets_info(self):
        """enable_verbose_logging must set level to INFO."""
        logger = get_logger("test_verbose")
        enable_verbose_logging()
        assert logger.level == logging.INFO

    def test_enable_quiet_logging_sets_warning(self):
        """enable_quiet_logging must set level to WARNING."""
        logger = get_logger("test_quiet")
        enable_quiet_logging()
        assert logger.level == logging.WARNING
