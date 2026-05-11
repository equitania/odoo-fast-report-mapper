# Codebase Structure

**Analysis Date:** 2026-05-11

## Directory Layout

```
odoo-fast-report-mapper/
├── odoo_fast_report_mapper/          # Main package (Equitania extension layer)
│   ├── __init__.py
│   ├── __version__.py                # Single version source (dynamic attr in pyproject.toml)
│   ├── odoo_fast_report_mapper.py    # CLI entry point (Click command)
│   ├── eq_odoo_connection.py         # EqOdooConnection — extends OdooConnection
│   ├── eq_report.py                  # EqReport — extends Report
│   ├── eq_utils.py                   # Factory functions, env/YAML loaders
│   ├── lang_utils.py                 # Language normalization utilities
│   ├── logging_config.py             # Singleton LoggerManager, colored+rotating logging
│   ├── progress.py                   # tqdm wrappers (ProgressBar, progress_bar)
│   └── MyDumper.py                   # Legacy YAML dumper (superseded by YAMLDumper in eq_odoo_connection.py)
├── odoo_report_helper/               # Base helper package (reusable primitives)
│   ├── __init__.py
│   ├── odoo_connection.py            # OdooConnection base class
│   ├── report.py                     # Report base class
│   ├── utils.py                      # prepare_connection(), parse_yaml_folder(), self_clean()
│   └── exceptions.py                 # OdooConnectionError, PathDoesNotExistError
├── tests/                            # Test suite
│   ├── __init__.py
│   ├── conftest.py                   # pytest fixtures
│   ├── fixtures/                     # Static test data
│   │   ├── sample_connection.yaml
│   │   ├── sample_report.yaml
│   │   └── sample_report_multicompany.yaml
│   ├── yaml_test/                    # YAML folder used by parse_yaml_folder() tests
│   │   ├── test.yaml
│   │   └── test2.yaml
│   ├── test_cli.py
│   ├── test_eq_odoo_connection.py
│   ├── test_eq_report.py
│   ├── test_eq_utils.py
│   ├── test_exceptions.py
│   ├── test_helper_utils.py
│   ├── test_lang_utils.py
│   ├── test_logging.py
│   ├── test_odoo_connection.py
│   ├── test_progress.py
│   └── test_report.py
├── yaml_examples/                    # Template and example YAML configs (not processed at runtime)
│   ├── reports_yaml/
│   │   ├── template.yaml             # Minimal report YAML template
│   │   └── template2.yaml            # Alternative template
│   ├── .yaml/                        # Real-world example report YAMLs
│   │   ├── eq_fr_core_account_move.yaml
│   │   ├── eq_fr_core_sale_order.yaml
│   │   └── ...                       # One file per Odoo report
│   └── .test/                        # Test/example YAMLs
├── .github/
│   └── workflows/
│       └── test.yml                  # GitHub Actions CI pipeline
├── .env.example                      # Example env config (safe to commit — no secrets)
├── .env                              # Active env config (gitignored, contains credentials)
├── pyproject.toml                    # Single source of truth: deps, build, ruff, pytest, mypy, coverage
├── uv.lock                           # UV lockfile (committed)
├── MANIFEST.in
├── README.md
├── RELEASE_NOTES.md
├── CLAUDE.md                         # Claude Code project instructions
└── .planning/                        # GSD planning artifacts
    └── codebase/
        ├── ARCHITECTURE.md
        └── STRUCTURE.md
```

## Directory Purposes

**`odoo_fast_report_mapper/` (main package):**
- Purpose: Equitania product-specific extension layer — all `eq_*` prefixed code lives here
- Contains: CLI, subclassed connection/report, language utils, logging, progress bars
- Key files: `odoo_fast_report_mapper.py` (entry point), `eq_odoo_connection.py` (core business logic), `eq_utils.py` (factories)

**`odoo_report_helper/` (base package):**
- Purpose: Reusable, product-agnostic Odoo RPC and report primitives
- Contains: Base classes, URL normalization, YAML parsing, custom exceptions
- Key files: `odoo_connection.py`, `report.py`, `utils.py`, `exceptions.py`
- Note: Packaged and distributed alongside the main package (both included via `[tool.setuptools.packages.find]` in `pyproject.toml`)

**`tests/`:**
- Purpose: Full unit test suite, organized by module (one test file per source file)
- Contains: pytest tests, conftest fixtures, static YAML fixtures, yaml_test folder for filesystem tests
- Coverage target: 60% minimum (`fail_under = 60` in `pyproject.toml`)

**`yaml_examples/`:**
- Purpose: Reference templates and real-world YAML examples for users setting up report configs
- NOT processed by the tool at runtime — user-maintained report folders are separate
- `reports_yaml/`: minimal templates; `.yaml/`: complete real-world examples

**`.github/workflows/`:**
- Purpose: GitHub Actions CI — runs test suite on push/PR
- Key file: `test.yml`

