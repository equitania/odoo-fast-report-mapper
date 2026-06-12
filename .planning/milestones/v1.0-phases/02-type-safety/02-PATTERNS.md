# Phase 2: Type Safety - Pattern Map

**Mapped:** 2026-05-29
**Files analyzed:** 10 (9 existing modules to annotate + 1 new file)
**Analogs found:** 10 / 10

---

## File Classification

| New/Modified File | Role | Data Flow | Closest Analog | Match Quality |
|-------------------|------|-----------|----------------|---------------|
| `_odoo_types.py` (NEW) | typed-definitions module | — | `_exceptions.py` (structure), `_progress.py` (import + module docstring style) | role-match |
| `_yaml_dumper.py` | utility / class | transform | itself (already partially annotated) | self |
| `_progress.py` | utility / function | transform | itself (already partially annotated) | self |
| `_lang_utils.py` | utility / functions | transform | itself (partially annotated — `normalize_language_code` typed, `normalize_name_dict` bare `dict`) | self |
| `_logging.py` | service / singleton | event-driven | itself (partially annotated — `setup_logger`, `get_logger` typed; singleton attrs missing) | self |
| `_report.py` | model / data container | CRUD | itself (partially annotated — `__init__` has some typed params, others bare) | self |
| `_utils.py` | utility / factory | request-response | itself (partially annotated — `_exceptions` imports typed, `os.getenv` unguarded) | self |
| `_connection.py` | service / RPC client | request-response + CRUD | itself (partially annotated — `auth_method: str` typed, init params bare) | self |
| `_cli.py` | controller / entry-point | request-response | itself (bare — no annotations beyond `click` decorator params) | self |
| `pyproject.toml` | config | — | existing `[tool.mypy]` section (3 keys → expand to strict + overrides) | self |

---

## Pattern Assignments

### `_odoo_types.py` (NEW — typed-definitions module)

**Analog:** `_exceptions.py` for file skeleton; `_progress.py` for module docstring + import style.

**File skeleton — from `_exceptions.py` (lines 1–4):**
```python
# Copyright 2014-now Equitania Software GmbH - Pforzheim - Germany
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).


```

**Module docstring style — from `_progress.py` (lines 4–5):**
```python
"""Progress bar context manager for long-running operations. Internal use only."""
```

**Import style for typing — from `_progress.py` (lines 7–10) adapted:**
```python
from __future__ import annotations

from typing import Any, Literal, TypedDict
```

**Established annotation style already in the codebase — union syntax (from `_progress.py` lines 17–18):**
```python
    total: int | None = None,
    colour: str | None = None,
```
Use `X | None` (not `Optional[X]`). This is the established style in `_progress.py`; replicate in `_odoo_types.py`.

**`TypedDict` body pattern to follow — D-06 shapes (not yet in codebase; copy from RESEARCH.md §`_odoo_types.py`):**
```python
class IrModelRecord(TypedDict, total=True):
    """ir.model record returned by Odoo RPC search_read calls."""
    id: int
    model: str
    name: str


class IrModelFieldsRecord(TypedDict, total=False):
    """ir.model.fields record. total=False: not all fields guaranteed in all Odoo versions."""
    id: int
    name: str
    ttype: str
    modules: str | Literal[False]  # Odoo returns False when no module sets the field


class ReportAction(TypedDict, total=True):
    """ir.actions.report record returned by browse/search_read."""
    id: int
    report_type: str
    model: str
    name: str
    ids: list[int]


class LanguageRecord(TypedDict, total=True):
    """res.lang record from get_installed_languages."""
    code: str
    name: str
```

**No-analog note:** There are no existing TypedDict definitions anywhere in the package. This file is genuinely new. The structural convention (copyright header, one-sentence docstring, `from __future__ import annotations` first after header) is extracted from the three already-clean modules (`_exceptions.py`, `__version__.py`, `_progress.py`).

---

### `_yaml_dumper.py` — 1 error (`no-untyped-def`)

