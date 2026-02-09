# Copyright 2014-now Equitania Software GmbH - Pforzheim - Germany
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

"""Tests for odoo_fast_report_mapper/eq_odoo_connection.py - EqOdooConnection class."""

from unittest.mock import MagicMock, patch

import yaml

from odoo_fast_report_mapper.eq_odoo_connection import EqOdooConnection, YAMLDumper

# ---------------------------------------------------------------------------
# Helper to create EqOdooConnection with mocked ODOO
# ---------------------------------------------------------------------------


def _make_eq_connection(
    language="ger",
    collect_yaml=False,
    disable_qweb=True,
    workflow=0,
    url="https://odoo.example.com",
    port=443,
    username="admin",
    password="secret",
    database="test_db",
):
    """Create an EqOdooConnection with a patched prepare_connection."""
    with patch("odoo_report_helper.odoo_connection.utils.prepare_connection") as mock_prepare:
        mock_connection = MagicMock()
        mock_connection.version = "18.0"
        mock_connection.config = {}
        mock_connection.env.context = {}
        mock_prepare.return_value = mock_connection

        conn = EqOdooConnection(
            language=language,
            collect_yaml=collect_yaml,
            disable_qweb=disable_qweb,
            workflow=workflow,
            url=url,
            port=port,
            username=username,
            password=password,
            database=database,
        )
    return conn


# ---------------------------------------------------------------------------
# Constructor tests
# ---------------------------------------------------------------------------


class TestEqOdooConnectionConstructor:
    """Verify constructor sets EqOdooConnection-specific attributes."""

    def test_constructor_sets_language(self):
        conn = _make_eq_connection(language="eng")
        assert conn.language == "eng"

    def test_constructor_sets_collect_yaml(self):
        conn = _make_eq_connection(collect_yaml=True)
        assert conn.collect_yaml is True

    def test_constructor_sets_disable_qweb(self):
        conn = _make_eq_connection(disable_qweb=False)
        assert conn.disable_qweb is False

    def test_constructor_sets_workflow(self):
        conn = _make_eq_connection(workflow=2)
        assert conn.workflow == 2

    def test_constructor_sets_all_attributes(self):
        conn = _make_eq_connection(language="ger", collect_yaml=False, disable_qweb=True, workflow=1)
        assert conn.language == "ger"
        assert conn.collect_yaml is False
        assert conn.disable_qweb is True
        assert conn.workflow == 1


# ---------------------------------------------------------------------------
# _search_report_v13() tests
# ---------------------------------------------------------------------------


class TestSearchReportV13:
    """Verify report search with company_id filtering (v13+ behavior)."""

    def test_search_report_v13_without_company_id(self):
        """_search_report_v13 must search with company_id=False when not provided."""
        conn = _make_eq_connection()
        mock_ir_report = MagicMock()
        mock_ir_report.search.return_value = [42]

        result = conn._search_report_v13(
            model_name="sale.order",
            report_name={"ger": "Verkaufsauftrag", "eng": "Sales_Order"},
            IR_ACTIONS_REPORT=mock_ir_report,
            company_id=False,
        )

        assert result == 42
        mock_ir_report.search.assert_called_once()
        call_args = mock_ir_report.search.call_args[0][0]
        # Verify company_id filter is present with False
        assert ("company_id", "=", False) in call_args

    def test_search_report_v13_with_company_id(self):
        """_search_report_v13 must search with specific company_id when provided."""
        conn = _make_eq_connection()
        mock_ir_report = MagicMock()
        mock_ir_report.search.return_value = [55]

        result = conn._search_report_v13(
            model_name="sale.order",
            report_name={"ger": "Verkaufsauftrag", "eng": "Sales_Order"},
            IR_ACTIONS_REPORT=mock_ir_report,
            company_id=3,
        )

        assert result == 55
        call_args = mock_ir_report.search.call_args[0][0]
        assert ("company_id", "=", 3) in call_args

    def test_search_report_v13_falls_back_to_english(self):
        """_search_report_v13 must try English name if German name yields no results."""
        conn = _make_eq_connection()
        mock_ir_report = MagicMock()
        # First search (German) returns nothing, second search (English) returns result
        mock_ir_report.search.side_effect = [[], [77]]

        result = conn._search_report_v13(
            model_name="sale.order",
            report_name={"ger": "Verkaufsauftrag", "eng": "Sales_Order"},
            IR_ACTIONS_REPORT=mock_ir_report,
            company_id=False,
        )

        assert result == 77
        assert mock_ir_report.search.call_count == 2

    def test_search_report_v13_returns_false_when_not_found(self):
        """_search_report_v13 must return False when no reports are found."""
        conn = _make_eq_connection()
        mock_ir_report = MagicMock()
        mock_ir_report.search.return_value = []

        result = conn._search_report_v13(
            model_name="sale.order",
            report_name={"ger": "Nonexistent"},
            IR_ACTIONS_REPORT=mock_ir_report,
            company_id=False,
        )

        assert result is False


