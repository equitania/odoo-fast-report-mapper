# Copyright 2014-now Equitania Software GmbH - Pforzheim - Germany
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

"""RPC call-count benchmark for collect_report_entries. PERF-01, PERF-03, PERF-04."""

import os
import urllib.error
from unittest.mock import MagicMock, patch

import pytest

from odoo_fast_report_mapper._connection import OdooConnection

# After fix: add_field_to_dictionary makes 0 IR_MODEL.search + 0 IR_FIELDS.search calls per field.
# Outer legitimate calls (IR_ACTIONS_REPORT.search + IR_MODEL_FIELDS.search outer) are not counted here.
RPC_CEILING: int = 0

# ---------------------------------------------------------------------------
# Helpers (copied verbatim from tests/test_connection.py)
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


def _setup_env(conn, models_map):
    """Wire up conn.connection.env[key] to return the given models_map entries."""

    def mock_env_getitem(key):
        return models_map.get(key, MagicMock())

    conn.connection.env.__getitem__ = MagicMock(side_effect=mock_env_getitem)


# ---------------------------------------------------------------------------
# Benchmark-specific helpers
# ---------------------------------------------------------------------------

_MODEL_NAMES = ["sale.order", "account.move", "res.partner", "stock.picking", "purchase.order"]
_MODULES_VARIANTS = ["sale", "account", "base", "", "sale,account"]


def _build_field_mock(report_ids, model_name, field_name, modules_str):
    """Return a MagicMock that mimics an ir.model.fields browse result."""
    m = MagicMock()
    m.eq_report_ids.ids = report_ids
    m.model_id.model = model_name
    m.name = field_name
    m.modules = modules_str
    return m


def _build_report_mock(report_name, model_name):
    """Return a MagicMock that mimics an ir.actions.report browse result."""
    m = MagicMock()
    m.report_name = report_name
    m.report_type = "fast_report"
    m.name = report_name.replace("_", " ").title()
    m.model = model_name
    m.eq_export_type = "pdf"
    m.eq_ignore_images = True
    m.eq_handling_html_fields = "standard"
    m.multi = False
    m.attachment_use = False
    m.attachment = f"{report_name}.pdf"
    m.print_report_name = report_name
    m.eq_calculated_field_ids = []
    m.eq_print_button = False
    m.eq_multiprint = "standard"
    m.company_id = MagicMock()
    m.company_id.id = False
    m.company_id.__bool__ = lambda s: False
    m.with_context.return_value = m
    return m


# ---------------------------------------------------------------------------
# Benchmark tests
# ---------------------------------------------------------------------------


