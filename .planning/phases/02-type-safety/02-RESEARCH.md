# Phase 2: Type Safety - Research

**Researched:** 2026-05-29
**Domain:** Python static type checking — mypy strict mode, TypedDict, annotation ramp strategy
**Confidence:** HIGH (all key facts verified against live codebase and running tools)

---

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

- **D-01:** Phase 1.1 runs first, then Phase 2. Phase 2 execution is blocked until Phase 1.1 verifies green. (Phase 1.1 is now complete — unblocked as of 2026-05-29.)
- **D-02:** odoorpc-toolbox already upgraded to 0.7.3 (confirmed installed in `.venv`). No further action required.
- **D-03:** Strict-mode boundary for odoorpc-toolbox uses `follow_untyped_imports = true` (mypy ≥1.18). No per-call `# type: ignore`, no local stubs, no Facade-wrapper. NOTE: As measured below, odoorpc-toolbox generates **zero** errors in the current error set — all 130 errors are purely internal. D-03 remains the right policy, but the override block adds zero errors in practice.
- **D-04:** Module-by-module ramp with `[[tool.mypy.overrides]]` exemptions. `strict = true` enabled globally on day one. Each plan removes its own `[[overrides]]` block. Order: `_exceptions` → `_yaml_dumper` → `_progress` → `_lang_utils` → `_logging` → `_report` → `_utils` → `_connection` → `_cli`.
- **D-05:** `from __future__ import annotations` added project-wide at top of every `_*.py` module in the first ramp commit.
- **D-06:** TypedDict 3-tier pragma — Tier 1 TypedDict for recurring shapes (`IrModelRecord`, etc.) in `_odoo_types.py`. Tier 2 `dict[str, Any]` for opaque/dynamic responses. Tier 3 `cast`/`isinstance` at the RPC boundary.
- **D-07:** Implicit `Any` forbidden. Explicit `Any` requires `# Any: <reason>`. `dict[str, Any]` / `list[Any]` are pre-justified as RPC-boundary convention.

### Claude's Discretion

- Split `_utils.py` (517 LOC) or `_connection.py` (873 LOC) if annotations make them unwieldy.
- TypedDict may be inlined into consuming module if a shape is used in exactly one place.
- No mypy plugin needed (no Pydantic).

### Deferred Ideas (OUT OF SCOPE)

- `py.typed` marker PR to upstream `odoorpc-toolbox`.
- `_logging.LoggerManager._loggers` refactor.
- Pydantic for runtime validation.
- `beartype` / `typeguard`.
- Mypy plugin ecosystem.
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| TYPE-01 | `mypy --strict odoo_fast_report_mapper/` runs fehlerfrei. All errors resolved, not suppressed. | Baseline: 130 errors in 8 files (measured 2026-05-29 post-Phase-1.1). Module-by-module ramp with overrides enables sequential resolution. |
| TYPE-02 | Type annotations for all public functions and methods. `from __future__ import annotations` introduced project-wide. | 64 `no-untyped-def` errors across all files confirm all public/private methods need annotations. No `__future__` imports exist yet. |
| TYPE-03 | `pyproject.toml` `[tool.mypy]` updated to `strict = true`. Current config has only permissive settings. | Current `[tool.mypy]` has `python_version`, `warn_return_any`, `warn_unused_configs`, `ignore_missing_imports` — no `strict = true`. |
</phase_requirements>

---

## Summary

Phase 2 brings the consolidated `odoo_fast_report_mapper/` package to mypy strict mode with zero errors.
The Phase 1.1 prerequisite is complete (2026-05-29, all 347 tests green). The codebase is in a stable,
annotable state.

**Measured baseline (2026-05-29, post-Phase-1.1):** `mypy --strict` reports **130 errors in 8 files**
(11 source files total — 3 are already clean: `_exceptions.py`, `__init__.py`, `__version__.py`).
The dominant error class is `no-untyped-def` (64 occurrences, 49%), meaning missing function/method
signatures. The second class is `no-untyped-call` (32 occurrences, 25%), which are cascade errors:
once the underlying `no-untyped-def` is fixed, the corresponding `no-untyped-call` disappears
automatically. Fixing `no-untyped-def` across all modules is the primary work of this phase.

The odoorpc-toolbox boundary is a non-issue in practice: **zero** of the 130 errors originate
from odoorpc-toolbox imports. The D-03 `follow_untyped_imports` override block is correct policy
(prevents future regression if odoorpc-toolbox grows untyped methods) but contributes nothing to
the current error count. The `ignore_missing_imports = true` that is currently in `[tool.mypy]`
may be suppressing the odoorpc-toolbox boundary silently — the override is still the right approach
because `follow_untyped_imports` is strictly better than `ignore_missing_imports`.

Mypy 1.19.1 is installed (`uv run mypy --version` confirmed), which exceeds the 1.18 minimum
required for `follow_untyped_imports`. The mypy pin can be tightened to `mypy>=1.18` with no
runtime impact.

Python floor is 3.12 (`requires-python = ">=3.12"` in `pyproject.toml`), making
`from __future__ import annotations` safe to add globally (PEP 563 is stable in 3.12).

