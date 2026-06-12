# Phase 1: Package Consolidation — Pattern Map

**Mapped:** 2026-05-28
**Files analyzed:** 19 (8 new private submodules + 3 rewrites + 8 test creates/merges/updates)
**Analogs found:** 19 / 19 — every new file IS a move/merge from existing source(s)

---

## File Classification

| New / Modified File | Role | Data Flow | Source Analog(s) | Match Quality |
|---------------------|------|-----------|------------------|---------------|
| `odoo_fast_report_mapper/_exceptions.py` | exception-classes | n/a (pure types) | `odoo_report_helper/exceptions.py` | exact copy |
| `odoo_fast_report_mapper/_lang_utils.py` | utility module | transform | `odoo_fast_report_mapper/lang_utils.py` | exact rename |
| `odoo_fast_report_mapper/_logging.py` | singleton service | n/a (setup) | `odoo_fast_report_mapper/logging_config.py` | exact rename |
| `odoo_fast_report_mapper/_yaml_dumper.py` | utility class | transform | `eq_odoo_connection.py` lines 20–24 (extraction) | extract |
| `odoo_fast_report_mapper/_progress.py` | context manager | event-driven | `odoo_fast_report_mapper/progress.py` lines 1–15 + 98–135 | partial copy |
| `odoo_fast_report_mapper/_connection.py` | production class | request-response | `eq_odoo_connection.py` (primary) + `odoo_report_helper/odoo_connection.py` (inline methods) | merge |
| `odoo_fast_report_mapper/_report.py` | data container | transform | `eq_report.py` (primary) + `odoo_report_helper/report.py` (add_* methods) | merge |
| `odoo_fast_report_mapper/_utils.py` | factory + loaders | request-response | `eq_utils.py` (primary) + `odoo_report_helper/utils.py` (helper functions) | merge |
| `odoo_fast_report_mapper/__init__.py` | public API re-export | n/a | existing `__init__.py` (rewrite) | rewrite |
| `odoo_fast_report_mapper/odoo_fast_report_mapper.py` | CLI entry point | request-response | self (update imports only) | update |
| `pyproject.toml` | build config | n/a | self (remove `odoo_report_helper*` entries) | update |
| `tests/test_connection.py` | test file | request-response | `test_eq_odoo_connection.py` (primary) + `test_odoo_connection.py` | merge |
| `tests/test_report.py` | test file | transform | `test_eq_report.py` (primary) + `test_report.py` | merge |
| `tests/test_utils.py` | test file | request-response | `test_eq_utils.py` (primary) + `test_helper_utils.py` | merge |
| `tests/test_exceptions.py` | test file | n/a | `tests/test_exceptions.py` (update import path only) | update |
| `tests/test_lang_utils.py` | test file | transform | `tests/test_lang_utils.py` (update import path only) | update |
| `tests/test_logging.py` | test file | n/a | `tests/test_logging.py` (update import path only) | update |
| `tests/test_progress.py` | test file | event-driven | `tests/test_progress.py` lines 115–145 only | cut |
| `tests/conftest.py` | test fixtures | n/a | self (update mock patch paths only) | update |

---

## Pattern Assignments

### `odoo_fast_report_mapper/_exceptions.py` (exception-classes)

**Source:** `odoo_report_helper/exceptions.py` — copy verbatim, no changes.

**Complete file pattern** (lines 1–14):
```python
# Copyright 2014-now Equitania Software GmbH - Pforzheim - Germany
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).


class OdooConnectionError(Exception):
    pass


class PathDoesNotExistError(Exception):
    pass


# Backward-compatibility alias for the historical misspelling (typo: "Exit" → "Exist")
PathDoesNotExitError = PathDoesNotExistError
```

**Note:** All three symbols migrate. The alias must be preserved for backward compatibility.

---

### `odoo_fast_report_mapper/_lang_utils.py` (utility module, transform)

**Source:** `odoo_fast_report_mapper/lang_utils.py` — rename only, content identical.

**File header pattern** (lines 1–10):
```python
# Copyright 2014-now Equitania Software GmbH - Pforzheim - Germany
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

"""
Language utility functions for multi-language support.
...
"""
```

