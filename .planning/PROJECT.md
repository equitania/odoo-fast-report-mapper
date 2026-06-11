# odoo-fast-report-mapper

## What This Is

A Python CLI tool (PyPI package) that maps YAML report definitions to Odoo `ir.actions.report` records via XML-RPC/JSON-RPC, registers calculated fields, sets multi-language report-name translations, and tests FastReport rendering. It is the configuration bridge between Equitania's FastReport templates and live Odoo instances (v13–v19) — used internally at Equitania, by external Odoo partners, by the `ownerp-demodata` tool, and by an unknown number of public PyPI consumers.

## Core Value

**Mapping YAML report configurations into a live Odoo database must remain reliable and reproducible across all supported Odoo versions.** If everything else fails, the core `odoo-fr-mapper --yaml_path=...` flow with workflow=0 (mapping only) must continue to work against a real Odoo server.

## Requirements

### Validated

<!-- Shipped and confirmed valuable through real-world use. -->

- ✓ Map YAML report definitions to `ir.actions.report` records — v0.x
- ✓ Test FastReport rendering via `eq_render_fast_report` ORM call — v0.x
- ✓ Collect (reverse-export) existing FastReport entries from Odoo to YAML — v0.x
- ✓ Manage calculated fields (`eq_calculated_field_value`) — v0.x
- ✓ Multi-language report names: `de_DE`, `en_US`, `fr_FR`, etc. with legacy-key backward compatibility (`ger`/`eng`) — v0.x
- ✓ Multi-company support with `company_id` filter in report search — v0.9.4
- ✓ Interactive YAML file selection via `--select` — v0.9.0
- ✓ Interactive report selection in collect mode — v0.8.0
- ✓ `.env`-based configuration via `python-dotenv` (replacing legacy YAML connection configs) — v0.2.5
- ✓ API-key authentication (Odoo ≥ 14) as alternative to `ODOO_PASSWORD` — v0.9.7
- ✓ Pre-login version gate blocks API-key against Odoo < 14 — v0.9.7
- ✓ Connection summary box with dynamic width — v0.9.7.3
- ✓ Differentiated error messages (file-missing vs incomplete vs invalid) — v0.9.7.2
- ✓ GitHub Actions CI on Python 3.12 + 3.13 (ruff + ruff format + mypy + pytest) — v0.9.6
- ✓ Security hardening: `yaml.safe_load` only, path-traversal guards, port validation, HTTP plaintext warning, password cleared after login — v0.9.x
- ✓ Correctness hardening (BUG-01..BUG-07): empty-search guards, calculated-field preservation, dependency-check contract, loud failures on empty/malformed connection+config input, dict-typed `entry_name` guard, YAML api_key auth honored — each locked by a regression test — Phase 1.1
- ✓ **TYPE-01**: mypy `--strict` passes with 0 errors and zero internal overrides; full annotation coverage incl. TypedDict RPC shapes, PEP 561 `py.typed` marker shipped — Phase 2

### Active

<!-- v1.0 — Reines Tech-Debt-Cleanup vor "Production-Ready" Statement. Breaking changes erlaubt. -->

- [ ] **CONS-01**: Consolidate two-package layout — dissolve `odoo_report_helper/` into `odoo_fast_report_mapper/` (eliminates circular import)
- [ ] **CONS-02**: Remove dead-but-public API — `ProgressBar`, `ReportProgress`, `create_progress_bar` and their tests (~350 LOC)
- [ ] **PERF-01**: Benchmark `add_field_to_dictionary()` RPC-call count and reduce to a defined target (eliminate the 2 extra `browse()` calls per field)
- [ ] **DOCS-01**: Write `MIGRATION.md` with Before/After examples for every breaking change (import paths, removed classes, deprecated patterns)
- [ ] **DOCS-02**: Refresh `README.md` (DE + EN), `SKILL.md`, `CLAUDE.md`, `RELEASE_NOTES.md` to v1.0 reality
- [ ] **CI-01**: Extend CI matrix to include Python 3.14 once it reaches GA (fallback: keep at 3.12 + 3.13 if 3.14 not stable at release time)

### Out of Scope

<!-- Explicit boundaries for v1.0. Each can be considered for v1.x. -->

- **Bulk-Operationen** (e.g., parallel-batch report registration across many Odoo instances) — out of scope for v1.0; v1.0 is reines Cleanup ohne neue Features
- **OAuth / SSO / weitere Auth-Methoden** — v1.0 ships with Password + API-Key only; OAuth is a feature addition, not cleanup
- **Report-Templates-Generator** (scaffolding new FRX/YAML reports) — out of scope; separate tool concern
- **Interactive TUI** (z.B. via Textual) — out of scope; CLI mit Click bleibt einzige UX
- **Direkter FastReport-API-Aufruf** (umgehen der Odoo-ORM `eq_render_fast_report` Methode) — out of scope; das verletzt die etablierte Daten-Pipeline (Odoo → FastReport API)
- **Auto-Publish zu PyPI** — Captain-Policy: `uv publish` und PyPI-Upload erfolgen **ausschließlich durch Captain manuell**, niemals durch Automation oder Claude
- **DeprecationWarnings für entfernte APIs** — v1.0 ist Hard-Break; Migration-Guide ersetzt Deprecation-Phase
- **Backward-Compat-Aliase für `odoo_report_helper.*` imports** — Hard-Break by design; siehe MIGRATION.md für neue Pfade

## Context

