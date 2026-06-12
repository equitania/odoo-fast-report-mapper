# Milestones

## v1.0 Cleanup (Shipped: 2026-06-12)

**Phases completed:** 5 phases (1, 1.1, 2, 3, 4), 28 plans, 54 tasks
**Stats:** 166 commits, 148 files changed (+24,189/−4,341), 2,588 LOC package + 5,378 LOC tests
**Audit:** passed 36/36 requirements (see milestones/v1.0-MILESTONE-AUDIT.md) · Security: threats_open 0

**Delivered:** Pure tech-debt cleanup release — the two-package layout consolidated into a single typed package, 9 correctness bugs fixed with regression tests, RPC performance gated in CI, and full v1.0 release preparation. `uv publish` performed manually by the Captain.

**Key accomplishments:**

- Package consolidation: `odoo_report_helper/` fully dissolved into `odoo_fast_report_mapper/` — circular import eliminated, standalone `OdooConnection`/`Report` classes without inheritance, dead public API (`ProgressBar`, `ReportProgress`, `create_progress_bar`, ~350 LOC) removed
- 9 correctness bugs (BUG-01..09) fixed in the consolidated layout — crash guards, calculated-field preservation, dependency-check contract, api_key auth honored — each locked by a regression test
- Type safety: `mypy --strict` passes with 0 errors and 0 overrides across 12 source files; TypedDict RPC shapes, PEP 561 `py.typed` marker ships in the wheel
- Performance: 1,000 redundant RPC calls per 10×50 collect run eliminated; deterministic mock-counter regression test enforces `RPC_CEILING = 0` as a blocking CI gate
- Release preparation: version 1.0.0, bilingual DE/EN MIGRATION.md (shipped in sdist), RELEASE_NOTES with Breaking Changes first, README/CLAUDE/SKILL docs refreshed to the real single-package layout
- CI hardened: Python 3.12/3.13/3.14 matrix all blocking, mypy `--strict` blocking, perf gate, `uv build` job; all five release gates green (349 tests), MIGRATION.md Captain-approved (GATE-04)

**Known deferred items at close:** 3 tech-debt notes (WR-01 wontfix by design D-10; dead `len<=1` branch in `build_name_search_domain`; stale locked worktree `agent-a9b56aee58ada07c5`) — see milestones/v1.0-MILESTONE-AUDIT.md frontmatter.

---