**Primary recommendation:** Sequence the ramp smallest-to-largest by error count, one module per plan,
removing each `[[overrides]]` block as it clears. The three already-clean modules (`_exceptions`,
`__init__`, `__version__`) require no annotation work — they can be verified clean in the initial
setup commit.

[VERIFIED: live codebase measurement 2026-05-29]

---

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Type annotation of public API | Package module layer | pyproject.toml config | Annotations live in source; config enables strict enforcement |
| mypy configuration | Build/config layer (`pyproject.toml`) | CI workflow (reads config) | Single source of truth; CI consumes, not overrides |
| TypedDict definitions | Package module layer (`_odoo_types.py`) | Consuming modules (`_connection.py`) | Centralised shapes; consuming modules import and use |
| odoorpc-toolbox boundary | mypy config `[[overrides]]` | None | Declarative config is sufficient; no runtime shim needed |
| `from __future__ import annotations` | Each `_*.py` module | None | PEP 563 is per-file; mechanical one-line addition |

---

## Empirical Error Baseline

### Full-Package Scan (2026-05-29, post-Phase-1.1)

```
uv run mypy --strict odoo_fast_report_mapper/ → 130 errors in 8 files (11 checked)
```

**Mypy version:** 1.19.1 (compiled) [VERIFIED: `uv run mypy --version`]

### Per-Module Error Distribution

| Module | LOC (approx) | Errors (total) | `no-untyped-def` | `no-untyped-call` | `type-arg` | Other |
|--------|-------------|----------------|-----------------|------------------|-----------|-------|
| `_connection.py` | 873 | **64** | 30 | 19 | 4 | 11 |
| `_utils.py` | 517 | **26** | 15 | 6 | 3 | 2 |
| `_logging.py` | 291 | **19** | 8 | 1 | 1 | 9 |
| `_report.py` | 147 | **10** | 6 | 0 | 2 | 2 |
| `_cli.py` | 341 | **10** | 3 | 6 | 0 | 1 |
| `_lang_utils.py` | 120 | **7** | 1 | 0 | 4 | 2 |
| `_progress.py` | 49 | **1** | 0 | 0 | 0 | 1 |
| `_yaml_dumper.py` | 13 | **1** | 1 | 0 | 0 | 0 |
| `_exceptions.py` | 14 | **0** | — | — | — | — |
| `__init__.py` | ~5 | **0** | — | — | — | — |
| `__version__.py` | ~3 | **0** | — | — | — | — |
| **TOTAL** | **~2373** | **138\*** | **64** | **32** | **14** | **28** |

\* The per-file grep counts sum to 138; mypy reports 130 because some lines have multiple errors on
the same location which the grep approach double-counts. The official number is 130.

[VERIFIED: live codebase measurement]

### Error Code Breakdown (package-wide)

| Error Code | Count | What It Means | Fix Pattern |
|------------|-------|--------------|-------------|
| `no-untyped-def` | 64 | Function/method missing annotation | Add param types + return type |
| `no-untyped-call` | 32 | Calling an untyped function | Disappears when callee's `no-untyped-def` is fixed |
| `type-arg` | 14 | Bare `dict` / `list` without type params | Change to `dict[str, Any]` or specific type |
| `no-any-return` | 5 | Function annotated non-Any but returns Any | Add explicit `cast` or narrow type |
| `union-attr` | 3 | Accessing attr on union that includes `bool` (Odoo `False`-sentinel) | Guard with `if report_object is not False:` or TypedDict |
| `var-annotated` | 6 | Bare `dict()` / `{}` literal, mypy cannot infer type | Add inline annotation `x: dict[str, Any] = {}` |
| `has-type` | 2 | `_initialized` set in `__new__` but type is lost (singleton pattern) | Add class-level annotation `_initialized: bool` |
| `assignment` | 2 | Type mismatch in assignment (1 in `_logging`, 1 in `_connection`) | Widen annotation or use `cast` |
| `arg-type` | 2 | `os.getenv()` returns `str | None` passed where `str` expected | Add `or ""` default or explicit guard |

[VERIFIED: live codebase measurement]

---

## Standard Stack

### Core (no new packages needed)

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| `mypy` | 1.19.1 (installed); pin to `>=1.18` | Static type checker | Enforces strict mode; `follow_untyped_imports` requires ≥1.18 |
| `types-PyYAML` | already in `dev` deps | Stubs for PyYAML | `yaml.safe_load`, `yaml.YAMLError` get proper types |

**No new runtime dependencies.** All annotation work uses stdlib `typing` / `collections.abc`.

### stdlib Typing Imports Needed

| Import | Used For | Notes |
|--------|----------|-------|
| `from typing import Any, TypedDict, cast, Literal, Optional` | TypedDict, cast, Odoo False-sentinel, Optional class attrs | `Optional[X]` = `X \| None`; use modern union syntax under `__future__` |
| `from collections.abc import Iterable, Iterator, Callable` | Generics for progress_bar, callable params | Preferred over `typing.Iterable` in Python 3.12 |
| `from typing import TYPE_CHECKING` | Guard circular imports in type-only contexts | Use if OdooConnection needs forward refs in `_report.py` |

