# Copyright 2014-now Equitania Software GmbH - Pforzheim - Germany
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

"""Comprehensive tests for odoo_fast_report_mapper._utils module."""

import logging
import os
from unittest.mock import patch

import pytest
import yaml

from odoo_fast_report_mapper import _utils
from odoo_fast_report_mapper._connection import OdooConnection
from odoo_fast_report_mapper._exceptions import PathDoesNotExitError
from odoo_fast_report_mapper._report import Report
from odoo_fast_report_mapper._utils import (
    build_reports_from_yaml_objects,
    collect_all_reports,
    create_connection_from_env,
    create_odoo_connection_from_yaml_object,
    create_report_object_from_yaml_object,
    generate_env_template,
    list_yaml_reports,
    parse_yaml,
    parse_yaml_folder,
    parse_yaml_folder_with_filenames,
    prepare_connection,
    self_clean,
)

# ---------------------------------------------------------------------------
# generate_env_template
# ---------------------------------------------------------------------------


class TestGenerateEnvTemplate:
    """Tests for generate_env_template()."""

    def test_creates_env_file_in_target_dir(self, tmp_path):
        """Template file is created in the given target directory."""
        result = generate_env_template(target_dir=str(tmp_path))
        expected_path = os.path.join(str(tmp_path), ".env")
        assert result == expected_path
        assert os.path.exists(expected_path)

    def test_env_file_contains_template_content(self, tmp_path):
        """Generated .env file contains the expected template content."""
        generate_env_template(target_dir=str(tmp_path))
        env_path = os.path.join(str(tmp_path), ".env")
        with open(env_path, encoding="utf-8") as f:
            content = f.read()
        assert "ODOO_URL=" in content
        assert "ODOO_PORT=" in content
        assert "ODOO_DATABASE=" in content
        assert "ODOO_LANGUAGE=" in content

    def test_raises_file_exists_error_when_env_already_exists(self, tmp_path):
        """FileExistsError is raised if .env already exists in target dir."""
        env_file = tmp_path / ".env"
        env_file.write_text("existing content")
        with pytest.raises(FileExistsError, match=".env file already exists"):
            generate_env_template(target_dir=str(tmp_path))

    def test_defaults_to_cwd_when_no_target_dir(self, tmp_path, monkeypatch):
        """When target_dir is None, the current working directory is used."""
        monkeypatch.chdir(tmp_path)
        result = generate_env_template(target_dir=None)
        expected = os.path.join(str(tmp_path), ".env")
        assert result == expected
        assert os.path.exists(expected)


# ---------------------------------------------------------------------------
# create_report_object_from_yaml_object
# ---------------------------------------------------------------------------


class TestCreateReportObjectFromYamlObject:
    """Tests for create_report_object_from_yaml_object()."""

    def test_creates_valid_report_object(self, sample_report_yaml_data):
        """Report is created with all fields from YAML data."""
        report = create_report_object_from_yaml_object(sample_report_yaml_data)
        assert isinstance(report, Report)
        assert report.entry_name == {"de_DE": "Verkaufsauftrag", "en_US": "Sales_Order"}
        assert report.report_name == "eq_fr_core_sale_order"
        assert report.report_type == "fast_report"
        assert report.model_name == "sale.order"
        assert report.eq_export_type == "pdf"
        assert report.multi is False
        assert report._dependencies == ["sale", "account"]

    def test_company_id_defaults_to_false_when_missing(self, sample_report_yaml_data):
        """company_id defaults to False when not present in YAML data."""
        sample_report_yaml_data.pop("company_id", None)
        report = create_report_object_from_yaml_object(sample_report_yaml_data)
        assert report.company_id is False

    def test_company_id_set_when_present(self, sample_report_yaml_data_with_company):
        """company_id is correctly assigned when provided in YAML data."""
        report = create_report_object_from_yaml_object(sample_report_yaml_data_with_company)
        assert report.company_id == [1, 3]

    def test_legacy_name_keys_normalized(self, sample_report_yaml_data_legacy):
        """Legacy ger/eng keys are normalized to de_DE/en_US."""
        report = create_report_object_from_yaml_object(sample_report_yaml_data_legacy)
        assert isinstance(report, Report)
        assert "de_DE" in report.entry_name
        assert "en_US" in report.entry_name
        assert report.entry_name["de_DE"] == "Verkaufsauftrag"
        assert report.entry_name["en_US"] == "Sales_Order"

    def test_report_fields_and_calculated_fields(self, sample_report_yaml_data):
        """Report fields and calculated fields are passed through correctly."""
        report = create_report_object_from_yaml_object(sample_report_yaml_data)
        assert "sale.order" in report._fields
        assert "payment_text" in report._calculated_fields


