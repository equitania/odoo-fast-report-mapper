---
phase: 02-type-safety
plan: "02"
subsystem: testing
tags: [mypy, type-safety, python, annotations, dict, typing]

# Dependency graph
requires:
  - phase: 02-type-safety/02-01
    provides: mypy strict mode enabled globally; _yaml_dumper and _progress gated modules cleared
provides:
  - "_lang_utils.py fully annotated with dict[str, str] and str | dict[str, str] types"
  - "[[tool.mypy.overrides]] block for _lang_utils removed from pyproject.toml"
  - "_lang_utils no longer gated — mypy strict mode enforced directly"
affects:
  - 02-03
  - 02-04
  - 02-05

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "dict[str, str] for bilingual name_dict parameters (language code -> name)"
    - "str | dict[str, str] union for attachment params accepting legacy string or multi-lang dict"
    - "list[Any] with inline comment for Odoo domain tuple heterogeneous lists"
    - "Per-module override block removal pattern: annotate -> verify 0 errors -> remove override"

key-files:
  created: []
  modified:
    - odoo_fast_report_mapper/_lang_utils.py
    - pyproject.toml

key-decisions:
  - "dict[str, str] chosen for name_dict parameters (values are always report name strings, keys are locale codes)"
  - "list[Any] for build_name_search_domain return — Odoo domain tuples are heterogeneous (str, str, str) by convention"
  - "str | dict[str, str] for resolve_attachment_value attachment param — backward compat with legacy string callers"
  - "from typing import Any added (not Any from collections.abc) — standard typing module import"

patterns-established:
  - "Ramp pattern: annotate module, run mypy --strict without override, confirm 0 errors, remove override block"
  - "Inline comment Any: ... required for non-pre-justified Any usage (e.g. list[Any] in domain builders)"

requirements-completed:
  - TYPE-01
  - TYPE-02

# Metrics
duration: 8min
completed: 2026-06-10
---

# Phase 2 Plan 02: _lang_utils.py Type Annotation Summary

**`_lang_utils.py` fully annotated with `dict[str, str]` types and `str | dict[str, str]` union; mypy override block removed — module now enforced under strict mode directly.**

## Performance

- **Duration:** ~8 min
- **Started:** 2026-06-10T00:00:00Z
- **Completed:** 2026-06-10T00:08:00Z
- **Tasks:** 1
- **Files modified:** 3 (including uv.lock from venv rebuild)

## Accomplishments
- Annotated all 4 previously-bare functions in `_lang_utils.py` (7 mypy strict errors cleared)
- Removed `[[tool.mypy.overrides]] ignore_errors = true` block for `_lang_utils` from `pyproject.toml`
- `uv run mypy odoo_fast_report_mapper/` now checks 12 source files including `_lang_utils` directly — 0 errors
- 347 tests pass unchanged

## Task Commits

Each task was committed atomically:

1. **Task 1: Annotate _lang_utils.py and remove its override block** - `a260ef6` (chg)

## Files Created/Modified
- `odoo_fast_report_mapper/_lang_utils.py` - Added `from typing import Any`; annotated 4 functions with specific dict/list/union types
- `pyproject.toml` - Removed `[[tool.mypy.overrides]]` block for `odoo_fast_report_mapper._lang_utils`
- `uv.lock` - Refreshed by uv during mypy venv creation (Python 3.13 vs 3.12 platform difference)

## Decisions Made
- Used `dict[str, str]` for all `name_dict` parameters — both keys (locale codes) and values (report names) are always strings
- Used `list[Any]` for `build_name_search_domain` return type — Odoo domain tuples are heterogeneous `(str, str, str)` with no TypedDict shape; Tier 2 pre-justified per plan D-06
- Used `str | dict[str, str]` union for `resolve_attachment_value.attachment` — backward compat with callers passing plain strings
- Added `# Any: Odoo domain tuples contain mixed types (str, str, str)` inline comment per D-07 non-pre-justified Any policy

## Deviations from Plan

None — plan executed exactly as written. All 7 mypy errors resolved as specified in the per-function fix table in 02-PATTERNS.md.

## Issues Encountered

None. The `ignore_errors = true` override was masking all 7 errors from the standard `uv run mypy` output. Running `mypy --config-file /dev/null` confirmed the exact 7 errors listed in the plan, and each was resolved by the annotated signatures as designed.

## User Setup Required

None - annotation-only changes, no external service configuration required.

## Next Phase Readiness
- `_lang_utils` is now fully typed and enforced under strict mode
- Wave 2 parallel execution: Plan 02-03 (`_logging.py`, 19 errors) can merge alongside this plan
- Plans 02-04 through 02-08 depend only on 02-01 completion (already done) — this plan establishes the ramp pattern they follow
- Remaining gated modules: `_logging`, `_report`, `_utils`, `_connection`, `_cli`

---
*Phase: 02-type-safety*
*Completed: 2026-06-10*
