---
phase: 02-type-safety
plan: "05"
subsystem: type-safety
tags: [mypy, typing, annotations, type-guards, python]

# Dependency graph
requires:
  - phase: 02-01
    provides: "from __future__ import annotations added project-wide, pyproject.toml strict mode, overrides scaffolding"
  - phase: 02-02
    provides: "_lang_utils.py annotated, dict[str,str] pattern established"
  - phase: 02-03
    provides: "_logging.py annotated, singleton class annotation pattern established"
provides:
  - "_utils.py fully annotated with 0 mypy --strict errors"
  - "os.getenv() None guards for ODOO_PORT and ODOO_LANGUAGE"
  - "Override block for odoo_fast_report_mapper._utils removed from pyproject.toml"
affects:
  - "02-06 (_connection.py — imports from _utils.py are now typed)"
  - "02-08 (_cli.py — create_connection_from_env return type is tuple[Any, str])"

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Callable[[ParamType], ReturnType] for function-parameter annotations"
    - "os.getenv(key) with None check pattern — replaces bare int(os.getenv(key))"
    - "dict[str, Any] for opaque YAML content (Tier 2 pre-justified)"
    - "list[tuple[str, dict[str, Any]]] for typed YAML-with-filename tuples"
    - "company_id_val = original.get(...) guard before len() call"

key-files:
  created: []
  modified:
    - "odoo_fast_report_mapper/_utils.py"
    - "pyproject.toml"

key-decisions:
  - "prepare_connection return type is ODOO (odoorpc_toolbox.ODOO) — explicit RPC object type"
  - "fire_all_functions uses Callable[[], None] — zero-arg, no-return function list"
  - "parse_yaml returns dict[str, Any] | bool — False on parse error (legacy convention preserved)"
  - "create_report_object_from_yaml_object returns Any — Report is lazily imported to avoid circular dependency"
  - "convert_all_yaml_objects uses Callable[[dict[str, Any]], Any] for converting_function — precise enough for both create_report and create_connection factories"
  - "ODOO_PORT None guard uses explicit if port_str is None: raise ValueError (T-02-05-01 threat mitigation)"
  - "ODOO_LANGUAGE None guard uses same explicit pattern (consistent with ODOO_PORT fix)"

patterns-established:
  - "Pattern: os.getenv() guard — extract to named var, explicit None raise before use"
  - "Pattern: dict[str, Any] for all YAML-loaded opaque content"

requirements-completed:
  - TYPE-01
  - TYPE-02

# Metrics
duration: 8min
completed: 2026-06-10
---

# Phase 02 Plan 05: _utils.py Type Annotation Summary

**All 15 untyped functions in _utils.py annotated with full param + return types; os.getenv None guards added; mypy override block removed — 0 strict errors across 12 source files.**

## Performance

- **Duration:** ~8 min
- **Started:** 2026-06-10T14:56:00Z
- **Completed:** 2026-06-10T15:04:18Z
- **Tasks:** 1
- **Files modified:** 2

## Accomplishments

- Annotated all 15 previously untyped functions in `_utils.py` with precise param and return types
- Added explicit None-guard for `os.getenv("ODOO_PORT")` and `os.getenv("ODOO_LANGUAGE")` (T-02-05-01 threat mitigation)
- Fixed type-arg errors: `list` → `list[Callable[[], None]]`, bare `dict` → `dict[str, list[str]]`, bare `list` on line 338
- Fixed arg-type error in `build_reports_from_yaml_objects` — extracted `company_id_val` to guard `len()` call against `Any | None`
- Removed `[[tool.mypy.overrides]]` block for `odoo_fast_report_mapper._utils` from pyproject.toml
- `uv run mypy odoo_fast_report_mapper/` → 0 errors (12 source files, includes _utils without override)
- 347 tests pass unchanged

## Task Commits

1. **Task 1: Annotate _utils.py — all function signatures, os.getenv guards, bare-dict fixes** - `d35a05c` ([CHG])

## Files Created/Modified

- `odoo_fast_report_mapper/_utils.py` — All 15 functions annotated; os.getenv None guards added; company_id_val guard for len()
- `pyproject.toml` — Removed `[[tool.mypy.overrides]]` block for `odoo_fast_report_mapper._utils`

## Decisions Made

- `prepare_connection` return type is `ODOO` (odoorpc_toolbox.ODOO imported as the concrete class)
- `parse_yaml` returns `dict[str, Any] | bool` — preserves the legacy `return False` on error; no behavior change
- `create_report_object_from_yaml_object` and `create_odoo_connection_from_yaml_object` return `Any` — their return types are lazily-imported classes (_report.Report, _connection.OdooConnection) with circular-import risk; `Any` is the correct Tier 2 annotation here
- `convert_all_yaml_objects` parameter typed as `Callable[[dict[str, Any]], Any]` — covers both factory functions cleanly

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Fixed len() called on Any|None in build_reports_from_yaml_objects**
- **Found during:** Task 1 (mypy check after initial annotation pass)
- **Issue:** `original.get("company_id")` returns `Any | None`; second call `len(original.get("company_id"))` triggered `arg-type` error since mypy cannot prove it's not None after the truthy check
- **Fix:** Extracted to `company_id_val = original.get("company_id")` then used `company_id_val` for both truthy guard and `len()` call — mypy can now track the narrowed type
- **Files modified:** `odoo_fast_report_mapper/_utils.py`
- **Verification:** `uv run mypy odoo_fast_report_mapper/` → 0 errors
- **Committed in:** d35a05c (Task 1 commit)

---

**Total deviations:** 1 auto-fixed (Rule 1 — bug)
**Impact on plan:** Minimal fix required to satisfy mypy strict. No scope creep. No behavior change.

## Issues Encountered

- Worktree was created from `571be45` (before plans 02-01..02-04 were merged). Rebased onto local `develop` HEAD (`7f56c9a`) before execution to get correct pyproject.toml (with strict mode + overrides scaffolding) and `from __future__ import annotations` already present in `_utils.py`.

## Next Phase Readiness

- `_utils.py` is fully typed; all factory and utility functions have concrete return types
- `_connection.py` can now resolve `prepare_connection` return type (ODOO) for its own annotation work in Plan 02-06/07
- Only 2 override blocks remain in pyproject.toml: `_connection` (Plan 02-06/07) and `_cli` (Plan 02-08)

---
*Phase: 02-type-safety*
*Completed: 2026-06-10*
