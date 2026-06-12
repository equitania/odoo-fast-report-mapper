---
phase: 02-type-safety
reviewed: 2026-06-11T09:00:38Z
depth: standard
files_reviewed: 12
files_reviewed_list:
  - odoo_fast_report_mapper/__init__.py
  - odoo_fast_report_mapper/__version__.py
  - odoo_fast_report_mapper/_cli.py
  - odoo_fast_report_mapper/_connection.py
  - odoo_fast_report_mapper/_exceptions.py
  - odoo_fast_report_mapper/_lang_utils.py
  - odoo_fast_report_mapper/_logging.py
  - odoo_fast_report_mapper/_odoo_types.py
  - odoo_fast_report_mapper/_progress.py
  - odoo_fast_report_mapper/_report.py
  - odoo_fast_report_mapper/_utils.py
  - odoo_fast_report_mapper/_yaml_dumper.py
findings:
  critical: 2
  warning: 3
  info: 2
  total: 7
status: issues_found
---

# Phase 02: Code Review Report

**Reviewed:** 2026-06-11T09:00:38Z
**Depth:** standard
**Files Reviewed:** 12
**Status:** issues_found

## Summary

Phase 02 added `from __future__ import annotations`, TypedDicts in `_odoo_types.py`, and `cast()` calls at odoorpc RPC boundaries throughout the package. The annotation work is generally sound, but the refactor introduced one clear behavioral regression in `test_fast_report_rendering` — the `company_id` argument was dropped from the `_search_report` call on the v17+ code path, causing company-filtered searches to silently widen to all-company scope during test runs. A second critical gap is in `_odoo_types.py`: the `LanguageRecord` TypedDict is structurally wrong relative to the actual dicts produced by `get_installed_languages()`, meaning any code that annotates against it will silently mistype the `iso_code` field. Three warnings cover a dead-code `if report_object:` guard, a noisy redundant env-variable guard, and a non-deterministic dependency ordering side-effect. Two info items address the misspelled public alias in `__all__` and a stale docstring example path.

---

## Critical Issues

### CR-01: Missing `company_id` in `_search_report` call inside `test_fast_report_rendering` (v17+ branch)

**File:** `odoo_fast_report_mapper/_connection.py:871`

**Issue:** In `test_fast_report_rendering`, when `report.company_id` is set and `self.version` is NOT in `["13","14","15","16"]` (i.e., Odoo 17+), the code calls `_search_report` without the `company_id` keyword argument:

```python
# line 870-871 — ACTUAL (broken)
else:
    report_id = self._search_report(report.model_name, report.entry_name, IR_ACTIONS_REPORT)
```

The equivalent block in `_create_or_update_report` (the mapping path) correctly passes `company_id`:

```python
# lines 327-329 — REFERENCE (correct)
else:
    report_id = self._search_report(
        report.model_name, report.entry_name, IR_ACTIONS_REPORT, company_id=report.company_id[0]
    )
```

Without `company_id`, `_search_report` omits the company filter from the domain (line 213-214), so it will match the first report with that name across all companies rather than the company-scoped one. In a multi-company Odoo instance this can cause workflow 1 and workflow 2 to render the wrong company's report, or silently succeed when the correct scoped report is absent.

This is the most likely annotation-driven regression: the type-safety refactor restructured these branches, and the `company_id` argument was lost in the v17+ else-branch.

**Fix:**
```python
# line 870-871 — FIXED
else:
    report_id = self._search_report(
        report.model_name,
        report.entry_name,
        IR_ACTIONS_REPORT,
        company_id=report.company_id[0],
    )
```

---

### CR-02: `LanguageRecord` TypedDict is structurally incomplete — `iso_code` field missing

**File:** `odoo_fast_report_mapper/_odoo_types.py:38-44`

**Issue:** `LanguageRecord` declares only `code` and `name`:

```python
class LanguageRecord(TypedDict, total=True):
    code: str
    name: str
```

But `get_installed_languages()` in `_connection.py:148-154` constructs dicts with a third field:

```python
languages.append({
    "code": lang_obj.code,
    "iso_code": lang_obj.iso_code,   # <-- not in TypedDict
    "name": lang_obj.name,
})
```

Under `--strict` mypy, any code that annotates `lang: LanguageRecord` and accesses `lang["iso_code"]` will produce a `TypedDict key "iso_code" not found` error. The TypedDict was the primary deliverable of this phase; shipping it with a structural mismatch defeats its purpose and will cause incorrect mypy reports — flagging real accesses as errors, or silently hiding missing-key bugs if a consumer uses `TypedDict.get("iso_code")`.

**Fix:**
```python
class LanguageRecord(TypedDict, total=True):
    code: str
    iso_code: str
    name: str
```

---

## Warnings

### WR-01: Dead `if report_object:` guard — always truthy after `browse()`

**File:** `odoo_fast_report_mapper/_connection.py:890`

**Issue:** `IR_ACTIONS_REPORT.browse(report_id)` (line 879) returns an odoorpc proxy object, which is always truthy. The `if report_object:` check at line 890 can never be `False` — the real guard (`if not report_id: continue`) already ran at line 876. All code inside the `if report_object:` block is always executed; the indentation is misleading and the guard is dead. If the intent was to protect against a "not found" proxy, `browse()` does not return `None` or `False` in odoorpc — it returns an empty recordset-style proxy.

