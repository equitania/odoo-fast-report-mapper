# Copyright 2014-now Equitania Software GmbH - Pforzheim - Germany
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

"""Comprehensive tests for odoo_fast_report_mapper.eq_utils module."""

import os
from unittest.mock import patch

import pytest
import yaml

from odoo_fast_report_mapper import eq_utils
from odoo_fast_report_mapper.eq_odoo_connection import EqOdooConnection
from odoo_fast_report_mapper.eq_report import EqReport
from odoo_report_helper.exceptions import PathDoesNotExitError

# ---------------------------------------------------------------------------
# generate_env_template
# ---------------------------------------------------------------------------


class TestGenerateEnvTemplate:
    """Tests for generate_env_template()."""

    def test_creates_env_file_in_target_dir(self, tmp_path):
        """Template file is created in the given target directory."""
        result = eq_utils.generate_env_template(target_dir=str(tmp_path))
        expected_path = os.path.join(str(tmp_path), ".env")
        assert result == expected_path
        assert os.path.exists(expected_path)

    def test_env_file_contains_template_content(self, tmp_path):
        """Generated .env file contains the expected template content."""
        eq_utils.generate_env_template(target_dir=str(tmp_path))
        env_path = os.path.join(str(tmp_path), ".env")
        with open(env_path, encoding="utf-8") as f:
            content = f.read()
        assert "ODOO_URL=" in content
        assert "ODOO_PORT=" in content
        assert "ODOO_DATABASE=" in content
        assert "ODOO_LANGUAGE=" in content

    def test_raises_file_exists_error_when_env_already_exists(self, tmp_path):
        """FileExistsError is raised if .env already exists in target dir."""
        # Create .env first
        env_file = tmp_path / ".env"
        env_file.write_text("existing content")
        with pytest.raises(FileExistsError, match=".env file already exists"):
            eq_utils.generate_env_template(target_dir=str(tmp_path))

    def test_defaults_to_cwd_when_no_target_dir(self, tmp_path, monkeypatch):
        """When target_dir is None, the current working directory is used."""
        monkeypatch.chdir(tmp_path)
        result = eq_utils.generate_env_template(target_dir=None)
        expected = os.path.join(str(tmp_path), ".env")
        assert result == expected
        assert os.path.exists(expected)


# ---------------------------------------------------------------------------
# create_report_object_from_yaml_object
# ---------------------------------------------------------------------------


class TestCreateReportObjectFromYamlObject:
    """Tests for create_report_object_from_yaml_object()."""

    def test_creates_valid_report_object(self, sample_report_yaml_data):
        """EqReport is created with all fields from YAML data."""
        report = eq_utils.create_report_object_from_yaml_object(sample_report_yaml_data)
        assert isinstance(report, EqReport)
        assert report.entry_name == {"de_DE": "Verkaufsauftrag", "en_US": "Sales_Order"}
        assert report.report_name == "eq_fr_core_sale_order"
        assert report.report_type == "fast_report"
        assert report.model_name == "sale.order"
        assert report.eq_export_type == "pdf"
        assert report.multi is False
        assert report._dependencies == ["sale", "account"]

    def test_company_id_defaults_to_false_when_missing(self, sample_report_yaml_data):
        """company_id defaults to False when not present in YAML data."""
        # Ensure there is no company_id key
        sample_report_yaml_data.pop("company_id", None)
        report = eq_utils.create_report_object_from_yaml_object(sample_report_yaml_data)
        assert report.company_id is False

    def test_company_id_set_when_present(self, sample_report_yaml_data_with_company):
        """company_id is correctly assigned when provided in YAML data."""
        report = eq_utils.create_report_object_from_yaml_object(sample_report_yaml_data_with_company)
        assert report.company_id == [1, 3]

    def test_legacy_name_keys_normalized(self, sample_report_yaml_data_legacy):
        """Legacy ger/eng keys are normalized to de_DE/en_US."""
        report = eq_utils.create_report_object_from_yaml_object(sample_report_yaml_data_legacy)
        assert isinstance(report, EqReport)
        assert "de_DE" in report.entry_name
        assert "en_US" in report.entry_name
        assert report.entry_name["de_DE"] == "Verkaufsauftrag"
        assert report.entry_name["en_US"] == "Sales_Order"

    def test_report_fields_and_calculated_fields(self, sample_report_yaml_data):
        """Report fields and calculated fields are passed through correctly."""
        report = eq_utils.create_report_object_from_yaml_object(sample_report_yaml_data)
        assert "sale.order" in report._fields
        assert "payment_text" in report._calculated_fields


