---
phase: 02-type-safety
plan: "06"
subsystem: odoo_fast_report_mapper._connection
tags: [type-safety, mypy, annotations, part-1]
dependency_graph:
  requires:
    - "02-04"  # _report.py annotated
    - "02-05"  # _utils.py annotated
  provides:
    - "_connection.py Part 1 (lines 1-496) annotated under mypy --strict"
  affects:
    - "02-07"  # Part 2 of _connection.py
tech_stack:
  added: []
  patterns:
    - "cast() at RPC boundary for Odoo proxy return values"
    - "str | None for security-cleared password field"
    - "Any with inline comment for odoorpc proxy params"
    - "Literal[False] for Odoo false-sentinel search returns"
key_files:
  modified:
    - odoo_fast_report_mapper/_connection.py
decisions:
  - "self.password annotated as str | None (not str) — cleared to None after login for security; this is a documentation of existing runtime behavior"
  - "IR_ACTIONS_REPORT and other odoorpc proxy params annotated as Any per D-06 Tier 2 policy"
  - "cast(int, report_ids[0]) at RPC search boundary — Odoo .search() returns Any, not int"
  - "models_fields typed as dict[int, dict[int, list[int]]] — model_id -> {field_id -> [report_ids]}"
metrics:
  duration: "~10 minutes"
  completed: "2026-06-11"
  tasks_completed: 1
  files_modified: 1
---

# Phase 02 Plan 06: Annotate _connection.py Part 1 Summary

**One-liner:** `_connection.py` Part 1 (lines 1–496: class attrs, `__init__`, login/auth, search, dependency-check, map/collect helpers up to `set_calculated_fields`) fully annotated under mypy `--strict`; `Any` + `cast` applied at odoorpc RPC boundaries.

## Tasks Completed

| Task | Name | Commit | Files |
|------|------|--------|-------|
| 1 | Annotate _connection.py Part 1 | 34e56fe | odoo_fast_report_mapper/_connection.py |

## What Was Done

### Task 1: Annotate _connection.py Part 1 (lines 1–496)

Added typing imports (`Any`, `Literal`, `cast`) and `_odoo_types` imports. Annotated all methods in the first half of the file:

**`__init__`** — All 10 parameters typed; `-> None` added; `self.password` declared `str | None` (cleared to `None` after login for security — required to avoid `[assignment]` error).

**Login/auth methods** — `login() -> None`, `__repr__() -> str`, `__str__() -> str`, `check_api_key_compatibility() -> None` (already annotated, left as-is).

**Search methods** — `_search_report_v13` and `_search_report` annotated with full signatures matching the fragile-area pattern from RESEARCH.md: `-> int | Literal[False]`; `cast(int, report_ids[0])` applied at RPC boundary.

**Query methods** — `_get_fast_report_ids() -> list[int]` (cast at RPC boundary); `check_module(str) -> bool`; `get_installed_languages() -> list[dict[str, Any]]`; `get_company_language(int) -> str` with `_company_lang_cache: dict[int, str]` annotation.

**Dependency check** — `check_dependencies(list[str] | Literal[False]) -> tuple[bool, list[str]]` (BUG-03 return type confirmed present, parameter annotated).

**Mapping methods** — `map_reports(list[Any]) -> list[tuple[str, str]]` with typed locals `models_fields: dict[int, dict[int, list[int]]]` and `model_name_ids: dict[str, int]`; `_create_or_update_report`, `_set_report_translations`, `_map_report_fields`, `_write_field_mappings` all annotated with `Any` for odoorpc proxy params.

**Calculated fields** — `set_calculated_fields(str, str, list[str], dict[str, str], str, int | Literal[False]) -> None`.

## Verification Results

```
uv run mypy odoo_fast_report_mapper/ → Success: no issues found in 12 source files (Exit 0)
grep "_connection" pyproject.toml → ignore_errors = true  # Plan 02-06 and 02-07  (PASS)
grep "auth_method: str" _connection.py → found in __init__ signature (PASS)
grep "tuple\[bool" _connection.py → found in check_dependencies (PASS)
pytest 347 passed in 0.75s (PASS)
```

**Residual Part 2 errors (scope of Plan 02-07):** 25 errors on lines 534+ — `list_fast_reports`, `collect_all_report_entries`, `collect_report_entries`, `add_field_to_dictionary`, `_collect_calculated_fields`, `create_eq_report_object`, `write_yaml`, `is_boolean`, `is_dict`, `test_fast_report_rendering`, `disable_qweb_reports`. These are gated by the `ignore_errors = true` override that remains in `pyproject.toml`.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] `self.password` needs `str | None` annotation**
- **Found during:** Task 1
- **Issue:** `__init__` param `password: str` but `self.password = None` executed in both error path (line 69) and success path (line 90) for security clearing. mypy raised `[assignment]` error.
- **Fix:** Declared `self.password: str | None = password  # cleared to None after login for security`
- **Files modified:** `odoo_fast_report_mapper/_connection.py`
- **Commit:** 34e56fe

**2. [Rule 2 - Missing critical functionality] `cast()` needed for RPC return values**
- **Found during:** Task 1
- **Issue:** `_get_fast_report_ids`, `_search_report_v13`, `_search_report` — odoorpc `.search()` and list indexing return `Any`; declared return types are `list[int]` and `int | Literal[False]`. mypy raised `[no-any-return]`.
- **Fix:** Added `cast(list[int], ...)` and `cast(int, report_ids[0])` at RPC boundaries with inline comments per D-06 Tier 3 pattern.
- **Files modified:** `odoo_fast_report_mapper/_connection.py`
- **Commit:** 34e56fe

## Known Stubs

None — no stub patterns introduced in Part 1.

## Threat Flags

None — annotation-only changes; no new I/O, no new trust boundaries.

## Self-Check: PASSED

- [x] `odoo_fast_report_mapper/_connection.py` modified — file exists and is committed at 34e56fe
- [x] `uv run mypy odoo_fast_report_mapper/` → 0 errors
- [x] `_connection` override block still in `pyproject.toml`
- [x] 347 tests pass
- [x] Part 2 residual error count documented: 25 errors on lines 534+
