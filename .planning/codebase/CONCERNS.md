# Codebase Concerns

**Analysis Date:** 2026-05-11
**Source:** REVIEW.md (v0.9.6 adversarial review, 18 findings) + v0.9.7 post-release state
**Branch:** develop (post v0.9.7, commit series after a2a315d)

---

## Legend

| Severity | Meaning |
|----------|---------|
| HIGH | Runtime crash risk under real input, test isolation break |
| MEDIUM | Logic error, data corruption risk, type contract violation |
| LOW | Style, naming, dead code, minor robustness |

| Status | Meaning |
|--------|---------|
| open | Not yet fixed |
| deferred-to-v1.0 | Deliberately deferred, documented decision |
| accepted | Known limitation, not worth fixing |
| fixed-in-v0.9.7 | Addressed in the v0.9.7 release series |

---

## Tech Debt

### Two-Package Architecture Layering

**Area:** Overall architecture
**Severity:** MEDIUM
**Status:** open

- Issue: `odoo_report_helper` is the base package; `odoo_fast_report_mapper` is the extension. In practice, nearly every method in `OdooConnection` (`map_reports`, `set_calculated_fields`, `add_calculated_fields`) is fully overridden — not extended — by `EqOdooConnection`. The base class is structurally intact but logically dead.
- Files: `odoo_report_helper/odoo_connection.py`, `odoo_fast_report_mapper/eq_odoo_connection.py`
- Impact: Bugs fixed in the subclass diverge silently from the base (see B-01, W-02, W-03 below — all live in dead base-class paths). Any future contributor who instantiates `OdooConnection` directly hits broken code.
- Fix approach: v1.0 candidate — collapse into a single package, or formally mark base methods as `NotImplemented` / abstract to make the override contract explicit.

---

### `preferred_lang` Defaults to German (Equitania Convention)

**Area:** `lang_utils.get_primary_lang()`
**Severity:** LOW
**Status:** fixed-in-v0.9.7

- Issue: v0.9.7 added `preferred_lang='de_DE'` parameter. The default still silently produces German-first behavior for callers that omit the argument — correct for Equitania deployments, potentially surprising for French/English-only installations.
- Files: `odoo_fast_report_mapper/lang_utils.py:52-68`
- Impact: Non-German Odoo instances see German-language report names selected as primary. Low real-world impact since deployments are Equitania-controlled.
- Fix approach: Accepted business convention. Document in docstring (done in v0.9.7). No further action needed unless the tool becomes a generic open-source utility.

---

### `add_field_to_dictionary` Extra RPC Calls per Field

**Area:** Performance — YAML collection mode
**Severity:** LOW
**Status:** open

- Issue: During collection mode (`collect_yaml: True`), `add_field_to_dictionary` makes 2 additional RPC calls per field: one to `ir.model` (to resolve model display name) and one to `ir.model.fields` (to resolve field metadata). For reports with many fields across many companies this compounds to significant network overhead.
- Files: `odoo_fast_report_mapper/eq_odoo_connection.py` (collection path, approx. lines 520-570)
- Impact: Slow collection runs on large Odoo instances; no correctness issue.
- Fix approach: Cache `ir.model` lookups by model name within a single collection run. Batch `ir.model.fields` search with `name in [...]` domain instead of per-field queries.

---

## Known Bugs

### B-01: `report.model` AttributeError in Base `OdooConnection.map_reports`

**Severity:** HIGH (dead code path — masked in production)
**Status:** open

- Symptoms: `AttributeError: 'EqReport' object has no attribute 'model'` when calling base `OdooConnection.map_reports` with calculated fields.
- Files: `odoo_report_helper/odoo_connection.py:103`
- Trigger: Instantiating `OdooConnection` directly (not `EqOdooConnection`) and processing reports with `calculated_fields`. Not reachable via CLI.
- Fix: `report.model` → `report.model_name` at line 103.

```python
# Line 103 — broken
self.set_calculated_fields(field, function_name, parameter, report.entry_name, report.model)
# Fix
self.set_calculated_fields(field, function_name, parameter, report.entry_name, report.model_name)
```

---

### B-02: `KeyError: 'dependencies'` in `create_eq_report_object`

**Severity:** HIGH (edge case — report with no mapped fields)
**Status:** fixed-in-v0.9.7

