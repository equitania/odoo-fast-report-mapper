# Code Review: odoo-fast-report-mapper v0.9.6

**Reviewed:** 2026-05-11  
**Branch:** develop (a2a315d)  
**Depth:** standard  
**Files Reviewed:** 14  

```
odoo_fast_report_mapper/__init__.py
odoo_fast_report_mapper/__version__.py
odoo_fast_report_mapper/eq_odoo_connection.py
odoo_fast_report_mapper/eq_report.py
odoo_fast_report_mapper/eq_utils.py
odoo_fast_report_mapper/lang_utils.py
odoo_fast_report_mapper/logging_config.py
odoo_fast_report_mapper/odoo_fast_report_mapper.py
odoo_fast_report_mapper/progress.py
odoo_report_helper/__init__.py
odoo_report_helper/exceptions.py
odoo_report_helper/odoo_connection.py
odoo_report_helper/report.py
odoo_report_helper/utils.py
```

**Status:** issues_found  

---

## Summary

The codebase is well-structured and security-hardened (safe_load, path-traversal guards, password cleared post-login, HTTP warning). No critical security issues found. Two bugs exist in the base `odoo_report_helper` package that are masked in normal operation by the override in `EqOdooConnection`. Several polish-level items remain from the architecture and style perspective.

---

## BLOCKER — Bugs

### B-01: `report.model` AttributeError in base `OdooConnection.map_reports`

**File:** `odoo_report_helper/odoo_connection.py:103`  
**Issue:** `set_calculated_fields` is called with `report.model`, but neither `Report` nor `EqReport` defines a `.model` attribute — the correct attribute is `.model_name`. This raises `AttributeError` whenever the base class `map_reports` is used with calculated fields. EqOdooConnection overrides `map_reports` so this is masked in production, but the base class is broken.

```python
# Current (line 103) — AttributeError: 'EqReport' object has no attribute 'model'
self.set_calculated_fields(field, function_name, parameter, report.entry_name, report.model)

# Fix
self.set_calculated_fields(field, function_name, parameter, report.entry_name, report.model_name)
```

**Rationale:** Dead-but-broken code in the base class is a trap for anyone instantiating `OdooConnection` directly or writing a test against it.

---

### B-02: `create_eq_report_object` accesses `field_dictionary["dependencies"]` before existence check

**File:** `odoo_fast_report_mapper/eq_odoo_connection.py:640-642`  
**Issue:** Line 640 does `sorted(field_dictionary["dependencies"])` unconditionally, then line 641 checks `if "dependencies" in field_dictionary`. If a report somehow has no `dependencies` key in the collected field dictionary (edge case: no fields were found for the report), this raises `KeyError`. The guard is after the access, not before.

```python
# Current — guard is too late
dependencies = sorted(field_dictionary["dependencies"])   # line 640: KeyError if key absent
if "dependencies" in field_dictionary:
    del field_dictionary["dependencies"]

# Fix — guard before access
dependencies = sorted(field_dictionary.pop("dependencies", []))
```

**Rationale:** `add_field_to_dictionary` only writes `dependencies` when at least one field is processed. A report with no mapped fields in a company sweep could produce a dict without the key.

---

### B-03: `set_calculated_fields` indexes `report_id[0]` without guard (both base and subclass)

**File:** `odoo_report_helper/odoo_connection.py:131-133`  
**File:** `odoo_fast_report_mapper/eq_odoo_connection.py:386-388`  
**Issue:** After searching for the report by name/model, `report_id[0]` is accessed without checking whether the search returned any results. If the report was not found (e.g. not yet created, or wrong model/name), this raises `IndexError`.

```python
# Current — unguarded
value_dict["eq_report_id"] = report_id[0]

# Fix — guard first
if not report_id:
    logger.error(f"Cannot set calculated fields: report not found for model={report_model}")
    return
value_dict["eq_report_id"] = report_id[0]
```

**Rationale:** `_create_or_update_report` calls `create_action()` before `set_calculated_fields` is invoked, so the report should normally exist — but a race condition or partial Odoo failure would surface this crash with no useful error message.

---

## WARNING — Logic / Robustness

### W-01: `company_id` loop variable shadowed inside `collect_report_entries`

**File:** `odoo_fast_report_mapper/eq_odoo_connection.py:461,501`  
**Issue:** The outer `for company_id in company_ids:` loop variable (the Odoo company integer) is silently overwritten at line 501 by `company_id = report_action_object.company_id.id if ... else False`. After the first `report_action_id` in the inner loop overwrites `company_id` to `False` (when the report has no company), the outer loop's `company_id` is corrupted for all subsequent iterations within that same field.  