**Installation:** No new packages. `types-PyYAML` is already installed.

[VERIFIED: pyproject.toml, Python 3.12 stdlib docs]

---

## Package Legitimacy Audit

This phase installs no new external packages. No legitimacy audit is required.

| Package | Action |
|---------|--------|
| `mypy>=1.18` | Already installed (1.19.1). Only the version pin in `pyproject.toml` changes. |
| `types-PyYAML` | Already in dev deps. No change. |

---

## Architecture Patterns

### System Architecture Diagram

```
pyproject.toml [tool.mypy]
      |
      | strict = true
      | overrides: odoorpc_toolbox.* → follow_untyped_imports
      |
      ↓
uv run mypy odoo_fast_report_mapper/
      |
      ├──> _exceptions.py  (0 errors — skip)
      ├──> __init__.py     (0 errors — skip)
      ├──> __version__.py  (0 errors — skip)
      |
      ├──> _yaml_dumper.py (1 error)   → Plan 02-01 (with setup commit)
      ├──> _progress.py   (1 error)   → Plan 02-01
      ├──> _lang_utils.py (7 errors)  → Plan 02-02
      ├──> _logging.py    (19 errors) → Plan 02-03
      ├──> _report.py     (10 errors) → Plan 02-04
      ├──> _utils.py      (26 errors) → Plan 02-05
      ├──> _connection.py (64 errors) → Plan 02-06 + 02-07
      └──> _cli.py        (10 errors) → Plan 02-08 (final — clears all overrides)
                                          ↓
                                    130 → 0 errors
```

Data flow: the ramp overrides block each module from strict enforcement until that module's plan
runs. Each plan removes its own override block. `_cli.py` is last because it imports all other
modules — once all callee modules are typed, all `no-untyped-call` cascade errors in `_cli.py`
disappear without any changes to `_cli.py` itself (except its own 3 `no-untyped-def` entries).

### Recommended Project Structure (new file only)

```
odoo_fast_report_mapper/
├── _odoo_types.py        # NEW — TypedDict shapes for Odoo RPC responses (D-06 Tier 1)
├── _exceptions.py        # Already clean
├── __version__.py        # Already clean
├── __init__.py           # Already clean
├── _yaml_dumper.py       # 1 error → Plan 02-01
├── _progress.py          # 1 error → Plan 02-01
├── _lang_utils.py        # 7 errors → Plan 02-02
├── _logging.py           # 19 errors → Plan 02-03
├── _report.py            # 10 errors → Plan 02-04
├── _utils.py             # 26 errors → Plan 02-05
├── _connection.py        # 64 errors → Plan 02-06/07
└── _cli.py               # 10 errors → Plan 02-08
```

### Pattern 1: Global Strict + Per-Module Override Ramp

**What:** `strict = true` in `[tool.mypy]` globally; pending modules get
`[[tool.mypy.overrides]]` blocks that suppress errors until that module's plan cleans them.

**When to use:** First commit of Phase 2 (setup commit). Each subsequent plan removes one block.

```toml
# pyproject.toml — initial state after setup commit
[tool.mypy]
python_version = "3.12"
strict = true

[[tool.mypy.overrides]]
module = "odoorpc_toolbox.*"
follow_untyped_imports = true

[[tool.mypy.overrides]]
module = "odoo_fast_report_mapper._yaml_dumper"
ignore_errors = true  # Plan 02-01

[[tool.mypy.overrides]]
module = "odoo_fast_report_mapper._progress"
ignore_errors = true  # Plan 02-01

# ... one block per pending module ...

[[tool.mypy.overrides]]
module = "odoo_fast_report_mapper._cli"
ignore_errors = true  # Plan 02-08 (last)
```

After each plan, remove the corresponding `[[overrides]]` block.
[ASSUMED — pattern derived from mypy docs and D-04 decision; specific TOML syntax verified against
mypy 1.x docs [CITED: mypy.readthedocs.io/en/stable/config_file.html]]

### Pattern 2: Fixing `no-untyped-def` (primary work)

**What:** Add parameter types and return type to every function/method.

**When to use:** Every function/method in every module.

```python
# Source: mypy strict mode requirements + Python 3.12 typing best practices
# BEFORE (generates no-untyped-def)
def normalize_name_dict(name_dict: dict) -> dict:
    ...

# AFTER (strict-compliant)
from __future__ import annotations
from typing import Any

def normalize_name_dict(name_dict: dict[str, Any]) -> dict[str, Any]:
    ...
```

### Pattern 3: `var-annotated` Fix for Empty Containers

**What:** Bare `dict()` / `{}` / `[]` literals need inline type annotation.

```python
# BEFORE — generates var-annotated
data_dictionary = {}

# AFTER — strict-compliant (Tier 2: dict[str, Any] for opaque RPC data)
data_dictionary: dict[str, Any] = {}
```

Key instances:
- `_connection.py:560` `report_name_id_combination = dict()` → `dict[str, int]`
- `_connection.py:561` `data_dictionary = {}` → `dict[str, Any]` (Tier 2, recursive RPC data)
- `_connection.py:167` `_company_lang_cache` → `dict[int, str]` (company_id → locale code)
- `_logging.py:100` `_loggers: dict` → `_loggers: dict[str, logging.Logger]`

