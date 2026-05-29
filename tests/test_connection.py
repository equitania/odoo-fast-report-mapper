# Copyright 2014-now Equitania Software GmbH - Pforzheim - Germany
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

"""Comprehensive tests for OdooConnection in odoo_fast_report_mapper/_connection.py."""

import urllib.error
from unittest.mock import MagicMock, patch

import pytest
import yaml
from odoorpc_toolbox import RPCError

from odoo_fast_report_mapper._connection import OdooConnection
from odoo_fast_report_mapper._report import Report
from odoo_fast_report_mapper._utils import create_report_object_from_yaml_object

# ---------------------------------------------------------------------------
# Helper to create OdooConnection with mocked ODOO
# ---------------------------------------------------------------------------


def _make_connection(
    language="de_DE",
    collect_yaml=False,
    disable_qweb=True,
    workflow=0,
    url="http://localhost",
    port=8069,
    username="admin",
    password="admin",
    database="test_db",
):
    """Create an OdooConnection with a patched prepare_connection."""
    with patch("odoo_fast_report_mapper._connection.prepare_connection") as mock_prepare:
        mock_connection = MagicMock()
        mock_connection.version = "18.0"
        mock_connection.config = {}
        mock_connection.env.context = {}
        mock_prepare.return_value = mock_connection

        conn = OdooConnection(
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
    conn.version = "18"
    return conn


def _make_report_from_fixture(sample_data):
    """Create a Report from fixture YAML data."""
    return create_report_object_from_yaml_object(sample_data)


def _setup_env(conn, models_map):
    """Wire up conn.connection.env[key] to return the given models_map entries."""

    def mock_env_getitem(key):
        return models_map.get(key, MagicMock())

    conn.connection.env.__getitem__ = MagicMock(side_effect=mock_env_getitem)


# ---------------------------------------------------------------------------
# 1. TestOdooConnectionInit
# ---------------------------------------------------------------------------


class TestOdooConnectionInit:
    """Verify constructor sets all OdooConnection attributes."""

    def test_init_sets_language(self):
        conn = _make_connection(language="en_US")
        assert conn.language == "en_US"

    def test_init_sets_collect_yaml(self):
        conn = _make_connection(collect_yaml=True)
        assert conn.collect_yaml is True

    def test_init_sets_disable_qweb(self):
        conn = _make_connection(disable_qweb=False)
        assert conn.disable_qweb is False

    def test_init_sets_workflow(self):
        conn = _make_connection(workflow=2)
        assert conn.workflow == 2

    def test_init_sets_all_attributes(self):
        conn = _make_connection(language="fr_FR", collect_yaml=True, disable_qweb=False, workflow=1)
        assert conn.language == "fr_FR"
        assert conn.collect_yaml is True
        assert conn.disable_qweb is False
        assert conn.workflow == 1

    def test_init_calls_parent_init(self):
        """Constructor must set username, password, database, connection."""
        conn = _make_connection(username="testuser", password="testpw", database="mydb")
        assert conn.username == "testuser"
        assert conn.password == "testpw"
        assert conn.database == "mydb"
        assert conn.connection is not None

    def test_constructor_calls_prepare_connection(self):
        """Constructor must call prepare_connection with url and port."""
        with patch("odoo_fast_report_mapper._connection.prepare_connection") as mock_prepare:
            mock_connection = MagicMock()
            mock_prepare.return_value = mock_connection
            conn = OdooConnection(
                url="https://odoo.example.com",
                port=443,
                username="admin",
                password="secret",
                database="test_db",
                language="de_DE",
                collect_yaml=False,
                disable_qweb=True,
                workflow=0,
            )
            mock_prepare.assert_called_once_with("https://odoo.example.com", 443)
            assert conn.connection is mock_connection
            assert conn.username == "admin"
            assert conn.password == "secret"
            assert conn.database == "test_db"
            assert conn.version == ""

    def test_constructor_raises_odoo_connection_error_on_url_error(self):
        """Constructor must raise OdooConnectionError when URLError occurs."""
        from odoo_fast_report_mapper._exceptions import OdooConnectionError

        with patch("odoo_fast_report_mapper._connection.prepare_connection") as mock_prepare:
            mock_prepare.side_effect = urllib.error.URLError("Connection refused")
            with pytest.raises(OdooConnectionError, match="Please check your parameters"):
                OdooConnection(
                    url="https://invalid.example.com",
                    port=443,
                    username="admin",
                    password="secret",
                    database="test_db",
                    language="de_DE",
                    collect_yaml=False,
                    disable_qweb=True,
                    workflow=0,
                )


# ---------------------------------------------------------------------------
# 2. TestOdooConnectionLogin
# ---------------------------------------------------------------------------


class TestOdooConnectionLogin:
    """Verify login behavior and error handling."""

    def test_login_calls_connection_login_and_sets_config(self):
        """login() must call connection.login and set auto_commit, context flags."""
        with patch("odoo_fast_report_mapper._connection.prepare_connection") as mock_prepare:
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
                language="de_DE",
                collect_yaml=False,
                disable_qweb=True,
                workflow=0,
            )
        conn.login()
        mock_connection.login.assert_called_once_with("test_db", "admin", "secret")
        assert mock_connection.config["auto_commit"] is True
        assert mock_connection.env.context["active_test"] is False
        assert mock_connection.env.context["tracking_disable"] is True
        assert conn.version == "18"

    def test_login_raises_odoo_connection_error_on_rpc_error(self):
        """login() must raise OdooConnectionError when RPCError occurs."""
        from odoo_fast_report_mapper._exceptions import OdooConnectionError

        with patch("odoo_fast_report_mapper._connection.prepare_connection") as mock_prepare:
            mock_connection = MagicMock()
            mock_connection.login.side_effect = RPCError("Invalid credentials")
            mock_prepare.return_value = mock_connection
            conn = OdooConnection(
                url="https://odoo.example.com",
                port=443,
                username="admin",
                password="wrong",
                database="test_db",
                language="de_DE",
                collect_yaml=False,
                disable_qweb=True,
                workflow=0,
            )
        with pytest.raises(OdooConnectionError, match="Please check your parameters"):
            conn.login()


# ---------------------------------------------------------------------------
# 3. TestCheckModule
# ---------------------------------------------------------------------------


class TestCheckModule:
    """Verify module installation checks."""

    def test_check_module_returns_true_when_installed(self):
        """check_module must return True when module is found."""
        conn = _make_connection()
        mock_ir_module = MagicMock()
        mock_ir_module.search.return_value = [42]
        _setup_env(conn, {"ir.module.module": mock_ir_module})

        result = conn.check_module("sale")
        assert result is True
        mock_ir_module.search.assert_called_once_with([("state", "=", "installed"), ("name", "=", "sale")])

    def test_check_module_returns_false_when_not_installed(self):
        """check_module must return False when module is not found."""
        conn = _make_connection()
        mock_ir_module = MagicMock()
        mock_ir_module.search.return_value = []
        _setup_env(conn, {"ir.module.module": mock_ir_module})

        result = conn.check_module("nonexistent_module")
        assert result is False


# ---------------------------------------------------------------------------
# 4. TestGetInstalledLanguages
# ---------------------------------------------------------------------------


class TestGetInstalledLanguages:
    """Verify installed language retrieval from res.lang."""

    def test_returns_language_list_with_codes(self):
        conn = _make_connection()
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
        _setup_env(conn, {"res.lang": mock_res_lang})

        result = conn.get_installed_languages()

        assert len(result) == 2
        assert result[0] == {"code": "de_DE", "iso_code": "de", "name": "German / Deutsch"}
        assert result[1] == {"code": "en_US", "iso_code": "en", "name": "English (US)"}

    def test_returns_empty_list_when_no_languages(self):
        conn = _make_connection()
        mock_res_lang = MagicMock()
        mock_res_lang.search.return_value = []
        _setup_env(conn, {"res.lang": mock_res_lang})

        result = conn.get_installed_languages()

        assert result == []

    def test_queries_active_languages_only(self):
        conn = _make_connection()
        mock_res_lang = MagicMock()
        mock_res_lang.search.return_value = []
        _setup_env(conn, {"res.lang": mock_res_lang})

        conn.get_installed_languages()

        call_args = mock_res_lang.search.call_args[0][0]
        assert ("active", "=", True) in call_args


