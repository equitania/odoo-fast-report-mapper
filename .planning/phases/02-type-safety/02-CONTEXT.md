# Phase 2: Type Safety - Context

**Gathered:** 2026-05-28
**Status:** Ready for planning

<domain>
## Phase Boundary

Phase 2 brings the consolidated `odoo_fast_report_mapper/` package to **mypy --strict with 0 errors**, without baseline suppressions and without `Any`-pollution. Concretely, after Phase 2:

- `mypy --strict odoo_fast_report_mapper/` exits 0 (baseline measured 2026-05-28 against the consolidated package: **131 errors in 8 files**; the "13" number in REQUIREMENTS.md was the v0.9.7 permissive-mode count and is obsolete)
- `pyproject.toml` `[tool.mypy]` has `strict = true` — the CI command runs `mypy --strict odoo_fast_report_mapper/` with no flag overrides
- Every public function and method has a complete type annotation (no implicit `Any`; explicit `Any` requires a justifying comment)
- All 335 tests still pass after annotation work
- `odoorpc-toolbox` upgrade from 0.7.2 → 0.7.3 is in place (already shipped 2026-05-28)

**Prerequisites (per ROADMAP):**
- Phase 1 (Package Consolidation) — Complete ✅
- **Phase 1.1 (Correctness Bug Fixes BUG-01..07) — must complete BEFORE Phase 2 starts.** Phase 1.1 touches the same files (`_connection.py`, `_utils.py`, `_report.py`) and would otherwise force re-annotation after bug-fix signature changes.

**In scope:** type annotations across all of `odoo_fast_report_mapper/`, mypy config change, TypedDict definitions for known Odoo response shapes, boundary handling for the untyped `odoorpc-toolbox` import.
**Out of scope:** behavior changes (Phase 1.1), RPC-call reduction (Phase 3), MIGRATION.md / DOCS work (Phase 4), runtime validation libraries (Pydantic), refactoring `_logging.LoggerManager._loggers` (deferred — outside Phase 1, still outside Phase 2 unless mypy-strict forces it).

</domain>

<decisions>
## Implementation Decisions

### Phase Sequencing (D-01)

- **D-01: Phase 1.1 runs first, then Phase 2.** ROADMAP shows Phase 1.1 inserted between Phase 1 and Phase 2; the ordering is locked. Phase 2 planning happens now (this CONTEXT.md captures the decisions) but Phase 2 execution waits until Phase 1.1 is verified complete.
  - **Why:** BUG-01..07 touch the same modules (`_connection.py`, `_utils.py`, `_report.py`). Doing bug fixes after annotation work would force re-annotation pass over the same signatures (e.g., BUG-03 `check_dependencies` returns `Tuple[bool, list]` vs `bool` — fixing that changes the annotation). Bug-fix-first avoids double work and gives mypy a correctness-stable foundation.
  - **How it applies:** plan-phase Phase 2 still proceeds and produces PLAN.md files; execute-phase Phase 2 is blocked until Phase 1.1 verifies green.

### Third-Party Boundary: odoorpc-toolbox (D-02 / D-03)

- **D-02: Upgrade odoorpc-toolbox 0.7.2 → 0.7.3 immediately, in a dedicated commit BEFORE Phase 1.1 starts.**
  - **Why:** 0.7.3 released 2026-05-28 with bug fixes and an expanded API surface (`Transport`, `MetricsTransport`, `TTLCache`, `batch_write`, `OdooConnection`/`EqOdooConnection` separated). Both Phase 1.1 and Phase 2 benefit from running on the current version. Equitania is the upstream author — known-low-risk vendor.
  - **How it applies:** bump `odoorpc-toolbox>=0.7.0` → `odoorpc-toolbox>=0.7.3` in `pyproject.toml`, `uv lock --upgrade-package odoorpc-toolbox`, `uv run pytest` must stay 335-green, single commit `[CHG] deps: upgrade odoorpc-toolbox 0.7.2 → 0.7.3`. **Not part of any Phase plan — Captain or planner of Phase 1.1 runs it as a prerequisite step.**

