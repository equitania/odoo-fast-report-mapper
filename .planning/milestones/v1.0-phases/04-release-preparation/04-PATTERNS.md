# Phase 04: Release Preparation - Pattern Map

**Mapped:** 2026-06-12
**Files analyzed:** 9 new/modified files + 1 skill update + 3 deletions
**Analogs found:** 9 / 9

## File Classification

| New/Modified File | Role | Data Flow | Closest Analog | Match Quality |
|-------------------|------|-----------|----------------|---------------|
| `MIGRATION.md` | doc | transform | `README.md` (bilingual DE/EN structure) | role-match |
| `README.md` | doc | transform | `README.md` (update in place) | exact |
| `RELEASE_NOTES.md` | doc | append | `RELEASE_NOTES.md` (existing format) | exact |
| `.github/workflows/test.yml` | config | batch | `.github/workflows/test.yml` (update in place) | exact |
| `pyproject.toml` | config | transform | `pyproject.toml` (update in place) | exact |
| `MANIFEST.in` | config | transform | `MANIFEST.in` (update in place) | exact |
| `odoo_fast_report_mapper/__version__.py` | utility | transform | `odoo_fast_report_mapper/__version__.py` | exact |
| `yaml_examples/reports_yaml/template.yaml` | config | transform | `yaml_examples/reports_yaml/template.yaml` + `.env.example` | exact |
| `~/.claude/skills/fr-mapper/SKILL.md` | doc | transform | `~/.claude/skills/fr-mapper/SKILL.md` (update in place) | exact |

---

## Pattern Assignments

### `MIGRATION.md` (doc, new file)

**Analog:** `README.md` — bilingual DE-first then EN structure

**Document structure pattern** (README.md lines 1–11):
```markdown
# Odoo Fast Report Mapper

> **Language / Sprache**: [DE](#deutsche-dokumentation) | [EN](#english-documentation)

---

## Deutsche Dokumentation

[... German content ...]

---

## English Documentation

[... English content ...]
```

**Content scope** (from D-02):
- Section order: Breaking Changes → Import Path Changes → Behavior Changes → Quick Migration Checklist
- Per breaking change: before/after code snippet
- Behavior changes from Phase 1.1: `ValueError` instead of silent fail, `api_key` takes precedence over `password`
- Removed classes: `OdooConnection` from `odoo_report_helper` → now `OdooConnection` in `odoo_fast_report_mapper._connection`
- tqdm direct usage: `from odoo_fast_report_mapper.progress import progress_bar` instead of tqdm directly

**MANIFEST.in entry to add** (analog: current MANIFEST.in line 3):
```
include MIGRATION.md
```
(CLAUDE.md entry on line 3 is removed in same edit — see MANIFEST.in section below)

---

### `README.md` (doc, update in place)

**Analog:** `README.md` (self)

**Changes required:**
1. Remove ALL `odoo_report_helper` references from Architecture section (README.md lines 311–328) — history moves to MIGRATION.md
2. Update Architecture block to match current single-package layout (no `odoo_report_helper/` tree entry)
3. Update test count badge (line 6): `344 passed` → current count (check with `pytest --collect-only -q | tail -1`)
4. Development section type-check command (line 363): remove `odoo_report_helper/` from mypy invocation

**Architecture block to replace** (lines 310–328) — new version lists only `odoo_fast_report_mapper/`:
```
odoo-fast-report-mapper/
├── odoo_fast_report_mapper/          # Main package (single-package layout as of v1.0)
│   ├── __version__.py               # Version source (pyproject.toml dynamic)
│   ├── _cli.py                      # CLI entry point (Click)
│   ├── _connection.py               # OdooConnection base class
│   ├── eq_odoo_connection.py        # EqOdooConnection: mapping, testing, collecting
│   ├── eq_report.py                 # EqReport objects & validation
│   ├── eq_utils.py                  # YAML collection, .env config, conversions
│   ├── lang_utils.py                # Language normalization & multi-lang utilities
│   ├── logging_config.py            # Centralized logging with color + rotation
│   └── progress.py                  # tqdm-based progress tracking
├── tests/                           # Unit tests
├── yaml_examples/                   # Configuration templates
└── pyproject.toml                   # Package configuration
```