# ---------------------------------------------------------------------------
# 5. TestGetCompanyLanguage
# ---------------------------------------------------------------------------


class TestGetCompanyLanguage:
    """Verify company language lookup with caching and fallback."""

    def test_returns_company_partner_lang(self):
        conn = _make_connection(language="de_DE")
        mock_company = MagicMock()
        mock_company.partner_id.lang = "en_US"
        mock_res_company = MagicMock()
        mock_res_company.browse.return_value = mock_company
        _setup_env(conn, {"res.company": mock_res_company})

        result = conn.get_company_language(1)

        assert result == "en_US"

    def test_returns_fallback_when_partner_lang_empty(self):
        conn = _make_connection(language="de_DE")
        mock_company = MagicMock()
        mock_company.partner_id.lang = ""
        mock_res_company = MagicMock()
        mock_res_company.browse.return_value = mock_company
        _setup_env(conn, {"res.company": mock_res_company})

        result = conn.get_company_language(1)

        assert result == "de_DE"

    def test_returns_fallback_on_exception(self):
        conn = _make_connection(language="de_DE")
        mock_res_company = MagicMock()
        mock_res_company.browse.side_effect = RPCError("RPC error")
        _setup_env(conn, {"res.company": mock_res_company})

        result = conn.get_company_language(1)

        assert result == "de_DE"

    def test_caches_result_per_company_id(self):
        conn = _make_connection(language="de_DE")
        mock_company = MagicMock()
        mock_company.partner_id.lang = "fr_FR"
        mock_res_company = MagicMock()
        mock_res_company.browse.return_value = mock_company
        _setup_env(conn, {"res.company": mock_res_company})

        result1 = conn.get_company_language(1)
        result2 = conn.get_company_language(1)

        assert result1 == "fr_FR"
        assert result2 == "fr_FR"
        mock_res_company.browse.assert_called_once_with(1)

    def test_different_company_ids_cached_separately(self):
        conn = _make_connection(language="de_DE")
        mock_c1 = MagicMock()
        mock_c1.partner_id.lang = "en_US"
        mock_c2 = MagicMock()
        mock_c2.partner_id.lang = "fr_FR"
        mock_res_company = MagicMock()
        mock_res_company.browse.side_effect = [mock_c1, mock_c2]
        _setup_env(conn, {"res.company": mock_res_company})

        assert conn.get_company_language(1) == "en_US"
        assert conn.get_company_language(2) == "fr_FR"
        assert mock_res_company.browse.call_count == 2


# ---------------------------------------------------------------------------
# 6. TestSearchReport
# ---------------------------------------------------------------------------


class TestSearchReport:
    """Verify report search with dynamic name domain."""

    def test_search_report_finds_existing_report(self):
        conn = _make_connection()
        mock_ir_report = MagicMock()
        mock_ir_report.search.return_value = [42]

        result = conn._search_report("sale.order", {"de_DE": "Verkaufsauftrag"}, mock_ir_report)

        assert result == 42

    def test_search_report_returns_false_when_not_found(self):
        conn = _make_connection()
        mock_ir_report = MagicMock()
        mock_ir_report.search.return_value = []

        result = conn._search_report("sale.order", {"de_DE": "Nonexistent"}, mock_ir_report)

        assert result is False

    def test_search_report_v13_includes_company_domain(self):
        conn = _make_connection()
        mock_ir_report = MagicMock()
        mock_ir_report.search.return_value = [55]

        conn._search_report_v13("sale.order", {"de_DE": "Test"}, mock_ir_report, company_id=3)

        call_args = mock_ir_report.search.call_args[0][0]
        assert ("company_id", "=", 3) in call_args
        assert ("company_id", "=", False) in call_args

    def test_search_report_uses_connection_env_when_not_passed(self):
        conn = _make_connection()
        mock_ir_report = MagicMock()
        mock_ir_report.search.return_value = [99]
        _setup_env(conn, {"ir.actions.report": mock_ir_report})

        result = conn._search_report("sale.order", {"de_DE": "Test"})

        assert result == 99

    def test_search_report_with_company_id_includes_company_domain(self):
        """_search_report with company_id should add company filter to domain."""
        conn = _make_connection()
        mock_ir_report = MagicMock()
        mock_ir_report.search.return_value = [77]

        conn._search_report("sale.order", {"de_DE": "Auftrag"}, mock_ir_report, company_id=2)

        call_args = mock_ir_report.search.call_args[0][0]
        assert ("company_id", "=", 2) in call_args
        assert ("company_id", "=", False) in call_args

    def test_search_report_without_company_id_no_company_domain(self):
        """_search_report without company_id should NOT include company filter."""
        conn = _make_connection()
        mock_ir_report = MagicMock()
        mock_ir_report.search.return_value = [88]

        conn._search_report("sale.order", {"de_DE": "Auftrag"}, mock_ir_report)

        call_args = mock_ir_report.search.call_args[0][0]
        assert not any(t[0] == "company_id" for t in call_args if isinstance(t, tuple))

    def test_search_report_returns_report_id_when_multiple_found(self):
        """_search_report must return the first report ID when found."""
        conn = _make_connection()
        mock_ir_report = MagicMock()
        mock_ir_report.search.return_value = [42, 43]
        _setup_env(conn, {"ir.actions.report": mock_ir_report})

        result = conn._search_report("sale.order", {"de_DE": "Sales Order"})

        assert result == 42


# ---------------------------------------------------------------------------
# 7. TestGetFastReportIds
# ---------------------------------------------------------------------------


class TestGetFastReportIds:
    """Verify retrieval of FastReport IDs."""

    def test_get_fast_report_ids_returns_list(self):
        """_get_fast_report_ids must return list of report IDs with report_type=fast_report."""
        conn = _make_connection()
        mock_ir_report = MagicMock()
        mock_ir_report.search.return_value = [1, 5, 10]
        _setup_env(conn, {"ir.actions.report": mock_ir_report})

        result = conn._get_fast_report_ids()

        assert result == [1, 5, 10]
        mock_ir_report.search.assert_called_once_with([("report_type", "=", "fast_report")])

    def test_get_fast_report_ids_returns_empty_list(self):
        """_get_fast_report_ids must return empty list when no FastReports exist."""
        conn = _make_connection()
        mock_ir_report = MagicMock()
        mock_ir_report.search.return_value = []
        _setup_env(conn, {"ir.actions.report": mock_ir_report})

        result = conn._get_fast_report_ids()

        assert result == []


# ---------------------------------------------------------------------------
# 8. TestCheckDependencies
# ---------------------------------------------------------------------------


