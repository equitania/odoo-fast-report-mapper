<!-- refreshed: 2026-05-11 -->
# Architecture

**Analysis Date:** 2026-05-11

## System Overview

```text
┌─────────────────────────────────────────────────────────────────────┐
│                          CLI Entry Point                             │
│  `odoo_fast_report_mapper/odoo_fast_report_mapper.py`               │
│  Click command: start_odoo_fast_report_mapper()                      │
└──────────┬───────────────────┬──────────────────┬───────────────────┘
           │                   │                  │
           ▼                   ▼                  ▼
  create_connection_     collect_all_       list_yaml_reports()
  from_env()             reports()          build_reports_from_
  (eq_utils.py)          (eq_utils.py)      yaml_objects()
           │                   │                  │
           ▼                   ▼                  ▼
┌──────────────────────────────────────────────────────────────────────┐
│                    Equitania Extension Layer                          │
│  `odoo_fast_report_mapper/eq_odoo_connection.py`  EqOdooConnection   │
│  `odoo_fast_report_mapper/eq_report.py`           EqReport           │
│  `odoo_fast_report_mapper/eq_utils.py`            Factory/loader     │
│  `odoo_fast_report_mapper/lang_utils.py`          Language helpers   │
│  `odoo_fast_report_mapper/logging_config.py`      LoggerManager      │
│  `odoo_fast_report_mapper/progress.py`            ProgressBar/tqdm   │
└──────────┬───────────────────────────────────────────────────────────┘
           │ inherits / imports
           ▼
┌──────────────────────────────────────────────────────────────────────┐
│                       Base Helper Package                             │
│  `odoo_report_helper/odoo_connection.py`  OdooConnection (base)      │
│  `odoo_report_helper/report.py`           Report (base)              │
│  `odoo_report_helper/utils.py`            prepare_connection(),      │
│                                           parse_yaml_folder()        │
│  `odoo_report_helper/exceptions.py`       OdooConnectionError,       │
│                                           PathDoesNotExistError      │
└──────────┬───────────────────────────────────────────────────────────┘
           │ RPC via odoorpc-toolbox
           ▼
┌──────────────────────────────────────────────────────────────────────┐
│                        Odoo Server (remote)                           │
│  ir.actions.report, ir.model, ir.model.fields,                       │
│  eq_calculated_field_value, res.lang, res.company,                   │
│  ir.module.module, ir.config_parameter                               │
└──────────────────────────────────────────────────────────────────────┘
```

## Component Responsibilities

| Component | Responsibility | File |
|-----------|----------------|------|
| CLI | Click entry point, user I/O, workflow dispatch | `odoo_fast_report_mapper/odoo_fast_report_mapper.py` |
| `EqOdooConnection` | Eq-specific connection: API-key auth, report mapping/testing/collect, multi-company, translations | `odoo_fast_report_mapper/eq_odoo_connection.py` |
| `OdooConnection` | Base class: RPC setup, login, base `map_reports`, `set_calculated_fields`, `check_dependencies` | `odoo_report_helper/odoo_connection.py` |
| `EqReport` | Equitania report model: multi-language name dict, company_id, Eq-specific fields, YAML serialization | `odoo_fast_report_mapper/eq_report.py` |
| `Report` | Base report model: entry_name, report_name, fields dict, calculated fields, dependencies | `odoo_report_helper/report.py` |
| `eq_utils` | Factory functions: `create_connection_from_env()`, `collect_all_reports()`, YAML loaders, env template | `odoo_fast_report_mapper/eq_utils.py` |
| `lang_utils` | Language normalization (ger→de_DE), `get_primary_lang()`, `build_name_search_domain()`, `resolve_attachment_value()` | `odoo_fast_report_mapper/lang_utils.py` |
| `logging_config` | Singleton `LoggerManager`: colored console + rotating file logging at `~/.odoo-fast-report-mapper/logs/` | `odoo_fast_report_mapper/logging_config.py` |
| `progress` | tqdm wrappers: `progress_bar()`, `ProgressBar`, `ReportProgress` | `odoo_fast_report_mapper/progress.py` |
| `utils` (helper) | `prepare_connection()` (URL normalization + ODOO RPC init), `parse_yaml_folder()`, `self_clean()` | `odoo_report_helper/utils.py` |
| `exceptions` | `OdooConnectionError`, `PathDoesNotExistError` (+ `PathDoesNotExitError` alias) | `odoo_report_helper/exceptions.py` |

