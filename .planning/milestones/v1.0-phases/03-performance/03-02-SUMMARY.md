---
phase: 03-performance
plan: "02"
subsystem: connection
tags: [performance, rpc, benchmark, perf, tdd, wave2, fix]
dependency_graph:
  requires:
    - 03-01 — RPC benchmark infrastructure and BEFORE-state baseline
  provides:
    - odoo_fast_report_mapper/_connection.py — add_field_to_dictionary with modules param, zero self.connection access
    - tests/test_benchmark_rpc.py — asserting regression test with RPC_CEILING=0
  affects:
    - tests/ (349 tests pass, same count — 2 existing benchmark tests replaced with 2 new asserting tests)
tech_stack:
  added: []
  patterns:
    - Pre-fetch + pass-through: resolve field_object.modules in outer loop, pass as parameter
    - Mock-Counter assertion: MagicMock.call_count == 0 to enforce zero inner RPC calls
    - modules or "" guard (BUG-08/BUG-09 pattern): handles False modules attribute from computed fields
key_files:
  created: []
  modified:
    - odoo_fast_report_mapper/_connection.py
    - tests/test_benchmark_rpc.py
decisions:
  - "add_field_to_dictionary remains an instance method (not @staticmethod) in Phase 3 — pure minimal diff"
  - "modules: list[str] | None = None as optional parameter preserves backward compat for all existing tests"
  - "RPC_CEILING = 0 documents the after-fix inner search count (outer legitimate searches excluded)"
  - "test_add_field_to_dictionary_calls_ir_model_search_currently deleted — pre-fix BEFORE-state doc-test no longer valid"
metrics:
  duration: "~10 minutes"
  completed: "2026-06-11"
  tasks: 2
  files: 2
---

# Phase 03 Plan 02: RPC Fix — Eliminate 2 Extra Calls Per Field (Wave 2) Summary

**One-liner:** Moved dependency resolution from `add_field_to_dictionary` (2 extra RPC calls per field) into the `collect_report_entries` outer loop using `field_object.modules` — eliminating 1000 redundant RPC calls in a 10×50 run, locked by asserting regression test with `RPC_CEILING = 0`.

## What Was Built

### Task 1: Fix `_connection.py`

**`collect_report_entries` outer loop** (lines 636–669):
- After `field_name = field_object.name`, two lines inserted to extract modules from the already-browsed field object:
  ```python
  raw_modules = field_object.modules or ""
  modules = [m for m in raw_modules.replace(" ", "").split(",") if m]
  ```
- The `add_field_to_dictionary` call-site gains `modules` as the sixth positional argument.

**`add_field_to_dictionary` method** (lines 688–720):
- New optional sixth parameter: `modules: list[str] | None = None` with inline comment documenting its source.
- Entire "Collect dependencies" block deleted: `IR_FIELDS`, `IR_MODEL`, `model_id`, `field_id`, `field_obj` assignments and all conditional logic using `self.connection` — 18 lines removed.
- Replaced with pure dict-mutation logic: `modules_dependencies = modules or []`, then dedup via `set()` same as before.
- Method now has zero `self.connection` access.

### Task 2: Update `tests/test_benchmark_rpc.py`

- `RPC_CEILING: int = -1` (sentinel) replaced with `RPC_CEILING: int = 0` (measured after-fix value).
- `test_rpc_baseline_call_count` renamed to `test_collect_rpc_call_count`: two `print()` lines replaced with assertions:
  - `assert mock_ir_model.search.call_count == RPC_CEILING` (== 0)
  - `assert mock_ir_model_fields.search.call_count == 1` (outer field ID search only)
- `test_add_field_to_dictionary_calls_ir_model_search_currently` deleted (BEFORE-state documentation, now fails after fix).
- New `test_add_field_to_dictionary_zero_rpc_calls`: direct call with `modules=["sale", "account"]` parameter, asserts result dict contains correct dependencies and both mock search call counts are 0.

## Performance Impact

| Metric | BEFORE (Wave 1 baseline) | AFTER (this plan) | Delta |
|--------|--------------------------|-------------------|-------|
| `ir.model.search` calls (10×50 run) | 500 | 0 | -500 |
| `ir.model.fields.search` inner calls (10×50 run) | 500 | 0 | -500 |
| `ir.model.fields.search` outer call | 1 | 1 | 0 |
| Total extra RPC calls per 500-field run | 1000 | 0 | **-1000** |
| RPC calls per field (inner) | 2 | 0 | -2 |

## Verification Results

```
uv run pytest tests/test_benchmark_rpc.py -v      → 2 passed
uv run pytest tests/ -q -m "not integration"      → 349 passed
uv run mypy odoo_fast_report_mapper/               → Success: no issues found in 12 source files
grep RPC_CEILING tests/test_benchmark_rpc.py       → 16: RPC_CEILING: int = 0
grep "self.connection" _connection.py (add_field)  → None found (PASS)
grep "modules.*list\[str\]" _connection.py         → 698: modules: list[str] | None = None
```

## Commits

| Task | Commit | Description |
|------|--------|-------------|
| Task 1 | `5b08b33` | feat(03-02): add modules param to add_field_to_dictionary, eliminate 2 RPC calls per field |
| Task 2 | `1876ba0` | test(03-02): update benchmark — RPC_CEILING=0, asserting regression test replaces doc-test |

## Deviations from Plan

None — plan executed exactly as written.

## Known Stubs

None. All functionality is fully implemented and wired. `RPC_CEILING = 0` is the correct measured after-fix value, not a placeholder.

## Threat Flags

None. This is a pure internal refactor — no new user-facing inputs, no authentication changes, no new file I/O, no new endpoints. The `modules` data was already flowing through the code via a different path (2 extra RPC calls); the fix moves the data source from a redundant re-query to the already-browsed `field_object`.

## Self-Check: PASSED

- [x] `odoo_fast_report_mapper/_connection.py` modified: FOUND
- [x] `tests/test_benchmark_rpc.py` modified: FOUND
- [x] Commit `5b08b33` exists: CONFIRMED (git log)
- [x] Commit `1876ba0` exists: CONFIRMED (git log)
- [x] `add_field_to_dictionary` signature contains `modules: list[str] | None = None`: CONFIRMED (line 698)
- [x] No `self.connection` inside `add_field_to_dictionary` body: CONFIRMED
- [x] `field_object.modules or ""` in `collect_report_entries` loop: CONFIRMED (line 637)
- [x] `RPC_CEILING: int = 0` in test file: CONFIRMED (line 16)
- [x] `test_collect_rpc_call_count` asserts `call_count == 0`: CONFIRMED (line 204)
- [x] `test_add_field_to_dictionary_zero_rpc_calls` passes: CONFIRMED (2 passed)
- [x] `test_add_field_to_dictionary_calls_ir_model_search_currently` absent: CONFIRMED (deleted)
- [x] All 349 tests pass: CONFIRMED
- [x] mypy 0 errors: CONFIRMED