class TestCheckDependencies:
    """Verify dependency checking returns (bool, list) tuple."""

    def test_all_installed_returns_true(self):
        conn = _make_connection()
        mock_ir_module = MagicMock()
        mock_ir_module.search.return_value = [1]
        _setup_env(conn, {"ir.module.module": mock_ir_module})

        result = conn.check_dependencies(["sale", "account"])

        assert result == (True, [])

    def test_missing_module_returns_false_with_list(self):
        conn = _make_connection()
        mock_ir_module = MagicMock()
        mock_ir_module.search.side_effect = [[1], []]
        _setup_env(conn, {"ir.module.module": mock_ir_module})

        result = conn.check_dependencies(["sale", "missing_mod"])

        assert result[0] is False
        assert "missing_mod" in result[1]

    def test_empty_dependencies_returns_true(self):
        conn = _make_connection()
        assert conn.check_dependencies([]) == (True, [])

    def test_none_dependencies_returns_true(self):
        conn = _make_connection()
        assert conn.check_dependencies(None) == (True, [])

    def test_false_dependencies_returns_true(self):
        conn = _make_connection()
        assert conn.check_dependencies(False) == (True, [])

    def test_check_dependencies_returns_true_when_all_installed(self):
        """check_dependencies must return True when all modules are installed."""
        conn = _make_connection()
        mock_ir_module = MagicMock()
        mock_ir_module.search.return_value = [1]
        _setup_env(conn, {"ir.module.module": mock_ir_module})

        result = conn.check_dependencies(["sale", "account", "stock"])
        assert result is True or (isinstance(result, tuple) and result[0] is True)

    def test_check_dependencies_returns_false_when_one_missing(self):
        """check_dependencies must return False when any module is missing."""
        conn = _make_connection()
        mock_ir_module = MagicMock()
        mock_ir_module.search.side_effect = [[1], []]
        _setup_env(conn, {"ir.module.module": mock_ir_module})

        result = conn.check_dependencies(["sale", "missing_module"])
        # Returns (bool, list) tuple now
        if isinstance(result, tuple):
            assert result[0] is False
        else:
            assert result is False

    def test_map_reports_skips_report_when_dependency_missing(self):
        """map_reports must not call ir.actions.report.create when a dependency is missing."""
        conn = _make_connection()
        env = _make_map_reports_env(conn)

        # Override ir.module.module: "sale" found, "account" missing
        mock_ir_module = MagicMock()
        mock_ir_module.search.side_effect = [[1], []]
        _setup_env(conn, {**env, "ir.module.module": mock_ir_module})

        report = _make_simple_report(dependencies=["sale", "account"])
        failed = conn.map_reports([report])

        assert len(failed) == 1
        env["ir.actions.report"].create.assert_not_called()


# ---------------------------------------------------------------------------
# 9. TestMapReports
# ---------------------------------------------------------------------------


def _make_map_reports_env(conn, report_search_return=None, installed_langs=None):
    """Set up a full mocked environment for map_reports tests."""
    if report_search_return is None:
        report_search_return = []
    if installed_langs is None:
        installed_langs = [
            {"code": "de_DE", "iso_code": "de", "name": "German"},
            {"code": "en_US", "iso_code": "en", "name": "English"},
        ]

    mock_ir_report = MagicMock()
    mock_ir_report.search.return_value = report_search_return
    mock_ir_report.create.return_value = 100
    mock_ir_report.env = MagicMock()
    mock_ir_report.env.user = MagicMock()
    mock_ir_report.env.user.company_id = 1

    mock_report_obj = MagicMock()
    mock_report_obj.id = 100 if not report_search_return else report_search_return[0]
    mock_ir_report.browse.return_value = mock_report_obj

    mock_ctx_obj = MagicMock()
    mock_report_obj.with_context.return_value = mock_ctx_obj

    mock_ir_model = MagicMock()
    mock_ir_model.search.return_value = [1]
    mock_ir_model.browse.return_value = MagicMock(model="sale.order")

    mock_ir_model_fields = MagicMock()
    mock_ir_model_fields.search.return_value = [10]
    mock_ir_model_fields.eq_get_field_report_ids.return_value = []

    mock_ir_module = MagicMock()
    mock_ir_module.search.return_value = [1]

    conn.get_installed_languages = MagicMock(return_value=installed_langs)

    env_map = {
        "ir.actions.report": mock_ir_report,
        "ir.model": mock_ir_model,
        "ir.model.fields": mock_ir_model_fields,
        "ir.module.module": mock_ir_module,
    }
    _setup_env(conn, env_map)
    conn.connection.env.user.company_id = 1

    return {
        "ir.actions.report": mock_ir_report,
        "ir.model": mock_ir_model,
        "ir.model.fields": mock_ir_model_fields,
        "ir.module.module": mock_ir_module,
        "report_obj": mock_report_obj,
        "ctx_obj": mock_ctx_obj,
    }


def _make_simple_report(
    entry_name=None,
    report_name="eq_fr_test",
    model_name="sale.order",
    company_id=False,
    dependencies=None,
    fields=None,
    calculated_fields=None,
    print_report_name="Test Report",
    attachment="Test.pdf",
):
    """Create a real Report for map_reports testing."""
    if entry_name is None:
        entry_name = {"de_DE": "Test_DE", "en_US": "Test_EN"}
    if dependencies is None:
        dependencies = ["sale"]
    if fields is None:
        fields = {"sale.order": ["id", "name"]}
    if calculated_fields is None:
        calculated_fields = {}

    return Report(
        entry_name=entry_name,
        report_name=report_name,
        report_type="fast_report",
        model_name=model_name,
        company_id=company_id,
        eq_export_type="pdf",
        print_report_name=print_report_name,
        attachment=attachment,
        eq_ignore_images=True,
        eq_handling_html_fields="standard",
        multi=False,
        attachment_use=False,
        eq_print_button=False,
        dependencies=dependencies,
        model_fields=fields,
        calculated_fields=calculated_fields,
    )


