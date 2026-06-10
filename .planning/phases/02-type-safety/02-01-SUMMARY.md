---
phase: 02-type-safety
plan: "01"
subsystem: testing
tags: [mypy, typing, TypedDict, type-safety, annotations]

# Dependency graph
requires: []
provides:
  - "mypy strict mode enabled globally in pyproject.toml"
  - "_odoo_types.py with IrModelRecord, IrModelFieldsRecord, ReportAction, LanguageRecord TypedDicts"
  - "from __future__ import annotations in all 12 source modules"
  - "_yaml_dumper.py annotated (increase_indent typed)"
  - "_progress.py annotated (return type tqdm[Any])"
  - "6 per-module ignore_errors override ramp blocks (Plans 02-02..02-08)"
  - "types-tqdm>=4.66.0 added to dev deps"
affects: [02-02, 02-03, 02-04, 02-05, 02-06, 02-07, 02-08]

# Tech tracking
tech-stack:
  added: [mypy>=1.18, types-tqdm>=4.66.0]
  patterns:
    - "strict = true with per-module ignore_errors override ramp"
    - "from __future__ import annotations first import in every _*.py module"
    - "TypedDict for Odoo RPC response shapes (IrModelRecord, LanguageRecord etc.)"
    - "tqdm[Any] as concrete generic return type for progress_bar()"
    - "follow_untyped_imports = true for odoorpc_toolbox.* (replaces ignore_missing_imports)"

key-files:
  created:
    - odoo_fast_report_mapper/_odoo_types.py
  modified:
    - pyproject.toml
    - uv.lock
    - odoo_fast_report_mapper/_yaml_dumper.py
    - odoo_fast_report_mapper/_progress.py
    - odoo_fast_report_mapper/__init__.py
    - odoo_fast_report_mapper/__version__.py
    - odoo_fast_report_mapper/_exceptions.py
    - odoo_fast_report_mapper/_lang_utils.py
    - odoo_fast_report_mapper/_logging.py
    - odoo_fast_report_mapper/_report.py
    - odoo_fast_report_mapper/_utils.py
    - odoo_fast_report_mapper/_connection.py
    - odoo_fast_report_mapper/_cli.py

key-decisions:
  - "mypy strict = true enabled globally on day one; 6 pending modules gated with ignore_errors = true override ramp"
  - "follow_untyped_imports = true for odoorpc_toolbox.* replaces blanket ignore_missing_imports (D-03)"
  - "mypy pin raised from >=1.0 to >=1.18 (follow_untyped_imports requires 1.18; lockfile resolved to 2.1.0)"
  - "types-tqdm added to dev deps: tqdm 4.67.3 lacks py.typed marker despite plan research suggesting otherwise"
  - "_yaml_dumper and _progress cleared in this plan (NOT gated); all other pending modules gated for Plans 02-02..02-08"
  - "tqdm[Any] as concrete return type for progress_bar() resolves no-any-return error"

patterns-established:
  - "Override ramp: strict = true globally + per-module ignore_errors = true blocks removed plan-by-plan"
  - "__future__ annotations placement: first import after copyright comment block and docstring"
  - "TypedDict style: X | Literal[False] union syntax (not Optional), total=True for complete shapes"

requirements-completed: [TYPE-01, TYPE-02, TYPE-03]

# Metrics
duration: 15min
completed: 2026-06-10
---

# Phase 02 Plan 01: Mypy Strict Scaffolding Summary

**mypy strict mode enabled globally with 6-module override ramp, _odoo_types.py TypedDicts created, and from __future__ import annotations added project-wide**

## Performance

- **Duration:** ~15 min
- **Started:** 2026-06-10T00:00:00Z
- **Completed:** 2026-06-10T00:15:00Z
- **Tasks:** 3
- **Files modified:** 13

## Accomplishments
- Replaced `[tool.mypy]` loose config with `strict = true` + 6 per-module `ignore_errors` override ramp
- Created `_odoo_types.py` with 4 TypedDicts: IrModelRecord, IrModelFieldsRecord, ReportAction, LanguageRecord
- Added `from __future__ import annotations` to all 12 source modules
- Annotated `_yaml_dumper.py` (increase_indent params+return) and `_progress.py` (tqdm[Any] return type)
- `uv run mypy odoo_fast_report_mapper/` passes with 0 errors in strict mode
- `uv run pytest` passes with 347 tests

## Task Commits

Each task was committed atomically:

