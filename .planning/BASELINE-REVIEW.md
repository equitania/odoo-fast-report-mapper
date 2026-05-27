---
phase: baseline
reviewed: 2026-05-27T00:00:00Z
depth: deep
files_reviewed: 14
files_reviewed_list:
  - odoo_fast_report_mapper/__init__.py
  - odoo_fast_report_mapper/__version__.py
  - odoo_fast_report_mapper/eq_odoo_connection.py
  - odoo_fast_report_mapper/eq_report.py
  - odoo_fast_report_mapper/eq_utils.py
  - odoo_fast_report_mapper/lang_utils.py
  - odoo_fast_report_mapper/logging_config.py
  - odoo_fast_report_mapper/odoo_fast_report_mapper.py
  - odoo_fast_report_mapper/progress.py
  - odoo_report_helper/__init__.py
  - odoo_report_helper/exceptions.py
  - odoo_report_helper/odoo_connection.py
  - odoo_report_helper/report.py
  - odoo_report_helper/utils.py
findings:
  critical: 4
  warning: 7
  info: 6
  total: 17
status: issues_found
---

# Baseline Code Review — odoo-fast-report-mapper v0.9.7.3

**Reviewed:** 2026-05-27
**Depth:** deep (cross-file import graph, call-chain tracing, type consistency)
**Files Reviewed:** 14
**Status:** issues_found

## Summary

Full deep review of the production codebase ahead of the v1.0 cleanup milestone. All 14 source files in both packages were read and cross-referenced.

The most severe issue is a **confirmed, reproducible circular import** between `odoo_report_helper` and `odoo_fast_report_mapper` that causes `ImportError` whenever the helper package is imported standalone (e.g., in tests that only import `odoo_report_helper`). This is the "known circular import" the cleanup milestone targets.

Three additional blockers were found beyond the circular import: an unguarded `list[0]` access that raises `IndexError` when Odoo returns no model match; a silent data-corruption bug in `self_clean()` that destroys calculated-field parameter lists; and a Liskov Substitution Principle violation where the subclass overrides `check_dependencies` with a different return type, silently breaking the base-class logic if ever reached.

The quality debt is consistent with a codebase grown incrementally: near-zero type annotations outside a handful of functions, fragmented logging (one file per module name instead of a unified log), and a `progress.py` module exposing three dead-code classes (`ProgressBar`, `ReportProgress`, `create_progress_bar`) that are only exercised in tests and never referenced in production code.

---

## Critical Issues

### CR-01: Circular import — confirmed `ImportError` when `odoo_report_helper` imported standalone

**File:** `odoo_report_helper/odoo_connection.py:9`

**Issue:** `odoo_report_helper/odoo_connection.py` imports `build_name_search_domain` from `odoo_fast_report_mapper.lang_utils`. Importing `odoo_fast_report_mapper` triggers its `__init__.py`, which imports `eq_odoo_connection`, which imports `OdooConnection` from the still-initializing `odoo_report_helper.odoo_connection`. Python detects the partial module and raises:

```
ImportError: cannot import name 'OdooConnection' from partially initialized module
'odoo_report_helper.odoo_connection' (most likely due to a circular import)
```

This was verified by direct runtime test. The circular path is:

```
odoo_report_helper/__init__.py
  -> odoo_report_helper/odoo_connection.py:9
       -> odoo_fast_report_mapper.lang_utils  (triggers __init__)
  -> odoo_fast_report_mapper/__init__.py:1
       -> eq_odoo_connection.py:11
            -> odoo_report_helper.odoo_connection.OdooConnection  (CYCLE)
```

The only reason `import odoo_fast_report_mapper` does not crash is import-order luck: `odoo_fast_report_mapper` is loaded first and `odoo_report_helper` finishes initializing before being re-entered. Any test or script that imports `odoo_report_helper` first will fail.

**Fix:** Move `build_name_search_domain` (and all other `lang_utils` symbols needed by `odoo_report_helper/odoo_connection.py`) into a module that does not import either package, or inline the domain-building logic directly in `OdooConnection._search_report`. The v1.0 plan to dissolve `odoo_report_helper` into `odoo_fast_report_mapper` will eliminate this by removing the cross-package dependency entirely.

