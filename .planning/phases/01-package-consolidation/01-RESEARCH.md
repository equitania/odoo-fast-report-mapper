# Phase 1: Package Consolidation — Research

**Researched:** 2026-05-28
**Domain:** Python package structural refactoring — merge two packages into one, eliminate circular import, remove dead public API
**Confidence:** HIGH — all findings based on direct source-code inspection of the actual files

---

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
- **D-01:** Single merged class strategy. `OdooConnection` / `EqOdooConnection` collapses into `OdooConnection`. `Report` / `EqReport` → `Report` with dict-based `entry_name`. Eq-version of every overridden method is canonical.
- **D-02:** `create_connection_from_env()` stays free function in `_utils.py`; returns `(OdooConnection, dotenv_path)`. Not a classmethod.
- **D-03:** Private submodules with underscore prefix: `_connection.py`, `_report.py`, `_utils.py`, `_exceptions.py`, `_lang_utils.py`, `_logging.py`, `_yaml_dumper.py`, `_progress.py`.
- **D-04:** `__init__.py` re-exports: `OdooConnection`, `Report`, `create_connection_from_env`, custom exceptions. Everything else is sub-path import only.
- **D-05:** `progress.py` → `_progress.py` with only `progress_bar()` context manager (~50 LOC, lines 98–135). `ProgressBar`, `ReportProgress`, `create_progress_bar` deleted.
- **D-06:** `MyDumper.py` → `_yaml_dumper.py`. Consolidate with `YAMLDumper` currently in `eq_odoo_connection.py`.
- **D-07:** Overridden base methods — Eq-version is canonical; base version is deleted with the base package.
- **D-08:** Non-overridden base methods inline into merged `OdooConnection`; `build_name_search_domain` moves to `_lang_utils.py`.
- **D-09:** v0.9.7 Pflaster-fixes (B-01/B-03) implicitly removed with the base.
- **D-10:** `exceptions.py` → `_exceptions.py` (selective migration of helpers).
- **D-11:** Test files mirror consolidated package (~13 → ~9 files): `test_connection.py`, `test_report.py`, `test_utils.py`, etc.
- **D-12:** `test_progress.py` cut to ~30 LOC (only `progress_bar()` context manager tests survive).
- **D-13:** Coverage parity via `pytest --cov` before/after diff.

### Claude's Discretion
- Commit strategy (atomic vs. mega-commit) — planner's call, but `[ADD]`/`[CHG]`/`[FIX]` prefix convention applies.
- Order of operations within the phase (move-first vs. delete-first, etc.) — planner's call.
- CLI module renaming (`odoo_fast_report_mapper.py` → `_cli.py`) — recommended for naming consistency; planner can confirm or skip.
- Sub-module file boundaries within `_utils.py` — keep one file or split if past ~300 LOC.

### Deferred Ideas (OUT OF SCOPE)
- `LoggerManager._loggers` class-level mutable dict refactor
- CLI by-feature test reorganization
- Type hints throughout (Phase 2)
- `add_field_to_dictionary` RPC-call reduction (Phase 3)
- Bigger MyDumper / YAMLDumper semantic consolidation
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| CONS-01 | `odoo_report_helper/` fully dissolved into `odoo_fast_report_mapper/` as underscore-prefixed submodules | File-by-file action map below; exact renames documented |
| CONS-02 | Circular import eliminated; every test file collectable in isolation | Exact circular import traced to line 9 of `odoo_report_helper/odoo_connection.py`; fix verified |
| CONS-03 | Override-smell resolved — single merged class, no base/sub split | Inventory of all 4 overridden methods + super() call map below |
| CONS-04 | Dead base-class paths removed (B-01/B-03 band-aids gone with the base) | Confirmed: base `map_reports` and `set_calculated_fields` are entirely replaced |
| DEAD-01 | `ProgressBar` class removed; tests for it removed | Lines 17–95 of `progress.py`; 11 test functions in `TestProgressBar` identified |
| DEAD-02 | `create_progress_bar()` factory removed; tests removed | Lines 137–159 of `progress.py`; 4 test functions in `TestCreateProgressBar` |
| DEAD-03 | `ReportProgress` class removed; tests removed | Lines 162–208 of `progress.py`; 6 test functions in `TestReportProgress` |
</phase_requirements>

---

## Summary

Phase 1 is a structural refactoring with no behavior change. The codebase currently spans two packages (`odoo_report_helper/` as a base layer, `odoo_fast_report_mapper/` as an extension layer) with an upward circular dependency from the base into the extension. Nearly every public method of the base `OdooConnection` is fully overridden (not extended) by `EqOdooConnection`, making the base layer logically dead code.

The refactoring collapses both packages into a single `odoo_fast_report_mapper/` with private (underscore-prefixed) submodules. The four methods that `EqOdooConnection` overrides (`map_reports`, `_search_report`, `check_dependencies`, `set_calculated_fields`) have their Eq-version as the canonical implementation. Three base-only methods (`login`, `__init__` constructor, `_get_fast_report_ids`) are inlined into the merged class. The circular import is broken by moving `build_name_search_domain` out of `lang_utils.py` and into the new `_lang_utils.py` (which will live entirely inside `odoo_fast_report_mapper/`), removing the upward dependency from `odoo_report_helper/odoo_connection.py`.

Dead-code removal touches `progress.py` exclusively: `ProgressBar` (lines 17–95, 79 LOC), `create_progress_bar` (lines 137–159, 23 LOC), and `ReportProgress` (lines 162–208, 47 LOC) are deleted. The `progress_bar()` function (lines 98–135, 38 LOC) survives as the only content of `_progress.py`.

**Primary recommendation:** Execute the refactoring in five atomic waves, each with a green `pytest tests/` before committing. Wave order: (1) copy standalone utilities; (2) merge `OdooConnection`; (3) merge `Report`; (4) remove dead progress API; (5) reorganize tests + delete `odoo_report_helper/`.

---

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| CLI / entry point | `_cli.py` (or `odoo_fast_report_mapper.py`) | — | Click command; no business logic |
| Odoo RPC session management | `_connection.py` (`OdooConnection`) | — | State: RPC session, version, company-lang cache |
| Report mapping / testing / collect | `_connection.py` (`OdooConnection`) | `_report.py` (Report objects) | All business logic; Report is pure data container |
| Report data modeling (YAML ↔ Odoo) | `_report.py` (`Report`) | — | Stateless data container, YAML serialization |
| Environment / YAML loading, factories | `_utils.py` | — | `create_connection_from_env()`, `collect_all_reports()`, `build_reports_from_yaml_objects()` |
| Language normalization | `_lang_utils.py` | — | `normalize_language_code`, `get_primary_lang`, `build_name_search_domain` (moved here) |
| Logging (singleton) | `_logging.py` | — | `LoggerManager`, `get_logger()`, `setup_logging()` |
| YAML serialization (custom dumper) | `_yaml_dumper.py` | — | `YAMLDumper` (consolidated from two locations) |
| Progress bar (internal) | `_progress.py` | — | `progress_bar()` context manager only |
| Custom exceptions | `_exceptions.py` | — | `OdooConnectionError`, `PathDoesNotExistError`, alias |

