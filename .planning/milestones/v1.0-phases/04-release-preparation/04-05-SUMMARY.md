---
phase: 04-release-preparation
plan: "05"
subsystem: testing
tags: [pytest, ruff, mypy, uv-build, release-gates, manifest, sdist]

# Dependency graph
requires:
  - phase: 04-01
    provides: CI/CD workflows and branch protection baseline
  - phase: 04-02
    provides: Type-safety (mypy --strict) applied to package
  - phase: 04-03
    provides: MIGRATION.md and RELEASE_NOTES.md authored
  - phase: 04-04
    provides: README.md and CLAUDE.md updated for v1.0 single-package layout
provides:
  - All automated release-quality gates confirmed passing (GATE-01..GATE-05)
  - Captain-reviewed and approved MIGRATION.md (GATE-04)
  - Built wheel and sdist dist/odoo_fast_report_mapper_equitania-1.0.0-* ready for uv publish
  - Documented GitHub branch-protection check names for Captain to configure
  - MANIFEST.in excludes CLAUDE.md (T-04-09 mitigated)
affects: [uv publish, GitHub branch protection settings]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "All release gates run sequentially before checkpoint: pytest → ruff → mypy → uv build"
    - "MANIFEST.in exclude pattern prevents information-disclosure from sdist"
    - "Captain-only publish gate: uv publish is never automated"

key-files:
  created:
    - dist/odoo_fast_report_mapper_equitania-1.0.0-py3-none-any.whl
    - dist/odoo_fast_report_mapper_equitania-1.0.0.tar.gz
  modified:
    - MANIFEST.in (added exclude CLAUDE.md)
    - odoo_fast_report_mapper/_connection.py (ruff: removed unused imports)
    - odoo_fast_report_mapper/_report.py (ruff: removed unused imports, formatting)
    - odoo_fast_report_mapper/_utils.py (ruff: removed unused imports)
    - odoo_fast_report_mapper/odoo_fast_report_mapper.py (ruff: removed unused imports)

key-decisions:
  - "uv publish is Captain-only — never automated in CI (GATE-05 policy, CONTEXT.md D-13)"
  - "CLAUDE.md excluded from sdist via MANIFEST.in to prevent information disclosure (T-04-09)"
  - "GitHub branch-protection required check names documented: test (3.12), test (3.13), test (3.14), perf, build"
  - "GATE-04 manual review: Captain approved MIGRATION.md on 2026-06-12"

patterns-established:
  - "Release gate sequence: GATE-01 tests → GATE-02 ruff → GATE-03 mypy --strict → GATE-05 uv build → GATE-04 Captain review"

requirements-completed: [GATE-01, GATE-02, GATE-03, GATE-04, GATE-05, DOCS-04]

# Metrics
duration: ~20min
completed: 2026-06-12
---

# Phase 04 Plan 05: Release Quality Gates Summary

**All five release gates green: 349 tests passed, ruff/mypy-strict clean, wheel+sdist built with MIGRATION.md included and CLAUDE.md excluded, MIGRATION.md approved by Captain — package ready for `uv publish`.**

## Performance

- **Duration:** ~20 min
- **Started:** 2026-06-12T00:00:00Z
- **Completed:** 2026-06-12T00:20:00Z
- **Tasks:** 2 (1 automated + 1 checkpoint)
- **Files modified:** 5 (4 source files via ruff auto-fix, MANIFEST.in)

## Accomplishments

- GATE-01: pytest — 349 tests passed (exit 0)
- GATE-02: ruff check + format — clean after auto-fix (11 unused imports removed, 4 files reformatted)
- GATE-03: mypy --strict — Success, 12 source files, 0 errors
- GATE-05 partial: uv build — wheel and sdist produced; sdist contains MIGRATION.md and excludes CLAUDE.md
- GATE-04: MIGRATION.md reviewed and approved by Captain on 2026-06-12

## Release Gate Evidence

| Gate | Tool | Result | Notes |
|------|------|--------|-------|
| GATE-01 | `uv run pytest` | 349 passed | Exit 0 |
| GATE-02 | `uv run ruff check .` + `ruff format --check .` | Clean | Auto-fixed 11 unused imports, 4 files formatted |
| GATE-03 | `uv run mypy odoo_fast_report_mapper/ --strict` | Success: 0 issues, 12 files | Exit 0 |
| GATE-05 partial | `uv build` | Wheel + sdist produced | 1.0.0 artifacts in dist/ |
| GATE-04 | Captain review of MIGRATION.md | Approved 2026-06-12 | Manual checkpoint |