```python
# Immediate workaround if full merge is not yet done:
# In odoo_report_helper/odoo_connection.py, replace the top-level import:
# from odoo_fast_report_mapper.lang_utils import build_name_search_domain

# With a local inline (no cross-package dependency):
def _build_name_search_domain(report_name):
    """Local copy — remove when odoo_report_helper is dissolved into odoo_fast_report_mapper."""
    if isinstance(report_name, dict):
        all_variants = []
        for name in report_name.values():
            all_variants.append(("name", "=ilike", name))
            all_variants.append(("name", "=ilike", name + " (PDF)"))
        if len(all_variants) <= 1:
            return all_variants
        return ["|"] * (len(all_variants) - 1) + all_variants
    return [("name", "=ilike", report_name), ("name", "=ilike", report_name + " (PDF)")]
```

---

### CR-02: IndexError — unguarded `model_id[0]` in `add_field_to_dictionary`

**File:** `odoo_fast_report_mapper/eq_odoo_connection.py:600-601`

**Issue:** `IR_MODEL.search(...)` can return an empty list when the model is not found in Odoo. Line 601 immediately accesses `model_id[0]` without checking:

```python
model_id = IR_MODEL.search([("model", "=", model_name)])         # line 600 — may return []
field_id = IR_FIELDS.search([("model_id", "=", model_id[0]), ...])  # line 601 — IndexError!
```

The `IndexError` propagates out of `add_field_to_dictionary`, aborting the caller loop in `collect_report_entries` mid-iteration, leaving `data_dictionary` in a partial state. No collected entries are written to disk for subsequent reports.

**Fix:**
```python
model_id = IR_MODEL.search([("model", "=", model_name)])
if not model_id:
    logger.warning(f"Model '{model_name}' not found — skipping dependency collection")
    return data_dictionary
field_id = IR_FIELDS.search([("model_id", "=", model_id[0]), ("name", "=", field_name)])
```

---

### CR-03: Data corruption — `self_clean()` destroys calculated-field parameter lists

**File:** `odoo_report_helper/report.py:79` (also `report.py:65`)

**Issue:** `self_clean()` in `odoo_report_helper/utils.py` calls `list(dict.fromkeys(value))` for every dict value. For `_fields` (values are lists) this correctly deduplicates. For `_calculated_fields` the values are dicts:

```python
{"eq_get_payment_terms": ["partner_id.lang", "currency_id"]}
```

`dict.fromkeys({"eq_get_payment_terms": [...]})` iterates over the **keys** of the inner dict, producing `["eq_get_payment_terms"]`. The parameter list `["partner_id.lang", "currency_id"]` is silently dropped.

After `add_calculated_fields()` returns, `_calculated_fields` is:
```python
{"payment_text": ["eq_get_payment_terms"]}  # ← WRONG, was {"eq_get_payment_terms": ["p1","p2"]}
```

Subsequent `set_calculated_fields()` calls iterate `content.items()` on a list, raising `AttributeError: 'list' object has no attribute 'items'`.

**Fix:** Do not call `self_clean()` on `_calculated_fields`. Deduplicate only the top-level keys:
```python
def add_calculated_fields(self, field_dict):
    for field_name, content in field_dict.items():
        self._calculated_fields[field_name] = content
    # Do NOT call self_clean here — values are dicts, not lists
```

---

### CR-04: LSP violation — `check_dependencies` return type changed in subclass, silently breaks base `map_reports`

**File:** `odoo_fast_report_mapper/eq_odoo_connection.py:141` / `odoo_report_helper/odoo_connection.py:190`

**Issue:** The base class defines:
```python
def check_dependencies(self, dependencies) -> bool:   # returns True or False
```
The subclass redefines:
```python
def check_dependencies(self, dependencies):           # returns (bool, list)
```
`OdooConnection.map_reports` (the base implementation) uses the return value as a bare boolean guard:
```python
dependencies_installed = self.check_dependencies(report._dependencies)
if not dependencies_installed:   # evaluates bool((False, ["sale"])) == True — ALWAYS passes!
    ...
```
If `OdooConnection.map_reports` is ever called on an `EqOdooConnection` instance (e.g., via `super().map_reports()` or a test that bypasses the override), all dependency checks are silently bypassed because `bool(tuple)` is always `True`.

**Fix:** Either give the subclass a different method name (e.g., `check_dependencies_detailed`), or make the base class return type consistent:
```python
# Option A: rename in subclass
def check_dependencies_with_details(self, dependencies) -> tuple[bool, list]: ...

# Option B: align base class to return tuple too and update all callers
def check_dependencies(self, dependencies) -> tuple[bool, list]:
    not_installed = [d for d in (dependencies or []) if not self.check_module(d)]
    return (len(not_installed) == 0), not_installed
```

