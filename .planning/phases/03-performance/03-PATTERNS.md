# Phase 3: Performance - Pattern Map

**Mapped:** 2026-06-11
**Files analyzed:** 2
**Analogs found:** 2 / 2

---

## File Classification

| New/Modified File | Role | Data Flow | Closest Analog | Match Quality |
|---|---|---|---|---|
| `odoo_fast_report_mapper/_connection.py` | service | request-response (RPC) | `odoo_fast_report_mapper/_connection.py` (existing) | exact — modifying existing method signatures and loop body |
| `tests/test_benchmark_rpc.py` | test | batch (loop-driven mock counter) | `tests/test_connection.py` — `TestCollectReportEntries` + `TestAddFieldToDictionary` | exact — same mock infrastructure, same `_make_connection` + `_setup_env` helpers |

---

## Pattern Assignments

### `odoo_fast_report_mapper/_connection.py` — `add_field_to_dictionary` refactor

**Analog:** `_connection.py` lines 688–731 (existing implementation to be changed)

**Imports pattern** (lines 13–30) — no new imports needed; existing `typing` and `Literal` already present:
```python
from __future__ import annotations
from typing import Any, Literal
```

**Current method signature** (`_connection.py` lines 688–695) — this is the BEFORE state:
```python
def add_field_to_dictionary(
    self,
    data_dictionary: dict[Any, Any],
    report_id: Any,
    model_name: str,
    field_name: str,
    company_id: int | Literal[False],
) -> dict[Any, Any]:
```

**New method signature after fix** — add `modules` as optional trailing parameter:
```python
def add_field_to_dictionary(
    self,
    data_dictionary: dict[Any, Any],
    report_id: Any,
    model_name: str,
    field_name: str,
    company_id: int | Literal[False],
    modules: list[str] | None = None,   # resolved by caller from field_object.modules
) -> dict[Any, Any]:
```

**Dependency block to DELETE** (`_connection.py` lines 708–730) — the 2-extra-RPC section:
```python
# DELETE the entire block below from add_field_to_dictionary:
IR_FIELDS = self.connection.env["ir.model.fields"]
IR_MODEL = self.connection.env["ir.model"]
model_id = IR_MODEL.search([("model", "=", model_name)])
if not model_id:
    logger.warning(f"Model '{model_name}' not found — skipping dependency collection")
    return data_dictionary
field_id = IR_FIELDS.search([("model_id", "=", model_id[0]), ("name", "=", field_name)])
if not field_id:
    logger.debug(f"Field '{field_name}' on '{model_name}' not found in ir.model.fields — skipping dependency")
    return data_dictionary
field_obj = IR_FIELDS.browse(field_id)
raw_modules = field_obj.modules.replace(" ", "").split(",")
modules_dependencies = [m for m in raw_modules if m]
```

**Replacement dependency block** — pure dict mutation, zero RPC:
```python
# REPLACEMENT — no self.connection access at all:
modules_dependencies = modules or []
```

**Modules extraction to ADD into `collect_report_entries` loop** (`_connection.py` lines 627–667) — copy the guard pattern verbatim from RESEARCH.md §Code Examples, which mirrors lines 719–720:
```python
# In the for field_id in progress_bar(...): loop, after line 636 (field_name = field_object.name):
raw_modules = field_object.modules or ""
modules = [m for m in raw_modules.replace(" ", "").split(",") if m]
```

**Call-site update in `collect_report_entries`** (line 661–667) — pass `modules` to the call:
```python
data_dictionary = self.add_field_to_dictionary(
    data_dictionary,
    report_action_id,
    model_name,
    field_name,
    report_company_id,
    modules,   # NEW — resolved above from field_object.modules
)
```

**Existing `collect_report_entries` loop structure** (`_connection.py` lines 627–636) — this is the context the planner needs to locate the insertion point:
```python
for field_id in progress_bar(
    all_report_field_ids, desc=f"Collecting fields ({company_name})", unit="field"
):
    field_object = IR_MODEL_FIELDS.browse(field_id)
    report_action_ids = field_object.eq_report_ids.ids
    model_id = field_object.model_id
    model_name = model_id.model
    field_name = field_object.name
    # ← INSERT raw_modules / modules extraction HERE (before the inner for loop)
```

