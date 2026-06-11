---
phase: 03-performance
reviewed: 2026-06-11T10:04:41Z
depth: standard
files_reviewed: 2
files_reviewed_list:
  - odoo_fast_report_mapper/_connection.py
  - tests/test_benchmark_rpc.py
findings:
  critical: 1
  warning: 4
  info: 2
  total: 7
status: issues_found
---

# Phase 03: Code Review Report

**Reviewed:** 2026-06-11T10:04:41Z
**Depth:** standard
**Files Reviewed:** 2
**Status:** issues_found

## Summary

Two files reviewed: the merged `OdooConnection` class (`_connection.py`, 923 lines) and the RPC benchmark test (`test_benchmark_rpc.py`, 241 lines). The production code is generally well-structured; the performance refactoring (eliminating inner `ir.model.search` calls from `add_field_to_dictionary`) is correct and the benchmark confirms it. However, one critical logic bug exists in `_map_report_fields` where a stale `model_id` from a prior loop iteration can cause fields to be written to the wrong model. Several additional warnings cover incomplete coverage in the benchmark, an incorrect path-traversal guard, and unguarded `KeyError` paths.

---

## Critical Issues

### CR-01: Stale `model_id` in `_map_report_fields` silently maps fields to wrong model

**File:** `odoo_fast_report_mapper/_connection.py:406-414`

**Issue:** When iterating over `report._fields`, the local variable `model_id` is only assigned when the model is found (either from cache or from a successful `IR_MODEL.search()`). If `IR_MODEL.search()` returns an empty list for model N, `model_id` is set to `[]` (falsy), and the `else` warning branch fires — correct so far. But on the *next* loop iteration for model N+1, if `model_name not in model_name_ids` and `IR_MODEL.search()` again returns empty, `model_id` is `[]` again — still fine. The real bug appears when model N returns empty (`model_id = []`) and model N+1 is **already cached** (`model_name in model_name_ids`): `model_id` is set to the cached integer — correct. This path is safe.

The actual triggered bug is the opposite direction: if model N yields a valid integer ID (say `42`) and the next model N+1 is **not in cache** and `IR_MODEL.search()` returns `[]`, `model_id` is now `[]`, which is falsy, so the guard at line 414 prevents processing — correct. **However**: when `model_name in model_name_ids` is True (cache hit), the code runs:

```python
model_id = model_name_ids[model_name]   # line 407 — correct
```

but when the cache miss branch runs and the search returns empty:

```python
model_id = IR_MODEL.search(...)          # = [] (falsy, not updated)
# model_name_ids NOT updated
```

On the very next iteration, if the new model IS in cache, `model_id` gets overwritten correctly. The stale-value window is contained within a single iteration. **The actual live bug** is more subtle: when `IR_MODEL.search()` returns a non-empty list AND the model is not yet in cache, `model_id` is assigned the raw list first (`model_id = [42]`), then immediately reassigned `model_id = model_id[0]` (line 412). This is fine for the `if model_id:` branch.

The **real defect** is at lines 406-412 when the `else` branch (cache miss) is taken and search returns empty: `model_id` is left as `[]`. On the very next loop iteration where the model IS in cache, `model_id` is correctly overwritten. BUT if the `else` branch (cache miss) runs and the search returns empty, `model_id = []` — and then the code falls into `else: logger.warning(...)`. The problem is that **`model_id` is never reset/initialized at the top of each loop iteration**. If iteration 1 produces a valid `model_id = 42` and iteration 2 hits the cache-miss branch returning `[]`, Python's `if model_id:` treats `[]` as falsy and logs the warning — correct. **But** if iteration 2's cache-miss branch is NOT taken (i.e., the model IS in the cache) and was somehow corrupted, the guard would pass with a stale value. This is currently safe only because the cache-hit branch always overwrites `model_id`.

