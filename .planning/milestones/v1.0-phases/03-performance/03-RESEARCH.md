# Phase 3: Performance — Research

**Researched:** 2026-06-11
**Domain:** RPC call-count optimization + pytest Mock-Counter benchmark
**Confidence:** HIGH

---

## Summary

Phase 3 has a sharply defined scope: eliminate the 2 extra RPC calls per field that
`add_field_to_dictionary()` fires (`IR_MODEL.search` + `IR_FIELDS.search`) and lock the
reduction in with a counting test that CI enforces.

The "2 extra calls" exist because `add_field_to_dictionary()` re-queries `ir.model` and
`ir.model.fields` to collect dependency module names, even though the **outer loop in
`collect_report_entries()`** already iterates over `ir.model.fields` records that were
fetched by the top-level `all_report_field_ids` search. The model name and field id are
already on the `field_object` that drives the loop; the two inner `.search()` calls are
pure redundancy.

The fix is a **pre-fetch + pass-through**: move dependency resolution out of
`add_field_to_dictionary()` into `collect_report_entries()`, where
`field_object.modules` is already accessible from the browsed record, and pass the
resolved modules into `add_field_to_dictionary()` as a parameter (or accumulate them
inline). `add_field_to_dictionary()` then becomes a pure dict-mutation function with
zero RPC calls — no search, no browse.

For the Mock-Counter test, the `odoorpc_toolbox` library ships a real
`RequestMetrics + MetricsTransport` pair in `odoorpc_toolbox.rpc.metrics` (verified at
version 0.8.2). However, since the project already uses `MagicMock` exclusively and
does not wire up the real transport, the simplest and most reliable approach is a
**call-count counter on the mock `search` side-effect** — a lightweight wrapper that
increments a counter each time `search` is invoked on any model proxy. This stays fully
within the existing test infrastructure and requires no new dependencies.

**Primary recommendation:** Resolve `field_object.modules` inline in the
`collect_report_entries()` loop (the data is already on the browsed object) and delete
the two `.search()` calls from `add_field_to_dictionary()`. Write one benchmark test
that drives a synthetic 10-report × 50-field collect loop via mocks and asserts
`search_call_count <= CEILING`, where the ceiling is measured in the baseline task of
this phase.

---

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| RPC call reduction | `_connection.py` — OdooConnection | — | All Odoo I/O is in this class; the collect flow is self-contained |
| Dependency resolution | `collect_report_entries()` loop | `add_field_to_dictionary()` parameter | The loop already holds the browsed field object; pass modules down |
| Mock-Counter benchmark | `tests/test_connection.py` | new `tests/test_benchmark_rpc.py` | Keeping benchmark in its own file keeps the main test file focused |
| mypy compliance | `_connection.py` + new parameter signature | `tests/test_benchmark_rpc.py` | Any signature change must stay mypy --strict clean |

---

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| PERF-01 | Benchmark for `collect_report_entries()` — counts RPC calls against 10 reports × 50 fields via Mock-Counter | Mock-Counter pattern designed; see Architecture Patterns below |
| PERF-02 | `add_field_to_dictionary()` makes 0 extra RPC calls per field (IR_MODEL.search + IR_FIELDS.search eliminated) | Root cause identified; fix strategy documented in Standard Stack |
| PERF-03 | Regression test in pytest suite — fails if RPC count exceeds threshold; CI-enforced | No new pytest plugin needed; pure call-counting via MagicMock.call_count |
| PERF-04 | Concrete ceiling value documented: baseline measured in Phase 3, ceiling ≤ baseline_after_fix | Wave 0 task: measure baseline before touching production code |
</phase_requirements>

---

## Standard Stack

### Core (no new packages required)

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| `pytest` | >=9.0 (already installed) | Test runner + assertion framework | Already in pyproject.toml dev deps [VERIFIED: pyproject.toml] |
| `pytest-mock` | >=3.6.0 (already installed) | `mocker` fixture, MagicMock helpers | Already in pyproject.toml dev deps [VERIFIED: pyproject.toml] |
| `unittest.mock.MagicMock` | stdlib | Mock-Counter implementation | Used throughout existing test suite [VERIFIED: tests/test_connection.py] |