### Pattern 4: Odoo `False`-Sentinel (`union-attr`)

**What:** Odoo RPC calls return `False` for "not found" instead of `None`. mypy infers `Any | bool`
or `Any | Literal[True]` for browse results, then complains when `.report_type` etc. are accessed.

**When:** 3 occurrences in `_connection.py` (lines 833, 850, 854).

```python
# BEFORE — generates union-attr
report_object = IR_ACTIONS_REPORT.browse(report_id) if report_id else False
if report_object.report_type != "fast_report":  # Item "bool" has no attr "report_type"

# AFTER — explicit guard eliminates the union-attr error
report_object = IR_ACTIONS_REPORT.browse(report_id) if report_id else False
if report_object is False or report_object.report_type != "fast_report":
    continue
```

The `report_object` type after the browse is `Any | bool` — mypy cannot narrow through the
`if report_id` guard alone. An explicit `is False` guard is sufficient. No TypedDict needed here
since the RPC return type is `Any` (Tier 2).

### Pattern 5: `has-type` Fix for Singleton `__new__` Pattern

**What:** `_logging.LoggerManager` sets `cls._instance._initialized = False` in `__new__`
but the instance-level attribute `_initialized` has no class-level annotation. mypy emits
`has-type [has-type]` because it cannot determine the type of `_initialized` at the usage site.

**When:** `_logging.py:91`, `_logging.py:96`.

```python
# BEFORE — generates has-type
class LoggerManager:
    _instance: Optional["LoggerManager"] = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False  # has-type error
        return cls._instance

# AFTER — class-level annotation resolves has-type
class LoggerManager:
    _instance: Optional["LoggerManager"] = None
    _initialized: bool  # class-level annotation, no default (set in __new__ / __init__)

    def __new__(cls) -> "LoggerManager":
        ...
```

The CONTEXT.md notes this area as fragile — annotate only, do not refactor. The fix is purely
additive (class-level annotation) and does not change runtime behavior.

### Pattern 6: `assignment` Fix for `ColoredFormatter` / Formatter

**What:** `_logging.py:156` assigns `logging.Formatter(...)` to a variable annotated (implicitly)
as `ColoredFormatter`. The two types are incompatible because `Formatter` is not a subclass of
`ColoredFormatter`.

```python
# BEFORE — generates assignment
if colored_output and sys.stdout.isatty():
    formatter = ColoredFormatter(console_format, datefmt=date_format)
else:
    formatter = logging.Formatter(console_format, datefmt=date_format)  # assignment error

# AFTER — widen the annotation
formatter: logging.Formatter
if colored_output and sys.stdout.isatty():
    formatter = ColoredFormatter(console_format, datefmt=date_format)
else:
    formatter = logging.Formatter(console_format, datefmt=date_format)
```

### Pattern 7: `arg-type` Fix for `os.getenv()` Returns

**What:** `_utils.py:470,477` passes `os.getenv(...)` (returns `str | None`) to functions
expecting `str`. This is BUG-05 territory (prepare_connection) — already fixed in Phase 1.1,
but similar patterns remain elsewhere.

```python
# BEFORE — generates arg-type
port = int(os.getenv("ODOO_PORT"))  # str | None, not str

# AFTER — explicit guard (already done in BUG-05 fix)
port_str = os.getenv("ODOO_PORT")
if port_str is None:
    raise ValueError("ODOO_PORT not set")
port = int(port_str)
```

If the function is `create_connection_from_env`, the Phase 1.1 BUG-05 fix already handles this.
Check if remaining `arg-type` instances are in that function or elsewhere.

### Pattern 8: `no-any-return` Fix

**What:** Function has non-`Any` return annotation but returns `Any` (e.g., returns a dict value
without narrowing).

```python
# BEFORE — generates no-any-return (return type str, but dict value is Any)
def get_primary_lang(name_dict: dict, ...) -> str:
    return next(iter(name_dict))  # Any

# AFTER — cast at boundary (Tier 3)
from typing import cast

def get_primary_lang(name_dict: dict[str, str], ...) -> str:
    return cast(str, next(iter(name_dict)))
# OR: narrow input type so result is already str
def get_primary_lang(name_dict: dict[str, str], ...) -> str:
    return next(iter(name_dict))  # now correctly str
```

Prefer narrowing input types (fix `dict` → `dict[str, str]`) over `cast` at output.

### Pattern 9: `_progress.py` `no-any-return`

**What:** `progress_bar()` is annotated `-> Iterable[Any]` but returns `tqdm(...)` which mypy
infers as `tqdm[Any]`. `tqdm[Any]` satisfies `Iterable[Any]` but mypy warns on the return.

**Fix:** Annotate return as `tqdm[Any]` (requires `from tqdm import tqdm`), or `Iterator[Any]`.

```python
from collections.abc import Iterator
from typing import Any
from tqdm import tqdm as TqdmType  # avoid name collision

def progress_bar(...) -> TqdmType[Any]:
    return tqdm(...)
```

