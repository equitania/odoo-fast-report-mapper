---
phase: 04-release-preparation
reviewed: 2026-06-12T00:00:00Z
depth: standard
files_reviewed: 12
files_reviewed_list:
  - .github/workflows/test.yml
  - CLAUDE.md
  - MANIFEST.in
  - MIGRATION.md
  - odoo_fast_report_mapper/__version__.py
  - odoo_fast_report_mapper/_connection.py
  - odoo_fast_report_mapper/_lang_utils.py
  - odoo_fast_report_mapper/_odoo_types.py
  - pyproject.toml
  - README.md
  - RELEASE_NOTES.md
  - tests/test_benchmark_rpc.py
findings:
  critical: 2
  warning: 4
  info: 3
  total: 9
status: fixed
---

# Phase 04: Code Review Report

**Reviewed:** 2026-06-12
**Depth:** standard
**Files Reviewed:** 12
**Status:** issues_found

## Summary

Release-preparation work for v1.0.0 covers version bump, packaging metadata, CI workflow
hardening, bilingual migration guide, and documentation refresh. The Python source files
(_connection.py, _lang_utils.py, _odoo_types.py) are clean. The CI workflow structure and
pyproject.toml metadata are sound. Two critical defects found: both migration import paths
advertised in MIGRATION.md cause `ImportError` at runtime. Four warnings found: the CI
`build` and `perf` jobs run unconditionally without depending on the `test` job, an `assert`
is used for a runtime invariant in production code, the README architecture tree lists
pre-consolidation file names that no longer exist, and the README/MIGRATION.md give
contradictory descriptions of the api_key-vs-password precedence behavior.

---

## Critical Issues

### CR-01: MIGRATION.md exceptions import path causes ImportError [FIXED e7c676a]

**File:** `MIGRATION.md:27` (DE) and `MIGRATION.md:178` (EN)

**Issue:** Both the German and English sections instruct users to run:
```python
from odoo_fast_report_mapper.exceptions import PathDoesNotExistError
```
There is no module `odoo_fast_report_mapper/exceptions.py`. The exception class lives in
`odoo_fast_report_mapper/_exceptions.py`. Running the documented import raises
`ImportError: No module named 'odoo_fast_report_mapper.exceptions'` — confirmed by executing
the import against the installed package tree. Any user following the migration guide will
hit this error immediately.

The correct public import is via the package root (re-exported from `__init__.py`):
```python
from odoo_fast_report_mapper import PathDoesNotExistError
```
or via the private module (not recommended but functional):
```python
from odoo_fast_report_mapper._exceptions import PathDoesNotExistError
```

**Fix:** Update all occurrences in MIGRATION.md (lines 27, 178) in both the Import Mapping
Table and the Before/After code blocks:

```markdown
| `from odoo_report_helper.exceptions import PathDoesNotExistError` | `from odoo_fast_report_mapper import PathDoesNotExistError` |
```

---

### CR-02: MIGRATION.md parse_yaml_folder import path causes ImportError [FIXED e7c676a]

**File:** `MIGRATION.md:29` (DE) and `MIGRATION.md:180` (EN)

**Issue:** Both language sections document:
```python
from odoo_fast_report_mapper.eq_utils import parse_yaml_folder
```
There is no module `odoo_fast_report_mapper/eq_utils.py`. The function lives in
`odoo_fast_report_mapper/_utils.py` and is **not re-exported from `__init__.py`**. Executing
this import raises `ImportError: No module named 'odoo_fast_report_mapper.eq_utils'` —
confirmed at runtime.

**Fix (two-part):** Either expose `parse_yaml_folder` via the public package init, or correct
the documented path to use the private module:

Option A — add to `odoo_fast_report_mapper/__init__.py` and update MIGRATION.md:
```python
# __init__.py addition
from ._utils import parse_yaml_folder
# __all__ addition
"parse_yaml_folder",
```
and in MIGRATION.md:
```python
from odoo_fast_report_mapper import parse_yaml_folder
```