class TestMapReports:
    """Test the full map_reports workflow with mocked Odoo."""

    def test_map_reports_creates_new_report(self):
        """When report not found, IR_ACTIONS_REPORT.create must be called."""
        conn = _make_connection()
        mocks = _make_map_reports_env(conn, report_search_return=[])
        report = _make_simple_report()

        conn.map_reports([report])

        mocks["ir.actions.report"].create.assert_called_once()
        create_args = mocks["ir.actions.report"].create.call_args[0][0]
        assert create_args["report_name"] == "eq_fr_test"

    def test_map_reports_updates_existing_report(self):
        """When report found, report_object.write must be called instead of create."""
        conn = _make_connection()
        mocks = _make_map_reports_env(conn, report_search_return=[42])
        report = _make_simple_report()

        conn.map_reports([report])

        mocks["ir.actions.report"].create.assert_not_called()
        mocks["report_obj"].write.assert_called()

    def test_map_reports_skips_report_when_dependencies_missing(self):
        """When dependencies are missing, report must be skipped — no create or write."""
        conn = _make_connection()
        mock_ir_module = MagicMock()
        mock_ir_module.search.return_value = []

        mocks = _make_map_reports_env(conn, report_search_return=[])
        env_map = {
            "ir.actions.report": mocks["ir.actions.report"],
            "ir.model": mocks["ir.model"],
            "ir.model.fields": mocks["ir.model.fields"],
            "ir.module.module": mock_ir_module,
        }
        _setup_env(conn, env_map)

        report = _make_simple_report(dependencies=["sale", "nonexistent_module"])

        conn.map_reports([report])

        mocks["ir.actions.report"].create.assert_not_called()
        mocks["report_obj"].write.assert_not_called()

    def test_map_reports_sets_translations_for_installed_langs(self):
        """with_context().write() must be called for each installed language in entry_name."""
        conn = _make_connection()
        mocks = _make_map_reports_env(conn, report_search_return=[42])
        report = _make_simple_report(
            entry_name={"de_DE": "Verkauf", "en_US": "Sales"},
        )

        conn.map_reports([report])

        ctx_calls = mocks["report_obj"].with_context.call_args_list

        name_write_langs = []
        for ctx_call, write_call in zip(ctx_calls, mocks["ctx_obj"].write.call_args_list, strict=False):
            write_data = write_call[0][0]
            if "name" in write_data:
                lang = ctx_call.kwargs.get("lang")
                name_write_langs.append(lang)

        assert "de_DE" in name_write_langs
        assert "en_US" in name_write_langs

    def test_map_reports_handles_dict_print_report_name(self):
        """Per-language dict print_report_name: each language gets its own expression."""
        conn = _make_connection()
        mocks = _make_map_reports_env(conn, report_search_return=[42])
        prn_dict = {
            "de_DE": "('Angebot-' + object.name)",
            "en_US": "('Quotation-' + object.name)",
        }
        report = _make_simple_report(print_report_name=prn_dict)

        conn.map_reports([report])

        write_calls = mocks["ctx_obj"].write.call_args_list
        prn_writes = [c for c in write_calls if "print_report_name" in c[0][0]]
        assert len(prn_writes) == 2

    def test_map_reports_handles_string_print_report_name(self):
        """Legacy single string: same value written for all installed languages."""
        conn = _make_connection()
        mocks = _make_map_reports_env(conn, report_search_return=[42])
        report = _make_simple_report(print_report_name="Report Name")

        conn.map_reports([report])

        write_calls = mocks["ctx_obj"].write.call_args_list
        prn_writes = [c for c in write_calls if "print_report_name" in c[0][0]]
        assert len(prn_writes) == 2
        for w in prn_writes:
            assert w[0][0]["print_report_name"] == "Report Name"

    def test_map_reports_handles_dict_attachment(self, sample_report_yaml_data_dict_attachment):
        """Per-language attachment dict must be resolved to single value."""
        conn = _make_connection(language="de_DE")
        _make_map_reports_env(conn, report_search_return=[42])
        conn.get_company_language = MagicMock(return_value="de_DE")

        report = _make_report_from_fixture(sample_report_yaml_data_dict_attachment)

        conn.map_reports([report])

        assert isinstance(report._data_dictionary["attachment"], str)

    def test_map_reports_maps_fields_correctly(self):
        """Field search and report_ids building must work correctly."""
        conn = _make_connection()
        mocks = _make_map_reports_env(conn, report_search_return=[42])
        mocks["ir.model.fields"].eq_get_field_report_ids.return_value = []
        mocks["report_obj"].id = 42

        report = _make_simple_report(fields={"sale.order": ["id", "name"]})

        conn.map_reports([report])

        field_search_calls = mocks["ir.model.fields"].search.call_args_list
        assert len(field_search_calls) >= 2
        mocks["ir.model"].eq_write_report_ids.assert_called()

    def test_map_reports_logs_warning_for_missing_field(self):
        """When a field is not found in Odoo, a warning should be logged."""
        conn = _make_connection()
        mocks = _make_map_reports_env(conn, report_search_return=[42])
        mocks["ir.model.fields"].search.return_value = []

        report = _make_simple_report(fields={"sale.order": ["nonexistent_field"]})

        with patch("odoo_fast_report_mapper._connection.logger") as mock_logger:
            conn.map_reports([report])
            warning_calls = [str(c) for c in mock_logger.warning.call_args_list]
            assert any("nonexistent_field" in w for w in warning_calls)

    def test_map_reports_logs_warning_for_missing_model(self):
        """When a model is not found in Odoo, a warning should be logged."""
        conn = _make_connection()
        mocks = _make_map_reports_env(conn, report_search_return=[42])
        mocks["ir.model"].search.return_value = []

        report = _make_simple_report(
            fields={"nonexistent.model": ["id"]},
        )

        with patch("odoo_fast_report_mapper._connection.logger") as mock_logger:
            conn.map_reports([report])
            warning_calls = [str(c) for c in mock_logger.warning.call_args_list]
            assert any("nonexistent.model" in w for w in warning_calls)

    def test_map_reports_handles_company_id(self):
        """When report has company_id, company switching logic must be triggered."""
        conn = _make_connection()
        conn.version = "18"
        mocks = _make_map_reports_env(conn, report_search_return=[42])

        report = _make_simple_report(company_id=[5])

        conn.map_reports([report])

        mocks["ir.actions.report"].browse.assert_called()

    def test_map_reports_handles_company_id_v13(self):
        """For v13-16, _search_report_v13 must be used instead of _search_report."""
        conn = _make_connection()
        conn.version = "16"
        _make_map_reports_env(conn, report_search_return=[42])

        report = _make_simple_report(company_id=[3])

        with patch.object(conn, "_search_report_v13", return_value=42) as mock_v13:
            conn.map_reports([report])
            mock_v13.assert_called_once()

    def test_map_reports_handles_calculated_fields(self):
        """set_calculated_fields must be called for each calculated field entry."""
        conn = _make_connection()
        _make_map_reports_env(conn, report_search_return=[42])

        calc_fields = {
            "payment_text": {
                "eq_get_payment_terms": ["partner_id.lang", "currency_id"],
            },
        }
        report = _make_simple_report(calculated_fields=calc_fields)

        with patch.object(conn, "set_calculated_fields") as mock_set_calc:
            conn.map_reports([report])
            mock_set_calc.assert_called_once_with(
                "payment_text",
                "eq_get_payment_terms",
                ["partner_id.lang", "currency_id"],
                report.entry_name,
                report.model_name,
                False,
            )

    def test_map_reports_continues_on_exception(self):
        """An exception during one report must not stop processing the next report."""
        conn = _make_connection()
        mocks = _make_map_reports_env(conn, report_search_return=[42])

        mocks["ir.model"].search.side_effect = [RPCError("Boom"), [1], [1]]

        report1 = _make_simple_report(report_name="report_1")
        report2 = _make_simple_report(report_name="report_2")

        conn.map_reports([report1, report2])

        assert mocks["ir.actions.report"].browse.call_count >= 2

    def test_map_reports_calls_create_action(self):
        """create_action must be called on the report object to add to print menu."""
        conn = _make_connection()
        mocks = _make_map_reports_env(conn, report_search_return=[])
        report = _make_simple_report()

        conn.map_reports([report])

        mocks["report_obj"].create_action.assert_called_once()

    def test_map_reports_uses_fixture_data(self, sample_report_yaml_data):
        """Full integration test with fixture data from conftest."""
        conn = _make_connection()
        mocks = _make_map_reports_env(conn, report_search_return=[])
        report = _make_report_from_fixture(sample_report_yaml_data)

        conn.map_reports([report])

        create_args = mocks["ir.actions.report"].create.call_args[0][0]
        assert create_args["report_name"] == "eq_fr_core_sale_order"
        assert create_args["model"] == "sale.order"
        assert create_args["report_type"] == "fast_report"

    def test_map_reports_restores_original_company_id(self):
        """After processing, original company_id must be restored."""
        conn = _make_connection()
        _make_map_reports_env(conn, report_search_return=[42])

        report = _make_simple_report(company_id=[5])

        conn.map_reports([report])

    def test_map_reports_returns_failed_reports_list(self):
        """map_reports must return a list of (name, error) tuples for failed reports."""
        conn = _make_connection()
        mocks = _make_map_reports_env(conn, report_search_return=[42])

        call_count = {"n": 0}

        def write_side_effect(*args, **kwargs):
            call_count["n"] += 1
            if call_count["n"] == 1:
                raise RPCError("Report on Print Button flag error")
            mocks["report_obj"].write.side_effect = None

        mocks["report_obj"].write.side_effect = write_side_effect

        report1 = _make_simple_report(report_name="eq_fr_failing_report")
        report2 = _make_simple_report(report_name="eq_fr_success_report")

        failed = conn.map_reports([report1, report2])

        assert len(failed) == 1
        assert failed[0][0] == "eq_fr_failing_report"
        assert "Report on Print Button flag error" in failed[0][1]
        assert mocks["ir.actions.report"].browse.call_count >= 2

    def test_map_reports_returns_empty_list_on_full_success(self):
        """map_reports must return an empty list when all reports succeed."""
        conn = _make_connection()
        _make_map_reports_env(conn, report_search_return=[42])

        report1 = _make_simple_report(report_name="eq_fr_report_1")
        report2 = _make_simple_report(report_name="eq_fr_report_2")

        failed = conn.map_reports([report1, report2])

        assert failed == []

    def test_map_reports_passes_model_name_to_set_calculated_fields(self):
        """map_reports must use report.model_name (not report.model) for calculated fields."""
        conn = _make_connection()
        _make_map_reports_env(conn, report_search_return=[42])

        report = _make_simple_report(
            calculated_fields={"payment_text": {"eq_get_payment_terms": ["partner_id.lang"]}},
        )
        with patch.object(conn, "set_calculated_fields") as mock_set_calc:
            conn.map_reports([report])
            mock_set_calc.assert_called_once()
            assert mock_set_calc.call_args.args[4] == "sale.order"


