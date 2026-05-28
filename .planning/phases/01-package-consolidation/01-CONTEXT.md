# Phase 1: Package Consolidation - Context

**Gathered:** 2026-05-28
**Status:** Ready for planning

<domain>
## Phase Boundary

Phase 1 consolidates the two-package layout (`odoo_report_helper/` + `odoo_fast_report_mapper/`) into a single package, eliminates the known circular import between them, and removes the dead-but-public progress-bar API (`ProgressBar`, `ReportProgress`, `create_progress_bar`).

After Phase 1:
- `odoo_report_helper/` is gone — `import odoo_report_helper` raises `ModuleNotFoundError`
- All production code lives in `odoo_fast_report_mapper/` as private (underscore-prefixed) submodules
- The Eq-prefixed classes (`EqOdooConnection`, `EqReport`) are merged into single classes (`OdooConnection`, `Report`)
- The dead progress-bar public API and its ~250 LOC of test coverage are removed
- Every test module runs in isolation (`pytest tests/test_connection.py` works standalone)
- The 369-test baseline (minus DEAD-01/02/03 removed tests) still passes

**In scope:** structural refactoring with breaking API changes (v1.0 major bump).
**Out of scope:** type-strict-mode (Phase 2), RPC-call-count reduction (Phase 3), MIGRATION.md content (Phase 4), correctness bug fixes (Phase 1.1).

</domain>

<decisions>
## Implementation Decisions

### Class Architecture (CONS-01, CONS-03)

- **D-01: Single merged class strategy.** The `OdooConnection` / `EqOdooConnection` inheritance hierarchy collapses into a single class `OdooConnection`. The Eq-prefixed name is dropped because there is no longer a base class to differentiate from. Same pattern for `Report` / `EqReport` → `Report` with dict-based `entry_name`.
  - **Why:** `EqOdooConnection` already overrides 5+ of the base's public methods (`map_reports`, `_search_report`, `check_dependencies`, `set_calculated_fields`). The base class is effectively dead code with only the Eq-derived production path actually used. Collapsing eliminates the override-smell that PROJECT.md flagged ("Vereinfacht das Mental Model, beseitigt Override-statt-Extend-Smell").
  - **How it applies:** The merged classes inherit the Eq-version of every overridden method. Base-only methods that are still called via `super()` (`login`, `authenticate`, `_is_odoo_version_at_least`) are inlined as methods on the merged class.

- **D-02: Factory stays in utils-module.** `create_connection_from_env()` (currently `odoo_fast_report_mapper/eq_utils.py:212`) moves to `_utils.py` and remains a free function returning `(OdooConnection, dotenv_path)`. Not a classmethod.
  - **Why:** Clean separation — class holds state, factory handles environment parsing. Easier to test without env mocks. Pattern carries forward from current state.

### Submodule Naming Convention

- **D-03: Private submodules with underscore prefix.** Production submodules are `_connection.py`, `_report.py`, `_utils.py`, `_exceptions.py`, `_lang_utils.py`, `_logging.py`, `_yaml_dumper.py`, `_progress.py`.
  - **Why:** Signals "this is implementation detail; the public API is what `__init__.py` re-exports." Aligns with REQUIREMENTS.md (CONS-01 explicitly proposes `_connection.py`, `_report.py`, `_utils.py`, `exceptions.py`). Gives the library freedom to refactor internal modules in v1.x without consumer impact.

- **D-04: Public API re-exports.** `__init__.py` re-exports: the two classes (`OdooConnection`, `Report`), the factory (`create_connection_from_env`), and the custom exception classes from `_exceptions.py`. Everything else is sub-path import only.
  - **Why:** Compact, dokumentierbar, deckt 99% des Konsumenten-Use-Case ab. Keeps the API contract small enough to honor across the v1.x line.

- **D-05: `progress.py` becomes `_progress.py` with only `progress_bar()` context manager.** The `ProgressBar`, `ReportProgress`, and `create_progress_bar` public classes/factories are removed (DEAD-01, DEAD-02, DEAD-03). The internal `progress_bar()` context manager (currently lines 98-135) survives as the only contents of `_progress.py` (~50 LOC, down from 208 LOC).
  - **Why:** REQUIREMENTS.md DEAD-01/02/03 explicitly require removal. The context manager remains because internal callers (mapping/testing/collect flows) still use it. Hard-break — no deprecation cycle; consumers use `tqdm` directly per MIGRATION.md (produced in Phase 4).

