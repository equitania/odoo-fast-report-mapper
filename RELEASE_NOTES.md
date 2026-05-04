# Release Notes

## Version 0.9.6 (04.05.2026)

### Added
- GitHub Actions CI workflow (`.github/workflows/test.yml`) running on Python 3.12 and 3.13: `ruff check`, `ruff format --check`, `mypy`, `pytest` with coverage on every push/PR to `main` and `develop`

### Fixed
- Security: `prepare_connection()` now emits a `logger.warning()` when an `http://` URL is used, alerting users that credentials will be transmitted unencrypted (previously silent protocol downgrade to plain `jsonrpc`)
- Security: removed plaintext-looking placeholder from `tests/fixtures/sample_connection.yaml` (`test_password` → `PLACEHOLDER_NOT_A_REAL_PASSWORD`) to prevent confusion with real credentials
- Lint: 5 pre-existing ruff violations fixed in test suite (B017 in `test_exceptions.py`, B007/F841 in `test_logging.py`, SIM117 in `test_progress.py`)

### Removed
- Redundant `tests/utils_test.py` deleted — silently excluded from pytest runs (didn't match `test_*.py` pattern), made a real network call to `odoo.com`, and was fully duplicated by `test_helper_utils.py` with proper mocks

### Tests
- New regression guard `test_dependencies_only_contain_field_specific_modules` in `TestCollectReportEntries`: verifies that YAML export reads dependencies from `ir.model.fields.modules` per field (correctly handling comma-separated multi-module fields like `"sale, account"`) and never falls back to dumping all installed modules from `ir.module.module`
- Total test count: 353 (up from 352 — the new regression test)

## Version 0.9.5 (31.03.2026)

### Fixed
- Dynamic CLI `prog_name`: both entry points (`odoo-fr-mapper`, `odoo-fast-report-mapper`) now self-identify correctly in `--version` output — previously hardcoded to the long name
- Password cleanup on connection failure: `self.password` is now cleared in the `except` block of `OdooConnection.__init__()` to prevent credential retention after failed connections
- URL schema validation: `prepare_connection()` now rejects non-http/https URL schemes (e.g. `ftp://`, `file://`) with a clear `ValueError`

### Changed
- Unified progress bars: replaced `click.progressbar` in `collect_report_entries()` with project's own `progress_bar()` wrapper (tqdm-based) for consistent styling across all operations
- Removed `import click` from `eq_odoo_connection.py` — Click is no longer a dependency of the connection module
- Total test count: 352

## Version 0.9.4 (24.03.2026)

### Fixed
- Multi-company report mapping: `_search_report()` now includes `company_id` filter for v17+ — previously reports with the same name but different companies would overwrite each other instead of creating separate records
- Total test count: 352

## Version 0.9.3 (24.03.2026)

### Added
- Connection summary confirmation prompt before login — shows .env path, server, port, database, user, workflow in a box and asks for user confirmation before connecting
- Failed reports summary at end of mapping — lists failed reports with error messages and `--select` retry hint

### Changed
- `map_reports()` now catches errors per report instead of aborting the entire batch — failed reports are logged and skipped, remaining reports continue processing
- `map_reports()` returns a list of failed `(report_name, error_message)` tuples for caller inspection
- `create_connection_from_env()` returns `(connection, dotenv_path)` tuple for env file tracking
- `EqOdooConnection` stores `url` and `port` as instance attributes for display purposes
- Total test count: 350 (up from 344)

## Version 0.9.2 (23.03.2026)

### Changed
- Replaced broad `except Exception` with specific exception types (`RPCError`, `KeyError`, `AttributeError`, `ValueError`, `IndexError`) in `eq_odoo_connection.py` (4 locations)
- Added `__repr__`/`__str__` to `OdooConnection` to prevent credential leakage in tracebacks/logs
- Clear `self.password` from memory after successful login
- YAML parsing now uses explicit `encoding="utf-8"` for cross-platform compatibility

### Fixed
- Path traversal check in `collect_report_entries()` — added trailing `os.sep` to prevent prefix collision
- `ODOO_WORKFLOW` environment variable validation — now catches non-integer values and enforces range (0, 1, 2)
- Rendering test exception handling — replaced fragile string-matching with `FileNotFoundError` / `RPCError`

## Version 0.9.1 (19.03.2026)

### Changed
- Comprehensive CLI `--help` documentation: workflows, .env variables, quick start guide, `--select` usage
- Python minimum version raised to >= 3.12 (pyproject.toml, classifiers, ruff, mypy)
- README updated with Python >= 3.12 prerequisite, UV tool install instructions, `--select` feature docs
- Updated `.project-tips` with current commands

## Version 0.9.0 (19.03.2026)

### Added
- Interactive YAML report selection for mapping mode via `--select` CLI flag
- New `list_yaml_reports()` function for displaying YAML files with metadata (filename, report_name, model)
- New `build_reports_from_yaml_objects()` for multi-company expansion (extracted from `collect_all_reports()`)
- New `parse_yaml_folder_with_filenames()` in odoo_report_helper for sorted filename-preserving YAML parsing
- 76 new tests for `EqOdooConnection` (map_reports, set_calculated_fields, collect, rendering, disable_qweb)
- 19 new tests for interactive selection, YAML listing, and helper functions
- Total test count: 344 (up from 249)

### Changed
- Refactored `map_reports()` into focused sub-methods: `_create_or_update_report()`, `_set_report_translations()`, `_map_report_fields()`, `_write_field_mappings()`
- Refactored `collect_all_reports()` to delegate to `build_reports_from_yaml_objects()`
- Refactored `parse_yaml_folder()` to delegate to `parse_yaml_folder_with_filenames()`
- Improved type hints: `IR_ACTIONS_REPORT=False` → `IR_ACTIONS_REPORT=None` for proper None semantics

### Fixed
- Removed dead code: unused `import base64`, unreferenced `self.connection.env["ir.model"]` calls, unused `base64.encodebytes` result
- Added logging in `get_company_language()` exception handler (previously silently swallowed)

## Version 0.8.0 (11.03.2026)

### Added
- Interactive report selection for `collect_yaml` mode — lists all FastReports in a table before export
- New `list_fast_reports()` method to query available FastReport entries across all companies
- New `collect_report_entries()` method with optional `report_ids` filter parameter
- Users can select specific reports (e.g. `1,3,5`) or export all (`all`, default)
- 12 new tests for interactive selection, report listing, and filtered collection

### Changed
- `collect_all_report_entries()` refactored as wrapper around `collect_report_entries()` for backward compatibility

## Version 0.7.2 (11.03.2026)

### Changed
- Migrate dependency from OdooRPC to odoorpc-toolbox (>= 0.7.0) — API-compatible, internalized OdooRPC
- Update import paths: `odoorpc.ODOO` → `odoorpc_toolbox.ODOO`, `odoorpc.error.RPCError` → `odoorpc_toolbox.RPCError`
- Update all test mocks to match new import paths
- Add PyYAML as explicit dependency (>= 6.0.1) instead of relying on transitive
- Raise python-dotenv minimum to >= 1.0.0
- Raise pytest to >= 8.0, pytest-cov to >= 5.0 in dev dependencies
- Update README.md and CLAUDE.md documentation references

### Fixed
- Path traversal protection in `parse_yaml_folder()` — validates resolved paths stay within target directory
- Port validation in `create_connection_from_env()` — validates numeric value and range (1-65535)

## Version 0.6.0 (2025)

### Added
- Company-language-aware attachment field resolution
- Multi-language support with Odoo locale codes and backward compatibility
- Comprehensive test suite (297 tests)

### Changed
- Migrate to pyproject.toml as single source of truth
- Update README for multi-language support

### Fixed
- Fix .env cwd discovery, add --init option, fix path traversal vulnerability