**Analog:** itself. The only untyped def is `increase_indent` (line 12).

**Current state (lines 1–13):**
```python
# Copyright 2014-now Equitania Software GmbH - Pforzheim - Germany
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

"""Custom YAML dumper with consistent indentation formatting."""

import yaml


class YAMLDumper(yaml.Dumper):
    """Custom YAML dumper for consistent indentation formatting."""

    def increase_indent(self, flow=False, indentless=False):
        return super().increase_indent(flow, False)
```

**Fix pattern — add `from __future__ import annotations` (D-05) and annotate (D-04):**
```python
from __future__ import annotations

import yaml


class YAMLDumper(yaml.Dumper):
    """Custom YAML dumper for consistent indentation formatting."""

    def increase_indent(self, flow: bool = False, indentless: bool = False) -> None:
        return super().increase_indent(flow, False)
```
The return type is `None` because `Dumper.increase_indent` returns `None` (sets internal state).
Check `yaml.Dumper.increase_indent` signature in `types-PyYAML` stubs to confirm.

---

### `_progress.py` — 1 error (`no-any-return`)

**Analog:** itself. Already partially annotated — return type is the issue.

**Current state (lines 7–20):**
```python
from collections.abc import Iterable
from typing import Any

from tqdm import tqdm


def progress_bar(
    iterable: Iterable[Any],
    desc: str = "Processing",
    unit: str = "item",
    total: int | None = None,
    disable: bool = False,
    colour: str | None = None,
) -> Iterable[Any]:
```

**Fix pattern — change return type to `tqdm[Any]`:**
```python
from __future__ import annotations

from collections.abc import Iterable
from typing import Any

from tqdm import tqdm


def progress_bar(
    iterable: Iterable[Any],
    desc: str = "Processing",
    unit: str = "item",
    total: int | None = None,
    disable: bool = False,
    colour: str | None = None,
) -> tqdm[Any]:
```
`tqdm` ships `py.typed` + stubs (tqdm ≥ 4.66). `tqdm[Any]` is the concrete generic type.
`Iterable[Any]` is technically correct but triggers `no-any-return` because mypy infers the
actual `tqdm(...)` constructor returns `tqdm[Any]`, not the declared `Iterable[Any]`.

---

### `_lang_utils.py` — 7 errors (`type-arg` ×4, `no-untyped-def` ×1, `no-any-return` ×2)

**Analog:** itself. Already has full parameter annotations for `normalize_language_code` (line 19) and the `preferred_lang` param (line 49) — those are the model to follow for the bare-`dict` params.

**Established typed signature (lines 19–28) — copy this pattern for the untyped functions:**
```python
def normalize_language_code(lang_code: str) -> str:
    """Convert legacy 'ger'/'eng' to Odoo locale codes, pass through valid locales.

    Args:
        lang_code: Language code, either legacy ('ger', 'eng') or Odoo locale ('de_DE', 'fr_FR').

    Returns:
        Odoo locale code string.
    """
```

**Bare `dict` params to fix (lines 31, 49, 70, 95):**

| Line | Current signature | Fixed signature |
|------|------------------|-----------------|
| 31 | `normalize_name_dict(name_dict: dict) -> dict` | `normalize_name_dict(name_dict: dict[str, str]) -> dict[str, str]` |
| 49 | `get_primary_lang(name_dict: dict, preferred_lang: str = "de_DE") -> str` | `get_primary_lang(name_dict: dict[str, str], preferred_lang: str = "de_DE") -> str` |
| 70 | `build_name_search_domain(name_dict: dict) -> list` | `build_name_search_domain(name_dict: dict[str, str]) -> list[Any]` |
| 95 | `resolve_attachment_value(attachment, company_lang, fallback_lang=None)` | see below |

**`resolve_attachment_value` fix (line 95) — `no-untyped-def`:**
```python
from __future__ import annotations

from typing import Any

def resolve_attachment_value(
    attachment: str | dict[str, str],
    company_lang: str,
    fallback_lang: str | None = None,
) -> str:
```