# ---------------------------------------------------------------------------
# _search_report() tests (EqOdooConnection override)
# ---------------------------------------------------------------------------


class TestSearchReport:
    """Verify report search with German and English name fallback."""

    def test_search_report_german_name_found(self):
        """_search_report must return ID when German name matches."""
        conn = _make_eq_connection()
        mock_ir_report = MagicMock()
        mock_ir_report.search.return_value = [10]

        result = conn._search_report(
            model_name="sale.order",
            report_name={"ger": "Verkaufsauftrag", "eng": "Sales_Order"},
            IR_ACTIONS_REPORT=mock_ir_report,
        )

        assert result == 10

    def test_search_report_english_name_fallback(self):
        """_search_report must fall back to English name when German yields no results."""
        conn = _make_eq_connection()
        mock_ir_report = MagicMock()
        mock_ir_report.search.side_effect = [[], [20]]

        result = conn._search_report(
            model_name="sale.order",
            report_name={"ger": "Verkaufsauftrag", "eng": "Sales_Order"},
            IR_ACTIONS_REPORT=mock_ir_report,
        )

        assert result == 20
        assert mock_ir_report.search.call_count == 2

    def test_search_report_returns_false_when_not_found(self):
        """_search_report must return False when neither name yields results."""
        conn = _make_eq_connection()
        mock_ir_report = MagicMock()
        mock_ir_report.search.return_value = []

        result = conn._search_report(
            model_name="sale.order",
            report_name={"ger": "Nonexistent", "eng": "Nonexistent"},
            IR_ACTIONS_REPORT=mock_ir_report,
        )

        assert result is False

    def test_search_report_uses_connection_env_when_no_ir_report_passed(self):
        """_search_report must use self.connection.env when IR_ACTIONS_REPORT is False."""
        conn = _make_eq_connection()
        mock_ir_report = MagicMock()
        mock_ir_report.search.return_value = [30]
        conn.connection.env.__getitem__ = MagicMock(return_value=mock_ir_report)

        result = conn._search_report(
            model_name="sale.order",
            report_name={"ger": "Test"},
        )

        conn.connection.env.__getitem__.assert_called_with("ir.actions.report")
        assert result == 30


# ---------------------------------------------------------------------------
# check_dependencies() tests (EqOdooConnection override)
# ---------------------------------------------------------------------------


