# Phase 04: Release Preparation - Context

**Gathered:** 2026-06-12
**Status:** Ready for planning

<domain>
## Phase Boundary

Phase 4 makes the project shippable as v1.0: all documentation is accurate for the single-package layout (MIGRATION.md, README.md, RELEASE_NOTES.md, SKILL.md, CLAUDE.md), CI enforces the full quality gates (Python matrix, mypy strict blocking, perf gate, build check), the version is bumped to 1.0.0, and legacy planning files are removed. The actual `uv publish` is performed exclusively by the Captain on his Mac — never by Claude (GATE-05).

</domain>

<decisions>
## Implementation Decisions

### MIGRATION.md Scope
- **D-01:** Language: bilingual DE/EN (consistent with the existing README structure).
- **D-02:** Depth: API breaks AND behavior changes — import-path mapping, removed classes with before/after snippets, tqdm-direct-usage example, PLUS Phase-1.1 behavior changes (ValueError instead of silent fail, `api_key` takes precedence over `password`).
- **D-03:** Discoverability: PyPI link in `[project.urls]` + include MIGRATION.md in the sdist via MANIFEST.in.

### README Strategy
- **D-04:** Update in place — keep the existing bilingual single-file structure (DE first, then EN), refresh contents for v1.0.
- **D-05:** Remove ALL `odoo_report_helper` references completely — history lives in MIGRATION.md and RELEASE_NOTES.md.
- **D-06:** Extend `yaml_examples/connection_yaml` templates with a commented-out `api_key` entry + note "api_key wins over password" (closes open D-07 from Phase 1.1).

### CI Matrix & Gates
- **D-07:** Python matrix: 3.12 + 3.13 + 3.14, all blocking (Python 3.14 is stable since Oct 2025 — CI-01 stable path applies).
- **D-08:** Mypy step: fix path to `odoo_fast_report_mapper/` (currently still references removed `odoo_report_helper/`), remove `continue-on-error: true`, run explicitly with `--strict`. Blocking (CI-02). Phase 2 already made mypy strict pass, so this gate is free.
- **D-09:** Perf gate (CI-03): use the existing deterministic RPC-count regression test from Phase 3 (`RPC_CEILING = 0`, mock-based) as the blocking gate. NO wall-clock benchmark — flaky on shared GitHub runners.
- **D-10:** Add `uv build` as a separate CI job (catches packaging regressions like MANIFEST errors). Document the required branch-protection checks briefly — the Captain sets the actual GitHub branch protection in the repo settings. `uv publish` stays local and Captain-only (GATE-05).

### Version & Legacy Files
- **D-11:** Version number: `1.0.0` (clean three-segment SemVer — `__version_info__` tuple keeps working, future patches as 1.0.1).
- **D-12:** Bump timing: set 1.0.0 during Phase 4 execution, BEFORE the Captain review (GATE-04) — RELEASE_NOTES, MIGRATION.md and docs then reference a consistent version. Review and publish remain with the Captain afterwards.
- **D-13:** Legacy pre-GSD planning files in repo root (`IMPROVEMENT_PLAN.md`, `REVIEW.md`, `TASK_TRACKING.md`): delete via `git rm` — contents are superseded by `.planning/` and RELEASE_NOTES; history stays in git.
- **D-14:** MANIFEST.in: remove `CLAUDE.md` from the sdist (internal developer instructions don't belong in the published package). Final sdist extras: README.md, LICENSE.txt, MIGRATION.md, yaml_examples.

### Claude's Discretion
- Exact wording/structure within MIGRATION.md sections, CI job naming and step ordering, RELEASE_NOTES v1.0 entry layout (as long as Breaking Changes section is at the top per DOCS-03).

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Requirements & Roadmap
- `.planning/REQUIREMENTS.md` — DOCS-01..05, CI-01..03, GATE-01..05 (full requirement texts for this phase)
- `.planning/ROADMAP.md` §Phase 4 — goal, dependencies, success criteria

### CI & Packaging
- `.github/workflows/test.yml` — current CI workflow to be hardened (matrix, mypy step, perf gate, build job)
- `pyproject.toml` — `[project.urls]`, mypy strict config, version source (`odoo_fast_report_mapper.__version__`)
- `MANIFEST.in` — sdist contents (CLAUDE.md out, MIGRATION.md in)
- `odoo_fast_report_mapper/__version__.py` — version bump target (0.9.7.4 → 1.0.0)

### Documentation Targets
- `README.md` — bilingual single-file structure to update in place
- `RELEASE_NOTES.md` — existing entry format ("## Version X.Y.Z (DD.MM.YYYY)")
- `~/.claude/skills/fr-mapper/SKILL.md` — DOCS-04 target (project structure, version history, skill hierarchy)
- `CLAUDE.md` (project) — DOCS-05 target (file structure block, architecture section)

### Prior Phase Evidence
- `.planning/phases/03-performance/03-02-SUMMARY.md` — RPC-count regression test with `RPC_CEILING = 0` (the CI-03 perf gate)
- `.planning/phases/01.1-correctness-bug-fixes-resolve-data-corruption-and-crash-bugs/01.1-CONTEXT.md` — behavior changes that must appear in MIGRATION.md (ValueError, api_key precedence)

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- RPC-count regression test (Phase 3): deterministic mock-counter test asserting `RPC_CEILING = 0` — becomes the CI perf gate without new infrastructure.
- Existing CI workflow `.github/workflows/test.yml`: uv-based setup with cache, ruff check + format, pytest with coverage — only matrix, mypy step, perf visibility, and build job change.

### Established Patterns
- Version is single-sourced from `odoo_fast_report_mapper/__version__.py` via `[tool.setuptools.dynamic]` in pyproject.toml — bump exactly one file.
- RELEASE_NOTES.md uses `## Version X.Y.Z (DD.MM.YYYY)` headers, newest first.
- Mypy strict already passes locally (Phase 2 completed strict typing) — CI just needs to stop ignoring it.

### Integration Points
- `dist/` and `*.egg-info` are git-ignored — no cleanup tasks needed there.
- Branch protection (merge blocking for develop/main) is a GitHub repo setting the Captain configures; CI provides the named check contexts.

</code_context>

<specifics>
## Specific Ideas

- Release workflow is intentionally LOCAL: Captain tests on his Mac and runs `uv publish` himself. CI exists to gate merges, not to publish. Claude must never run `uv publish` (GATE-05).
- MIGRATION.md ships inside the sdist so PyPI users get it offline.

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope.

</deferred>

---

*Phase: 04-release-preparation*
*Context gathered: 2026-06-12*