- **D-03: Strict-mode boundary for odoorpc-toolbox uses `follow_untyped_imports = true` (mypy ≥1.18) — no per-call `# type: ignore`, no local stubs, no Facade-wrapper.**
  - **Why:** 0.7.3 source IS annotated (44 typed defs in `fields.py`, 17 in `base_helper.py`, 16 in `environment.py`) — only the `py.typed` marker is missing. `follow_untyped_imports` (mypy 1.18+) tells mypy to read those source annotations anyway. Cheapest path; gives strict-typed boundary with no architecture impact. Avoids `# type: ignore` proliferation (which violates ROADMAP SC-1 "no baseline suppressions") and avoids a Facade-wrapper that would also block Phase 3 perf work.
  - **How it applies:** in `pyproject.toml`:
    ```toml
    [[tool.mypy.overrides]]
    module = "odoorpc_toolbox.*"
    follow_untyped_imports = true
    ```
    plus mypy version pin: `mypy>=1.18` in `[dependency-groups]`.
  - **Deferred:** a `py.typed`-marker PR to upstream `odoorpc-toolbox` is a separate Equitania-internal task — noted under Deferred Ideas, not blocking this phase.

### Strict-Mode Ramp Strategy (D-04 / D-05)

- **D-04: Module-by-module ramp with `[[tool.mypy.overrides]]` exemptions per pending module. `strict = true` is enabled globally on day one.**
  - **Why:** Big-bang in one mega-commit is unreviewable (131 errors at once). Module-by-module produces 1–2 module-sized atomic commits, each independently testable and revertable. Each plan removes the corresponding `[[overrides]]` block when its module is clean. The final plan removes any remaining overrides and asserts `strict = true` is unflagged.
  - **How it applies:**
    - Initial `pyproject.toml` patch: `strict = true` globally + one `[[overrides]] disable_error_code = [...]` block per pending module (`_lang_utils`, `_logging`, `_progress`, `_yaml_dumper`, `_exceptions`, `_utils`, `_connection`, `_report`, `_cli`)
    - Each plan tackles 1–2 modules, removes its `[[overrides]]` block at the end of the plan
    - Last plan: zero remaining `[[overrides]]`, mypy --strict exits 0
    - Order recommendation (smallest/leafiest first): `_exceptions` (14 LOC) → `_yaml_dumper` (13) → `_progress` (49) → `_lang_utils` (120) → `_logging` (291) → `_report` (147) → `_utils` (517) → `_connection` (873) → `_cli` (341).

- **D-05: `from __future__ import annotations` is added project-wide at the top of every `_*.py` module as part of the first ramp step.**
  - **Why:** TYPE-02 leaves this as an option ("falls für lesbarere Annotations nötig"). Project-wide adoption makes annotations evaluable as strings (PEP 563), avoids forward-reference quoting hell (`"OdooConnection"` strings disappear), and matches Python 3.12+ best practice. Cheap one-time mechanical change; consistent surface for downstream readers.
  - **How it applies:** included in the first ramp commit alongside the mypy config change — single commit `[CHG] type-safety: enable mypy strict, add from __future__ import annotations across package`.

### Odoo Data Shape Modeling (D-06)

- **D-06: TypedDict for known Odoo shapes (3-tier pragma).**
  - **Tier 1 (TypedDict):** Known/recurring Odoo response shapes get explicit `TypedDict` definitions: `IrModelRecord`, `IrModelFieldsRecord`, `ReportAction`, `CompanyRecord`, plus any other shape touched in ≥2 call sites. Lives in `_odoo_types.py` (new file).
  - **Tier 2 (`dict[str, Any]`):** Generic YAML loads, opaque/dynamic Odoo responses where shape varies by Odoo version, and one-off helper dicts use `dict[str, Any]`. Counts as explicit `Any` and is allowed without per-occurrence justification (covered by the `_odoo_types.py` module docstring).
  - **Tier 3 (boundary `cast` / `isinstance`):** At the read-from-RPC boundary, `cast(IrModelRecord, raw_dict)` or `assert isinstance(raw_dict, dict)` narrows the type. Markers go at clearly named locations (RPC-fetching methods), never sprinkled.
  - **Why:** Full TypedDict coverage is overkill for opaque RPC responses; `Any`-everywhere defeats TYPE-02 intent. TypedDict for the half-dozen recurring shapes documents the real API surface, while `dict[str, Any]` keeps the dynamic edges honest. No new runtime dependency (no Pydantic), no Protocol-types subtlety.
  - **How it applies:** new `_odoo_types.py` with TypedDict definitions, exported privately. The `False`-sentinel pattern (Odoo returns `False` for missing records) becomes `IrModelRecord | Literal[False]` at read sites where applicable.

### `Any` Policy (D-07)

- **D-07: Implicit `Any` is forbidden (`strict = true` enforces this). Explicit `Any` must have a comment justifying it (`# Any: <reason>`). `dict[str, Any]` and `list[Any]` per D-06 Tier 2 are pre-justified as the YAML/RPC-boundary convention and need no per-site comment.**
  - **Why:** matches ROADMAP SC-2 ("no `Any` without explicit `# type: ignore` justification") with an explicit policy. The pre-justified blanket for `dict[str, Any]`/`list[Any]` keeps the noise down where it would otherwise dominate every RPC call site.
  - **How it applies:** plan-checker / code review enforces it. CI does not enforce comment-presence (no automated checker for that — manual gate).

