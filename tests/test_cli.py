# Copyright 2014-now Equitania Software GmbH - Pforzheim - Germany
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

"""Comprehensive pytest tests for the CLI module odoo_fast_report_mapper._cli."""

import os
from unittest.mock import MagicMock, patch

import pytest
from click.testing import CliRunner

from odoo_fast_report_mapper.__version__ import __author__, __url__, __version__
from odoo_fast_report_mapper._cli import (
    print_banner,
    start_odoo_fast_report_mapper,
)


@pytest.fixture
def cli_runner():
    """Create a Click CliRunner for invoking CLI commands."""
    return CliRunner()


@pytest.fixture
def mock_connection():
    """Create a mock OdooConnection with configurable attributes."""
    conn = MagicMock()
    conn.collect_yaml = False
    conn.workflow = 0
    conn.disable_qweb = False
    conn.database = "test_db"
    conn.url = "https://test.odoo.com"
    conn.port = 443
    conn.username = "admin"
    conn.login.return_value = None
    conn.map_reports.return_value = []
    conn.test_fast_report_rendering.return_value = None
    conn.disable_qweb_reports.return_value = None
    conn.collect_all_report_entries.return_value = None
    return conn


class TestVersionOption:
    """Tests for the --version CLI option."""

    def test_version_option(self, cli_runner):
        """--version should display the current version."""
        result = cli_runner.invoke(start_odoo_fast_report_mapper, ["--version"])
        assert result.exit_code == 0
        assert __version__ in result.output


class TestInitFlag:
    """Tests for the --init CLI flag."""

    def test_init_flag_creates_env_template(self, cli_runner, tmp_path):
        """--init should generate a .env template in the current directory."""
        with cli_runner.isolated_filesystem(temp_dir=tmp_path):
            result = cli_runner.invoke(start_odoo_fast_report_mapper, ["--init"])
            assert result.exit_code == 0
            assert "Created .env template at:" in result.output
            assert "Edit the file with your Odoo connection details" in result.output
            assert os.path.exists(".env")

    def test_init_flag_existing_file_shows_warning(self, cli_runner, tmp_path):
        """--init should show a warning if .env already exists."""
        with cli_runner.isolated_filesystem(temp_dir=tmp_path):
            with open(".env", "w") as f:
                f.write("EXISTING=true\n")
            result = cli_runner.invoke(start_odoo_fast_report_mapper, ["--init"])
            assert result.exit_code == 0
            assert "Warning:" in result.output
            assert ".env file already exists" in result.output

    def test_init_flag_does_not_prompt_for_yaml_path(self, cli_runner, tmp_path):
        """--init is eager and should exit before prompting for yaml_path."""
        with cli_runner.isolated_filesystem(temp_dir=tmp_path):
            result = cli_runner.invoke(start_odoo_fast_report_mapper, ["--init"])
            assert result.exit_code == 0
            assert "Please enter the path to your YAML reports folder" not in result.output


class TestPrintBanner:
    """Tests for the print_banner() function."""

    def test_banner_output_contains_expected_strings(self):
        """print_banner should output version, author, and URL information."""
        import click

        runner = CliRunner()

        @click.command()
        def _banner_cmd():
            print_banner()

        result = runner.invoke(_banner_cmd)
        assert result.exit_code == 0
        assert __version__ in result.output
        assert __author__ in result.output
        assert __url__ in result.output
        assert "FastReport" in result.output
        assert "Mapping" in result.output or "Integration" in result.output


class TestWorkflow0Mapping:
    """Tests for workflow 0 (mapping only)."""

    @patch("odoo_fast_report_mapper._cli._utils")
    def test_workflow_0_calls_map_reports(self, mock_utils, cli_runner, mock_connection):
        """Workflow 0 should call map_reports and not test_fast_report_rendering."""
        mock_connection.workflow = 0
        mock_connection.collect_yaml = False
        mock_connection.disable_qweb = False
        mock_utils.create_connection_from_env.return_value = (mock_connection, "/fake/.env")
        mock_utils.collect_all_reports.return_value = [MagicMock()]

        result = cli_runner.invoke(
            start_odoo_fast_report_mapper,
            ["--yaml_path", "/tmp/fake_yaml"],
            input="y\n",
        )

        assert result.exit_code == 0
        mock_connection.login.assert_called_once()
        mock_utils.collect_all_reports.assert_called_once_with("/tmp/fake_yaml")
        mock_connection.map_reports.assert_called_once()
        mock_connection.test_fast_report_rendering.assert_not_called()


