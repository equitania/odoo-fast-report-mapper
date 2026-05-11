# External Integrations

**Analysis Date:** 2026-05-11

## APIs & External Services

**Odoo RPC (primary integration):**
- Service: Any Odoo instance (v12–v18+) with FastReport module installed
- Protocol: JSON-RPC over HTTPS (`jsonrpc+ssl`) or HTTP (`jsonrpc`)
  - Protocol auto-selected in `odoo_report_helper/utils.py:prepare_connection()` based on URL scheme
  - HTTP triggers a runtime warning about unencrypted credentials
- Transport: `odoorpc-toolbox >= 0.7.2` (internalized OdooRPC), provides `ODOO` class and `RPCError`
  - `ODOO` object created in `odoo_report_helper/utils.py:prepare_connection()`
  - Used in `odoo_report_helper/odoo_connection.py:OdooConnection`

**Odoo models accessed via RPC:**

| Odoo Model | Operations | Location |
|---|---|---|
| `ir.actions.report` | search, create, write, browse, `create_action()` | `odoo_connection.py:map_reports()` |
| `ir.model` | search, browse | `odoo_connection.py:map_reports()` |
| `ir.model.fields` | search, browse, write (`eq_report_ids`) | `odoo_connection.py:map_reports()` |
| `ir.module.module` | search (state=installed) | `odoo_connection.py:check_module()` |
| `eq_calculated_field_value` | search, create, write | `odoo_connection.py:set_calculated_fields()` |

**FastReport rendering (indirect — via Odoo ORM):**
- No direct HTTP call to FastReport API server
- Rendering is triggered by calling Odoo ORM methods (`eq_render_fast_report`) on `ir.actions.report` records
- The FastReport API server (`.NET`, typically on port 8899 in dev environments) is managed by Odoo; this tool only instructs Odoo to trigger it
- Test rendering invoked via `odoo_fast_report_mapper/eq_odoo_connection.py:EqOdooConnection.test_fast_report_rendering()`

## Authentication

**Auth Provider:**
- Odoo native authentication (no external IdP)
- Two supported methods, selected at `.env` load time in `odoo_fast_report_mapper/eq_utils.py:create_connection_from_env()`:

| Method | Env var | Odoo version | Notes |
|---|---|---|---|
| Password | `ODOO_PASSWORD` | All versions | Classic username + password |
| API Key | `ODOO_API_KEY` | >= 14 only | Recommended for v16+; pre-login version gate in `eq_odoo_connection.py:check_api_key_compatibility()` |

- If both vars are set, `ODOO_API_KEY` takes precedence with a warning logged
- Password cleared from memory after successful login (`odoo_connection.py:login()` line 50)

## Data Storage

**Databases:**
- None local — all data lives in the target Odoo PostgreSQL database accessed via RPC
- No local SQLite or file-based store

**File Storage:**
- Local filesystem only: YAML report definitions (input) and exported YAML files (collect mode output)
- YAML files read with `yaml.safe_load()` and path-traversal protection in `odoo_report_helper/utils.py:parse_yaml_folder_with_filenames()`

**Caching:**
- None

## Environment Configuration

**Required env vars (`.env` file):**
```
ODOO_URL        # Odoo server URL, e.g. https://odoo.example.com
ODOO_PORT       # Port: 443 (HTTPS) or 8069 (HTTP)
ODOO_USER       # Odoo login username
ODOO_DATABASE   # Database name
ODOO_LANGUAGE   # Locale code: de_DE, en_US, fr_FR (legacy: ger, eng)
```

**Auth (one required):**
```
ODOO_PASSWORD   # Classic password
ODOO_API_KEY    # API key (Odoo >= 14, takes precedence over password if both set)
```

**Optional env vars:**
```
ODOO_WORKFLOW       # 0=mapping only (default), 1=testing only, 2=both
ODOO_COLLECT_YAML   # True = export reports from Odoo to YAML (default: False)
ODOO_DISABLE_QWEB   # True = disable QWeb reports after mapping (default: True)
```

**Secrets location:**
- `.env` file in working directory (or path supplied via `--env_path`)
- Generated via `odoo-fr-mapper --init`
- Must not be committed to version control (noted in generated template)

## Monitoring & Observability

**Error Tracking:**
- None (no Sentry or similar)

**Logs:**
- Python `logging` module; setup in `odoo_fast_report_mapper/logging_config.py`
- Default level: `INFO` (set in `odoo_fast_report_mapper.py:setup_logging()`)
- Structured log messages for all RPC operations and errors
- Progress bars via `tqdm` for batch operations (`odoo_fast_report_mapper/progress.py`)

## CI/CD & Deployment

**Hosting:**
- PyPI as `odoo-fast-report-mapper-equitania`
- Source: GitHub `equitania/odoo-fast-report-mapper`

**CI Pipeline:**
- GitHub Actions: `.github/workflows/test.yml`
- Triggers: push/PR to `main` and `develop` branches
- Matrix: Python 3.12 and 3.13 on `ubuntu-latest`
- Steps: uv install → ruff lint → ruff format check → mypy (non-blocking) → pytest with coverage
- Coverage report uploaded as artifact (Python 3.12 run only, 7-day retention)
- No automated PyPI publish step in CI (manual via twine)

## Webhooks & Callbacks

**Incoming:** None

**Outgoing:** None (all communication is client-initiated RPC to Odoo)

---

*Integration audit: 2026-05-11*