# ---------------------------------------------------------------------------
# create_odoo_connection_from_yaml_object
# ---------------------------------------------------------------------------


class TestCreateOdooConnectionFromYamlObject:
    """Tests for create_odoo_connection_from_yaml_object()."""

    def test_creates_valid_connection(self, sample_connection_yaml_data, mock_odoorpc):
        """EqOdooConnection is created with correct attributes from YAML."""
        conn = eq_utils.create_odoo_connection_from_yaml_object(sample_connection_yaml_data)
        assert isinstance(conn, EqOdooConnection)
        # Legacy 'ger' is normalized to 'de_DE'
        assert conn.language == "de_DE"
        assert conn.collect_yaml is False
        assert conn.disable_qweb is True
        assert conn.workflow == 0
        assert conn.database == "test_db"
        assert conn.username == "admin"

    def test_optional_fields_default_values(self, mock_odoorpc):
        """Optional fields use defaults when not specified in YAML."""
        minimal_yaml = {
            "Server": {
                "url": "https://odoo.example.com",
                "port": 443,
                "user": "admin",
                "password": "secret",
                "database": "mydb",
                "language": "eng",
            }
        }
        conn = eq_utils.create_odoo_connection_from_yaml_object(minimal_yaml)
        assert conn.collect_yaml is False
        assert conn.disable_qweb is True
        assert conn.workflow == 0


# ---------------------------------------------------------------------------
# convert_all_yaml_objects
# ---------------------------------------------------------------------------


class TestConvertAllYamlObjects:
    """Tests for convert_all_yaml_objects()."""

    def test_converts_list_using_function(self):
        """Each element in the list is converted through the given function."""
        items = [1, 2, 3]
        result = eq_utils.convert_all_yaml_objects(items, lambda x: x * 10)
        assert result == [10, 20, 30]

    def test_empty_list_returns_empty(self):
        """An empty input list produces an empty output list."""
        result = eq_utils.convert_all_yaml_objects([], lambda x: x)
        assert result == []

    def test_preserves_order(self):
        """Output order matches input order."""
        items = ["c", "a", "b"]
        result = eq_utils.convert_all_yaml_objects(items, str.upper)
        assert result == ["C", "A", "B"]


# ---------------------------------------------------------------------------
# collect_all_reports
# ---------------------------------------------------------------------------


class TestCollectAllReports:
    """Tests for collect_all_reports()."""

    def test_collects_reports_from_yaml_directory(self, tmp_yaml_dir):
        """Reports are correctly loaded from YAML files in a directory."""
        reports = eq_utils.collect_all_reports(str(tmp_yaml_dir))
        assert len(reports) == 1
        assert isinstance(reports[0], EqReport)
        assert reports[0].report_name == "eq_fr_test"

    def test_multi_company_splitting(self, tmp_path):
        """A report with multiple company_ids is split into separate report objects."""
        yaml_dir = tmp_path / "mc_reports"
        yaml_dir.mkdir()
        report_data = {
            "name": {"de_DE": "MC_Report", "en_US": "MC_Report"},
            "report_name": "eq_fr_mc",
            "report_type": "fast_report",
            "print_report_name": "MC",
            "report_model": "account.move",
            "company_id": [1, 3, 5],
            "eq_export_type": "pdf",
            "eq_ignore_images": True,
            "eq_handling_html_fields": "standard",
            "eq_multiprint": "standard",
            "multi": False,
            "attachment": "MC.pdf",
            "attachment_use": False,
            "eq_print_button": False,
            "dependencies": ["account"],
            "report_fields": {"account.move": ["id", "name"]},
            "calculated_fields": {},
        }
        with open(yaml_dir / "mc_report.yaml", "w") as f:
            yaml.dump(report_data, f)

        reports = eq_utils.collect_all_reports(str(yaml_dir))
        assert len(reports) == 3
        company_ids = [r.company_id for r in reports]
        assert [1] in company_ids
        assert [3] in company_ids
        assert [5] in company_ids

    def test_single_company_not_split(self, tmp_path):
        """A report with a single company_id is not split."""
        yaml_dir = tmp_path / "sc_reports"
        yaml_dir.mkdir()
        report_data = {
            "name": {"de_DE": "SC_Report", "en_US": "SC_Report"},
            "report_name": "eq_fr_sc",
            "report_type": "fast_report",
            "print_report_name": "SC",
            "report_model": "sale.order",
            "company_id": [2],
            "eq_export_type": "pdf",
            "eq_ignore_images": True,
            "eq_handling_html_fields": "standard",
            "eq_multiprint": "standard",
            "multi": False,
            "attachment": "SC.pdf",
            "attachment_use": False,
            "eq_print_button": False,
            "dependencies": ["sale"],
            "report_fields": {"sale.order": ["id"]},
            "calculated_fields": {},
        }
        with open(yaml_dir / "sc_report.yaml", "w") as f:
            yaml.dump(report_data, f)

        reports = eq_utils.collect_all_reports(str(yaml_dir))
        assert len(reports) == 1
        assert reports[0].company_id == [2]

    def test_invalid_path_raises_error(self):
        """PathDoesNotExitError is raised for a non-existent directory."""
        with pytest.raises(PathDoesNotExitError):
            eq_utils.collect_all_reports("/nonexistent/path/that/does/not/exist")


