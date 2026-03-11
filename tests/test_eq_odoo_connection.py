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
            report_name={"de_DE": "Verkaufsauftrag", "en_US": "Sales_Order"},
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
            report_name={"de_DE": "Verkaufsauftrag", "en_US": "Sales_Order"},
            IR_ACTIONS_REPORT=mock_ir_report,
            company_id=3,
        )

        assert result == 55
        call_args = mock_ir_report.search.call_args[0][0]
        assert ("company_id", "=", 3) in call_args

    def test_search_report_v13_searches_all_names_at_once(self):
        """_search_report_v13 must search all name variants in a single query."""
        conn = _make_eq_connection()
        mock_ir_report = MagicMock()
        mock_ir_report.search.return_value = [77]

        result = conn._search_report_v13(
            model_name="sale.order",
            report_name={"de_DE": "Verkaufsauftrag", "en_US": "Sales_Order"},
            IR_ACTIONS_REPORT=mock_ir_report,
            company_id=False,
        )

        assert result == 77
        # Should only need one search call with OR domain for all names
        mock_ir_report.search.assert_called_once()

    def test_search_report_v13_returns_false_when_not_found(self):
        """_search_report_v13 must return False when no reports are found."""
        conn = _make_eq_connection()
        mock_ir_report = MagicMock()
        mock_ir_report.search.return_value = []

        result = conn._search_report_v13(
            model_name="sale.order",
            report_name={"de_DE": "Nonexistent"},
            IR_ACTIONS_REPORT=mock_ir_report,
            company_id=False,
        )

        assert result is False


# ---------------------------------------------------------------------------
# _search_report() tests (EqOdooConnection override)
# ---------------------------------------------------------------------------


class TestSearchReport:
    """Verify report search with dynamic name domain."""

    def test_search_report_found(self):
        """_search_report must return ID when name matches."""
        conn = _make_eq_connection()
        mock_ir_report = MagicMock()
        mock_ir_report.search.return_value = [10]

        result = conn._search_report(
            model_name="sale.order",
            report_name={"de_DE": "Verkaufsauftrag", "en_US": "Sales_Order"},
            IR_ACTIONS_REPORT=mock_ir_report,
        )

        assert result == 10

    def test_search_report_single_query_for_all_names(self):
        """_search_report must search all name variants in one query."""
        conn = _make_eq_connection()
        mock_ir_report = MagicMock()
        mock_ir_report.search.return_value = [20]

        result = conn._search_report(
            model_name="sale.order",
            report_name={"de_DE": "Verkaufsauftrag", "en_US": "Sales_Order"},
            IR_ACTIONS_REPORT=mock_ir_report,
        )

        assert result == 20
        # Should only need one search call with all names in OR domain
        mock_ir_report.search.assert_called_once()

    def test_search_report_returns_false_when_not_found(self):
        """_search_report must return False when no names yield results."""
        conn = _make_eq_connection()
        mock_ir_report = MagicMock()
        mock_ir_report.search.return_value = []

        result = conn._search_report(
            model_name="sale.order",
            report_name={"de_DE": "Nonexistent", "en_US": "Nonexistent"},
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
            report_name={"de_DE": "Test"},
        )

        conn.connection.env.__getitem__.assert_called_with("ir.actions.report")
        assert result == 30

    def test_search_report_multi_language(self):
        """_search_report must handle 3+ languages in one query."""
        conn = _make_eq_connection()
        mock_ir_report = MagicMock()
        mock_ir_report.search.return_value = [40]

        result = conn._search_report(
            model_name="sale.order",
            report_name={"de_DE": "Verkauf", "en_US": "Sales", "fr_FR": "Ventes"},
            IR_ACTIONS_REPORT=mock_ir_report,
        )

        assert result == 40
        mock_ir_report.search.assert_called_once()
        call_args = mock_ir_report.search.call_args[0][0]
        # Should contain all name variants including PDF suffix
        assert ("name", "=ilike", "Verkauf") in call_args
        assert ("name", "=ilike", "Sales") in call_args
        assert ("name", "=ilike", "Ventes") in call_args


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
            "name": {"de_DE": "Verkaufsauftrag", "en_US": "Sales_Order"},
            "report_name": "eq_fr_core_sale_order",
            "report_type": "fast_report",
        }

        conn.write_yaml(str(output_file), data)

        assert output_file.exists()
        with open(output_file, encoding="utf8") as f:
            loaded = yaml.safe_load(f)
        assert loaded["name"] == {"de_DE": "Verkaufsauftrag", "en_US": "Sales_Order"}
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