- **D-06: `MyDumper.py` is renamed to `_yaml_dumper.py`.** Legacy filename (`MyDumper.py`) cleaned up to match the snake_case underscore-prefix convention.
  - **Why:** Legacy code hygiene. STRUCTURE.md notes the existing `MyDumper.py` is already partially superseded by `YAMLDumper` in `eq_odoo_connection.py` — Phase 1 consolidates these too.

### Dead-Code Removal Scope (CONS-04)

- **D-07: Overridden base methods → Eq-version becomes canonical.** For every method that `EqOdooConnection` overrides (`map_reports`, `_search_report`, `check_dependencies`, `set_calculated_fields`, and others), the Eq-version is the production code; the base version is deleted with the base package.
  - **Why:** Production behavior has run on the Eq-version since at least v0.x. The base versions are only exercised by tests targeting the base class — those tests are removed alongside the base.

- **D-08: Non-overridden base methods → inline into merged `OdooConnection`.** `login`, `authenticate`, `_is_odoo_version_at_least`, and similar base-only helpers are moved as methods onto the merged `OdooConnection` class. `super()` calls are removed (there is no super class anymore). `build_name_search_domain` moves to `_lang_utils.py` as a module-level function.
  - **Why:** Eliminates the `super()` chain. `build_name_search_domain` is in `_lang_utils.py` because that's where its companions (`normalize_language_code`, etc.) live — moving it there also fixes the circular import (CONS-02).

- **D-09: v0.9.7 "Pflaster"-Fixes (B-01/B-03) implicitly removed with the base.** No separate handling. The Eq-version contains the production fix logic; whatever patches were added to the base in v0.9.7 vanish when the base package is deleted.
  - **Why:** Confirmed by code-review history — v0.9.7 patches were band-aids on already-dead base-class paths. PROJECT.md / REQUIREMENTS.md (CONS-04) explicitly say "entfernt den toten Code statt ihn zu reparieren."

- **D-10: `exceptions.py` → `_exceptions.py` (selective).** Custom exception classes from `odoo_report_helper/exceptions.py` move to `_exceptions.py`. Helper functions in `odoo_report_helper/utils.py` are migrated case-by-case into `_utils.py` — only the helpers actually still referenced by the merged `OdooConnection` / `Report` / Eq-utils survive.
  - **Why:** Errors and helpers serve different concerns; keeping them separate stays readable. Selective migration avoids carrying over unused helpers.

### Test Reorganization

- **D-11: Test files mirror the consolidated package.** Test files merge symmetrically:
  - `test_odoo_connection.py` + `test_eq_odoo_connection.py` → `test_connection.py`
  - `test_report.py` + `test_eq_report.py` → `test_report.py`
  - `test_helper_utils.py` + `test_eq_utils.py` → `test_utils.py`
  - Result: ~13 test files → ~9 test files. Each merged file inherits the Eq-version's coverage (production code path) and absorbs base-only edge-case tests that cover unique behavior.
  - **Why:** Each merged test file targets the merged class. Required for Success Criteria #1 (isolated execution via `pytest tests/test_connection.py`).

- **D-12: `test_progress.py` cut to ~30 LOC.** Tests for `ProgressBar`, `ReportProgress`, `create_progress_bar` are removed (DEAD-01/02/03 explicitly say "Tests entfernt"). Only the `progress_bar()` context manager tests survive.
  - **Why:** Consistent with the production-code removal. ~220 LOC of test coverage for removed APIs goes away — but those tests covered code that no longer exists.

