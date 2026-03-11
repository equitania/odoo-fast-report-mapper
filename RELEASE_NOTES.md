# Release Notes

## Version 0.7.1 (11.03.2026)

### Changed
- Migrate dependency from OdooRPC to odoorpc-toolbox (>= 0.7.0) — API-compatible, internalized OdooRPC
- Remove explicit PyYAML dependency (now transitive via odoorpc-toolbox)
- Update import paths: `odoorpc.ODOO` → `odoorpc_toolbox.ODOO`, `odoorpc.error.RPCError` → `odoorpc_toolbox.RPCError`
- Update all test mocks to match new import paths
- Update README.md and CLAUDE.md documentation references

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
