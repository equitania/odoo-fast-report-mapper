# Copyright 2014-now Equitania Software GmbH - Pforzheim - Germany
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

"""
Comprehensive pytest tests for odoo_report_helper/utils.py

Covers:
- prepare_connection: protocol detection, URL stripping, port normalization
- fire_all_functions: execution order and empty list handling
- self_clean: duplicate removal in dictionary value lists
- parse_yaml: valid files, invalid YAML, nonexistent files
- parse_yaml_folder: multi-file parsing, empty directories, mixed validity
"""

import os
from unittest.mock import MagicMock, patch

import pytest
import yaml

import odoo_report_helper.utils as utils

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

YAML_TEST_DIR = os.path.join(os.path.dirname(__file__), "yaml_test")


@pytest.fixture
def yaml_test_dir():
    """Return the path to the existing yaml_test fixture directory."""
    return YAML_TEST_DIR


# ---------------------------------------------------------------------------
# prepare_connection tests
# ---------------------------------------------------------------------------


class TestPrepareConnection:
    """Tests for prepare_connection(url, port)."""

    @patch("odoo_report_helper.utils.ODOO")
    def test_https_url(self, mock_odoo):
        """HTTPS URL should use jsonrpc+ssl protocol and strip the scheme."""
        mock_odoo.return_value = MagicMock()
        utils.prepare_connection("https://odoo.example.com", 443)
        mock_odoo.assert_called_once_with("odoo.example.com", port=443, protocol="jsonrpc+ssl")

    @patch("odoo_report_helper.utils.ODOO")
    def test_http_url(self, mock_odoo):
        """HTTP URL should use jsonrpc protocol and strip the scheme."""
        mock_odoo.return_value = MagicMock()
        utils.prepare_connection("http://odoo.example.com", 8069)
        mock_odoo.assert_called_once_with("odoo.example.com", port=8069, protocol="jsonrpc")

    @patch("odoo_report_helper.utils.ODOO")
    def test_url_with_trailing_slashes(self, mock_odoo):
        """Trailing forward slashes in URL should be stripped."""
        mock_odoo.return_value = MagicMock()
        utils.prepare_connection("https://odoo.example.com///", 443)
        mock_odoo.assert_called_once_with("odoo.example.com", port=443, protocol="jsonrpc+ssl")

    @patch("odoo_report_helper.utils.ODOO")
    def test_url_with_trailing_backslashes(self, mock_odoo):
        """Trailing backslashes in URL should be stripped."""
        mock_odoo.return_value = MagicMock()
        utils.prepare_connection("https://odoo.example.com\\\\", 443)
        mock_odoo.assert_called_once_with("odoo.example.com", port=443, protocol="jsonrpc+ssl")

    @patch("odoo_report_helper.utils.ODOO")
    def test_https_port_zero_defaults_to_443(self, mock_odoo):
        """Port <= 0 with HTTPS should default to 443."""
        mock_odoo.return_value = MagicMock()
        utils.prepare_connection("https://odoo.example.com", 0)
        mock_odoo.assert_called_once_with("odoo.example.com", port=443, protocol="jsonrpc+ssl")

    @patch("odoo_report_helper.utils.ODOO")
    def test_port_string_is_cast_to_int(self, mock_odoo):
        """Port supplied as string should be cast to int."""
        mock_odoo.return_value = MagicMock()
        utils.prepare_connection("http://odoo.example.com", "8069")
        mock_odoo.assert_called_once_with("odoo.example.com", port=8069, protocol="jsonrpc")

    @patch("odoo_report_helper.utils.ODOO")
    def test_no_protocol_uses_ssl_default(self, mock_odoo):
        """URL without explicit protocol should default to jsonrpc+ssl."""
        mock_odoo.return_value = MagicMock()
        utils.prepare_connection("odoo.example.com", 443)
        mock_odoo.assert_called_once_with("odoo.example.com", port=443, protocol="jsonrpc+ssl")


# ---------------------------------------------------------------------------
# fire_all_functions tests
# ---------------------------------------------------------------------------