**Mypy command in Development section** (line 363) — remove `odoo_report_helper/`:
```bash
mypy odoo_fast_report_mapper/
```

---

### `RELEASE_NOTES.md` (doc, prepend new entry)

**Analog:** `RELEASE_NOTES.md` — exact header format

**Existing header pattern** (lines 1–3):
```markdown
# Release Notes

## Version 0.9.7.3 (11.05.2026)
```

**New v1.0 entry to prepend** (after line 2, before existing v0.9.7.3 entry):
```markdown
## Version 1.0.0 (12.06.2026)

### Breaking Changes
- Removed `odoo_report_helper` package — all public API now in `odoo_fast_report_mapper`
  - `from odoo_report_helper.exceptions import PathDoesNotExistError` → `from odoo_fast_report_mapper.exceptions import PathDoesNotExistError`
  - `from odoo_report_helper.utils import parse_yaml_folder` → `from odoo_fast_report_mapper.eq_utils import parse_yaml_folder`
  - See MIGRATION.md for full import-path mapping and before/after examples

### Added
- MIGRATION.md: bilingual DE/EN migration guide for users upgrading from pre-1.0 versions
- `[project.urls]` in pyproject.toml: added "Migration Guide" link pointing to MIGRATION.md on GitHub

### Changed
- Version bumped to 1.0.0 (clean three-segment SemVer; future patches as 1.0.1)
- Development Status classifier: "4 - Beta" → "5 - Production/Stable"
- CI matrix extended to Python 3.14 (stable since Oct 2025)
- mypy CI step: removed `continue-on-error: true`, now blocking; path fixed to `odoo_fast_report_mapper/` only
- CI perf gate: RPC-count regression test (`tests/test_benchmark_rpc.py`) runs as blocking separate job

### Removed
- Legacy pre-GSD planning files: `IMPROVEMENT_PLAN.md`, `REVIEW.md`, `TASK_TRACKING.md` (history preserved in git)
- `CLAUDE.md` removed from sdist (internal developer instructions; not for PyPI users)
```

**Format rules** (from existing entries):
- `### Fixed` / `### Added` / `### Changed` / `### Removed` subsections
- `### Breaking Changes` at top (DOCS-03 requirement)
- Bullet items with dash, no trailing period
- Date format: DD.MM.YYYY

---

### `.github/workflows/test.yml` (config, update in place)

**Analog:** `.github/workflows/test.yml` (self)

**Current matrix** (lines 14–15):
```yaml
        python-version: ["3.12", "3.13"]
```

**Target matrix** (D-07):
```yaml
        python-version: ["3.12", "3.13", "3.14"]
```

**Current mypy step** (lines 40–42 — blocking removal + path fix per D-08):
```yaml
      - name: Mypy type check
        run: uv run mypy odoo_fast_report_mapper/ odoo_report_helper/
        continue-on-error: true
```
Replace with:
```yaml
      - name: Mypy type check
        run: uv run mypy odoo_fast_report_mapper/ --strict
```

**New `build` job to add** (D-10) — separate job at same level as `test:`:
```yaml
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Install uv
        uses: astral-sh/setup-uv@v6
        with:
          enable-cache: true

      - name: Set up Python
        run: uv python install 3.12

      - name: Create virtual environment
        run: uv venv --python 3.12

      - name: Install project with dev extras
        run: uv pip install -e ".[dev]"

      - name: Build sdist and wheel
        run: uv build

      - name: Upload build artifacts
        uses: actions/upload-artifact@v4
        with:
          name: dist
          path: dist/
          retention-days: 7
```

**Perf gate job to add** (D-09) — separate job running the RPC regression test:
```yaml
  perf:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Install uv
        uses: astral-sh/setup-uv@v6
        with:
          enable-cache: true

      - name: Set up Python
        run: uv python install 3.12

      - name: Create virtual environment
        run: uv venv --python 3.12

      - name: Install project with dev extras
        run: uv pip install -e ".[dev]"

      - name: RPC count regression test (PERF gate)
        run: uv run pytest tests/test_benchmark_rpc.py -v
```

**Trigger branches** (lines 3–8) — add `"main"` if not yet included (currently only `main` and `develop` are listed — no change needed):
```yaml
on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main, develop]
```

