# Project Retrospective

*A living document updated after each milestone. Lessons feed forward into future planning.*

## Milestone: v1.0 — Cleanup

**Shipped:** 2026-06-12
**Phases:** 5 (1, 1.1, 2, 3, 4) | **Plans:** 28 | **Commits:** 166

### What Was Built
- Single-package layout: `odoo_report_helper/` dissolved into `odoo_fast_report_mapper/`, circular import eliminated, dead public API removed
- 9 correctness fixes (BUG-01..09), each locked by a regression test
- `mypy --strict` with 0 errors/0 overrides, TypedDict RPC shapes, `py.typed` in the wheel
- RPC performance gate: 1,000 redundant calls per collect run eliminated, `RPC_CEILING = 0` enforced in CI
- v1.0.0 release artifacts: bilingual MIGRATION.md (in sdist), hardened CI (3.12–3.14, mypy strict, perf, build), all release gates green

### What Worked
- Inserted gap-closure phase (1.1) caught real data-corruption bugs from the baseline review before type-safety work locked the APIs
- Module-by-module mypy override ramp (Phase 2) kept every commit green while tightening to full strict
- Mock-counter RPC benchmark (Phase 3) made performance deterministic and CI-enforceable — no flaky wall-clock thresholds
- Plan-time threat models made the final security audit a verification pass (12/12 closed) instead of a discovery exercise
- Code-review gate after Phase 4 execution caught 2 critical doc errors (import examples against non-existent modules) before release

### What Was Inefficient
- Planner and PATTERNS.md propagated stale module names (`eq_utils.py`, `eq_odoo_connection.py`) into Phase-4 docs — the package had been renamed to `_`-prefixed modules in Phase 1; ground-truth file listing should be re-verified at plan time, not inherited from earlier artifacts
- Several SUMMARY.md files had malformed one-liner frontmatter ("One-liner:" placeholder), polluting automated accomplishment extraction at milestone close
- Worktree agents occasionally forked from a stale base (pre-plan-commit HEAD), forcing manual merges instead of the templated cleanup path
- REQUIREMENTS.md traceability was not updated by phase completion tooling (stayed "Pending" though phases passed) — needed manual sync at audit time

### Patterns Established
- Deterministic mock-counter tests as CI performance gates (`RPC_CEILING`)
- Bilingual DE-first/EN-second single-file docs (README pattern reused for MIGRATION.md)
- `uv publish` is Captain-only, forever — CI gates merges, never releases
- Explicit `exclude CLAUDE.md` in MANIFEST.in (setuptools auto-includes top-level files)

### Key Lessons
1. Docs that show code (import examples, file trees) must be verified against the live package API, not against plans or pattern maps — two critical review findings came from exactly this gap.
2. Keep requirement traceability in sync at phase close; stale "Pending" rows nearly forced an unnecessary gap investigation at milestone close.
3. Summary one-liner quality matters downstream — milestone tooling consumes it verbatim.

### Cost Observations
- Model mix: opus for planning only; sonnet for execution/verification/audit agents; orchestration inline
- Sessions: ~6 across 2026-05-11 → 2026-06-12
- Notable: plan-time threat models + pattern mapping kept the audit and security passes cheap (pure verification, no discovery)

## Cross-Milestone Trends

| Milestone | Phases | Plans | Commits | Requirements | Audit |
|-----------|--------|-------|---------|--------------|-------|
| v1.0 Cleanup | 5 | 28 | 166 | 36/36 | passed |