class TestCheckDependencies:
    """Verify dependency checking returns tuple (bool, list)."""

    def test_check_dependencies_all_installed(self):
        """check_dependencies must return (True, []) when all are installed."""
        conn = _make_eq_connection()
        mock_ir_module = MagicMock()
        mock_ir_module.search.return_value = [1]
        conn.connection.env.__getitem__ = MagicMock(return_value=mock_ir_module)

        result = conn.check_dependencies(["sale", "account"])

        assert result == (True, [])

    def test_check_dependencies_one_missing(self):
        """check_dependencies must return (False, [missing]) when one is missing."""
        conn = _make_eq_connection()
        mock_ir_module = MagicMock()
        mock_ir_module.search.side_effect = [[1], []]
        conn.connection.env.__getitem__ = MagicMock(return_value=mock_ir_module)

        result = conn.check_dependencies(["sale", "missing_module"])

        assert result[0] is False
        assert "missing_module" in result[1]

    def test_check_dependencies_empty_list(self):
        """check_dependencies must return (True, []) for empty list."""
        conn = _make_eq_connection()

        result = conn.check_dependencies([])

        assert result == (True, [])

    def test_check_dependencies_none(self):
        """check_dependencies must return (True, []) for None."""
        conn = _make_eq_connection()

        result = conn.check_dependencies(None)

        assert result == (True, [])


# ---------------------------------------------------------------------------
# is_boolean() / is_dict() tests
# ---------------------------------------------------------------------------


class TestIsBoolean:
    """Verify is_boolean type checking."""

    def test_is_boolean_true(self):
        conn = _make_eq_connection()
        assert conn.is_boolean(True) is True

    def test_is_boolean_false(self):
        conn = _make_eq_connection()
        assert conn.is_boolean(False) is True

    def test_is_boolean_integer(self):
        conn = _make_eq_connection()
        assert conn.is_boolean(1) is False

    def test_is_boolean_string(self):
        conn = _make_eq_connection()
        assert conn.is_boolean("True") is False

    def test_is_boolean_none(self):
        conn = _make_eq_connection()
        assert conn.is_boolean(None) is False


class TestIsDict:
    """Verify is_dict type checking."""

    def test_is_dict_with_dict(self):
        conn = _make_eq_connection()
        assert conn.is_dict({"key": "value"}) is True

    def test_is_dict_with_empty_dict(self):
        conn = _make_eq_connection()
        assert conn.is_dict({}) is True

    def test_is_dict_with_list(self):
        conn = _make_eq_connection()
        assert conn.is_dict([1, 2]) is False

    def test_is_dict_with_string(self):
        conn = _make_eq_connection()
        assert conn.is_dict("not a dict") is False

    def test_is_dict_with_none(self):
        conn = _make_eq_connection()
        assert conn.is_dict(None) is False


# ---------------------------------------------------------------------------
# write_yaml() tests
# ---------------------------------------------------------------------------


class TestWriteYaml:
    """Verify YAML file writing."""

    def test_write_yaml_creates_valid_yaml_file(self, tmp_path):
        """write_yaml must create a valid YAML file with correct content."""
        conn = _make_eq_connection()
        output_file = tmp_path / "test_output.yaml"
        data = {
            "name": {"ger": "Verkaufsauftrag", "eng": "Sales_Order"},
            "report_name": "eq_fr_core_sale_order",
            "report_type": "fast_report",
        }

        conn.write_yaml(str(output_file), data)

        assert output_file.exists()
        with open(output_file, encoding="utf8") as f:
            loaded = yaml.safe_load(f)
        assert loaded["name"] == {"ger": "Verkaufsauftrag", "eng": "Sales_Order"}
        assert loaded["report_name"] == "eq_fr_core_sale_order"
        assert loaded["report_type"] == "fast_report"

    def test_write_yaml_utf8_encoding(self, tmp_path):
        """write_yaml must handle UTF-8 characters correctly."""
        conn = _make_eq_connection()
        output_file = tmp_path / "test_utf8.yaml"
        data = {"name": {"ger": "Rechnungsueberblick"}}

        conn.write_yaml(str(output_file), data)

        content = output_file.read_text(encoding="utf8")
        assert "Rechnungsueberblick" in content

    def test_write_yaml_uses_yaml_dumper(self, tmp_path):
        """write_yaml must use the custom YAMLDumper for formatting."""
        conn = _make_eq_connection()
        output_file = tmp_path / "test_dumper.yaml"
        data = {
            "level1": {
                "level2": ["item1", "item2"],
            },
        }

        conn.write_yaml(str(output_file), data)

        content = output_file.read_text(encoding="utf8")
        # YAMLDumper increases indent, so nested items should be indented
        assert "level1:" in content
        assert "level2:" in content