---

### `pyproject.toml` (config, update in place)

**Analog:** `pyproject.toml` (self)

**Current `[project.urls]` block** (lines 37–41):
```toml
[project.urls]
Homepage = "https://github.com/equitania/odoo-fast-report-mapper"
"Bug Reports" = "https://github.com/equitania/odoo-fast-report-mapper/issues"
Documentation = "https://www.ownerp.com/odoo-fastreport"
Company = "https://www.equitania.de"
```
Add `"Migration Guide"` entry (D-03):
```toml
[project.urls]
Homepage = "https://github.com/equitania/odoo-fast-report-mapper"
"Bug Reports" = "https://github.com/equitania/odoo-fast-report-mapper/issues"
Documentation = "https://www.ownerp.com/odoo-fastreport"
"Migration Guide" = "https://github.com/equitania/odoo-fast-report-mapper/blob/main/MIGRATION.md"
Company = "https://www.equitania.de"
```

**Classifier update** (line 18):
```toml
    "Development Status :: 5 - Production/Stable",
```
(currently `"4 - Beta"`)

**Add Python 3.14 classifier** after line 22 (`"Programming Language :: Python :: 3.13"`):
```toml
    "Programming Language :: Python :: 3.14",
```

**Version source** (line 65) — no change needed, already correct:
```toml
[tool.setuptools.dynamic]
version = { attr = "odoo_fast_report_mapper.__version__.__version__" }
```

**mypy config** (lines 119–128) — no change needed, `strict = true` already set and `odoo_report_helper` override can be removed after that package is gone:
```toml
[tool.mypy]
python_version = "3.12"
strict = true
```
Remove the `[[tool.mypy.overrides]]` block for `odoo_report_helper.*` if present (currently only `odoorpc_toolbox.*` override exists — no action needed).

---

### `MANIFEST.in` (config, update in place)

**Analog:** `MANIFEST.in` (self)

**Current content** (lines 1–5):
```
include README.md
include LICENSE.txt
include CLAUDE.md
recursive-include yaml_examples *.yaml
prune *.egg-info
```

**Target content** (D-14, D-03):
```
include README.md
include LICENSE.txt
include MIGRATION.md
recursive-include yaml_examples *.yaml
prune *.egg-info
```
Change: line 3 `include CLAUDE.md` → `include MIGRATION.md`

---

### `odoo_fast_report_mapper/__version__.py` (utility, update in place)

**Analog:** `odoo_fast_report_mapper/__version__.py` (self)

**Current version** (line 12):
```python
__version__ = "0.9.7.4"
__version_info__ = tuple(int(x) for x in __version__.split("."))
```

**Target version** (D-11):
```python
__version__ = "1.0.0"
__version_info__ = tuple(int(x) for x in __version__.split("."))
```

`__version_info__` tuple continues to work correctly: `(1, 0, 0)`.
No other changes to this file — copyright header, metadata constants, and license comment stay as-is.

---

### `yaml_examples/reports_yaml/template.yaml` (config, update in place)

**Analog:** `.env.example` lines 11–17 (api_key comment pattern)

**Current template** does not mention `api_key`. The `.env.example` analog shows the comment pattern:
```bash
# Option B: API key (Odoo >= 14, recommended for v16+)
# Generate via Odoo: Preferences → Account Security → New API Key
# If both are set, ODOO_API_KEY takes precedence.
# ODOO_API_KEY=your_api_key
```

The `template.yaml` file (yaml_examples/reports_yaml/template.yaml) itself is a report YAML — it does not contain connection settings and therefore does NOT need an `api_key` entry. Connection settings live in `.env` only.

**D-06 target is `.env.example` and any remaining `connection_yaml/` templates** — verify those exist:
- `.env.example` already has the `ODOO_API_KEY` comment block (lines 14–17 — complete, no change needed)
- `yaml_examples/connection_yaml/` directory does not exist (was legacy format, superseded by `.env`-based config)
- **No file changes needed for D-06** — `.env.example` is already correct

---

### `~/.claude/skills/fr-mapper/SKILL.md` (doc, update in place)

**Analog:** `~/.claude/skills/fr-mapper/SKILL.md` (self)

**Changes required** (DOCS-04):