# ---------------------------------------------------------------------------
# get_installed_languages() tests
# ---------------------------------------------------------------------------


# ---------------------------------------------------------------------------
# map_reports() tests — print_report_name multi-language
# ---------------------------------------------------------------------------


class TestMapReportsPrintReportName:
    """Verify print_report_name is written for all installed languages."""

    def _setup_map_reports(self, conn, report):
        """Helper to set up mocks for map_reports tests."""
        mock_ir_report = MagicMock()
        mock_ir_report.search.return_value = [42]
        mock_report_obj = MagicMock()
        mock_report_obj.id = 42
        mock_ir_report.browse.return_value = mock_report_obj

        mock_ctx_obj = MagicMock()
        mock_report_obj.with_context = MagicMock(return_value=mock_ctx_obj)

        mock_ir_model = MagicMock()
        mock_ir_model_fields = MagicMock()

        def mock_env_getitem(key):
            mapping = {
                "ir.actions.report": mock_ir_report,
                "ir.model": mock_ir_model,
                "ir.model.fields": mock_ir_model_fields,
            }
            return mapping.get(key, MagicMock())

        conn.connection.env.__getitem__ = MagicMock(side_effect=mock_env_getitem)
        conn.connection.env.user.company_id = 1

        return mock_report_obj, mock_ctx_obj

    def _make_report_mock(self, print_report_name):
        """Helper to create a minimal report mock."""
        report = MagicMock()
        report.entry_name = {"de_DE": "Angebot", "en_US": "Quotation"}
        report.report_name = "eq_fr_sale_order"
        report.model_name = "sale.order"
        report.company_id = False
        report._dependencies = []
        report._fields = {}
        report._calculated_fields = {}
        report._data_dictionary = {}
        report.print_report_name = print_report_name
        return report

    def test_map_reports_dict_print_report_name_per_language(self):
        """Dict print_report_name: each language gets its own expression via with_context."""
        conn = _make_eq_connection()

        installed_langs = [
            {"code": "de_DE", "iso_code": "de", "name": "German"},
            {"code": "en_US", "iso_code": "en", "name": "English"},
            {"code": "sr@latin", "iso_code": "sr", "name": "Serbian (Latin)"},
        ]
        conn.get_installed_languages = MagicMock(return_value=installed_langs)

        prn_dict = {
            "de_DE": "('Angebot-' + (object.name or '').replace('/','')",
            "en_US": "('Quotation-' + (object.name or '').replace('/','')",
        }
        report = self._make_report_mock(prn_dict)

        mock_report_obj, mock_ctx_obj = self._setup_map_reports(conn, report)

        conn.map_reports([report])

        # Collect write payloads
        write_calls = mock_ctx_obj.write.call_args_list
        prn_writes = [c for c in write_calls if "print_report_name" in c[0][0]]

        # Only de_DE and en_US are in the dict — sr@latin is NOT, so only 2 writes
        assert len(prn_writes) == 2, f"Expected 2 print_report_name writes (one per dict key), got {len(prn_writes)}"

    def test_map_reports_dict_print_report_name_correct_values(self):
        """Dict print_report_name: each language gets its correct expression value."""
        conn = _make_eq_connection()

        installed_langs = [
            {"code": "de_DE", "iso_code": "de", "name": "German"},
            {"code": "en_US", "iso_code": "en", "name": "English"},
        ]
        conn.get_installed_languages = MagicMock(return_value=installed_langs)

        prn_dict = {
            "de_DE": "('Angebot-' + (object.name or '').replace('/','')",
            "en_US": "('Quotation-' + (object.name or '').replace('/','')",
        }
        report = self._make_report_mock(prn_dict)

        mock_report_obj, mock_ctx_obj = self._setup_map_reports(conn, report)

        conn.map_reports([report])

        # Collect (lang_code, prn_value) from with_context/write calls
        ctx_calls = mock_report_obj.with_context.call_args_list
        write_calls = mock_ctx_obj.write.call_args_list

        prn_lang_values = {}
        for ctx_call, write_call in zip(ctx_calls, write_calls, strict=False):
            if "print_report_name" in write_call[0][0]:
                lang = ctx_call[1].get("lang") if ctx_call[1] else ctx_call[0][0]
                prn_lang_values[lang] = write_call[0][0]["print_report_name"]

        assert prn_lang_values.get("de_DE") == prn_dict["de_DE"]
        assert prn_lang_values.get("en_US") == prn_dict["en_US"]

    def test_map_reports_string_print_report_name_all_languages(self):
        """String print_report_name (legacy): same value written for ALL installed languages."""
        conn = _make_eq_connection()

        installed_langs = [
            {"code": "de_DE", "iso_code": "de", "name": "German"},
            {"code": "en_US", "iso_code": "en", "name": "English"},
            {"code": "sr@latin", "iso_code": "sr", "name": "Serbian (Latin)"},
        ]
        conn.get_installed_languages = MagicMock(return_value=installed_langs)

        prn_string = "('Angebot-' + (object.name or '').replace('/','')"
        report = self._make_report_mock(prn_string)

        _, mock_ctx_obj = self._setup_map_reports(conn, report)

        conn.map_reports([report])

        write_calls = mock_ctx_obj.write.call_args_list
        prn_writes = [c for c in write_calls if "print_report_name" in c[0][0]]

        # String fallback: one write per installed language (3 languages)
        assert len(prn_writes) == 3, (
            f"Expected 3 print_report_name writes (one per installed lang), got {len(prn_writes)}"
        )

        # All writes should contain the same expression
        for write_call in prn_writes:
            assert write_call[0][0]["print_report_name"] == prn_string

    def test_map_reports_skips_print_report_name_when_empty(self):
        """print_report_name should not be written when it is empty/falsy."""
        conn = _make_eq_connection()

        installed_langs = [
            {"code": "de_DE", "iso_code": "de", "name": "German"},
            {"code": "en_US", "iso_code": "en", "name": "English"},
        ]
        conn.get_installed_languages = MagicMock(return_value=installed_langs)

        report = self._make_report_mock("")  # Empty — should skip

        _, mock_ctx_obj = self._setup_map_reports(conn, report)

        conn.map_reports([report])

        write_calls = mock_ctx_obj.write.call_args_list
        prn_writes = [c for c in write_calls if "print_report_name" in c[0][0]]

        assert len(prn_writes) == 0, "print_report_name should not be written when empty"

    def test_map_reports_dict_skips_uninstalled_languages(self):
        """Dict print_report_name: languages not installed in Odoo should be skipped."""
        conn = _make_eq_connection()

        installed_langs = [
            {"code": "de_DE", "iso_code": "de", "name": "German"},
        ]
        conn.get_installed_languages = MagicMock(return_value=installed_langs)

        prn_dict = {
            "de_DE": "('Angebot-' + (object.name or '').replace('/','')",
            "fr_FR": "('Devis-' + (object.name or '').replace('/','')",  # Not installed
        }
        report = self._make_report_mock(prn_dict)

        _, mock_ctx_obj = self._setup_map_reports(conn, report)

        conn.map_reports([report])

        write_calls = mock_ctx_obj.write.call_args_list
        prn_writes = [c for c in write_calls if "print_report_name" in c[0][0]]

        # Only de_DE should be written, fr_FR is not installed
        assert len(prn_writes) == 1