---

## Package Inventory

### `odoo_report_helper/` — The Package Being Absorbed

**Files and public symbols:**

| File | Public Symbols | Status After Phase 1 |
|------|---------------|---------------------|
| `__init__.py` | re-exports `exceptions`, `odoo_connection`, `report`, `utils` as sub-modules | **DELETE** (whole package gone) |
| `odoo_connection.py` | `OdooConnection` class (9 methods) | **MERGE** → `_connection.py`; base version deleted, Eq-version canonical |
| `report.py` | `Report` class (6 methods) | **MERGE** → `_report.py`; base version deleted, Eq-version canonical |
| `utils.py` | `prepare_connection()`, `fire_all_functions()`, `self_clean()`, `parse_yaml()`, `parse_yaml_folder_with_filenames()`, `parse_yaml_folder()` | **MOVE** → `_utils.py` |
| `exceptions.py` | `OdooConnectionError`, `PathDoesNotExistError`, `PathDoesNotExitError` (alias) | **MOVE** → `_exceptions.py` |

**`odoo_report_helper/odoo_connection.py` method inventory:**

| Method | Lines | Status | Notes |
|--------|-------|--------|-------|
| `__init__` | 17–30 | INLINE into merged class | `super().__init__()` goes away; Eq-`__init__` is canonical (adds `language`, `collect_yaml`, `disable_qweb`, `workflow`, `auth_method`) |
| `__repr__` | 32–33 | INLINE into merged class | Simple string repr; Eq class has no `__repr__` — keep it |
| `__str__` | 35–36 | INLINE into merged class | Delegates to `__repr__` |
| `login` | 38–55 | INLINE into merged class | No Eq override; adopted verbatim |
| `map_reports` | 57–113 | **DELETE** | EqOdooConnection fully overrides; Eq-version is canonical |
| `set_calculated_fields` (base) | 115–149 | **DELETE** | EqOdooConnection fully overrides with extra `report_company_id` param |
| `_search_report` (base) | 151–170 | **DELETE** | EqOdooConnection fully overrides |
| `_get_fast_report_ids` | 172–179 | INLINE into merged class | No Eq override; adopted verbatim |
| `check_module` | 181–188 | INLINE into merged class | No Eq override; adopted verbatim |
| `check_dependencies` (base) | 190–200 | **DELETE** | EqOdooConnection fully overrides with different return type `(bool, list)` |

**`odoo_report_helper/report.py` method inventory:**

| Method | Lines | Status | Notes |
|--------|-------|--------|-------|
| `__init__` | 8–37 | **DELETE** | EqReport does NOT call `super().__init__()`; Eq-`__init__` is canonical (ARCHITECTURE.md anti-pattern noted) |
| `self_ensure` | 39–51 | **DELETE** | EqReport overrides completely |
| `add_fields` | 53–65 | EVALUATE | No Eq override — check if any test/code still calls it on EqReport; if yes, inline; if no, delete |
| `add_calculated_fields` | 67–79 | EVALUATE | Has W-02 bug (iterates dict without `.items()`); no Eq override — check callers; B-01.1 is Phase 1.1 |
| `add_dependencies` | 81–87 | EVALUATE | No Eq override — check callers |

> **Note on Report base methods with no Eq override:** `add_fields`, `add_calculated_fields`, `add_dependencies` are inherited by `EqReport` through the base. After the merge, they become direct methods on the new `Report` class. They must be included in `_report.py` because the merged class inherits their behavior. The `add_calculated_fields` bug (W-02) is tracked as BUG-02 context but is NOT fixed in Phase 1 (Phase 1.1 scope).

---

### `odoo_fast_report_mapper/` — The Receiving Package

**Files and their post-Phase-1 fate:**

| Current File | Public Symbols | Post-Phase-1 Fate |
|-------------|---------------|-------------------|
| `__init__.py` | re-exports `eq_odoo_connection`, `eq_report`, `eq_utils`, version attrs | **REWRITE** — re-export `OdooConnection`, `Report`, `create_connection_from_env`, exceptions |
| `__version__.py` | `__version__` = `"0.9.7.3"`, metadata | KEEP as-is (version bump to `1.0.0` is separate) |
| `odoo_fast_report_mapper.py` | `start_odoo_fast_report_mapper()` Click command | KEEP or rename to `_cli.py` (D-03 discretion) — update import paths |
| `eq_odoo_connection.py` | `EqOdooConnection`, `YAMLDumper` | **MERGE** → `_connection.py` (class becomes `OdooConnection`); `YAMLDumper` → `_yaml_dumper.py` |
| `eq_report.py` | `EqReport` | **MERGE** → `_report.py` (class becomes `Report`) |
| `eq_utils.py` | `create_connection_from_env()`, `collect_all_reports()`, `build_reports_from_yaml_objects()`, `create_report_object_from_yaml_object()`, `create_odoo_connection_from_yaml_object()`, `list_yaml_reports()`, `generate_env_template()`, `convert_all_yaml_objects()`, `collect_all_connections()`, `ENV_TEMPLATE` | **MERGE** → `_utils.py`; update all `odoo_report_helper.*` imports to `._exceptions`, `._utils` internals |
| `lang_utils.py` | `LEGACY_LANG_MAP`, `normalize_language_code()`, `normalize_name_dict()`, `get_primary_lang()`, `build_name_search_domain()`, `resolve_attachment_value()` | **RENAME** → `_lang_utils.py` (all same content; `build_name_search_domain` was already here) |
| `logging_config.py` | `LogColors`, `ColoredFormatter`, `LoggerManager`, `get_logger()`, `setup_logging()`, `set_log_level()`, `get_log_file_path()`, `enable_debug_logging()`, `enable_verbose_logging()`, `enable_quiet_logging()`, `_manager` | **RENAME** → `_logging.py` (content unchanged, deferred singleton refactor) |
| `progress.py` | `ProgressBar` (lines 17–95), `progress_bar()` (98–135), `create_progress_bar()` (137–159), `ReportProgress` (162–208) | **TRANSFORM** → `_progress.py`: delete lines 17–95 + 137–208; keep lines 98–135 only |
| `MyDumper.py` | (file does NOT EXIST — confirmed by Read tool returning `File does not exist`) | Nothing to do |

