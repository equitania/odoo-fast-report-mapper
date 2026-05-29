# ROADMAP — odoo-fast-report-mapper v1.0

**Milestone:** v1.0 Cleanup
**Granularity:** Coarse (4 phases + 1 inserted bug-fix phase)
**Coverage:** 34/34 requirements mapped

---

## Phases

- [x] **Phase 1: Package Consolidation** - Dissolve odoo_report_helper/ into a single package, remove dead progress-bar APIs, eliminate circular import (completed 2026-05-28)
- [ ] **Phase 1.1: Correctness Bug Fixes** *(inserted)* - Fix data-corruption and crash bugs surfaced by the baseline review before type-safety work begins
- [ ] **Phase 2: Type Safety** - Mypy strict mode passes with zero errors across the consolidated production codebase
- [ ] **Phase 3: Performance** - Benchmark and eliminate the 2 extra RPC calls per field in add_field_to_dictionary()
- [ ] **Phase 4: Release Preparation** - MIGRATION.md, docs refresh, CI matrix hardening, all release-quality gates

---

## Phase Details

### Phase 1: Package Consolidation
**Goal**: The codebase is one package — odoo_report_helper/ no longer exists, the circular import is gone, dead progress-bar public APIs are removed, and every test module runs in isolation.
**Depends on**: Nothing (first phase)
**Requirements**: CONS-01, CONS-02, CONS-03, CONS-04, DEAD-01, DEAD-02, DEAD-03
**Success Criteria** (what must be TRUE):
  1. `pytest tests/test_odoo_connection.py` passes standalone — no import errors, no circular-import failures
  2. `import odoo_report_helper` raises `ModuleNotFoundError` — the package directory is gone
  3. `from odoo_fast_report_mapper import OdooConnection` (or equivalent consolidated path) resolves without error
  4. `from odoo_fast_report_mapper.progress import ProgressBar` raises `ImportError` — dead API is removed
  5. All remaining tests pass (369 minus the legitimately removed P-08/P-09 tests)
**Plans**: 5 plans
Plans:
- [x] 01-01-PLAN.md — Coverage baseline and pre-flight green verification (D-13)
- [x] 01-02-PLAN.md — Create leaf private submodules: _exceptions, _lang_utils, _logging, _yaml_dumper, _progress
- [x] 01-03-PLAN.md — Create merged _connection.py (OdooConnection) and _utils.py
- [x] 01-04-PLAN.md — Create merged _report.py (Report class)
- [x] 01-05-PLAN.md — Switch imports, rename CLI to _cli.py, merge tests, delete old files, verify all success criteria

### Phase 1.1: Correctness Bug Fixes (INSERTED)
**Goal**: The correctness bugs surfaced by the baseline review are fixed in the consolidated codebase — no unguarded crashes, no silent data corruption, no bypassed dependency checks, and connection/config parsing fails loudly instead of silently mis-handling input. Each fix is locked in by a regression test.
**Depends on**: Phase 1 (bugs are fixed in the consolidated structure, not the pre-consolidation duplicate files)
**Requirements**: BUG-01, BUG-02, BUG-03, BUG-04, BUG-05, BUG-06, BUG-07 (see `.planning/BASELINE-REVIEW.md`)
**Success Criteria** (what must be TRUE):
  1. **BUG-01 (CR-02)** — `add_field_to_dictionary()` guards the `IR_MODEL.search()` result before indexing; an empty result raises a clear error or skips the field instead of `IndexError`. Regression test covers the empty-search case.
  2. **BUG-02 (CR-03)** — `self_clean()` preserves calculated-field parameter lists; a config like `{"eq_get_payment_terms": ["p1","p2"]}` survives cleaning intact. Regression test asserts the inner structure is unchanged.
  3. **BUG-03 (CR-04)** — `check_dependencies` and its caller agree on the return contract; a failed dependency check actually blocks mapping (no `bool((False, [...]))` always-true path). Regression test proves a missing dependency stops the run.
  4. **BUG-04 (WR-03)** — `build_name_search_domain({})` fails loudly (or returns a guarded result) instead of producing an unbounded all-reports-for-model search.
  5. **BUG-05 (WR-04)** — `prepare_connection` URL parsing strips scheme and any path component correctly; a URL like `https://host/web` yields hostname `host`, not `host/web`.
  6. **BUG-06 (WR-05)** — `Report.__init__` `entry_name` handling matches its runtime type; no dict is ever written to Odoo's `name` field.
  7. **BUG-07 (WR-07)** — `create_odoo_connection_from_yaml_object` honors the configured auth method; an API key in YAML is treated as an API key, not silently as a password.
  8. All existing tests still pass after the fixes.