class TestGetInstalledLanguages:
    """Verify installed language retrieval from res.lang."""

    def test_returns_installed_languages(self):
        """get_installed_languages must return list of active language dicts."""
        conn = _make_eq_connection()
        mock_res_lang = MagicMock()
        mock_res_lang.search.return_value = [1, 2]

        mock_lang_de = MagicMock()
        mock_lang_de.code = "de_DE"
        mock_lang_de.iso_code = "de"
        mock_lang_de.name = "German / Deutsch"

        mock_lang_en = MagicMock()
        mock_lang_en.code = "en_US"
        mock_lang_en.iso_code = "en"
        mock_lang_en.name = "English (US)"

        mock_res_lang.browse.side_effect = [mock_lang_de, mock_lang_en]

        conn.connection.env.__getitem__ = MagicMock(return_value=mock_res_lang)

        result = conn.get_installed_languages()

        assert len(result) == 2
        assert result[0]["code"] == "de_DE"
        assert result[0]["iso_code"] == "de"
        assert result[1]["code"] == "en_US"
        assert result[1]["iso_code"] == "en"

    def test_returns_empty_list_when_no_languages(self):
        """get_installed_languages must return empty list when no languages found."""
        conn = _make_eq_connection()
        mock_res_lang = MagicMock()
        mock_res_lang.search.return_value = []

        conn.connection.env.__getitem__ = MagicMock(return_value=mock_res_lang)

        result = conn.get_installed_languages()

        assert result == []

    def test_queries_active_languages_only(self):
        """get_installed_languages must filter for active=True."""
        conn = _make_eq_connection()
        mock_res_lang = MagicMock()
        mock_res_lang.search.return_value = []

        conn.connection.env.__getitem__ = MagicMock(return_value=mock_res_lang)

        conn.get_installed_languages()

        call_args = mock_res_lang.search.call_args[0][0]
        assert ("active", "=", True) in call_args


