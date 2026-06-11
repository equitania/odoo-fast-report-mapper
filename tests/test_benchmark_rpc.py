# Copyright 2014-now Equitania Software GmbH - Pforzheim - Germany
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

"""RPC call-count benchmark for collect_report_entries. PERF-01, PERF-03, PERF-04."""

import os
import urllib.error
from unittest.mock import MagicMock, patch

import pytest

from odoo_fast_report_mapper._connection import OdooConnection

# PLACEHOLDER — set to measured after-fix value in plan 03-02. -1 means not yet established.
RPC_CEILING: int = -1

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


def test_rpc_baseline_call_count(tmp_path):
    """BASELINE: measure current IR_MODEL.search and IR_FIELDS.search call counts.

    Runs collect_report_entries with 10 report mocks, each with 50 field objects.
    Prints BASELINE call counts to stdout — NO assertion on counts (measurement only).
    The test passes on the current (unfixed) codebase.

    PERF-01, PERF-04: This Wave 1 task establishes the infrastructure and documents
    the BEFORE state. Wave 2 (plan 03-02) converts this into an asserting regression
    test after the fix is applied.
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

    # --- ir.model mock (used inside add_field_to_dictionary for IR_MODEL.search) ---
    mock_ir_model = MagicMock()
    mock_ir_model.search.return_value = [1]  # non-empty so inner search proceeds

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

    # --- Baseline measurement (no assertion on counts) ---
    print(f"BASELINE ir.model.search calls: {mock_ir_model.search.call_count}")
    print(f"BASELINE ir.model.fields.search total calls: {mock_ir_model_fields.search.call_count}")
    print(f"  (includes 1 outer search + inner dependency searches per field)")
    print(f"  n_reports={n_reports}, n_fields_per_report={n_fields_per_report}, total_fields={n_reports * n_fields_per_report}")


def test_add_field_to_dictionary_calls_ir_model_search_currently():
    """BEFORE state: add_field_to_dictionary currently fires 2 RPC calls per field.

    Asserts mock_ir_model.search.call_count == 1 and mock_ir_fields.search.call_count == 1
    to document the current (pre-fix) behavior explicitly.

    This test documents the BEFORE state and will be DELETED in plan 03-02 once
    the fix is applied (the fix makes both counts 0).
    """
    conn = _make_connection()

    mock_ir_model = MagicMock()
    mock_ir_model.search.return_value = [1]

    mock_ir_fields = MagicMock()
    mock_ir_fields.search.return_value = [10]

    mock_field_obj = MagicMock()
    mock_field_obj.modules = "sale"
    mock_ir_fields.browse.return_value = mock_field_obj

    _setup_env(conn, {"ir.model.fields": mock_ir_fields, "ir.model": mock_ir_model})

    conn.add_field_to_dictionary({}, 100, "sale.order", "amount_total", False)

    # BEFORE: each call fires 1 IR_MODEL.search + 1 IR_FIELDS.search
    assert mock_ir_model.search.call_count == 1, (
        f"Expected 1 IR_MODEL.search call (BEFORE state), got {mock_ir_model.search.call_count}"
    )
    assert mock_ir_fields.search.call_count == 1, (
        f"Expected 1 IR_FIELDS.search call (BEFORE state), got {mock_ir_fields.search.call_count}"
    )
