# Phase 2: Type Safety - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in `02-CONTEXT.md` — this log preserves the alternatives considered.

**Date:** 2026-05-28
**Phase:** 2-type-safety
**Areas discussed:** Phase 1.1 sequencing, odoorpc-toolbox boundary, strict-mode ramp, Odoo data shape modeling, odoorpc-toolbox upgrade timing

---

## Phase 1.1 Sequencing

| Option | Description | Selected |
|--------|-------------|----------|
| 1.1 zuerst, dann Phase 2 | BUG-01..07 fixen, dann mypy-strict drauf. Vermeidet Doppelarbeit, Tests-vor-Annotation gibt sicheren Boden. | ✓ |
| Phase 2 zuerst, dann 1.1 | mypy-strict zwingt zu Annotation, deckt Bugs auf (BUG-03 wäre sofort sichtbar). BUG-Fixes ändern dann Signaturen, Re-Annotation nötig. | |
| Verzahnt: pro Modul | Modul-für-Modul: annotieren + alle BUG-Fixes für dieses Modul mitnehmen. Spart Re-Visits, höchste kognitive Last. | |
| Phase 2 nur fixen-aber-nicht-annotieren-falls-Bug | mypy entdeckt Bug → TODO im VERIFICATION, Phase 1.1 macht Fix-Set. Hält Boundary sauber, akzeptiert kurzfristig kaputten mypy. | |

**User's choice:** 1.1 zuerst, dann Phase 2.
**Notes:** Recommended-Option und ROADMAP-Reihenfolge stimmen überein. Phase 2 wird heute geplant, aber execute-phase Phase 2 wartet auf Phase 1.1 verifiziertes Complete.

---

## odoorpc-toolbox Boundary

| Option | Description | Selected |
|--------|-------------|----------|
| Upgrade auf 0.7.3 + `follow_untyped_imports` overrides | Upgrade, lokal mypy overrides für `odoorpc_toolbox.*` mit `follow_untyped_imports = true` (mypy 1.18+). Optionaler py.typed-PR upstream. | ✓ |
| Typisierter Facade-Wrapper | `_odoo_rpc.py` als dünner Wrapper, strict-Boundary an einer Stelle. Saubere Architektur, mehr Maintenance, blockiert Phase 3. | |
| Per-call `# type: ignore` | 33 no-untyped-call-Errors mit type-ignore-Kommentaren. Verstößt gegen ROADMAP SC-1 "no baseline suppressions". | |
| py.typed-PR upstream + warten | PR an odoorpc-toolbox, neue Version released, dann Phase 2. Sauberste Lösung, aber externe Pipeline-Blockade. | |

**User's choice:** Upgrade auf 0.7.3 + `follow_untyped_imports` overrides.
**Notes:** Captain stellte initial die Frage "odoorpc-toolbox 0.7.3 checken — wurde einiges überarbeitet". Verification ergab: 0.7.3 ist heute released, kein `py.typed`-Marker, aber Source ist annotiert. `follow_untyped_imports` (mypy 1.18+) ist die saubere Brücke. py.typed-PR upstream wandert in Deferred Ideas.

---

## Strict-Mode Ramp

| Option | Description | Selected |
|--------|-------------|----------|
| Modul-für-Modul mit `[[overrides]]` | `strict = true` global, `[[overrides]] disable_error_code = [...]` pro pendender Modul. Ein Plan pro 1–2 Module. Letzter Plan entfernt alle overrides. Erfüllt SC-3 sofort, SC-1 am Ende. | ✓ |
| Big-Bang in einem Plan-Set | Ein großer Plan, alle 131 in einem Sweep. Schneller, aber risk-front-loaded, schwer zu reviewen/reverten. | |
| Kategorie-basiert | Plan 1: type-arg + var-annotated. Plan 2: no-untyped-def. Plan 3: no-untyped-call. Plan 4: Long-Tail. Folgt der Error-Verteilung statt Modul-Grenzen. | |
| TDD-Style: Test-driven per Modul | Pro Modul: Tests-Lock, annotieren, strict, commit. Max. Sicherheit, langsamer Loop. TDD-Mode ist aktuell nicht in config. | |