**No new packages needed.** `pytest-benchmark` (the pypi plugin) is NOT used — the
benchmark here is a call-count assertion, not a timing benchmark. Adding
`pytest-benchmark` would introduce `--benchmark-skip` complexity and timing variance;
a count-based assertion is deterministic, fast, and sufficient for PERF-03. [ASSUMED
— based on requirements text reading "Mock-Counter on the RPC layer"; if Captain
wants wall-clock benchmarking too, add `pytest-benchmark` in Phase 4.]

### Supporting (already in toolbox — no install needed)

| Module | Location | Purpose |
|--------|----------|---------|
| `odoorpc_toolbox.rpc.metrics.RequestMetrics` | `.venv/.../odoorpc_toolbox/rpc/metrics.py` | Thread-safe request counter (wraps real transport) — available but NOT used in unit tests |
| `odoorpc_toolbox.cache.TTLCache` | `.venv/.../odoorpc_toolbox/cache.py` | TTL cache with maxsize — available for optional model-id caching in future |
| `odoorpc_toolbox.cache.cached_lookup` | `.venv/.../odoorpc_toolbox/cache.py` | `@cached_lookup()` decorator for instance-scoped caching | [VERIFIED: .venv source] |

**Why `RequestMetrics` is not used for unit tests:** It wraps a real `Transport` and
counts HTTP-level requests. The test suite mocks at the `self.connection.env[...]` level
(model proxy layer), so HTTP transport is never invoked. A Mock-Counter lives one level
up — on the model proxy's `.search()` method.

### Package Legitimacy Audit

No new packages are installed in this phase. The audit section is N/A.

---

## Architecture Patterns

### System Architecture Diagram

```
collect_report_entries()
  │
  ├─ IR_ACTIONS_REPORT.search(...)          [1 call — top-level report ID fetch]
  ├─ IR_MODEL_FIELDS.search(eq_report_ids)  [1 call — all field IDs for found reports]
  │
  └─ for field_id in all_report_field_ids:
       field_object = IR_MODEL_FIELDS.browse(field_id)   [1 call per field — NEEDED]
       model_name  = field_object.model_id.model          [attribute, 0 RPC]
       field_name  = field_object.name                    [attribute, 0 RPC]
       modules     = field_object.modules                 [attribute, 0 RPC] ← KEY INSIGHT
       │
       └─ add_field_to_dictionary(
              data_dictionary,
              report_action_id,
              model_name,
              field_name,
              company_id,
              modules  ← NEW PARAMETER         [0 extra RPC — was 2]
          )
              │
              └─ pure dict mutation, no connection access
```

**Current (before fix):** `add_field_to_dictionary` calls
`IR_MODEL.search([("model", "=", model_name)])` and
`IR_FIELDS.search([("model_id", "=", model_id[0]), ("name", "=", field_name)])` — 2
extra RPC calls per field, even though the field_object already holds `modules`.

**After fix:** modules resolved from `field_object.modules` in the outer loop; passed
as parameter. The two `.search()` calls and the `.browse()` inside
`add_field_to_dictionary()` are deleted. The `self.connection` reference inside
`add_field_to_dictionary()` is removed entirely.

### Recommended Project Structure

No new directories or files needed beyond one new test file:

```
tests/
├── test_connection.py       # existing — add nothing here (keep focused)
├── test_benchmark_rpc.py    # NEW — Mock-Counter benchmark (PERF-01, PERF-03)
└── conftest.py              # existing — no changes needed
odoo_fast_report_mapper/
└── _connection.py           # modified — add `modules` param to add_field_to_dictionary,
                             # remove IR_MODEL.search + IR_FIELDS.search from that method
```

### Pattern 1: Mock-Counter for Search Calls

**What:** A `MagicMock` whose `.search` side-effect increments a shared counter.
Injected into `conn.connection.env[...]` via the existing `_setup_env()` helper.

**When to use:** Any test that needs to assert "method X was called at most N times"
across a multi-iteration loop without running real network I/O.

