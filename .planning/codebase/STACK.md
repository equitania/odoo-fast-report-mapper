# Technology Stack

**Analysis Date:** 2026-05-11

## Languages

**Primary:**
- Python 3.12+ — entire production codebase (`odoo_fast_report_mapper/`, `odoo_report_helper/`)

**Secondary:**
- YAML — report and (legacy) connection configuration format (`yaml_examples/`)

## Runtime

**Environment:**
- CPython 3.12 or 3.13 (tested in CI matrix)
- Minimum: Python >= 3.12 (enforced in `pyproject.toml`)

**Package Manager:**
- uv (Astral) — replaces pip everywhere; lockfile present (`uv.lock`)
- Lockfile: `uv.lock` present and committed
- Install: `uv pip install -e ".[dev]"`

## Frameworks

**CLI:**
- Click 8.1.3+ — command definitions, prompts, echo (`odoo_fast_report_mapper/odoo_fast_report_mapper.py`)

**Build:**
- setuptools >= 68.0 + wheel — build backend (`pyproject.toml` `[build-system]`)
- Dynamic version sourced from `odoo_fast_report_mapper/__version__.py` via `attr =` directive
- Build artifact: `uv build` → `dist/`

**Testing:**
- pytest 8.0+ — test runner; config in `[tool.pytest.ini_options]`
- pytest-cov 5.0+ — coverage; minimum 60% enforced (`[tool.coverage.report]`)
- pytest-mock 3.6.0+ — mocking helpers

**Type Checking:**
- mypy 1.0+ — `continue-on-error: true` in CI (non-blocking)
- types-PyYAML 6.0.0+ — stubs for PyYAML

**Linting / Formatting:**
- ruff 0.4.0+ — lint (`E,W,F,I,UP,B,SIM`) + format (double quotes, spaces)
- Line length: 120 characters
- Target: `py312`
- First-party: `odoo_fast_report_mapper`, `odoo_report_helper`

**Publishing:**
- twine 4.0+ — PyPI upload (`[project.optional-dependencies].dev`)
- Package name on PyPI: `odoo-fast-report-mapper-equitania`

## Key Dependencies

**Critical:**
- `odoorpc-toolbox >= 0.7.2` — internalized OdooRPC; provides `ODOO` class and `RPCError`; handles XML-RPC/JSON-RPC transport (`odoo_report_helper/utils.py:prepare_connection`)
- `click >= 8.1.3` — CLI entry points (`odoo-fast-report-mapper`, `odoo-fr-mapper`)
- `PyYAML >= 6.0.1` — `yaml.safe_load()` for report YAML files (`odoo_report_helper/utils.py`)
- `python-dotenv >= 1.0.0` — loads `.env` file; `load_dotenv()` in `odoo_fast_report_mapper/eq_utils.py`
- `tqdm >= 4.65.0` — progress bars (`odoo_fast_report_mapper/progress.py`)

**Dev/Test Only:**
- `ruff >= 0.4.0`, `mypy >= 1.0`, `types-PyYAML >= 6.0.0`
- `pytest >= 8.0`, `pytest-cov >= 5.0`, `pytest-mock >= 3.6.0`
- `twine >= 4.0`, `build >= 1.0.0`

## Configuration

**Environment:**
- Primary config via `.env` file loaded by `python-dotenv`
- Required vars: `ODOO_URL`, `ODOO_PORT`, `ODOO_USER`, `ODOO_DATABASE`, `ODOO_LANGUAGE`
- Auth vars (one required): `ODOO_PASSWORD` or `ODOO_API_KEY` (API key takes precedence if both set)
- Optional vars: `ODOO_COLLECT_YAML` (default False), `ODOO_DISABLE_QWEB` (default True), `ODOO_WORKFLOW` (0/1/2, default 0)
- Template generated via `odoo-fr-mapper --init` → `odoo_fast_report_mapper/eq_utils.py:generate_env_template()`
- Legacy: YAML-based server config (`connection_yaml/`) still parseable via `create_odoo_connection_from_yaml_object()` (deprecated)

**Build:**
- `pyproject.toml` — single source of truth for all deps, scripts, tool config
- No `requirements.txt` or `requirements-dev.txt` — use `uv pip install -e ".[dev]"`

## CLI Entry Points

Both map to the same function:
```
odoo-fast-report-mapper  →  odoo_fast_report_mapper.odoo_fast_report_mapper:start_odoo_fast_report_mapper
odoo-fr-mapper           →  odoo_fast_report_mapper.odoo_fast_report_mapper:start_odoo_fast_report_mapper
```

## Platform Requirements

**Development:**
- Python 3.12 or 3.13
- uv package manager
- `.env` file with Odoo credentials

**Production:**
- Any OS (Python 3.12+, OS Independent per classifiers)
- Network access to target Odoo instance (HTTPS recommended; HTTP warns at runtime)
- Odoo instance with FastReport module (`eq_fr_*` models present)

---

*Stack analysis: 2026-05-11*