# ---------------------------------------------------------------------------
# create_connection_from_env
# ---------------------------------------------------------------------------


class TestCreateConnectionFromEnv:
    """Tests for create_connection_from_env()."""

    @staticmethod
    def _clear_odoo_env_vars(monkeypatch):
        """Remove all ODOO_* environment variables to prevent test pollution."""
        for key in list(os.environ.keys()):
            if key.startswith("ODOO_"):
                monkeypatch.delenv(key, raising=False)

    def test_from_explicit_env_file_path(self, tmp_env_file, mock_odoorpc, monkeypatch):
        """Connection is created from an explicit .env file path."""
        self._clear_odoo_env_vars(monkeypatch)
        conn = eq_utils.create_connection_from_env(env_path=str(tmp_env_file))
        assert isinstance(conn, EqOdooConnection)
        assert conn.database == "test_db"
        assert conn.username == "admin"
        # Legacy 'ger' is normalized to 'de_DE'
        assert conn.language == "de_DE"

    def test_from_directory_path(self, tmp_env_file, mock_odoorpc, monkeypatch):
        """Connection is created when env_path points to a directory containing .env."""
        self._clear_odoo_env_vars(monkeypatch)
        conn = eq_utils.create_connection_from_env(env_path=str(tmp_env_file.parent))
        assert isinstance(conn, EqOdooConnection)
        assert conn.database == "test_db"

    def test_missing_required_vars_raises_value_error(self, tmp_path, mock_odoorpc, monkeypatch):
        """ValueError is raised when required environment variables are missing."""
        self._clear_odoo_env_vars(monkeypatch)
        env_file = tmp_path / ".env"
        # Only provide partial variables - missing ODOO_PASSWORD, ODOO_DATABASE, ODOO_LANGUAGE
        env_file.write_text("ODOO_URL=https://test.com\nODOO_PORT=443\nODOO_USER=admin\n")
        with pytest.raises(ValueError, match="Missing required environment variables"):
            eq_utils.create_connection_from_env(env_path=str(env_file))

    def test_optional_defaults(self, tmp_path, mock_odoorpc, monkeypatch):
        """Optional variables use correct defaults when not specified."""
        self._clear_odoo_env_vars(monkeypatch)
        env_content = (
            "ODOO_URL=https://test.com\n"
            "ODOO_PORT=8069\n"
            "ODOO_USER=admin\n"
            "ODOO_PASSWORD=pw\n"
            "ODOO_DATABASE=mydb\n"
            "ODOO_LANGUAGE=en_US\n"
        )
        env_file = tmp_path / ".env"
        env_file.write_text(env_content)
        conn = eq_utils.create_connection_from_env(env_path=str(env_file))
        assert conn.collect_yaml is False
        assert conn.disable_qweb is True
        assert conn.workflow == 0

    def test_env_file_not_found_raises_value_error(self, tmp_path, mock_odoorpc, monkeypatch):
        """ValueError is raised when the specified .env file does not exist."""
        self._clear_odoo_env_vars(monkeypatch)
        with pytest.raises(ValueError, match=".env file not found"):
            eq_utils.create_connection_from_env(env_path=str(tmp_path / "nonexistent.env"))

    def test_boolean_env_parsing(self, tmp_path, mock_odoorpc, monkeypatch):
        """Boolean environment variables are correctly parsed from string values."""
        self._clear_odoo_env_vars(monkeypatch)
        env_content = (
            "ODOO_URL=https://test.com\n"
            "ODOO_PORT=443\n"
            "ODOO_USER=admin\n"
            "ODOO_PASSWORD=pw\n"
            "ODOO_DATABASE=db\n"
            "ODOO_LANGUAGE=ger\n"
            "ODOO_COLLECT_YAML=True\n"
            "ODOO_DISABLE_QWEB=False\n"
            "ODOO_WORKFLOW=2\n"
        )
        env_file = tmp_path / ".env"
        env_file.write_text(env_content)
        conn = eq_utils.create_connection_from_env(env_path=str(env_file))
        assert conn.collect_yaml is True
        assert conn.disable_qweb is False
        assert conn.workflow == 2

    def test_invalid_port_non_numeric_raises_value_error(self, tmp_path, mock_odoorpc, monkeypatch):
        """ValueError is raised when ODOO_PORT is not a valid number."""
        self._clear_odoo_env_vars(monkeypatch)
        env_content = (
            "ODOO_URL=https://test.com\n"
            "ODOO_PORT=abc\n"
            "ODOO_USER=admin\n"
            "ODOO_PASSWORD=pw\n"
            "ODOO_DATABASE=db\n"
            "ODOO_LANGUAGE=en_US\n"
        )
        env_file = tmp_path / ".env"
        env_file.write_text(env_content)
        with pytest.raises(ValueError, match="Invalid ODOO_PORT"):
            eq_utils.create_connection_from_env(env_path=str(env_file))

    def test_invalid_port_out_of_range_raises_value_error(self, tmp_path, mock_odoorpc, monkeypatch):
        """ValueError is raised when ODOO_PORT is outside valid range."""
        self._clear_odoo_env_vars(monkeypatch)
        env_content = (
            "ODOO_URL=https://test.com\n"
            "ODOO_PORT=99999\n"
            "ODOO_USER=admin\n"
            "ODOO_PASSWORD=pw\n"
            "ODOO_DATABASE=db\n"
            "ODOO_LANGUAGE=en_US\n"
        )
        env_file = tmp_path / ".env"
        env_file.write_text(env_content)
        with pytest.raises(ValueError, match="Invalid ODOO_PORT"):
            eq_utils.create_connection_from_env(env_path=str(env_file))