# ---------------------------------------------------------------------------
# YAMLDumper tests
# ---------------------------------------------------------------------------


class TestYAMLDumper:
    """Verify custom YAMLDumper increases indent correctly."""

    def test_yaml_dumper_increases_indent(self):
        """YAMLDumper must override indentless=False for consistent indentation."""
        data = {
            "parent": {
                "child": ["item1", "item2"],
            },
        }
        output = yaml.dump(data, Dumper=YAMLDumper, default_flow_style=False)

        # With indentless=False, list items should be indented under their parent
        assert "parent:" in output
        assert "child:" in output
        lines = output.strip().split("\n")
        # Verify child is indented relative to parent
        parent_indent = len(lines[0]) - len(lines[0].lstrip())
        child_indent = len(lines[1]) - len(lines[1].lstrip())
        assert child_indent > parent_indent


# ---------------------------------------------------------------------------
# add_field_to_dictionary() tests
# ---------------------------------------------------------------------------


class TestAddFieldToDictionary:
    """Verify field addition to data dictionary."""

    def test_add_field_to_new_report(self):
        """add_field_to_dictionary must create new report entry in dictionary."""
        conn = _make_eq_connection()
        mock_ir_fields = MagicMock()
        mock_ir_model = MagicMock()
        mock_ir_model.search.return_value = [1]
        mock_ir_fields.search.return_value = [10]
        mock_field_obj = MagicMock()
        mock_field_obj.modules = "sale, account"
        mock_ir_fields.browse.return_value = mock_field_obj

        def mock_env_getitem(key):
            if key == "ir.model.fields":
                return mock_ir_fields
            if key == "ir.model":
                return mock_ir_model
            return MagicMock()

        conn.connection.env.__getitem__ = MagicMock(side_effect=mock_env_getitem)

        data_dict = {}
        result = conn.add_field_to_dictionary(data_dict, 100, "sale.order", "name", False)

        assert 100 in result
        assert "sale.order" in result[100]
        assert "name" in result[100]["sale.order"]

    def test_add_field_to_existing_report(self):
        """add_field_to_dictionary must append field to existing report entry."""
        conn = _make_eq_connection()
        mock_ir_fields = MagicMock()
        mock_ir_model = MagicMock()
        mock_ir_model.search.return_value = [1]
        mock_ir_fields.search.return_value = [10]
        mock_field_obj = MagicMock()
        mock_field_obj.modules = "sale"
        mock_ir_fields.browse.return_value = mock_field_obj

        def mock_env_getitem(key):
            if key == "ir.model.fields":
                return mock_ir_fields
            if key == "ir.model":
                return mock_ir_model
            return MagicMock()

        conn.connection.env.__getitem__ = MagicMock(side_effect=mock_env_getitem)

        data_dict = {100: {"sale.order": ["id"], "dependencies": ["sale"]}}
        result = conn.add_field_to_dictionary(data_dict, 100, "sale.order", "partner_id", False)

        assert "partner_id" in result[100]["sale.order"]
        assert "id" in result[100]["sale.order"]

    def test_add_field_with_company_id(self):
        """add_field_to_dictionary must store company_id when provided."""
        conn = _make_eq_connection()
        mock_ir_fields = MagicMock()
        mock_ir_model = MagicMock()
        mock_ir_model.search.return_value = [1]
        mock_ir_fields.search.return_value = [10]
        mock_field_obj = MagicMock()
        mock_field_obj.modules = "account"
        mock_ir_fields.browse.return_value = mock_field_obj

        def mock_env_getitem(key):
            if key == "ir.model.fields":
                return mock_ir_fields
            if key == "ir.model":
                return mock_ir_model
            return MagicMock()

        conn.connection.env.__getitem__ = MagicMock(side_effect=mock_env_getitem)

        data_dict = {}
        result = conn.add_field_to_dictionary(data_dict, 200, "account.move", "name", 3)

        assert "company_id" in result[200]
        assert 3 in result[200]["company_id"]