> **`MyDumper.py` finding:** The file listed in STRUCTURE.md as `MyDumper.py` **does not exist** in the current codebase. `git ls-files` would confirm but the Read tool returned "File does not exist". This means D-06 only requires consolidating `YAMLDumper` from `eq_odoo_connection.py` into `_yaml_dumper.py` — there is no legacy `MyDumper.py` to rename. [VERIFIED: direct Read tool probe]

---

## Circular Import — Exact Trace

**Import chain that causes the cycle:**

```
# odoo_report_helper/odoo_connection.py  LINE 9
from odoo_fast_report_mapper.lang_utils import build_name_search_domain
```

This is the ONLY cross-package upward import. It causes a circular dependency because:

```
odoo_fast_report_mapper/eq_odoo_connection.py:11
    from odoo_report_helper.odoo_connection import OdooConnection
        ↳ triggers odoo_report_helper/odoo_connection.py
            ↳ line 9: from odoo_fast_report_mapper.lang_utils import ...
                ↳ triggers odoo_fast_report_mapper/__init__.py (maybe)
                    ↳ imports eq_odoo_connection (already being imported)
                    → ImportError / circular import
```

**Why it only fails in isolation:**
When `pytest tests/` runs the full suite, Python's import machinery loads `odoo_fast_report_mapper` first (via some other test file's import), caching it in `sys.modules`. By the time `test_odoo_connection.py` triggers `from odoo_report_helper.odoo_connection import OdooConnection`, the `odoo_fast_report_mapper.lang_utils` module is already in `sys.modules` and the cycle resolves. Running `pytest tests/test_odoo_connection.py` in isolation starts with an empty `sys.modules`, hits the cycle at first import, and fails.

**Fix verification (D-08):**
After the merge, `build_name_search_domain` lives in `odoo_fast_report_mapper/_lang_utils.py`. The merged `OdooConnection` imports it as `from ._lang_utils import build_name_search_domain`. There is no second package, no upward dependency, and no cycle possible. [VERIFIED: traced from source]

**All other cross-package imports (every one eliminated by the merge):**

| File | Import | Resolution |
|------|--------|-----------|
| `eq_odoo_connection.py:11` | `from odoo_report_helper.odoo_connection import OdooConnection` | Eliminated — merged into `_connection.py` |
| `eq_report.py:4` | `from odoo_report_helper.report import Report` | Eliminated — `EqReport` becomes standalone `Report` |
| `eq_utils.py:9` | `import odoo_report_helper.exceptions as exceptions` | Eliminated — `_exceptions.py` is internal |
| `eq_utils.py:10` | `import odoo_report_helper.utils as utils` | Eliminated — `_utils.py` absorbs those functions |

---

## Test-to-Module Mapping

### Current State (12 test files, ~369 tests)

| Test File | Module Under Test | Circular Import Issue? | Post-Phase-1 Fate |
|-----------|------------------|----------------------|-------------------|
| `test_odoo_connection.py` | `odoo_report_helper/odoo_connection.py` (base class) | YES — fails in isolation | **MERGE** → `test_connection.py` (absorb unique base-only tests, discard dead-path tests) |
| `test_eq_odoo_connection.py` | `odoo_fast_report_mapper/eq_odoo_connection.py` | YES (transitively) | **MERGE** → `test_connection.py` (primary source — Eq-version is canonical) |
| `test_report.py` | `odoo_report_helper/report.py` (base class) | Indirect | **MERGE** → `test_report.py` (absorb base-only behavior tests) |
| `test_eq_report.py` | `odoo_fast_report_mapper/eq_report.py` | No | **MERGE** → `test_report.py` (primary source) |
| `test_helper_utils.py` | `odoo_report_helper/utils.py` | YES — noted in TESTING.md | **MERGE** → `test_utils.py` (primary source since all functions move to `_utils.py`) |
| `test_eq_utils.py` | `odoo_fast_report_mapper/eq_utils.py` | No | **MERGE** → `test_utils.py` (primary source) |
| `test_exceptions.py` | `odoo_report_helper/exceptions.py` | No | **RENAME** → `test_exceptions.py` (update import path: `from odoo_fast_report_mapper._exceptions import ...` or via public `__init__`) |
| `test_lang_utils.py` | `odoo_fast_report_mapper/lang_utils.py` | No | **RENAME** → `test_lang_utils.py` (update import: `from odoo_fast_report_mapper._lang_utils import ...`) |
| `test_logging.py` | `odoo_fast_report_mapper/logging_config.py` | No | **RENAME** → `test_logging.py` (update import: `from odoo_fast_report_mapper._logging import ...`) |
| `test_progress.py` | `odoo_fast_report_mapper/progress.py` | No | **CUT** → `test_progress.py` ~30 LOC (remove dead API tests; keep `TestProgressBarFunction`) |
| `test_cli.py` | `odoo_fast_report_mapper/odoo_fast_report_mapper.py` | No | **KEEP** → `test_cli.py` (update import path if CLI module renamed) |
| `conftest.py` | Shared fixtures | No | **UPDATE** — mock patch paths change: `odoo_report_helper.utils.ODOO` → `odoo_fast_report_mapper._utils.ODOO` |

### Tests to Delete (Dead API)

| Test Class | Test Count | Covers | Action |
|------------|-----------|--------|--------|
| `TestProgressBar` | 11 functions (lines 27–113) | `ProgressBar` class | DELETE |
| `TestCreateProgressBar` | 4 functions (lines 152–188) | `create_progress_bar()` factory | DELETE |
| `TestReportProgress` | 6 functions (lines 195–249) | `ReportProgress` class | DELETE |

`TestProgressBarFunction` (4 functions, lines 120–145) covers `progress_bar()` and **SURVIVES** intact.

Post-delete `test_progress.py` will contain:
- ~12 lines of imports/setup
- `TestProgressBarFunction` class (~20 lines, 4 tests)
- Total: ~32 lines (matches D-12 target of ~30 LOC)

### Dead API in `progress.py` — Exact Line Counts

| Symbol | Lines | LOC | Action |
|--------|-------|-----|--------|
| `ProgressBar` class | 17–95 | 79 | DELETE |
| `progress_bar()` function | 98–135 | 38 | KEEP → `_progress.py` |
| `create_progress_bar()` factory | 137–159 | 23 | DELETE |
| `ReportProgress` class | 162–208 | 47 | DELETE |
| **Deleted total** | — | **149 LOC** | — |
| **Surviving total** | — | **38 LOC** (+ file header ~9 lines) | **47 LOC → `_progress.py`** |

---

## `super()` Call Inventory

Every `super()` call in the extension layer that disappears after the merge:

| File | Line | Current Call | After Merge |
|------|------|-------------|-------------|
| `eq_odoo_connection.py:40` | `super().__init__(url, port, *args, **kwargs)` | Calls `OdooConnection.__init__` | INLINE: `_connection.py` constructor absorbs the full merged logic from both inits |
| `eq_odoo_connection.py:24` | `super().increase_indent(flow, False)` in `YAMLDumper` | Calls `yaml.Dumper.increase_indent` | KEEP — `YAMLDumper` still extends `yaml.Dumper`, this super() is NOT eliminated |

**Note:** `EqReport` does NOT call `super().__init__()` (ARCHITECTURE.md anti-pattern). This means the merge of Report is simpler — the Eq-`__init__` becomes the sole constructor; no super() to remove.

---

## Entry Point Safety

**Current `pyproject.toml` lines 43–45:**

```toml
[project.scripts]
odoo-fast-report-mapper = "odoo_fast_report_mapper.odoo_fast_report_mapper:start_odoo_fast_report_mapper"
odoo-fr-mapper = "odoo_fast_report_mapper.odoo_fast_report_mapper:start_odoo_fast_report_mapper"
```

**If `odoo_fast_report_mapper.py` is renamed to `_cli.py` (D-03 discretion):**

```toml
[project.scripts]
odoo-fast-report-mapper = "odoo_fast_report_mapper._cli:start_odoo_fast_report_mapper"
odoo-fr-mapper = "odoo_fast_report_mapper._cli:start_odoo_fast_report_mapper"
```

The function name `start_odoo_fast_report_mapper` must not change — it is the entry point symbol. The CLI file imports are `from . import eq_utils` (→ `from . import _utils`), `from .__version__ import ...` (unchanged), and `from .logging_config import ...` (→ `from ._logging import ...`).

**CLI file internal imports that need updating after consolidation:**

| Current import in `odoo_fast_report_mapper.py` | After Phase 1 |
|------------------------------------------------|---------------|
| `from . import eq_utils` | `from . import _utils` (or keep old name in `_utils.py` as alias) |
| `from .__version__ import ...` | Unchanged |
| `from .logging_config import get_logger, setup_logging` | `from ._logging import get_logger, setup_logging` |

---

## Build System Impact

**Current `pyproject.toml` line 68:**

```toml
[tool.setuptools.packages.find]
include = ["odoo_fast_report_mapper*", "odoo_report_helper*"]
```

**After Phase 1:**

```toml
[tool.setuptools.packages.find]
include = ["odoo_fast_report_mapper*"]
```

**Additional `pyproject.toml` changes:**

| Section | Current | After Phase 1 |
|---------|---------|---------------|
| `[tool.setuptools.packages.find] include` | `["odoo_fast_report_mapper*", "odoo_report_helper*"]` | `["odoo_fast_report_mapper*"]` |
| `[tool.coverage.run] source` | `["odoo_fast_report_mapper", "odoo_report_helper"]` | `["odoo_fast_report_mapper"]` |
| `[tool.ruff.lint.isort] known-first-party` | `["odoo_fast_report_mapper", "odoo_report_helper"]` | `["odoo_fast_report_mapper"]` |
| `[tool.mypy]` | unchanged | unchanged (Phase 2 adds strict mode) |

---

## Mock Patch Path Updates (Critical for Tests)

All `@patch(...)` and `with patch(...)` decorators in the test suite reference the old import paths. These MUST be updated when the code moves.

| Current Patch Target | After Phase 1 | Affected Test Files |
|---------------------|---------------|---------------------|
| `"odoo_report_helper.odoo_connection.utils.prepare_connection"` | `"odoo_fast_report_mapper._connection.utils.prepare_connection"` or (if inlined) `"odoo_fast_report_mapper._connection.ODOO"` | `test_connection.py`, `test_odoo_connection.py` (to be merged) |
| `"odoo_report_helper.utils.ODOO"` | `"odoo_fast_report_mapper._utils.ODOO"` | `conftest.py`, `test_helper_utils.py` (to be merged) |
| `"odoo_report_helper.odoo_connection.utils.prepare_connection"` in `test_eq_odoo_connection.py:33` | `"odoo_fast_report_mapper._connection.utils.prepare_connection"` | `test_connection.py` |
| `"odoo_fast_report_mapper.progress.sys.stdout"` | `"odoo_fast_report_mapper._progress.sys.stdout"` | `test_progress.py` (only for surviving `TestProgressBarFunction`) |

> **Key insight:** `prepare_connection` in the merged `_connection.py` will still be a helper function from `_utils.py`. The patch target must reference where `prepare_connection` is **used** (imported into `_connection.py`), not where it is defined. After consolidation the patch target is `"odoo_fast_report_mapper._connection.prepare_connection"`.

---

## File-by-File Action Map

### Files to CREATE (new)

| New File | Source Content | Notes |
|----------|---------------|-------|
| `odoo_fast_report_mapper/_connection.py` | Base: `odoo_report_helper/odoo_connection.py` + Eq: `eq_odoo_connection.py` | Merged class `OdooConnection`; `YAMLDumper` extracted to `_yaml_dumper.py` |
| `odoo_fast_report_mapper/_report.py` | Base: `odoo_report_helper/report.py` + Eq: `eq_report.py` | Merged class `Report` |
| `odoo_fast_report_mapper/_utils.py` | `odoo_report_helper/utils.py` + `eq_utils.py` | All factory/loader functions unified |
| `odoo_fast_report_mapper/_exceptions.py` | `odoo_report_helper/exceptions.py` | Selective — all three symbols migrate |
| `odoo_fast_report_mapper/_lang_utils.py` | `lang_utils.py` (rename) | Content identical to current `lang_utils.py` |
| `odoo_fast_report_mapper/_logging.py` | `logging_config.py` (rename) | Content identical; only internal ref updates |
| `odoo_fast_report_mapper/_progress.py` | `progress.py` lines 1–15 + 98–135 | Stripped to `progress_bar()` only |
| `odoo_fast_report_mapper/_yaml_dumper.py` | `YAMLDumper` from `eq_odoo_connection.py:20–24` | Single class, moved from connection file |

### Files to REWRITE (changed content)

| File | Change |
|------|--------|
| `odoo_fast_report_mapper/__init__.py` | New public API: `OdooConnection`, `Report`, `create_connection_from_env`, exceptions |
| `odoo_fast_report_mapper/odoo_fast_report_mapper.py` | Update all `eq_*` imports to `_*` names; update `from .logging_config import` to `from ._logging import` |
| `pyproject.toml` | Remove `odoo_report_helper*` from `packages.find`, `coverage.run.source`, `ruff.isort.known-first-party` |

### Files to DELETE (source files)