**`no-any-return` in `get_primary_lang` and `build_name_search_domain`:**
- `get_primary_lang` returns `next(iter(name_dict))` — after narrowing `name_dict` to `dict[str, str]`, `iter` produces `str` keys, so the return is `str`. No `cast` needed.
- `build_name_search_domain` returns `list[Any]` (Odoo domain tuples are heterogeneous). `list[Any]` is a pre-justified Tier 2 type; add `# Any: Odoo domain tuples contain mixed types (str, str, str)` inline.

---

### `_logging.py` — 19 errors (`no-untyped-def` ×8, `has-type` ×2, `assignment` ×1, `no-any-return` ×2, other ×6)

**Analog:** itself. `setup_logger` (lines 106–115) and `get_logger` (lines 182–194) are already fully annotated — copy that signature style for the remaining methods.

**Established typed method signature (lines 106–115):**
```python
def setup_logger(
    self,
    name: str = "odoo_fast_report_mapper",
    level: int = logging.INFO,
    log_to_file: bool = True,
    log_to_console: bool = True,
    max_bytes: int = 10 * 1024 * 1024,
    backup_count: int = 5,
    colored_output: bool = True,
) -> logging.Logger:
```

**`has-type` fix — class-level annotations missing (lines 85–100):**
```python
class LoggerManager:
    _instance: LoggerManager | None = None  # under __future__, no quotes needed
    _initialized: bool                       # ADD THIS — set in __new__/__init__
    _loggers: dict[str, logging.Logger]      # fix bare dict (line 100)
```

**`assignment` fix — `formatter` variable type widening (line 153–156):**
```python
# Add explicit annotation before the conditional:
formatter: logging.Formatter
if colored_output and sys.stdout.isatty():
    formatter = ColoredFormatter(console_format, datefmt=date_format)
else:
    formatter = logging.Formatter(console_format, datefmt=date_format)
```

**`__new__` return type — required under strict (line 87):**
```python
def __new__(cls) -> LoggerManager:
```

**Untyped methods to annotate (follow `setup_logger` style):**

| Method | Expected signature |
|--------|--------------------|
| `ColoredFormatter.format` (line 56) | `def format(self, record: logging.LogRecord) -> str:` |
| `set_level` (line 196) | `def set_level(self, level: int) -> None:` |
| `get_log_dir` | `def get_log_dir(self) -> Path:` |
| `configure` (if present) | `def configure(self, ...) -> None:` |
| `setup_logging` module-level fn | `def setup_logging(...) -> logging.Logger:` |

---

### `_report.py` — 10 errors (`no-untyped-def` ×6, `var-annotated` ×2, `type-arg` ×2)

**Analog:** itself. `__init__` (lines 12–57) already has `entry_name: dict[str, str]` and `report_name: str` typed — follow that established style for the remaining untyped params and methods.

**Established style (lines 14–21):**
```python
def __init__(
    self,
    entry_name: dict[str, str],
    report_name: str,
    report_type: str,
    model_name: str,
    company_id,           # ← UNTYPED — needs annotation
    eq_export_type="pdf", # ← UNTYPED — needs annotation
```

**Bare-typed params to annotate (`__init__` continuation):**
```python
    company_id: int | Literal[False],   # Odoo company_id; False = no company filter
    eq_export_type: str = "pdf",
    print_report_name: str | dict[str, str] = "Report",
    attachment: str | dict[str, str] = "Report.pdf",
    eq_ignore_images: bool = True,
    eq_handling_html_fields: str = "standard",
    multi: bool = False,
    attachment_use: bool = False,
    eq_print_button: bool = False,
    dependencies: list[str] | Literal[False] = False,
    model_fields: dict[str, list[str]] | None = None,
    calculated_fields: dict[str, Any] | None = None,
    eq_multiprint: str = "standard",
) -> None:
```

**`var-annotated` fix — bare `{}` on line 56:**
```python
self._data_dictionary: dict[str, Any] = {}  # Any: mixed Odoo field values
```

