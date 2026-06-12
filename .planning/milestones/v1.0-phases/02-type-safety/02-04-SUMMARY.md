---
phase: 02-type-safety
plan: "04"
subsystem: typing
tags: [mypy, strict, report, literal-false, type-annotations, python]

# Dependency graph
requires:
  - phase: 02-type-safety plan 01
    provides: mypy strict mode enabled, override ramp in pyproject.toml
  - phase: 02-type-safety plan 02
    provides: _lang_utils.py fully annotated (resolve_attachment_value, get_primary_lang)
  - phase: 02-type-safety plan 03
    provides: _logging.py fully annotated
provides:
  - _report.py fully annotated (0 mypy --strict errors)
  - company_id typed as list[int] | Literal[False] (Odoo many2one convention)
  - _data_dictionary inline-annotated as dict[str, Any]
  - Override block for odoo_fast_report_mapper._report removed from pyproject.toml
affects: [02-05, 02-06, 02-07, 02-08]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "list[int] | Literal[False] for Odoo many2one company_id fields (list, not int)"
    - "Guard Literal[False] before list concat: isinstance check before appending"
    - "dict[str, Any] inline annotation for bare {} dict attribute"

key-files:
  created: []
  modified:
    - odoo_fast_report_mapper/_report.py
    - pyproject.toml

key-decisions:
  - "company_id annotated as list[int] | Literal[False], not int | Literal[False] — Odoo many2one returns [id, name] list at RPC boundary"
  - "add_dependencies guards Literal[False] case with isinstance before list concatenation"
  - "Override block for _report removed from pyproject.toml; _report now gated by full strict mode"

patterns-established:
  - "Odoo many2one sentinel: list[int] | Literal[False] (PATTERNS.md had int | Literal[False] — corrected per actual runtime contract)"
  - "Literal[False] guard in list ops: if isinstance(x, list) else [] before concatenation"

requirements-completed:
  - TYPE-01
  - TYPE-02

# Metrics
duration: 12min
completed: 2026-06-10
---

# Phase 02 Plan 04: Type Safety — _report.py Summary

**Fully annotated Report model class with list[int] | Literal[False] for company_id and guard for Literal[False] in add_dependencies; _report override block removed from pyproject.toml**

## Performance

- **Duration:** 12 min
- **Started:** 2026-06-10T00:00:00Z
- **Completed:** 2026-06-10T00:12:00Z
- **Tasks:** 1
- **Files modified:** 2

## Accomplishments

- Annotated all 10 mypy --strict errors in `_report.py` (6 no-untyped-def, 2 var-annotated, 2 type-arg)
- Fixed actual runtime contract: `company_id` is `list[int] | Literal[False]`, not `int | Literal[False]`
- Guarded `add_dependencies` against `Literal[False]` state before list concatenation
- Removed `[[tool.mypy.overrides]]` block for `odoo_fast_report_mapper._report` from `pyproject.toml`
- All 347 tests pass; `uv run mypy odoo_fast_report_mapper/` exits 0

## Task Commits

Each task was committed atomically:

1. **Task 1: Annotate _report.py — __init__ params, var-annotated, method return types** - `9cb4844` (chg)

## Files Created/Modified

- `odoo_fast_report_mapper/_report.py` - Added typing imports, annotated __init__ with full param types, fixed _data_dictionary var-annotated, annotated 5 methods, guarded add_dependencies Literal[False] case
- `pyproject.toml` - Removed [[tool.mypy.overrides]] block for odoo_fast_report_mapper._report

## Decisions Made

- Used `list[int] | Literal[False]` instead of plan-specified `int | Literal[False]` for company_id: the actual runtime contract confirmed by tests (`company_id=[5]`, `company_id=[1, 3]`) and by `report.company_id[0]` subscript in `_connection.py` and `_report.py` requires a list type
- Added `isinstance(self._dependencies, list)` guard in `add_dependencies` to handle the `Literal[False]` initial state before any dependencies are set — this is correct behavior since `False + list[str]` would be a type error and runtime error

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Corrected company_id type from int to list[int]**
- **Found during:** Task 1 (annotation of _report.py __init__)
- **Issue:** PATTERNS.md specified `company_id: int | Literal[False]` but actual runtime usage is subscript-indexed (`company_id[0]`), and test fixtures use `company_id=[5]`, `company_id=[1, 3]` — confirming many2one list format
- **Fix:** Changed annotation to `list[int] | Literal[False]` which matches both the mypy requirement (no index error on line 78) and the actual Odoo RPC data contract
- **Files modified:** `odoo_fast_report_mapper/_report.py`
- **Verification:** mypy --strict exits 0; 347 tests pass
- **Committed in:** 9cb4844 (Task 1 commit)

**2. [Rule 1 - Bug] Added Literal[False] guard in add_dependencies**
- **Found during:** Task 1 (mypy verification after annotation)
- **Issue:** `self._dependencies` is typed `list[str] | Literal[False]`; the original `self._dependencies + dependency_list` would fail mypy when `_dependencies` is `False` (which is its initial value per __init__)
- **Fix:** Added `existing: list[str] = self._dependencies if isinstance(self._dependencies, list) else []` before concatenation
- **Files modified:** `odoo_fast_report_mapper/_report.py`
- **Verification:** mypy --strict exits 0; 347 tests pass
- **Committed in:** 9cb4844 (Task 1 commit)

---

**Total deviations:** 2 auto-fixed (2 Rule 1 bugs — wrong type annotation + missing guard)
**Impact on plan:** Both auto-fixes necessary for correctness. The list[int] fix matches the actual Odoo RPC contract. The guard fix prevents a runtime error when add_dependencies is called before any dependencies are set.

## Issues Encountered

None — both issues resolved as part of the annotation task. The PATTERNS.md type specification for company_id was incorrect (int vs list[int]); actual runtime behavior confirmed via test fixtures and usage in _connection.py.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- `_report.py` is fully annotated and no longer gated by override
- `pyproject.toml` override ramp now has 3 remaining modules: `_utils`, `_connection`, `_cli`
- Wave 4 plans (02-05 through 02-08) can proceed with clean `_report.py` type signatures

---
*Phase: 02-type-safety*
*Completed: 2026-06-10*