This is a pre-existing pattern that survived the refactor. The `if report_object:` check is harmless at runtime but it misleads readers into thinking there is a legitimate "None" path, and it adds an unnecessary level of indentation for the entire body of the rendering logic.

**Fix:** Remove the dead guard and de-dent its body:

```python
# Remove lines 890 and the matching dedent at the end of the try block
report_model_records_ids = IR_REPORT_MODEL.search([])
try:
    if not len(report_model_records_ids):
        ...
```

---

### WR-02: Double-guard on `ODOO_PORT` — redundant `None` check after `missing_vars` already raised

**File:** `odoo_fast_report_mapper/_utils.py:478-480`

**Issue:**

```python
# line 450-455 — already raises if ODOO_PORT is missing/empty
missing_vars = [var for var in required_vars if not os.getenv(var)]
if missing_vars:
    raise ValueError(...)

# line 478-480 — can never be None here
port_str = os.getenv("ODOO_PORT")
if port_str is None:
    raise ValueError("ODOO_PORT environment variable not set")
```

`ODOO_PORT` is in `required_vars`, so `missing_vars` check at line 450-455 already raises `ValueError` if it is absent or empty. The `if port_str is None` check at line 480 is dead code. Worse, the redundant check raises a *different* error message (`"ODOO_PORT environment variable not set"`) than the structured `missing_vars` path, which would confuse error handling in `_cli.py` where the caller inspects `"Missing required environment variables"` in the message to branch user guidance.

**Fix:** Remove the redundant guard:
```python
port_str = os.getenv("ODOO_PORT", "")   # guaranteed non-None by missing_vars check above
try:
    port = int(port_str)
    ...
```

---

### WR-03: `add_dependencies` produces non-deterministic ordering

**File:** `odoo_fast_report_mapper/_report.py:154-157`

**Issue:**

```python
existing: list[str] = self._dependencies if isinstance(self._dependencies, list) else []
self._dependencies = existing + dependency_list
self._dependencies = list(set(self._dependencies))  # <-- arbitrary order
```

`list(set(...))` produces a non-deterministic iteration order (hash-randomized in CPython). Each run with the same input may produce a different dependency list order, causing non-reproducible YAML output between runs. For testing/diffing YAML files this is a friction point, and it differs from the analogous deduplication in `add_field_to_dictionary` at `_connection.py:727-728` which also uses `list(set(...))` (same issue there). The `collect_all_report_entries` path explicitly sorts dependencies via `sorted(...)` at `_connection.py:794`, highlighting the inconsistency.

**Fix:** Use `sorted()` for deterministic ordering, consistent with line 794:
```python
self._dependencies = sorted(set(existing + dependency_list))
```

---

## Info

### IN-01: Misspelled alias `PathDoesNotExitError` exported in `__all__`

**File:** `odoo_fast_report_mapper/__init__.py:25`

**Issue:** `PathDoesNotExitError` (misspelling of "Exit" vs "Exist") is exported in `__all__` alongside the correctly-spelled `PathDoesNotExistError`. The alias is intentional for backward compatibility (documented in `_exceptions.py:16`), but advertising it in `__all__` makes the typo part of the permanent public API. New consumers will discover the misspelling via tab-completion or `dir()` and may adopt it, growing the compatibility burden.

**Fix:** Keep the alias in `_exceptions.py` for backward compatibility, but remove it from `__all__` so it is not a first-class advertised export:
```python
# __init__.py __all__ — remove line:
"PathDoesNotExitError",
```
If the alias must be importable (`from odoo_fast_report_mapper import PathDoesNotExitError`), it will still work even without being in `__all__`; only `from odoo_fast_report_mapper import *` would no longer include it.

---

### IN-02: `_logging.py` docstring example uses stale import path

**File:** `odoo_fast_report_mapper/_logging.py:234-236`

**Issue:** The docstring for `get_logger` shows:
```python
>>> from odoo_fast_report_mapper.logging_config import get_logger
```
The module is now `_logging.py`, not `logging_config.py`. The example import will raise `ModuleNotFoundError` if a user copies it literally.

**Fix:**
```python
>>> from odoo_fast_report_mapper._logging import get_logger
```
Or, since `get_logger` is re-exported via `__init__.py`:
```python
>>> from odoo_fast_report_mapper import OdooConnection  # use public API
```

---

_Reviewed: 2026-06-11T09:00:38Z_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_

## Fixes Applied

**Fixed at:** 2026-06-11T09:30:00Z
**Fixed by:** Claude (gsd-code-fixer)

| Finding | Status | Commit | Notes |
|---------|--------|--------|-------|
| CR-01 | fixed | 0bbc73e | Passed `company_id=report.company_id[0]` in `test_fast_report_rendering` v17+ branch |
| CR-02 | fixed | 5d166c6 | Added `iso_code: str` field to `LanguageRecord` TypedDict |
| WR-01 | fixed | f2b574b | Removed dead `if report_object:` guard and dedented body |
| WR-02 | fixed | 22194ff | Removed redundant `if port_str is None` check after `missing_vars` guard |
| WR-03 | fixed | ad90c81 | Replaced `list(set(...))` with `sorted(set(...))` in `add_dependencies` |
| IN-01 | skipped | — | Out of scope (Info) |
| IN-02 | skipped | — | Out of scope (Info) |

**Post-fix verification:**
- mypy: `Success: no issues found in 12 source files`
- pytest: `347 passed in 0.95s`