1. **Version** in header description (line 11): `v0.9.7` → `v1.0.0`

2. **Project Structure** section (lines 43–87) — remove `odoo_report_helper/` subtree entirely, update `__version__.py` comment:
```
├── odoo_fast_report_mapper/          # Main package (single-package layout)
│   ├── __version__.py               # Version: 1.0.0
│   ├── _cli.py                      # CLI entry point (Click)
│   ├── _connection.py               # OdooConnection base class
│   ├── eq_odoo_connection.py        # EqOdooConnection (extends OdooConnection)
```
Remove the `odoo_report_helper/` block (lines 69–73).

3. **Version History** section (lines 358–374) — prepend v1.0.0 entry consistent with RELEASE_NOTES.md breaking changes summary.

4. **Architecture / Class Hierarchy** — remove `OdooConnection (odoo_report_helper)` parent reference; update to show `OdooConnection` from `odoo_fast_report_mapper._connection`.

5. **Development Commands** mypy line (line 258):
```bash
mypy odoo_fast_report_mapper/
```
(remove `odoo_report_helper/`)

---

## Shared Patterns

### Bilingual Document Structure
**Source:** `README.md` lines 1–11
**Apply to:** `MIGRATION.md` (new), any updated doc sections
```markdown
> **Language / Sprache**: [DE](#deutsche-dokumentation) | [EN](#english-documentation)

---

## Deutsche Dokumentation
[German content]

---

## English Documentation
[English content]
```

### Version Bump Single-Source Pattern
**Source:** `odoo_fast_report_mapper/__version__.py` + `pyproject.toml` lines 64–65
**Apply to:** `__version__.py` only — pyproject.toml reads it dynamically
```python
__version__ = "1.0.0"  # Change only this file; pyproject.toml reads via dynamic attr
```

### RELEASE_NOTES Header Format
**Source:** `RELEASE_NOTES.md` lines 3–4
**Apply to:** New v1.0.0 entry
```markdown
## Version X.Y.Z (DD.MM.YYYY)

### Breaking Changes   ← always first subsection for v1.0
```

### CI uv Job Pattern
**Source:** `.github/workflows/test.yml` lines 17–32 (setup steps)
**Apply to:** New `build` job and `perf` job — copy identical checkout + uv install setup block:
```yaml
    steps:
      - uses: actions/checkout@v4
      - name: Install uv
        uses: astral-sh/setup-uv@v6
        with:
          enable-cache: true
      - name: Set up Python
        run: uv python install 3.12
      - name: Create virtual environment
        run: uv venv --python 3.12
      - name: Install project with dev extras
        run: uv pip install -e ".[dev]"
```

---

## Perf Gate Test — Exact Reference

**File:** `tests/test_benchmark_rpc.py`
**Invocation:** `uv run pytest tests/test_benchmark_rpc.py -v`
**Key constant:** `RPC_CEILING: int = 0` (line 16) — zero inner `ir.model.search` calls
**Two test functions:**
- `test_collect_rpc_call_count` (line 113) — 10 reports × 50 fields, asserts `mock_ir_model.search.call_count == 0`
- `test_add_field_to_dictionary_zero_rpc_calls` (line 214) — unit-level, asserts both `ir.model.search` and `ir.model.fields.search` call counts are 0

Both tests are mock-based (no real Odoo connection) — deterministic and safe for CI.

---

## Deletions (git rm)

**Files to delete via `git rm`** (D-13):
- `IMPROVEMENT_PLAN.md` — confirmed present at `/Users/picard/gitbase/PyPi-Projects/odoo-fast-report-mapper/IMPROVEMENT_PLAN.md`
- `REVIEW.md` — confirmed present
- `TASK_TRACKING.md` — confirmed present

Note: `.claude/worktrees/` copies of these files are worktree artifacts — do NOT delete those separately; `git rm` on the root copies is sufficient.

---

## No Analog Found

All files have existing analogs. No gaps.

---

## Metadata

**Analog search scope:** project root, `.github/workflows/`, `odoo_fast_report_mapper/`, `yaml_examples/`, `tests/`, `~/.claude/skills/fr-mapper/`
**Files scanned:** 11 source files read directly
**Pattern extraction date:** 2026-06-12