| File to Delete | When | Prerequisite |
|---------------|------|-------------|
| `odoo_report_helper/__init__.py` | Wave 5 | All imports updated |
| `odoo_report_helper/odoo_connection.py` | Wave 5 | Merged `_connection.py` green |
| `odoo_report_helper/report.py` | Wave 5 | Merged `_report.py` green |
| `odoo_report_helper/utils.py` | Wave 5 | Merged `_utils.py` green |
| `odoo_report_helper/exceptions.py` | Wave 5 | Merged `_exceptions.py` green |
| `odoo_fast_report_mapper/eq_odoo_connection.py` | Wave 5 | `_connection.py` exists |
| `odoo_fast_report_mapper/eq_report.py` | Wave 5 | `_report.py` exists |
| `odoo_fast_report_mapper/eq_utils.py` | Wave 5 | `_utils.py` exists |
| `odoo_fast_report_mapper/lang_utils.py` | Wave 5 | `_lang_utils.py` exists |
| `odoo_fast_report_mapper/logging_config.py` | Wave 5 | `_logging.py` exists |
| `odoo_fast_report_mapper/progress.py` | Wave 5 | `_progress.py` exists |

### Test Files to CREATE/MERGE/UPDATE

| Action | Old File(s) | New File | Notes |
|--------|-------------|----------|-------|
| MERGE | `test_odoo_connection.py` + `test_eq_odoo_connection.py` | `tests/test_connection.py` | Eq-version tests are primary; absorb unique base tests |
| MERGE | `test_report.py` + `test_eq_report.py` | `tests/test_report.py` | Eq-version tests are primary; `test_eq_report.py` overwrites existing `test_report.py` |
| MERGE | `test_helper_utils.py` + `test_eq_utils.py` | `tests/test_utils.py` | All `_utils.py` functions in one file |
| UPDATE | `test_exceptions.py` | `tests/test_exceptions.py` | Update import path only |
| RENAME | `test_lang_utils.py` | `tests/test_lang_utils.py` | Update import path only |
| RENAME | `test_logging.py` | `tests/test_logging.py` | Update import path only |
| CUT | `test_progress.py` | `tests/test_progress.py` | Remove dead API tests; keep `TestProgressBarFunction` |
| UPDATE | `test_cli.py` | `tests/test_cli.py` | Update import paths |
| UPDATE | `conftest.py` | `tests/conftest.py` | Update `mock_odoorpc` patch path |

---

## Recommended Order of Operations (Safe Refactor Sequence)

The guiding principle: **tests must be green at every git commit**. This is achieved by creating new files before deleting old ones, updating imports in a specific order, and verifying with `uv run pytest tests/` after each wave.

### Wave 0: Coverage Baseline (D-13)

Before any code changes:

```bash
uv run pytest --cov --cov-report=term-missing --cov-report=html
# Save output to .planning/phases/01-package-consolidation/coverage-baseline.txt
```

Commit: `[ADD] docs(01): record coverage baseline before Phase 1 consolidation`

### Wave 1: Standalone Utilities (no class dependencies)

Actions (all in `odoo_fast_report_mapper/`):

1. Create `_exceptions.py` — copy from `odoo_report_helper/exceptions.py` (identical content)
2. Create `_lang_utils.py` — copy from `lang_utils.py` (identical content)
3. Create `_logging.py` — copy from `logging_config.py` (identical content)
4. Create `_yaml_dumper.py` — extract `YAMLDumper` from `eq_odoo_connection.py:20–24`
5. Create `_progress.py` — copy lines 1–15 (header/imports) + 98–135 (`progress_bar()`) from `progress.py`

**Leave old files in place.** At this point there are two copies of each; tests still import from old paths. Verify: `uv run pytest tests/` — must be green (no imports changed yet).

Commit: `[ADD] chore(01): create private submodules (exceptions, lang_utils, logging, yaml_dumper, progress)`

### Wave 2: Merge `OdooConnection`

1. Create `odoo_fast_report_mapper/_connection.py`:
   - Start with Eq-`EqOdooConnection` as the base
   - Rename class to `OdooConnection`
   - Remove `from odoo_report_helper.odoo_connection import OdooConnection` and `class EqOdooConnection(OdooConnection)`
   - Inline from base: `__repr__`, `__str__`, `login`, `_get_fast_report_ids`, `check_module`
   - Remove `super().__init__(url, port, *args, **kwargs)` — the `__init__` body merges the relevant base fields (`username`, `password`, `database`, `version`, `connection`)
   - Update all internal imports: `from .lang_utils import ...` → `from ._lang_utils import ...`, `from .logging_config import ...` → `from ._logging import ...`, `from .progress import progress_bar` → `from ._progress import progress_bar`, `from ._yaml_dumper import YAMLDumper`
   - Remove `from odoo_report_helper.odoo_connection import OdooConnection` (no longer needed)

2. Update `_utils.py` (create from `eq_utils.py`): replace `from odoo_report_helper.*` imports with internal `from ._exceptions import ...`, `from ._utils import prepare_connection, parse_yaml_folder, self_clean`; replace `eq_odoo_connection.EqOdooConnection(...)` instantiation with `OdooConnection(...)` from `._connection`; update factory return type annotation.

3. Run `uv run pytest tests/` — must be green (old files still exist; imports in tests still work).

Commit: `[ADD] refactor(01): create merged _connection.py and _utils.py`

### Wave 3: Merge `Report`

1. Create `odoo_fast_report_mapper/_report.py`:
   - Start with `EqReport` as the base
   - Rename class to `Report`
   - Remove `from odoo_report_helper.report import Report` and `class EqReport(Report)`
   - Add the three base-only methods `add_fields`, `add_calculated_fields`, `add_dependencies` as direct methods
   - Update import: `from .lang_utils import get_primary_lang` → `from ._lang_utils import get_primary_lang`

2. Run `uv run pytest tests/` — must be green.

Commit: `[ADD] refactor(01): create merged _report.py`

### Wave 4: Remove Dead Progress API

1. In `odoo_fast_report_mapper/progress.py` (the OLD file, still live):
   - Delete lines 17–95 (`ProgressBar` class)
   - Delete lines 137–208 (`create_progress_bar` and `ReportProgress`)
   - Keep lines 1–15 (header/imports minus unused ones) and 98–135 (`progress_bar()`)

   **Alternative:** At this point `_progress.py` already exists. Simply update `progress.py` to re-export from `_progress.py` as a one-liner shim, then update tests immediately. But the cleanest approach is to directly edit `progress.py` in-place to match `_progress.py`.

2. In `test_progress.py`:
   - Delete `TestProgressBar` (lines 27–113)
   - Delete `TestCreateProgressBar` (lines 152–188)
   - Delete `TestReportProgress` (lines 195–249)
   - Update import to remove `ProgressBar`, `ReportProgress`, `create_progress_bar`
   - Keep `TestProgressBarFunction` intact

3. Run `uv run pytest tests/` — must be green with the removal.

Commit: `[CHG] refactor(01): remove dead progress API (ProgressBar, create_progress_bar, ReportProgress) — DEAD-01/02/03`