class TestWorkflow1Testing:
    """Tests for workflow 1 (testing only)."""

    @patch("odoo_fast_report_mapper._cli._utils")
    def test_workflow_1_calls_test_fast_report_rendering(self, mock_utils, cli_runner, mock_connection):
        """Workflow 1 should call test_fast_report_rendering and not map_reports."""
        mock_connection.workflow = 1
        mock_connection.collect_yaml = False
        mock_connection.disable_qweb = False
        mock_utils.create_connection_from_env.return_value = (mock_connection, "/fake/.env")
        mock_utils.collect_all_reports.return_value = [MagicMock()]

        result = cli_runner.invoke(
            start_odoo_fast_report_mapper,
            ["--yaml_path", "/tmp/fake_yaml"],
            input="y\n",
        )

        assert result.exit_code == 0
        mock_connection.login.assert_called_once()
        mock_connection.test_fast_report_rendering.assert_called_once()
        mock_connection.map_reports.assert_not_called()


class TestWorkflow2Both:
    """Tests for workflow 2 (mapping and testing)."""

    @patch("odoo_fast_report_mapper._cli._utils")
    def test_workflow_2_calls_both_map_and_test(self, mock_utils, cli_runner, mock_connection):
        """Workflow 2 should call both map_reports and test_fast_report_rendering."""
        mock_connection.workflow = 2
        mock_connection.collect_yaml = False
        mock_connection.disable_qweb = False
        mock_utils.create_connection_from_env.return_value = (mock_connection, "/fake/.env")
        mock_utils.collect_all_reports.return_value = [MagicMock()]

        result = cli_runner.invoke(
            start_odoo_fast_report_mapper,
            ["--yaml_path", "/tmp/fake_yaml"],
            input="y\n",
        )

        assert result.exit_code == 0
        mock_connection.login.assert_called_once()
        mock_connection.map_reports.assert_called_once()
        mock_connection.test_fast_report_rendering.assert_called_once()


class TestEnvError:
    """Tests for connection configuration errors."""

    @patch("odoo_fast_report_mapper._cli._utils")
    def test_env_error_missing_vars_message(self, mock_utils, cli_runner):
        """Missing-variable error must show the specific reason, not a generic 'init' hint."""
        mock_utils.create_connection_from_env.side_effect = ValueError(
            "Missing required environment variables in /tmp/x/.env: ODOO_URL, ODOO_PORT"
        )

        result = cli_runner.invoke(
            start_odoo_fast_report_mapper,
            ["--yaml_path", "/tmp/fake_yaml"],
        )

        assert result.exit_code == 0
        assert "Failed to load connection configuration" in result.output
        assert "missing one or more required entries" in result.output
        assert "ODOO_URL, ODOO_PORT" in result.output
        assert "odoo-fr-mapper --init" not in result.output

    @patch("odoo_fast_report_mapper._cli._utils")
    def test_env_error_file_not_found_recommends_init(self, mock_utils, cli_runner):
        """File-not-found error must recommend --init."""
        mock_utils.create_connection_from_env.side_effect = ValueError(".env file not found at: /tmp/nonexistent/.env")

        result = cli_runner.invoke(
            start_odoo_fast_report_mapper,
            ["--yaml_path", "/tmp/fake_yaml"],
        )

        assert result.exit_code == 0
        assert "Failed to load connection configuration" in result.output
        assert "odoo-fr-mapper --init" in result.output

    @patch("odoo_fast_report_mapper._cli._utils")
    def test_env_error_with_custom_env_path(self, mock_utils, cli_runner):
        """When env_path is given and config fails, the searched path should be shown."""
        mock_utils.create_connection_from_env.side_effect = ValueError(".env file not found")

        result = cli_runner.invoke(
            start_odoo_fast_report_mapper,
            ["--yaml_path", "/tmp/fake_yaml", "--env_path", "/custom/path/.env"],
        )

        assert result.exit_code == 0
        assert "Failed to load connection configuration" in result.output
        assert "/custom/path/.env" in result.output