```python
# Source: derived from existing _setup_env pattern in tests/test_connection.py
class SearchCallCounter:
    """Counts .search() calls across all mock model proxies."""
    def __init__(self):
        self.count = 0

    def counting_mock(self, name: str) -> MagicMock:
        counter = self
        m = MagicMock(name=name)
        original_search = m.search

        def tracked_search(domain):
            counter.count += 1
            return original_search(domain)

        m.search = MagicMock(side_effect=tracked_search)
        return m
```

**Alternative (simpler):** After the run, assert on `mock.search.call_count` directly
for each model mock. The `SearchCallCounter` pattern is useful when you need a combined
total across multiple model proxies.

### Pattern 2: Baseline Measurement First (Wave 0 task)

Before touching production code, measure current call count:

```python
# test_benchmark_rpc.py — Wave 0 baseline measurement
def test_rpc_call_baseline(tmp_path):
    """BASELINE: measure current search() call count for 10 reports x 50 fields.
    This test documents the BEFORE state. It MUST PASS at baseline (no assertion).
    After the fix, this test becomes the regression guard with an assertion.
    """
    conn = _make_connection()
    # ... build 10-report x 50-field mock setup
    ir_model_mock = MagicMock()
    ir_model_mock.search.return_value = [1]
    ir_fields_mock = MagicMock()
    ir_fields_mock.search.return_value = [10]
    # ... wire up and run collect_report_entries
    # Log the counts — no assertion yet
    print(f"BASELINE ir.model.search calls: {ir_model_mock.search.call_count}")
    print(f"BASELINE ir.model.fields.search calls (inner): {ir_fields_mock.search.call_count}")
```

**After fix:** Add `assert ir_model_mock.search.call_count == 0` inside
`add_field_to_dictionary` scope (the outer `.search` for report IDs is a different mock).

### Anti-Patterns to Avoid

- **Do not cache model IDs inside `add_field_to_dictionary()`** as a middle-ground fix.
  The real fix is removing the two searches entirely — caching still makes N RPC calls
  on the first encounter per model. The data is already on `field_object.modules`.

- **Do not introduce `@cached_lookup` from odoorpc_toolbox** as the primary fix.
  The `@cached_lookup` decorator is designed for connection-level lookups where the
  query is genuinely necessary; using it here would hide the redundancy rather than
  remove it.

- **Do not break the `add_field_to_dictionary()` public signature silently.** The
  existing 6 unit tests for this method mock `conn.connection.env[...]` and expect 0
  RPC calls in the empty-search paths. Adding `modules: list[str]` as an optional
  parameter (defaulting to an empty list) preserves backward compat for existing tests.

- **Do not touch `map_reports()` in this phase.** `_map_report_fields()` also calls
  `IR_MODEL.search` and `IR_MODEL_FIELDS.search`, but those are the **legitimate**
  field mapping calls during write mode. PERF-02 is scoped to `add_field_to_dictionary`
  in the collect flow only.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Call counting | Custom instrumentation wrapper around odoorpc proxy | `mock.search.call_count` attribute on MagicMock | MagicMock tracks call count automatically; zero extra code |
| TTL caching of model IDs | Dict-based manual cache with expiry | `odoorpc_toolbox.cache.TTLCache` (if caching needed in future) | Already in the installed toolbox; but not needed here — the fix is removal, not caching |
| Timing-based perf regression | Wall-clock assertions with sleep tolerance | Count-based assertions | Deterministic, no CI flakiness from CPU load variance |

---

## Common Pitfalls

### Pitfall 1: Signature Change Breaks Mypy Strict

**What goes wrong:** Adding `modules: list[str]` to `add_field_to_dictionary()` without
updating the 3 call-sites in `collect_report_entries()` — mypy reports missing argument.

**Why it happens:** `add_field_to_dictionary` is called in a loop inside
`collect_report_entries`; also called in 6 existing unit tests via direct call.

**How to avoid:** Add `modules: list[str] = field(default_factory=list)` — wait, this is
not a dataclass. Use `modules: list[str] | None = None` as the new optional parameter,
with `modules = modules or []` inside the body. Existing unit tests that do not pass
`modules` continue to work. The call-site in `collect_report_entries()` passes the
resolved value explicitly.

**Warning signs:** `mypy --strict odoo_fast_report_mapper/` reports errors after the
signature change — catch this before committing.