## Pattern Overview

**Overall:** Layered architecture with inheritance — base helper package provides reusable primitives; Equitania extension package adds product-specific logic. CLI is a thin orchestrator: it calls factory functions, displays UI, and delegates all business logic downward.

**Key Characteristics:**
- Two-package design: `odoo_report_helper` (reusable base) and `odoo_fast_report_mapper` (product layer)
- `eq_*` prefix marks all Equitania-specific extensions (classes, functions, fields, Odoo models)
- Stateless report objects (`EqReport`) carry YAML-loaded configuration and are passed to the connection for RPC execution
- Connection objects are stateful: they hold the live RPC session, version string, company language cache, and workflow flags

## Layers

**CLI Layer:**
- Purpose: User interaction, argument parsing, confirmation prompts, error display, workflow dispatch
- Location: `odoo_fast_report_mapper/odoo_fast_report_mapper.py`
- Contains: Single `@click.command`, banner/summary rendering, workflow if-branches
- Depends on: `eq_utils`, `logging_config`, `__version__`
- Used by: Console entrypoints `odoo-fast-report-mapper` and `odoo-fr-mapper`

**Equitania Extension Layer:**
- Purpose: Product-specific logic — multi-language support, API-key auth, multi-company switching, field mapping optimization, YAML collect/export
- Location: `odoo_fast_report_mapper/`
- Contains: `EqOdooConnection`, `EqReport`, factory utilities, language helpers, logging, progress
- Depends on: `odoo_report_helper` (base), `odoorpc_toolbox`, `yaml`, `tqdm`, `python-dotenv`
- Used by: CLI layer

**Base Helper Layer:**
- Purpose: Reusable, product-agnostic primitives for Odoo RPC connection management and report data modeling
- Location: `odoo_report_helper/`
- Contains: `OdooConnection`, `Report`, `utils`, `exceptions`
- Depends on: `odoorpc_toolbox`, `PyYAML`
- Used by: Equitania extension layer

**Configuration Layer:**
- Purpose: Load runtime config from `.env` file; YAML files supply report definitions
- Location: `.env` (user-managed), `connection_yaml/` (legacy, deprecated), `reports_yaml/` (user-supplied)
- Contains: env vars (`ODOO_URL`, `ODOO_PORT`, `ODOO_USER`, `ODOO_DATABASE`, `ODOO_LANGUAGE`, `ODOO_API_KEY`/`ODOO_PASSWORD`, `ODOO_WORKFLOW`, `ODOO_COLLECT_YAML`, `ODOO_DISABLE_QWEB`)
- Depends on: `python-dotenv` for loading
- Used by: `eq_utils.create_connection_from_env()`

## Data Flow

### Primary Request Path — Mapping (ODOO_WORKFLOW=0)

1. User runs `odoo-fr-mapper --yaml_path=./reports_yaml` → CLI entry (`odoo_fast_report_mapper.py:82`)
2. `eq_utils.create_connection_from_env()` loads `.env`, validates vars, instantiates `EqOdooConnection` (`eq_utils.py:212`)
3. CLI renders connection summary box and prompts user confirmation (`odoo_fast_report_mapper.py:173-205`)
4. `connection.check_api_key_compatibility()` — unauthenticated version gate for API-key auth (`eq_odoo_connection.py:49`)
5. `connection.login()` — RPC login, sets `auto_commit=True`, `tracking_disable=True`, captures Odoo major version (`odoo_connection.py:38`)
6. `eq_utils.collect_all_reports(yaml_path)` → `utils.parse_yaml_folder()` → YAML parsed → `build_reports_from_yaml_objects()` → list of `EqReport` objects (`eq_utils.py:199`)
7. `connection.map_reports(report_list)` orchestrates per-report processing (`eq_odoo_connection.py:156`):
   - `_create_or_update_report()` — dependency check, company switch, search/create/update `ir.actions.report`, `create_action()` (`eq_odoo_connection.py:193`)
   - `_set_report_translations()` — writes `name` and `print_report_name` per installed language using `with_context(lang=...)` (`eq_odoo_connection.py:260`)
   - `_map_report_fields()` — searches `ir.model`/`ir.model.fields` IDs, builds in-memory `models_fields` accumulator dict, calls `set_calculated_fields()` (`eq_odoo_connection.py:288`)
   - `_write_field_mappings()` — single batch write per model via `IR_MODEL.eq_write_report_ids()` (`eq_odoo_connection.py:352`)