# ---------------------------------------------------------------------------
# get_company_language() tests
# ---------------------------------------------------------------------------


class TestGetCompanyLanguage:
    """Verify company language lookup from res.company.partner_id.lang."""

    def test_returns_partner_lang(self):
        """get_company_language must return partner_id.lang value."""
        conn = _make_eq_connection(language="de_DE")
        mock_company = MagicMock()
        mock_company.partner_id.lang = "en_US"
        mock_res_company = MagicMock()
        mock_res_company.browse.return_value = mock_company

        conn.connection.env.__getitem__ = MagicMock(return_value=mock_res_company)

        result = conn.get_company_language(1)

        assert result == "en_US"

    def test_fallback_when_partner_lang_empty(self):
        """get_company_language must fall back to self.language when partner_id.lang is empty."""
        conn = _make_eq_connection(language="de_DE")
        mock_company = MagicMock()
        mock_company.partner_id.lang = ""
        mock_res_company = MagicMock()
        mock_res_company.browse.return_value = mock_company

        conn.connection.env.__getitem__ = MagicMock(return_value=mock_res_company)

        result = conn.get_company_language(1)

        assert result == "de_DE"

    def test_fallback_on_exception(self):
        """get_company_language must fall back to self.language on RPC exception."""
        conn = _make_eq_connection(language="de_DE")
        mock_res_company = MagicMock()
        mock_res_company.browse.side_effect = Exception("RPC error")

        conn.connection.env.__getitem__ = MagicMock(return_value=mock_res_company)

        result = conn.get_company_language(1)

        assert result == "de_DE"

    def test_cache_prevents_second_rpc(self):
        """get_company_language must cache result — second call should not hit RPC."""
        conn = _make_eq_connection(language="de_DE")
        mock_company = MagicMock()
        mock_company.partner_id.lang = "fr_FR"
        mock_res_company = MagicMock()
        mock_res_company.browse.return_value = mock_company

        conn.connection.env.__getitem__ = MagicMock(return_value=mock_res_company)

        result1 = conn.get_company_language(1)
        result2 = conn.get_company_language(1)

        assert result1 == "fr_FR"
        assert result2 == "fr_FR"
        # browse should only be called once due to caching
        mock_res_company.browse.assert_called_once_with(1)

    def test_different_company_ids_cached_separately(self):
        """get_company_language must cache per company_id."""
        conn = _make_eq_connection(language="de_DE")

        mock_company_1 = MagicMock()
        mock_company_1.partner_id.lang = "en_US"
        mock_company_2 = MagicMock()
        mock_company_2.partner_id.lang = "fr_FR"

        mock_res_company = MagicMock()
        mock_res_company.browse.side_effect = [mock_company_1, mock_company_2]

        conn.connection.env.__getitem__ = MagicMock(return_value=mock_res_company)

        result1 = conn.get_company_language(1)
        result2 = conn.get_company_language(2)

        assert result1 == "en_US"
        assert result2 == "fr_FR"
        assert mock_res_company.browse.call_count == 2


