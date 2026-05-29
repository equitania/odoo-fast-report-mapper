---
gsd_state_version: 1.0
milestone: v1.0
milestone_name: milestone
status: Phase 01.1 executing
last_updated: "2026-05-29T09:28:53.700Z"
progress:
  total_phases: 5
  completed_phases: 1
  total_plans: 12
  completed_plans: 11
  percent: 20
---

# STATE — odoo-fast-report-mapper

## Project Reference

**Core value**: Mapping YAML report configurations into a live Odoo database must remain reliable and reproducible across all supported Odoo versions.
**Milestone**: v1.0 Cleanup
**Milestone goal**: Production-ready single-package codebase with mypy-strict, no dead code, no circular imports, performance-benchmarked, fully documented.

---

## Current Position

Phase: 1.1 (Correctness Bug Fixes (INSERTED)) — EXECUTING
Plan: 7 of 7
**Phase**: 1.1 — Correctness Bug Fixes (INSERTED)
**Plan**: 6 of 7 — EXECUTED
**Status**: Phase 1.1 executing (6/7 executed)
**Progress**: Phase 1 complete (5/5); Phase 1.1 executing (6/7 executed)

```
[Phase 1: Consolidation] ✓ → [Phase 2: Type Safety] → [Phase 3: Performance] → [Phase 4: Release Prep]
```

---

## Performance Metrics

| Metric | Value |
|--------|-------|
| Tests passing (baseline) | 369 (v0.9.7.3 on develop) |
| Mypy errors (baseline) | 13 (permissive mode) |
| Mypy target | 0 (strict mode) |
| RPC calls per field (baseline) | 2 extra (IR_MODEL.search + IR_FIELDS.search) |
| RPC target | 0 extra per field |

---
| Phase 01-package-consolidation P03 | 15 | 3 tasks | 2 files |
| Phase 01-package-consolidation P04 | 8 | 2 tasks | 1 files |
| Phase 01.1-correctness-bug-fixes-resolve-data-corruption-and-crash-bugs P01 | 10m | 2 tasks | 2 files |
| Phase 01.1-correctness-bug-fixes-resolve-data-corruption-and-crash-bugs P02 | 8m | 2 tasks | 2 files |
| Phase 01.1-correctness-bug-fixes-resolve-data-corruption-and-crash-bugs P04 | 5m | 2 tasks | 2 files |
| Phase 01.1 P05 | 5m | 2 tasks | 2 files |
| Phase 01.1-correctness-bug-fixes-resolve-data-corruption-and-crash-bugs P03 | 5m | 2 tasks | 2 files |

## Accumulated Context

### Roadmap Evolution

- Phase 1.1 inserted after Phase 1: Correctness Bug Fixes (BUG-01..BUG-07) from baseline review — crashes, data corruption, bypassed dependency check

### Key Decisions Logged

| Decision | Rationale |
|----------|-----------|
| 4 coarse phases, not 3 | Type-Safety and Performance can run in parallel after Phase 1 but are distinct concerns — keeping them separate makes plans cleaner and reviewable independently |
| Phase 2 and Phase 3 both depend on Phase 1 | Both touch the same consolidated files; Type-Safety needs stable import paths; Performance needs the cleaned-up add_field_to_dictionary() code |
| DEAD-04 excluded from Phase 1 | progress_bar() wrapper is still used internally in eq_odoo_connection.py — only the unused public class APIs are removed |
| GATE-01..GATE-05 in Phase 4 | Release-quality gates are final verification steps, not work items — they belong in Release Preparation alongside docs and CI hardening |
| No UI hint on any phase | Pure Python CLI/library — no frontend components anywhere in scope |
| Lazy import for _report.Report in Wave 3 | Avoids forward-reference before Wave 4 creates _report.py — clean and no circular dependency |
| Explicit params in merged OdooConnection.__init__ | Replaces *args/**kwargs pass-through — eliminates silent positional-arg reordering risk (R-01) |
| test_connection.py patches _connection.prepare_connection | prepare_connection is bound at import time in _connection.py; patching _utils.prepare_connection would miss the already-bound reference |
| Empty odoo_report_helper/ namespace dir required explicit rmdir | git rm removes files but leaves directories; empty dir with __pycache__ was treated as namespace package by Python |
| Do NOT call self_clean on dict-valued containers | self_clean uses dict.fromkeys which iterates keys only, destroying nested {function_name: [params]} structure in calculated_fields |
| ValueError on empty name_dict in build_name_search_domain | Fail loudly per D-02; empty dict is always a broken YAML (never a legitimate runtime state), so raising ValueError before any Odoo RPC call prevents silent overwrite of unintended report records |
| dict[str, str] annotation on entry_name with isinstance+truthy guard | Per-key validation excluded (D-09); isinstance+truthy only is sufficient to prevent dict object reaching Odoo name field |

### Architectural Facts (for plan authors)

- Circular import: `odoo_report_helper/odoo_connection.py` line 9 imports `build_name_search_domain` from `odoo_fast_report_mapper/lang_utils.py` — upward dependency, eliminated by dissolution
- After Phase 1: one package (`odoo_fast_report_mapper/`), with `_connection.py`, `_report.py`, `_utils.py`, `exceptions.py` as submodules
- Two entry points (`odoo-fast-report-mapper`, `odoo-fr-mapper`) both registered in pyproject.toml — must remain after consolidation
- `uv publish` is NEVER automated — Captain runs manually; Claude never executes this command
- Git: push to both `origin` (GitLab) and `upstream` (GitHub) for every release commit/tag

### Todos

- [ ] Plan Phase 1 via /gsd-plan-phase 1

### Blockers

None.

---

## Session Continuity

**Last action**: Plan 01.1-06 executed — BUG-06 fixed (1be3c90) — 2026-05-29
**Next action**: Execute Phase 1.1 Plan 07 (final plan in phase 1.1)

---

*Initialized: 2026-05-11*