**`.planning/codebase/`:**
- Purpose: GSD codebase mapping artifacts consumed by `/gsd-plan-phase` and `/gsd-execute-phase`
- Generated: Yes (by `/gsd-map-codebase`)
- Committed: Yes

## Key File Locations

**Entry Points:**
- `odoo_fast_report_mapper/odoo_fast_report_mapper.py`: CLI `@click.command` — `start_odoo_fast_report_mapper()`
- `pyproject.toml:44-45`: Registers `odoo-fast-report-mapper` and `odoo-fr-mapper` console scripts

**Version:**
- `odoo_fast_report_mapper/__version__.py`: Contains `__version__`, `__author__`, `__url__` — single source of truth

**Configuration:**
- `pyproject.toml`: All build, lint, test, and coverage configuration
- `.env` / `.env.example`: Runtime connection configuration (gitignored / example committed)

**Core Business Logic:**
- `odoo_fast_report_mapper/eq_odoo_connection.py`: `map_reports()`, `collect_report_entries()`, `test_fast_report_rendering()`, `disable_qweb_reports()`
- `odoo_fast_report_mapper/eq_utils.py`: `create_connection_from_env()` — primary factory

**Base Layer:**
- `odoo_report_helper/utils.py`: `prepare_connection()` — URL normalization and RPC client init
- `odoo_report_helper/odoo_connection.py`: `OdooConnection.login()`, base `map_reports()`

**Testing:**
- `tests/conftest.py`: Shared pytest fixtures
- `tests/fixtures/`: Static YAML files used as test data
- `tests/yaml_test/`: Two-file YAML folder for `parse_yaml_folder()` tests

## Naming Conventions

**Files:**
- `eq_*.py` — Equitania-specific extension files (all in `odoo_fast_report_mapper/`)
- `*_utils.py` — utility/helper modules (no classes, only functions)
- `test_*.py` — pytest test files, one per source module
- `*.yaml` — report definition files; named after the `report_name` field value (e.g., `eq_fr_core_sale_order.yaml`)

**Classes:**
- `Eq*` prefix — Equitania subclasses (`EqOdooConnection`, `EqReport`)
- No prefix — base classes (`OdooConnection`, `Report`)

**Functions:**
- `create_*` — factory functions returning new objects
- `collect_*` — functions that gather/load data from filesystem or Odoo
- `parse_*` — YAML parsing functions
- `_*` — private methods (single underscore), internal to class
- `eq_*` — Equitania custom RPC methods called on Odoo server side (e.g., `eq_write_report_ids`, `eq_render_fast_report`)

**Environment Variables:**
- `ODOO_*` prefix for all configuration variables

## Where to Add New Code

**New Odoo RPC operation:**
- Implementation: `odoo_fast_report_mapper/eq_odoo_connection.py` — add method to `EqOdooConnection`
- Tests: `tests/test_eq_odoo_connection.py`

**New CLI option:**
- Implementation: `odoo_fast_report_mapper/odoo_fast_report_mapper.py` — add `@click.option` to `start_odoo_fast_report_mapper`
- If option needs env var: add to `create_connection_from_env()` in `odoo_fast_report_mapper/eq_utils.py` and update `ENV_TEMPLATE`

**New report field (Odoo-side):**
- `EqReport.__init__()` in `odoo_fast_report_mapper/eq_report.py` — add parameter
- `EqReport.self_ensure()` — add to `_data_dictionary`
- `EqReport.ensure_data_for_yaml()` — add to YAML output dict
- `create_report_object_from_yaml_object()` in `odoo_fast_report_mapper/eq_utils.py` — read from yaml_object
- Tests: `tests/test_eq_report.py` and `tests/fixtures/sample_report.yaml`

**New language utility:**
- `odoo_fast_report_mapper/lang_utils.py`
- Tests: `tests/test_lang_utils.py`

**New utility function (base, report-agnostic):**
- `odoo_report_helper/utils.py`
- Tests: `tests/test_helper_utils.py`

**New custom exception:**
- `odoo_report_helper/exceptions.py`
- Tests: `tests/test_exceptions.py`

**New YAML report example:**
- `yaml_examples/.yaml/eq_fr_core_<model_name>.yaml` — follow existing naming pattern

## Special Directories

**`.planning/`:**
- Purpose: GSD planning documents (architecture maps, implementation plans, phases)
- Generated: Partially (codebase/ subdir by `/gsd-map-codebase`)
- Committed: Yes

**`.github/`:**
- Purpose: GitHub Actions CI configuration
- Generated: No
- Committed: Yes

**`yaml_examples/`:**
- Purpose: User-facing reference templates — NOT runtime inputs to the tool
- Generated: No
- Committed: Yes

**`tests/fixtures/`:**
- Purpose: Static YAML fixtures for unit tests
- Generated: No
- Committed: Yes

**`.venv/`:**
- Purpose: UV virtual environment (created by `uv venv`)
- Generated: Yes
- Committed: No (gitignored)

**`dist/`:**
- Purpose: Built package artifacts (`uv build`)
- Generated: Yes
- Committed: No (gitignored)

---

*Structure analysis: 2026-05-11*