8. If `disable_qweb=True`, `connection.disable_qweb_reports()` removes QWeb reports from print menu (`eq_odoo_connection.py:790`)

### Testing Flow (ODOO_WORKFLOW=1)

1. Steps 1–6 as above
2. `connection.test_fast_report_rendering(reports)` — for each report, finds `ir.actions.report` record, picks a random model record ID, calls `eq_render_fast_report()` RPC or `eq_render_fast_report_empty_db()` for empty databases (`eq_odoo_connection.py:726`)

### Collect/Export Flow (ODOO_COLLECT_YAML=True)

1. Steps 1–5 as above (no YAML loading)
2. `connection.list_fast_reports()` — returns all `fast_report` records across user companies for interactive selection (`eq_odoo_connection.py:432`)
3. User selects report IDs; `connection.collect_report_entries(yaml_path, report_ids)` iterates companies, fields, and builds `data_dictionary` (`eq_odoo_connection.py:484`)
4. Per-report: `create_eq_report_object()` assembles `EqReport` → `ensure_data_for_yaml()` → `write_yaml()` writes timestamped YAML file (`eq_odoo_connection.py:633`)

**State Management:**
- `EqOdooConnection` holds mutable state: RPC session (`self.connection`), `self.version`, `self._company_lang_cache` dict (populated lazily per company_id)
- `models_fields` dict is built in-memory during `map_reports()` across all reports, then flushed once in `_write_field_mappings()` — batch optimization
- Password/API key cleared from memory after successful login (`odoo_connection.py:50`)

## Key Abstractions

**`OdooConnection` / `EqOdooConnection` (inheritance):**
- Purpose: Represents an authenticated Odoo RPC session with report management operations
- Base: `odoo_report_helper/odoo_connection.py` — core RPC, login, base `map_reports`
- Extended by: `odoo_fast_report_mapper/eq_odoo_connection.py` — overrides `map_reports`, `_search_report`, `check_dependencies`, `set_calculated_fields`; adds `check_api_key_compatibility`, `get_installed_languages`, `get_company_language`, `collect_report_entries`, `test_fast_report_rendering`, `disable_qweb_reports`

**`Report` / `EqReport` (inheritance):**
- Purpose: Data container for a single report definition loaded from YAML
- Base: `odoo_report_helper/report.py` — plain string `entry_name`, base fields
- Extended by: `odoo_fast_report_mapper/eq_report.py` — `entry_name` is a dict (locale→name), adds `company_id`, `eq_export_type`, `eq_ignore_images`, `eq_handling_html_fields`, `eq_multiprint`, `eq_print_button`; overrides `self_ensure()` to build Eq-specific Odoo write dict; adds `ensure_data_for_yaml()` for round-trip YAML export

**`eq_utils.create_connection_from_env()` (factory):**
- Purpose: Single authoritative factory for `EqOdooConnection` from environment variables
- Location: `odoo_fast_report_mapper/eq_utils.py:212`
- Returns: `(EqOdooConnection, dotenv_path)` tuple

**`lang_utils` (language normalization):**
- Purpose: Abstracts the legacy `ger`/`eng` → `de_DE`/`en_US` migration and all multi-language name dict operations
- Key functions: `normalize_language_code()`, `normalize_name_dict()`, `get_primary_lang()`, `build_name_search_domain()`, `resolve_attachment_value()`
- Location: `odoo_fast_report_mapper/lang_utils.py`

## Entry Points

**CLI command:**
- Location: `odoo_fast_report_mapper/odoo_fast_report_mapper.py:82`
- Triggers: `odoo-fast-report-mapper` or `odoo-fr-mapper` shell commands (both registered in `pyproject.toml`)
- Responsibilities: Parse args, load `.env`, show confirmation, dispatch to connection methods