# ---------------------------------------------------------------------------
# list_fast_reports() tests
# ---------------------------------------------------------------------------


class TestListFastReports:
    """Verify listing of FastReport entries across companies."""

    def _setup_connection_with_reports(self, conn, reports_per_company):
        """Helper to set up mocked Odoo env with FastReport entries.

        Args:
            conn: EqOdooConnection instance
            reports_per_company: dict mapping company_id to list of report dicts
                Each report dict has: id, report_name, name, model, eq_export_type
        """
        all_company_ids = list(reports_per_company.keys())
        conn.connection.env.user.company_ids.ids = all_company_ids
        conn.connection.env.user.company_ids.__bool__ = lambda s: True
        conn.connection.env.user.company_id = MagicMock()
        conn.connection.env.user.company_id.ids = all_company_ids

        mock_ir_report = MagicMock()
        mock_res_company = MagicMock()

        # Track which company is currently set to return correct reports
        current_company = {"id": all_company_ids[0]}

        def set_company(val):
            current_company["id"] = val

        type(conn.connection.env.user).company_id = property(
            lambda self: current_company["id"],
            lambda self, val: set_company(val),
        )

        def search_side_effect(domain):
            cid = current_company["id"]
            reports = reports_per_company.get(cid, [])
            return [r["id"] for r in reports]

        mock_ir_report.search = MagicMock(side_effect=search_side_effect)

        report_objs = {}
        for reports in reports_per_company.values():
            for r in reports:
                obj = MagicMock()
                obj.report_name = r["report_name"]
                obj.name = r["name"]
                obj.model = r["model"]
                obj.eq_export_type = r.get("eq_export_type", "pdf")
                report_objs[r["id"]] = obj

        mock_ir_report.browse = MagicMock(side_effect=lambda rid: report_objs[rid])

        company_names = {1: "Company A", 2: "Company B", 3: "Company C"}

        def browse_company(cid):
            obj = MagicMock()
            obj.name = company_names.get(cid, f"Company {cid}")
            return obj

        mock_res_company.browse = MagicMock(side_effect=browse_company)

        def mock_env_getitem(key):
            if key == "ir.actions.report":
                return mock_ir_report
            if key == "res.company":
                return mock_res_company
            return MagicMock()

        conn.connection.env.__getitem__ = MagicMock(side_effect=mock_env_getitem)

        return mock_ir_report

    def test_returns_correct_structure(self):
        """list_fast_reports must return list of dicts with expected keys."""
        conn = _make_eq_connection()
        self._setup_connection_with_reports(
            conn,
            {
                1: [{"id": 10, "report_name": "eq_fr_sale", "name": "Sales Order", "model": "sale.order"}],
            },
        )

        result = conn.list_fast_reports()

        assert len(result) == 1
        r = result[0]
        assert r["id"] == 10
        assert r["report_name"] == "eq_fr_sale"
        assert r["name"] == "Sales Order"
        assert r["model"] == "sale.order"
        assert r["company"] == "Company A"
        assert "export_type" in r

    def test_deduplicates_by_report_name(self):
        """list_fast_reports must deduplicate reports with the same report_name."""
        conn = _make_eq_connection()
        self._setup_connection_with_reports(
            conn,
            {
                1: [
                    {"id": 10, "report_name": "eq_fr_sale", "name": "Sales", "model": "sale.order"},
                ],
                2: [
                    {"id": 20, "report_name": "eq_fr_sale", "name": "Sales", "model": "sale.order"},
                ],
            },
        )

        result = conn.list_fast_reports()

        assert len(result) == 1
        assert result[0]["id"] == 10

    def test_multiple_reports_across_companies(self):
        """list_fast_reports must collect unique reports from all companies."""
        conn = _make_eq_connection()
        self._setup_connection_with_reports(
            conn,
            {
                1: [
                    {"id": 10, "report_name": "eq_fr_sale", "name": "Sales", "model": "sale.order"},
                ],
                2: [
                    {"id": 20, "report_name": "eq_fr_invoice", "name": "Invoice", "model": "account.move"},
                ],
            },
        )

        result = conn.list_fast_reports()

        assert len(result) == 2
        names = {r["report_name"] for r in result}
        assert names == {"eq_fr_sale", "eq_fr_invoice"}

    def test_empty_database(self):
        """list_fast_reports must return empty list when no FastReports exist."""
        conn = _make_eq_connection()
        self._setup_connection_with_reports(conn, {1: []})

        result = conn.list_fast_reports()

        assert result == []


