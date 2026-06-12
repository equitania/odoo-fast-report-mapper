---
phase: 01-package-consolidation
plan: 03
subsystem: api
tags: [odoo, connection, yaml, rpc, refactor, consolidation]

# Dependency graph
requires:
  - phase: 01-package-consolidation
    provides: _exceptions.py, _lang_utils.py, _logging.py, _yaml_dumper.py, _progress.py (Wave 2)
provides:
  - "odoo_fast_report_mapper/_connection.py — merged OdooConnection class, no inheritance, no circular import"
  - "odoo_fast_report_mapper/_utils.py — all helper and factory functions, self-contained"
affects:
  - "01-04 (creates _report.py — referenced lazily from _connection.py and _utils.py)"
  - "01-05 (import switching — rewires callers to new _* modules)"

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Lazy imports (from ._report import Report inside functions) avoid forward-reference before _report.py exists"
    - "Merged constructor: explicit positional params replace *args/**kwargs pass-through to base class"
    - "No-inheritance design: OdooConnection stands alone, circular import eliminated"

key-files:
  created:
    - "odoo_fast_report_mapper/_connection.py"
    - "odoo_fast_report_mapper/_utils.py"
  modified: []

key-decisions:
  - "Lazy import pattern for _report.Report inside create_eq_report_object and create_report_object_from_yaml_object — avoids forward-reference error before Wave 4 creates _report.py"
  - "Comment-only references to odoo_report_helper in docstrings are acceptable — only functional imports are prohibited by plan verification"
  - "Merged __init__ preserves all positional parameter semantics (language, collect_yaml, disable_qweb, workflow, url, port, username, password, database, auth_method)"

patterns-established:
  - "Wave 3 pattern: new _* files import only from sibling _* modules, never from odoo_report_helper or old eq_* modules"
  - "BUG-01 (unguarded model_id[0] in add_field_to_dictionary) preserved verbatim — Phase 1.1 adds the guard"

requirements-completed:
  - CONS-01
  - CONS-02
  - CONS-03
  - CONS-04

# Metrics
duration: 15min
completed: 2026-05-28
---

# Phase 01 Plan 03: Wave 3 — Merge OdooConnection + Create _utils.py Summary

**Standalone OdooConnection class (no inheritance, no super()) and merged _utils.py created — circular import between odoo_report_helper and odoo_fast_report_mapper eliminated**

## Performance

- **Duration:** ~15 min
- **Started:** 2026-05-28T12:58:00Z
- **Completed:** 2026-05-28T13:05:00Z
- **Tasks:** 3
- **Files created:** 2

## Accomplishments

- `_utils.py` merges all helper functions from `odoo_report_helper/utils.py` plus all factory/utility functions from `eq_utils.py` — no cross-package imports
- `_connection.py` merges base `OdooConnection` and `EqOdooConnection` into one flat class — constructor takes explicit params, no `super().__init__()` call
- Circular import `odoo_report_helper/odoo_connection.py → lang_utils.py → odoo_fast_report_mapper/` fully eliminated in the new modules
- Old `eq_odoo_connection.py`, `eq_utils.py`, `odoo_report_helper/` remain untouched — test suite stays at 369 green

## Task Commits

Each task was committed atomically:

1. **Task 1: Create _utils.py** — part of `70aaff9`
2. **Task 2: Create _connection.py** — part of `70aaff9`
3. **Task 3: Commit Wave 3 files** — `70aaff9` ([ADD] refactor(01-03))

## Files Created/Modified

- `odoo_fast_report_mapper/_utils.py` — merged helper functions (prepare_connection, self_clean, parse_yaml_folder, fire_all_functions, parse_yaml, parse_yaml_folder_with_filenames) + all factory functions (create_connection_from_env, create_report_object_from_yaml_object, create_odoo_connection_from_yaml_object, build_reports_from_yaml_objects, collect_all_reports, collect_all_connections, list_yaml_reports, generate_env_template, convert_all_yaml_objects)
- `odoo_fast_report_mapper/_connection.py` — merged OdooConnection class: explicit constructor, login, _get_fast_report_ids, check_module, check_dependencies, map_reports, set_calculated_fields, _search_report, _search_report_v13, collect_report_entries, add_field_to_dictionary, create_eq_report_object, write_yaml, test_fast_report_rendering, disable_qweb_reports, and all helper methods

## Decisions Made

- **Lazy imports for _report.Report**: Both `create_report_object_from_yaml_object` (_utils.py) and `create_eq_report_object` (_connection.py) use `from ._report import Report` inside the function body. This avoids a forward-reference error before `_report.py` is created in Wave 4, while keeping the code clean and identical to what Wave 5 will produce.
- **Comments mentioning odoo_report_helper are acceptable**: The plan verification intent is zero functional cross-package imports. Docstring mentions of source file paths are documentation, not imports.
- **BUG-01 preserved verbatim**: `add_field_to_dictionary` retains the unguarded `model_id[0]` access as required by the plan (Phase 1.1 will add the guard).

## Deviations from Plan

None — plan executed exactly as written. The comment-only mentions of `odoo_report_helper` in module docstrings are not a deviation; they are historical attribution notes, not functional imports.

## Issues Encountered

None.

## Known Stubs

None — the new files contain no placeholder data, no hardcoded empty values flowing to UI, and no TODO/FIXME markers in logic paths.

## Threat Flags

None — no new network endpoints, auth paths, file access patterns, or schema changes introduced.

## Next Phase Readiness

- Wave 4 (`01-04`) can create `_report.py` — the lazy `from ._report import Report` in both `_connection.py` and `_utils.py` will resolve correctly once that file exists
- Wave 5 (`01-05`) can switch all callers to the new `_*` modules
- Old `eq_odoo_connection.py` and `eq_utils.py` remain in place until Wave 5

## Self-Check: PASSED

- `odoo_fast_report_mapper/_connection.py` — FOUND
- `odoo_fast_report_mapper/_utils.py` — FOUND
- Commit `70aaff9` — FOUND
- `python -c "from odoo_fast_report_mapper._connection import OdooConnection"` — exits 0
- `python -c "from odoo_fast_report_mapper._utils import create_connection_from_env, prepare_connection"` — exits 0
- `uv run pytest -q` — 369 passed

---
*Phase: 01-package-consolidation*
*Completed: 2026-05-28*