**Untyped methods to annotate:**

| Method | Expected signature |
|--------|--------------------|
| `self_ensure` (line 59) | `def self_ensure(self) -> None:` |
| `ensure_data_for_yaml` (line 89) | `def ensure_data_for_yaml(self) -> dict[str, Any]:` |
| `add_fields` (line 117) | already has `field_dict: dict` → fix to `field_dict: dict[str, list[str]]` |
| `add_calculated_fields` (line 131) | `def add_calculated_fields(self, field_dict: dict[str, Any]) -> None:` |
| `add_dependencies` (line 146) | `def add_dependencies(self, dependency_list: list[str]) -> None:` |

---

### `_utils.py` — 26 errors (`no-untyped-def` ×15, `no-untyped-call` ×6, `type-arg` ×3, `arg-type` ×2)

**Analog:** itself. Module header and import block (lines 1–25) are the established import pattern.

**Established import pattern (lines 1–25):**
```python
# Copyright 2014-now Equitania Software GmbH - Pforzheim - Germany
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

"""
Merged utility and factory functions for odoo-fast-report-mapper.
...
"""

import copy
import logging
import os
from urllib.parse import urlparse

import yaml
from dotenv import load_dotenv
from odoorpc_toolbox import ODOO

from ._exceptions import PathDoesNotExistError
from ._lang_utils import normalize_language_code, normalize_name_dict
from ._logging import get_logger
```

Add after the existing imports:
```python
from __future__ import annotations  # insert as first line after copyright block

from typing import Any
```

**`arg-type` fix — `os.getenv()` pattern (lines 470, 477):**
```python
# Pattern from Phase 1.1 BUG-05 fix in prepare_connection — replicate for remaining sites:
port_str = os.getenv("ODOO_PORT")
if port_str is None:
    raise ValueError("ODOO_PORT environment variable not set")
port = int(port_str)
```

**`type-arg` fix — bare `dict` / `list` in utility functions:**
```python
# Before
def self_clean(data: dict) -> dict:
# After
def self_clean(data: dict[str, list[str]]) -> dict[str, list[str]]:
```

**`no-untyped-def` dominant pattern — all public functions need param + return types.
For YAML-parsing functions (opaque return shapes), use `dict[str, Any]` (D-06 Tier 2):**
```python
def collect_yaml_files(path: str) -> list[dict[str, Any]]:
    ...

def prepare_connection(server_config: dict[str, Any]) -> dict[str, Any]:
    ...

def generate_env_template(target_dir: str) -> str:
    ...
```

---

### `_connection.py` — 64 errors (`no-untyped-def` ×30, `no-untyped-call` ×19, `type-arg` ×4, other ×11)

**Analog:** itself. `auth_method: str = "password"` (line 48) is the one typed param in `__init__`; use that established style.

**Established partial annotation (lines 37–60):**
```python
class OdooConnection:
    """
    Merged Odoo connection class — all connection, mapping, and collection logic
    in one place. No base-class inheritance.
    """

    def __init__(
        self,
        language,
        collect_yaml,
        disable_qweb,
        workflow,
        url,
        port,
        username,
        password,
        database,
        auth_method: str = "password",
    ):
```

**`__init__` fix pattern — annotate all bare params:**
```python
def __init__(
    self,
    language: str,
    collect_yaml: bool,
    disable_qweb: bool,
    workflow: int,
    url: str,
    port: int,
    username: str,
    password: str,
    database: str,
    auth_method: str = "password",
) -> None:
```

**`var-annotated` fix — lines 560–561 (from RESEARCH.md §fragile areas):**
```python
report_name_id_combination: dict[str, int] = {}    # report_name → ir.actions.report id
data_dictionary: dict[str, Any] = {}               # Any: nested Odoo report field data
```

**`union-attr` fix — Odoo `False`-sentinel pattern (lines 833, 850, 854):**
```python
# Before
report_object = IR_ACTIONS_REPORT.browse(report_id) if report_id else False
if report_object.report_type != "fast_report":

# After — explicit guard
report_object = IR_ACTIONS_REPORT.browse(report_id) if report_id else False
if report_object is False or report_object.report_type != "fast_report":
    continue
```

