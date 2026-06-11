---
phase: 03-performance
plan: "01"
subsystem: tests
tags: [benchmark, rpc, perf, tdd, wave1]
dependency_graph:
  requires: []
  provides:
    - tests/test_benchmark_rpc.py — Mock-Counter benchmark infrastructure with BEFORE-state baseline
  affects:
    - tests/ (349 tests pass, +2 new)
tech_stack:
  added: []
  patterns:
    - Mock-Counter via MagicMock.call_count on ir.model and ir.model.fields proxies
    - _build_field_mock / _build_report_mock helpers for 10×50 batch mock setup
    - ir.module.module AssertionError guard in env_map
key_files:
  created:
    - tests/test_benchmark_rpc.py
  modified: []
decisions:
  - "RPC_CEILING set to -1 sentinel (not yet established); Wave 2 (03-02) sets the measured after-fix value"
  - "test_rpc_baseline_call_count prints BASELINE counts without asserting — measurement only"
  - "test_add_field_to_dictionary_calls_ir_model_search_currently documents BEFORE state with hard assertions (call_count == 1 each)"
  - "ir.module.module guarded with AssertionError side_effect to catch accidental access during collect"
metrics:
  duration: "~5 minutes"
  completed: "2026-06-11"
  tasks: 1
  files: 1
---

# Phase 03 Plan 01: RPC Benchmark Infrastructure (Wave 1) Summary

**One-liner:** Mock-Counter benchmark for `collect_report_entries` measuring 500 extra RPC calls (IR_MODEL.search × 500 + IR_FIELDS.search × 500) as BEFORE-state baseline for PERF-01/PERF-04.

## What Was Built

`tests/test_benchmark_rpc.py` (242 lines) provides the benchmark infrastructure and baseline measurement for Phase 3 (PERF-01, PERF-03, PERF-04):

### Test 1: `test_rpc_baseline_call_count`

- Runs `collect_report_entries` with 10 report mocks × 50 field mocks (500 total fields)
- Uses `_build_report_mock` and `_build_field_mock` helpers to construct the full mock fixture
- Guards `ir.module.module` with `AssertionError` side-effect to catch accidental access
- **Prints BASELINE counts, no assertion on call counts** (measurement only)
- **Measured BEFORE state:**
  - `ir.model.search calls: 500` (1 per field — pure redundancy)
  - `ir.model.fields.search total calls: 501` (1 outer + 500 inner dependency searches)

### Test 2: `test_add_field_to_dictionary_calls_ir_model_search_currently`

- Direct call to `add_field_to_dictionary` for a single field
- **Asserts** `mock_ir_model.search.call_count == 1` and `mock_ir_fields.search.call_count == 1`
- Explicitly documents the pre-fix BEFORE behavior
- Will be deleted in plan 03-02 once the fix eliminates these calls

### `RPC_CEILING: int = -1`

Sentinel constant placed after imports. Comment explains it will be updated in Wave 2 (plan 03-02) after the fix is applied and the after-fix count is measured.

## Baseline Measurement Results

| Metric | Count | Notes |
|--------|-------|-------|
| `ir.model.search` calls (BEFORE) | 500 | 1 per field inside `add_field_to_dictionary` |
| `ir.model.fields.search` calls (BEFORE) | 501 | 1 outer (legitimate) + 500 inner (redundant) |
| Total extra RPC calls (500 fields) | 1000 | Both inner searches per field = 2 × 500 |
| Expected after fix | 0 extra | IR_MODEL.search + inner IR_FIELDS.search removed |

## Verification Results

```
uv run pytest tests/test_benchmark_rpc.py -v    → 2 passed
uv run pytest tests/ -q -m "not integration"    → 349 passed (347 existing + 2 new)
uv run mypy odoo_fast_report_mapper/            → Success: no issues found in 12 source files
grep RPC_CEILING tests/test_benchmark_rpc.py    → 15: RPC_CEILING: int = -1
```

## Commits

| Task | Commit | Description |
|------|--------|-------------|
| Task 1 | `e092280` | test(03-01): add RPC call-count benchmark infrastructure |

## Deviations from Plan

None — plan executed exactly as written.

## Known Stubs

`RPC_CEILING: int = -1` is an intentional sentinel (not a stub). Plan 03-02 sets the real measured value after the fix. This is by design per PERF-04.

## Threat Flags

None. Test-only file, no new production attack surface.

## Self-Check: PASSED

- [x] `tests/test_benchmark_rpc.py` exists: FOUND
- [x] Commit `e092280` exists in git log
- [x] Both tests pass: 2 passed
- [x] Full suite green: 349 passed
- [x] mypy 0 errors
- [x] `RPC_CEILING: int = -1` present in file