---

### `tests/test_benchmark_rpc.py` — new Mock-Counter benchmark

**Analog:** `tests/test_connection.py` — `TestCollectReportEntries` (lines 1094–1228) and `TestAddFieldToDictionary` (lines 1560–1647)

**Imports pattern** — copy exactly from `tests/test_connection.py` lines 1–15 (no additions needed):
```python
# Copyright 2014-now Equitania Software GmbH - Pforzheim - Germany
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import urllib.error
from unittest.mock import MagicMock, patch

import pytest

from odoo_fast_report_mapper._connection import OdooConnection
```

**`_make_connection` helper** — copy verbatim from `tests/test_connection.py` lines 22–53. Do NOT duplicate the definition; import it if the file is made a module, or copy it inline. The pattern:
```python
def _make_connection(...):
    """Create an OdooConnection with a patched prepare_connection."""
    with patch("odoo_fast_report_mapper._connection.prepare_connection") as mock_prepare:
        mock_connection = MagicMock()
        mock_connection.version = "18.0"
        mock_connection.config = {}
        mock_connection.env.context = {}
        mock_prepare.return_value = mock_connection
        conn = OdooConnection(language=language, ...)
    conn.version = "18"
    return conn
```

**`_setup_env` helper** — copy verbatim from `tests/test_connection.py` lines 61–67:
```python
def _setup_env(conn, models_map):
    """Wire up conn.connection.env[key] to return the given models_map entries."""

    def mock_env_getitem(key):
        return models_map.get(key, MagicMock())

    conn.connection.env.__getitem__ = MagicMock(side_effect=mock_env_getitem)
```

**Field-object mock pattern** — copy from `TestCollectReportEntries.test_writes_yaml_files_to_output_path` (lines 1128–1135) and `test_dependencies_only_contain_field_specific_modules` (lines 1199–1206). This is the canonical way to mock `ir.model.fields` browse results with `.modules`, `.eq_report_ids.ids`, `.model_id.model`, `.name`:
```python
mock_ir_model_fields = MagicMock()
mock_ir_model_fields.search.return_value = [<field_id>, ...]  # list of IDs
mock_field_obj = MagicMock()
mock_field_obj.eq_report_ids.ids = [<report_id>]
mock_field_obj.model_id.model = "sale.order"
mock_field_obj.name = "amount_total"
mock_field_obj.modules = "sale, account"   # or "" or False
mock_ir_model_fields.browse.return_value = mock_field_obj
```

**Report-object mock pattern** — copy from `TestCollectReportEntries.test_writes_yaml_files_to_output_path` (lines 1104–1126). All these attributes are required for `create_eq_report_object` to succeed without crashing:
```python
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
```

**Full env_map wiring pattern** — copy from `TestCollectReportEntries` (lines 1145–1151):
```python
env_map = {
    "ir.actions.report": mock_ir_report,
    "ir.model.fields": mock_ir_model_fields,
    "ir.model": mock_ir_model,
    "res.company": mock_res_company,
}
_setup_env(conn, env_map)
conn.get_installed_languages = MagicMock(return_value=[{"code": "de_DE", "iso_code": "de", "name": "German"}])
```

**Mock-Counter assertion pattern** — after the fix, assert on `.call_count` directly (zero-setup, from RESEARCH.md §Pattern 1 and the simpler "Alternative" note):
```python
# After the fix: inner dependency searches must be zero
# The outer IR_MODEL_FIELDS.search (top-level field ID fetch) IS called once — that is legitimate.
# The inner IR_MODEL.search and IR_FIELDS.search (inside add_field_to_dictionary) must be 0.
# Use separate mocks for outer vs inner to avoid counting the legitimate outer call:
mock_ir_model_inner = MagicMock()
mock_ir_model_inner.search.return_value = []
# Wire it in a way that the outer ir.model.fields.search is a different mock (or track by call args)
# Simplest: assert mock_ir_model.search.call_count == 0  (ir.model is ONLY used inside add_field_to_dictionary)
assert mock_ir_model.search.call_count == 0, (
    f"add_field_to_dictionary must not call ir.model.search — "
    f"got {mock_ir_model.search.call_count} calls"
)
```