**TypedDict import at RPC-fetch sites (Tier 3 cast pattern):**
```python
from ._odoo_types import IrModelRecord, IrModelFieldsRecord, ReportAction, LanguageRecord
from typing import cast

# At RPC read boundary:
raw = env["ir.model"].search_read([("model", "=", model_name)], ["id", "model", "name"])
records = cast(list[IrModelRecord], raw)  # Any: Odoo RPC response — shape verified against Odoo docs
```

**`_search_report_v13` signature pattern (RESEARCH.md §fragile areas):**
```python
def _search_report_v13(
    self,
    model_name: str,
    report_name: dict[str, str],
    IR_ACTIONS_REPORT: Any | None = None,  # Any: odoorpc proxy object, no typed class
    company_id: int | None = None,
) -> int | Literal[False]:
```

**General method return type conventions for `_connection.py`:**

| Method category | Return type |
|----------------|-------------|
| Login / connection setup | `None` |
| Record search (returns id or False) | `int \| Literal[False]` |
| Record search (returns list) | `list[IrModelRecord]` or `list[Any]` |
| Mapping operations | `None` |
| Collection operations | `dict[str, Any]` |
| Dependency check | `tuple[bool, list[str]]` (post Phase 1.1 BUG-03 fix) |

---

### `_cli.py` — 10 errors (`no-untyped-def` ×3, `no-untyped-call` ×6, `type-arg` ×0, other ×1)

**Analog:** itself. `@click.command()`, `@click.option()` decorators are already present.
The 6 `no-untyped-call` errors are cascade — they disappear once the callees in other modules
are annotated. Only 3 genuine `no-untyped-def` remain.

**Current bare functions (lines 24–53):**
```python
def print_banner():
    """Print professional banner with version information"""
    ...

def init_callback(ctx, param, value):
    """Handle --init flag before other prompts."""
    ...
```

**Fix pattern — Click callback signature:**
```python
from __future__ import annotations

import click

def print_banner() -> None:
    """Print professional banner with version information."""
    ...

def init_callback(ctx: click.Context, param: click.Parameter, value: bool) -> None:
    """Handle --init flag before other prompts."""
    ...
```

The main `@click.command()` function itself does not need a return type annotation beyond `-> None`
(Click wraps it internally). All `click.option` callbacks follow `(ctx, param, value) -> None`.

---

### `pyproject.toml` — config change (Plan 02-01 setup commit)

**Analog:** existing `[tool.mypy]` section (3 keys).

**Current state:**
```toml
[tool.mypy]
python_version = "3.12"
warn_return_any = true
warn_unused_configs = true
ignore_missing_imports = true
```

**Target state (after Plan 02-01):**
```toml
[tool.mypy]
python_version = "3.12"
strict = true
# warn_return_any and warn_unused_configs are subsumed by strict = true
# ignore_missing_imports removed — replaced by targeted follow_untyped_imports override below

[[tool.mypy.overrides]]
module = "odoorpc_toolbox.*"
follow_untyped_imports = true   # reads source annotations from 0.7.3; no py.typed needed

# Per-module override ramp (removed one-by-one as each plan completes):
[[tool.mypy.overrides]]
module = "odoo_fast_report_mapper._yaml_dumper"
ignore_errors = true  # Plan 02-01

[[tool.mypy.overrides]]
module = "odoo_fast_report_mapper._progress"
ignore_errors = true  # Plan 02-01

[[tool.mypy.overrides]]
module = "odoo_fast_report_mapper._lang_utils"
ignore_errors = true  # Plan 02-02

[[tool.mypy.overrides]]
module = "odoo_fast_report_mapper._logging"
ignore_errors = true  # Plan 02-03

[[tool.mypy.overrides]]
module = "odoo_fast_report_mapper._report"
ignore_errors = true  # Plan 02-04

[[tool.mypy.overrides]]
module = "odoo_fast_report_mapper._utils"
ignore_errors = true  # Plan 02-05

[[tool.mypy.overrides]]
module = "odoo_fast_report_mapper._connection"
ignore_errors = true  # Plan 02-06 and 02-07

[[tool.mypy.overrides]]
module = "odoo_fast_report_mapper._cli"
ignore_errors = true  # Plan 02-08 (final)
```

