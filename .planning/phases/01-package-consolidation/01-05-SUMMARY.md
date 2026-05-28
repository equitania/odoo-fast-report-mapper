---
phase: 01-package-consolidation
plan: 05
subsystem: cli,api,tests
tags: [odoo, report, yaml, refactor, consolidation, import-switch, cleanup]

# Dependency graph
requires:
  - phase: 01-package-consolidation
    provides: "all _*.py private submodules — Waves 1-4"
provides:
  - "single-package codebase: odoo_fast_report_mapper only"
  - "all Phase 1 ROADMAP success criteria (SC-1 through SC-5)"
affects:
  - "Phase 2: Type Safety (now has stable import paths to annotate)"
  - "Phase 1.1: Correctness Bug Fixes"

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "CLI module renamed: odoo_fast_report_mapper.py -> _cli.py"
    - "All eq_utils.* -> _utils.* in CLI"
    - "All logging_config -> _logging in CLI"
    - "test_connection.py patches odoo_fast_report_mapper._connection.prepare_connection (not _utils)"
    - "conftest.py mock_odoorpc patches odoo_fast_report_mapper._utils.ODOO"
    - "test_progress.py: dead API classes removed, TestProgressBarFunction retained"
    - "Namespace package elimination: empty odoo_report_helper/ dir also removed (rmdir)"

key-files:
  created:
    - "odoo_fast_report_mapper/_cli.py"
    - "tests/test_connection.py"
    - "tests/test_utils.py"
    - ".planning/phases/01-package-consolidation/coverage-post.txt"
    - ".planning/phases/01-package-consolidation/coverage-post.json"
  modified:
    - "odoo_fast_report_mapper/__init__.py — D-04 re-export pattern"
    - "tests/conftest.py — mock patch path updated to _utils.ODOO"
    - "tests/test_report.py — merged, uses _report.Report"
    - "tests/test_exceptions.py — imports from top-level package"
    - "tests/test_lang_utils.py — imports from _lang_utils"
    - "tests/test_logging.py — imports from _logging"
    - "tests/test_progress.py — dead tests removed, import from _progress"
    - "tests/test_cli.py — imports from _cli, patches _cli._utils"
    - "pyproject.toml — entry points, packages.find, coverage.run, ruff.isort"
  deleted:
    - "odoo_fast_report_mapper/odoo_fast_report_mapper.py (replaced by _cli.py)"
    - "odoo_fast_report_mapper/eq_odoo_connection.py"
    - "odoo_fast_report_mapper/eq_report.py"
    - "odoo_fast_report_mapper/eq_utils.py"
    - "odoo_fast_report_mapper/lang_utils.py"
    - "odoo_fast_report_mapper/logging_config.py"
    - "odoo_fast_report_mapper/progress.py"
    - "odoo_report_helper/__init__.py"
    - "odoo_report_helper/odoo_connection.py"
    - "odoo_report_helper/report.py"
    - "odoo_report_helper/utils.py"
    - "odoo_report_helper/exceptions.py"
    - "tests/test_odoo_connection.py"
    - "tests/test_eq_odoo_connection.py"
    - "tests/test_eq_report.py"
    - "tests/test_helper_utils.py"
    - "tests/test_eq_utils.py"

key-decisions:
  - "Patch path is _connection.prepare_connection (not _utils.prepare_connection) — prepare_connection is bound in _connection.py at import time"
  - "conftest.py mock_odoorpc patches _utils.ODOO correctly — this is where OdooConnection is instantiated"
  - "merged Report requires company_id positional argument (EqReport-style) — base-style tests adapted with company_id=False"
  - "minimal_report fixture uses dependencies=[] so add_dependencies works (not False which is EqReport default)"
  - "Empty odoo_report_helper/ directory (with __pycache__) was treated as namespace package — required rmdir after git rm of files"
  - "21 dead API tests removed: TestProgressBar (11), TestCreateProgressBar (4), TestReportProgress (6)"
  - "test_connection.py has 104 tests merged from 2 source files"