### Anti-Patterns to Avoid

- **`# type: ignore` as a shortcut:** Violates ROADMAP SC-1. Every error must be resolved by annotation, not ignored.
- **Annotating with `Any` everywhere:** Violates D-07. Use `dict[str, Any]` only at Tier 2 boundaries.
- **Adding `cast()` without a justifying comment:** Cast hides real type errors. Always add `# Any: RPC boundary — shape is Odoo-version-dependent`.
- **`overrides: ignore_errors = true` as permanent:** Each override is a temporary exemption. Leaving any `ignore_errors` block after the final plan violates TYPE-03.
- **Using `Optional[X]` style:** Prefer `X | None` under `from __future__ import annotations` (Python 3.12+).

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Odoo RPC response type narrowing | Custom validation class | `TypedDict` + `cast` at boundary | Zero runtime overhead; mypy understands it natively |
| Per-module error baseline tracking | Custom error-counting script | `[[tool.mypy.overrides]] ignore_errors = true` | Declarative; removed mechanically per plan |
| Stub files for odoorpc-toolbox | `.pyi` stub tree | `follow_untyped_imports = true` | Source annotations already exist in 0.7.3; stubs would drift |

**Key insight:** The entire type-safety surface is achievable with stdlib typing alone. No
annotation-generation tools, no runtime validators, no stubs needed.

---

## Fragile Areas — Specific Mypy Errors

The CONTEXT.md flagged three fragile areas. Here is what the errors actually are:

### 1. `_logging.LoggerManager._loggers` (singleton pattern)

**Errors:** `has-type` at lines 91, 96; `no-any-return` at lines 133, 194; `no-untyped-def` ×8.

**What mypy sees:** `_initialized` is set in `__new__` (`cls._instance._initialized = False`) but
has no class-level type annotation. Mypy cannot resolve its type at `if self._initialized:` (line 94)
or `self._initialized = True` (line 96). Also, `_loggers: dict` (bare, no type params).

**Required fix (annotate only, do not refactor):**
```python
class LoggerManager:
    _instance: Optional["LoggerManager"] = None
    _initialized: bool         # add this line
    _loggers: dict[str, logging.Logger]  # add this line (replaces bare dict)
```
`_loggers` gets populated in `__init__` — the class-level annotation without a default is legal
in Python and mypy-friendly. The `no-any-return` on the `get_logger()` / `configure()` methods
is from the method bodies returning `self._loggers.get(name)` (type `Logger | None`, not `Logger`).
Fix by guarding: `return self._loggers[name]` after an `ensure` step, or returning `Logger | None`.

### 2. `_search_report_v13` Odoo-version branching

**Errors:** This method itself only has `no-untyped-def` (missing param/return annotations). The
v13 branching is in the control flow, not a mypy error source. Parameters `model_name`, `report_name`,
`IR_ACTIONS_REPORT`, `company_id` need annotations.

**Required fix:**
```python
def _search_report_v13(
    self,
    model_name: str,
    report_name: dict[str, str],
    IR_ACTIONS_REPORT: Any | None = None,  # Any: odoorpc proxy object, no typed class
    company_id: int | None = None,
) -> int | Literal[False]:
```

The `Literal[False]` return models the Odoo convention of returning `False` for "not found".
This is the correct Tier 3 pattern — document once in the method's docstring.

### 3. `_connection.py:560-561` recursive `data_dictionary`

**Errors:** `var-annotated` at lines 560 and 561.

**What the structure is:** `data_dictionary` accumulates nested report data:
```python
data_dictionary = {}  # outer key = report model name (str)
                      # value = dict[str, Any] with field names → metadata
```
After `add_field_to_dictionary()` calls, values contain nested dicts for field metadata.

**Required fix:** `dict[str, Any]` (Tier 2) is correct here. The recursive nature means a
full TypedDict tree would be over-specified and version-sensitive.

```python
report_name_id_combination: dict[str, int] = {}   # report_name → ir.actions.report id
data_dictionary: dict[str, Any] = {}              # Any: nested Odoo report field data
```

No TypedDict is needed. This is the canonical Tier 2 case (D-06).

---

## `_odoo_types.py` — TypedDict Shapes (D-06 Tier 1)

Shapes used in ≥2 call sites in `_connection.py` qualify for Tier 1 TypedDict. Based on inspection:

| TypedDict Name | Used Where | Key Fields |
|----------------|-----------|------------|
| `IrModelRecord` | `add_field_to_dictionary`, `_map_report_fields` | `id: int`, `model: str`, `name: str` |
| `IrModelFieldsRecord` | `add_field_to_dictionary`, `_collect_calculated_fields` | `id: int`, `name: str`, `ttype: str`, `modules: str \| Literal[False]` |
| `ReportAction` | `_create_or_update_report`, `map_reports`, `test_reports` | `id: int`, `report_type: str`, `model: str`, `name: str`, `ids: list[int]` |
| `LanguageRecord` | `get_installed_languages` | `code: str`, `name: str` |

These are `total=False` for optional keys not always present in all Odoo versions.