Option B — if the function is intentionally private, update MIGRATION.md to reflect the
private path:
```python
from odoo_fast_report_mapper._utils import parse_yaml_folder
```

---

## Warnings

### WR-01: CI `build` and `perf` jobs run independently of `test` — broken artifacts can be uploaded [WONTFIX D-10]

**File:** `.github/workflows/test.yml:54-105`

**Issue:** The `perf` (line 54) and `build` (line 77) jobs have no `needs:` declaration.
They run in parallel with — and independently of — the `test` matrix job. When the `test`
job fails (e.g., a mypy error on Python 3.14 or a new test regression), the `build` job can
still succeed and upload dist artifacts. This means release candidates built from broken
commits can accumulate as workflow artifacts and be misused.

The `perf` job similarly starts even when `test` is red; a failing test suite makes the
PERF gate moot.

**Decision:** Intentional parallel design (D-10) — branch protection requires all checks green; parallel jobs are expected. Skipped.

**Fix (if reversed):** Add `needs: test` to both jobs so they are gated on a green test run:

```yaml
  perf:
    runs-on: ubuntu-latest
    needs: test          # <-- add this

  build:
    runs-on: ubuntu-latest
    needs: test          # <-- add this
```

---

### WR-02: `assert` used for production-code runtime invariant in `login()` [FIXED e7c676a]

**File:** `odoo_fast_report_mapper/_connection.py:82`

**Issue:**
```python
assert self.password is not None, "Password must be set before login"
```
Python assertions are eliminated when the interpreter is run with the `-O` (optimize) flag
(`python -O` or `PYTHONOPTIMIZE=1`). In that mode this guard becomes a no-op and
`self.connection.login(self.database, self.username, None)` is passed to the RPC layer,
causing an opaque error downstream instead of the clear diagnostic message. The comment on
the same line acknowledges this is a deliberate invariant ("cleared to None after login"),
which makes a hard `raise` the correct construct.

**Fix:**
```python
if self.password is None:
    raise OdooConnectionError("Password must be set before login (already cleared after a previous login call)")
self.connection.login(self.database, self.username, self.password)
```

---

### WR-03: README architecture tree lists pre-consolidation file names that do not exist [FIXED e7c676a]

**File:** `README.md:322-329`

**Issue:** The architecture section lists these module files:
```
│   ├── eq_odoo_connection.py
│   ├── eq_report.py
│   ├── eq_utils.py
│   ├── lang_utils.py
│   ├── logging_config.py
│   └── progress.py
```
None of these files exist in the package. The actual v1.0 module names are:
`_connection.py`, `_report.py`, `_utils.py`, `_lang_utils.py`, `_logging.py`, `_progress.py`.
A developer inspecting the package after reading the README will find a completely
mismatched file tree and may be unable to locate the code they need. The data-flow diagram
on line 338 also refers to the non-existent `EqReport` and `EqOdooConnection` class names.

**Fix:** Replace the architecture block with the actual file names:
```
odoo-fast-report-mapper/
├── odoo_fast_report_mapper/          # Main package (single-package layout as of v1.0)
│   ├── __version__.py               # Version source (pyproject.toml dynamic)
│   ├── _cli.py                      # CLI entry point (Click)
│   ├── _connection.py               # OdooConnection: all mapping, testing, collecting logic
│   ├── _exceptions.py               # Custom exception classes
│   ├── _lang_utils.py               # Language normalization & multi-lang utilities
│   ├── _logging.py                  # Centralized logging configuration
│   ├── _odoo_types.py               # TypedDict definitions for Odoo RPC shapes
│   ├── _progress.py                 # tqdm-based progress wrapper
│   ├── _report.py                   # Report object & validation
│   ├── _utils.py                    # YAML collection, .env config, conversions
│   ├── _yaml_dumper.py              # Custom YAML serializer
│   └── py.typed                     # PEP 561 marker
```
Update the data-flow diagram to use `Report Objects` and `OdooConnection`.

---

### WR-04: README and MIGRATION.md give contradictory descriptions of api_key precedence [FIXED e7c676a]

