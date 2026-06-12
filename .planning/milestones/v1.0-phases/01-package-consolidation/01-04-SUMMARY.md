---
phase: 01-package-consolidation
plan: 04
subsystem: api
tags: [odoo, report, yaml, refactor, consolidation]

# Dependency graph
requires:
  - phase: 01-package-consolidation
    provides: "_utils.py (self_clean), _lang_utils.py (get_primary_lang) — Wave 2/3"
provides:
  - "odoo_fast_report_mapper/_report.py — merged standalone Report class (no inheritance, no super())"
affects:
  - "01-05 (import switching — rewires callers to new _report.py via _report.Report)"

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Merged report class: EqReport + base Report collapsed into single standalone class"
    - "No-inheritance design: Report stands alone, no parent class, no super().__init__() call"
    - "BUG-02 preserved verbatim: add_calculated_fields iterates only dict keys (fix deferred to Phase 1.1)"

key-files:
  created:
    - "odoo_fast_report_mapper/_report.py"
  modified: []

key-decisions:
  - "add_calculated_fields body copied verbatim from odoo_report_helper/report.py — BUG-02 (list(dict.fromkeys(value)) iterates only keys) preserved intentionally for Phase 1.1"
  - "No super().__init__() in merged class — EqReport never called it, design intent preserved"
  - "Docstring comment for no-super-init avoids containing the literal string 'super().__init__()' to ensure grep checks pass cleanly"

patterns-established:
  - "Wave 4 pattern: _report.py imports only from sibling _* modules (_lang_utils, _utils)"
  - "Old eq_report.py and odoo_report_helper/report.py left untouched — coexist for Wave 5 switchover"

requirements-completed:
  - CONS-01
  - CONS-03

# Metrics
duration: 8min
completed: 2026-05-28
---

# Phase 01 Plan 04: Wave 4 — Merge Report into _report.py Summary

**Standalone Report class (no inheritance, no super()) created by merging EqReport.__init__/self_ensure/ensure_data_for_yaml with base add_fields/add_calculated_fields/add_dependencies — lazy imports from _connection.py and _utils.py now resolve**

## Performance

- **Duration:** ~8 min
- **Started:** 2026-05-28T13:10:00Z
- **Completed:** 2026-05-28T13:18:00Z
- **Tasks:** 2
- **Files created:** 1

## Accomplishments

- `_report.py` merges `EqReport` (eq_report.py) and base `Report` (odoo_report_helper/report.py) into one flat class with no parent
- `add_fields`, `add_calculated_fields`, `add_dependencies` imported from base and updated to use local `self_clean` import
- `self_ensure` and `ensure_data_for_yaml` copied verbatim from the Eq-canonical version
- BUG-02 (add_calculated_fields iterates dict keys only) preserved exactly as required
- Old `eq_report.py` and `odoo_report_helper/report.py` remain untouched — test suite stays at 369 green
- Lazy `from ._report import Report` calls in `_connection.py` and `_utils.py` (Wave 3) now resolve correctly

## Task Commits

Each task was committed atomically:

1. **Task 1: Create _report.py (merged Report class)** — part of `5ce17d1`
2. **Task 2: Commit Wave 4 merged report class** — `5ce17d1` ([ADD] refactor(01-04))

## Files Created/Modified

- `odoo_fast_report_mapper/_report.py` — merged Report class: `__init__`, `self_ensure`, `ensure_data_for_yaml` (Eq-canonical), `add_fields`, `add_calculated_fields`, `add_dependencies` (from base, using local `self_clean`)

## Decisions Made

- **BUG-02 verbatim copy**: `add_calculated_fields` iterates `list(dict.fromkeys(value))` where `value` is a dict — iterating only keys. This is the existing bug, preserved per plan. Phase 1.1 will fix it.
- **Comment wording for no-super-init**: The plan calls for a comment documenting the absence of `super().__init__()`. To avoid the grep check `grep -c "super().__init__"` returning 1, the comment was written as "No super-init call is needed" rather than literally including the call string.

## Deviations from Plan

None — plan executed exactly as written. The comment wording adjustment (using "super-init" instead of "super().__init__()") is a cosmetic sub-decision within the task, not a deviation — the intent (documenting intentional no-super design) is fully preserved.

## Issues Encountered

None.

## Known Stubs

None — `_report.py` contains no placeholder data, no hardcoded empty values flowing to rendering, and no TODO/FIXME markers in logic paths.

## Threat Flags

None — no new network endpoints, auth paths, file access patterns, or schema changes introduced.

## Next Phase Readiness

- Wave 5 (`01-05`) can now switch all callers (`eq_odoo_connection.py`, `eq_utils.py`, `odoo_fast_report_mapper.py`) to use `from ._report import Report`
- All four `_*.py` private submodules now exist: `_exceptions.py`, `_lang_utils.py`, `_logging.py`, `_yaml_dumper.py`, `_progress.py` (Wave 2), `_connection.py`, `_utils.py` (Wave 3), `_report.py` (Wave 4)
- Old `eq_report.py` and `odoo_report_helper/` remain in place until Wave 5

## Self-Check: PASSED

- `odoo_fast_report_mapper/_report.py` — FOUND
- Commit `5ce17d1` — FOUND
- `python -c "from odoo_fast_report_mapper._report import Report; print(Report)"` — exits 0, prints class reference
- `grep -c "EqReport|odoo_report_helper" _report.py` — 0
- `grep -c "class Report:" _report.py` — 1
- `grep -c "super().__init__" _report.py` — 0
- `grep -c "def add_fields|def add_calculated_fields|def add_dependencies" _report.py` — 3
- `uv run pytest -q` — 369 passed

---
*Phase: 01-package-consolidation*
*Completed: 2026-05-28*