The `False`-sentinel pattern (`modules: str | Literal[False]`) models the Odoo convention precisely
without requiring runtime validation. [ASSUMED — shape derived from reading `_connection.py` + Odoo
RPC convention; exact field availability varies by Odoo version]

---

## Common Pitfalls

### Pitfall 1: `no-untyped-call` Cascade

**What goes wrong:** Annotating a module's functions in isolation does not eliminate all its errors.
A function in `_utils.py` that calls an unannotated function in the same module generates a
`no-untyped-call` at the call site.

**Why it happens:** mypy checks function-by-function; if the callee is unannotated at check time,
the call site gets a `no-untyped-call` even if the callee is in the same file being edited.

**How to avoid:** Always annotate all functions in a module in a single commit before verifying
mypy errors drop. Never commit a "half-annotated" module with the override removed — the
`no-untyped-call` count will mislead.

**Warning signs:** After annotating a module, `no-untyped-call` count in a different module
drops without changes to that module — this is the correct cascade resolution.

### Pitfall 2: Override Blocks vs. Error Count

**What goes wrong:** After enabling `strict = true` globally with `[[overrides]] ignore_errors = true`
for each module, `uv run mypy odoo_fast_report_mapper/` shows 0 errors — but each plan must
verify by running WITHOUT the override for the target module, not with the suppression still in place.

**How to avoid:** Each plan's verification step is:
1. Remove the target module's `[[overrides]]` block
2. Run `uv run mypy odoo_fast_report_mapper/`
3. Confirm the count decreased by the expected amount

### Pitfall 3: `os.getenv()` Returns `str | None` Everywhere

**What goes wrong:** 2 `arg-type` errors in `_utils.py` (lines 470, 477) are from passing
`os.getenv(...)` directly to `int()` and `normalize_language_code()` without guarding for `None`.

**How to avoid:** Pattern: always call `os.getenv("KEY", "default")` with a default, or add
an explicit `None`-check before use. The Phase 1.1 BUG-05 fix in `prepare_connection` already
demonstrates the correct pattern — replicate it for remaining sites.

### Pitfall 4: `_logging.py:156` Formatter Assignment Requires Upfront Widening

**What goes wrong:** The conditional `formatter = ColoredFormatter(...)` / `formatter = logging.Formatter(...)` pattern forces the variable type to the first assignment's type. If mypy encounters
`ColoredFormatter` first, the second assignment (`logging.Formatter`) is incompatible.

**How to avoid:** Declare `formatter: logging.Formatter` before the conditional. `ColoredFormatter`
is a subclass of `logging.Formatter`, so the assignment in the `if` branch is valid after widening.

### Pitfall 5: `tqdm` Return Type Annotation

**What goes wrong:** `_progress.py` annotates `progress_bar()` as `-> Iterable[Any]` but returns
`tqdm(...)`. `tqdm` class is generic (`tqdm[_T]`); returning it as `Iterable[Any]` triggers
`no-any-return` because mypy infers `tqdm[Any]` not `Iterable[Any]`.

**How to avoid:** Return `tqdm[Any]` directly. The `tqdm` stub types are available (tqdm ships
its own `py.typed` + stubs). Import `from tqdm import tqdm` (class) for the return annotation.

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| `ignore_missing_imports = true` (blanket) | `follow_untyped_imports = true` per third-party module | mypy 1.18 (2025) | Gets type info from annotated-but-not-py.typed packages |
| `Optional[X]` | `X \| None` | Python 3.10+ PEP 604; universal with `__future__` on 3.12 | Cleaner; `Optional` not needed |
| `typing.Dict`, `typing.List` | `dict[...]`, `list[...]` | Python 3.9+ PEP 585 | stdlib generics; `from typing import Dict` no longer needed |
| `typing.Iterable` | `collections.abc.Iterable` | Python 3.9+; mypy 1.x | `collections.abc` is canonical; `typing.Iterable` deprecated |

**Deprecated/outdated in this codebase:**
- `from typing import Optional` — keep for `_logging.py` line 16 (`Optional["LoggerManager"]`), or replace with `"LoggerManager" | None` under `__future__`.
- `ignore_missing_imports = true` — superseded by `follow_untyped_imports` for the odoorpc boundary.

---

## Recommended Plan Sequencing

Based on error counts and dependency order:

| Plan | Modules Covered | Error Count | Work Type |
|------|----------------|-------------|-----------|
| 02-01 | Setup commit: pyproject.toml, `_odoo_types.py`, `__future__` across package, `_yaml_dumper`, `_progress` | 2 (both easy) | Config + trivial annotations |
| 02-02 | `_lang_utils.py` | 7 | `type-arg` + 1 `no-untyped-def` + `no-any-return` |
| 02-03 | `_logging.py` | 19 | `no-untyped-def` + singleton `has-type` + `assignment` fix |
| 02-04 | `_report.py` | 10 | `no-untyped-def` + `var-annotated` + `type-arg` |
| 02-05 | `_utils.py` | 26 | `no-untyped-def` cascade + `arg-type` |
| 02-06 | `_connection.py` Part 1: lines 37–496 | ~40 | `no-untyped-def` for init/login/check methods |
| 02-07 | `_connection.py` Part 2: lines 496–873 | ~24 | `var-annotated` + `union-attr` + remaining `no-untyped-def` |
| 02-08 | `_cli.py` + final cleanup (remove all overrides) | 10 (mostly cascade-resolved) | 3 `no-untyped-def` + verify 0 total |