### Claude's Discretion

- **Internal helper splitting** — if `_utils.py` (517 LOC) or `_connection.py` (873 LOC) becomes unwieldy with annotations + TypedDict imports, the planner may split into `_utils_env.py`/`_utils_yaml.py` or `_connection_read.py`/`_connection_write.py`. Not required; planner decides per actual file size.
- **TypedDict location** — `_odoo_types.py` is the recommended location, but the planner may inline TypedDicts into the consuming module if a shape is used in exactly one place.
- **Mypy plugin (`pydantic.mypy`, etc.)** — not in scope; we do not use Pydantic per D-06. If a plugin is required for some edge case, planner flags it as a deviation.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Project & Milestone Context

- `.planning/PROJECT.md` — Project overview, hard-break policy for v1.0, `uv publish` manual-only constraint.
- `.planning/REQUIREMENTS.md` §"Type-Safety" — TYPE-01, TYPE-02, TYPE-03 verification criteria. **Note:** the "13 baseline errors" referenced in TYPE-01 is the v0.9.7 permissive-mode count; the consolidated package against `mypy --strict` measures 131 errors as of 2026-05-28.
- `.planning/ROADMAP.md` §"Phase 2: Type Safety" — Goal, depends-on (Phase 1; sequencing extends to Phase 1.1 per D-01), Success Criteria.
- `.planning/STATE.md` — Current milestone state, Phase 1 complete (2026-05-28).

### Phase 1 Outputs (for continuity)

- `.planning/phases/01-package-consolidation/01-CONTEXT.md` — Phase 1 decisions D-01 through D-13 that locked the package layout Phase 2 annotates.
- `.planning/phases/01-package-consolidation/VERIFICATION.md` — Phase 1 verified passed, 5/5 criteria.
- `.planning/phases/01-package-consolidation/01-05-SUMMARY.md` — Final consolidation summary; lists the 11 private submodules Phase 2 will annotate.

### Phase 1.1 Prerequisite Context

- `.planning/BASELINE-REVIEW.md` — BUG-01..07 specifications. Phase 2 planning must understand which bugs change which signatures, since Phase 1.1 lands before Phase 2 executes.

### Codebase Maps

- `.planning/codebase/STRUCTURE.md` — Current consolidated layout (Phase 1 result).
- `.planning/codebase/CONCERNS.md` §"Two-Package Architecture Layering" (now resolved) — Historical context for why the consolidation happened.
- `.planning/codebase/CONVENTIONS.md` — Naming, commit prefixes, formatting.

### Build / Type-Check Configuration

- `pyproject.toml` (repo root) — `[tool.mypy]` currently `python_version = "3.12"`, `warn_return_any = true`, `warn_unused_configs = true`, `ignore_missing_imports = true`. Phase 2 replaces this with `strict = true` + `[[tool.mypy.overrides]]` for `odoorpc_toolbox.*`. `[project.scripts]` entry points (`odoo-fast-report-mapper`, `odoo-fr-mapper`) must keep resolving — annotations must not break entry-point dispatch.
- `[dependency-groups]` `mypy>=1.0` — needs to pin `mypy>=1.18` for `follow_untyped_imports` support.

### Third-Party Boundary

- `odoorpc-toolbox` 0.7.3 — installed in venv at `.venv/lib/python3.13/site-packages/odoorpc_toolbox/`. No `py.typed`. Source-level annotations exist (44 typed defs in `fields.py`, 17 in `base_helper.py`, 16 in `environment.py`). `follow_untyped_imports = true` (mypy 1.18+) is the consumption strategy per D-03.
- `types-PyYAML>=6.0.0` — already in dependencies; PyYAML annotations available out of the box.

### Captain Constraints

- `~/gitbase/CLAUDE.md` §"Git Commit Prefix Rules" — `[ADD]` / `[CHG]` / `[FIX]` prefixes; release commits push to both `origin` (GitLab) and `upstream` (GitHub).
- `~/gitbase/CLAUDE.md` §"UTF-8 ENCODING" — preserve German umlauts and Unicode in annotated docstrings.

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets

