---
phase: 04-release-preparation
plan: "01"
subsystem: packaging
tags: [pypi, version, manifest, semver, classifiers]

# Dependency graph
requires:
  - phase: 03-performance
    provides: RPC-count regression test used in CI perf gate
provides:
  - "Package version set to 1.0.0 (single-sourced from __version__.py)"
  - "pyproject.toml classifiers: Production/Stable + Python 3.14 + Migration Guide URL"
  - "MANIFEST.in: MIGRATION.md included, CLAUDE.md excluded from sdist"
  - "Legacy pre-GSD planning files removed from working tree"
affects: [04-02, 04-03, 04-04, 04-05]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Version single-source pattern: __version__.py -> pyproject.toml dynamic attr"
    - "sdist contents controlled via MANIFEST.in (no internal files shipped to PyPI)"

key-files:
  created: []
  modified:
    - "odoo_fast_report_mapper/__version__.py - version bumped to 1.0.0"
    - "pyproject.toml - classifiers, Python 3.14, Migration Guide URL"
    - "MANIFEST.in - CLAUDE.md replaced by MIGRATION.md"
  deleted:
    - "IMPROVEMENT_PLAN.md - superseded by .planning/ (D-13)"
    - "REVIEW.md - superseded by .planning/ (D-13)"
    - "TASK_TRACKING.md - superseded by .planning/ (D-13)"

key-decisions:
  - "D-11: Version 1.0.0 uses clean three-segment SemVer; __version_info__ tuple derived dynamically"
  - "D-14: CLAUDE.md excluded from sdist (internal developer instructions); MIGRATION.md included instead"
  - "D-13: Legacy pre-GSD files removed via git rm; history preserved in git"
  - "D-03: Migration Guide URL added to pyproject.toml [project.urls] for PyPI discoverability"

patterns-established:
  - "T-04-01 mitigated: CLAUDE.md no longer ships to PyPI users"

requirements-completed: [DOCS-03, GATE-05, CI-01]

# Metrics
duration: 8min
completed: 2026-06-12
---

# Phase 04 Plan 01: Version Bump and Packaging Cleanup Summary

**Version set to 1.0.0, pyproject.toml upgraded to Production/Stable with Python 3.14 classifier and Migration Guide URL, MANIFEST.in switches CLAUDE.md to MIGRATION.md, and three legacy pre-GSD planning files removed via git rm.**

## Performance

- **Duration:** ~8 min
- **Started:** 2026-06-12T00:00:00Z
- **Completed:** 2026-06-12
- **Tasks:** 2
- **Files modified:** 3 modified, 3 deleted

## Accomplishments

- Single-source version string updated from 0.9.7.4 to 1.0.0; `__version_info__` evaluates to `(1, 0, 0)` at runtime
- pyproject.toml classifiers now reflect Production/Stable and Python 3.14; Migration Guide URL discoverable from PyPI
- MANIFEST.in no longer ships CLAUDE.md (internal instructions) to PyPI users; MIGRATION.md ships instead (T-04-01 mitigated)
- Three legacy pre-GSD planning files (IMPROVEMENT_PLAN.md, REVIEW.md, TASK_TRACKING.md) removed from working tree per D-13; content preserved in git history

## Task Commits

Each task was committed atomically:

1. **Task 1: Bump version to 1.0.0 and update pyproject.toml metadata** - `433681d` ([CHG])
2. **Task 2: Fix MANIFEST.in and remove legacy planning files** - `b0f648a` ([CHG])

**Plan metadata:** (docs commit follows)

## Files Created/Modified

- `odoo_fast_report_mapper/__version__.py` - Version changed from "0.9.7.4" to "1.0.0"
- `pyproject.toml` - Beta -> Production/Stable classifier, Python 3.14 added, Migration Guide URL added
- `MANIFEST.in` - Line 3: "include CLAUDE.md" replaced with "include MIGRATION.md"
- `IMPROVEMENT_PLAN.md` - Deleted via git rm (D-13)
- `REVIEW.md` - Deleted via git rm (D-13)
- `TASK_TRACKING.md` - Deleted via git rm (D-13)

## Decisions Made

- No new decisions beyond executing D-11, D-12, D-13, D-14, D-03 from 04-CONTEXT.md
- No `[[tool.mypy.overrides]]` block for `odoo_report_helper.*` was present (already removed in Phase 1); no action needed

## Deviations from Plan

None - plan executed exactly as written.

## Threat Surface Scan

T-04-01 (Information Disclosure via MANIFEST.in) was the targeted threat for this plan. CLAUDE.md is now excluded from the sdist. No new security-relevant surfaces were introduced.

## Issues Encountered

None.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- Version 1.0.0 is set; all subsequent plans (04-02 through 04-05) can reference it consistently
- MIGRATION.md slot in MANIFEST.in is ready; Plan 04-02 will create the actual MIGRATION.md file
- Legacy files removed; repo root is clean for documentation work

---
*Phase: 04-release-preparation*
*Completed: 2026-06-12*