**mypy version pin — also in Plan 02-01:**
```toml
# In [dependency-groups] dev section:
"mypy>=1.18",  # was "mypy>=1.0" — follow_untyped_imports requires 1.18; 1.19.1 installed
```

---

## Shared Patterns

### `from __future__ import annotations` (D-05)
**Source:** D-05 decision + `_progress.py` style (already uses modern `X | None` syntax).
**Apply to:** Every `_*.py` module as the first import after the copyright/license block.
**Placement rule:** Line 1 of imports (after copyright comment block), before all other imports.
```python
# Copyright 2014-now Equitania Software GmbH - Pforzheim - Germany
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

"""Module docstring."""

from __future__ import annotations   # ← always here, first import
```

### Typing Imports — Standard Block
**Source:** `_progress.py` lines 7–10 (established `collections.abc` + `typing` split).
**Apply to:** All modules that add new type annotations.
```python
from __future__ import annotations

from collections.abc import Iterable, Iterator   # prefer over typing.Iterable
from typing import Any, Literal, cast            # Any + cast for RPC boundaries
```
Never use deprecated `from typing import Dict, List, Optional, Tuple` — use built-in generics
and `X | None` syntax (stable under `__future__`).

### `dict[str, Any]` / `list[Any]` — Tier 2 Pre-Justified Annotation
**Source:** D-06 decision / D-07 policy.
**Apply to:** YAML loads, opaque RPC responses, recursive data structures.
**Rule:** No per-site `# Any:` comment needed for `dict[str, Any]` or `list[Any]` — the module
docstring of `_odoo_types.py` covers the pre-justification. All other explicit `Any` use
requires `# Any: <reason>` inline.

### `X | Literal[False]` — Odoo False-Sentinel Pattern
**Source:** RESEARCH.md §Pattern 4 + D-06 Tier 1.
**Apply to:** Any method that can return an Odoo record or `False` (not-found).
```python
from typing import Literal

def _search_report(self, ...) -> int | Literal[False]:
    ...
    return False  # Odoo convention: False = not found
```

### Copyright Header + Docstring Format
**Source:** `_exceptions.py` lines 1–3, `_progress.py` lines 1–5.
**Apply to:** `_odoo_types.py` (new file).
```python
# Copyright 2014-now Equitania Software GmbH - Pforzheim - Germany
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

"""One-line module description. Internal use only."""
```

### `cast()` at RPC Boundary — Tier 3 Pattern
**Source:** D-06 Tier 3 / RESEARCH.md §Pattern 8.
**Apply to:** `_connection.py` RPC-fetch methods only (never sprinkle).
```python
from typing import cast
from ._odoo_types import IrModelRecord

raw = env["ir.model"].search_read(domain, fields)
records = cast(list[IrModelRecord], raw)  # Any: Odoo RPC — shape matches IrModelRecord
```

---

## No Analog Found

All files have a clear analog (themselves, for existing modules; `_exceptions.py` + `_progress.py` skeleton for the new `_odoo_types.py`). No files are without pattern coverage.

---

## Metadata

**Analog search scope:** `odoo_fast_report_mapper/` (all 11 source files)
**Files scanned:** 11
**Pattern extraction date:** 2026-05-29
**Key finding:** The three already-clean modules (`_exceptions.py`, `__version__.py`, `__init__.py`) establish the structural skeleton. The partially-annotated modules (`_progress.py`, `_logging.py`, `_report.py`, `_lang_utils.py`) each contain the dominant annotation style — the pattern mapper's job is to extend what is already there, not introduce new conventions.