### Pitfall 2: Measuring the Wrong Search Calls

**What goes wrong:** The benchmark asserts on `IR_MODEL_FIELDS.search.call_count` but
this mock is also used for the **outer** `all_report_field_ids` search in
`collect_report_entries()` — that call is legitimate and must not be counted.

**Why it happens:** There is only one `ir.model.fields` proxy in the env map, so all
searches go through the same mock.

**How to avoid:** Either use `side_effect` to track call arguments and count only
zero-argument inner calls, OR split the mock into two separate `MagicMock` instances
for the outer search and the inner dependency search (by intercepting the second call).
Simplest approach: after the fix, assert `call_count == N_outer_searches` where
`N_outer_searches` is exactly 1 (one top-level fields search per company iteration).

### Pitfall 3: `field_object.modules` Can Be `False` (BUG-08 already fixed)

**What goes wrong:** A computed Odoo field with no module has `modules = False`, not
`""`. Calling `.replace()` on `False` crashes.

**Why it doesn't apply here:** BUG-08 was already fixed in Phase 1.1. The fix guards
`field_obj.modules` before `.replace()`. When moving the resolution into the outer
loop, the same guard must be preserved:

```python
raw = field_object.modules or ""
modules = [m for m in raw.replace(" ", "").split(",") if m]
```

This pattern is already in `add_field_to_dictionary()` post-BUG-08 fix and must be
kept verbatim when moved.

### Pitfall 4: `collect_report_entries` Loop Calls `add_field_to_dictionary` via Multiple Paths

**What goes wrong:** There is a conditional branch in the `for report_action_id in
report_action_ids` loop that calls `add_field_to_dictionary` only on some paths
(company_id branching at lines 639–667). If the benchmark test only exercises the
non-company path, it misses the company-id path entirely.

**How to avoid:** The benchmark test should cover both paths — at least one report with
`company_id` set and one without — to ensure the mock-counter reflects real-world usage.

---

## Code Examples

### Resolved modules extraction (to move into collect_report_entries loop)

```python
# Source: _connection.py lines 718-720, post-BUG-08/BUG-09 fix
raw_modules = field_obj.modules or ""
raw_modules_clean = raw_modules.replace(" ", "").split(",")
modules_dependencies = [m for m in raw_modules_clean if m]
```

After the fix, this runs on `field_object` (already browsed in the outer loop at
line 631), and `modules_dependencies` is passed to `add_field_to_dictionary()`.

### add_field_to_dictionary signature (after fix)

```python
def add_field_to_dictionary(
    self,
    data_dictionary: dict[Any, Any],
    report_id: Any,
    model_name: str,
    field_name: str,
    company_id: int | Literal[False],
    modules: list[str] | None = None,   # NEW — resolved by caller from field_object.modules
) -> dict[Any, Any]:
    # ... existing dict-mutation logic ...
    # Dependency accumulation (no RPC calls):
    modules_dependencies = modules or []
    if modules_dependencies:
        if "dependencies" in data_dictionary[report_id]:
            data_dictionary[report_id]["dependencies"].extend(modules_dependencies)
            data_dictionary[report_id]["dependencies"] = list(set(data_dictionary[report_id]["dependencies"]))
        else:
            data_dictionary[report_id]["dependencies"] = list(modules_dependencies)
    return data_dictionary
    # DELETED: IR_FIELDS = self.connection.env["ir.model.fields"]
    # DELETED: IR_MODEL = self.connection.env["ir.model"]
    # DELETED: model_id = IR_MODEL.search(...)
    # DELETED: field_id = IR_FIELDS.search(...)
    # DELETED: field_obj = IR_FIELDS.browse(field_id)
```

### Mock-Counter benchmark test skeleton