**Note on splitting `_connection.py`:** 64 errors in 873 LOC is manageable in two plans without
splitting the file itself. The CONTEXT.md allows the planner to split if it becomes unwieldy.
The split at line 496 (`_search_report` is the boundary between connection-setup and
mapping/collection logic) is a natural seam.

---

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| `mypy` | Type checking | Yes | 1.19.1 | — |
| `types-PyYAML` | PyYAML annotation | Yes | in dev extras | — |
| `uv` | Package management | Yes | in PATH | — |
| `tqdm` stubs | `_progress.py` annotation | Yes (tqdm ships py.typed) | bundled with tqdm | — |

**Missing dependencies with no fallback:** None.

[VERIFIED: live environment check]

---

## odoorpc-toolbox Boundary — Detailed Finding

**Installed version:** 0.7.3 [VERIFIED: `_version.py` in site-packages]
**py.typed marker:** ABSENT [VERIFIED: `ls .venv/lib/python*/site-packages/odoorpc_toolbox/py.typed` → not found]
**Source annotations:** Present (fields.py, base_helper.py, environment.py have typed defs per CONTEXT.md)
**Imports from odoorpc_toolbox in package:**
- `_connection.py:19`: `from odoorpc_toolbox import RPCError`
- `_utils.py:19`: `from odoorpc_toolbox import ODOO`

**Key empirical finding:** With `ignore_missing_imports = true` (current config), zero errors
originate from odoorpc_toolbox. The D-03 `follow_untyped_imports` override is the right
long-term policy (removes the blanket ignore), but it does not change the error count in this
baseline. Both `RPCError` and `ODOO` are used only for exception handling and type annotation
respectively — neither generates `no-untyped-call` errors because mypy already knows them as
`Any` (from `ignore_missing_imports`).

**Recommended config change (Plan 02-01):**
```toml
[tool.mypy]
python_version = "3.12"
strict = true
# Remove: ignore_missing_imports = true  ← replaced by targeted override

[[tool.mypy.overrides]]
module = "odoorpc_toolbox.*"
follow_untyped_imports = true  # reads source annotations; better than ignore_missing_imports
```

Running with `follow_untyped_imports = true` and without `ignore_missing_imports` was verified
to produce the same error count (130) as the current config. [VERIFIED: live test]

---

## BUG-04/BUG-05 Routing — Mypy-Discoverable Errors

The CONTEXT.md noted BUG-04 and BUG-05 might be mypy-discoverable. Both are now **fixed in Phase 1.1**.

**BUG-04** (`build_name_search_domain({})` → ValueError): The fix in Phase 1.1 added a guard.
This generates no mypy errors in the current baseline.

**BUG-05** (`prepare_connection` URL parsing): The fix in Phase 1.1 replaced `str.replace` with
`urlparse.hostname`. No mypy errors remain from this fix.

**Conclusion:** None of the 130 current errors are BUG-04/BUG-05 related. All are pure
annotation gaps. No routing to Phase 1.1 needed — it is already complete.

---

## `pyproject.toml` Changes Required

```toml
# CURRENT
[tool.mypy]
python_version = "3.12"
warn_return_any = true
warn_unused_configs = true
ignore_missing_imports = true

# AFTER Plan 02-01 (setup commit)
[tool.mypy]
python_version = "3.12"
strict = true
# warn_return_any and warn_unused_configs are included in strict = true

[[tool.mypy.overrides]]
module = "odoorpc_toolbox.*"
follow_untyped_imports = true

# One block per pending module (all added in Plan 02-01, removed progressively)
[[tool.mypy.overrides]]
module = "odoo_fast_report_mapper._yaml_dumper"
ignore_errors = true

[[tool.mypy.overrides]]
module = "odoo_fast_report_mapper._progress"
ignore_errors = true

[[tool.mypy.overrides]]
module = "odoo_fast_report_mapper._lang_utils"
ignore_errors = true

[[tool.mypy.overrides]]
module = "odoo_fast_report_mapper._logging"
ignore_errors = true

[[tool.mypy.overrides]]
module = "odoo_fast_report_mapper._report"
ignore_errors = true

[[tool.mypy.overrides]]
module = "odoo_fast_report_mapper._utils"
ignore_errors = true

[[tool.mypy.overrides]]
module = "odoo_fast_report_mapper._connection"
ignore_errors = true

[[tool.mypy.overrides]]
module = "odoo_fast_report_mapper._cli"
ignore_errors = true

# Also update mypy pin:
[project.optional-dependencies]
dev = [
    ...
    "mypy>=1.18",   # was "mypy>=1.0" — follow_untyped_imports requires 1.18
    ...
]
```

Also remove `odoo_report_helper/` from the CI mypy invocation in `.github/workflows/test.yml`:
```yaml
# Current (stale — odoo_report_helper/ no longer exists)
run: uv run mypy odoo_fast_report_mapper/ odoo_report_helper/

# After Plan 02-01
run: uv run mypy odoo_fast_report_mapper/
```