**Technical environment:** Python 3.12+ PyPI CLI tool. Two entry points (`odoo-fast-report-mapper`, `odoo-fr-mapper`). Build via hatchling + `pyproject.toml`. Dependencies: odoorpc-toolbox ≥ 0.7.0 (internalized OdooRPC), Click ≥ 8.1.3, PyYAML ≥ 6.0.1, tqdm ≥ 4.65.0, python-dotenv ≥ 1.0.0. CI on Python 3.12 + 3.13 via GitHub Actions.

**Codebase state (v0.9.7.3, May 2026):**
- Two packages: `odoo_report_helper/` (base) + `odoo_fast_report_mapper/` (extension). Inheritance: `OdooConnection` → `EqOdooConnection`.
- Most base-class methods are overridden (not extended) in the subclass — historical design that v1.0 will collapse.
- Known circular import between the two packages (only resolvable in full test-suite, not in test-isolation).
- 369 tests pass on `develop`. 13 pre-existing mypy errors form the current baseline.
- REVIEW.md at repo root documents the v0.9.6 code review findings; v0.9.7 closed 15 of 18, P-08/P-09 deferred here to v1.0.

**Consumers (mixed visibility):**
- **Equitania internal:** Used for live customer deployments (e.g. `palettecad-bih`). Full control over all call sites — Equitania can migrate immediately when v1.0 ships.
- **ownerp-demodata:** Equitania-internal demo-data generator that invokes `odoo-fr-mapper` as a subprocess. Migration path needs coordination but is tracked.
- **External Odoo partners:** Several partner organizations using FastReport with Odoo. Migration-Guide is the primary support channel for them.
- **PyPI public consumers:** Unknown count, unknown integration depth. v1.0 release notes and `MIGRATION.md` must be discoverable and complete enough for unattended migration.

**Domain:** FastReport for Odoo is a commercial reporting solution (https://www.ownerp.com/odoo-fastreport). This tool is the configuration-loader piece; the FastReport API itself (ASP.NET Core) and the eq_fr_* Odoo modules (Python/XML) are separate codebases (see `fr-api` and `fr-odoo` skills).

**Repository state:** Git repo synced to two remotes — `origin` = `gitlab.ownerp.io:pypi-projects/odoo-fast-report-mapper.git`, `upstream` = `github.com:equitania/odoo-fast-report-mapper.git`. All releases must be pushed to both.

## Constraints

- **Tech stack**: Python 3.12+ — set by `pyproject.toml` `requires-python`. No drop in v1.0 unless explicitly decided.
- **Dependencies**: Stay on odoorpc-toolbox (not raw OdooRPC, not stock XML-RPC) — Equitania-internalized library is the supported RPC layer.
- **Backward compatibility (Odoo versions)**: Must continue to support Odoo v13 through v19 for the mapping/testing/collect flows — the version branching in `_search_report_v13` exists for a reason.
- **Release policy**: `uv publish` to PyPI is **manual, by Captain only**. CI may build wheels but never push. This is a hard policy constraint.
- **Git push**: Every release commit and tag must be pushed to both `origin` (GitLab) and `upstream` (GitHub). Both remotes stay in sync.
- **Security**: `yaml.safe_load` only (never `yaml.load`); all paths checked via `os.path.realpath()`; credentials cleared from memory after login; HTTP plaintext logs a warning.
- **Performance baseline**: v1.0 must not regress current end-to-end mapping time. Performance phase only improves; never trades correctness for speed.
- **Test coverage**: All v1.0 changes preserve the 369-test pass rate (minus the legitimately removed P-08/P-09 tests). Mypy strict must pass before v1.0 ships.

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Two-Package-Konsolidierung statt nur circular-import fix | Vereinfacht das Mental Model, beseitigt Override-statt-Extend-Smell. Breaking-Change ist im v1.0-Major-Bump akzeptabel | — Pending |
| P-08/P-09 hart entfernen statt Deprecation-Phase | Vor v1.0 deferred (v0.9.7). MIGRATION.md gibt Konsumenten klaren Pfad zu `tqdm` direkt | — Pending |
| Mypy **strict mode** statt nur "baseline zu 0" | Stronger reife-statement für v1.0. Equitania-interne Code-Quality-Erwartung passt zu major release | — Pending |
| Performance mit Benchmark + Zielwert (statt Code-Review-only) | Messbar, reproduzierbar, verhindert Regression in zukünftigen Releases. Test-Counter-Mock auf RPC-Schicht | — Pending |
| MIGRATION.md als separates Dokument (nicht nur RELEASE_NOTES) | Public-PyPI-User brauchen Before/After-Beispiele, suchbar im Repo-Root | — Pending |
| `uv publish` ausschließlich durch Captain | Sicherheitskontrolle gegen versehentlich falschen Release. Bleibt auch in v1.0+ Policy | — Pending |
| v1.0 ist 100% Cleanup, keine neuen Features | Klare Trennung: v1.0 = stable + clean. v1.x = neue Features. Verhindert Scope-Creep | — Pending |

## Evolution

This document evolves at phase transitions and milestone boundaries.

**After each phase transition** (via `/gsd-transition`):
1. Requirements invalidated? → Move to Out of Scope with reason
2. Requirements validated? → Move to Validated with phase reference
3. New requirements emerged? → Add to Active
4. Decisions to log? → Add to Key Decisions
5. "What This Is" still accurate? → Update if drifted

**After each milestone** (via `/gsd-complete-milestone`):
1. Full review of all sections
2. Core Value check — still the right priority?
3. Audit Out of Scope — reasons still valid?
4. Update Context with current state

---
*Last updated: 2026-06-11 after Phase 2 (Type Safety) completion*