# ---------------------------------------------------------------------------
# collect_all_connections (deprecated)
# ---------------------------------------------------------------------------


class TestCollectAllConnections:
    """Tests for collect_all_connections() - deprecated function."""

    def test_returns_connection_objects(self, tmp_path, mock_odoorpc):
        """Connections are correctly loaded from YAML files in a directory."""
        yaml_dir = tmp_path / "connections"
        yaml_dir.mkdir()
        conn_data = {
            "Server": {
                "url": "https://odoo.test.com",
                "port": 443,
                "user": "admin",
                "password": "secret",
                "database": "testdb",
                "language": "ger",
            }
        }
        with open(yaml_dir / "conn.yaml", "w") as f:
            yaml.dump(conn_data, f)

        connections = eq_utils.collect_all_connections(str(yaml_dir))
        assert len(connections) == 1
        assert isinstance(connections[0], EqOdooConnection)
        assert connections[0].database == "testdb"

    def test_emits_deprecation_warning_in_logs(self, tmp_path, mock_odoorpc):
        """The function logs a deprecation warning."""
        yaml_dir = tmp_path / "conn_warn"
        yaml_dir.mkdir()
        conn_data = {
            "Server": {
                "url": "https://odoo.test.com",
                "port": 443,
                "user": "admin",
                "password": "pw",
                "database": "db",
                "language": "eng",
            }
        }
        with open(yaml_dir / "conn.yaml", "w") as f:
            yaml.dump(conn_data, f)

        with patch("odoo_fast_report_mapper.eq_utils.logger") as mock_logger:
            eq_utils.collect_all_connections(str(yaml_dir))
            mock_logger.warning.assert_called_once()
            warning_msg = mock_logger.warning.call_args[0][0]
            assert "deprecated" in warning_msg.lower()

    def test_invalid_path_raises_error(self, mock_odoorpc):
        """PathDoesNotExitError is raised for a non-existent directory."""
        with pytest.raises(PathDoesNotExitError):
            eq_utils.collect_all_connections("/nonexistent/connection/path")