# ---------------------------------------------------------------------------
# collect_all_reports
# ---------------------------------------------------------------------------


class TestCollectAllReports:
    """Tests for collect_all_reports()."""

    def test_collects_reports_from_yaml_directory(self, tmp_yaml_dir):
        """Reports are correctly loaded from YAML files in a directory."""
        reports = collect_all_reports(str(tmp_yaml_dir))
        assert len(reports) == 1
        assert isinstance(reports[0], Report)
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

        reports = collect_all_reports(str(yaml_dir))
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

        reports = collect_all_reports(str(yaml_dir))
        assert len(reports) == 1
        assert reports[0].company_id == [2]

    def test_invalid_path_raises_error(self):
        """PathDoesNotExitError is raised for a non-existent directory."""
        with pytest.raises(PathDoesNotExitError):
            collect_all_reports("/nonexistent/path/that/does/not/exist")


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
        conn, env_file = create_connection_from_env(env_path=str(tmp_env_file))
        assert isinstance(conn, OdooConnection)
        assert conn.database == "test_db"
        assert conn.username == "admin"
        assert conn.language == "de_DE"
        assert str(tmp_env_file) in env_file

    def test_from_directory_path(self, tmp_env_file, mock_odoorpc, monkeypatch):
        """Connection is created when env_path points to a directory containing .env."""
        self._clear_odoo_env_vars(monkeypatch)
        conn, env_file = create_connection_from_env(env_path=str(tmp_env_file.parent))
        assert isinstance(conn, OdooConnection)
        assert conn.database == "test_db"
        assert ".env" in env_file

    def test_missing_required_vars_raises_value_error(self, tmp_path, mock_odoorpc, monkeypatch):
        """ValueError is raised when required environment variables are missing."""
        self._clear_odoo_env_vars(monkeypatch)
        env_file = tmp_path / ".env"
        env_file.write_text("ODOO_URL=https://test.com\nODOO_PORT=443\nODOO_USER=admin\n")
        with pytest.raises(ValueError, match="Missing required environment variables"):
            create_connection_from_env(env_path=str(env_file))

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
        conn, _ = create_connection_from_env(env_path=str(env_file))
        assert conn.collect_yaml is False
        assert conn.disable_qweb is True
        assert conn.workflow == 0

    def test_env_file_not_found_raises_value_error(self, tmp_path, mock_odoorpc, monkeypatch):
        """ValueError is raised when the specified .env file does not exist."""
        self._clear_odoo_env_vars(monkeypatch)
        with pytest.raises(ValueError, match=".env file not found"):
            create_connection_from_env(env_path=str(tmp_path / "nonexistent.env"))

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
        conn, _ = create_connection_from_env(env_path=str(env_file))
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
            create_connection_from_env(env_path=str(env_file))

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
            create_connection_from_env(env_path=str(env_file))

    # ----- API-key authentication -----

    @staticmethod
    def _base_env_lines():
        return "ODOO_URL=https://test.com\nODOO_PORT=443\nODOO_USER=admin\nODOO_DATABASE=db\nODOO_LANGUAGE=en_US\n"

    def test_api_key_only_sets_auth_method_api_key(self, tmp_path, mock_odoorpc, monkeypatch):
        """Only ODOO_API_KEY set → auth_method == 'api_key', password slot holds the key."""
        self._clear_odoo_env_vars(monkeypatch)
        env_file = tmp_path / ".env"
        env_file.write_text(self._base_env_lines() + "ODOO_API_KEY=secret-api-key-xyz\n")
        conn, _ = create_connection_from_env(env_path=str(env_file))
        assert conn.auth_method == "api_key"
        assert conn.password == "secret-api-key-xyz"

    def test_password_only_sets_auth_method_password(self, tmp_path, mock_odoorpc, monkeypatch):
        """Only ODOO_PASSWORD set → auth_method == 'password'."""
        self._clear_odoo_env_vars(monkeypatch)
        env_file = tmp_path / ".env"
        env_file.write_text(self._base_env_lines() + "ODOO_PASSWORD=plain-pw\n")
        conn, _ = create_connection_from_env(env_path=str(env_file))
        assert conn.auth_method == "password"
        assert conn.password == "plain-pw"

    def test_api_key_wins_over_password_when_both_set(self, tmp_path, mock_odoorpc, monkeypatch):
        """Both set → API-key wins + warning logged."""
        self._clear_odoo_env_vars(monkeypatch)
        env_file = tmp_path / ".env"
        env_file.write_text(self._base_env_lines() + "ODOO_PASSWORD=plain-pw\nODOO_API_KEY=api-key-1\n")
        with patch.object(_utils.logger, "warning") as mock_warning:
            conn, _ = create_connection_from_env(env_path=str(env_file))
        assert conn.auth_method == "api_key"
        assert conn.password == "api-key-1"
        warning_messages = [c.args[0] for c in mock_warning.call_args_list]
        assert any("ODOO_API_KEY" in msg and "ODOO_PASSWORD" in msg for msg in warning_messages)

    def test_neither_password_nor_api_key_raises(self, tmp_path, mock_odoorpc, monkeypatch):
        """Neither auth var → ValueError mentioning both."""
        self._clear_odoo_env_vars(monkeypatch)
        env_file = tmp_path / ".env"
        env_file.write_text(self._base_env_lines())
        with pytest.raises(ValueError, match="ODOO_API_KEY.*ODOO_PASSWORD"):
            create_connection_from_env(env_path=str(env_file))


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

        result = list_yaml_reports(str(yaml_dir))
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

        result = list_yaml_reports(str(yaml_dir))
        filenames = [r["filename"] for r in result]
        assert filenames == ["a_sale.yaml", "b_picking.yaml", "c_invoice.yaml"]

    def test_empty_directory(self, tmp_path):
        """Empty directory should return empty list."""
        yaml_dir = tmp_path / "empty"
        yaml_dir.mkdir()
        result = list_yaml_reports(str(yaml_dir))
        assert result == []

    def test_missing_fields_show_na(self, tmp_path):
        """When YAML lacks report_name or report_model, 'N/A' is used."""
        yaml_dir = tmp_path / "reports"
        yaml_dir.mkdir()
        with open(yaml_dir / "minimal.yaml", "w") as f:
            yaml.dump({"name": {"de_DE": "Test"}}, f)

        result = list_yaml_reports(str(yaml_dir))
        assert result[0]["report_name"] == "N/A"
        assert result[0]["model"] == "N/A"