- Symptoms: `KeyError: 'dependencies'` when a report in a company sweep produces an empty field dictionary.
- Files: `odoo_fast_report_mapper/eq_odoo_connection.py:640-642`
- Trigger: Multi-company collection where one company has no visible report actions for a given report.
- Fix applied: `sorted(field_dictionary.pop("dependencies", []))` replaces the two-line access-then-guard pattern.

---

### B-03: Unguarded `report_id[0]` IndexError

**Severity:** HIGH (reachable under race condition or wrong model/name)
**Status:** fixed-in-v0.9.7

- Symptoms: `IndexError: list index out of range` in `set_calculated_fields` when the report is not found by name/model search.
- Files: `odoo_report_helper/odoo_connection.py:131-133`, `odoo_fast_report_mapper/eq_odoo_connection.py:386-388`
- Trigger: Report not yet created in Odoo, wrong `report_model`, or partial Odoo RPC failure before `set_calculated_fields` is called.
- Fix applied: Guard added; logs `logger.error(...)` and returns early if `report_id` is empty.

---

### W-02: `add_calculated_fields` Iterates Dict Without `.items()`

**Severity:** MEDIUM (dead code path — silent crash if called)
**Status:** open

- Symptoms: `ValueError: too many values to unpack` at runtime if `add_calculated_fields` is ever called on a non-empty `field_dict`.
- Files: `odoo_report_helper/report.py:77`
- Trigger: Not called in any production path — only reachable via direct `Report` instantiation. Dead but broken.
- Fix: `for field_name, content in field_dict:` → `for field_name, content in field_dict.items():`

---

### W-04: `_search_report_v13` Passes `None` as `company_id` in Domain

**Severity:** LOW (Odoo treats `None` and `False` identically for Many2one)
**Status:** fixed-in-v0.9.7

- Symptoms: Slightly incorrect domain `["|", ("company_id", "=", None), ("company_id", "=", False)]` when called without `company_id`.
- Files: `odoo_fast_report_mapper/eq_odoo_connection.py:85-93`
- Fix applied: Guards now mirror `_search_report` — company domain omitted when `company_id` is falsy.

---

### P-05: Off-by-One `else` in `add_field_to_dictionary` Company Accumulation

**Severity:** MEDIUM (data loss — can overwrite accumulated company IDs)
**Status:** fixed-in-v0.9.7

- Symptoms: In multi-company collection, previously accumulated `company_id` list entries overwritten by a fresh one-element list when the `if` branch condition evaluates False for the wrong reason.
- Files: `odoo_fast_report_mapper/eq_odoo_connection.py:555-562`
- Fix applied: Condition split into `if "company_id" not in ...` / `elif company_id not in ...` guards.

---

### P-10: Company Context Not Restored on `continue` in `test_fast_report_rendering`

**Severity:** LOW (transient — outer loop resets company at next iteration start)
**Status:** fixed-in-v0.9.7

- Symptoms: If a report is skipped (not found, or not `fast_report` type), the env company is not restored before `continue`. Next report in same run starts with wrong company context for one RPC call.
- Files: `odoo_fast_report_mapper/eq_odoo_connection.py:704-765`
- Fix applied: Wrapped company assignment and restoration in `try/finally`.

---

## Security Considerations

### HTTP Plaintext Connection

**Area:** Connection URL validation
**Severity:** MEDIUM (warn-only, user-controlled)
**Status:** fixed-in-v0.9.7

- Risk: Users who provide `http://` URLs send credentials in plaintext.
- Files: `odoo_fast_report_mapper/eq_utils.py` (URL validation path)
- Current mitigation: v0.9.7 added a logged warning when `http://` is detected; connection proceeds but user is informed.
- Recommendation: No further action needed for CLI tool targeting developer/admin users.

### Password Cleared Post-Login

**Area:** Credential lifecycle
**Severity:** LOW (accepted)
**Status:** fixed-in-v0.9.7

- Risk: Server config dict retained password in memory after successful login.
- Files: `odoo_report_helper/odoo_connection.py` (login path)
- Current mitigation: Password placeholder zeroed after login in v0.9.7.

---

## Fragile Areas

### Circular Import: `odoo_report_helper` ↔ `odoo_fast_report_mapper`

**Severity:** HIGH (test isolation broken)
**Status:** open — PRE-EXISTING, not introduced in v0.9.7