**All symbols to carry over** (full file, 121 lines):
- `LEGACY_LANG_MAP` dict (lines 13–16)
- `normalize_language_code(lang_code: str) -> str` (lines 19–28)
- `normalize_name_dict(name_dict: dict) -> dict` (lines 31–46)
- `get_primary_lang(name_dict: dict, preferred_lang: str = "de_DE") -> str` (lines 49–67)
- `build_name_search_domain(name_dict: dict) -> list` (lines 70–90)
- `resolve_attachment_value(attachment, company_lang, fallback_lang=None)` (lines 93–120)

**Nothing changes except the filename.** Consumers import from `._lang_utils`.

---

### `odoo_fast_report_mapper/_logging.py` (singleton service)

**Source:** `odoo_fast_report_mapper/logging_config.py` — rename only, content identical.

**File header pattern** (lines 1–16):
```python
# Copyright 2014-now Equitania Software GmbH - Pforzheim - Germany
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

"""
Centralized logging configuration for odoo-fast-report-mapper.
...
"""

import logging
import logging.handlers
import sys
from pathlib import Path
from typing import Optional
```

**All symbols to carry over** (full file):
- `LogColors` class
- `ColoredFormatter(logging.Formatter)` class
- `LoggerManager` class (singleton, deferred refactor — copy verbatim per CONTEXT.md §Fragile Areas)
- Module-level functions: `get_logger()`, `setup_logging()`, `set_log_level()`, `get_log_file_path()`, `enable_debug_logging()`, `enable_verbose_logging()`, `enable_quiet_logging()`
- `_manager` module-level instance

**Nothing changes except the filename.** Consumers import from `._logging`.

---

### `odoo_fast_report_mapper/_yaml_dumper.py` (utility class, extract)

**Source:** `odoo_fast_report_mapper/eq_odoo_connection.py` lines 20–24 (extraction from that file).

**Complete extracted class** (`eq_odoo_connection.py` lines 20–24):
```python
class YAMLDumper(yaml.Dumper):
    """Custom YAML dumper for consistent indentation formatting."""

    def increase_indent(self, flow=False, indentless=False):
        return super().increase_indent(flow, False)
```

**Required imports for `_yaml_dumper.py`**:
```python
# Copyright 2014-now Equitania Software GmbH - Pforzheim - Germany
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

"""Custom YAML dumper with consistent indentation formatting."""

import yaml
```

**Note:** The `super().increase_indent(flow, False)` call is NOT eliminated — it calls `yaml.Dumper.increase_indent`, not the intra-package base class. This `super()` survives the merge.

---

### `odoo_fast_report_mapper/_progress.py` (context manager, event-driven)

**Source:** `odoo_fast_report_mapper/progress.py` — keep only header + `progress_bar()`.

**File header pattern** (`progress.py` lines 1–15, adapted):
```python
# Copyright 2014-now Equitania Software GmbH - Pforzheim - Germany
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

"""
Progress bar context manager for long-running operations.

Internal use only. Consumers should use tqdm directly.
"""

import sys
from collections.abc import Iterable
from typing import Any

from tqdm import tqdm
```

**Surviving function** (`progress.py` lines 98–134):
```python
def progress_bar(
    iterable: Iterable[Any],
    desc: str = "Processing",
    unit: str = "item",
    total: int | None = None,
    disable: bool = False,
    colour: str | None = None,
) -> Iterable[Any]:
    """
    Wrap an iterable with a progress bar.
    ...
    """
    return tqdm(
        iterable,
        desc=desc,
        unit=unit,
        total=total,
        disable=disable,
        colour=colour or "green",
        file=sys.stdout,
        dynamic_ncols=True,
    )
```

**What is deleted** from `progress.py` (do NOT include in `_progress.py`):
- `ProgressBar` class: lines 17–95 (79 LOC)
- `create_progress_bar()` factory: lines 137–159 (23 LOC)
- `ReportProgress` class: lines 162–208 (47 LOC)

---

### `odoo_fast_report_mapper/_connection.py` (production class, request-response)

**Primary source:** `odoo_fast_report_mapper/eq_odoo_connection.py` (Eq-version is canonical for all overridden methods)
**Inline from:** `odoo_report_helper/odoo_connection.py` (base-only methods: `__repr__`, `__str__`, `login`, `_get_fast_report_ids`, `check_module`)

**Imports pattern** — replace all cross-package imports with internal relative imports:

Current `eq_odoo_connection.py` lines 1–17:
```python
# Copyright 2014-now Equitania Software GmbH - Pforzheim - Germany
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
import os
from datetime import datetime
from random import choice

import yaml
from odoorpc_toolbox import RPCError

from odoo_fast_report_mapper.progress import progress_bar       # → from ._progress import progress_bar
from odoo_report_helper.odoo_connection import OdooConnection   # → DELETE this line

from . import eq_report                                          # → from . import _report (or from ._report import Report)
from .lang_utils import build_name_search_domain, get_primary_lang, resolve_attachment_value
                                                                 # → from ._lang_utils import ...
from .logging_config import get_logger                           # → from ._logging import get_logger
```

**After replacement** (target imports for `_connection.py`):
```python
import os
from datetime import datetime
from random import choice

import yaml
from odoorpc_toolbox import RPCError

from ._lang_utils import build_name_search_domain, get_primary_lang, resolve_attachment_value
from ._logging import get_logger
from ._progress import progress_bar
from ._utils import prepare_connection
from ._yaml_dumper import YAMLDumper
```

**Class declaration pattern** — drop inheritance, rename class:

Current `eq_odoo_connection.py` line 27:
```python
class EqOdooConnection(OdooConnection):
```
Becomes:
```python
class OdooConnection:
```

**Constructor pattern** — merged `__init__` must absorb both base and Eq init bodies.

Base `__init__` (`odoo_report_helper/odoo_connection.py` lines 17–30) sets:
- `self.username`, `self.password`, `self.database`, `self.version = ""`
- `self.connection = utils.prepare_connection(url, port)` (with `URLError` → `OdooConnectionError`)

Eq `__init__` (`eq_odoo_connection.py` lines 28–47) additionally sets:
- `self.url`, `self.port`, `self.language`, `self.collect_yaml`, `self.disable_qweb`, `self.workflow`, `self.auth_method`
- Currently calls `super().__init__(url, port, *args, **kwargs)` to set the base attrs

**Merged constructor target** (no `super()`, explicit params):
```python
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
    self.url = url
    self.port = port
    self.username = username
    self.password = password
    self.database = database
    self.version = ""
    self.language = language
    self.collect_yaml = collect_yaml
    self.disable_qweb = disable_qweb
    self.workflow = workflow
    self.auth_method = auth_method
    try:
        self.connection = prepare_connection(url, port)
    except urllib.error.URLError as ex:
        self.password = None
        raise OdooConnectionError(
            "ERROR: Please check your parameters and your connection" + " " + str(ex)
        ) from ex
```

**Also add `import urllib.error`** at the top (currently done transitively via `odoo_report_helper`).

**Methods to inline from base** (`odoo_report_helper/odoo_connection.py`):

`__repr__` (line 32–33):
```python
def __repr__(self):
    return f"OdooConnection(username={self.username!r}, database={self.database!r})"
```

`__str__` (line 35–36):
```python
def __str__(self):
    return self.__repr__()
```

`login` (lines 38–55): copy verbatim, replacing `exceptions.OdooConnectionError` with `OdooConnectionError` from `._exceptions`:
```python
def login(self):
    try:
        self.connection.login(self.database, self.username, self.password)
        self.connection.config["auto_commit"] = True
        self.connection.env.context["active_test"] = False
        self.connection.env.context["tracking_disable"] = True
        self.version = self.connection.version.split(".")[0]
        self.password = None
        logger.info(f"Connected to database: {self.database}")
    except RPCError as ex:
        raise OdooConnectionError(
            "ERROR: Please check your parameters and your connection" + " " + str(ex)
        ) from ex
```

`_get_fast_report_ids` (lines 172–179) and `check_module` (lines 181–188): copy verbatim, replacing `exceptions.OdooConnectionError` with `OdooConnectionError`.

**`_search_report_v13` fragile method** — copy verbatim, zero edits to body (CONS-02 / R-05).

**`YAMLDumper` extraction** — remove from `_connection.py`, replace usage with:
```python
from ._yaml_dumper import YAMLDumper
```

---

### `odoo_fast_report_mapper/_report.py` (data container, transform)

**Primary source:** `odoo_fast_report_mapper/eq_report.py` (Eq-version is canonical for `__init__`, `self_ensure`, `ensure_data_for_yaml`)
**Add from base:** `odoo_report_helper/report.py` methods `add_fields`, `add_calculated_fields`, `add_dependencies` (lines 53–87)

**Imports pattern** — replace cross-package import:

Current `eq_report.py` lines 1–7:
```python
from odoo_report_helper.report import Report   # → DELETE

from .lang_utils import get_primary_lang       # → from ._lang_utils import get_primary_lang
```

**After replacement**:
```python
# Copyright 2014-now Equitania Software GmbH - Pforzheim - Germany
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from ._lang_utils import get_primary_lang
from ._utils import self_clean
```

**Class declaration** — drop inheritance, rename:
```python
# Current eq_report.py:
class EqReport(Report):
# Becomes:
class Report:
```

**Constructor** — `EqReport.__init__` does NOT call `super().__init__()` (anti-pattern noted in ARCHITECTURE.md). The Eq `__init__` (`eq_report.py` lines 10–51) is the sole constructor. Copy it verbatim; rename class only.

**`add_fields` method** (from `odoo_report_helper/report.py` lines 53–65):
```python
def add_fields(self, field_dict: dict):
    """Set fields for the report and clean them (remove duplicates)."""
    for model, fields in field_dict.items():
        self._fields[model] = fields
    self._fields = self_clean(self._fields)
```

**`add_calculated_fields` method** (from `odoo_report_helper/report.py` lines 67–79) — copy verbatim (BUG-02 is Phase 1.1, NOT fixed here):
```python
def add_calculated_fields(self, field_dict):
    """Add calculated fields for the report and clean them."""
    for field_name, content in field_dict.items():
        self._calculated_fields[field_name] = content
    self._calculated_fields = self_clean(self._calculated_fields)
```

**`add_dependencies` method** (from `odoo_report_helper/report.py` lines 81–87):
```python
def add_dependencies(self, dependency_list: list):
    """Add dependencies to self._dependencies."""
    self._dependencies = self._dependencies + dependency_list
    self._dependencies = list(set(self._dependencies))
```

**Note on `self_clean` import:** `add_fields` and `add_calculated_fields` currently call `utils.self_clean(...)` via `from . import utils` (base package). After the merge, `self_clean` lives in `_utils.py`. Import it directly: `from ._utils import self_clean`.

---

### `odoo_fast_report_mapper/_utils.py` (factory + loaders, request-response)

**Primary source:** `odoo_fast_report_mapper/eq_utils.py` (376 lines)
**Absorb from:** `odoo_report_helper/utils.py` (121 lines) — functions: `prepare_connection`, `fire_all_functions`, `self_clean`, `parse_yaml`, `parse_yaml_folder_with_filenames`, `parse_yaml_folder`

**Imports pattern** — replace cross-package imports:

Current `eq_utils.py` lines 1–16:
```python
import odoo_report_helper.exceptions as exceptions   # → from ._exceptions import OdooConnectionError, PathDoesNotExistError
import odoo_report_helper.utils as utils             # → inline the utils functions directly into this file

from . import eq_odoo_connection, eq_report          # → from ._connection import OdooConnection; from ._report import Report
from .lang_utils import normalize_language_code, normalize_name_dict
                                                     # → from ._lang_utils import normalize_language_code, normalize_name_dict
from .logging_config import get_logger               # → from ._logging import get_logger
```

**Helper functions from `odoo_report_helper/utils.py`** to include verbatim at top of `_utils.py` (before factory functions):
```python
# From odoo_report_helper/utils.py — integrated into _utils.py
import logging
import os
from urllib.parse import urlparse

import yaml
from odoorpc_toolbox import ODOO

logger_helper = logging.getLogger(__name__)  # or reuse the eq_utils logger


def prepare_connection(url, port):
    """Build the OdooRPC connection object."""
    # ... full body from odoo_report_helper/utils.py lines 14–51 verbatim


def fire_all_functions(function_list: list):
    # ... lines 54–60 verbatim


def self_clean(input_dictionary: dict) -> dict:
    # ... lines 63–72 verbatim (BUG-02 body — do NOT fix)


def parse_yaml(yaml_file):
    # ... lines 75–87 verbatim


def parse_yaml_folder_with_filenames(path):
    # ... lines 90–111 verbatim


def parse_yaml_folder(path):
    # ... lines 114–120 verbatim
```

**`create_connection_from_env` factory** (currently `eq_utils.py` line 212): update return type from `EqOdooConnection` to `OdooConnection`, update instantiation call:
```python
# Current (eq_utils.py ~line 341):
conn = eq_odoo_connection.EqOdooConnection(
    language=..., collect_yaml=..., ...
)
# After:
conn = OdooConnection(
    language=..., collect_yaml=..., ...
)
```