---

## Validation Architecture

> `nyquist_validation` is explicitly `false` in `.planning/config.json`. This section is SKIPPED.

---

## Security Domain

Phase 2 is annotation-only. No new attack surface, no new data flows, no new dependencies.
ASVS controls not applicable to a type-annotation phase. Security domain: SKIPPED.

---

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | TypedDict shapes for `IrModelRecord`, `IrModelFieldsRecord`, `ReportAction`, `LanguageRecord` are Tier 1 (used ≥2 call sites) | `_odoo_types.py` section | If shape is used only once, inline TypedDict or Tier 2 is better — no functional risk, only style |
| A2 | `_connection.py` can be cleanly split at line 496 (init/login/check vs. mapping/collection) across two plans | Plan sequencing | If the split is not clean, both plans could be merged into one larger plan — no correctness risk |
| A3 | `tqdm` ships its own `py.typed` + stubs (tqdm ≥4.66) | `_progress.py` annotation | If stubs missing, `tqdm[Any]` return annotation still works but mypy may be less precise |
| A4 | `ReportAction.ids` is `list[int]` (Odoo RPC proxy `.ids` property) | TypedDict design | If `.ids` returns other types in some Odoo versions, the TypedDict would need `Any` — Tier 2 fallback available |

---

## Open Questions

1. **`_connection.py` split threshold**
   - What we know: 64 errors, 873 LOC, natural seam at line 496 (setup vs. mapping)
   - What's unclear: Whether the annotations for the `map_reports`/`collect_all_reports` methods
     in Part 2 will require TypedDict imports that entangle heavily with Part 1
   - Recommendation: Keep as two plans (02-06, 02-07). If entanglement is found at execution time,
     merge into one plan — both are valid.

2. **CI workflow `mypy` command**
   - What we know: `.github/workflows/test.yml` still invokes `mypy odoo_fast_report_mapper/ odoo_report_helper/` with `continue-on-error: true`
   - What's unclear: Is CI-02 (removing `continue-on-error: true`) in Phase 4 or Phase 2?
   - Recommendation: Plan 02-01 removes `odoo_report_helper/` from the command (dead path) and
     removes `continue-on-error: true` only after all modules are clean (Plan 02-08). This
     satisfies TYPE-03 without waiting for Phase 4.

---

## Sources

### Primary (HIGH confidence)
- Live codebase measurement: `uv run mypy --strict odoo_fast_report_mapper/` — all error counts
- `.planning/phases/02-type-safety/02-CONTEXT.md` — locked decisions D-01..D-07
- `pyproject.toml` — current mypy config, dependencies, Python floor
- `odoo_fast_report_mapper/*.py` — source code read directly

### Secondary (MEDIUM confidence)
- [mypy configuration docs](https://mypy.readthedocs.io/en/stable/config_file.html) — `follow_untyped_imports`, `[[tool.mypy.overrides]]` TOML syntax [CITED]
- [mypy 1.18 changelog](https://mypy-lang.org/news.html) — `follow_untyped_imports` added in 1.18 [CITED]

### Tertiary (LOW confidence — ASSUMED)
- TypedDict shape field lists for Odoo RPC responses — derived from reading `_connection.py`; exact Odoo version-specific shapes not verified against live Odoo instance [A1, A4]

---

## Metadata

**Confidence breakdown:**
- Error baseline: HIGH — measured directly from live codebase
- Standard stack: HIGH — all packages already installed; no new dependencies
- Architecture patterns: HIGH — verified against actual mypy output for each error code
- TypedDict shapes: MEDIUM — inferred from source code; live Odoo not available
- Plan sizing: MEDIUM — error counts are accurate; effort per error varies

**Research date:** 2026-05-29
**Valid until:** 2026-06-29 (stable domain; only invalid if odoorpc-toolbox 0.7.4+ or mypy 1.20+ change behaviour)

## Project Constraints (from CLAUDE.md)

| Directive | Source | Impact on Phase 2 |
|-----------|--------|------------------|
| UV not pip for all package management | CLAUDE.md §Essential Workflow | All commands use `uv run mypy`, `uv pip install` |
| Git prefixes `[ADD]` / `[CHG]` / `[FIX]` | CLAUDE.md §Git Commit Prefix Rules | Annotation commits use `[CHG]`; new `_odoo_types.py` uses `[ADD]` |
| `pyproject.toml` is single source of truth — no `requirements.txt` | CLAUDE.md §Dependency Management | mypy pin bump goes in `[project.optional-dependencies]` dev |
| UTF-8 encoding for all files | CLAUDE.md §UTF-8 | Annotations of docstrings must preserve German umlauts |
| Never run `uv publish` | CLAUDE.md / PROJECT.md | Not applicable to Phase 2 |
| Push to both `origin` (GitLab) and `upstream` (GitHub) | CLAUDE.md §Git Push Strategy | Each Phase 2 commit must push to both remotes |
| `continue-on-error: true` in CI mypy step | `.github/workflows/test.yml` | Must be removed when final plan clears all errors |