# ---------------------------------------------------------------------------
# build_reports_from_yaml_objects
# ---------------------------------------------------------------------------


class TestBuildReportsFromYamlObjects:
    """Tests for build_reports_from_yaml_objects()."""

    def test_converts_single_report(self, sample_report_yaml_data):
        """A single YAML dict is converted to a Report object."""
        reports = build_reports_from_yaml_objects([sample_report_yaml_data])
        assert len(reports) == 1
        assert isinstance(reports[0], Report)
        assert reports[0].report_name == "eq_fr_core_sale_order"

    def test_multi_company_expansion(self):
        """A YAML with company_id: [1, 3] is split into two Report objects."""
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
        reports = build_reports_from_yaml_objects([yaml_obj])
        assert len(reports) == 2
        assert reports[0].company_id == [1]
        assert reports[1].company_id == [3]

    def test_empty_list(self):
        """Empty input returns empty output."""
        assert build_reports_from_yaml_objects([]) == []


# ---------------------------------------------------------------------------
# prepare_connection tests
# ---------------------------------------------------------------------------


class TestPrepareConnection:
    """Tests for prepare_connection(url, port)."""

    def test_https_url(self):
        """HTTPS URL should use jsonrpc+ssl protocol and strip the scheme."""
        with patch("odoo_fast_report_mapper._utils.ODOO") as mock_odoo:
            mock_odoo.return_value = object()
            prepare_connection("https://odoo.example.com", 443)
            mock_odoo.assert_called_once_with("odoo.example.com", port=443, protocol="jsonrpc+ssl")

    def test_http_url(self):
        """HTTP URL should use jsonrpc protocol and strip the scheme."""
        with patch("odoo_fast_report_mapper._utils.ODOO") as mock_odoo:
            mock_odoo.return_value = object()
            prepare_connection("http://odoo.example.com", 8069)
            mock_odoo.assert_called_once_with("odoo.example.com", port=8069, protocol="jsonrpc")

    def test_url_with_trailing_slashes(self):
        """Trailing forward slashes in URL should be stripped."""
        with patch("odoo_fast_report_mapper._utils.ODOO") as mock_odoo:
            mock_odoo.return_value = object()
            prepare_connection("https://odoo.example.com///", 443)
            mock_odoo.assert_called_once_with("odoo.example.com", port=443, protocol="jsonrpc+ssl")

    def test_url_with_trailing_backslashes(self):
        """Trailing backslashes in URL should be stripped."""
        with patch("odoo_fast_report_mapper._utils.ODOO") as mock_odoo:
            mock_odoo.return_value = object()
            prepare_connection("https://odoo.example.com\\\\", 443)
            mock_odoo.assert_called_once_with("odoo.example.com", port=443, protocol="jsonrpc+ssl")

    def test_https_port_zero_defaults_to_443(self):
        """Port <= 0 with HTTPS should default to 443."""
        with patch("odoo_fast_report_mapper._utils.ODOO") as mock_odoo:
            mock_odoo.return_value = object()
            prepare_connection("https://odoo.example.com", 0)
            mock_odoo.assert_called_once_with("odoo.example.com", port=443, protocol="jsonrpc+ssl")

    def test_port_string_is_cast_to_int(self):
        """Port supplied as string should be cast to int."""
        with patch("odoo_fast_report_mapper._utils.ODOO") as mock_odoo:
            mock_odoo.return_value = object()
            prepare_connection("http://odoo.example.com", "8069")
            mock_odoo.assert_called_once_with("odoo.example.com", port=8069, protocol="jsonrpc")

    def test_no_protocol_uses_ssl_default(self):
        """URL without explicit protocol should default to jsonrpc+ssl."""
        with patch("odoo_fast_report_mapper._utils.ODOO") as mock_odoo:
            mock_odoo.return_value = object()
            prepare_connection("odoo.example.com", 443)
            mock_odoo.assert_called_once_with("odoo.example.com", port=443, protocol="jsonrpc+ssl")

    def test_url_with_path_component_strips_path(self):
        """BUG-05 regression: path components must not reach OdooRPC."""
        with patch("odoo_fast_report_mapper._utils.ODOO") as mock_odoo:
            mock_odoo.return_value = object()
            prepare_connection("https://host.example.com/web", 443)
            mock_odoo.assert_called_once_with("host.example.com", port=443, protocol="jsonrpc+ssl")