**Note on `_utils.py` size:** Combined ~376 + ~121 LOC minus overlap ≈ 450–480 LOC. Create as a single file first per D-03 discretion guidance. Only split if ruff/linter complaints arise.

---

### `odoo_fast_report_mapper/__init__.py` (public API re-export, rewrite)

**Source:** current `__init__.py` (complete rewrite — current pattern shown for reference only).

**Current pattern** (lines 1–29) — old module-level re-exports:
```python
from . import eq_odoo_connection as eq_odoo_connection
from . import eq_report as eq_report
from . import eq_utils as eq_utils
from .__version__ import (...)
```

**Target pattern after Phase 1** (D-04):
```python
# Copyright 2014-now Equitania Software GmbH - Pforzheim - Germany
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from .__version__ import (
    __author__,
    __author_email__,
    __copyright__,
    __description__,
    __license__,
    __title__,
    __url__,
    __version__,
    __version_info__,
)
from ._connection import OdooConnection
from ._exceptions import OdooConnectionError, PathDoesNotExistError, PathDoesNotExitError
from ._report import Report
from ._utils import create_connection_from_env

__all__ = [
    # Version metadata
    "__version__",
    "__version_info__",
    "__title__",
    "__description__",
    "__author__",
    "__author_email__",
    "__url__",
    "__license__",
    "__copyright__",
    # Public API
    "OdooConnection",
    "Report",
    "create_connection_from_env",
    "OdooConnectionError",
    "PathDoesNotExistError",
    "PathDoesNotExitError",
]
```

**`__version__.py`** — do NOT touch; version bump to `1.0.0` is a separate task.

---

### `odoo_fast_report_mapper/odoo_fast_report_mapper.py` (CLI entry, update imports)

**Source:** self — update 3 import lines only, no logic changes.

**Current imports** (lines 9–11):
```python
from . import eq_utils
from .__version__ import __author__, __url__, __version__
from .logging_config import get_logger, setup_logging
```

**After update**:
```python
from . import _utils as _utils           # or: from . import _utils
from .__version__ import __author__, __url__, __version__
from ._logging import get_logger, setup_logging
```

**All `eq_utils.*` call sites** in the file body — replace `eq_utils.` with `_utils.`:
- Line 48: `eq_utils.generate_env_template(target_dir)` → `_utils.generate_env_template(target_dir)`
- Line 145: `eq_utils.create_connection_from_env(env_path=env_path)` → `_utils.create_connection_from_env(env_path=env_path)`
- Line 262: `eq_utils.list_yaml_reports(yaml_path)` → `_utils.list_yaml_reports(yaml_path)`
- Line 297: `eq_utils.build_reports_from_yaml_objects(selected_yamls)` → `_utils.build_reports_from_yaml_objects(selected_yamls)`
- Line 299: `eq_utils.collect_all_reports(yaml_path)` → `_utils.collect_all_reports(yaml_path)`

**Entry-point function name** `start_odoo_fast_report_mapper` — must NOT be renamed (it is the `pyproject.toml` entry point symbol).

**If CLI module is renamed to `_cli.py`** (D-03 discretion), update `pyproject.toml` lines 44–45:
```toml
odoo-fast-report-mapper = "odoo_fast_report_mapper._cli:start_odoo_fast_report_mapper"
odoo-fr-mapper = "odoo_fast_report_mapper._cli:start_odoo_fast_report_mapper"
```

---

### `pyproject.toml` (build config, update 3 sections)

**Section 1 — `[tool.setuptools.packages.find]`** (line 68):
```toml
# Current:
include = ["odoo_fast_report_mapper*", "odoo_report_helper*"]
# After:
include = ["odoo_fast_report_mapper*"]
```

**Section 2 — `[tool.coverage.run]`** (line 100):
```toml
# Current:
source = ["odoo_fast_report_mapper", "odoo_report_helper"]
# After:
source = ["odoo_fast_report_mapper"]
```

**Section 3 — `[tool.ruff.lint.isort]`** (line 82):
```toml
# Current:
known-first-party = ["odoo_fast_report_mapper", "odoo_report_helper"]
# After:
known-first-party = ["odoo_fast_report_mapper"]
```

