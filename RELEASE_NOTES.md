# Release Notes

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
