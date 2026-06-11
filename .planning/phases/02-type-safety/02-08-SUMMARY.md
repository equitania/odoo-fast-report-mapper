---
phase: 02-type-safety
plan: 08
subsystem: cli
tags: [type-safety, mypy, click, annotations, phase-complete]
dependency_graph:
  requires: [02-01, 02-02, 02-03, 02-04, 02-05, 02-06, 02-07]
  provides: [full-strict-mypy-coverage]
  affects: [pyproject.toml, odoo_fast_report_mapper/_cli.py]
tech_stack:
  added: []
  patterns: [click-callback-typing, from-future-annotations]
key_files:
  created: []
  modified:
    - odoo_fast_report_mapper/_cli.py
    - pyproject.toml
decisions:
  - "Annotated Click command function parameters directly (yaml_path: str, env_path: str | None, select: bool) — Click passes Python-native types after coercion"
  - "init_callback typed with click.Context and click.Parameter — click>=8.1.3 ships py.typed stubs"
  - "No CI workflow changes — TYPE-03 satisfied by strict = true in pyproject.toml; local workflow uses uv run mypy (no flags)"
metrics:
  duration: "5 minutes"
  completed: "2026-06-11"
---

# Phase 02 Plan 08: Annotate _cli.py and Remove Final Override — Summary

One-liner: Final annotation pass on _cli.py (3 functions) + removal of last ignore_errors override block, establishing zero-override strict mypy for the entire package.

## What Was Done

### Task 1: Annotate _cli.py AND remove all remaining override blocks — atomic final pass

**PART A — _cli.py annotations:**

Three functions annotated:

1. `print_banner() -> None` — bare function, no params
2. `init_callback(ctx: click.Context, param: click.Parameter, value: bool) -> None` — Click eager callback
3. `start_odoo_fast_report_mapper(yaml_path: str, env_path: str | None, select: bool) -> None` — Click command entry point

The 6 `no-untyped-call` cascade errors noted in the plan were already absent — all callee modules (Plans 02-02 through 02-07) were clean before this plan ran. Pre-annotation mypy check confirmed 0 errors.

**PART B — pyproject.toml override removal:**

Removed the final `[[tool.mypy.overrides]]` block:
```toml
# Per-module override ramp (removed one-by-one as each plan completes):
[[tool.mypy.overrides]]
module = "odoo_fast_report_mapper._cli"
ignore_errors = true  # Plan 02-08 (final)
```

Only the `odoorpc_toolbox.*` `follow_untyped_imports = true` override remains (external dependency, intentional).

**PART C — Final verification results:**

| Check | Result |
|-------|--------|
| `mypy odoo_fast_report_mapper/` (no flags, config-driven) | Success: no issues found in 12 source files |
| `grep ignore_errors pyproject.toml` (non-comment lines) | 0 matches — all internal overrides removed |
| `grep follow_untyped_imports pyproject.toml` | Found — odoorpc_toolbox.* override retained |
| `grep "strict = true" pyproject.toml` | Found — TYPE-03 satisfied |
| Entry point import check | PASS: start_odoo_fast_report_mapper importable |
| Test suite | 347 passed in 0.51s |

## Deviations from Plan

None — plan executed exactly as written.

The cascade `no-untyped-call` errors had already resolved (as predicted in the plan) since all callee modules were annotated in Plans 02-02 through 02-07. The pre-annotation mypy check returned 0 errors even before adding the annotations, confirming the cascade resolution.

## Phase 2 Completion Status

All 8 plans of Phase 02 (type-safety) are complete:

| Plan | Module | Status |
|------|--------|--------|
| 02-01 | Infrastructure + _odoo_types.py | Complete |
| 02-02 | _logging.py | Complete |
| 02-03 | _report.py | Complete |
| 02-04 | _connection.py | Complete |
| 02-05 | _utils.py | Complete |
| 02-06 | __init__.py + __version__.py | Complete |
| 02-07 | _connection.py advanced | Complete |
| 02-08 | _cli.py + override removal | Complete |

**Requirements satisfied:** TYPE-01, TYPE-02, TYPE-03

## Self-Check

- [x] `odoo_fast_report_mapper/_cli.py` exists and is annotated
- [x] `pyproject.toml` has no `ignore_errors` lines (non-comment)
- [x] Commit c97b946 exists

## Self-Check: PASSED