# ---------------------------------------------------------------------------
# collect_report_entries() with filter tests
# ---------------------------------------------------------------------------


class TestCollectReportEntries:
    """Verify collect_report_entries with optional report_ids filter."""

    def test_collect_all_report_entries_delegates(self):
        """collect_all_report_entries must delegate to collect_report_entries."""
        conn = _make_eq_connection()
        conn.collect_report_entries = MagicMock()

        conn.collect_all_report_entries("/tmp/output")

        conn.collect_report_entries.assert_called_once_with("/tmp/output")

    def test_collect_report_entries_with_filter_adds_domain(self):
        """collect_report_entries with report_ids must add ID filter to search domain."""
        conn = _make_eq_connection()

        mock_ir_report = MagicMock()
        mock_ir_report.search.return_value = []
        mock_ir_model_fields = MagicMock()
        mock_ir_model_fields.search.return_value = []

        conn.connection.env.user.company_ids.ids = [1]
        conn.connection.env.user.company_ids.__bool__ = lambda s: True

        mock_res_company = MagicMock()
        mock_company_obj = MagicMock()
        mock_company_obj.name = "Test Co"
        mock_res_company.browse.return_value = mock_company_obj

        def mock_env_getitem(key):
            if key in ("ir.actions.report",):
                return mock_ir_report
            if key == "ir.model.fields":
                return mock_ir_model_fields
            if key == "res.company":
                return mock_res_company
            return MagicMock()

        conn.connection.env.__getitem__ = MagicMock(side_effect=mock_env_getitem)

        conn.collect_report_entries("/tmp/output", report_ids=[10, 20])

        # Verify the search domain includes the ID filter
        search_call = mock_ir_report.search.call_args[0][0]
        assert ("id", "in", [10, 20]) in search_call

    def test_collect_report_entries_without_filter_no_id_domain(self):
        """collect_report_entries without report_ids must not add ID filter."""
        conn = _make_eq_connection()

        mock_ir_report = MagicMock()
        mock_ir_report.search.return_value = []
        mock_ir_model_fields = MagicMock()
        mock_ir_model_fields.search.return_value = []

        conn.connection.env.user.company_ids.ids = [1]
        conn.connection.env.user.company_ids.__bool__ = lambda s: True

        mock_res_company = MagicMock()
        mock_company_obj = MagicMock()
        mock_company_obj.name = "Test Co"
        mock_res_company.browse.return_value = mock_company_obj

        def mock_env_getitem(key):
            if key in ("ir.actions.report",):
                return mock_ir_report
            if key == "ir.model.fields":
                return mock_ir_model_fields
            if key == "res.company":
                return mock_res_company
            return MagicMock()

        conn.connection.env.__getitem__ = MagicMock(side_effect=mock_env_getitem)

        conn.collect_report_entries("/tmp/output")

        # Verify the search domain does NOT include ID filter
        search_call = mock_ir_report.search.call_args[0][0]
        id_filters = [d for d in search_call if len(d) == 3 and d[0] == "id" and d[1] == "in"]
        assert len(id_filters) == 0


# ---------------------------------------------------------------------------
# map_reports() tests — attachment dict resolution
# ---------------------------------------------------------------------------