**File:** `README.md:252` vs `MIGRATION.md:261`

**Issue:** The two documents directly contradict each other on whether a warning is emitted
when both `ODOO_API_KEY` and `ODOO_PASSWORD` are set:

- `README.md` (English .env config block, line 252):
  `# If both are set, the API key wins (with warning).`
- `MIGRATION.md` (section 3b, line 261):
  `api_key takes precedence silently. No warning is emitted.`

Both statements are *partially* correct but describe different code paths: the `.env` loader
(`create_connection_from_env`, `_utils.py:461`) **does** emit a `logger.warning` when both
are set, while the YAML-based loader (`_utils.py:285`) silently prefers `api_key`. The
README comment applies to the `.env` path (which is what the README config section
demonstrates), so `README.md` is correct for that context. MIGRATION.md section 3b's
heading says "(YAML loader)" in the German section but the English section heading omits
this qualifier, making the silent-precedence statement appear universal when it is not.

**Fix:** In `MIGRATION.md`, ensure the English section 3b heading includes the "(YAML
loader)" qualifier to match the German heading, and add a note clarifying that the `.env`
loader emits a warning whereas the YAML loader is silent:

```markdown
#### 3b. api_key takes precedence over password (YAML loader)

When both `api_key` and `password` are set in the **server YAML configuration**,
`api_key` takes precedence silently. No warning is emitted.

> **Note:** The `.env`-based loader (`ODOO_API_KEY` + `ODOO_PASSWORD`) **does** emit a
> `logger.warning` when both are set. This difference is intentional (D-06).
```

---

## Info

### IN-01: Dead code path in `build_name_search_domain` — `len <= 1` branch is unreachable [SKIPPED — info only]

**File:** `odoo_fast_report_mapper/_lang_utils.py:95-96`

**Issue:**
```python
if len(all_variants) <= 1:
    return all_variants
```
`all_variants` is built by appending **two** entries per key in `name_dict` (the name and the
`name + " (PDF)"` variant). Because an empty dict is already rejected by the `ValueError`
guard at line 89, `all_variants` will always have a minimum length of 2 after the guard.
The `<= 1` branch is therefore unreachable dead code and misleads readers into thinking there
is a valid single-condition path.

**Fix:** Remove the unreachable branch:
```python
# Remove lines 95-96; or replace with an assert for documentation:
assert len(all_variants) >= 2, "invariant: each key contributes 2 variants"
or_operators = ["|"] * (len(all_variants) - 1)
return or_operators + all_variants
```

---

### IN-02: RELEASE_NOTES.md test count (368) does not match actual test suite (349) [FIXED e7c676a]

**File:** `RELEASE_NOTES.md:88`

**Issue:** The v0.9.7 release notes state:
```
Total test count: 368 (up from 353): +11 API-key tests, +4 BLOCKER regression tests,
+2 W-04 domain-shape regression tests, −2 obsolete LOCALE_TO_LEGACY tests
```
The actual collected test count is **349** (confirmed by `pytest --collect-only -q`). The
README badge (`tests-349 passed`) is correct. The RELEASE_NOTES arithmetic overstates the
count. This creates confusion when auditing test coverage history.

**Fix:** Correct the v0.9.7 entry to read `Total test count: 349`.

---

### IN-03: MANIFEST.in does not include RELEASE_NOTES.md in the sdist [FIXED e7c676a]

**File:** `MANIFEST.in:1-6`

**Issue:** `RELEASE_NOTES.md` is absent from the `include` directives. Users who download
and inspect the source distribution (`.tar.gz`) from PyPI will not find the changelog.
README.md references RELEASE_NOTES.md implicitly through version history, and it was
explicitly called out in the v1.0.0 changelog entry. Not including it in the sdist reduces
utility for offline/air-gapped users.

**Fix:**
```
include README.md
include LICENSE.txt
include MIGRATION.md
include RELEASE_NOTES.md
```

---

_Reviewed: 2026-06-12_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_
