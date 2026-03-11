# Copyright 2014-now Equitania Software GmbH - Pforzheim - Germany
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

"""Tests for odoo_report_helper/odoo_connection.py - OdooConnection class."""

import urllib.error
from unittest.mock import MagicMock, patch

import pytest

from odoo_report_helper.exceptions import OdooConnectionError
from odoo_report_helper.odoo_connection import OdooConnection

# ---------------------------------------------------------------------------
# Constructor tests
# ---------------------------------------------------------------------------


class TestOdooConnectionConstructor:
    """Verify constructor calls prepare_connection and handles errors."""

    @patch("odoo_report_helper.odoo_connection.utils.prepare_connection")
    def test_constructor_calls_prepare_connection(self, mock_prepare):
        """Constructor must call prepare_connection with url and port."""
        mock_connection = MagicMock()
        mock_prepare.return_value = mock_connection

        conn = OdooConnection(
            url="https://odoo.example.com",
            port=443,
            username="admin",
            password="secret",
            database="test_db",
        )

        mock_prepare.assert_called_once_with("https://odoo.example.com", 443)
        assert conn.connection is mock_connection
        assert conn.username == "admin"
        assert conn.password == "secret"
        assert conn.database == "test_db"
        assert conn.version == ""

    @patch("odoo_report_helper.odoo_connection.utils.prepare_connection")
    def test_constructor_raises_odoo_connection_error_on_url_error(self, mock_prepare):
        """Constructor must raise OdooConnectionError when URLError occurs."""
        mock_prepare.side_effect = urllib.error.URLError("Connection refused")

        with pytest.raises(OdooConnectionError, match="Please check your parameters"):
            OdooConnection(
                url="https://invalid.example.com",
                port=443,
                username="admin",
                password="secret",
                database="test_db",
            )


# ---------------------------------------------------------------------------
# login() tests
# ---------------------------------------------------------------------------


class TestOdooConnectionLogin:
    """Verify login behavior and error handling."""

    @patch("odoo_report_helper.odoo_connection.utils.prepare_connection")
    def test_login_calls_connection_login_and_sets_config(self, mock_prepare):
        """login() must call connection.login and set auto_commit, context flags."""
        mock_connection = MagicMock()
        mock_connection.version = "18.0"
        mock_connection.config = {}
        mock_connection.env.context = {}
        mock_prepare.return_value = mock_connection

        conn = OdooConnection(
            url="https://odoo.example.com",
            port=443,
            username="admin",
            password="secret",
            database="test_db",
        )
        conn.login()

        mock_connection.login.assert_called_once_with("test_db", "admin", "secret")
        assert mock_connection.config["auto_commit"] is True
        assert mock_connection.env.context["active_test"] is False
        assert mock_connection.env.context["tracking_disable"] is True
        assert conn.version == "18"

    @patch("odoo_report_helper.odoo_connection.utils.prepare_connection")
    def test_login_raises_odoo_connection_error_on_rpc_error(self, mock_prepare):
        """login() must raise OdooConnectionError when RPCError occurs."""
        from odoorpc_toolbox import RPCError

        mock_connection = MagicMock()
        mock_connection.login.side_effect = RPCError("Invalid credentials")
        mock_prepare.return_value = mock_connection

        conn = OdooConnection(
            url="https://odoo.example.com",
            port=443,
            username="admin",
            password="wrong",
            database="test_db",
        )

        with pytest.raises(OdooConnectionError, match="Please check your parameters"):
            conn.login()


# ---------------------------------------------------------------------------
# check_module() tests
# ---------------------------------------------------------------------------


class TestCheckModule:
    """Verify module installation checks."""

    @patch("odoo_report_helper.odoo_connection.utils.prepare_connection")
    def test_check_module_returns_true_when_installed(self, mock_prepare):
        """check_module must return True when module is found."""
        mock_connection = MagicMock()
        mock_ir_module = MagicMock()
        mock_ir_module.search.return_value = [42]
        mock_connection.env.__getitem__ = lambda self, key: mock_ir_module
        mock_prepare.return_value = mock_connection

        conn = OdooConnection("https://odoo.example.com", 443, "admin", "secret", "test_db")
        result = conn.check_module("sale")

        assert result is True
        mock_ir_module.search.assert_called_once_with([("state", "=", "installed"), ("name", "=", "sale")])

    @patch("odoo_report_helper.odoo_connection.utils.prepare_connection")
    def test_check_module_returns_false_when_not_installed(self, mock_prepare):
        """check_module must return False when module is not found."""
        mock_connection = MagicMock()
        mock_ir_module = MagicMock()
        mock_ir_module.search.return_value = []
        mock_connection.env.__getitem__ = lambda self, key: mock_ir_module
        mock_prepare.return_value = mock_connection

        conn = OdooConnection("https://odoo.example.com", 443, "admin", "secret", "test_db")
        result = conn.check_module("nonexistent_module")

        assert result is False


# ---------------------------------------------------------------------------
# check_dependencies() tests
# ---------------------------------------------------------------------------