```python
# tests/test_benchmark_rpc.py
# Source: pattern derived from TestCollectReportEntries in tests/test_connection.py

import pytest
from unittest.mock import MagicMock, patch
from odoo_fast_report_mapper._connection import OdooConnection

# Ceiling documented here after baseline measurement in Wave 0
# Format: (reports * models_per_report) + N_outer_searches_per_company + fixed_overhead
# After fix: inner IR_MODEL.search + IR_FIELDS.search == 0
RPC_CEILING: int = 0  # PLACEHOLDER — set after Wave 0 baseline run

def _make_collect_mocks(n_reports: int, n_fields_per_report: int):
    """Build mock field objects for n_reports * n_fields_per_report collect scenario."""
    # Each field object has .eq_report_ids.ids, .model_id.model, .name, .modules
    ...

def test_collect_rpc_call_count(tmp_path):
    """PERF-01/PERF-03: search() call count must not exceed RPC_CEILING for 10x50 run."""
    ...
    assert ir_model_inner_search_calls == 0, (
        f"add_field_to_dictionary must not call IR_MODEL.search — "
        f"got {ir_model_inner_search_calls} calls"
    )
    assert ir_fields_inner_search_calls == 0, (
        f"add_field_to_dictionary must not call IR_FIELDS.search — "
        f"got {ir_fields_inner_search_calls} calls"
    )
```

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Per-field IR_MODEL.search + IR_FIELDS.search inside `add_field_to_dictionary` | Resolve from already-browsed `field_object.modules` in outer loop | Phase 3 (this phase) | 2 RPC calls per field → 0; 10 reports × 50 fields = 1000 fewer calls |

**Deprecated/outdated:**
- `IR_MODEL.search` + `IR_FIELDS.search` inside `add_field_to_dictionary`: replaced by
  caller-provided `modules` parameter derived from the already-browsed `field_object`.

---

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | `pytest-benchmark` is NOT needed; count-based assertion is sufficient for PERF-03 | Standard Stack | Low — if Captain wants wall-clock too, add pytest-benchmark in Phase 4; does not block Phase 3 |
| A2 | The `modules` parameter should be optional (`list[str] | None = None`) to preserve existing test compatibility | Code Examples | Low — existing 6 unit tests pass `modules` implicitly; making it required would break them but be cleaner |

---

## Open Questions (RESOLVED)

1. **Exact ceiling value for PERF-04**
   - What we know: after the fix, inner `IR_MODEL.search + IR_FIELDS.search = 0` per field.
     The remaining legitimate searches are: 1 `IR_ACTIONS_REPORT.search` + 1
     `IR_MODEL_FIELDS.search` per company iteration in `collect_report_entries`.
   - What's unclear: the exact integer ceiling depends on how many companies are in the
     10×50 test fixture and whether `create_eq_report_object` fires any `.search()` calls
     during the post-loop YAML serialization.
   - Recommendation: **Wave 0 task must measure and log the baseline count BEFORE the
     fix, then measure AFTER the fix and set `RPC_CEILING` to the after-fix count + 0
     tolerance.**
   - **RESOLVED: Wave 1 measures baseline; Wave 2 sets `RPC_CEILING = 0` (inner search count after fix).**

2. **Should `add_field_to_dictionary` lose its `self` reference entirely?**
   - What we know: after removing the two RPC calls, `add_field_to_dictionary` no longer
     accesses `self.connection` at all. It becomes a pure dict mutation.
   - What's unclear: whether making it a `@staticmethod` or a module-level function is
     preferred by Captain (CONS-03 already removed override smell; this would be a
     further cleanup).
   - Recommendation: leave as instance method in this phase (minimal diff, easier
     review). Document as a v2.0 candidate.
   - **RESOLVED: Leave as instance method in Phase 3; `@staticmethod` is a v2.0 candidate.**

---

## Environment Availability

No external tools required. All dependencies already installed.

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| pytest | Benchmark test | ✓ | >=9.0 | — |
| pytest-mock | Mock setup | ✓ | >=3.6.0 | — |
| mypy | Strict check after signature change | ✓ | >=1.18 | — |
| odoorpc_toolbox | Import in tests | ✓ | 0.8.2 | — |

---

## Validation Architecture

### Test Framework

| Property | Value |
|----------|-------|
| Framework | pytest >=9.0 |
| Config file | `pyproject.toml` `[tool.pytest.ini_options]` |
| Quick run command | `uv run pytest tests/test_benchmark_rpc.py -q` |
| Full suite command | `uv run pytest tests/ -q -m "not integration"` |