# ---------------------------------------------------------------------------
# self_clean tests
# ---------------------------------------------------------------------------


class TestSelfClean:
    """Tests for self_clean(input_dictionary)."""

    def test_removes_duplicates(self):
        """Duplicate values within each list should be removed."""
        unclean = {
            "a": ["x", "y", "x"],
            "b": [1, 2, 2, 3, 1],
        }
        result = self_clean(unclean)
        assert result == {"a": ["x", "y"], "b": [1, 2, 3]}

    def test_already_clean_dict(self):
        """A dictionary without duplicates should be returned unchanged."""
        clean = {"key1": ["a", "b"], "key2": [1, 2, 3]}
        result = self_clean(clean)
        assert result == clean

    def test_empty_dict(self):
        """An empty dictionary should return an empty dictionary."""
        result = self_clean({})
        assert result == {}

    def test_does_not_mutate_original(self):
        """The original dictionary should not be modified."""
        original = {"k": ["dup", "dup", "unique"]}
        original_copy = {"k": ["dup", "dup", "unique"]}
        self_clean(original)
        assert original == original_copy


# ---------------------------------------------------------------------------
# parse_yaml tests
# ---------------------------------------------------------------------------

YAML_TEST_DIR = os.path.join(os.path.dirname(__file__), "yaml_test")