---

## Warnings

### WR-01: CLI key-prefix display depends on `connection.password` not yet being `None` — order-sensitive fragility

**File:** `odoo_fast_report_mapper/odoo_fast_report_mapper.py:176`

**Issue:** The connection summary box reads `connection.password` at line 176 to extract and display the first 4 characters of the API key. `login()` is called later at line 218. After `login()`, `self.password` is set to `None`. The current ordering is correct, but the code contains no comment or guard. Any refactor that moves the `login()` call earlier (e.g., to eagerly validate credentials) would silently show `"…"` instead of the key prefix, breaking the UX without an error.

**Fix:** Read the key prefix before constructing `EqOdooConnection`, or store the prefix in a dedicated attribute at construction time:
```python
# In EqOdooConnection.__init__:
self._api_key_prefix = (credential[:4] + "…") if auth_method == "api_key" and len(credential) > 4 else "…"
```

---

### WR-02: `set_log_level()` has no effect on loggers created after the call

**File:** `odoo_fast_report_mapper/logging_config.py:203`

**Issue:** `set_level()` stores the level in `self._log_level` and updates all currently cached loggers. But `setup_logger()` ignores `self._log_level`; it uses the `level` parameter which defaults to `logging.INFO`. Any module that calls `get_logger(__name__)` after `set_log_level(logging.DEBUG)` still receives an `INFO`-level logger.

**Fix:** In `setup_logger()`, use `self._log_level` as the effective default:
```python
def setup_logger(self, name: str = "odoo_fast_report_mapper",
                 level: int | None = None, ...) -> logging.Logger:
    effective_level = level if level is not None else self._log_level
    logger = logging.getLogger(name)
    logger.setLevel(effective_level)
    ...
```

---

### WR-03: `build_name_search_domain` returns `[]` for empty `name_dict`, creating an unbounded model search

**File:** `odoo_fast_report_mapper/lang_utils.py:87`

**Issue:** When `name_dict` is empty, `all_variants = []` and `len(all_variants) <= 1` is `True`, so the function returns `[]`. The caller builds the search domain as:
```python
[("model", "=ilike", model_name)] + []  # = [("model", "=ilike", model_name)]
```
This matches **all** reports for that model. The first one found is silently updated rather than a new report being created.

**Fix:** Raise or return a sentinel that callers can detect:
```python
if not all_variants:
    raise ValueError(f"Cannot build name search domain from empty name_dict")
```

---

### WR-04: `prepare_connection` URL parsing is fragile — path components are silently retained

**File:** `odoo_report_helper/utils.py:27`

**Issue:** `url.replace("https:", "")` strips only the literal scheme token but leaves `//hostname/path`. The while-loop strips leading slashes, leaving `hostname/path`, which is passed as-is to `ODOO(url, ...)`. OdooRPC uses this string as the HTTP host header, causing a silent connection failure when the URL includes any path component (e.g., `https://odoo.example.com/web`).

**Fix:** Use `urlparse` to extract only the hostname:
```python
from urllib.parse import urlparse
parsed = urlparse(url)
hostname = parsed.hostname  # always just the hostname, no scheme/path/port
```

---

### WR-05: `Report` base class annotates `entry_name: str` but always receives a `dict` at runtime

**File:** `odoo_report_helper/report.py:10`

**Issue:** `Report.__init__` declares `entry_name: str`. `EqReport` (the only concrete subclass) always passes a `dict` mapping locale codes to names. `Report.self_ensure()` assigns `self._data_dictionary["name"] = self.entry_name` directly. If `Report.self_ensure()` were called on an `EqReport` instance (bypassing the override), Odoo would receive a Python dict as the `name` field value.

**Fix:** Change the annotation in `Report.__init__` to reflect actual usage:
```python
entry_name: str | dict,  # dict when used via EqReport (lang_code -> name)
```
Or, since the cleanup milestone intends to dissolve the base class, document this as a known pre-merge inconsistency.

---

### WR-06: `add_field_to_dictionary` issues 2 uncached RPC calls per field during collection

**File:** `odoo_fast_report_mapper/eq_odoo_connection.py:598-602`