**Plans**: 7 plans
Plans:
- [x] 01.1-01-PLAN.md — BUG-01: add_field_to_dictionary IndexError guard (skip-and-warn on empty IR_MODEL.search)
- [x] 01.1-02-PLAN.md — BUG-02: remove broken self_clean call from add_calculated_fields
- [x] 01.1-03-PLAN.md — BUG-03: formalize check_dependencies return annotation + map_reports dependency-blocking regression test
- [x] 01.1-04-PLAN.md — BUG-04: build_name_search_domain ValueError on empty name_dict
- [x] 01.1-05-PLAN.md — BUG-05: prepare_connection urlparse.hostname-based extraction replacing str.replace loop
- [x] 01.1-06-PLAN.md — BUG-06: Report.__init__ entry_name dict[str, str] guard + fixture updates
- [ ] 01.1-07-PLAN.md — BUG-07: create_odoo_connection_from_yaml_object api_key support

### Phase 2: Type Safety
**Goal**: mypy --strict odoo_fast_report_mapper/ exits with zero errors — no ignores, no baseline suppressions.
**Depends on**: Phase 1
**Requirements**: TYPE-01, TYPE-02, TYPE-03
**Success Criteria** (what must be TRUE):
  1. `mypy --strict odoo_fast_report_mapper/` reports 0 errors (was 13 baseline errors in v0.9.7)
  2. Every public function and method has a complete type annotation (no `Any` without explicit `# type: ignore` justification)
  3. `pyproject.toml` `[tool.mypy]` section contains `strict = true` — the CI command uses no override flags
  4. All existing tests still pass after annotation additions
**Plans**: TBD

### Phase 3: Performance
**Goal**: The collect flow makes at most the minimum necessary RPC calls — the 2 extra search calls per field are eliminated and a regression test enforces the limit in CI.
**Depends on**: Phase 1
**Requirements**: PERF-01, PERF-02, PERF-03, PERF-04
**Success Criteria** (what must be TRUE):
  1. A pytest benchmark test exists that counts RPC calls for a simulated 10-report × 50-field collect run via Mock-Counter on the RPC layer
  2. The benchmark passes with ≤ the documented call-count ceiling (exact number established during baseline measurement in this phase)
  3. `add_field_to_dictionary()` no longer calls `IR_MODEL.search()` + `IR_FIELDS.search()` per field — verified by the Mock-Counter test
  4. `pytest --collect-only` shows the benchmark test in the suite and `pytest tests/` (without --benchmark-skip) makes CI fail if the threshold is exceeded
**Plans**: TBD

### Phase 4: Release Preparation
**Goal**: All documentation is accurate for v1.0, CI enforces mypy-strict and the perf threshold, and the Captain can run uv publish to ship a clean release.
**Depends on**: Phase 2, Phase 3
**Requirements**: DOCS-01, DOCS-02, DOCS-03, DOCS-04, DOCS-05, CI-01, CI-02, CI-03, GATE-01, GATE-02, GATE-03, GATE-04, GATE-05
**Success Criteria** (what must be TRUE):
  1. `MIGRATION.md` exists at repo root with complete import-path mapping, before/after code snippets for every removed class, and a tqdm-direct-usage example
  2. `README.md`, `SKILL.md`, `CLAUDE.md`, and `RELEASE_NOTES.md` contain no references to `odoo_report_helper` as an active package
  3. GitHub Actions CI workflow passes on Python 3.12 + 3.13 (+ 3.14 if stable) with mypy-strict and perf-benchmark checks as blocking steps
  4. `ruff check . && ruff format --check .` exits 0, `mypy --strict odoo_fast_report_mapper/` exits 0, all tests pass — all three in a single clean CI run
  5. `uv build` produces a wheel and sdist without errors or warnings
**Plans**: TBD

---

## Progress Table

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. Package Consolidation | 5/5 | Complete   | 2026-05-28 |
| 1.1 Correctness Bug Fixes *(inserted)* | 6/7 | In Progress|  |
| 2. Type Safety | 0/1 | Not started | - |
| 3. Performance | 0/1 | Not started | - |
| 4. Release Preparation | 0/2 | Not started | - |

---

*Created: 2026-05-11*