**`--init` flag:**
- Location: `odoo_fast_report_mapper/odoo_fast_report_mapper.py:42` (`init_callback`)
- Triggers: `odoo-fr-mapper --init`
- Responsibilities: Generate `.env` template in CWD via `eq_utils.generate_env_template()`

## Architectural Constraints

- **Threading:** Single-threaded. All RPC calls are synchronous via `odoorpc-toolbox`. No worker threads.
- **Global state:** `LoggerManager._instance` singleton at `odoo_fast_report_mapper/logging_config.py:215`. `_manager` module-level reference at line 215 is the permanent handle all `get_logger()` / `setup_logging()` calls use.
- **Circular imports:** `odoo_report_helper/odoo_connection.py` imports from `odoo_fast_report_mapper/lang_utils.py` — a cross-package upward dependency from base to extension layer. This is the only known circular-direction risk.
- **Odoo version branching:** Version-specific code paths exist in `EqOdooConnection` for Odoo 10 (`ir.actions.report.xml` model name) and 13–16 (`_search_report_v13` for company filtering). Branching is keyed on `self.version` string after login.
- **Company switching:** `connection.env.user.company_id` is mutated mid-operation during multi-company processing and restored via try/finally. This is stateful and not thread-safe.
- **Batch field write:** `_write_field_mappings()` accumulates all field→report ID associations across ALL reports before writing. This is intentional for performance (fewer RPC calls) but means partial failures leave field mappings un-written.

## Anti-Patterns

### Base Package Imports from Extension Package

**What happens:** `odoo_report_helper/odoo_connection.py` (base) imports `build_name_search_domain` from `odoo_fast_report_mapper/lang_utils.py` (extension) at line 9.
**Why it's wrong:** Creates an upward dependency — the base layer depends on the extension layer, breaking the layered architecture and preventing `odoo_report_helper` from being used independently.
**Do this instead:** Move `build_name_search_domain` to `odoo_report_helper/utils.py` or `odoo_report_helper/lang_utils.py` so the base layer only imports from itself.

### `EqReport` Does Not Call `super().__init__()`

**What happens:** `EqReport.__init__()` (`eq_report.py:34–51`) manually assigns all instance attributes instead of calling `super().__init__()` from `Report`.
**Why it's wrong:** Any future logic added to `Report.__init__()` will be silently bypassed, and the two classes can drift out of sync.
**Do this instead:** Call `super().__init__(...)` with the shared parameters and only set `EqReport`-specific attributes directly.

## Error Handling

**Strategy:** Fail-fast per report, continue processing remaining reports. Failed reports are collected as `(name, error_msg)` tuples returned from `map_reports()` and displayed as a summary at the end.

**Patterns:**
- `OdooConnectionError` raised on RPC/network failure during connection setup or login (`odoo_report_helper/exceptions.py`)
- `PathDoesNotExistError` raised when YAML directory is not found (`odoo_report_helper/exceptions.py`)
- `ValueError` raised by `create_connection_from_env()` for missing/invalid env vars; caught in CLI with user-friendly differentiated messages
- Per-report exceptions caught in `map_reports()` loop: `RPCError`, `KeyError`, `AttributeError`, `ValueError`, `IndexError` — logged, appended to `failed_reports`, loop continues
- Password/API key cleared from `self.password` after login (security)
- Path traversal guard in `collect_report_entries()`: output filenames verified with `os.path.realpath()` before write

## Cross-Cutting Concerns

**Logging:** Singleton `LoggerManager` (`logging_config.py`). All modules call `get_logger(__name__)`. Console output is colored (ANSI, TTY-detected). File output rotates at 10MB, keeps 5 backups at `~/.odoo-fast-report-mapper/logs/`. `odoo_report_helper` uses stdlib `logging.getLogger(__name__)` directly (not the custom manager).

**Language normalization:** All locale codes pass through `normalize_language_code()` / `normalize_name_dict()` at YAML load time (`eq_utils.py`). Legacy `ger`/`eng` keys are transparent to all downstream code.

**Validation:** Connection config validated in `create_connection_from_env()` before any RPC. Port range check (1–65535), workflow enum check (0/1/2), URL scheme check (`http`/`https` only in `utils.prepare_connection()`).

---

*Architecture analysis: 2026-05-11*