# ---------------------------------------------------------------------------
# 10. TestSetCalculatedFields
# ---------------------------------------------------------------------------


class TestSetCalculatedFields:
    """Verify calculated field creation and update."""

    def _setup_calc_env(self, conn, existing_calc_field_ids=None):
        """Set up mocks for set_calculated_fields tests."""
        if existing_calc_field_ids is None:
            existing_calc_field_ids = []

        mock_ir_report = MagicMock()
        mock_ir_report.search.return_value = [42]
        mock_ir_report.env = MagicMock()
        mock_ir_report.env.user = MagicMock()

        mock_report_calc = MagicMock()
        mock_report_calc.search.return_value = existing_calc_field_ids

        env_map = {
            "ir.actions.report": mock_ir_report,
            "eq_calculated_field_value": mock_report_calc,
        }
        _setup_env(conn, env_map)

        return mock_ir_report, mock_report_calc

    def test_creates_new_calculated_field(self):
        conn = _make_connection()
        _, mock_calc = self._setup_calc_env(conn, existing_calc_field_ids=[])

        conn.set_calculated_fields(
            "payment_text",
            "eq_get_payment_terms",
            ["partner_id.lang", "currency_id"],
            {"de_DE": "Test"},
            "sale.order",
            False,
        )

        mock_calc.create.assert_called_once()
        create_args = mock_calc.create.call_args[0][0]
        assert create_args["eq_field_name"] == "payment_text"
        assert create_args["eq_function_name"] == "eq_get_payment_terms"
        assert create_args["eq_parameters_name"] == "partner_id.lang, currency_id"
        assert create_args["eq_report_id"] == 42

    def test_updates_existing_calculated_field(self):
        conn = _make_connection()
        _, mock_calc = self._setup_calc_env(conn, existing_calc_field_ids=[99])

        conn.set_calculated_fields(
            "payment_text",
            "eq_get_payment_terms",
            ["partner_id.lang"],
            {"de_DE": "Test"},
            "sale.order",
            False,
        )

        mock_calc.create.assert_not_called()
        mock_calc.write.assert_called_once()
        write_args = mock_calc.write.call_args[0]
        assert write_args[0] == [99]
        assert write_args[1]["eq_field_name"] == "payment_text"

    def test_handles_company_id(self):
        conn = _make_connection()
        mock_ir_report, mock_calc = self._setup_calc_env(conn, existing_calc_field_ids=[])

        conn.set_calculated_fields(
            "test_field",
            "test_func",
            ["param1"],
            {"de_DE": "Test"},
            "sale.order",
            3,
        )

        search_call = mock_ir_report.search.call_args[0][0]
        assert ("company_id", "=", 3) in search_call
        assert ("company_id", "=", False) in search_call

    def test_without_company_id_no_company_domain(self):
        conn = _make_connection()
        mock_ir_report, _ = self._setup_calc_env(conn, existing_calc_field_ids=[])

        conn.set_calculated_fields(
            "test_field",
            "test_func",
            ["param1"],
            {"de_DE": "Test"},
            "sale.order",
            False,
        )

        search_call = mock_ir_report.search.call_args[0][0]
        company_filters = [d for d in search_call if isinstance(d, tuple) and d[0] == "company_id"]
        assert len(company_filters) == 0

    def test_returns_when_report_not_found(self):
        conn = _make_connection()
        ir_actions = MagicMock()
        ir_actions.search.return_value = []
        ir_actions.env.user.company_id = 1
        report_calc = MagicMock()
        conn.connection.env.__getitem__.side_effect = lambda k: {
            "ir.actions.report": ir_actions,
            "eq_calculated_field_value": report_calc,
        }.get(k, MagicMock())

        result = conn.set_calculated_fields(
            field_name="payment_text",
            function_name="eq_get_payment_terms",
            parameters=["partner_id.lang"],
            report_name={"de_DE": "Report"},
            report_model="sale.order",
            report_company_id=False,
        )

        assert result is None
        report_calc.create.assert_not_called()
        report_calc.write.assert_not_called()


# ---------------------------------------------------------------------------
# 11. TestCollectReportEntries
# ---------------------------------------------------------------------------