**Everything else unchanged** — `fail_under = 60`, `[project.scripts]`, `[tool.mypy]` all stay as-is.

---

## Test File Patterns

### `tests/test_connection.py` (merge: `test_eq_odoo_connection.py` primary + `test_odoo_connection.py`)

**File header pattern** (`test_eq_odoo_connection.py` lines 1–17):
```python
# Copyright 2014-now Equitania Software GmbH - Pforzheim - Germany
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

"""Comprehensive tests for OdooConnection in odoo_fast_report_mapper/_connection.py."""

from unittest.mock import MagicMock, patch

import pytest
import yaml
from odoorpc_toolbox import RPCError

from odoo_fast_report_mapper._connection import OdooConnection, YAMLDumper
from odoo_fast_report_mapper._report import Report
from odoo_fast_report_mapper._utils import create_report_object_from_yaml_object
```

**Helper `_make_connection` pattern** (`test_eq_odoo_connection.py` lines 21–52) — update patch target and class name:
```python
def _make_connection(...):
    """Create an OdooConnection with a patched prepare_connection."""
    with patch("odoo_fast_report_mapper._utils.prepare_connection") as mock_prepare:
        ...
        conn = OdooConnection(
            language=language, collect_yaml=collect_yaml, ...
        )
    conn.version = "18"
    return conn
```

**Critical patch target change** (R-02):
```python
# Old (test_eq_odoo_connection.py line 33):
with patch("odoo_report_helper.odoo_connection.utils.prepare_connection") as mock_prepare:
# New:
with patch("odoo_fast_report_mapper._utils.prepare_connection") as mock_prepare:
```

### `tests/test_report.py` (merge: `test_eq_report.py` primary + `test_report.py`)

**Import update only**:
```python
# Old:
from odoo_fast_report_mapper.eq_report import EqReport
# New:
from odoo_fast_report_mapper._report import Report
```

### `tests/test_utils.py` (merge: `test_eq_utils.py` primary + `test_helper_utils.py`)

**Import update only**:
```python
# Old:
from odoo_fast_report_mapper.eq_utils import create_connection_from_env, ...
import odoo_report_helper.utils as utils
# New:
from odoo_fast_report_mapper._utils import (
    create_connection_from_env,
    prepare_connection,
    self_clean,
    parse_yaml,
    parse_yaml_folder,
    ...
)
```

### `tests/test_exceptions.py` (update import path only)

```python
# Old:
from odoo_report_helper.exceptions import OdooConnectionError, PathDoesNotExistError
# New (via public API):
from odoo_fast_report_mapper import OdooConnectionError, PathDoesNotExistError, PathDoesNotExitError
# Or via private submodule:
from odoo_fast_report_mapper._exceptions import OdooConnectionError, PathDoesNotExistError
```

### `tests/test_lang_utils.py` (update import path only)

```python
# Old:
from odoo_fast_report_mapper.lang_utils import ...
# New:
from odoo_fast_report_mapper._lang_utils import ...
```

### `tests/test_logging.py` (update import path only)

```python
# Old:
from odoo_fast_report_mapper.logging_config import LoggerManager, get_logger, ...
# New:
from odoo_fast_report_mapper._logging import LoggerManager, get_logger, ...
```

### `tests/test_progress.py` (cut to ~30 LOC)

**Surviving content only** (`test_progress.py` lines 1–19 adapted + lines 120–145):

```python
# Copyright 2014-now Equitania Software GmbH - Pforzheim - Germany
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

"""Tests for odoo_fast_report_mapper/_progress.py - Progress bar context manager."""

import io
from unittest.mock import patch

from odoo_fast_report_mapper._progress import progress_bar   # ← updated import path

_devnull = io.StringIO()
```

**Keep `TestProgressBarFunction` verbatim** (`test_progress.py` lines 120–145, 4 tests):
```python
class TestProgressBarFunction:
    """Verify progress_bar wraps iterables."""

    def test_progress_bar_wraps_iterable(self): ...
    def test_progress_bar_wraps_empty_iterable(self): ...
    def test_progress_bar_wraps_string_iterable(self): ...
    def test_progress_bar_preserves_order(self): ...
```

**Patch path for surviving tests** — update any `patch("odoo_fast_report_mapper.progress.sys.stdout")` to `patch("odoo_fast_report_mapper._progress.sys.stdout")`.