class TestCheckDependencies:
    """Verify dependency checking across multiple modules."""

    @patch("odoo_report_helper.odoo_connection.utils.prepare_connection")
    def test_check_dependencies_returns_true_when_all_installed(self, mock_prepare):
        """check_dependencies must return True when all modules are installed."""
        mock_connection = MagicMock()
        mock_ir_module = MagicMock()
        mock_ir_module.search.return_value = [1]
        mock_connection.env.__getitem__ = lambda self, key: mock_ir_module
        mock_prepare.return_value = mock_connection

        conn = OdooConnection("https://odoo.example.com", 443, "admin", "secret", "test_db")
        result = conn.check_dependencies(["sale", "account", "stock"])

        assert result is True

    @patch("odoo_report_helper.odoo_connection.utils.prepare_connection")
    def test_check_dependencies_returns_false_when_one_missing(self, mock_prepare):
        """check_dependencies must return False when any module is missing."""
        mock_connection = MagicMock()
        mock_ir_module = MagicMock()
        # First module installed, second not installed
        mock_ir_module.search.side_effect = [[1], []]
        mock_connection.env.__getitem__ = lambda self, key: mock_ir_module
        mock_prepare.return_value = mock_connection

        conn = OdooConnection("https://odoo.example.com", 443, "admin", "secret", "test_db")
        result = conn.check_dependencies(["sale", "missing_module"])

        assert result is False

    @patch("odoo_report_helper.odoo_connection.utils.prepare_connection")
    def test_check_dependencies_returns_true_for_empty_list(self, mock_prepare):
        """check_dependencies must return True for empty dependency list."""
        mock_connection = MagicMock()
        mock_prepare.return_value = mock_connection

        conn = OdooConnection("https://odoo.example.com", 443, "admin", "secret", "test_db")
        result = conn.check_dependencies([])

        assert result is True

    @patch("odoo_report_helper.odoo_connection.utils.prepare_connection")
    def test_check_dependencies_returns_true_for_none(self, mock_prepare):
        """check_dependencies must return True when dependencies is None."""
        mock_connection = MagicMock()
        mock_prepare.return_value = mock_connection

        conn = OdooConnection("https://odoo.example.com", 443, "admin", "secret", "test_db")
        result = conn.check_dependencies(None)

        assert result is True


# ---------------------------------------------------------------------------
# _search_report() tests
# ---------------------------------------------------------------------------


class TestSearchReport:
    """Verify report search behavior."""

    @patch("odoo_report_helper.odoo_connection.utils.prepare_connection")
    def test_search_report_returns_report_id(self, mock_prepare):
        """_search_report must return the first report ID when found."""
        mock_connection = MagicMock()
        mock_ir_report = MagicMock()
        mock_ir_report.search.return_value = [42, 43]
        mock_connection.env.__getitem__ = lambda self, key: mock_ir_report
        mock_prepare.return_value = mock_connection

        conn = OdooConnection("https://odoo.example.com", 443, "admin", "secret", "test_db")
        result = conn._search_report("sale.order", "Sales Order")

        assert result == 42

    @patch("odoo_report_helper.odoo_connection.utils.prepare_connection")
    def test_search_report_returns_false_when_not_found(self, mock_prepare):
        """_search_report must return False when no reports are found."""
        mock_connection = MagicMock()
        mock_ir_report = MagicMock()
        mock_ir_report.search.return_value = []
        mock_connection.env.__getitem__ = lambda self, key: mock_ir_report
        mock_prepare.return_value = mock_connection

        conn = OdooConnection("https://odoo.example.com", 443, "admin", "secret", "test_db")
        result = conn._search_report("sale.order", "Nonexistent Report")

        assert result is False


# ---------------------------------------------------------------------------
# _get_fast_report_ids() tests
# ---------------------------------------------------------------------------


class TestGetFastReportIds:
    """Verify retrieval of FastReport IDs."""

    @patch("odoo_report_helper.odoo_connection.utils.prepare_connection")
    def test_get_fast_report_ids_returns_list(self, mock_prepare):
        """_get_fast_report_ids must return list of report IDs with report_type=fast_report."""
        mock_connection = MagicMock()
        mock_ir_report = MagicMock()
        mock_ir_report.search.return_value = [1, 5, 10]
        mock_connection.env.__getitem__ = lambda self, key: mock_ir_report
        mock_prepare.return_value = mock_connection

        conn = OdooConnection("https://odoo.example.com", 443, "admin", "secret", "test_db")
        result = conn._get_fast_report_ids()

        assert result == [1, 5, 10]
        mock_ir_report.search.assert_called_once_with([("report_type", "=", "fast_report")])

    @patch("odoo_report_helper.odoo_connection.utils.prepare_connection")
    def test_get_fast_report_ids_returns_empty_list(self, mock_prepare):
        """_get_fast_report_ids must return empty list when no FastReports exist."""
        mock_connection = MagicMock()
        mock_ir_report = MagicMock()
        mock_ir_report.search.return_value = []
        mock_connection.env.__getitem__ = lambda self, key: mock_ir_report
        mock_prepare.return_value = mock_connection

        conn = OdooConnection("https://odoo.example.com", 443, "admin", "secret", "test_db")
        result = conn._get_fast_report_ids()

        assert result == []