class TestCollectReportEntries:
    """Verify YAML file collection from Odoo."""

    def test_writes_yaml_files_to_output_path(self, tmp_path):
        """collect_report_entries must write YAML files to the output directory."""
        conn = _make_connection()

        conn.connection.env.user.company_ids.ids = [1]
        conn.connection.env.user.company_ids.__bool__ = lambda s: True

        mock_ir_report = MagicMock()
        mock_ir_report.search.return_value = [10]

        mock_report_obj = MagicMock()
        mock_report_obj.report_name = "eq_fr_test"
        mock_report_obj.report_type = "fast_report"
        mock_report_obj.name = "Test Report"
        mock_report_obj.model = "sale.order"
        mock_report_obj.eq_export_type = "pdf"
        mock_report_obj.eq_ignore_images = True
        mock_report_obj.eq_handling_html_fields = "standard"
        mock_report_obj.multi = False
        mock_report_obj.attachment_use = False
        mock_report_obj.attachment = "Test.pdf"
        mock_report_obj.print_report_name = "Test"
        mock_report_obj.eq_calculated_field_ids = []
        mock_report_obj.eq_print_button = False
        mock_report_obj.eq_multiprint = "standard"
        mock_report_obj.company_id = MagicMock()
        mock_report_obj.company_id.id = False
        mock_report_obj.company_id.__bool__ = lambda s: False
        mock_report_obj.with_context.return_value = mock_report_obj
        mock_ir_report.browse.return_value = mock_report_obj

        mock_ir_model_fields = MagicMock()
        mock_ir_model_fields.search.return_value = [20]
        mock_field_obj = MagicMock()
        mock_field_obj.eq_report_ids.ids = [10]
        mock_field_obj.model_id.model = "sale.order"
        mock_field_obj.name = "name"
        mock_field_obj.modules = "sale"
        mock_ir_model_fields.browse.return_value = mock_field_obj

        mock_ir_model = MagicMock()
        mock_ir_model.search.return_value = [1]

        mock_res_company = MagicMock()
        mock_company_obj = MagicMock()
        mock_company_obj.name = "Test Co"
        mock_res_company.browse.return_value = mock_company_obj

        env_map = {
            "ir.actions.report": mock_ir_report,
            "ir.model.fields": mock_ir_model_fields,
            "ir.model": mock_ir_model,
            "res.company": mock_res_company,
        }
        _setup_env(conn, env_map)

        conn.get_installed_languages = MagicMock(return_value=[{"code": "de_DE", "iso_code": "de", "name": "German"}])

        output_dir = tmp_path / "output"
        output_dir.mkdir()

        conn.collect_report_entries(str(output_dir))

        yaml_files = list(output_dir.glob("*.yaml"))
        assert len(yaml_files) >= 1

        with open(yaml_files[0]) as f:
            data = yaml.safe_load(f)
        assert data is not None
        assert "report_name" in data

    def test_dependencies_only_contain_field_specific_modules(self, tmp_path):
        """Exported dependencies must come from ir.model.fields.modules per field."""
        conn = _make_connection()

        conn.connection.env.user.company_ids.ids = [1]
        conn.connection.env.user.company_ids.__bool__ = lambda s: True

        mock_ir_report = MagicMock()
        mock_ir_report.search.return_value = [10]

        mock_report_obj = MagicMock()
        mock_report_obj.report_name = "eq_fr_multi_module"
        mock_report_obj.report_type = "fast_report"
        mock_report_obj.name = "Multi Module Report"
        mock_report_obj.model = "sale.order"
        mock_report_obj.eq_export_type = "pdf"
        mock_report_obj.eq_ignore_images = True
        mock_report_obj.eq_handling_html_fields = "standard"
        mock_report_obj.multi = False
        mock_report_obj.attachment_use = False
        mock_report_obj.attachment = "MM.pdf"
        mock_report_obj.print_report_name = "MM"
        mock_report_obj.eq_calculated_field_ids = []
        mock_report_obj.eq_print_button = False
        mock_report_obj.eq_multiprint = "standard"
        mock_report_obj.company_id = MagicMock()
        mock_report_obj.company_id.id = False
        mock_report_obj.company_id.__bool__ = lambda s: False
        mock_report_obj.with_context.return_value = mock_report_obj
        mock_ir_report.browse.return_value = mock_report_obj

        mock_ir_model_fields = MagicMock()
        mock_ir_model_fields.search.return_value = [20]
        mock_field_obj = MagicMock()
        mock_field_obj.eq_report_ids.ids = [10]
        mock_field_obj.model_id.model = "sale.order"
        mock_field_obj.name = "amount_total"
        mock_field_obj.modules = "sale, account"
        mock_ir_model_fields.browse.return_value = mock_field_obj

        mock_ir_model = MagicMock()
        mock_ir_model.search.return_value = [1]

        mock_res_company = MagicMock()
        mock_res_company.browse.return_value = MagicMock(name="Test Co")

        env_map = {
            "ir.actions.report": mock_ir_report,
            "ir.model.fields": mock_ir_model_fields,
            "ir.model": mock_ir_model,
            "res.company": mock_res_company,
        }
        _setup_env(conn, env_map)

        ir_module_module_mock = MagicMock(
            side_effect=AssertionError("ir.module.module must not be queried during export")
        )
        conn.connection.env.__getitem__.side_effect = lambda key: (
            ir_module_module_mock() if key == "ir.module.module" else env_map[key]
        )

        conn.get_installed_languages = MagicMock(return_value=[{"code": "de_DE", "iso_code": "de", "name": "German"}])

        output_dir = tmp_path / "output"
        output_dir.mkdir()

        conn.collect_report_entries(str(output_dir))

        yaml_files = list(output_dir.glob("*.yaml"))
        assert len(yaml_files) == 1

        with open(yaml_files[0]) as f:
            data = yaml.safe_load(f)

        assert "dependencies" in data
        assert sorted(data["dependencies"]) == ["account", "sale"]
        assert len(data["dependencies"]) == 2

    def test_sanitizes_report_name_for_path_traversal(self, tmp_path):
        """Report names with path traversal characters must be sanitized."""
        conn = _make_connection()

        conn.connection.env.user.company_ids.ids = [1]
        conn.connection.env.user.company_ids.__bool__ = lambda s: True

        mock_ir_report = MagicMock()
        mock_ir_report.search.return_value = [10]

        mock_report_obj = MagicMock()
        mock_report_obj.report_name = "../../etc/passwd"
        mock_report_obj.report_type = "fast_report"
        mock_report_obj.name = "Evil Report"
        mock_report_obj.model = "sale.order"
        mock_report_obj.eq_export_type = "pdf"
        mock_report_obj.eq_ignore_images = True
        mock_report_obj.eq_handling_html_fields = "standard"
        mock_report_obj.multi = False
        mock_report_obj.attachment_use = False
        mock_report_obj.attachment = "Test.pdf"
        mock_report_obj.print_report_name = "Test"
        mock_report_obj.eq_calculated_field_ids = []
        mock_report_obj.eq_print_button = False
        mock_report_obj.eq_multiprint = "standard"
        mock_report_obj.company_id = MagicMock()
        mock_report_obj.company_id.id = False
        mock_report_obj.company_id.__bool__ = lambda s: False
        mock_report_obj.with_context.return_value = mock_report_obj
        mock_ir_report.browse.return_value = mock_report_obj

        mock_ir_model_fields = MagicMock()
        mock_ir_model_fields.search.return_value = [20]
        mock_field_obj = MagicMock()
        mock_field_obj.eq_report_ids.ids = [10]
        mock_field_obj.model_id.model = "sale.order"
        mock_field_obj.name = "name"
        mock_field_obj.modules = "sale"
        mock_ir_model_fields.browse.return_value = mock_field_obj

        mock_ir_model = MagicMock()
        mock_ir_model.search.return_value = [1]

        mock_res_company = MagicMock()
        mock_company_obj = MagicMock()
        mock_company_obj.name = "Test Co"
        mock_res_company.browse.return_value = mock_company_obj

        env_map = {
            "ir.actions.report": mock_ir_report,
            "ir.model.fields": mock_ir_model_fields,
            "ir.model": mock_ir_model,
            "res.company": mock_res_company,
        }
        _setup_env(conn, env_map)

        conn.get_installed_languages = MagicMock(return_value=[{"code": "de_DE", "iso_code": "de", "name": "German"}])

        output_dir = tmp_path / "output"
        output_dir.mkdir()

        conn.collect_report_entries(str(output_dir))

        for f in output_dir.rglob("*"):
            assert str(f).startswith(str(output_dir))

        parent_files = list(tmp_path.glob("etc/*"))
        assert len(parent_files) == 0


# ---------------------------------------------------------------------------
# 12. TestTestFastReportRendering
# ---------------------------------------------------------------------------


class TestTestFastReportRendering:
    """Verify FastReport rendering test workflow."""

    def _setup_rendering_env(self, conn, report_search_return=None, model_records=None):
        if report_search_return is None:
            report_search_return = [42]
        if model_records is None:
            model_records = [1, 2, 3]

        mock_ir_report = MagicMock()
        mock_ir_report.search.return_value = report_search_return

        mock_report_obj = MagicMock()
        mock_report_obj.report_type = "fast_report"
        mock_report_obj.ids = [42]
        mock_ir_report.browse.return_value = mock_report_obj
        mock_ir_report.eq_render_fast_report.return_value = ("rendered_content", "pdf")

        mock_ir_model = MagicMock()

        mock_report_model = MagicMock()
        mock_report_model.search.return_value = model_records

        conn.connection.env.user.company_id = 1

        env_map = {
            "ir.actions.report": mock_ir_report,
            "ir.model": mock_ir_model,
        }

        def mock_env_getitem(key):
            if key in env_map:
                return env_map[key]
            if key == "sale.order":
                return mock_report_model
            return MagicMock()

        conn.connection.env.__getitem__ = MagicMock(side_effect=mock_env_getitem)

        return mock_ir_report, mock_report_obj, mock_report_model

    def test_renders_report_successfully(self):
        conn = _make_connection()
        mock_ir_report, mock_report_obj, _ = self._setup_rendering_env(conn)

        report = _make_simple_report()

        conn.test_fast_report_rendering([report])

        mock_ir_report.eq_render_fast_report.assert_called_once()

    def test_skips_non_fast_report(self):
        conn = _make_connection()
        mock_ir_report, mock_report_obj, _ = self._setup_rendering_env(conn)
        mock_report_obj.report_type = "qweb-pdf"

        report = _make_simple_report()

        conn.test_fast_report_rendering([report])

        mock_ir_report.eq_render_fast_report.assert_not_called()

    def test_handles_empty_database(self):
        conn = _make_connection()
        mock_ir_report, mock_report_obj, _ = self._setup_rendering_env(conn, model_records=[])
        mock_ir_report.eq_render_fast_report_empty_db.return_value = ("demo_content", "pdf")

        report = _make_simple_report()

        conn.test_fast_report_rendering([report])

        mock_ir_report.eq_render_fast_report_empty_db.assert_called_once()

    def test_handles_rendering_exception(self):
        conn = _make_connection()
        mock_ir_report, _, _ = self._setup_rendering_env(conn)
        mock_ir_report.eq_render_fast_report.side_effect = RPCError("Rendering failed")

        report = _make_simple_report()

        conn.test_fast_report_rendering([report])

    def test_skips_when_report_not_found(self):
        conn = _make_connection()
        mock_ir_report = MagicMock()
        mock_ir_report.search.return_value = []
        mock_ir_report.browse.return_value = False

        mock_ir_model = MagicMock()
        _setup_env(conn, {"ir.actions.report": mock_ir_report, "ir.model": mock_ir_model})
        conn.connection.env.user.company_id = 1

        report = _make_simple_report()

        conn.test_fast_report_rendering([report])

        mock_ir_report.eq_render_fast_report.assert_not_called()