class TestDisableQweb:
    """Tests for the disable_qweb behavior."""

    @patch("odoo_fast_report_mapper._cli._utils")
    def test_disable_qweb_called_when_enabled(self, mock_utils, cli_runner, mock_connection):
        """When connection.disable_qweb is True, disable_qweb_reports should be called."""
        mock_connection.workflow = 0
        mock_connection.collect_yaml = False
        mock_connection.disable_qweb = True
        mock_utils.create_connection_from_env.return_value = (mock_connection, "/fake/.env")
        mock_utils.collect_all_reports.return_value = [MagicMock()]

        result = cli_runner.invoke(
            start_odoo_fast_report_mapper,
            ["--yaml_path", "/tmp/fake_yaml"],
            input="y\n",
        )

        assert result.exit_code == 0
        mock_connection.disable_qweb_reports.assert_called_once()

    @patch("odoo_fast_report_mapper._cli._utils")
    def test_disable_qweb_not_called_when_disabled(self, mock_utils, cli_runner, mock_connection):
        """When connection.disable_qweb is False, disable_qweb_reports should not be called."""
        mock_connection.workflow = 0
        mock_connection.collect_yaml = False
        mock_connection.disable_qweb = False
        mock_utils.create_connection_from_env.return_value = (mock_connection, "/fake/.env")
        mock_utils.collect_all_reports.return_value = [MagicMock()]

        result = cli_runner.invoke(
            start_odoo_fast_report_mapper,
            ["--yaml_path", "/tmp/fake_yaml"],
            input="y\n",
        )

        assert result.exit_code == 0
        mock_connection.disable_qweb_reports.assert_not_called()


class TestCollectYaml:
    """Tests for the collect_yaml mode with interactive report selection."""

    @patch("odoo_fast_report_mapper._cli._utils")
    def test_collect_yaml_interactive_select_specific(self, mock_utils, cli_runner, mock_connection):
        """When collect_yaml is True, user can select specific reports interactively."""
        mock_connection.collect_yaml = True
        mock_connection.disable_qweb = False
        mock_connection.list_fast_reports.return_value = [
            {
                "id": 10,
                "report_name": "eq_fr_sale",
                "name": "Sales",
                "model": "sale.order",
                "company": "TestCo",
                "export_type": "pdf",
            },
            {
                "id": 20,
                "report_name": "eq_fr_invoice",
                "name": "Invoice",
                "model": "account.move",
                "company": "TestCo",
                "export_type": "pdf",
            },
            {
                "id": 30,
                "report_name": "eq_fr_picking",
                "name": "Picking",
                "model": "stock.picking",
                "company": "TestCo",
                "export_type": "pdf",
            },
        ]
        mock_utils.create_connection_from_env.return_value = (mock_connection, "/fake/.env")

        result = cli_runner.invoke(
            start_odoo_fast_report_mapper,
            ["--yaml_path", "/tmp/fake_yaml"],
            input="y\n1,3\n",
        )

        assert result.exit_code == 0
        mock_connection.collect_report_entries.assert_called_once_with("/tmp/fake_yaml", report_ids=[10, 30])
        mock_utils.collect_all_reports.assert_not_called()
        mock_connection.map_reports.assert_not_called()

    @patch("odoo_fast_report_mapper._cli._utils")
    def test_collect_yaml_interactive_select_all(self, mock_utils, cli_runner, mock_connection):
        """When collect_yaml is True and user selects 'all', all report IDs are passed."""
        mock_connection.collect_yaml = True
        mock_connection.disable_qweb = False
        mock_connection.list_fast_reports.return_value = [
            {
                "id": 10,
                "report_name": "eq_fr_sale",
                "name": "Sales",
                "model": "sale.order",
                "company": "TestCo",
                "export_type": "pdf",
            },
            {
                "id": 20,
                "report_name": "eq_fr_invoice",
                "name": "Invoice",
                "model": "account.move",
                "company": "TestCo",
                "export_type": "pdf",
            },
        ]
        mock_utils.create_connection_from_env.return_value = (mock_connection, "/fake/.env")

        result = cli_runner.invoke(
            start_odoo_fast_report_mapper,
            ["--yaml_path", "/tmp/fake_yaml"],
            input="y\nall\n",
        )

        assert result.exit_code == 0
        mock_connection.collect_report_entries.assert_called_once_with("/tmp/fake_yaml", report_ids=[10, 20])

    @patch("odoo_fast_report_mapper._cli._utils")
    def test_collect_yaml_no_reports_found(self, mock_utils, cli_runner, mock_connection):
        """When no FastReports exist, should show message and return."""
        mock_connection.collect_yaml = True
        mock_connection.disable_qweb = False
        mock_connection.list_fast_reports.return_value = []
        mock_utils.create_connection_from_env.return_value = (mock_connection, "/fake/.env")

        result = cli_runner.invoke(
            start_odoo_fast_report_mapper,
            ["--yaml_path", "/tmp/fake_yaml"],
            input="y\n",
        )

        assert result.exit_code == 0
        assert "No FastReport entries found" in result.output
        mock_connection.collect_report_entries.assert_not_called()

    @patch("odoo_fast_report_mapper._cli._utils")
    def test_collect_yaml_shows_table(self, mock_utils, cli_runner, mock_connection):
        """collect_yaml mode should display a table of available reports."""
        mock_connection.collect_yaml = True
        mock_connection.disable_qweb = False
        mock_connection.list_fast_reports.return_value = [
            {
                "id": 10,
                "report_name": "eq_fr_sale_order",
                "name": "Sales Order",
                "model": "sale.order",
                "company": "My Company",
                "export_type": "pdf",
            },
        ]
        mock_utils.create_connection_from_env.return_value = (mock_connection, "/fake/.env")

        result = cli_runner.invoke(
            start_odoo_fast_report_mapper,
            ["--yaml_path", "/tmp/fake_yaml"],
            input="y\nall\n",
        )

        assert result.exit_code == 0
        assert "Found 1 FastReport(s)" in result.output
        assert "eq_fr_sale_order" in result.output
        assert "sale.order" in result.output
        assert "My Company" in result.output

    @patch("odoo_fast_report_mapper._cli._utils")
    def test_collect_yaml_default_is_all(self, mock_utils, cli_runner, mock_connection):
        """Pressing Enter without input should default to 'all'."""
        mock_connection.collect_yaml = True
        mock_connection.disable_qweb = False
        mock_connection.list_fast_reports.return_value = [
            {
                "id": 10,
                "report_name": "eq_fr_sale",
                "name": "Sales",
                "model": "sale.order",
                "company": "TestCo",
                "export_type": "pdf",
            },
        ]
        mock_utils.create_connection_from_env.return_value = (mock_connection, "/fake/.env")

        result = cli_runner.invoke(
            start_odoo_fast_report_mapper,
            ["--yaml_path", "/tmp/fake_yaml"],
            input="y\n\n",
        )

        assert result.exit_code == 0
        mock_connection.collect_report_entries.assert_called_once_with("/tmp/fake_yaml", report_ids=[10])


