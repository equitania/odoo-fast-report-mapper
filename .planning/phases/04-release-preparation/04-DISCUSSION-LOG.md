# Phase 04: Release Preparation - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-06-12 (session 1: 2026-06-11, resumed from checkpoint)
**Phase:** 04-release-preparation
**Areas discussed:** MIGRATION.md Zuschnitt, README-Strategie, CI-Matrix & Gates, Version & Alt-Dateien

---

## MIGRATION.md Zuschnitt (session 1)

| Option | Description | Selected |
|--------|-------------|----------|
| English-only (Empfohlen) | Single-language migration guide | |
| Bilingual DE/EN | Consistent with README structure | ✓ |

**User's choice:** Bilingual DE/EN

| Option | Description | Selected |
|--------|-------------|----------|
| API + Verhalten (Empfohlen) | Import paths, removed classes, tqdm example PLUS Phase-1.1 behavior changes | ✓ |
| Nur API-Brüche | API surface only | |

**User's choice:** API + behavior changes (ValueError instead of silent fail, api_key > password)

| Option | Description | Selected |
|--------|-------------|----------|
| PyPI-Link + sdist (Empfohlen) | Link in [project.urls] + include in sdist via MANIFEST.in | ✓ |
| Nur im Repo | Repo-only file | |
| Du entscheidest | Claude's discretion | |

**User's choice:** PyPI link + sdist inclusion

---

## README-Strategie (session 1)

| Option | Description | Selected |
|--------|-------------|----------|
| Update in place (Empfohlen) | Keep bilingual single-file structure (DE first, then EN), refresh contents | ✓ |
| uv-python-tools-Template | Rebuild from the standard template | |

**User's choice:** Update in place

| Option | Description | Selected |
|--------|-------------|----------|
| Komplett entfernen (Empfohlen) | History lives in MIGRATION.md and RELEASE_NOTES | ✓ |
| Als historisch markieren | Keep references, marked historical | |

**User's choice:** Remove all `odoo_report_helper` references completely

| Option | Description | Selected |
|--------|-------------|----------|
| Ja, Beispiele ergänzen (Empfohlen) | Commented api_key entry + precedence note | ✓ |
| Nein, nur README-Text | README documentation only | |

**User's choice:** Yes — extend yaml_examples/connection_yaml templates (closes open D-07 from Phase 1.1)

---

## CI-Matrix & Gates (session 2)

| Option | Description | Selected |
|--------|-------------|----------|
| 3.12 + 3.13 + 3.14 blocking (Empfohlen) | All three versions as full blocking matrix entries | ✓ |
| 3.14 erst non-blocking | 3.14 with continue-on-error, observe first | |
| Bei 3.12 + 3.13 bleiben | Matrix unchanged (CI-01 fallback) | |

**User's choice:** 3.12 + 3.13 + 3.14, all blocking
**Notes:** Python 3.14 stable since Oct 2025 — CI-01 stable path applies.

| Option | Description | Selected |
|--------|-------------|----------|
| Fixen + blocking (Empfohlen) | Fix path to odoo_fast_report_mapper/, drop continue-on-error, run --strict | ✓ |
| Fixen, aber non-blocking | Fix path, keep continue-on-error | |

**User's choice:** Fix + blocking (CI-02)
**Notes:** Current step still references the removed `odoo_report_helper/` package.

| Option | Description | Selected |
|--------|-------------|----------|
| RPC-Count-Test als Gate (Empfohlen) | Existing deterministic Phase-3 regression test (RPC_CEILING = 0) as blocking gate | ✓ |
| Zeit-basierter Benchmark | Wall-clock benchmark with threshold — flaky on shared runners | |
| Beides | RPC-count blocking + time benchmark non-blocking | |

**User's choice:** RPC-count regression test as the CI-03 perf gate

| Option | Description | Selected |
|--------|-------------|----------|
| Build-Job + Doku für Protection (Empfohlen) | uv build as CI job + document required branch-protection checks (Captain sets them) | ✓ |
| Nur Build-Job | Build job without protection docs | |
| Kein Build-Job | uv build stays local-only | |

**User's choice:** Build job + branch-protection documentation; publish stays local and Captain-only (GATE-05)

---

## Version & Alt-Dateien (session 2)

| Option | Description | Selected |
|--------|-------------|----------|
| 1.0.0 (Empfohlen) | Clean three-segment SemVer | ✓ |
| 1.0.0.0 | Keep existing 4-segment scheme | |

**User's choice:** 1.0.0

| Option | Description | Selected |
|--------|-------------|----------|
| In Phase 4, vor Captain-Review (Empfohlen) | Bump during Phase 4 execution so all docs reference a consistent version | ✓ |
| Erst nach allen Gates | Bump as the very last commit before publish | |
| Captain bumpt manuell | Captain sets version himself at release time | |

**User's choice:** Bump during Phase 4, before Captain review (GATE-04)

| Option | Description | Selected |
|--------|-------------|----------|
| Löschen via git rm (Empfohlen) | Contents superseded by .planning/ and RELEASE_NOTES; history stays in git | ✓ |
| Nach .planning/archive verschieben | Keep as living files in the planning archive | |
| Behalten | No cleanup in Phase 4 | |

**User's choice:** Delete IMPROVEMENT_PLAN.md, REVIEW.md, TASK_TRACKING.md via `git rm`

| Option | Description | Selected |
|--------|-------------|----------|
| CLAUDE.md raus (Empfohlen) | Internal developer instructions don't belong in the published package | ✓ |
| CLAUDE.md behalten | Status quo | |

**User's choice:** Remove CLAUDE.md from MANIFEST.in/sdist; MIGRATION.md goes in (per session-1 decision)

---

## Claude's Discretion

- Exact wording/structure within MIGRATION.md sections
- CI job naming and step ordering
- RELEASE_NOTES v1.0 entry layout (Breaking Changes section at top per DOCS-03)

## Deferred Ideas

None — discussion stayed within phase scope.