The outer loop's `self.connection.env.user.company_id = company_id` assignment on the next iteration still uses the correct value from `company_ids` (Python re-binds it at the top of the for-loop), so the env switch is safe. But any code between the inner assignment and the next outer-loop iteration that relies on `company_id` being the outer value could behave incorrectly.

```python
# Fix: rename inner variable
for report_action_id in report_action_ids:
    report_company_id = report_action_object.company_id.id if report_action_object.company_id else False
    if report_company_id:
        ...
    data_dictionary = self.add_field_to_dictionary(
        data_dictionary, report_action_id, model_name, field_name, report_company_id
    )
```

---

### W-02: `add_calculated_fields` in `Report` iterates `field_dict` without `.items()`

**File:** `odoo_report_helper/report.py:77`  
**Issue:** `for field_name, content in field_dict:` attempts to unpack dict keys (strings) as 2-tuples, which raises `ValueError: too many values to unpack` (or `not enough values`) on any real input. Should be `field_dict.items()`. This method is not called anywhere in the production code path (only `EqOdooConnection` uses `_calculated_fields` directly), so it is silently broken dead code.

```python
# Current (line 77) — TypeError/ValueError at runtime
for field_name, content in field_dict:

# Fix
for field_name, content in field_dict.items():
```

---

### W-03: `base OdooConnection.map_reports` silently returns `None`; caller in CLI checks truthy result

**File:** `odoo_report_helper/odoo_connection.py:57-107`  
**File:** `odoo_fast_report_mapper/odoo_fast_report_mapper.py:247,253`  
**Issue:** The base `OdooConnection.map_reports` has no return statement (returns `None`). The CLI at lines 247 and 253 does `failed_reports = connection.map_reports(reports)` and then `if failed_reports:`. If anyone ever calls the base version, `None` is iterable-falsy which happens to be fine, but the type contract is violated and the call at line 264 `for name, error in failed_reports:` would crash on `None` since `None` is not iterable.

```python
# Fix: add explicit return in base class
def map_reports(self, report_list: list) -> list:
    ...
    return []  # base implementation never collected failures; return empty list
```

---

### W-04: `_search_report_v13` always queries with company_id domain even when `company_id=None`

