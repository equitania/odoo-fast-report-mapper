---
phase: 4
slug: release-preparation
status: verified
threats_open: 0
asvs_level: 1
created: 2026-06-12
---

# Phase 4 — Security

> Per-phase security contract: threat register, accepted risks, and audit trail.

---

## Trust Boundaries

| Boundary | Description | Data Crossing |
|----------|-------------|---------------|
| MANIFEST.in → sdist → PyPI | Controls which files are packaged and published to PyPI users | Internal developer instructions (CLAUDE.md), migration docs (MIGRATION.md) |
| `__version__.py` → published metadata | Single source of truth for PyPI package version | Version string only |
| `.github/workflows/test.yml` → CI runners | GitHub Actions workflow executing untrusted code paths | No secrets in scope; only test artifacts uploaded |
| `uv publish` gate | Publish action that pushes to PyPI | Package credentials — Captain-only, never automated |
| SKILL.md → Claude agent context | Active import advice injected into future Claude sessions | stale package references would cause wrong code generation |

---

## Threat Register

| Threat ID | Category | Component | Disposition | Mitigation | Status |
|-----------|----------|-----------|-------------|------------|--------|
| T-04-01 | Information Disclosure | MANIFEST.in | mitigate | `include MIGRATION.md` present; `exclude CLAUDE.md` present in MANIFEST.in; `tar -tzf dist/odoo_fast_report_mapper_equitania-1.0.0.tar.gz \| grep CLAUDE` returns no output (verified) | closed |
| T-04-02 | Tampering | pyproject.toml classifiers | accept | Classifier values are informational metadata only; incorrect value causes cosmetic PyPI mislabeling, not a security issue | closed |
| T-04-03 | Tampering | CI workflow injection | accept | No `pull_request_target` trigger; no `${{ github.event.* }}` inputs in any step (grep returns EXIT:1 on both checks) | closed |
| T-04-04 | Information Disclosure | uploaded dist/ artifact | accept | `actions/upload-artifact@v4` uploads `dist/` (wheel + sdist only); no secrets in pyproject.toml dev/test extras; retention-days: 7 | closed |
| T-04-05 | Information Disclosure | MIGRATION.md code snippets | mitigate | All credentials in MIGRATION.md are placeholders: `your_password`, `your_api_key`, `https://odoo.example.com` — verified via grep, no real secrets present | closed |
| T-04-06 | Information Disclosure | RELEASE_NOTES.md | accept | Public changelog with factual version information only; no credentials or internal paths | closed |
| T-04-07 | Information Disclosure | README.md on PyPI | accept | Contains only directory structure, CLI options, and role descriptions; no credentials or internal paths | closed |
| T-04-08 | Tampering | SKILL.md stale data | mitigate | SKILL.md line 332 contains only one `odoo_report_helper` reference — an explicit statement that the package "no longer exists"; no active import advice present; stale fixture path corrected to `odoo_fast_report_mapper._utils.ODOO` | closed |
| T-04-09 | Information Disclosure | sdist contents | mitigate | `exclude CLAUDE.md` added to MANIFEST.in (commit 4ec5799); `tar -tzf dist/*1.0.0*.tar.gz \| grep -E "(CLAUDE\|MIGRATION)"` returns only `MIGRATION.md` — CLAUDE.md absent from sdist | closed |
| T-04-10 | Tampering | uv publish automation | mitigate | `uv publish` absent from `.github/workflows/test.yml` (grep returns EXIT:1); `git log --oneline \| grep publish` returns no match; Captain-only publish policy documented in 04-05-SUMMARY.md | closed |
| T-04-11 | Information Disclosure | branch protection check names | accept | Check names (`test (3.12)`, `test (3.13)`, `test (3.14)`, `perf`, `build`) are informational workflow job names matching `.github/workflows/test.yml`; publishing them is intentional to help configure GitHub settings | closed |
| T-04-SC (×5 plans) | Tampering | package installs | accept | No new package installs in any plan across phases 04-01 through 04-05; all changes are file edits only; `pyproject.toml` dependencies unchanged | closed |

*Status: open · closed*
*Disposition: mitigate (implementation required) · accept (documented risk) · transfer (third-party)*

---

## Accepted Risks Log

| Risk ID | Threat Ref | Rationale | Accepted By | Date |
|---------|------------|-----------|-------------|------|
| AR-04-01 | T-04-02 | pyproject.toml classifiers are informational PyPI metadata; wrong value causes cosmetic mislabeling only, not a security vulnerability | Captain (Martin Schmid) | 2026-06-12 |
| AR-04-02 | T-04-03 | CI uses `push` and `pull_request` triggers only — no `pull_request_target` (which would allow fork secrets access); no `${{ github.event.* }}` interpolation in workflow steps; standard GitHub Actions security model applies | Captain (Martin Schmid) | 2026-06-12 |
| AR-04-03 | T-04-04 | Uploaded `dist/` artifact contains only the built wheel and sdist — no credentials or sensitive data; 7-day retention is appropriate for release artifacts | Captain (Martin Schmid) | 2026-06-12 |
| AR-04-04 | T-04-06 | RELEASE_NOTES.md is a public changelog with factual version content; no secrets or internal paths present | Captain (Martin Schmid) | 2026-06-12 |
| AR-04-05 | T-04-07 | README.md is a public-facing document designed for PyPI; content is limited to installation instructions, CLI options, and directory structure | Captain (Martin Schmid) | 2026-06-12 |
| AR-04-06 | T-04-11 | Branch protection check names match GitHub Actions job names and are required for the Captain to configure repository settings; disclosing job names does not expose credentials or exploit surface | Captain (Martin Schmid) | 2026-06-12 |
| AR-04-07 | T-04-SC | No new package installs across all five plans in phase 04; only file edits, git rm, and `uv build` (using already-installed packages) | Captain (Martin Schmid) | 2026-06-12 |

*Accepted risks do not resurface in future audit runs.*

---

## Unregistered Flags

None. The `## Threat Flags` section in 04-05-SUMMARY.md explicitly states: "No new security surface introduced. T-04-09 (Information Disclosure via sdist CLAUDE.md) was detected and mitigated via MANIFEST.in fix in this plan." T-04-09 is already registered in the threat model above.

---

## Security Audit Trail

| Audit Date | Threats Total | Closed | Open | Run By |
|------------|---------------|--------|------|--------|
| 2026-06-12 | 12 | 12 | 0 | security-auditor agent (claude-sonnet-4-6) |

---

## Sign-Off

- [x] All threats have a disposition (mitigate / accept / transfer)
- [x] Accepted risks documented in Accepted Risks Log
- [x] `threats_open: 0` confirmed
- [x] `status: verified` set in frontmatter

**Approval:** verified 2026-06-12