class TestParseYaml:
    """Tests for parse_yaml(yaml_file)."""

    def test_valid_yaml_file(self):
        """A valid YAML file should be parsed into a dict."""
        result = parse_yaml(os.path.join(YAML_TEST_DIR, "test.yaml"))
        assert isinstance(result, dict)
        assert result["variable"] == "var"
        assert result["dictionary"] == {"first": "foo", "second": "bar"}
        assert result["list"] == ["Hello", "World"]

    def test_invalid_yaml_returns_false(self, tmp_path):
        """An invalid YAML file should return False without raising."""
        bad_yaml = tmp_path / "bad.yaml"
        bad_yaml.write_text("key: [\ninvalid: yaml: content\n  broken")
        result = parse_yaml(str(bad_yaml))
        assert result is False

    def test_nonexistent_file_raises(self):
        """A nonexistent file should raise FileNotFoundError."""
        with pytest.raises(FileNotFoundError):
            parse_yaml("/nonexistent/path/missing.yaml")

    def test_empty_yaml_file(self, tmp_path):
        """An empty YAML file should return None (yaml.safe_load behaviour)."""
        empty_file = tmp_path / "empty.yaml"
        empty_file.write_text("")
        result = parse_yaml(str(empty_file))
        assert result is None


# ---------------------------------------------------------------------------
# parse_yaml_folder tests
# ---------------------------------------------------------------------------


class TestParseYamlFolder:
    """Tests for parse_yaml_folder(path)."""

    def test_multiple_files(self):
        """All valid .yaml files in the directory should be parsed."""
        results = parse_yaml_folder(YAML_TEST_DIR)
        assert isinstance(results, list)
        assert len(results) == 2
        variables = sorted([r["variable"] for r in results])
        assert variables == ["var", "varo"]

    def test_empty_directory(self, tmp_path):
        """An empty directory should return an empty list."""
        results = parse_yaml_folder(str(tmp_path))
        assert results == []

    def test_mixed_valid_and_invalid_files(self, tmp_path):
        """Invalid YAML files should be skipped; valid ones should be returned."""
        valid = tmp_path / "good.yaml"
        valid.write_text(yaml.dump({"status": "ok"}))

        invalid = tmp_path / "bad.yaml"
        invalid.write_text("key: [\ninvalid: yaml: broken\n  nope")

        results = parse_yaml_folder(str(tmp_path))
        assert len(results) == 1
        assert results[0]["status"] == "ok"

    def test_nonexistent_directory_raises(self):
        """A nonexistent directory should raise FileNotFoundError."""
        with pytest.raises(FileNotFoundError, match="Directory not found"):
            parse_yaml_folder("/nonexistent/directory/path")

    def test_file_path_raises(self, tmp_path):
        """A file path (not directory) should raise FileNotFoundError."""
        f = tmp_path / "not_a_dir.txt"
        f.write_text("hello")
        with pytest.raises(FileNotFoundError, match="Directory not found"):
            parse_yaml_folder(str(f))

    def test_non_yaml_files_ignored(self, tmp_path):
        """Files without .yaml extension should be ignored."""
        txt_file = tmp_path / "notes.txt"
        txt_file.write_text("This is not yaml")

        json_file = tmp_path / "data.json"
        json_file.write_text('{"key": "value"}')

        yml_file = tmp_path / "config.yml"
        yml_file.write_text(yaml.dump({"should": "be_ignored"}))

        yaml_file = tmp_path / "actual.yaml"
        yaml_file.write_text(yaml.dump({"should": "be_included"}))

        results = parse_yaml_folder(str(tmp_path))
        assert len(results) == 1
        assert results[0]["should"] == "be_included"


