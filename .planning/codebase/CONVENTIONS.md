# Coding Conventions

**Analysis Date:** 2026-05-11

## Copyright Header

Every source file **must** begin with the Equitania copyright header (no exceptions):

```python
# Copyright 2014-now Equitania Software GmbH - Pforzheim - Germany
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
```

This applies to all `.py` files in `odoo_fast_report_mapper/` and `odoo_report_helper/`. Test files also carry the header.

## Naming Patterns

**Files:**
- `snake_case.py` throughout — e.g., `odoo_connection.py`, `lang_utils.py`, `logging_config.py`
- Equitania-specific modules prefixed `eq_` — e.g., `eq_report.py`, `eq_odoo_connection.py`, `eq_utils.py`
- Test files: `test_<module>.py` matching the source module name

**Classes:**
- Standard library-style base classes: `OdooConnection`, `Report`, `LoggerManager`
- Equitania-extended subclasses prefixed `Eq`: `EqReport(Report)`, `EqOdooConnection(OdooConnection)`
- Formatter/Utility classes without prefix: `ColoredFormatter`, `YAMLDumper`, `LogColors`

**Functions and methods:**
- `snake_case` throughout
- Equitania-specific Odoo field/function names use `eq_` prefix: `eq_get_payment_terms`, `eq_calculated_field_value`, `eq_fr_core`, `eq_report_ids`, `eq_export_type`, `eq_ignore_images`, `eq_handling_html_fields`, `eq_multiprint`, `eq_print_button`

**Variables:**
- `snake_case`; Odoo model handles use `ALL_CAPS`: `IR_MODEL`, `IR_MODEL_FIELDS`, `IR_ACTIONS_REPORT`

**Private attributes:**
- Leading underscore for internal state: `_dependencies`, `_fields`, `_calculated_fields`, `_data_dictionary`, `_loggers`, `_instance`

## Code Style

**Formatter:** `ruff format`
- Quote style: double quotes
- Indent style: spaces (4)
- Line length: 120 characters (enforced by formatter; `E501` disabled in linter)

**Linter:** `ruff check`
- Config: `pyproject.toml` `[tool.ruff]` and `[tool.ruff.lint]`
- Rule sets: `E`, `W`, `F` (pyflakes/pycodestyle), `I` (isort), `UP` (pyupgrade), `B` (bugbear), `SIM` (simplify)
- Ignored: `E501` (line length), `SIM108` (ternary operator — readability preference)
- First-party packages: `odoo_fast_report_mapper`, `odoo_report_helper`

**Type checking:** `mypy`
- Config: `pyproject.toml` `[tool.mypy]`
- Target: Python 3.12
- `ignore_missing_imports = true` (lenient — external stubs not required)
- `warn_return_any = true`, `warn_unused_configs = true`
- mypy runs with `continue-on-error: true` in CI — failures are reported but do not block

**Run commands:**
```bash
uv run ruff check .          # lint
uv run ruff format .         # format
uv run ruff format --check . # CI format check
uv run mypy odoo_fast_report_mapper/ odoo_report_helper/
```

## Import Organization

**Order (enforced by ruff/isort):**
1. Standard library
2. Third-party (`yaml`, `click`, `odoorpc_toolbox`)
3. First-party (`odoo_fast_report_mapper`, `odoo_report_helper`)

**Intra-package imports:** relative for same-package modules:
```python
from . import exceptions, utils        # odoo_report_helper/odoo_connection.py
from .logging_config import get_logger # odoo_fast_report_mapper/eq_odoo_connection.py
from .lang_utils import build_name_search_domain
```

**Cross-package imports:** absolute:
```python
from odoo_report_helper.odoo_connection import OdooConnection
from odoo_report_helper.exceptions import OdooConnectionError
```

## Logging

**Framework:** Python stdlib `logging` via centralized `LoggerManager` singleton.

**Pattern — every module that logs:**
```python
# In odoo_report_helper/ modules (no centralized manager needed):
logger = logging.getLogger(__name__)

# In odoo_fast_report_mapper/ modules (use centralized manager):
from .logging_config import get_logger
logger = get_logger(__name__)
```

**Configuration:** `odoo_fast_report_mapper/logging_config.py`
- `LoggerManager` singleton (`__new__` pattern) manages all loggers
- Console: `ColoredFormatter` with ANSI colors per level (DEBUG=cyan, INFO=green, WARNING=yellow, ERROR=red, CRITICAL=bold red) — colors only when `sys.stdout.isatty()`
- File: `RotatingFileHandler`, 10 MB max, 5 backups, UTF-8, stored in `~/.odoo-fast-report-mapper/logs/`
- Date format: `%H:%M:%S %d.%m.%Y`
- `propagate = False` on all managed loggers (prevents double-logging)
- Public API: `get_logger(name)`, `setup_logging()`, `set_log_level()`, `enable_debug_logging()`, `enable_quiet_logging()`