class TestSelectFlag:
    """Tests for the --select flag for interactive YAML report selection."""

    @patch("odoo_fast_report_mapper._cli._utils")
    def test_select_flag_shows_table(self, mock_utils, cli_runner, mock_connection):
        """--select should display a table of available YAML reports."""
        mock_connection.collect_yaml = False
        mock_connection.workflow = 0
        mock_connection.disable_qweb = False
        mock_utils.create_connection_from_env.return_value = (mock_connection, "/fake/.env")
        mock_utils.list_yaml_reports.return_value = [
            {
                "filename": "eq_fr_sale_order.yaml",
                "report_name": "eq_fr_core_sale_order",
                "model": "sale.order",
                "yaml_object": {"report_name": "eq_fr_core_sale_order"},
            },
        ]
        mock_utils.build_reports_from_yaml_objects.return_value = []

        result = cli_runner.invoke(
            start_odoo_fast_report_mapper,
            ["--yaml_path", "/tmp/fake_yaml", "--select"],
            input="y\nall\n",
        )

        assert result.exit_code == 0
        assert "Found 1 YAML report(s)" in result.output
        assert "eq_fr_sale_order.yaml" in result.output
        assert "eq_fr_core_sale_order" in result.output
        assert "sale.order" in result.output

    @patch("odoo_fast_report_mapper._cli._utils")
    def test_select_flag_specific_indices(self, mock_utils, cli_runner, mock_connection):
        """--select with '1,3' should pass only selected YAML dicts to build_reports."""
        mock_connection.collect_yaml = False
        mock_connection.workflow = 0
        mock_connection.disable_qweb = False
        mock_utils.create_connection_from_env.return_value = (mock_connection, "/fake/.env")

        yaml1 = {"report_name": "eq_fr_sale"}
        yaml2 = {"report_name": "eq_fr_invoice"}
        yaml3 = {"report_name": "eq_fr_picking"}

        mock_utils.list_yaml_reports.return_value = [
            {"filename": "sale.yaml", "report_name": "eq_fr_sale", "model": "sale.order", "yaml_object": yaml1},
            {"filename": "invoice.yaml", "report_name": "eq_fr_invoice", "model": "account.move", "yaml_object": yaml2},
            {
                "filename": "picking.yaml",
                "report_name": "eq_fr_picking",
                "model": "stock.picking",
                "yaml_object": yaml3,
            },
        ]
        mock_utils.build_reports_from_yaml_objects.return_value = []

        result = cli_runner.invoke(
            start_odoo_fast_report_mapper,
            ["--yaml_path", "/tmp/fake_yaml", "--select"],
            input="y\n1,3\n",
        )

        assert result.exit_code == 0
        mock_utils.build_reports_from_yaml_objects.assert_called_once_with([yaml1, yaml3])
        mock_utils.collect_all_reports.assert_not_called()

    @patch("odoo_fast_report_mapper._cli._utils")
    def test_select_flag_default_all(self, mock_utils, cli_runner, mock_connection):
        """Pressing Enter (default 'all') should process all reports."""
        mock_connection.collect_yaml = False
        mock_connection.workflow = 0
        mock_connection.disable_qweb = False
        mock_utils.create_connection_from_env.return_value = (mock_connection, "/fake/.env")

        yaml1 = {"report_name": "eq_fr_sale"}
        yaml2 = {"report_name": "eq_fr_invoice"}

        mock_utils.list_yaml_reports.return_value = [
            {"filename": "sale.yaml", "report_name": "eq_fr_sale", "model": "sale.order", "yaml_object": yaml1},
            {"filename": "invoice.yaml", "report_name": "eq_fr_invoice", "model": "account.move", "yaml_object": yaml2},
        ]
        mock_utils.build_reports_from_yaml_objects.return_value = []

        result = cli_runner.invoke(
            start_odoo_fast_report_mapper,
            ["--yaml_path", "/tmp/fake_yaml", "--select"],
            input="y\n\n",
        )

        assert result.exit_code == 0
        mock_utils.build_reports_from_yaml_objects.assert_called_once_with([yaml1, yaml2])

    @patch("odoo_fast_report_mapper._cli._utils")
    def test_select_flag_invalid_input_aborts(self, mock_utils, cli_runner, mock_connection):
        """Invalid input should show error and abort without processing."""
        mock_connection.collect_yaml = False
        mock_connection.workflow = 0
        mock_connection.disable_qweb = False
        mock_utils.create_connection_from_env.return_value = (mock_connection, "/fake/.env")
        mock_utils.list_yaml_reports.return_value = [
            {"filename": "sale.yaml", "report_name": "eq_fr_sale", "model": "sale.order", "yaml_object": {}},
        ]

        result = cli_runner.invoke(
            start_odoo_fast_report_mapper,
            ["--yaml_path", "/tmp/fake_yaml", "--select"],
            input="y\nabc\n",
        )

        assert result.exit_code == 0
        assert "Invalid selection" in result.output
        mock_utils.build_reports_from_yaml_objects.assert_not_called()
        mock_connection.map_reports.assert_not_called()

    @patch("odoo_fast_report_mapper._cli._utils")
    def test_select_flag_no_reports_found(self, mock_utils, cli_runner, mock_connection):
        """When no YAML files exist, should show message and return."""
        mock_connection.collect_yaml = False
        mock_connection.workflow = 0
        mock_connection.disable_qweb = False
        mock_utils.create_connection_from_env.return_value = (mock_connection, "/fake/.env")
        mock_utils.list_yaml_reports.return_value = []

        result = cli_runner.invoke(
            start_odoo_fast_report_mapper,
            ["--yaml_path", "/tmp/fake_yaml", "--select"],
            input="y\n",
        )

        assert result.exit_code == 0
        assert "No YAML report files found" in result.output
        mock_connection.map_reports.assert_not_called()

    @patch("odoo_fast_report_mapper._cli._utils")
    def test_without_select_flag_processes_all(self, mock_utils, cli_runner, mock_connection):
        """Without --select, all reports should be processed without interactive prompt."""
        mock_connection.collect_yaml = False
        mock_connection.workflow = 0
        mock_connection.disable_qweb = False
        mock_utils.create_connection_from_env.return_value = (mock_connection, "/fake/.env")
        mock_utils.collect_all_reports.return_value = []

        result = cli_runner.invoke(
            start_odoo_fast_report_mapper,
            ["--yaml_path", "/tmp/fake_yaml"],
            input="y\n",
        )

        assert result.exit_code == 0
        mock_utils.collect_all_reports.assert_called_once_with("/tmp/fake_yaml")
        mock_utils.list_yaml_reports.assert_not_called()