**User's choice:** Modul-für-Modul mit `[[overrides]]`.
**Notes:** Ramp-Reihenfolge in CONTEXT.md D-04: leaf-first (`_exceptions` → `_yaml_dumper` → `_progress` → `_lang_utils` → `_logging` → `_report` → `_utils` → `_connection` → `_cli`). Letzter Plan strippt alle overrides und assertet SC-1.

---

## Odoo Data Shape Modellierung

| Option | Description | Selected |
|--------|-------------|----------|
| TypedDict für bekannte Shapes, `dict[str, Any]` sonst | Konkrete TypedDicts (IrModelRecord, IrModelFieldsRecord, ReportAction). `dict[str, Any]` für generische YAML/unbekannte Antworten. `cast()`/`isinstance()` an markierten Boundaries. Pragmatisch, dokumentierend. | ✓ |
| `Any` am Boundary, str/int/bool intern | Any am odoorpc-toolbox-Boundary, intern alle Variablen typisiert. Minimal-invasiv, leichteres mypy-Bypass-Risiko. | |
| Dataclass / Pydantic-Modelle | Pydantic für alle Odoo-Rückgaben. Runtime-Validation. Neue Hard-Dependency, mehr Code, geht über Cleanup-Scope hinaus. | |
| Protocol-Types (structural typing) | Protocol-Klassen für dict-like Objekte. Sehr Python-idiomatisch, aber kompliziert für Subagenten/Reader. | |

**User's choice:** TypedDict für bekannte Shapes, `dict[str, Any]` sonst.
**Notes:** D-06 in CONTEXT.md spezifiziert 3-Tier-Pragma: Tier 1 TypedDict für recurring Shapes (in `_odoo_types.py`), Tier 2 `dict[str, Any]` für generische/dynamische, Tier 3 `cast()`/`isinstance()` an klar markierten Read-Boundary-Stellen. Keine Pydantic-Dependency.

---

## odoorpc-toolbox Upgrade Timing

| Option | Description | Selected |
|--------|-------------|----------|
| Sofort, eigener Commit vor Phase 1.1 | Bump pyproject.toml, Tests grün, Commit. Phase 1.1 und Phase 2 bauen beide auf 0.7.3. | ✓ |
| Als Task in Phase 2 | Upgrade ist Teil des ersten Phase-2-Plans. Phase 1.1 läuft noch auf 0.7.2. | |
| Defer auf Phase 4 | Phase 4 macht Dependency-Hygiene. 0.7.2 reicht für alle Phasen davor. Konservativ. | |

**User's choice:** Sofort, eigener Commit vor Phase 1.1.
**Notes:** Captain wählte die proaktive Variante. Commit ist nicht Teil eines Phase-Plans (D-02 markiert es als Phase-1.1-Prerequisite-Step). Risiko-Mitigation: vor Commit `uv run pytest` muss 335-grün bleiben; falls 0.7.3 Breaking-Changes hat → Captain entscheidet (Pin auf 0.7.2 oder Anpassung).

---

## Claude's Discretion

Aus CONTEXT.md D-04 + Claude's-Discretion-Sektion:

- **Internal helper splitting** — wenn `_utils.py` (517 LOC) oder `_connection.py` (873 LOC) durch Annotations unhandlich wird, darf der Planner sie aufsplitten. Default: intakt lassen.
- **TypedDict location** — `_odoo_types.py` empfohlen, aber Planner darf Single-Use-Shapes inline lassen.
- **Mypy plugin** — nicht in Scope. Falls eine Lib einen Plugin braucht, Planner flag als Deviation.

## Deferred Ideas

- **`py.typed`-PR upstream an `odoorpc-toolbox`** — Equitania ist Author, einzeilige Änderung. Captain-Aufgabe oder separater Side-Quest. Nach Release kann Phase 4 die `follow_untyped_imports`-Override droppen.
- **`_logging.LoggerManager._loggers` Refactor** — fragile area aus Phase 1, nur annotieren in Phase 2.
- **Pydantic für Runtime-Validation** — explizit out-of-scope. Re-eval bei v1.1.
- **`_connection.py` / `_utils.py` Splitting** — Claude's-Discretion, nur falls unhandlich.
- **Runtime type-checking (beartype, typeguard)** — nicht in Scope. v1.x add-on möglich.