**Delete entirely**: `TestProgressBar` (lines 27–113), `TestCreateProgressBar` (lines 152–188), `TestReportProgress` (lines 195–249).

### `tests/conftest.py` (update mock patch path — critical)

**Critical fixture update** (`conftest.py` line 188) — R-02:
```python
# Old (conftest.py line 188):
with patch("odoo_report_helper.utils.ODOO") as mock_odoo_cls:
# New:
with patch("odoo_fast_report_mapper._utils.ODOO") as mock_odoo_cls:
```

All other fixture content (`sample_report_yaml_data`, `tmp_yaml_dir`, `tmp_env_file`, etc.) is unchanged — those fixtures hold data, not import paths.

---

## Shared Patterns

### Copyright Header
**Source:** Any file in either package (all identical)
**Apply to:** Every new `_*.py` file created in Wave 1 and later
```python
# Copyright 2014-now Equitania Software GmbH - Pforzheim - Germany
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
```

### Module Docstring
**Source:** `lang_utils.py` lines 4–10 (best example of the module docstring convention)
**Apply to:** All new private submodule files
```python
"""
<One-sentence description of module purpose>.

<Optional: 2–3 lines of details about what the module provides.>
"""
```

### Relative Import Convention
**Source:** `eq_odoo_connection.py` lines 13–16 (current within-package imports)
**Apply to:** All new `_*.py` files

All imports of sibling modules use dot-relative syntax:
```python
from ._lang_utils import build_name_search_domain, get_primary_lang
from ._logging import get_logger
from ._progress import progress_bar
from ._utils import prepare_connection
from ._yaml_dumper import YAMLDumper
from ._exceptions import OdooConnectionError, PathDoesNotExistError
```

Never use absolute `odoo_fast_report_mapper._utils` paths within the package itself.

### Logger Instantiation
**Source:** `eq_odoo_connection.py` line 17, `odoo_fast_report_mapper.py` line 15
**Apply to:** Any new module-level file that emits log messages
```python
logger = get_logger(__name__)
```

### Error Wrapping Pattern
**Source:** `odoo_report_helper/odoo_connection.py` lines 23–30 (connection) and lines 52–55 (login)
**Apply to:** `_connection.py` constructor and `login()` — copy verbatim
```python
except urllib.error.URLError as ex:
    self.password = None
    raise OdooConnectionError(
        "ERROR: Please check your parameters and your connection" + " " + str(ex)
    ) from ex
```

### Test Helper Factory Pattern
**Source:** `test_eq_odoo_connection.py` lines 21–52 (`_make_connection` helper)
**Apply to:** `tests/test_connection.py` merged file — update class name and patch target, keep the helper function shape
```python
def _make_connection(...):
    """Create an OdooConnection with a patched prepare_connection."""
    with patch("odoo_fast_report_mapper._utils.prepare_connection") as mock_prepare:
        mock_connection = MagicMock()
        mock_connection.version = "18.0"
        mock_connection.config = {}
        mock_connection.env.context = {}
        mock_prepare.return_value = mock_connection
        conn = OdooConnection(language=..., ...)
    conn.version = "18"
    return conn
```

---

## No Analog Found

None. Every file in Phase 1 is a move, rename, merge, or targeted update of an existing file. All patterns have direct source analogs.

---

## Behavior-Freeze Guard (Phase 1.1 Safety)

The following methods must be copied **verbatim** (no logic changes, even if the bug is obvious):

| Method | Location in source | Bug tracked as | Phase 1.1 fix |
|--------|-------------------|----------------|---------------|
| `self_clean` | `odoo_report_helper/utils.py` lines 63–72 | BUG-02 | Yes |
| `add_calculated_fields` | `odoo_report_helper/report.py` lines 67–79 | BUG-02 | Yes |
| `add_field_to_dictionary` | `eq_odoo_connection.py` (~line 601) | BUG-01 | Yes |
| `check_dependencies` (Eq-version) | `eq_odoo_connection.py` | BUG-03 | Yes |
| `_search_report_v13` | `eq_odoo_connection.py` lines 119–127 | fragile v13 support | Never touch |

---

## Metadata

**Analog search scope:** `odoo_fast_report_mapper/`, `odoo_report_helper/`, `tests/`
**Files read for pattern extraction:** 14 source files + `pyproject.toml` + `tests/conftest.py` + 2 test files
**Pattern extraction date:** 2026-05-28