class TestMapReportsAttachment:
    """Verify attachment dict is resolved based on company language."""

    def _setup_map_reports(self, conn, report):
        """Helper to set up mocks for map_reports tests."""
        mock_ir_report = MagicMock()
        mock_ir_report.search.return_value = [42]
        mock_report_obj = MagicMock()
        mock_report_obj.id = 42
        mock_ir_report.browse.return_value = mock_report_obj

        mock_ctx_obj = MagicMock()
        mock_report_obj.with_context = MagicMock(return_value=mock_ctx_obj)

        mock_ir_model = MagicMock()
        mock_ir_model_fields = MagicMock()

        def mock_env_getitem(key):
            mapping = {
                "ir.actions.report": mock_ir_report,
                "ir.model": mock_ir_model,
                "ir.model.fields": mock_ir_model_fields,
            }
            return mapping.get(key, MagicMock())

        conn.connection.env.__getitem__ = MagicMock(side_effect=mock_env_getitem)
        conn.connection.env.user.company_id = 1

        return mock_ir_report, mock_report_obj

    def _make_report_mock(self, attachment, company_id=False):
        """Helper to create a minimal report mock with attachment."""
        report = MagicMock()
        report.entry_name = {"de_DE": "Angebot", "en_US": "Quotation"}
        report.report_name = "eq_fr_sale_order"
        report.model_name = "sale.order"
        report.company_id = company_id
        report._dependencies = []
        report._fields = {}
        report._calculated_fields = {}
        report._data_dictionary = {}
        report.print_report_name = ""
        report.attachment = attachment

        # Make self_ensure() populate _data_dictionary like the real implementation
        def mock_self_ensure():
            report._data_dictionary = {
                "name": "Angebot",
                "report_name": report.report_name,
                "report_type": "fast_report",
                "print_report_name": "",
                "model": report.model_name,
                "company_id": report.company_id[0] if report.company_id else False,
                "eq_export_type": "pdf",
                "eq_ignore_images": True,
                "eq_handling_html_fields": "standard",
                "eq_multiprint": "standard",
                "multi": False,
                "attachment": attachment if not isinstance(attachment, dict) else "Angebot.pdf",
                "attachment_use": False,
                "eq_print_button": False,
            }

        report.self_ensure = mock_self_ensure
        return report

    def test_dict_attachment_resolved_by_company_lang(self):
        """Dict attachment must be resolved to company language value."""
        conn = _make_eq_connection(language="de_DE")

        installed_langs = [
            {"code": "de_DE", "iso_code": "de", "name": "German"},
            {"code": "en_US", "iso_code": "en", "name": "English"},
        ]
        conn.get_installed_languages = MagicMock(return_value=installed_langs)

        # Mock company language lookup to return en_US
        conn.get_company_language = MagicMock(return_value="en_US")

        attachment_dict = {"de_DE": "Angebot.pdf", "en_US": "Quotation.pdf"}
        report = self._make_report_mock(attachment_dict, company_id=[5])

        self._setup_map_reports(conn, report)

        conn.map_reports([report])

        # The data_dictionary should have the en_US value since company speaks English
        assert report._data_dictionary["attachment"] == "Quotation.pdf"

    def test_string_attachment_unchanged(self):
        """String attachment must pass through unchanged."""
        conn = _make_eq_connection(language="de_DE")

        installed_langs = [
            {"code": "de_DE", "iso_code": "de", "name": "German"},
        ]
        conn.get_installed_languages = MagicMock(return_value=installed_langs)

        report = self._make_report_mock("Report.pdf")

        self._setup_map_reports(conn, report)

        conn.map_reports([report])

        # String attachment is set by self_ensure() and should stay unchanged
        assert report._data_dictionary["attachment"] == "Report.pdf"

    def test_dict_attachment_without_company_id_uses_connection_language(self):
        """Dict attachment without company_id must use self.language as fallback."""
        conn = _make_eq_connection(language="de_DE")

        installed_langs = [
            {"code": "de_DE", "iso_code": "de", "name": "German"},
            {"code": "en_US", "iso_code": "en", "name": "English"},
        ]
        conn.get_installed_languages = MagicMock(return_value=installed_langs)

        attachment_dict = {"de_DE": "Angebot.pdf", "en_US": "Quotation.pdf"}
        report = self._make_report_mock(attachment_dict, company_id=False)

        self._setup_map_reports(conn, report)

        conn.map_reports([report])

        # No company_id -> should use self.language (de_DE)
        assert report._data_dictionary["attachment"] == "Angebot.pdf"