# ---------------------------------------------------------------------------
# list_yaml_reports
# ---------------------------------------------------------------------------


class TestListYamlReports:
    """Tests for list_yaml_reports()."""

    def test_returns_metadata_for_each_yaml(self, tmp_path):
        """Each YAML file should produce a dict with filename, report_name, model."""
        yaml_dir = tmp_path / "reports"
        yaml_dir.mkdir()
        report_data = {
            "name": {"de_DE": "Test"},
            "report_name": "eq_fr_sale",
            "report_model": "sale.order",
            "report_type": "fast_report",
        }
        with open(yaml_dir / "sale.yaml", "w") as f:
            yaml.dump(report_data, f)

        result = eq_utils.list_yaml_reports(str(yaml_dir))
        assert len(result) == 1
        assert result[0]["filename"] == "sale.yaml"
        assert result[0]["report_name"] == "eq_fr_sale"
        assert result[0]["model"] == "sale.order"
        assert "yaml_object" in result[0]

    def test_multiple_files_sorted(self, tmp_path):
        """Results should be sorted by filename."""
        yaml_dir = tmp_path / "reports"
        yaml_dir.mkdir()
        for name in ["c_invoice.yaml", "a_sale.yaml", "b_picking.yaml"]:
            with open(yaml_dir / name, "w") as f:
                yaml.dump({"report_name": name.replace(".yaml", ""), "report_model": "test"}, f)

        result = eq_utils.list_yaml_reports(str(yaml_dir))
        filenames = [r["filename"] for r in result]
        assert filenames == ["a_sale.yaml", "b_picking.yaml", "c_invoice.yaml"]

    def test_empty_directory(self, tmp_path):
        """Empty directory should return empty list."""
        yaml_dir = tmp_path / "empty"
        yaml_dir.mkdir()
        result = eq_utils.list_yaml_reports(str(yaml_dir))
        assert result == []

    def test_missing_fields_show_na(self, tmp_path):
        """When YAML lacks report_name or report_model, 'N/A' is used."""
        yaml_dir = tmp_path / "reports"
        yaml_dir.mkdir()
        with open(yaml_dir / "minimal.yaml", "w") as f:
            yaml.dump({"name": {"de_DE": "Test"}}, f)

        result = eq_utils.list_yaml_reports(str(yaml_dir))
        assert result[0]["report_name"] == "N/A"
        assert result[0]["model"] == "N/A"


# ---------------------------------------------------------------------------
# build_reports_from_yaml_objects
# ---------------------------------------------------------------------------


class TestBuildReportsFromYamlObjects:
    """Tests for build_reports_from_yaml_objects()."""

    def test_converts_single_report(self, sample_report_yaml_data):
        """A single YAML dict is converted to an EqReport object."""
        reports = eq_utils.build_reports_from_yaml_objects([sample_report_yaml_data])
        assert len(reports) == 1
        assert isinstance(reports[0], EqReport)
        assert reports[0].report_name == "eq_fr_core_sale_order"

    def test_multi_company_expansion(self):
        """A YAML with company_id: [1, 3] is split into two EqReport objects."""
        yaml_obj = {
            "name": {"de_DE": "Test", "en_US": "Test"},
            "report_name": "eq_fr_mc",
            "report_type": "fast_report",
            "print_report_name": "Test",
            "report_model": "sale.order",
            "company_id": [1, 3],
            "eq_export_type": "pdf",
            "eq_ignore_images": True,
            "eq_handling_html_fields": "standard",
            "eq_multiprint": "standard",
            "multi": False,
            "attachment": "Test.pdf",
            "attachment_use": False,
            "eq_print_button": False,
            "dependencies": ["sale"],
            "report_fields": {"sale.order": ["id"]},
            "calculated_fields": {},
        }
        reports = eq_utils.build_reports_from_yaml_objects([yaml_obj])
        assert len(reports) == 2
        assert reports[0].company_id == [1]
        assert reports[1].company_id == [3]

    def test_empty_list(self):
        """Empty input returns empty output."""
        assert eq_utils.build_reports_from_yaml_objects([]) == []