1. **Task 1: Update pyproject.toml — mypy strict config + override ramp scaffold** - `c2e4a91` ([CHG])
2. **Task 2: Create _odoo_types.py — TypedDict shapes for Odoo RPC responses** - `1343cba` ([ADD])
3. **Task 3: Add __future__ annotations project-wide + annotate _yaml_dumper.py and _progress.py** - `49ba720` ([CHG])

## Files Created/Modified
- `odoo_fast_report_mapper/_odoo_types.py` - New TypedDict definitions for Odoo RPC response shapes (IrModelRecord, IrModelFieldsRecord, ReportAction, LanguageRecord)
- `pyproject.toml` - mypy strict config, follow_untyped_imports override, 6 ignore_errors blocks, mypy pin >=1.18, types-tqdm dep
- `uv.lock` - Updated lockfile (mypy 1.19.1 -> 2.1.0, types-tqdm 4.68.0 added)
- `odoo_fast_report_mapper/_yaml_dumper.py` - from __future__; increase_indent annotated (flow: bool, indentless: bool) -> None
- `odoo_fast_report_mapper/_progress.py` - from __future__; return type changed Iterable[Any] -> tqdm[Any]
- `odoo_fast_report_mapper/__init__.py` - from __future__ added
- `odoo_fast_report_mapper/__version__.py` - from __future__ added
- `odoo_fast_report_mapper/_exceptions.py` - from __future__ added
- `odoo_fast_report_mapper/_lang_utils.py` - from __future__ added
- `odoo_fast_report_mapper/_logging.py` - from __future__ added
- `odoo_fast_report_mapper/_report.py` - from __future__ added
- `odoo_fast_report_mapper/_utils.py` - from __future__ added
- `odoo_fast_report_mapper/_connection.py` - from __future__ added
- `odoo_fast_report_mapper/_cli.py` - from __future__ added

## Decisions Made
- mypy pin raised from `>=1.0` to `>=1.18`; lockfile resolved to 2.1.0 (satisfies constraint)
- `follow_untyped_imports = true` for odoorpc_toolbox.* replaces blanket `ignore_missing_imports = true`
- `_yaml_dumper` and `_progress` cleared in this plan (no ignore_errors blocks); all other pending modules gated
- `tqdm[Any]` as concrete return type for `progress_bar()` (resolves no-any-return)
- `types-tqdm` added as dev dep — tqdm 4.67.3 ships without py.typed despite plan research suggesting >=4.66 includes it

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 2 - Missing Critical] Added types-tqdm dev dependency**
- **Found during:** Task 2 (_odoo_types.py verification)
- **Issue:** Plan stated "tqdm ships py.typed + stubs (tqdm ≥ 4.66)" but tqdm 4.67.3 in this environment lacks py.typed marker. mypy strict mode raised `import-untyped` error for tqdm import in _progress.py.
- **Fix:** Added `types-tqdm>=4.66.0` to `[project.optional-dependencies].dev` in pyproject.toml; updated lockfile (types-tqdm 4.68.0 installed)
- **Files modified:** pyproject.toml, uv.lock
- **Verification:** mypy --strict on _odoo_types.py and _progress.py both exit 0 after fix
- **Committed in:** 1343cba (Task 2 commit)

---

**Total deviations:** 1 auto-fixed (Rule 2 - missing critical dev dep)
**Impact on plan:** Required for correct mypy operation. No scope creep.

## Issues Encountered
- tqdm 4.67.3 lacks py.typed despite plan research stating tqdm >=4.66 ships stubs. Fixed by adding types-tqdm to dev deps.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- Plan 02-01 scaffolding complete: strict mode active, 6 modules gated with override ramp
- Plan 02-02 (_lang_utils.py, 7 errors) ready to begin: remove ignore_errors block, annotate bare dict params
- Plan 02-03 (_logging.py, 19 errors) follows in wave 2
- All TypedDicts available in _odoo_types.py for use by Plans 02-06/02-07

## Self-Check

### Files exist:
- `odoo_fast_report_mapper/_odoo_types.py` exists: FOUND
- `pyproject.toml` has strict = true: FOUND
- `pyproject.toml` has follow_untyped_imports: FOUND

### Commits exist:
- c2e4a91: FOUND
- 1343cba: FOUND
- 49ba720: FOUND

## Self-Check: PASSED

---
*Phase: 02-type-safety*
*Completed: 2026-06-10*