- **`from __future__ import annotations`** (PEP 563) — already supported by Python 3.12+; safe to add globally per D-05. Eliminates forward-ref quoting.
- **`types-PyYAML`** — already in dependencies; PyYAML `yaml.safe_load(...)`, `yaml.YAMLError`, etc. all have annotations.
- **Existing partial annotations** — `_connection.py:496` shows mixed-state code where some defs have return annotations and others don't (the 33 `no-untyped-call` cascade stems from this). Planner should grep for existing annotation style and stay consistent.
- **`__version__.py`** — single source of version; type as `__version__: str = "X.Y.Z"`.

### Established Patterns

- **Underscore-private submodules** (Phase 1 D-03) — annotations are added to the submodules; `__init__.py` re-export list (D-04) does not need annotation changes, only the underlying defs.
- **No `super()` chain** (Phase 1 D-08) — merged `OdooConnection` is single-class; mypy method resolution is straightforward, no MRO surprises.
- **`progress_bar()` context manager** (`_progress.py`) — already context-manager-shaped, annotation is `@contextmanager def progress_bar(...) -> Iterator[tqdm]:`.
- **Logger singleton `_logging.LoggerManager`** — class-level mutable dict `_loggers: dict[str, Logger] = {}`. Annotation is mechanical; the documented fragility (deferred from Phase 1) does not block strict-mode.

### Integration Points

- **CI workflow** — Phase 2 changes mypy invocation. `pyproject.toml` becomes the single source; CI command shrinks to `uv run mypy odoo_fast_report_mapper/` (no flag override; `strict = true` is read from config). The actual CI YAML change is Phase 4 CI-02, not this phase — Phase 2 only ensures the config is correct.
- **Test suite (335 tests)** — must stay green; annotations should not change runtime behavior. If a test discovers that an annotation revealed a real bug (BUG-04, BUG-05 are mypy-discoverable), Phase 2 documents the discovery and routes it to Phase 1.1 instead of fixing it inline.

### Fragile Areas (don't touch in Phase 2)

- **`_logging.LoggerManager._loggers` class-level mutable dict** — annotate (`dict[str, Logger]`), do not refactor. Refactor is a v1.x concern.
- **`_search_report_v13` Odoo-version branching** — annotate, do not refactor. Odoo v13 support is a hard PROJECT.md constraint.
- **`_connection.py:561` `data_dictionary = {}`** — picks up a recursive structure. TypedDict modeling here is non-trivial; planner should consider `dict[str, Any]` (per D-06 Tier 2) unless a clean shape emerges.

</code_context>

<specifics>
## Specific Ideas

- **mypy version pin: `mypy>=1.18`** — required for `follow_untyped_imports`. First plan in Phase 2 (or the pre-phase setup commit if a planner picks it up) bumps this in `pyproject.toml` `[dependency-groups]`.
- **`_odoo_types.py` filename** — matches the underscore-prefix convention (D-03 from Phase 1). Keep it `_odoo_types.py`, not `types.py` (would shadow stdlib `types`).
- **TypedDict ordering** — `total=False` for partial shapes (when not all keys are guaranteed present); `total=True` (default) for shapes Odoo always returns complete. Document the choice inline next to each definition.
- **mypy invocation in dev** — should be `uv run mypy odoo_fast_report_mapper/` (no `--strict` flag, since `strict = true` is in config). Plan-checker should verify this is consistent across docs.

</specifics>

<deferred>
## Deferred Ideas

- **`py.typed` marker PR to upstream `odoorpc-toolbox`** — Equitania is the author; adding the marker (and ensuring 100% annotation coverage in 0.7.4) is a one-line change. Captain task or separate side-quest; not blocking Phase 2. Once shipped, Phase 4 can drop the `follow_untyped_imports = true` override.
- **`_logging.LoggerManager._loggers` refactor** — flagged in Phase 1 CONCERNS as fragile; Phase 2 only annotates, no refactor. Candidate for a future cleanup phase if it surfaces under concurrency review.
- **Pydantic introduction for runtime validation** — explicitly out of scope per D-06. If real demand surfaces (e.g., YAML config validation in v1.1), re-evaluate then.
- **Splitting `_connection.py` (873 LOC) / `_utils.py` (517 LOC)** — Claude's-Discretion item under D-decisions; only if annotations make these files unwieldy. Default: leave intact.
- **Mypy plugin ecosystem** — none planned; if a third-party lib (e.g., `odoorpc_toolbox` itself in some edge case) needs a plugin, it surfaces in execution and gets flagged as a deviation.
- **Runtime type-checking with `beartype` / `typeguard`** — not in scope; mypy-strict is the contract. Could be a v1.x add-on.

</deferred>

---

*Phase: 2-Type Safety*
*Context gathered: 2026-05-28*