class TestFireAllFunctions:
    """Tests for fire_all_functions(function_list)."""

    def test_calls_all_functions(self):
        """Every function in the list should be called exactly once."""
        mock_a = MagicMock()
        mock_b = MagicMock()
        mock_c = MagicMock()
        utils.fire_all_functions([mock_a, mock_b, mock_c])
        mock_a.assert_called_once()
        mock_b.assert_called_once()
        mock_c.assert_called_once()

    def test_empty_list(self):
        """An empty list should not raise and should do nothing."""
        utils.fire_all_functions([])  # Should not raise


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
        result = utils.self_clean(unclean)
        assert result == {"a": ["x", "y"], "b": [1, 2, 3]}

    def test_already_clean_dict(self):
        """A dictionary without duplicates should be returned unchanged."""
        clean = {"key1": ["a", "b"], "key2": [1, 2, 3]}
        result = utils.self_clean(clean)
        assert result == clean

    def test_empty_dict(self):
        """An empty dictionary should return an empty dictionary."""
        result = utils.self_clean({})
        assert result == {}

    def test_does_not_mutate_original(self):
        """The original dictionary should not be modified."""
        original = {"k": ["dup", "dup", "unique"]}
        original_copy = {"k": ["dup", "dup", "unique"]}
        utils.self_clean(original)
        assert original == original_copy


# ---------------------------------------------------------------------------
# parse_yaml tests
# ---------------------------------------------------------------------------


class TestParseYaml:
    """Tests for parse_yaml(yaml_file)."""

    def test_valid_yaml_file(self, yaml_test_dir):
        """A valid YAML file should be parsed into a dict."""
        result = utils.parse_yaml(os.path.join(yaml_test_dir, "test.yaml"))
        assert isinstance(result, dict)
        assert result["variable"] == "var"
        assert result["dictionary"] == {"first": "foo", "second": "bar"}
        assert result["list"] == ["Hello", "World"]

    def test_invalid_yaml_returns_false(self, tmp_path):
        """An invalid YAML file should return False without raising."""
        bad_yaml = tmp_path / "bad.yaml"
        bad_yaml.write_text("key: [\ninvalid: yaml: content\n  broken")
        result = utils.parse_yaml(str(bad_yaml))
        assert result is False

    def test_nonexistent_file_raises(self):
        """A nonexistent file should raise FileNotFoundError."""
        with pytest.raises(FileNotFoundError):
            utils.parse_yaml("/nonexistent/path/missing.yaml")

    def test_empty_yaml_file(self, tmp_path):
        """An empty YAML file should return None (yaml.safe_load behaviour)."""
        empty_file = tmp_path / "empty.yaml"
        empty_file.write_text("")
        result = utils.parse_yaml(str(empty_file))
        assert result is None


# ---------------------------------------------------------------------------
# parse_yaml_folder tests
# ---------------------------------------------------------------------------


class TestParseYamlFolder:
    """Tests for parse_yaml_folder(path)."""

    def test_multiple_files(self, yaml_test_dir):
        """All valid .yaml files in the directory should be parsed."""
        results = utils.parse_yaml_folder(yaml_test_dir)
        assert isinstance(results, list)
        assert len(results) == 2
        variables = sorted([r["variable"] for r in results])
        assert variables == ["var", "varo"]

    def test_empty_directory(self, tmp_path):
        """An empty directory should return an empty list."""
        results = utils.parse_yaml_folder(str(tmp_path))
        assert results == []

    def test_mixed_valid_and_invalid_files(self, tmp_path):
        """Invalid YAML files should be skipped; valid ones should be returned."""
        valid = tmp_path / "good.yaml"
        valid.write_text(yaml.dump({"status": "ok"}))

        invalid = tmp_path / "bad.yaml"
        invalid.write_text("key: [\ninvalid: yaml: broken\n  nope")

        results = utils.parse_yaml_folder(str(tmp_path))
        assert len(results) == 1
        assert results[0]["status"] == "ok"

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

        results = utils.parse_yaml_folder(str(tmp_path))
        assert len(results) == 1
        assert results[0]["should"] == "be_included"