## Error Handling

**Custom exceptions** (`odoo_report_helper/exceptions.py`):
- `OdooConnectionError` — network/auth failures
- `PathDoesNotExistError` — missing file/directory paths
- `PathDoesNotExitError` — backward-compat alias (historical typo: "Exit" → "Exist")

**Narrow catch scopes** — catch specific exception types, never bare `except`:
```python
except urllib.error.URLError as ex:
    self.password = None  # clear sensitive data
    raise OdooConnectionError("...") from ex

except RPCError as ex:
    raise OdooConnectionError("...") from ex

except yaml.YAMLError as exc:
    logger.error(f"YAML parsing error in file: {yaml_file}")
    logger.exception(exc)
    return False
```

**Exception chaining:** always use `raise ... from ex` to preserve traceback.

**Context in ValueError:** include path, variable name, or relevant value:
```python
raise ValueError(f"URL scheme must be http or https, got: {parsed.scheme!r}")
```

**Caught types in use:** `RPCError`, `urllib.error.URLError`, `yaml.YAMLError`, `KeyError`, `AttributeError`, `ValueError`, `IndexError` — all in narrow scopes.

## Security Patterns

**Password/credential hygiene:**
- Clear password from memory immediately after use:
  ```python
  self.password = None  # after login() or on connection failure
  ```

**Path traversal guards** (`odoo_report_helper/utils.py`):
```python
resolved_path = os.path.realpath(path)
file_path = os.path.realpath(os.path.join(resolved_path, file))
if not file_path.startswith(resolved_path + os.sep):
    logger.warning(f"Skipping file outside target directory: {file}")
    continue
```

**URL schema validation:**
```python
if parsed.scheme and parsed.scheme not in ("http", "https"):
    raise ValueError(f"URL scheme must be http or https, got: {parsed.scheme!r}")
```

**Plain HTTP warning** — when connecting via `http://`, emit a `logger.warning()` that credentials are unencrypted.

**Port validation:** enforce range 1–65535 before use.

**Workflow value validation:** validate `ODOO_WORKFLOW` env var values (0, 1, 2 only).

## YAML Handling

**Always `yaml.safe_load()`** — never `yaml.load()`:
```python
return yaml.safe_load(stream)   # odoo_report_helper/utils.py parse_yaml()
```

**Custom dumper:** `YAMLDumper(yaml.Dumper)` in `odoo_fast_report_mapper/eq_odoo_connection.py` overrides `increase_indent` for consistent indentation in exported YAML files.

**File I/O:** always `encoding="utf-8"`:
```python
with open(yaml_file, encoding="utf-8") as stream:
```

## Language Handling

**Module:** `odoo_fast_report_mapper/lang_utils.py`

**Rule:** normalize all incoming language codes before use:
```python
from odoo_fast_report_mapper.lang_utils import normalize_language_code, normalize_name_dict

normalize_language_code("ger")  # -> "de_DE"
normalize_language_code("eng")  # -> "en_US"
normalize_language_code("fr_FR")  # -> "fr_FR" (pass-through)
```

**`LEGACY_LANG_MAP`** maps `{"ger": "de_DE", "eng": "en_US"}` — both legacy and modern keys must be supported in YAML input.

**Report name dicts:** use `normalize_name_dict()` to convert all keys to Odoo locale codes. Canonical internal format is `{"de_DE": "...", "en_US": "..."}`.

**Primary language selection:** `get_primary_lang(name_dict, preferred_lang="de_DE")` — Equitania convention defaults to German.

**Attachment resolution:** `resolve_attachment_value(attachment, company_lang, fallback_lang)` handles both legacy string and new per-language dict format.

## Function Design

**Size:** functions focused on a single responsibility; helper factory functions (`_make_report()`) used in tests for DRY construction.

**Parameters:** use keyword-only and defaults for optional Odoo fields; mutable defaults guarded with `None` + body assignment:
```python
def __init__(self, ..., model_fields=None, calculated_fields=None):
    if calculated_fields is None:
        calculated_fields = {}
    if model_fields is None:
        model_fields = {}
```

**Return values:** functions return `False` on non-fatal parse failures (YAML), raise exceptions on fatal errors.

## Module Design

**Exports:** no `__all__` defined — all public names available.

**Package split:**
- `odoo_report_helper/` — base classes (`OdooConnection`, `Report`, `utils`, `exceptions`) reusable as a library
- `odoo_fast_report_mapper/` — Equitania-extended classes (`EqOdooConnection`, `EqReport`), CLI, logging, lang utils

**Docstrings:** Google-style with `Args:` and `Returns:` sections on public functions. Short inline comments for non-obvious logic. Module-level docstrings on utility modules.

---

*Convention analysis: 2026-05-11*