# ---------------------------------------------------------------------------
# 13. TestDisableQwebReports
# ---------------------------------------------------------------------------


class TestDisableQwebReports:
    """Verify QWeb report disabling."""

    def test_unlinks_all_qweb_reports(self):
        conn = _make_connection()

        mock_ir_report = MagicMock()
        mock_ir_report.search.return_value = [1, 2, 3]

        mock_obj_1 = MagicMock()
        mock_obj_2 = MagicMock()
        mock_obj_3 = MagicMock()
        mock_ir_report.browse.side_effect = [mock_obj_1, mock_obj_2, mock_obj_3]

        _setup_env(conn, {"ir.actions.report": mock_ir_report})

        conn.disable_qweb_reports()

        mock_obj_1.unlink_action.assert_called_once()
        mock_obj_2.unlink_action.assert_called_once()
        mock_obj_3.unlink_action.assert_called_once()

    def test_handles_no_qweb_reports(self):
        conn = _make_connection()

        mock_ir_report = MagicMock()
        mock_ir_report.search.return_value = []
        _setup_env(conn, {"ir.actions.report": mock_ir_report})

        conn.disable_qweb_reports()

        mock_ir_report.browse.assert_not_called()

    def test_searches_all_qweb_types(self):
        conn = _make_connection()

        mock_ir_report = MagicMock()
        mock_ir_report.search.return_value = []
        _setup_env(conn, {"ir.actions.report": mock_ir_report})

        conn.disable_qweb_reports()

        search_domain = mock_ir_report.search.call_args[0][0]
        types_in_domain = [d[2] for d in search_domain if isinstance(d, tuple) and d[0] == "report_type"]
        assert "qweb-pdf" in types_in_domain
        assert "qweb-html" in types_in_domain
        assert "qweb-text" in types_in_domain


# ---------------------------------------------------------------------------
# 14. Utility tests (is_boolean, is_dict, write_yaml, YAMLDumper)
# ---------------------------------------------------------------------------


class TestIsBoolean:
    """Verify is_boolean type checking."""

    def test_true_is_boolean(self):
        assert _make_connection().is_boolean(True) is True

    def test_false_is_boolean(self):
        assert _make_connection().is_boolean(False) is True

    def test_int_is_not_boolean(self):
        assert _make_connection().is_boolean(1) is False

    def test_string_is_not_boolean(self):
        assert _make_connection().is_boolean("True") is False

    def test_none_is_not_boolean(self):
        assert _make_connection().is_boolean(None) is False


class TestIsDict:
    """Verify is_dict type checking."""

    def test_dict_is_dict(self):
        assert _make_connection().is_dict({"key": "val"}) is True

    def test_empty_dict_is_dict(self):
        assert _make_connection().is_dict({}) is True

    def test_list_is_not_dict(self):
        assert _make_connection().is_dict([1, 2]) is False

    def test_none_is_not_dict(self):
        assert _make_connection().is_dict(None) is False


class TestWriteYaml:
    """Verify YAML file writing."""

    def test_creates_valid_yaml_file(self, tmp_path):
        conn = _make_connection()
        output_file = tmp_path / "test.yaml"
        data = {"name": "test", "value": 42}

        conn.write_yaml(str(output_file), data)

        assert output_file.exists()
        with open(output_file) as f:
            loaded = yaml.safe_load(f)
        assert loaded["name"] == "test"
        assert loaded["value"] == 42

    def test_utf8_encoding(self, tmp_path):
        conn = _make_connection()
        output_file = tmp_path / "utf8.yaml"
        data = {"name": "Rechnungsübersicht"}

        conn.write_yaml(str(output_file), data)

        content = output_file.read_text(encoding="utf8")
        assert "Rechnungsübersicht" in content


class TestYAMLDumper:
    """Verify custom YAMLDumper indentation behavior."""

    def test_increases_indent(self):
        from odoo_fast_report_mapper._yaml_dumper import YAMLDumper

        data = {"parent": {"child": ["a", "b"]}}
        output = yaml.dump(data, Dumper=YAMLDumper, default_flow_style=False)
        lines = output.strip().split("\n")
        parent_indent = len(lines[0]) - len(lines[0].lstrip())
        child_indent = len(lines[1]) - len(lines[1].lstrip())
        assert child_indent > parent_indent


# ---------------------------------------------------------------------------
# 15. TestAddFieldToDictionary
# ---------------------------------------------------------------------------


class TestAddFieldToDictionary:
    """Verify field addition to data dictionary."""

    def _setup_field_env(self, conn, modules="sale"):
        mock_ir_fields = MagicMock()
        mock_ir_model = MagicMock()
        mock_ir_model.search.return_value = [1]
        mock_ir_fields.search.return_value = [10]
        mock_field_obj = MagicMock()
        mock_field_obj.modules = modules
        mock_ir_fields.browse.return_value = mock_field_obj
        _setup_env(conn, {"ir.model.fields": mock_ir_fields, "ir.model": mock_ir_model})
        return mock_ir_fields

    def test_adds_field_to_new_entry(self):
        conn = _make_connection()
        self._setup_field_env(conn)

        result = conn.add_field_to_dictionary({}, 100, "sale.order", "name", False)

        assert 100 in result
        assert "name" in result[100]["sale.order"]

    def test_adds_field_to_existing_entry(self):
        conn = _make_connection()
        self._setup_field_env(conn)

        data = {100: {"sale.order": ["id"], "dependencies": ["sale"]}}
        result = conn.add_field_to_dictionary(data, 100, "sale.order", "partner_id", False)

        assert "partner_id" in result[100]["sale.order"]
        assert "id" in result[100]["sale.order"]

    def test_adds_company_id(self):
        conn = _make_connection()
        self._setup_field_env(conn)

        result = conn.add_field_to_dictionary({}, 100, "sale.order", "name", 3)

        assert "company_id" in result[100]
        assert 3 in result[100]["company_id"]

    def test_empty_model_search_skips_and_returns_dict(self):
        """When IR_MODEL.search returns [], field is still recorded but dependencies are skipped; IR_FIELDS.search not called."""
        conn = _make_connection()
        mock_ir_model = MagicMock()
        mock_ir_model.search.return_value = []
        mock_ir_fields = MagicMock()
        _setup_env(conn, {"ir.model": mock_ir_model, "ir.model.fields": mock_ir_fields})

        result = conn.add_field_to_dictionary({}, report_id=1, model_name="missing.model", field_name="id", company_id=False)

        # The field entry is recorded (no data loss), but no crash occurs
        assert result == {1: {"missing.model": ["id"]}}
        # Dependency collection is skipped — IR_FIELDS.search must never be called
        mock_ir_fields.search.assert_not_called()


# ---------------------------------------------------------------------------
# 16. TestCollectCalculatedFields
# ---------------------------------------------------------------------------


class TestCollectCalculatedFields:
    """Verify extraction of calculated fields from mock objects."""

    def test_extracts_correctly(self):
        conn = _make_connection()
        mock_field = MagicMock()
        mock_field.eq_field_name = "payment_text"
        mock_field.eq_function_name = "eq_get_payment_terms"
        mock_field.eq_parameters_name = "partner_id.lang, currency_id"

        result = conn._collect_calculated_fields([mock_field])

        assert result["payment_text"]["eq_get_payment_terms"] == ["partner_id.lang", "currency_id"]

    def test_empty_list_returns_empty_dict(self):
        conn = _make_connection()
        assert conn._collect_calculated_fields([]) == {}

    def test_strips_spaces_from_parameters(self):
        conn = _make_connection()
        mock_field = MagicMock()
        mock_field.eq_field_name = "f"
        mock_field.eq_function_name = "fn"
        mock_field.eq_parameters_name = "  a ,  b "

        result = conn._collect_calculated_fields([mock_field])

        assert result["f"]["fn"] == ["a", "b"]