- **D-13: Coverage parity verified via `pytest --cov` before/after diff.** Generate a baseline coverage report on `develop` before Phase 1, regenerate after Phase 1 completes, diff module-by-module. Coverage loss is only acceptable for explicitly-removed dead code (DEAD-01/02/03).
  - **Why:** Detects accidental coverage gaps from the merge (e.g., a base-only edge case that wasn't absorbed into the merged test). Cheaper and more semantic than counting tests.

### Claude's Discretion

- **Commit strategy** (atomic vs. mega-commit) — planner's call, but the [ADD]/[CHG]/[FIX] prefix convention from `~/gitbase/CLAUDE.md` applies.
- **Order of operations within the phase** (move-first vs. delete-first, etc.) — planner's call.
- **CLI module renaming** (`odoo_fast_report_mapper.py` → `_cli.py`) — recommended for naming consistency; planner can confirm or skip.
- **Sub-module file boundaries within `_utils.py`** — keep it one file, or split into `_env_loader.py` / `_yaml_loader.py` / etc. if it grows past ~300 LOC. Planner can apply judgment after seeing the actual line count.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Project & Milestone Context

- `.planning/PROJECT.md` — Project overview, milestone v1.0 scope, hard-break policy, `uv publish` manual-only constraint, key decisions table.
- `.planning/REQUIREMENTS.md` — Detailed requirements CONS-01 through CONS-04 and DEAD-01 through DEAD-03 with verification criteria.
- `.planning/ROADMAP.md` §"Phase 1: Package Consolidation" — Goal, depends-on, Success Criteria (the five must-be-TRUE statements).

### Codebase Maps

- `.planning/codebase/STRUCTURE.md` — Current two-package layout, file-by-file inventory, exact line numbers for `ProgressBar` (lines 17-95), `create_progress_bar` (lines 137-160), `ReportProgress` (lines 161-208), `progress_bar` context manager (lines 98-135).
- `.planning/codebase/ARCHITECTURE.md` — Key abstractions: which methods `EqOdooConnection` overrides vs. extends; the inheritance pattern for `Report` / `EqReport`; `create_connection_from_env()` factory at `eq_utils.py:212`.
- `.planning/codebase/CONCERNS.md` §"Circular Import" — Exact failure location: `odoo_report_helper/odoo_connection.py:9` imports `build_name_search_domain` from `odoo_fast_report_mapper/lang_utils.py`. Also documents `LoggerManager._loggers` class-level mutable dict as a separate fragile area (deferred).
- `.planning/codebase/TESTING.md` — 369-test baseline, test-file-to-module mapping.

### Phase 1.1 Dependency Context

- `.planning/BASELINE-REVIEW.md` — Correctness bugs (BUG-01..07) that Phase 1.1 will fix **in the consolidated structure**. Phase 1 must not introduce changes that conflict with these fixes; if a bug-fix target line moves during consolidation, Phase 1.1 plans will need to follow it.

### Historical Context

- `REVIEW.md` (repo root) — v0.9.6 code review that drove v0.9.7. Sections P-08/P-09 are the originating decision to defer `ProgressBar`/`ReportProgress`/`create_progress_bar` removal to v1.0 (= Phase 1).

### Build / Release Constraints

- `pyproject.toml` (repo root) — Two `[project.scripts]` entry points: `odoo-fast-report-mapper` and `odoo-fr-mapper` (both point to `start_odoo_fast_report_mapper`). Both must continue to resolve after consolidation. `[tool.setuptools.packages.find]` `include` list currently lists both packages; needs update.
- `~/gitbase/CLAUDE.md` §"Git Commit Prefix Rules" — Use `[ADD]` / `[CHG]` / `[FIX]` prefixes; release commits push to both `origin` (GitLab) and `upstream` (GitHub).

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets

- **`progress_bar()` context manager** (`odoo_fast_report_mapper/progress.py:98-135`) — The only progress code that survives. Used internally by mapping / testing / collect flows.
- **`build_name_search_domain` + `normalize_language_code`** (in `odoo_fast_report_mapper/lang_utils.py`) — Language-normalization utilities that the merged `OdooConnection` continues to depend on. Moving here breaks the circular import.
- **`YAMLDumper`** (currently inside `eq_odoo_connection.py`) — supersedes the legacy `MyDumper.py`. Consolidate both into `_yaml_dumper.py`.
- **`logging_config.LoggerManager`** (`odoo_fast_report_mapper/logging_config.py`) — Singleton, used everywhere. Move to `_logging.py`. The class-level mutable dict (`_loggers`) is documented as a separate concern in CONCERNS.md and is **deferred** beyond Phase 1.
- **`create_connection_from_env()`** (`odoo_fast_report_mapper/eq_utils.py:212`) — Returns `(EqOdooConnection, dotenv_path)`. After D-02, returns `(OdooConnection, dotenv_path)` — same shape, simpler type.

### Established Patterns

- **`super()` calls in Eq-extensions** — Several Eq-methods call `super().method(...)` then add Eq-specific behavior. After D-08, these `super()` calls disappear because the base methods are inlined.
- **Version-branching `_search_report_v13`** (`odoo_fast_report_mapper/eq_odoo_connection.py`) — Lives unchanged on the merged class; Odoo v13 support remains a hard constraint per PROJECT.md.
- **Two entry points** (`odoo-fast-report-mapper`, `odoo-fr-mapper`) both pointing to `start_odoo_fast_report_mapper` in `odoo_fast_report_mapper.py` — must continue working. Phase 1 may rename the CLI module file (e.g., `_cli.py`) but the entry-point function name must remain `start_odoo_fast_report_mapper` or the rename must update `pyproject.toml` `[project.scripts]` accordingly.

### Integration Points

- **Consumers** (per PROJECT.md): Equitania internal (e.g. `palettecad-bih`), `ownerp-demodata` (subprocess invocation — affected only at CLI level), external Odoo partners, public PyPI users. Hard-break is accepted by Captain decision; MIGRATION.md (Phase 4 deliverable) is the support channel.
- **`pyproject.toml` `[tool.setuptools.packages.find]`** — Currently `include = ["odoo_fast_report_mapper*", "odoo_report_helper*"]`. Phase 1 removes the second entry. This is the build-system signal that `odoo_report_helper` no longer ships.

### Fragile Areas (don't touch in Phase 1)

- **`LoggerManager._loggers` class-level mutable dict** — CONCERNS.md flags this as a fragile area. Deferred — Phase 1 only moves `logging_config.py` → `_logging.py`. Behavior unchanged.
- **`_search_report_v13` Odoo-version branching** — works as-is; refactoring is risky and Odoo v13 must keep working.

</code_context>

<specifics>
## Specific Ideas

- **Public name `OdooConnection`** for the merged class — Success Criteria #3 in ROADMAP.md hints at this exact import path: `from odoo_fast_report_mapper import OdooConnection`. The decision lines up with that hint.
- **`tqdm` directly for consumers** (DEAD-01 requirement) — Captain explicitly wants the MIGRATION.md example to show `from tqdm import tqdm` instead of `ProgressBar`. Phase 1 only removes; Phase 4 writes the migration example.
- **Two entry points stay** — non-negotiable per PROJECT.md constraints. Phase 1 plans must verify both still resolve after `pyproject.toml` updates.

</specifics>

<deferred>
## Deferred Ideas

- **`LoggerManager._loggers` class-level mutable dict refactor** — flagged by CONCERNS.md as a fragile area. Not in Phase 1 scope (Phase 1 is structural moves, not concurrency hardening). Candidate for a v1.x cleanup or Phase 2 if it surfaces during mypy-strict.
- **CLI by-feature test reorganization** (`test_connection_login.py`, `test_connection_mapping.py`, etc.) — bigger refactor. Considered and noted as out-of-Phase-1-scope. Could be v1.x if test files grow unwieldy after the merge.
- **Type hints throughout** — Phase 2 (`TYPE-01` mypy-strict). Phase 1 may add hints opportunistically when moving code, but no requirement to annotate everything.
- **`add_field_to_dictionary` RPC-call reduction** — Phase 3 (`PERF-01`). Phase 1 leaves the method's call signature unchanged.
- **Bigger MyDumper / YAMLDumper consolidation** — Phase 1 only renames `MyDumper.py` → `_yaml_dumper.py` and moves `YAMLDumper` from `eq_odoo_connection.py` into the same file. Deeper refactor of YAML-dumper semantics deferred.

</deferred>

---

*Phase: 1-Package Consolidation*
*Context gathered: 2026-05-28*