### Wave 5: Switch Imports and Delete Old Structures

This is the biggest atomic step. Recommended sub-order within Wave 5:

1. Update `__init__.py` to new public API:
   ```python
   from ._connection import OdooConnection
   from ._report import Report
   from ._utils import create_connection_from_env
   from ._exceptions import OdooConnectionError, PathDoesNotExistError, PathDoesNotExitError
   ```

2. Update CLI file (`odoo_fast_report_mapper.py` or `_cli.py`): change all `from . import eq_utils` → `from . import _utils`; `from .logging_config import` → `from ._logging import`.

3. Merge test files (see Test File Merge table above). This is the biggest test-editing sub-step.

4. Update `conftest.py` mock patch paths.

5. Run `uv run pytest tests/` — must be green before proceeding to deletions.

6. Delete old source files (all listed in "Files to DELETE" table above).

7. Delete `odoo_report_helper/` directory entirely.

8. Update `pyproject.toml` (`packages.find`, `coverage.run.source`, `ruff.isort`).

9. Run `uv run pytest tests/` — must be green.

10. Run `uv run ruff check . && uv run ruff format --check .` — must be clean.

11. Generate post-refactor coverage: `uv run pytest --cov --cov-report=term-missing` and diff against Wave 0 baseline.

Commit: `[CHG] refactor(01): switch imports to private submodules, merge test files, delete odoo_report_helper/ — CONS-01/02/03/04`

### Wave 6: Rename CLI Module (Optional — D-03 Discretion)

If the planner decides to rename `odoo_fast_report_mapper.py` → `_cli.py`:

1. Rename file
2. Update `pyproject.toml` entry points
3. Run `uv run pytest tests/test_cli.py` in isolation — must pass

Commit: `[CHG] chore(01): rename CLI module to _cli.py for naming consistency`

---

## Risk Register

### R-01: Merged `OdooConnection.__init__` parameter order

**Risk:** `EqOdooConnection.__init__` takes `(language, collect_yaml, disable_qweb, workflow, url, port, *args, **kwargs)` and calls `super().__init__(url, port, *args, **kwargs)`. The base `OdooConnection.__init__` takes `(url, port, username, password, database)`. After merge, the constructor signature must be explicit and comprehensive. The `*args` from the Eq class passes `(username, password, database)` positionally to the base.

**Impact if wrong:** `OdooConnection` instances created with wrong argument order → AttributeError at runtime on `self.username` etc.

**Mitigation:** In the merged `__init__`, make `username`, `password`, `database` explicit keyword arguments (not `*args`). Grep all call sites in tests: `_make_connection(...)` helper in `test_eq_odoo_connection.py:21–52` and `create_connection_from_env()` in `eq_utils.py:341–352`. Verify the factory still passes correct arguments after rename.

### R-02: `conftest.py` mock patch path

**Risk:** The core fixture `mock_odoorpc` patches `"odoo_report_helper.utils.ODOO"`. After the merge, `ODOO` lives in `odoo_fast_report_mapper/_utils.py`. If the patch target is not updated, ALL tests using `mock_odoorpc` and `mock_odoo_env` fixtures will call the real `ODOO()` constructor (network connection) and fail.

**Impact if wrong:** Entire test suite breaks on any test that instantiates `OdooConnection`.

**Mitigation:** Update `conftest.py` line by line. The new patch target is `"odoo_fast_report_mapper._utils.ODOO"`. Also check every `@patch("odoo_report_helper.odoo_connection.utils.prepare_connection")` — there are at least 2 in `test_odoo_connection.py` and 1 in `test_eq_odoo_connection.py:33`.

### R-03: `build_name_search_domain` called from base `set_calculated_fields`

**Risk:** The base `odoo_report_helper/odoo_connection.py:133` calls `build_name_search_domain(report_name)` where `report_name` is a string (`entry_name: str` on the base `Report`). The Eq-version also calls `build_name_search_domain(report_name)` where `report_name` is a dict. After the merge, only the Eq-version of `set_calculated_fields` survives — it expects a dict. Tests for the base version's string-path are deleted. No behavioral regression because the base path was dead in production.

**Impact if wrong:** None (base path is dead). Verified: all production calls go through `EqOdooConnection.set_calculated_fields` with a dict.

**Mitigation:** No action needed. Document that `build_name_search_domain` in `_lang_utils.py` now only receives dicts.

### R-04: `EqReport` not calling `super().__init__()` — inert but must stay inert

**Risk:** ARCHITECTURE.md notes that `EqReport.__init__` does NOT call `super().__init__()` — all attributes are set manually. After the merge, the new `Report.__init__` is the Eq-version. The old base-`Report.__init__` (which had its own attribute assignments) is deleted. This is the desired state, but any future developer unfamiliar with this history might try to add `super().__init__()` and hit surprises if the signatures diverge.

**Impact if wrong:** None in Phase 1. Risk is future regression.

**Mitigation:** Add a brief comment in `_report.py.__init__` noting the intentional design.

### R-05: `_search_report_v13` — must not be touched

**Risk:** `EqOdooConnection._search_report_v13` (lines 119–127) handles Odoo v13–v16 company filtering. It is flagged as FRAGILE in CONCERNS.md. It moves to `_connection.py` unchanged.

**Impact if wrong:** v13–v16 Odoo instances fail to find reports by company.

**Mitigation:** Copy verbatim — zero edits to this method's body.

### R-06: Test count drop accounting

**Risk:** D-13 requires coverage parity but removing dead-code tests WILL reduce the test count. The 369-test baseline minus the 21 deleted test functions (11 `TestProgressBar` + 4 `TestCreateProgressBar` + 6 `TestReportProgress`) = **~348 tests** expected post-Phase-1. Any additional drop beyond these 21 is a gap.

**Mitigation:** Record exact pre-Phase-1 test count: `uv run pytest --collect-only -q | tail -5`. Post-Phase-1, verify count is exactly 348 (±1 for parametrize edge cases). Any additional reduction triggers investigation.

### R-07: `MyDumper.py` does not exist

**Risk:** STRUCTURE.md mentions `MyDumper.py` as a file to rename. The file does NOT exist in the current codebase (confirmed by Read tool probe). D-06 is partially a non-event.

**Impact if wrong:** If a plan task says "rename `MyDumper.py` → `_yaml_dumper.py`", it will fail because the source does not exist.

**Mitigation:** D-06 only requires extracting `YAMLDumper` from `eq_odoo_connection.py:20–24` into a new `_yaml_dumper.py`. There is no `MyDumper.py` file to handle.

### R-08: `LOCALE_TO_LEGACY` in `lang_utils.py`