# ---------------------------------------------------------------------------
# _collect_calculated_fields() tests
# ---------------------------------------------------------------------------


class TestCollectCalculatedFields:
    """Verify extraction of calculated fields from mock objects."""

    def test_collect_calculated_fields_extracts_correctly(self):
        """_collect_calculated_fields must extract field data from eq_calculated_field objects."""
        conn = _make_eq_connection()

        mock_field_1 = MagicMock()
        mock_field_1.eq_field_name = "payment_text"
        mock_field_1.eq_function_name = "eq_get_payment_terms"
        mock_field_1.eq_parameters_name = "partner_id.lang, currency_id"

        mock_field_2 = MagicMock()
        mock_field_2.eq_field_name = "total_weight"
        mock_field_2.eq_function_name = "eq_calc_weight"
        mock_field_2.eq_parameters_name = "product_id, quantity"

        result = conn._collect_calculated_fields([mock_field_1, mock_field_2])

        assert "payment_text" in result
        assert result["payment_text"]["eq_get_payment_terms"] == ["partner_id.lang", "currency_id"]
        assert "total_weight" in result
        assert result["total_weight"]["eq_calc_weight"] == ["product_id", "quantity"]

    def test_collect_calculated_fields_empty_list(self):
        """_collect_calculated_fields must return empty dict for empty list."""
        conn = _make_eq_connection()

        result = conn._collect_calculated_fields([])

        assert result == {}

    def test_collect_calculated_fields_strips_spaces(self):
        """_collect_calculated_fields must strip spaces from parameter names."""
        conn = _make_eq_connection()

        mock_field = MagicMock()
        mock_field.eq_field_name = "test_field"
        mock_field.eq_function_name = "test_func"
        mock_field.eq_parameters_name = "  param1 ,  param2 "

        result = conn._collect_calculated_fields([mock_field])

        assert result["test_field"]["test_func"] == ["param1", "param2"]


# ---------------------------------------------------------------------------
# disable_qweb_reports() tests
# ---------------------------------------------------------------------------


class TestDisableQwebReports:
    """Verify QWeb report disabling."""

    def test_disable_qweb_reports_calls_unlink_action(self):
        """disable_qweb_reports must call unlink_action for each QWeb report."""
        conn = _make_eq_connection()

        mock_ir_report = MagicMock()
        mock_ir_report.search.return_value = [1, 2, 3]

        mock_report_obj_1 = MagicMock()
        mock_report_obj_2 = MagicMock()
        mock_report_obj_3 = MagicMock()
        mock_ir_report.browse.side_effect = [mock_report_obj_1, mock_report_obj_2, mock_report_obj_3]

        conn.connection.env.__getitem__ = MagicMock(return_value=mock_ir_report)

        conn.disable_qweb_reports()

        mock_report_obj_1.unlink_action.assert_called_once()
        mock_report_obj_2.unlink_action.assert_called_once()
        mock_report_obj_3.unlink_action.assert_called_once()
        assert mock_ir_report.browse.call_count == 3

    def test_disable_qweb_reports_no_reports(self):
        """disable_qweb_reports must handle case with no QWeb reports gracefully."""
        conn = _make_eq_connection()

        mock_ir_report = MagicMock()
        mock_ir_report.search.return_value = []

        conn.connection.env.__getitem__ = MagicMock(return_value=mock_ir_report)

        # Should not raise any exception
        conn.disable_qweb_reports()

        mock_ir_report.browse.assert_not_called()
