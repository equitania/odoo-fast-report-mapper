---
phase: "04-release-preparation"
plan: "02"
subsystem: "ci"
tags: ["github-actions", "ci", "mypy", "perf-gate", "build-gate"]
dependency_graph:
  requires: []
  provides: ["CI workflow with hardened gates"]
  affects: [".github/workflows/test.yml"]
tech_stack:
  added: []
  patterns: ["GitHub Actions matrix strategy", "uv build gate", "RPC count regression gate"]
key_files:
  created: []
  modified:
    - ".github/workflows/test.yml"
decisions:
  - "Python 3.14 added to matrix (all three versions blocking, fail-fast: false)"
  - "Mypy step hardened: --strict flag, odoo_fast_report_mapper/ only, no continue-on-error"
  - "perf and build jobs run in parallel (no needs: dependency) with the test job"
  - "Perf gate uses existing tests/test_benchmark_rpc.py — deterministic mock-based, RPC_CEILING=0"
metrics:
  duration: "~5 minutes"
  completed: "2026-06-12"
  tasks_completed: 2
  tasks_total: 2
  files_changed: 1
---

# Phase 04 Plan 02: CI Workflow Hardening Summary

GitHub Actions workflow extended with Python 3.14, blocking mypy --strict, and two new independent jobs (perf RPC gate + build artifact gate).

## Tasks Completed

| Task | Name | Commit | Files |
|------|------|--------|-------|
| 1 | Harden test job matrix and mypy step | 157d31b | .github/workflows/test.yml |
| 2 | Add perf and build jobs | d947f00 | .github/workflows/test.yml |

## Changes Made

### Task 1: Matrix + Mypy Hardening (157d31b)

**Matrix (D-07):** `python-version: ["3.12", "3.13"]` → `["3.12", "3.13", "3.14"]`

**Mypy step (D-08):**
- Before: `uv run mypy odoo_fast_report_mapper/ odoo_report_helper/` with `continue-on-error: true`
- After: `uv run mypy odoo_fast_report_mapper/ --strict` (blocking, correct path)

### Task 2: Perf and Build Jobs (d947f00)

**perf job (D-09):** Runs `uv run pytest tests/test_benchmark_rpc.py -v` — deterministic mock-based RPC count regression test with `RPC_CEILING = 0`. Blocks merge on failure. Uses `astral-sh/setup-uv@v6` with `enable-cache: true`.

**build job (D-10):** Runs `uv build` to produce sdist + wheel, then uploads `dist/` as artifact with `retention-days: 7`. Blocks merge on build failure.

Both jobs are independent (no `needs:` key) and run in parallel with the `test` job.

## Verification Results

All 6 plan verifications passed:
1. `3.14` present in matrix
2. No `continue-on-error` anywhere in file
3. No `odoo_report_helper/` anywhere in file
4. `test_benchmark_rpc.py` referenced in perf gate step
5. `uv build` step present in build job
6. YAML syntactically valid

## Deviations from Plan

None - plan executed exactly as written.

## Threat Surface Scan

No new network endpoints, auth paths, file access patterns, or schema changes. The CI workflow additions are consistent with the threat model in the plan:
- No `pull_request_target` triggers added
- No `${{ github.event.* }}` inputs in new job steps
- `dist/` artifact contains only wheel/sdist — no secrets

## Self-Check: PASSED

- `.github/workflows/test.yml` — FOUND and correct
- Commit `157d31b` — present in git log
- Commit `d947f00` — present in git log