class TestSuccessOutput:
    """Tests for successful completion output."""

    @patch("odoo_fast_report_mapper._cli._utils")
    def test_success_message_displayed(self, mock_utils, cli_runner, mock_connection):
        """On successful completion, the CLI should display a success message."""
        mock_connection.workflow = 0
        mock_connection.collect_yaml = False
        mock_connection.disable_qweb = False
        mock_utils.create_connection_from_env.return_value = (mock_connection, "/fake/.env")
        mock_utils.collect_all_reports.return_value = []

        result = cli_runner.invoke(
            start_odoo_fast_report_mapper,
            ["--yaml_path", "/tmp/fake_yaml"],
            input="y\n",
        )

        assert result.exit_code == 0
        assert "All operations completed successfully" in result.output


class TestConnectionConfirmation:
    """Tests for the connection confirmation prompt."""

    @patch("odoo_fast_report_mapper._cli._utils")
    def test_confirmation_denied_aborts(self, mock_utils, cli_runner, mock_connection):
        """When user denies confirmation, CLI should abort without login."""
        mock_utils.create_connection_from_env.return_value = (mock_connection, "/fake/.env")

        result = cli_runner.invoke(
            start_odoo_fast_report_mapper,
            ["--yaml_path", "/tmp/fake_yaml"],
            input="n\n",
        )

        assert result.exit_code == 0
        assert "Aborted" in result.output
        mock_connection.login.assert_not_called()
        mock_connection.map_reports.assert_not_called()

    @patch("odoo_fast_report_mapper._cli._utils")
    def test_confirmation_shows_connection_details(self, mock_utils, cli_runner, mock_connection):
        """Confirmation prompt should display .env path, server, database, user, workflow."""
        mock_utils.create_connection_from_env.return_value = (mock_connection, "/path/to/.env")
        mock_utils.collect_all_reports.return_value = []

        result = cli_runner.invoke(
            start_odoo_fast_report_mapper,
            ["--yaml_path", "/tmp/fake_yaml"],
            input="y\n",
        )

        assert result.exit_code == 0
        assert "Connection Summary" in result.output
        assert "/path/to/.env" in result.output
        assert "https://test.odoo.com" in result.output
        assert "443" in result.output
        assert "test_db" in result.output
        assert "admin" in result.output
        assert "Mapping only" in result.output