- Files: `odoo_report_helper/odoo_connection.py:9` imports `odoo_fast_report_mapper.lang_utils`; `odoo_fast_report_mapper/eq_odoo_connection.py:11` imports `OdooConnection` from `odoo_report_helper.odoo_connection`
- Why fragile: `tests/test_odoo_connection.py` cannot be collected in isolation (`pytest tests/test_odoo_connection.py` fails with `ImportError`). Full suite (`pytest tests/`) passes because import order resolves correctly when all modules are loaded together.
- Safe modification: Always run the full test suite. Never run individual test files in `tests/` that touch connection classes.
- Test coverage: 369 tests total; all pass in full-suite mode.
- Fix approach: v1.0 — move `lang_utils` to `odoo_report_helper` (the base package), eliminating the reverse dependency.

---

### `LoggerManager._loggers` Class-Level Mutable Dict

**Severity:** MEDIUM
**Status:** open (W-05 from REVIEW.md)

- Files: `odoo_fast_report_mapper/logging_config.py:87`
- Why fragile: `_loggers: dict = {}` is a class attribute shared across all instances. The singleton pattern (`_initialized` flag) prevents re-init in production, but tests that import the module in unusual order or reset singleton state could share logger state silently.
- Test impact: `test_logging.py` has a complex fixture that resets singleton state between tests — this fixture is itself fragile and tightly coupled to the singleton implementation.
- Safe modification: Do not modify `LoggerManager.__init__` without also updating `test_logging.py` reset fixtures.
- Fix approach: Move `_loggers = {}` into `__init__` as an instance attribute (after the `_initialized` guard).

---

### W-01: `company_id` Loop Variable Shadowed in `collect_report_entries`

**Severity:** MEDIUM
**Status:** fixed-in-v0.9.7

- Files: `odoo_fast_report_mapper/eq_odoo_connection.py:461,501`
- Why fragile: Outer `for company_id in company_ids:` loop variable was silently overwritten at line 501 by inner assignment. Python's for-loop re-bind at next iteration made the env switch safe in practice, but any code between the shadowing and the next loop start saw the wrong value.
- Fix applied: Inner variable renamed to `report_company_id`.

---

## Dead-But-Public API (Deferred)

### P-08 / P-09: `ProgressBar`, `ReportProgress`, `create_progress_bar` in `progress.py`

**Severity:** LOW
**Status:** deferred-to-v1.0

- Files: `odoo_fast_report_mapper/progress.py:17-208`
- What's unused: `ProgressBar` class (thin tqdm wrapper, lines 17-95), `create_progress_bar()` factory (lines 137-160), `ReportProgress` static methods `mapping_progress`/`field_progress`/`testing_progress` (lines 161-208). Only `progress_bar()` (simple context manager, lines 98-135) is used internally.
- Why deferred: These are part of the PyPI public API (exported via `__init__.py`) and have 250+ lines of test coverage in `tests/test_progress.py`. Removal would be a breaking change requiring a major version bump.
- Decision rationale: Preserve for v1.0, at which point either add meaningful abstraction to `ProgressBar` (auto-increment `tick()` method) or formally deprecate with `DeprecationWarning` before removal in v2.0.
- Risk: Callers relying on these in downstream code would break silently on removal without a deprecation cycle.

---

## Mypy Baseline Errors (13 Pre-Existing)

**Severity:** LOW (type-checker only; no runtime impact)
**Status:** accepted

Known mypy errors that exist in the codebase and are not blocking:

| File | Line(s) | Error |
|------|---------|-------|
| `odoo_fast_report_mapper/logging_config.py` | 156 | `Formatter`/`ColoredFormatter` assignment incompatibility |
| `odoo_fast_report_mapper/logging_config.py` | 194, 211 | `Any` return from `Path`-typed functions |
| `odoo_report_helper/report.py` | 37 | `_data_dictionary` annotation mismatch |
| `odoo_fast_report_mapper/eq_odoo_connection.py` | 165, 166 | `models_fields`, `model_name_ids` type issues |
| `odoo_fast_report_mapper/eq_odoo_connection.py` | ~755, 772, 776 | `report_object` union attribute access |

- Fix approach: Address incrementally; requires either stub types for `odoorpc-toolbox` or explicit `cast()` calls. Not blocking any feature work.

---

## Missing Critical Features

### P-06: `ENV_TEMPLATE` Missing API-Key Placeholder

**Severity:** LOW
**Status:** fixed-in-v0.9.7

- Problem: The generated `.env` template only documented `ODOO_USER` / `ODOO_PASSWORD`. With API-key auth added in v0.9.7, new adopters generating templates would not see the `ODOO_API_KEY` option.
- Files: `odoo_fast_report_mapper/eq_utils.py:18-44`
- Fix applied: `# ODOO_API_KEY=your_api_key` placeholder added (commented, with mutual-exclusivity note).