### Phase Requirements → Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| PERF-01 | Benchmark counts RPC calls for 10×50 collect run | unit (count-based) | `pytest tests/test_benchmark_rpc.py::test_collect_rpc_call_count -x` | ❌ Wave 0 |
| PERF-02 | `add_field_to_dictionary` fires 0 IR_MODEL.search + 0 IR_FIELDS.search | unit assertion | `pytest tests/test_benchmark_rpc.py::test_collect_rpc_call_count -x` | ❌ Wave 0 |
| PERF-03 | Benchmark fails if count exceeds ceiling | unit (threshold assert) | `pytest tests/test_benchmark_rpc.py -x` | ❌ Wave 0 |
| PERF-04 | Ceiling value documented in test file constant | documentation | grep `RPC_CEILING` in test file | ❌ Wave 0 |

### Sampling Rate

- **Per task commit:** `uv run pytest tests/test_benchmark_rpc.py tests/test_connection.py -q`
- **Per wave merge:** `uv run pytest tests/ -q -m "not integration"`
- **Phase gate:** Full suite green + `uv run mypy odoo_fast_report_mapper/` exits 0

### Wave 0 Gaps

- [ ] `tests/test_benchmark_rpc.py` — covers PERF-01, PERF-02, PERF-03, PERF-04
- [ ] `RPC_CEILING` constant in `test_benchmark_rpc.py` — set after baseline measurement

---

## Security Domain

No security-relevant changes in this phase. No new inputs, no authentication changes,
no data written. The fix is a pure internal refactor (remove dead RPC calls).

ASVS V5 Input Validation: not applicable (no new user-facing input added).

---

## Project Constraints (from CLAUDE.md)

- Use UV for all Python operations: `uv run pytest`, `uv run mypy`
- Commit prefix: `[CHG]` for the production code change, `[ADD]` for the new test file
- All code and docs in English
- UTF-8 encoding for all file operations (no change needed — existing convention)
- `pyproject.toml` is the single source of truth — no `requirements.txt`
- After fix: `uv run mypy odoo_fast_report_mapper/` must exit 0 (strict = true already enabled)
- Do NOT run `uv publish` — Captain runs this manually

---

## Sources

### Primary (HIGH confidence)

- `odoo_fast_report_mapper/_connection.py` (lines 688–731) — `add_field_to_dictionary`
  implementation, confirmed 2 extra search calls [VERIFIED: codebase read]
- `odoo_fast_report_mapper/_connection.py` (lines 583–686) — `collect_report_entries`
  outer loop, confirmed `field_object.modules` attribute already available [VERIFIED: codebase read]
- `.venv/lib/python3.13/site-packages/odoorpc_toolbox/rpc/metrics.py` — `RequestMetrics`,
  `MetricsTransport` — confirmed present at v0.8.2 [VERIFIED: .venv source read]
- `.venv/lib/python3.13/site-packages/odoorpc_toolbox/cache.py` — `TTLCache`,
  `cached_lookup` — confirmed present at v0.8.2 [VERIFIED: .venv source read]
- `tests/test_connection.py` (lines 1560–1647) — `TestAddFieldToDictionary` and its
  `_setup_field_env` helper — confirmed existing mock pattern [VERIFIED: codebase read]
- `tests/conftest.py` — confirmed `MagicMock` + `_setup_env` pattern convention [VERIFIED: codebase read]
- `pyproject.toml` — confirmed no `pytest-benchmark` installed, `pytest>=9.0`,
  `mypy strict = true` [VERIFIED: codebase read]

### Secondary (MEDIUM confidence)

- `odoorpc_toolbox` v0.8.2 version confirmed via
  `.venv/lib/python3.13/site-packages/odoorpc_toolbox/_version.py` [VERIFIED: .venv]

---

## Metadata

**Confidence breakdown:**
- Root cause (2 extra RPC calls in add_field_to_dictionary): HIGH — verified directly in source
- Fix strategy (pass modules from outer loop): HIGH — field_object.modules is directly available at loop site
- Mock-Counter test pattern: HIGH — derived from existing test infrastructure conventions
- Ceiling value (PERF-04): MEDIUM — depends on Wave 0 measurement; exact number not pre-determinable

**Research date:** 2026-06-11
**Valid until:** 2026-07-11 (stable internal codebase — no external API churn risk)