# ---------------------------------------------------------------------------
# parse_yaml_folder_with_filenames tests
# ---------------------------------------------------------------------------


class TestParseYamlFolderWithFilenames:
    """Tests for parse_yaml_folder_with_filenames(path)."""

    def test_returns_tuples_of_filename_and_dict(self):
        """Each item should be a (filename, dict) tuple."""
        results = parse_yaml_folder_with_filenames(YAML_TEST_DIR)
        assert isinstance(results, list)
        assert len(results) == 2
        for filename, yaml_obj in results:
            assert isinstance(filename, str)
            assert filename.endswith(".yaml")
            assert isinstance(yaml_obj, dict)

    def test_sorted_by_filename(self, tmp_path):
        """Results should be sorted alphabetically by filename."""
        (tmp_path / "c_report.yaml").write_text(yaml.dump({"name": "c"}))
        (tmp_path / "a_report.yaml").write_text(yaml.dump({"name": "a"}))
        (tmp_path / "b_report.yaml").write_text(yaml.dump({"name": "b"}))

        results = parse_yaml_folder_with_filenames(str(tmp_path))
        filenames = [f for f, _ in results]
        assert filenames == ["a_report.yaml", "b_report.yaml", "c_report.yaml"]

    def test_empty_directory(self, tmp_path):
        """An empty directory should return an empty list."""
        results = parse_yaml_folder_with_filenames(str(tmp_path))
        assert results == []

    def test_nonexistent_directory_raises(self):
        """A nonexistent directory should raise FileNotFoundError."""
        with pytest.raises(FileNotFoundError, match="Directory not found"):
            parse_yaml_folder_with_filenames("/nonexistent/directory")

    def test_skips_invalid_yaml(self, tmp_path):
        """Invalid YAML files should be skipped."""
        (tmp_path / "good.yaml").write_text(yaml.dump({"status": "ok"}))
        (tmp_path / "bad.yaml").write_text("key: [\nbad: yaml\n  broken")

        results = parse_yaml_folder_with_filenames(str(tmp_path))
        assert len(results) == 1
        assert results[0][0] == "good.yaml"

    def test_consistent_with_parse_yaml_folder(self):
        """Content should match parse_yaml_folder output."""
        with_names = parse_yaml_folder_with_filenames(YAML_TEST_DIR)
        without_names = parse_yaml_folder(YAML_TEST_DIR)
        contents_from_with_names = [obj for _, obj in with_names]
        assert contents_from_with_names == without_names


# ---------------------------------------------------------------------------
# create_odoo_connection_from_yaml_object (BUG-07 regression tests)
# ---------------------------------------------------------------------------


class TestCreateConnectionFromYamlObject:
    """Regression tests for create_odoo_connection_from_yaml_object() — BUG-07.

    Verifies that api_key in the YAML Server config is honoured and that
    auth_method is passed correctly to OdooConnection.
    """

    def test_api_key_sets_auth_method_api_key(self, mock_odoorpc, sample_connection_yaml_data):
        """api_key in YAML → auth_method='api_key', credential = api_key value."""
        sample_connection_yaml_data["Server"]["api_key"] = "my-api-key"
        conn = create_odoo_connection_from_yaml_object(sample_connection_yaml_data)
        assert conn.auth_method == "api_key"
        assert conn.password == "my-api-key"

    def test_password_only_sets_auth_method_password(self, mock_odoorpc, sample_connection_yaml_data):
        """No api_key in YAML → auth_method='password', credential = password value."""
        # sample_connection_yaml_data has password='test_password' and no api_key
        conn = create_odoo_connection_from_yaml_object(sample_connection_yaml_data)
        assert conn.auth_method == "password"
        assert conn.password == "test_password"

    def test_api_key_wins_when_both_set(self, mock_odoorpc, sample_connection_yaml_data):
        """Both api_key and password in YAML → api_key wins silently."""
        sample_connection_yaml_data["Server"]["api_key"] = "api-key-wins"
        # password='test_password' already present from fixture
        conn = create_odoo_connection_from_yaml_object(sample_connection_yaml_data)
        assert conn.auth_method == "api_key"
        assert conn.password == "api-key-wins"