---

## Test Coverage Gaps

### Isolated Test Collection Failure (Circular Import)

**What's not tested:** `odoo_report_helper/odoo_connection.py` in isolation.
**Files:** `tests/test_odoo_connection.py`
**Risk:** A regression in the base `OdooConnection` class would only be caught if the full suite is run. A developer running only connection-related tests gets a collection error, not a test failure — easy to misinterpret as "tests pass" when they were never collected.
**Priority:** MEDIUM

### Base Class Dead Paths (B-01, W-02, W-03)

**What's not tested:** `OdooConnection.map_reports()` with calculated fields, `Report.add_calculated_fields()` with a non-empty dict, base `map_reports` return value handling.
**Files:** `odoo_report_helper/odoo_connection.py:57-107`, `odoo_report_helper/report.py:77`
**Risk:** These paths are broken (see B-01 and W-02 above) but no test exercises them — they would crash silently in production if the base class were ever used directly.
**Priority:** LOW (only relevant if two-package architecture is preserved; lower priority if v1.0 collapses it)

### `LoggerManager` Singleton Reset Fragility

**What's not tested:** `LoggerManager` behavior when imported in unusual module order or after partial reset.
**Files:** `odoo_fast_report_mapper/logging_config.py`, `tests/test_logging.py`
**Risk:** `test_logging.py` relies on complex fixture teardown to reset `_initialized` and `_loggers`. If a test leaves the singleton in a partially-initialized state, subsequent tests in the same process may silently receive stale loggers.
**Priority:** LOW

---

## Minor Polish Items (Open)

| ID | File | Line | Issue | Status |
|----|------|------|-------|--------|
| P-01 | `odoo_report_helper/exceptions.py:9` | 9 | Typo: `PathDoesNotExitError` (missing 's') — all callers use same misspelling, so no runtime impact | fixed-in-v0.9.7 |
| P-02 | `odoo_fast_report_mapper/eq_odoo_connection.py` | 733-740 | Commented-out debug block with "Can be commented if not necessary" note | fixed-in-v0.9.7 |
| P-03 | `odoo_fast_report_mapper/lang_utils.py` | 52-68 | German-first priority; `preferred_lang` param added but default unchanged | fixed-in-v0.9.7 |
| P-04 | `odoo_fast_report_mapper/eq_utils.py` | 161 | `build_reports_from_yaml_objects` mutates input dict before deepcopy of copies | fixed-in-v0.9.7 |
| P-07 | `odoo_fast_report_mapper/lang_utils.py` | 19 | `LOCALE_TO_LEGACY` computed at import time but never called anywhere | fixed-in-v0.9.7 |

---

## Open Items Summary

| ID | Severity | Status | File | Line | Topic |
|----|----------|--------|------|------|-------|
| B-01 | HIGH | open | `odoo_report_helper/odoo_connection.py` | 103 | `report.model` → `report.model_name` crash in base class |
| W-02 | MEDIUM | open | `odoo_report_helper/report.py` | 77 | `add_calculated_fields` iterates dict without `.items()` |
| W-03 | MEDIUM | open | `odoo_report_helper/odoo_connection.py` | 57 | Base `map_reports` returns `None`, CLI would crash on iteration |
| W-05 | MEDIUM | open | `odoo_fast_report_mapper/logging_config.py` | 87 | `_loggers` class-level mutable dict — singleton fragile |
| CIRC | HIGH | open | `odoo_report_helper/odoo_connection.py:9` + `eq_odoo_connection.py:11` | — | Circular import breaks isolated test collection |
| ARCH | MEDIUM | open | `odoo_report_helper/`, `odoo_fast_report_mapper/` | — | Two-package layering with mostly-dead base class |
| PERF | LOW | open | `odoo_fast_report_mapper/eq_odoo_connection.py` | ~520-570 | 2 extra RPC calls per field in collection mode |
| MYPY | LOW | accepted | Multiple (see table above) | various | 13 pre-existing mypy baseline errors |
| P-08/09 | LOW | deferred-to-v1.0 | `odoo_fast_report_mapper/progress.py` | 17-208 | Dead-but-public `ProgressBar`/`ReportProgress`/`create_progress_bar` |

---

*Concerns audit: 2026-05-11*
*Source: REVIEW.md v0.9.6 (18 findings), v0.9.7 release series, prompt-supplied context*