def test_collect_rpc_call_count(tmp_path):
    """PERF-01/PERF-02/PERF-03: after fix, IR_MODEL.search count must be 0 for 10x50 collect run.

    Runs collect_report_entries with 10 report mocks, each with 50 field objects (500 total fields).
    Asserts that add_field_to_dictionary no longer calls ir.model.search or fires extra
    ir.model.fields.search calls — only the single outer all_report_field_ids search is allowed.

    RPC_CEILING = 0 means: zero inner IR_MODEL.search calls after the fix (PERF-04).
    """
    conn = _make_connection()

    conn.connection.env.user.company_ids.ids = [1]
    conn.connection.env.user.company_ids.__bool__ = lambda s: True

    # --- Report mocks (IDs 10..19, one model per report) ---
    n_reports = 10
    report_ids = list(range(10, 10 + n_reports))
    report_mocks = {}
    for i, rid in enumerate(report_ids):
        model = _MODEL_NAMES[i % len(_MODEL_NAMES)]
        report_mocks[rid] = _build_report_mock(f"eq_fr_bench_report_{rid}", model)

    mock_ir_report = MagicMock()
    mock_ir_report.search.return_value = report_ids

    def _ir_report_browse(report_id):
        if isinstance(report_id, list):
            report_id = report_id[0]
        return report_mocks.get(report_id, MagicMock())

    mock_ir_report.browse.side_effect = _ir_report_browse

    # --- Field mocks (IDs 1000..1499, 50 per report) ---
    n_fields_per_report = 50
    all_field_ids = list(range(1000, 1000 + n_reports * n_fields_per_report))
    field_mocks = {}
    for idx, fid in enumerate(all_field_ids):
        report_idx = idx // n_fields_per_report
        report_id = report_ids[report_idx]
        model = _MODEL_NAMES[report_idx % len(_MODEL_NAMES)]
        field_name = f"field_{fid}"
        modules_str = _MODULES_VARIANTS[idx % len(_MODULES_VARIANTS)]
        field_mocks[fid] = _build_field_mock([report_id], model, field_name, modules_str)

    mock_ir_model_fields = MagicMock()
    mock_ir_model_fields.search.return_value = all_field_ids

    def _fields_browse(field_id):
        if isinstance(field_id, list):
            field_id = field_id[0]
        return field_mocks.get(field_id, MagicMock())

    mock_ir_model_fields.browse.side_effect = _fields_browse

    # --- ir.model mock (only used inside add_field_to_dictionary; must be 0 calls after fix) ---
    mock_ir_model = MagicMock()
    mock_ir_model.search.return_value = [1]

    # --- res.company mock ---
    mock_res_company = MagicMock()
    mock_company_obj = MagicMock()
    mock_company_obj.name = "Bench Co"
    mock_res_company.browse.return_value = mock_company_obj

    # --- Wire env_map ---
    # ir.module.module MUST NOT be accessed during collect — guard with AssertionError
    ir_module_module_guard = MagicMock(
        side_effect=AssertionError("ir.module.module must not be queried during collect")
    )
    env_map = {
        "ir.actions.report": mock_ir_report,
        "ir.model.fields": mock_ir_model_fields,
        "ir.model": mock_ir_model,
        "res.company": mock_res_company,
    }
    _setup_env(conn, env_map)
    # Override __getitem__ to guard ir.module.module
    conn.connection.env.__getitem__.side_effect = lambda key: (
        ir_module_module_guard() if key == "ir.module.module" else env_map[key]
    )

    conn.get_installed_languages = MagicMock(
        return_value=[{"code": "de_DE", "iso_code": "de", "name": "German"}]
    )

    output_dir = tmp_path / "output"
    output_dir.mkdir()

    conn.collect_report_entries(str(output_dir))

    # --- Regression assertions (PERF-02/PERF-03): zero inner search calls after fix ---
    assert mock_ir_model.search.call_count == RPC_CEILING, (
        f"add_field_to_dictionary must not call ir.model.search after fix — "
        f"got {mock_ir_model.search.call_count} calls (RPC_CEILING={RPC_CEILING})"
    )
    assert mock_ir_model_fields.search.call_count == 1, (
        f"ir.model.fields.search must be called exactly once (outer field ID fetch) — "
        f"got {mock_ir_model_fields.search.call_count}"
    )


def test_add_field_to_dictionary_zero_rpc_calls():
    """PERF-02/PERF-03: After fix, add_field_to_dictionary accepts modules param and performs 0 RPC calls.

    Verifies the new modules parameter is used correctly and that no env access occurs.
    """
    conn = _make_connection()

    mock_ir_model = MagicMock()
    mock_ir_fields = MagicMock()
    _setup_env(conn, {"ir.model.fields": mock_ir_fields, "ir.model": mock_ir_model})

    result = conn.add_field_to_dictionary({}, 100, "sale.order", "amount_total", False, modules=["sale", "account"])

    # Verify result contains the correct field entry and dependencies
    assert 100 in result
    assert "sale.order" in result[100]
    assert "amount_total" in result[100]["sale.order"]
    assert "dependencies" in result[100]
    assert set(result[100]["dependencies"]) == {"sale", "account"}

    # Verify zero RPC calls — modules param eliminates both searches
    assert mock_ir_model.search.call_count == 0, (
        "add_field_to_dictionary must not call ir.model.search — modules param eliminates this RPC call"
    )
    assert mock_ir_fields.search.call_count == 0, (
        "add_field_to_dictionary must not call ir.model.fields.search — modules param eliminates this RPC call"
    )
