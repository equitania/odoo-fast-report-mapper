# Copyright 2014-now Equitania Software GmbH - Pforzheim - Germany
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

"""Tests for odoo_fast_report_mapper._exceptions - Custom exception classes."""

import pytest

from odoo_fast_report_mapper import OdooConnectionError, PathDoesNotExistError, PathDoesNotExitError

# ---------------------------------------------------------------------------
# OdooConnectionError tests
# ---------------------------------------------------------------------------


class TestOdooConnectionError:
    """Verify OdooConnectionError behavior."""

    def test_can_be_raised_and_caught(self):
        """OdooConnectionError must be raisable and catchable."""
        with pytest.raises(OdooConnectionError):
            raise OdooConnectionError("Connection failed")

    def test_inherits_from_exception(self):
        """OdooConnectionError must inherit from Exception."""
        assert issubclass(OdooConnectionError, Exception)

    def test_error_message_is_preserved(self):
        """OdooConnectionError must preserve the error message."""
        error = OdooConnectionError("Test error message")
        assert str(error) == "Test error message"

    def test_can_be_caught_as_exception(self):
        """OdooConnectionError must be catchable as generic Exception."""
        with pytest.raises(Exception, match="Caught as Exception"):
            raise OdooConnectionError("Caught as Exception")

    def test_empty_message(self):
        """OdooConnectionError must work with empty message."""
        error = OdooConnectionError()
        assert str(error) == ""

    def test_message_with_special_characters(self):
        """OdooConnectionError must handle UTF-8 characters in message."""
        msg = "Verbindungsfehler: Server nicht erreichbar"
        error = OdooConnectionError(msg)
        assert str(error) == msg


# ---------------------------------------------------------------------------
# PathDoesNotExitError tests
# ---------------------------------------------------------------------------


class TestPathDoesNotExitError:
    """Verify PathDoesNotExitError behavior."""

    def test_can_be_raised_and_caught(self):
        """PathDoesNotExitError must be raisable and catchable."""
        with pytest.raises(PathDoesNotExitError):
            raise PathDoesNotExitError("Path not found")

    def test_inherits_from_exception(self):
        """PathDoesNotExitError must inherit from Exception."""
        assert issubclass(PathDoesNotExitError, Exception)

    def test_error_message_is_preserved(self):
        """PathDoesNotExitError must preserve the error message."""
        error = PathDoesNotExitError("/invalid/path/to/yaml")
        assert str(error) == "/invalid/path/to/yaml"

    def test_can_be_caught_as_exception(self):
        """PathDoesNotExitError must be catchable as generic Exception."""
        with pytest.raises(Exception, match="Caught as Exception"):
            raise PathDoesNotExitError("Caught as Exception")

    def test_empty_message(self):
        """PathDoesNotExitError must work with empty message."""
        error = PathDoesNotExitError()
        assert str(error) == ""

    def test_message_with_path(self):
        """PathDoesNotExitError must handle path strings correctly."""
        path = "/home/user/yaml_reports/config.yaml"
        error = PathDoesNotExitError(path)
        assert str(error) == path


# ---------------------------------------------------------------------------
# PathDoesNotExistError tests (alias)
# ---------------------------------------------------------------------------


class TestPathDoesNotExistError:
    """Verify PathDoesNotExistError (corrected spelling alias) behavior."""

    def test_can_be_raised_and_caught(self):
        with pytest.raises(PathDoesNotExistError):
            raise PathDoesNotExistError("Path not found")

    def test_inherits_from_exception(self):
        assert issubclass(PathDoesNotExistError, Exception)


# ---------------------------------------------------------------------------
# Cross-exception tests
# ---------------------------------------------------------------------------


class TestExceptionIndependence:
    """Verify that exceptions are independent from each other."""

    def test_odoo_error_not_caught_as_path_error(self):
        """OdooConnectionError must not be caught as PathDoesNotExitError."""
        with pytest.raises(OdooConnectionError):
            try:
                raise OdooConnectionError("connection error")
            except PathDoesNotExitError:
                pytest.fail("OdooConnectionError should not be caught as PathDoesNotExitError")

    def test_path_error_not_caught_as_odoo_error(self):
        """PathDoesNotExitError must not be caught as OdooConnectionError."""
        with pytest.raises(PathDoesNotExitError):
            try:
                raise PathDoesNotExitError("path error")
            except OdooConnectionError:
                pytest.fail("PathDoesNotExitError should not be caught as OdooConnectionError")

    def test_both_catchable_as_base_exception(self):
        """Both exceptions must be catchable as base Exception."""
        for exc_cls in [OdooConnectionError, PathDoesNotExitError]:
            try:
                raise exc_cls("test")
            except Exception as e:
                assert str(e) == "test"
