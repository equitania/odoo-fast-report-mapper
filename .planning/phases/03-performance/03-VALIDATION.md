# Phase 3: Performance — Validation Architecture

Extracted from `03-RESEARCH.md § Validation Architecture`.

---

## Test Framework

| Property | Value |
|----------|-------|
| Framework | pytest >=9.0 |
| Config file | `pyproject.toml` `[tool.pytest.ini_options]` |
| Quick run command | `uv run pytest tests/test_benchmark_rpc.py -q` |
| Full suite command | `uv run pytest tests/ -q -m "not integration"` |

---

## Phase Requirements → Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| PERF-01 | Benchmark counts RPC calls for 10×50 collect run | unit (count-based) | `uv run pytest tests/test_benchmark_rpc.py::test_collect_rpc_call_count -x` | Wave 1 creates it |
| PERF-02 | `add_field_to_dictionary` fires 0 IR_MODEL.search + 0 IR_FIELDS.search | unit assertion | `uv run pytest tests/test_benchmark_rpc.py::test_collect_rpc_call_count -x` | Wave 1 creates it |
| PERF-03 | Benchmark fails if count exceeds ceiling | unit (threshold assert) | `uv run pytest tests/test_benchmark_rpc.py -x` | Wave 1 creates it |
| PERF-04 | Ceiling value documented in test file constant | documentation | `grep RPC_CEILING tests/test_benchmark_rpc.py` | Wave 2 sets final value |

---

## Sampling Rate

- **Per task commit:** `uv run pytest tests/test_benchmark_rpc.py tests/test_connection.py -q`
- **Per wave merge:** `uv run pytest tests/ -q -m "not integration"`
- **Phase gate:** Full suite green + `uv run mypy odoo_fast_report_mapper/` exits 0

---

## Wave 0 Gaps (created by plans)

- [ ] `tests/test_benchmark_rpc.py` — covers PERF-01, PERF-02, PERF-03, PERF-04
- [ ] `RPC_CEILING` constant in `test_benchmark_rpc.py` — set to `0` after fix in Wave 2