requirements-completed:
  - CONS-01
  - CONS-02
  - CONS-03
  - CONS-04
  - DEAD-01
  - DEAD-02
  - DEAD-03

# Metrics
duration: 65min
completed: 2026-05-28
---

# Phase 01 Plan 05: Wave 5 — Import Switch, CLI Rename, Test Merge, Delete Summary

**Single-package consolidation complete: all imports switched to private submodules, CLI renamed to _cli.py, old eq_* files and entire odoo_report_helper/ package deleted, 21 dead API tests removed, 335 tests green, all 5 Phase 1 success criteria pass**

## Performance

- **Duration:** ~65 min
- **Started:** 2026-05-28T13:20:00Z
- **Completed:** 2026-05-28T14:25:00Z
- **Tasks:** 4
- **Files created:** 5 (including coverage reports)
- **Files deleted:** 17 source + test files

## Accomplishments

### Task 1: __init__.py rewrite + conftest.py
- `__init__.py` now exports `OdooConnection`, `Report`, `create_connection_from_env`, `OdooConnectionError`, `PathDoesNotExistError`, `PathDoesNotExitError` from private submodules
- `conftest.py` `mock_odoorpc` now patches `odoo_fast_report_mapper._utils.ODOO`

### Task 2: CLI rename + pyproject.toml
- `_cli.py` created from `odoo_fast_report_mapper.py` with `_utils` and `_logging` imports
- `pyproject.toml`: both entry points point to `_cli:start_odoo_fast_report_mapper`
- `pyproject.toml`: removed all `odoo_report_helper` references from packages, coverage, isort

### Task 3: Test file merges (8 files)
- `test_connection.py`: 104 tests, covers full OdooConnection merged class; patches `_connection.prepare_connection`
- `test_report.py`: 62 tests, uses `_report.Report` with `company_id` required
- `test_utils.py`: covers `_utils.*` including `prepare_connection`, `self_clean`, `parse_yaml*`
- `test_exceptions.py`: imports from top-level package
- `test_lang_utils.py`: imports from `_lang_utils`
- `test_logging.py`: imports from `_logging`
- `test_progress.py`: 4 tests (21 dead tests removed)
- `test_cli.py`: patches `_cli._utils`

### Task 4: Deletions + verification
- All 12 old source files deleted
- 5 old test files deleted
- Empty `odoo_report_helper/` namespace directory removed
- All 5 Phase 1 success criteria verified

## Phase 1 Success Criteria: ALL PASS

| Criterion | Check | Result |
|-----------|-------|--------|
| SC-1 | `uv run pytest tests/test_connection.py` standalone | 104 PASS |
| SC-2 | `import odoo_report_helper` raises `ModuleNotFoundError` | PASS |
| SC-3 | `from odoo_fast_report_mapper import OdooConnection` | PASS |
| SC-4 | `from odoo_fast_report_mapper._progress import ProgressBar` raises `ImportError` | PASS |
| SC-4 | `from odoo_fast_report_mapper.progress import ProgressBar` raises `ModuleNotFoundError` | PASS |
| SC-5 | `uv run pytest -q` → 335 passed, 0 failures | PASS |

## Verification Results

1. `import odoo_report_helper` — `ModuleNotFoundError`: 1 (PASS)
2. `from odoo_fast_report_mapper import OdooConnection` — exits 0, prints PASS (PASS)
3. Dead API verification (SC-4): Both checks pass
4. `uv run pytest tests/test_connection.py -v` — 104 passed (PASS)
5. `uv run pytest -q` — 335 passed (PASS)
6. `odoo-fast-report-mapper --help` — exits 0, shows Usage (PASS)
7. `odoo-fr-mapper --help` — exits 0, shows Usage (PASS)
8. `grep -c "odoo_report_helper" pyproject.toml` — 0 (PASS)
9. `uv run ruff check .` — All checks passed (PASS)
10. `uv build` — Successfully built wheel + sdist (PASS)
11. Coverage total: 92% (fail_under=60 passes) (PASS)
12. Coverage loss: only from deleted dead-code modules and old helper files (ACCEPTABLE)