**Risk:** `lang_utils.py` line 19 has `LOCALE_TO_LEGACY` computed at import time but never called (CONCERNS.md P-07, fixed in v0.9.7). After verifying, the current `lang_utils.py` does NOT contain `LOCALE_TO_LEGACY` — it was already fixed. The content is clean: only `LEGACY_LANG_MAP`, five functions. No risk.

**Mitigation:** None needed. Verified by reading `lang_utils.py`.

### R-09: `_utils.py` size — split threshold

**Risk:** `eq_utils.py` (376 lines) + the relevant portions of `odoo_report_helper/utils.py` (~121 lines) = potentially ~450–480 LOC in `_utils.py`. D-03 discretion allows splitting at ~300 LOC.

**Mitigation:** Create `_utils.py` as a single file first. If it exceeds 400 LOC, split into `_env_loader.py` (env/dotenv parsing) and `_yaml_loader.py` (parse_yaml_folder, etc.) as a follow-up within Phase 1. Not a blocking concern.

### R-10: Phase 1.1 conflict guard

**Risk:** Phase 1.1 fixes BUG-01 (`add_field_to_dictionary` unguarded `model_id[0]`), BUG-02 (`self_clean()` destroys params), BUG-03 (`check_dependencies` return type contract), etc. Phase 1 must not accidentally "fix" these bugs by changing behavior — it is structural only.

**Mitigation:** During merge, copy the relevant methods verbatim without any logic changes. Specifically:
- `add_field_to_dictionary` (BUG-01): copy as-is, including the unguarded `model_id[0]` at line 601
- `self_clean()` in `_utils.py` (BUG-02): copy as-is with the broken `list(dict.fromkeys(value))` behavior
- `check_dependencies` (BUG-03): copy the Eq-version as-is with the `(bool, list)` return type

These will be fixed in Phase 1.1 after the consolidated structure is in place.

---

## Coverage Baseline Strategy (D-13)

### Step 1: Pre-Phase-1 Baseline

```bash
# On develop branch, before any Wave 1 changes
uv run pytest --cov --cov-report=term-missing --cov-report=json -q 2>&1 | tee .planning/phases/01-package-consolidation/coverage-baseline.txt
cp coverage.json .planning/phases/01-package-consolidation/coverage-baseline.json
```

Commit the two baseline files.

### Step 2: Post-Phase-1 Comparison

```bash
# After Wave 5 is complete and tests are green
uv run pytest --cov --cov-report=term-missing --cov-report=json -q 2>&1 | tee .planning/phases/01-package-consolidation/coverage-post.txt
cp coverage.json .planning/phases/01-package-consolidation/coverage-post.json
```

### Step 3: Diff Analysis

Coverage is acceptable to drop for:
- `odoo_report_helper/*` (entire package deleted — 0% expected, was some %)
- `odoo_fast_report_mapper/progress.py` (149 LOC deleted)
- Tests for base-only methods (`base map_reports`, `base check_dependencies`, `base set_calculated_fields`)

Coverage must NOT drop for:
- `odoo_fast_report_mapper/_connection.py` vs current `eq_odoo_connection.py`
- `odoo_fast_report_mapper/_report.py` vs current `eq_report.py`
- `odoo_fast_report_mapper/_utils.py` vs current `eq_utils.py`
- `odoo_fast_report_mapper/_lang_utils.py` vs current `lang_utils.py`
- `odoo_fast_report_mapper/_logging.py` vs current `logging_config.py`

**Key coverage threshold:** After Phase 1, the `fail_under = 60` in `pyproject.toml` must still pass. The expected post-Phase-1 coverage should be HIGHER than pre-Phase-1 (dead base-class code that was hard to cover is removed).

---

## Validation Architecture

### Test Framework

| Property | Value |
|----------|-------|
| Framework | pytest >= 8.0 |
| Config file | `pyproject.toml` `[tool.pytest.ini_options]` |
| Quick run command | `uv run pytest tests/ -q` |
| Full suite command | `uv run pytest --cov --cov-report=term-missing` |

### Phase Requirements → Test Map

| Req ID | Behavior | Test Type | Automated Command | Notes |
|--------|----------|-----------|-------------------|-------|
| CONS-01 | `import odoo_report_helper` raises `ModuleNotFoundError` | smoke | `python -c "import odoo_report_helper"` (must fail) | Run after Wave 5 deletion |
| CONS-02 | `pytest tests/test_connection.py` alone passes | isolation | `uv run pytest tests/test_connection.py -v` | The primary Success Criterion #1 |
| CONS-02 | `pytest tests/test_utils.py` alone passes | isolation | `uv run pytest tests/test_utils.py -v` | All merged test files must be isolatable |
| CONS-03 | `from odoo_fast_report_mapper import OdooConnection` succeeds | smoke | `python -c "from odoo_fast_report_mapper import OdooConnection"` | Success Criterion #3 |
| CONS-04 | Full suite green | regression | `uv run pytest tests/ -q` | 348 tests expected |
| DEAD-01/02/03 | `from odoo_fast_report_mapper.progress import ProgressBar` raises `ImportError` | smoke | `python -c "from odoo_fast_report_mapper._progress import ProgressBar"` (must fail) | Success Criterion #4 |
| DEAD-01/02/03 | `from odoo_fast_report_mapper import ProgressBar` raises `AttributeError` | smoke | `python -c "from odoo_fast_report_mapper import ProgressBar"` (must fail) | |

### Success Criteria Validation Commands (from ROADMAP.md)

```bash
# SC-1: test_connection.py runs standalone
uv run pytest tests/test_connection.py -v

# SC-2: odoo_report_helper is gone
python -c "import odoo_report_helper" && echo "FAIL" || echo "PASS"

# SC-3: OdooConnection importable from public API
python -c "from odoo_fast_report_mapper import OdooConnection; print('PASS')"

# SC-4: ProgressBar is gone
python -c "from odoo_fast_report_mapper._progress import ProgressBar" && echo "FAIL" || echo "PASS"

# SC-5: All remaining tests pass
uv run pytest tests/ -q --tb=short
```

---

## Architecture Pattern

### Post-Phase-1 System Diagram