## Branch Protection Check Names (GitHub Settings)

Required status checks for `main` and `develop` branch protection rules
(repo Settings → Branches → "Require status checks to pass before merging"):

- `test (3.12)`
- `test (3.13)`
- `test (3.14)`
- `perf`
- `build`

## Task Commits

Each task was committed atomically:

1. **Task 1: Run all automated release-quality gates**
   - `1d0aa15` — [FIX] Remove unused imports and fix formatting (GATE-02 ruff clean)
   - `4ec5799` — [FIX] Exclude CLAUDE.md from sdist to prevent information disclosure (T-04-09)
2. **Checkpoint GATE-04:** Captain approved MIGRATION.md (2026-06-12, no code commit)

**Plan metadata:** *(this commit)*

## Files Created/Modified

- `dist/odoo_fast_report_mapper_equitania-1.0.0-py3-none-any.whl` — Built wheel for PyPI
- `dist/odoo_fast_report_mapper_equitania-1.0.0.tar.gz` — Built sdist for PyPI
- `MANIFEST.in` — Added `exclude CLAUDE.md` to prevent information disclosure in sdist
- `odoo_fast_report_mapper/_connection.py` — Removed 4 unused imports (ruff auto-fix)
- `odoo_fast_report_mapper/_report.py` — Removed 3 unused imports, formatting (ruff auto-fix)
- `odoo_fast_report_mapper/_utils.py` — Removed 2 unused imports (ruff auto-fix)
- `odoo_fast_report_mapper/odoo_fast_report_mapper.py` — Removed 2 unused imports (ruff auto-fix)

## Decisions Made

- `uv publish` stays Captain-only — never automated (GATE-05 policy confirmed)
- CLAUDE.md excluded from sdist via MANIFEST.in `exclude CLAUDE.md` (mitigates T-04-09)
- Branch-protection check names documented for Captain's GitHub settings configuration

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 2 - Missing Critical] MANIFEST.in missing CLAUDE.md exclusion**
- **Found during:** Task 1 (GATE-05 sdist contents check)
- **Issue:** `tar -tzf dist/*1.0.0*.tar.gz | grep CLAUDE` returned a hit — CLAUDE.md was included in the sdist, exposing internal project instructions (T-04-09: Information Disclosure threat)
- **Fix:** Added `exclude CLAUDE.md` to MANIFEST.in; rebuilt sdist to confirm exclusion
- **Files modified:** `MANIFEST.in`
- **Verification:** `tar -tzf dist/*1.0.0*.tar.gz | grep CLAUDE` returned no output after fix
- **Committed in:** `4ec5799`

**2. [Rule 1 - Bug] Ruff reported 11 unused imports across 4 source files**
- **Found during:** Task 1 (GATE-02 ruff check)
- **Issue:** `uv run ruff check .` returned lint errors in `_connection.py`, `_report.py`, `_utils.py`, `odoo_fast_report_mapper.py`
- **Fix:** `uv run ruff check . --fix` applied automatically; `uv run ruff format .` reformatted 4 files
- **Files modified:** `odoo_fast_report_mapper/_connection.py`, `_report.py`, `_utils.py`, `odoo_fast_report_mapper.py`
- **Verification:** `uv run ruff check . && uv run ruff format --check .` both exit 0 with no output
- **Committed in:** `1d0aa15`

---

**Total deviations:** 2 auto-fixed (1 missing critical / information disclosure, 1 bug / lint errors)
**Impact on plan:** Both fixes essential for security and release quality. No scope creep.

## Issues Encountered

None — all automated gates passed after auto-fixes; GATE-04 checkpoint approved by Captain without required corrections.

## User Setup Required

**Captain actions required before final release:**

1. **GitHub branch protection** — Configure required status checks on `main` and `develop`:
   - `test (3.12)`, `test (3.13)`, `test (3.14)`, `perf`, `build`
2. **PyPI publish** — Run locally on Mac:
   ```bash
   cd /Users/picard/gitbase/PyPi-Projects/odoo-fast-report-mapper
   uv publish
   ```
   (Never automated in CI per GATE-05 policy)

## Threat Flags

No new security surface introduced. T-04-09 (Information Disclosure via sdist CLAUDE.md) was detected and mitigated via MANIFEST.in fix in this plan.

## Next Phase Readiness

- All release gates green — package is ready for `uv publish`
- dist/ artifacts are current and verified
- Phase 04 (release-preparation) is complete; this is the final plan

---
*Phase: 04-release-preparation*
*Completed: 2026-06-12*