**`RPC_CEILING` constant placement** — top of file, after imports, before test functions:
```python
# Ceiling documented after Wave 0 baseline measurement.
# After fix: inner IR_MODEL.search + IR_FIELDS.search == 0 per field.
# Outer legitimate calls: 1 IR_ACTIONS_REPORT.search + 1 IR_MODEL_FIELDS.search per company.
RPC_CEILING: int = 0  # inner-search ceiling; set to measured after-fix count
```

**`_setup_field_env` helper** — for direct `add_field_to_dictionary` tests, copy from `TestAddFieldToDictionary._setup_field_env` (lines 1563–1572):
```python
def _setup_field_env(conn, modules="sale"):
    mock_ir_fields = MagicMock()
    mock_ir_model = MagicMock()
    mock_ir_model.search.return_value = [1]
    mock_ir_fields.search.return_value = [10]
    mock_field_obj = MagicMock()
    mock_field_obj.modules = modules
    mock_ir_fields.browse.return_value = mock_field_obj
    _setup_env(conn, {"ir.model.fields": mock_ir_fields, "ir.model": mock_ir_model})
    return mock_ir_fields
```

**Mypy compliance pattern** — the signature `modules: list[str] | None = None` uses the `|` union syntax already established throughout `_connection.py` (e.g., `company_id: int | Literal[False]` at line 694). No `Optional[...]` wrapper needed; the `from __future__ import annotations` at line 13 makes it valid for all Python >=3.8.

---

## Shared Patterns

### Mock environment wiring (`_setup_env`)
**Source:** `tests/test_connection.py` lines 61–67
**Apply to:** Both `test_benchmark_rpc.py` test functions (baseline and regression)
```python
def _setup_env(conn, models_map):
    def mock_env_getitem(key):
        return models_map.get(key, MagicMock())
    conn.connection.env.__getitem__ = MagicMock(side_effect=mock_env_getitem)
```

### Connection factory (`_make_connection`)
**Source:** `tests/test_connection.py` lines 22–53
**Apply to:** Every test function in `test_benchmark_rpc.py` — creates OdooConnection with patched transport, no network I/O

### `modules or ""` guard (BUG-08/BUG-09 pattern)
**Source:** `_connection.py` lines 718–720 (current `add_field_to_dictionary` body, pre-fix)
**Apply to:** The new extraction block added to `collect_report_entries` loop
```python
raw_modules = field_object.modules or ""
modules = [m for m in raw_modules.replace(" ", "").split(",") if m]
```
This guard must be preserved verbatim when moving resolution into the outer loop.

### `ir.module.module` must-not-be-queried guard
**Source:** `tests/test_connection.py` lines 1222–1227 (AssertionError side_effect pattern)
**Apply to:** The `test_collect_rpc_call_count` test — assert that `ir.module.module` is never touched during collect:
```python
ir_module_module_mock = MagicMock(
    side_effect=AssertionError("ir.module.module must not be queried during export")
)
conn.connection.env.__getitem__.side_effect = lambda key: (
    ir_module_module_mock() if key == "ir.module.module" else env_map[key]
)
```

---

## No Analog Found

None. Both files have strong existing analogs in the codebase.

---

## Metadata

**Analog search scope:** `odoo_fast_report_mapper/`, `tests/`
**Files scanned:** `_connection.py` (lines 580–731), `tests/test_connection.py` (lines 1–67, 1094–1228, 1560–1647), `tests/conftest.py` (lines 186–261)
**Pattern extraction date:** 2026-06-11