**File:** `odoo_fast_report_mapper/eq_odoo_connection.py:85-93`  
**Issue:** `_search_report_v13` always appends `company_domain = ["|", ("company_id", "=", company_id), ("company_id", "=", False)]` regardless of whether `company_id` is `None`. When called without a company (the v13 path in `test_fast_report_rendering` line 710 doesn't pass `company_id`), the domain becomes `... ["|", ("company_id", "=", None), ("company_id", "=", False)]` — a slightly wrong but probably harmless query (Odoo treats `None` and `False` identically for Many2one). The inconsistency with `_search_report` (which guards `if company_id:`) is a latent correctness issue.

```python
# Fix: mirror the guard from _search_report
company_domain = ["|", ("company_id", "=", company_id), ("company_id", "=", False)] if company_id else []
report_ids = IR_ACTIONS_REPORT.search([("model", "=ilike", model_name)] + name_domain + company_domain)
```

---

### W-05: `LoggerManager._loggers` is a class-level mutable dict — shared across all instances

**File:** `odoo_fast_report_mapper/logging_config.py:87`  
**Issue:** `_loggers: dict = {}` is declared as a class attribute, not an instance attribute. In a singleton this is largely harmless, but if the singleton assumption ever breaks (tests, imports in unusual order), all `LoggerManager` instances share the same logger dict, leading to silently dropped logger reconfiguration. The `_initialized` flag prevents re-init via `__init__`, which does protect the singleton in practice, but the dict should be an instance attribute set in `__init__`.

```python
# Fix: move to __init__
def __init__(self):
    if self._initialized:
        return
    self._initialized = True
    self._loggers = {}   # instance attribute, not class attribute
    ...
```

---

## POLISH — Style, Naming, Minor Cleanup

### P-01: `exceptions.py` typo in class name: `PathDoesNotExitError` → `PathDoesNotExistError`

**File:** `odoo_report_helper/exceptions.py:9`  
**Issue:** Class is named `PathDoesNotExitError` (missing 's'). All callers use the same misspelling so it works, but it reads as "does not exit" rather than "does not exist". Fix in one place.

```python
# Current
class PathDoesNotExitError(Exception):

# Fix
class PathDoesNotExistError(Exception):
```

Update all three raise sites in `eq_utils.py` (lines 202, 345) accordingly.

---

### P-02: Commented-out debug block in `test_fast_report_rendering`

**File:** `odoo_fast_report_mapper/eq_odoo_connection.py:733-740`  
**Issue:** A multi-line block of commented-out code with an inline note "Can be commented if not necessary" has been left in. Either convert to a proper `logger.debug` call or remove entirely.

```python
# Remove lines 733-740 (the triple-quoted "extra help" comment block)
# If the debug info is genuinely useful, replace with:
logger.debug(
    "Model %s used by report %s (file: %s)",
    report.model_name, report.report_name, report.print_report_name
)
```

---

### P-03: `get_primary_lang` German-first priority is an undocumented business rule hardcoded in shared utility

**File:** `odoo_fast_report_mapper/lang_utils.py:52-68`  
**Issue:** The function hardcodes `de_DE` as the default primary language with fallback to any `de*` code. This is business-logic (Equitania is a German company) embedded in a generic utility. When a French-only or English-only installation uses the tool, the fallback chain silently falls through to "first key in dict" (arbitrary in Python <3.7 insertion-ordered dicts). The function should either accept a `preferred_lang` argument or at minimum document the Equitania-specific assumption.

```python
def get_primary_lang(name_dict: dict, preferred_lang: str = "de_DE") -> str:
    """Return primary language code from name dict.
    
    Priority: preferred_lang > any key starting with same prefix > first key.
    Default preferred_lang is 'de_DE' (Equitania convention).
    """
    if preferred_lang in name_dict:
        return preferred_lang
    prefix = preferred_lang.split("_")[0]
    for key in name_dict:
        if key.startswith(prefix):
            return key
    return next(iter(name_dict))
```

---

### P-04: `build_reports_from_yaml_objects` mutates the input `yaml_report_object` dict

**File:** `odoo_fast_report_mapper/eq_utils.py:161`  
**Issue:** `del yaml_report_object["company_id"]` modifies the original dict from the YAML parse result. In `--select` mode, the same `yaml_object` reference lives in `report_items[i]["yaml_object"]`, so re-running the selection path a second time in the same process would produce reports with missing `company_id`. The `deepcopy` on line 163 is applied to the per-company expansion copies, but the original dict is already mutated before copies are made.

```python
# Fix: copy before mutation
for yaml_report_object in yaml_objects:
    yaml_report_object = dict(yaml_report_object)  # shallow copy is enough for this key
    if yaml_report_object.get("company_id") and len(yaml_report_object.get("company_id")) > 1:
        company_ids = yaml_report_object.pop("company_id")  # no longer mutates original
        ...
```

---

### P-05: `add_field_to_dictionary` has an off-by-one `else` in company_id branch

**File:** `odoo_fast_report_mapper/eq_odoo_connection.py:555-562`  
**Issue:** The logic for adding `company_id` to the dict has an `else` that runs when the `if` condition `"company_id" in data_dictionary[report_id] and company_id not in ...` is False. This means it runs both when there is no `company_id` key yet AND when the key exists but the condition fails (company already present). The second case overwrites the existing list with a fresh one-element list, losing previously accumulated company IDs.

```python
# Current (lines 556-562)
if (
    "company_id" in data_dictionary[report_id]
    and company_id not in data_dictionary[report_id]["company_id"]
):
    data_dictionary[report_id]["company_id"].append(company_id)
else:
    data_dictionary[report_id]["company_id"] = [company_id]

# Fix: separate the two conditions
if "company_id" not in data_dictionary[report_id]:
    data_dictionary[report_id]["company_id"] = [company_id]
elif company_id not in data_dictionary[report_id]["company_id"]:
    data_dictionary[report_id]["company_id"].append(company_id)
```

---

### P-06: `ENV_TEMPLATE` in `eq_utils.py` documents only username/password auth

**File:** `odoo_fast_report_mapper/eq_utils.py:18-44`  
**Issue:** The generated `.env` template has `ODOO_USER` and `ODOO_PASSWORD` fields only. With the upcoming API-key feature in v0.9.7, `ODOO_API_KEY` should be added (commented-out, with a note that it is mutually exclusive with the password). Generating templates without it will cause confusion for new adopters of the feature.

```ini
# Authentication (use one method only)
ODOO_USER=admin
ODOO_PASSWORD=your_password
# ODOO_API_KEY=your_api_key   # Alternative to user/password (Odoo >= 14)
```

---

### P-07: `LOCALE_TO_LEGACY` reverse map in `lang_utils.py` is defined but never used

**File:** `odoo_fast_report_mapper/lang_utils.py:19`  
**Issue:** `LOCALE_TO_LEGACY = {v: k for k, v in LEGACY_LANG_MAP.items()}` is computed at import time but has no callers anywhere in the codebase.

```python
# Remove line 19 unless there is a planned use (comment the intent if so)
```

---

### P-08: `progress.py` — `ReportProgress` class and `create_progress_bar` factory are dead code

**File:** `odoo_fast_report_mapper/progress.py:137-208`  
**Issue:** `create_progress_bar` and the entire `ReportProgress` class (`mapping_progress`, `field_progress`, `testing_progress`) are defined but never imported or called anywhere in the codebase. Only `progress_bar()` (the simple wrapper) is used.

```python
# Either remove the unused class/function, or add a TODO comment
# marking them as planned API for v1.0 public interface.
```

---

### P-09: `ProgressBar` class in `progress.py` duplicates `tqdm` with no added value

**File:** `odoo_fast_report_mapper/progress.py:17-95`  
**Issue:** `ProgressBar` is a thin wrapper that re-exposes `update`, `set_description`, `set_postfix`, `close`, and context-manager protocol — all of which are already on `tqdm` directly. The wrapper adds zero logic. If the goal was to insulate from tqdm API changes, the wrapper should at least add some abstraction (e.g., a `tick()` method). As-is it adds indirection with no benefit.

```python
# Option A: remove ProgressBar, use tqdm directly in create_progress_bar
# Option B: add meaningful abstraction (e.g., auto-increment on context exit)
```

---

### P-10: `test_fast_report_rendering` — company context not restored on early `continue`

**File:** `odoo_fast_report_mapper/eq_odoo_connection.py:704-765`  
**Issue:** `original_company_yaml_user` is saved at line 704, and restored at line 765. However, if `report.company_id` is set, the company is changed at line 707 before the `continue` at line 725. If the report is not found (`not report_id`) or is not a FastReport type, execution hits `continue` and skips the restoration. On the next iteration, the env company is already set to the wrong company.

```python
# Fix: restore company before every continue, or restructure with try/finally
try:
    if report.company_id:
        self.connection.env.user.company_id = report.company_id[0]
    ...
    if not report_id or report_object.report_type != "fast_report":
        logger.warning(...)
        continue  # BUG: company not restored
finally:
    self.connection.env.user.company_id = original_company_yaml_user
```

Note: this is classified as **Polish** (not Warning) only because the outer loop overwrites the company at the start of the next report iteration — the contamination is transient. If reports are processed in a single-company environment it is invisible.

---

## Findings Summary

| ID   | Severity | File                                    | Line    | Topic                                         |
|------|----------|-----------------------------------------|---------|-----------------------------------------------|
| B-01 | BLOCKER  | odoo_report_helper/odoo_connection.py   | 103     | `report.model` → `report.model_name` crash    |
| B-02 | BLOCKER  | eq_odoo_connection.py                   | 640-642 | KeyError: dependencies accessed before guard  |
| B-03 | BLOCKER  | odoo_connection.py + eq_odoo_connection | 131,386 | Unguarded `report_id[0]` IndexError           |
| W-01 | WARNING  | eq_odoo_connection.py                   | 461,501 | `company_id` loop variable shadowed           |
| W-02 | WARNING  | odoo_report_helper/report.py            | 77      | `add_calculated_fields` iterates without `.items()` |
| W-03 | WARNING  | odoo_connection.py + CLI               | 57,247  | Base `map_reports` returns None silently      |
| W-04 | WARNING  | eq_odoo_connection.py                   | 85-93   | `_search_report_v13` passes None as company_id|
| W-05 | WARNING  | logging_config.py                       | 87      | `_loggers` class-level mutable shared dict    |
| P-01 | POLISH   | odoo_report_helper/exceptions.py        | 9       | Typo: `PathDoesNotExitError`                  |
| P-02 | POLISH   | eq_odoo_connection.py                   | 733-740 | Commented-out debug block                     |
| P-03 | POLISH   | lang_utils.py                           | 52-68   | German-first hardcoded in shared utility      |
| P-04 | POLISH   | eq_utils.py                             | 161     | Input dict mutated before deepcopy            |
| P-05 | POLISH   | eq_odoo_connection.py                   | 555-562 | Off-by-one else in company_id accumulation    |
| P-06 | POLISH   | eq_utils.py                             | 18-44   | ENV_TEMPLATE missing API-key placeholder      |
| P-07 | POLISH   | lang_utils.py                           | 19      | `LOCALE_TO_LEGACY` unused dead code           |
| P-08 | POLISH   | progress.py                             | 137-208 | `ReportProgress` + `create_progress_bar` unused |
| P-09 | POLISH   | progress.py                             | 17-95   | `ProgressBar` wrapper adds no value over tqdm |
| P-10 | POLISH   | eq_odoo_connection.py                   | 704-765 | Company context not restored on `continue`    |

---

_Reviewed: 2026-05-11_  
_Reviewer: Claude (adversarial code review)_  
_Depth: standard_