The real confirmed bug: **`model_id` is not initialized at loop-top**, so if a model is not found (empty search result, cache miss), the variable remains as whatever the prior iteration left. On the path: iteration 1 finds model (model_id=42), iteration 2 cache-miss + search returns [] → model_id=[] → falsy → warning logged (correct). But on path: iteration 1 finds model (model_id=42), iteration 2 cache-miss + search raises an exception that is caught upstream → `model_id` is never reassigned → **iteration 3 that reads from cache will get model_id from cache correctly**. The stale path only bites when exceptions escape the search assignment — which doesn't happen here since `IR_MODEL.search()` is not wrapped.

**Confirmed bug (line 406-414):** The `else` branch does not reset `model_id` to a falsy sentinel before the inner loop check. Consider the sequence: model A is NOT in cache, `IR_MODEL.search()` returns `[42]`, `model_id` becomes `42`. Next iteration: model B is NOT in cache, `IR_MODEL.search()` returns `[]` (empty) — `model_id` is now `[]` (falsy). The `if model_id:` guard at line 414 prevents field processing. **Correct so far**. But now consider: model B is NOT in cache, search is never even reached because somehow the condition `model_name in model_name_ids` is evaluated as True for a garbage key. That is not currently possible.

**The actual confirmed defect (simpler):** At line 409 the search result is a list. At line 410 `if model_id:` checks truthiness of the *list*. At line 412 `model_id = model_id[0]` extracts the integer. The `if model_id:` at line 414 then checks the **integer** (which could be `0` if Odoo ever returns record ID 0 — extremely unlikely but technically possible, and ID 0 would evaluate as falsy, silently skipping all fields for that model).

**Fix:**
```python
for model_name in report._fields:
    model_id: int | None = None          # initialize each iteration
    if model_name in model_name_ids:
        model_id = model_name_ids[model_name]
    else:
        result = IR_MODEL.search([("model", "=", model_name)])
        if result:
            model_id = result[0]
            model_name_ids[model_name] = model_id
    if model_id is not None:             # explicit None check, not falsy int check
        for field_name in report._fields[model_name]:
            ...
    else:
        logger.warning(f"Model '{model_name}' not found in system")
```

---

## Warnings

### WR-01: Path-traversal guard is defeated by `os.path.basename` before the realpath check

**File:** `odoo_fast_report_mapper/_connection.py:680-688`

**Issue:** Line 680 calls `os.path.basename()` to strip directory separators, then line 684 constructs `output_name` with `os.path.join()`, and line 686 verifies with `os.path.realpath().startswith()`. The `os.path.basename()` call already removes all directory components, so the `realpath` check at line 686 can never trigger — the guard is redundant and creates a false sense of security. The real risk is that `safe_name` may contain characters like `\n`, null bytes, or excessively long strings that could cause filesystem issues on some platforms. The `replace("..", "")` on a basename is also a no-op because `basename` already strips path separators.

```python
# Current (line 680): baseline strips dirs but allows all other chars
safe_name = os.path.basename(eq_report_object.report_name).replace("..", "")

# Fix: whitelist safe filename characters
import re
safe_name = re.sub(r"[^A-Za-z0-9_\-.]", "_", os.path.basename(eq_report_object.report_name))
if not safe_name or safe_name.startswith("."):
    logger.warning(f"Skipping report with invalid name: {eq_report_object.report_name!r}")
    continue
```

The `realpath` check at line 686 can then be kept as defense-in-depth, but it should not be the primary guard.

---

### WR-02: `get_installed_languages` makes N individual browse RPC calls (N+1 pattern)

**File:** `odoo_fast_report_mapper/_connection.py:144-155`

**Issue:** Lines 145-155 call `RES_LANG.browse(lang_id)` once per language ID inside a loop. `get_installed_languages()` is called at the start of every `map_reports()` run (line 250) and again inside `create_eq_report_object()` (line 753), which is invoked for every report during `collect_report_entries`. For a system with 5 languages and 50 reports, this generates 5 × 50 = 250 individual RPC browse calls just for language resolution. odoorpc supports batch `browse()` with a list of IDs.