# ---------------------------------------------------------------------------
# parse_yaml duplicate key detection
# ---------------------------------------------------------------------------


class _ListHandler(logging.Handler):
    """Collect log records in a list — independent of global logging state."""

    def __init__(self) -> None:
        super().__init__()
        self.records: list[logging.LogRecord] = []

    def emit(self, record: logging.LogRecord) -> None:
        self.records.append(record)


class TestParseYamlDuplicateKeys:
    """Duplicate mapping keys must be logged — PyYAML silently keeps the last
    value, which wiped the sale-order attachment expressions in v19-fast-report."""

    @pytest.fixture()
    def utils_log(self):
        """Attach a capture handler directly to the package logger.

        The package logger uses propagate=False and other tests reconfigure
        global logging, so caplog/capsys are unreliable here.
        """
        logger = logging.getLogger("odoo_fast_report_mapper._utils")
        handler = _ListHandler()
        old_level = logger.level
        logger.addHandler(handler)
        logger.setLevel(logging.WARNING)
        yield handler
        logger.removeHandler(handler)
        logger.setLevel(old_level)

    def test_duplicate_top_level_key_warns_and_keeps_last_value(self, tmp_path, utils_log):
        """A duplicate top-level key should log a warning with file and line."""
        yaml_file = tmp_path / "report.yaml"
        yaml_file.write_text(
            "attachment:\n  de_DE: expr\nreport_name: foo\nattachment: false\n",
            encoding="utf-8",
        )
        result = parse_yaml(str(yaml_file))
        assert result["attachment"] is False  # last-wins behavior unchanged
        out = "\n".join(rec.getMessage() for rec in utils_log.records)
        assert "Duplicate YAML key 'attachment'" in out
        assert "line 4" in out
        assert "report.yaml" in out

    def test_duplicate_nested_key_warns(self, tmp_path, utils_log):
        """Duplicates inside nested mappings (e.g. the name dict) are detected too."""
        yaml_file = tmp_path / "report.yaml"
        yaml_file.write_text("name:\n  de_DE: A\n  de_DE: B\n", encoding="utf-8")
        result = parse_yaml(str(yaml_file))
        assert result["name"]["de_DE"] == "B"
        out = "\n".join(rec.getMessage() for rec in utils_log.records)
        assert "Duplicate YAML key 'de_DE'" in out
        assert "line 3" in out

    def test_clean_yaml_logs_no_warning(self, tmp_path, utils_log):
        """A file without duplicate keys should not produce any warning."""
        yaml_file = tmp_path / "report.yaml"
        yaml_file.write_text("report_name: foo\nreport_model: sale.order\n", encoding="utf-8")
        result = parse_yaml(str(yaml_file))
        assert result == {"report_name": "foo", "report_model": "sale.order"}
        out = "\n".join(rec.getMessage() for rec in utils_log.records)
        assert "Duplicate YAML key" not in out

    def test_invalid_yaml_still_returns_false(self, tmp_path):
        """Broken YAML keeps returning False (error contract unchanged)."""
        yaml_file = tmp_path / "broken.yaml"
        yaml_file.write_text("key: [\nbad: yaml\n  broken", encoding="utf-8")
        assert parse_yaml(str(yaml_file)) is False