class TestFailedReportsSummary:
    """Tests for the failed reports summary output."""

    @patch("odoo_fast_report_mapper._cli._utils")
    def test_failed_reports_shows_summary(self, mock_utils, cli_runner, mock_connection):
        """When map_reports returns failures, a summary should be displayed."""
        mock_connection.workflow = 0
        mock_connection.collect_yaml = False
        mock_connection.disable_qweb = False
        mock_connection.map_reports.return_value = [
            ("eq_fr_core_account_move", "Report on Print Button flag error"),
        ]
        mock_utils.create_connection_from_env.return_value = (mock_connection, "/fake/.env")
        mock_utils.collect_all_reports.return_value = [MagicMock()]

        result = cli_runner.invoke(
            start_odoo_fast_report_mapper,
            ["--yaml_path", "/tmp/fake_yaml"],
            input="y\n",
        )

        assert result.exit_code == 0
        assert "1 of 1 report(s) failed" in result.output
        assert "eq_fr_core_account_move" in result.output
        assert "--select" in result.output

    @patch("odoo_fast_report_mapper._cli._utils")
    def test_no_failures_no_summary(self, mock_utils, cli_runner, mock_connection):
        """When all reports succeed, no failure summary should be shown."""
        mock_connection.workflow = 0
        mock_connection.collect_yaml = False
        mock_connection.disable_qweb = False
        mock_connection.map_reports.return_value = []
        mock_utils.create_connection_from_env.return_value = (mock_connection, "/fake/.env")
        mock_utils.collect_all_reports.return_value = [MagicMock()]

        result = cli_runner.invoke(
            start_odoo_fast_report_mapper,
            ["--yaml_path", "/tmp/fake_yaml"],
            input="y\n",
        )

        assert result.exit_code == 0
        assert "report(s) failed" not in result.output
        assert "All operations completed successfully" in result.output