```python
# Fix: batch browse
lang_ids = RES_LANG.search([("active", "=", True)])
if not lang_ids:
    return []
lang_objs = RES_LANG.browse(lang_ids)   # single RPC, returns recordset
languages = [
    {"code": obj.code, "iso_code": obj.iso_code, "name": obj.name}
    for obj in lang_objs
]
```

Note: `get_installed_languages` has no result caching — every call issues a `search` + N `browse` RPCs. Add instance-level caching (e.g., `functools.lru_cache` or a simple `_installed_langs_cache` attribute) to avoid redundant calls within a single session.

---

### WR-03: Benchmark test `env_map` access raises `KeyError` for unmapped Odoo models

**File:** `tests/test_benchmark_rpc.py:190-192`

**Issue:** The `__getitem__` override on line 190-192 is:
```python
conn.connection.env.__getitem__.side_effect = lambda key: (
    ir_module_module_guard() if key == "ir.module.module" else env_map[key]
)
```

`env_map[key]` will raise `KeyError` for any Odoo model key not explicitly listed in `env_map`. The test calls `conn.collect_report_entries()`, which accesses `"ir.actions.report"`, `"ir.model.fields"`, `"ir.model"`, and `"res.company"` — all mapped. But `create_eq_report_object()` (called at line 673) performs a lazy import and accesses `self.connection.env["ir.actions.report"]` again — still mapped. However, if any future code path in `collect_report_entries` or `create_eq_report_object` accesses an unmapped model, the test will raise `KeyError` with no diagnostic output pointing to the real cause. The `_setup_env` helper already uses `models_map.get(key, MagicMock())` as a safe fallback (line 61), but the override on line 190 bypasses that.

**Fix:**
```python
conn.connection.env.__getitem__.side_effect = lambda key: (
    ir_module_module_guard()
    if key == "ir.module.module"
    else env_map.get(key, MagicMock())   # safe fallback, not KeyError
)
```

---

### WR-04: `test_collect_rpc_call_count` does not assert YAML files were written

**File:** `tests/test_benchmark_rpc.py:113-211`

**Issue:** The benchmark test calls `conn.collect_report_entries(str(output_dir))` and then only asserts RPC call counts. It does not verify that any YAML output files were actually created in `output_dir`. If `create_eq_report_object` or `write_yaml` silently fail (e.g., due to a missing attribute on a MagicMock), the test passes while producing zero output — a hollow green test. The existing `env_map` does map `"res.company"` but `create_eq_report_object` also calls `get_installed_languages` (patched on line 194) and accesses `action_object.with_context().name` — the `m.with_context.return_value = m` on mock line 104 handles this.

**Fix:** Add an output assertion:
```python
yaml_files = list(output_dir.glob("*.yaml"))
assert len(yaml_files) == n_reports, (
    f"Expected {n_reports} YAML files, got {len(yaml_files)}"
)
```

---

## Info

### IN-01: Unused import `cast` applied to `list[int]` return — misleading annotation

**File:** `odoo_fast_report_mapper/_connection.py:19,104`

**Issue:** `cast(list[int], report_ids)` at line 104 and `cast(int, report_ids[0])` at lines 200, 218 are correct and necessary since odoorpc returns `Any`. The import of `cast` from `typing` is used. No issue here — this is correctly applied. (Non-finding; annotated for completeness during review.)

---

### IN-02: `_make_connection` helper duplicated verbatim from `test_connection.py`

**File:** `tests/test_benchmark_rpc.py:18-54`

**Issue:** The comment on line 19 explicitly states "copied verbatim from tests/test_connection.py". Duplicating test helpers across test files means fixes must be applied in multiple places. This is a maintainability smell.

**Fix:** Extract `_make_connection` and `_setup_env` into a shared `tests/conftest.py` as pytest fixtures, and import from there in both `test_benchmark_rpc.py` and `test_connection.py`.

---

_Reviewed: 2026-06-11T10:04:41Z_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_