**Issue:** For every field processed in `collect_report_entries`, `add_field_to_dictionary` makes two round-trip RPC calls:
1. `IR_MODEL.search([("model", "=", model_name)])` — same model name is re-queried for every field in that model.
2. `IR_FIELDS.search([("model_id", "=", model_id[0]), ("name", "=", field_name)])` — unbatched per field.

With a real database containing hundreds of fields per report, this produces O(n_fields) sequential RPCs in the hot path of the collect operation.

**Fix:** Extract model_id lookups into a cache dict (same pattern already used in `_map_report_fields`):
```python
# Move model_id lookup outside add_field_to_dictionary or pass it as a parameter:
if model_name not in _model_id_cache:
    model_ids = IR_MODEL.search([("model", "=", model_name)])
    _model_id_cache[model_name] = model_ids[0] if model_ids else None
```

---

### WR-07: `create_odoo_connection_from_yaml_object` hard-codes `auth_method='password'`, silently ignores API key

**File:** `odoo_fast_report_mapper/eq_utils.py:126`

**Issue:** The legacy YAML connection loader passes `yaml_object["Server"]["password"]` with no `auth_method` argument, defaulting to `"password"`. There is no support for an `api_key` key in the YAML connection format. A user who puts an API key in the `password` field will get wrong authentication behavior. The function is marked deprecated but is still reachable via `collect_all_connections()`.

**Fix:** Either add `api_key` field support to the YAML format, or add a deprecation warning that routes users to `create_connection_from_env()`:
```python
if yaml_object["Server"].get("api_key"):
    credential = yaml_object["Server"]["api_key"]
    auth_method = "api_key"
else:
    credential = yaml_object["Server"]["password"]
    auth_method = "password"
```

---

## Info

### IN-01: Dead code — `ProgressBar`, `create_progress_bar`, `ReportProgress` unused in production

**File:** `odoo_fast_report_mapper/progress.py:17`

**Issue:** Only `progress_bar()` (the bare function wrapping `tqdm`) is called in production code (once, in `collect_report_entries`). The `ProgressBar` class, `create_progress_bar()` factory, and `ReportProgress` static-method class are exercised only by tests. These three symbols should be removed as part of the "removing dead progress-bar APIs" cleanup milestone goal.

---

### IN-02: Dead code — `OdooConnection._get_fast_report_ids()` never called in production

**File:** `odoo_report_helper/odoo_connection.py:172`

**Issue:** `_get_fast_report_ids()` has no callers outside the test suite. It will become unreachable once `odoo_report_helper` is dissolved.

---

### IN-03: Dead code — `fire_all_functions()` never called in production

**File:** `odoo_report_helper/utils.py:54`

**Issue:** `fire_all_functions()` has no callers outside the test suite. Remove during cleanup.

---

### IN-04: Commented-out code left in `set_calculated_fields`

**File:** `odoo_report_helper/odoo_connection.py:147-148`

**Issue:** Two lines of commented-out code remain:
```python
# calculated_field_id = calculated_field_id[0]
# calculated_field_object = REPORT_CALC.browse(calculated_field_id)
```
These appear to be a previous implementation replaced without deletion.

---

### IN-05: Pervasive missing type annotations across both packages

**File:** `odoo_fast_report_mapper/eq_odoo_connection.py`, `odoo_report_helper/odoo_connection.py`, and others

**Issue:** The vast majority of function parameters and return types lack annotations. A scan of all 14 files found 56 functions with missing return type annotations and dozens of unannotated parameters. This will block the mypy-strict milestone goal. The most type-critical gaps are:
- All methods in `EqOdooConnection` (eq_odoo_connection.py)
- All methods in `OdooConnection` (odoo_connection.py)
- `Report.__init__` entry_name parameter (discussed in WR-05)

---

### IN-06: Each module creates its own log file instead of a unified log

**File:** `odoo_fast_report_mapper/logging_config.py:107`

**Issue:** `setup_logger(name)` creates `~/.odoo-fast-report-mapper/logs/{name}.log`. Since every module calls `get_logger(__name__)`, the application produces separate log files:
- `odoo_fast_report_mapper.log`
- `odoo_fast_report_mapper.eq_odoo_connection.log`
- `odoo_fast_report_mapper.eq_utils.log`
- etc.

Operators have to tail multiple files to trace a single operation. The standard Python approach is to use a root logger with `propagate=True` and configure handlers only on the root, or to strip the module name to a common prefix.

---

_Reviewed: 2026-05-27_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: deep_