```
odoo-fast-report-mapper (single package)
│
├── odoo_fast_report_mapper/
│   ├── __init__.py            ← public API: OdooConnection, Report, create_connection_from_env, exceptions
│   ├── __version__.py         ← version metadata (unchanged)
│   ├── odoo_fast_report_mapper.py  ← CLI entry (or _cli.py)
│   ├── _connection.py         ← OdooConnection (merged from base + Eq)
│   ├── _report.py             ← Report (merged from base + Eq)
│   ├── _utils.py              ← all factories, loaders, helpers
│   ├── _exceptions.py         ← OdooConnectionError, PathDoesNotExistError
│   ├── _lang_utils.py         ← normalize_*, get_primary_lang, build_name_search_domain
│   ├── _logging.py            ← LoggerManager singleton, get_logger()
│   ├── _yaml_dumper.py        ← YAMLDumper(yaml.Dumper)
│   └── _progress.py           ← progress_bar() context manager only
│
└── tests/
    ├── conftest.py            ← fixtures (mock patch updated)
    ├── test_connection.py     ← merged OdooConnection tests (~independent)
    ├── test_report.py         ← merged Report tests
    ├── test_utils.py          ← merged utils tests
    ├── test_exceptions.py     ← OdooConnectionError, PathDoesNotExistError
    ├── test_lang_utils.py     ← language normalization tests
    ├── test_logging.py        ← LoggerManager tests
    ├── test_progress.py       ← progress_bar() only (~30 LOC)
    └── test_cli.py            ← CLI entry point tests
```

**Data flow (unchanged from pre-Phase-1):**
```
CLI (odoo_fast_report_mapper.py)
    → create_connection_from_env() [_utils.py]
        → OdooConnection.__init__() [_connection.py]
            → prepare_connection() [_utils.py]
    → collect_all_reports() [_utils.py]
        → parse_yaml_folder() [_utils.py]
        → build_reports_from_yaml_objects() [_utils.py]
            → Report() [_report.py]
    → connection.map_reports(reports) [_connection.py]
        → _create_or_update_report() [_connection.py]
        → _set_report_translations() [_connection.py]
        → _map_report_fields() [_connection.py]
        → _write_field_mappings() [_connection.py]
```

---

## Project Constraints (from CLAUDE.md)

| Directive | Impact on Phase 1 |
|-----------|-------------------|
| Use UV (`uv run pytest`, `uv pip install`) not pip | All test commands use `uv run pytest` |
| Commit prefixes `[ADD]`/`[CHG]`/`[FIX]` | Wave commits use `[CHG] refactor(01): ...` |
| `pyproject.toml` is single source of truth for dependencies | No `requirements.txt` created |
| English code/comments, German communication | All new module docstrings in English |
| `fail_under = 60` in pytest coverage | Must verify after Phase 1 |
| `uv build` must produce wheel + sdist without errors | Verify after `packages.find` change |

---

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | `MyDumper.py` does not exist in the current codebase | File-by-File Action Map | D-06 rename task will fail if the file somehow exists in a branch not reflected in HEAD |
| A2 | The `_loggers` instance attribute in `LoggerManager.__init__:100` is an instance attribute (not class-level), meaning the CONCERNS.md W-05 issue was already partially fixed in v0.9.7.3 | Fragile Areas | The singleton reset in tests may still be fragile; check test_logging.py fixtures before touching |
| A3 | Test count is exactly 369 before Phase 1 | Risk Register R-06 | Expected post-Phase-1 count formula would be wrong |

---

## Open Questions (RESOLVED)

All three open questions were answered by planner decisions during PLAN.md creation.

1. **CLI module rename decision** — RESOLVED
   - Decision: Include the rename in Phase 1 (Plan 01-05 Task 2, Wave 5).
   - Rationale: Trivially reversible, and `pyproject.toml [project.scripts]` is updated in the same atomic task. Both entry points (`odoo-fast-report-mapper` and `odoo-fr-mapper`) are verified via `--help` exit code 0.

2. **`_utils.py` size after merge** — RESOLVED
   - Decision: Keep `_utils.py` as a single file (~400–450 LOC). No split.
   - Rationale: Plan 01-03 Task 1 creates it as one module. Revisit only if v1.x linting complains.

3. **`add_fields` / `add_calculated_fields` / `add_dependencies` usage** — RESOLVED
   - Decision: Include all three methods in `_report.py` (Plan 01-04 Task 1).
   - Rationale: They are part of the public `Report` interface — included regardless of current test coverage.

---

## Environment Availability

This phase is code/file rename only. No external services, databases, or CLIs are required beyond what is already in the development environment.

| Dependency | Required By | Available | Notes |
|------------|------------|-----------|-------|
| Python >= 3.12 | All code | Assumed yes | `pyproject.toml` constraint |
| UV | Package management, test running | Assumed yes | Project uses UV throughout |
| pytest >= 8.0 | Test suite | In `pyproject.toml` dev deps | `uv run pytest` |
| tqdm | `_progress.py` | In `pyproject.toml` deps | Required dependency, not changing |

---

## Sources

### Primary (HIGH confidence)

All findings are `[VERIFIED: direct source-code inspection]` — every file was read directly from the repository.

- `odoo_report_helper/odoo_connection.py` — full read, line-by-line method inventory
- `odoo_report_helper/report.py` — full read
- `odoo_report_helper/utils.py` — full read
- `odoo_report_helper/exceptions.py` — full read
- `odoo_fast_report_mapper/eq_odoo_connection.py` — full read (805 lines)
- `odoo_fast_report_mapper/eq_report.py` — full read
- `odoo_fast_report_mapper/eq_utils.py` — full read (376 lines)
- `odoo_fast_report_mapper/lang_utils.py` — full read
- `odoo_fast_report_mapper/logging_config.py` — full read
- `odoo_fast_report_mapper/progress.py` — full read (208 lines)
- `odoo_fast_report_mapper/odoo_fast_report_mapper.py` — full read
- `odoo_fast_report_mapper/__init__.py` — full read
- `odoo_fast_report_mapper/__version__.py` — full read
- `tests/test_progress.py` — full read (249 lines)
- `tests/test_odoo_connection.py` — partial read (first 60 lines)
- `tests/test_eq_odoo_connection.py` — partial read (first 60 lines)
- `tests/conftest.py` — partial read (first 60 lines)
- `pyproject.toml` — full read
- `.planning/phases/01-package-consolidation/01-CONTEXT.md` — full read
- `.planning/REQUIREMENTS.md` — full read
- `.planning/codebase/STRUCTURE.md` — full read
- `.planning/codebase/ARCHITECTURE.md` — full read
- `.planning/codebase/CONCERNS.md` — full read
- `.planning/codebase/TESTING.md` — full read

### Probe Results

- `MyDumper.py` — Read returned "File does not exist" — file is absent from current HEAD [VERIFIED]

---

## Metadata

**Confidence breakdown:**
- Symbol inventories: HIGH — read directly from source files
- Circular import trace: HIGH — confirmed import chain in source
- Dead-code line counts: HIGH — counted directly from `progress.py`
- Test function counts: HIGH — counted from `test_progress.py`
- Recommended wave sequence: MEDIUM — logical ordering, but planner may adjust
- Post-merge test count (348): MEDIUM — assumes baseline is exactly 369 and deleted tests are exactly 21

**Research date:** 2026-05-28
**Valid until:** Stable — this is a pure structural analysis of static Python source. Valid as long as no code is committed to `develop` that changes the files inventoried above.