## Coverage Delta

| Metric | Baseline | Post-Phase-1 |
|--------|---------|--------------|
| Total coverage | 92.43% | 92% |
| Tests | 369 | 335 |
| Delta | - | -0.43% (acceptable: dead code deleted) |

Coverage loss is exclusively from deleted modules:
- `odoo_report_helper/*`: 0% (package deleted)
- `odoo_fast_report_mapper/progress.py`: 0% (file deleted)
- `odoo_fast_report_mapper/eq_*.py`: 0% (files deleted)

Test count difference: 369 → 335 (−34 tests = 21 dead-API + 13 duplicate base-class tests absorbed into merged files with fewer assertions)

## Task Commits

1. **Task 1**: `023641c` — rewrite __init__.py D-04 pattern, conftest mock patch path
2. **Task 2**: `4b849ca` — create _cli.py, update pyproject.toml entry points
3. **Task 3**: `5d46bcc` — merge 8 test files to private submodule paths
4. **Task 4**: `79c1fcd` — delete old files, verify all SC, coverage reports

## Deviations from Plan

### [Rule 1 - Bug] Fixed patch target in test_connection.py

- **Found during:** Task 3 (test merge)
- **Issue:** Plan specified patching `"odoo_fast_report_mapper._utils.prepare_connection"` but `_connection.py` imports `prepare_connection` at module load time — the bound name lives in `odoo_fast_report_mapper._connection`, not `_utils`
- **Fix:** Changed patch to `"odoo_fast_report_mapper._connection.prepare_connection"` throughout test_connection.py
- **Files modified:** `tests/test_connection.py`

### [Rule 1 - Bug] Empty namespace package directory caused SC-2 failure

- **Found during:** Task 4 verification
- **Issue:** After `git rm` of all Python files, `odoo_report_helper/` directory remained with only `__pycache__`. Python treated it as a namespace package, making `import odoo_report_helper` succeed (returning None `__file__`)
- **Fix:** `rmdir odoo_report_helper/__pycache__ && rmdir odoo_report_helper/`
- **Files modified:** Directory deleted (not a git-tracked file)

### [Rule 1 - Bug] merged Report requires `company_id` — base-style test fixtures incompatible

- **Found during:** Task 3 (test_report.py merge)
- **Issue:** `minimal_report` and `full_report` fixtures in old `test_report.py` used base `Report(entry_name="string", ...)` without `company_id`, but merged `_report.Report` requires `company_id` as positional arg
- **Fix:** Added `company_id=False` to fixtures; used `entry_name={"de_DE": ..., "en_US": ...}` dict (EqReport style) for self_ensure tests; used `dependencies=[]` (not `False`) for add_dependencies tests
- **Files modified:** `tests/test_report.py`

## Known Stubs

None — all data flows are live; no placeholder values or TODO/FIXME markers in logic paths.

## Threat Flags

None — no new network endpoints, auth paths, file access patterns, or schema changes introduced. This wave only deletes code.

## Self-Check: PASSED

Files created:
- `odoo_fast_report_mapper/_cli.py` — FOUND
- `tests/test_connection.py` — FOUND
- `tests/test_utils.py` — FOUND
- `.planning/phases/01-package-consolidation/coverage-post.txt` — FOUND
- `.planning/phases/01-package-consolidation/coverage-post.json` — FOUND

Commits:
- `023641c` — FOUND
- `4b849ca` — FOUND
- `5d46bcc` — FOUND
- `79c1fcd` — FOUND

Verifications:
- `python -c "from odoo_fast_report_mapper import OdooConnection"` — exits 0
- `python -c "import odoo_report_helper"` — ModuleNotFoundError
- `uv run pytest -q` — 335 passed, 0 failures
- `odoo-fast-report-mapper --help` — exits 0
- `odoo-fr-mapper --help` — exits 0
- `uv run ruff check .` — All checks passed
- `uv build` — Successfully built

---
*Phase: 01-package-consolidation*
*Completed: 2026-05-28*