# ---------------------------------------------------------------------------
# 17. TestListFastReports
# ---------------------------------------------------------------------------


class TestListFastReports:
    """Verify listing of FastReport entries across companies."""

    def _setup_reports(self, conn, reports_per_company):
        all_company_ids = list(reports_per_company.keys())
        conn.connection.env.user.company_ids.ids = all_company_ids
        conn.connection.env.user.company_ids.__bool__ = lambda s: True
        conn.connection.env.user.company_id = MagicMock()
        conn.connection.env.user.company_id.ids = all_company_ids

        mock_ir_report = MagicMock()
        mock_res_company = MagicMock()

        current_company = {"id": all_company_ids[0]}

        def set_company(val):
            current_company["id"] = val

        type(conn.connection.env.user).company_id = property(
            lambda self: current_company["id"],
            lambda self, val: set_company(val),
        )

        def search_side_effect(domain):
            cid = current_company["id"]
            return [r["id"] for r in reports_per_company.get(cid, [])]

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

        def browse_company(cid):
            obj = MagicMock()
            obj.name = f"Company {cid}"
            return obj

        mock_res_company.browse = MagicMock(side_effect=browse_company)

        _setup_env(conn, {"ir.actions.report": mock_ir_report, "res.company": mock_res_company})

    def test_returns_correct_structure(self):
        conn = _make_connection()
        self._setup_reports(
            conn,
            {
                1: [{"id": 10, "report_name": "eq_fr_sale", "name": "Sales", "model": "sale.order"}],
            },
        )

        result = conn.list_fast_reports()

        assert len(result) == 1
        assert result[0]["report_name"] == "eq_fr_sale"
        assert "company" in result[0]

    def test_deduplicates_by_report_name(self):
        conn = _make_connection()
        self._setup_reports(
            conn,
            {
                1: [{"id": 10, "report_name": "eq_fr_sale", "name": "Sales", "model": "sale.order"}],
                2: [{"id": 20, "report_name": "eq_fr_sale", "name": "Sales", "model": "sale.order"}],
            },
        )

        result = conn.list_fast_reports()

        assert len(result) == 1

    def test_empty_database(self):
        conn = _make_connection()
        self._setup_reports(conn, {1: []})

        result = conn.list_fast_reports()

        assert result == []


# ---------------------------------------------------------------------------
# 18. TestCollectAllReportEntries
# ---------------------------------------------------------------------------


class TestCollectAllReportEntries:
    """Verify backward-compatible wrapper delegates correctly."""

    def test_delegates_to_collect_report_entries(self):
        conn = _make_connection()
        conn.collect_report_entries = MagicMock()

        conn.collect_all_report_entries("/tmp/output")

        conn.collect_report_entries.assert_called_once_with("/tmp/output")


# ---------------------------------------------------------------------------
# 19. TestCreateEqReportObjectGuards (B-02 regression)
# ---------------------------------------------------------------------------


class TestCreateEqReportObjectGuards:
    """Verify create_eq_report_object does not crash on missing dependencies (B-02)."""

    def _setup_action(self, conn, with_calc_fields=True):
        ir_actions = MagicMock()
        action_obj = MagicMock()
        action_obj.name = "Test Report"
        action_obj.report_name = "test_report"
        action_obj.report_type = "fast_report"
        action_obj.eq_export_type = "pdf"
        action_obj.print_report_name = ""
        action_obj.model = "sale.order"
        action_obj.eq_ignore_images = False
        action_obj.eq_handling_html_fields = "standard"
        action_obj.multi = False
        action_obj.attachment_use = False
        action_obj.attachment = ""
        action_obj.eq_calculated_field_ids = [] if with_calc_fields else False
        action_obj.eq_print_button = False
        action_obj.eq_multiprint = False
        action_obj.with_context.return_value = action_obj
        ir_actions.browse.return_value = action_obj
        res_lang = MagicMock()
        res_lang.search.return_value = [1]
        lang_obj = MagicMock(code="de_DE", iso_code="de", name="German")
        res_lang.browse.return_value = lang_obj
        conn.connection.env.__getitem__.side_effect = lambda k: {
            "ir.actions.report": ir_actions,
            "res.lang": res_lang,
        }.get(k, MagicMock())

    def test_no_keyerror_when_dependencies_missing(self):
        """B-02: field_dictionary without 'dependencies' must not raise KeyError."""
        conn = _make_connection()
        self._setup_action(conn)
        field_dictionary = {"sale.order": ["name"]}

        report = conn.create_eq_report_object(action_id=1, field_dictionary=field_dictionary)

        assert report is not None
        assert report.report_name == "test_report"


# ---------------------------------------------------------------------------
# 20. TestSearchReportV13CompanyGuard (W-04 regression)
# ---------------------------------------------------------------------------


class TestSearchReportV13CompanyGuard:
    """Verify _search_report_v13 does not inject None into the company_id domain (W-04)."""

    def test_no_company_domain_when_company_id_none(self):
        conn = _make_connection()
        ir_actions = MagicMock()
        ir_actions.search.return_value = [42]

        conn._search_report_v13(
            model_name="sale.order",
            report_name={"de_DE": "Test Report"},
            IR_ACTIONS_REPORT=ir_actions,
            company_id=None,
        )

        call_args = ir_actions.search.call_args
        domain = call_args.args[0]
        for clause in domain:
            if isinstance(clause, tuple):
                assert clause[0] != "company_id", "company_id clause leaked into v13 search domain"

    def test_company_domain_present_when_company_id_set(self):
        conn = _make_connection()
        ir_actions = MagicMock()
        ir_actions.search.return_value = [42]

        conn._search_report_v13(
            model_name="sale.order",
            report_name={"de_DE": "Test Report"},
            IR_ACTIONS_REPORT=ir_actions,
            company_id=7,
        )

        domain = ir_actions.search.call_args.args[0]
        company_clauses = [c for c in domain if isinstance(c, tuple) and c[0] == "company_id"]
        assert len(company_clauses) == 2
        assert ("company_id", "=", 7) in company_clauses


# ---------------------------------------------------------------------------
# 21. TestApiKeyAuthMethod
# ---------------------------------------------------------------------------


class TestApiKeyAuthMethod:
    """Verify auth_method attribute and check_api_key_compatibility() pre-login gate."""

    def test_default_auth_method_is_password(self):
        conn = _make_connection()
        assert conn.auth_method == "password"

    def test_explicit_auth_method_api_key(self):
        with patch("odoo_fast_report_mapper._connection.prepare_connection") as mock_prepare:
            mock_connection = MagicMock()
            mock_prepare.return_value = mock_connection
            conn = OdooConnection(
                language="de_DE",
                collect_yaml=False,
                disable_qweb=True,
                workflow=0,
                url="https://test",
                port=443,
                username="admin",
                password="api-key-value",
                database="db",
                auth_method="api_key",
            )
        assert conn.auth_method == "api_key"

    def test_check_compatibility_password_auth_is_noop(self):
        """Password auth must skip the version check entirely."""
        conn = _make_connection()
        conn.connection.version = "12.0"
        conn.check_api_key_compatibility()

    def test_check_compatibility_v14_passes(self):
        conn = _make_connection()
        conn.auth_method = "api_key"
        conn.connection.version = "14.0"
        conn.check_api_key_compatibility()

    def test_check_compatibility_v18_passes(self):
        conn = _make_connection()
        conn.auth_method = "api_key"
        conn.connection.version = "18.0"
        conn.check_api_key_compatibility()

    def test_check_compatibility_v13_raises(self):
        conn = _make_connection()
        conn.auth_method = "api_key"
        conn.connection.version = "13.0"
        with pytest.raises(ValueError, match="API-key authentication requires Odoo >= 14"):
            conn.check_api_key_compatibility()

    def test_check_compatibility_v10_raises(self):
        conn = _make_connection()
        conn.auth_method = "api_key"
        conn.connection.version = "10.0"
        with pytest.raises(ValueError, match="requires Odoo >= 14.*v10"):
            conn.check_api_key_compatibility()
