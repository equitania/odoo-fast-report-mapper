# Requirements — odoo-fast-report-mapper v1.0

**Milestone:** v1.0 Cleanup
**Scope:** Reines Tech-Debt-Cleanup. Keine neuen Features. Breaking-Changes erlaubt (Semver-Major-Bump).
**Audience:** Equitania intern, ownerp-demodata, externe Odoo-Partner, PyPI-Public-User
**Source:** REVIEW.md (v0.9.6 Code Review, 11.05.2026) + Codebase-Map + Captain-Entscheidungen vom 11.05.2026

---

## v1.0 Requirements

### Consolidation

- [x] **CONS-01**: `odoo_report_helper/` package wird vollständig in `odoo_fast_report_mapper/` aufgelöst. Inhalte (`OdooConnection`, `Report`, `utils`, `exceptions`) wandern als Untermodule (z.B. `odoo_fast_report_mapper/_connection.py`, `_report.py`, `_utils.py`, `exceptions.py`). Nach v1.0 existiert nur noch ein Package.

- [x] **CONS-02**: Circular import zwischen den zwei Packages ist eliminiert. Alle Tests können auch in Isolation kollektiert werden (`pytest tests/test_odoo_connection.py` allein darf nicht mehr scheitern).

- [x] **CONS-03**: Override-Smell aufgelöst — `EqOdooConnection` erweitert die Basis statt sie zu überschreiben. Gemeinsame Logik liegt in einer Basisklasse (oder in Modul-Funktionen), nicht doppelt.

- [x] **CONS-04**: Tot-aber-defekte Base-Class-Pfade entfernt (B-01/B-03 Fixes in v0.9.7 waren Pflaster — v1.0 entfernt den toten Code statt ihn zu reparieren).

### Dead-Code-Removal

- [x] **DEAD-01**: `ProgressBar`-Klasse aus `progress.py` entfernt. Konsumenten nutzen `tqdm` direkt (siehe MIGRATION.md). Tests für `ProgressBar` entfernt.

- [x] **DEAD-02**: `create_progress_bar()`-Factory entfernt. Tests entfernt.

- [x] **DEAD-03**: `ReportProgress`-Klasse mit ihren statischen Methoden (`mapping_progress`, `field_progress`, `testing_progress`) entfernt. Tests entfernt.

- [ ] **DEAD-04**: `progress_bar()`-Wrapper-Funktion bleibt — sie wird intern in `eq_odoo_connection.py` verwendet. (Nur die ungenutzten Klassen-APIs sind in Scope.)

### Type-Safety

- [ ] **TYPE-01**: `mypy --strict odoo_fast_report_mapper/` läuft fehlerfrei für den gesamten Production-Code. Alle 13 baseline-Errors aus v0.9.7 sind aufgelöst, nicht nur ignoriert.

- [ ] **TYPE-02**: Type-Annotations für alle Public-Funktionen und Methods. `from __future__ import annotations` wird projektweit eingeführt falls für lesbarere Annotations nötig.

- [ ] **TYPE-03**: Mypy-Konfiguration in `pyproject.toml` aktualisiert auf `strict = true` (statt der aktuellen permissiven Konfiguration).

### Performance

- [ ] **PERF-01**: Benchmark für `collect_report_entries()` etabliert — misst RPC-Call-Count gegen ein definiertes Sample (z.B. 10 Reports × 50 Fields). Implementiert via Mock-Counter auf der RPC-Schicht.

- [ ] **PERF-02**: `add_field_to_dictionary()` macht maximal **0 zusätzliche** RPC-Calls pro Field (die 2 aktuellen `IR_MODEL.search()` + `IR_FIELDS.search()`-Calls werden eliminiert, z.B. durch Caching pro Modul oder Pre-Fetch).

- [ ] **PERF-03**: Performance-Regression-Test im pytest-Suite — Benchmark-Test scheitert, falls die RPC-Call-Count über dem definierten Limit liegt. CI-enforced.

- [ ] **PERF-04**: Konkrete Zielwerte dokumentiert: Sample-DB X Reports → max Y RPC-Calls insgesamt (genaue Zahlen werden in der Performance-Phase festgelegt nach Baseline-Messung).

### Documentation

- [ ] **DOCS-01**: `MIGRATION.md` im Repo-Root erstellt. Enthält:
  - Vollständige Import-Pfad-Mapping `odoo_report_helper.X` → `odoo_fast_report_mapper.X`
  - Before/After-Beispiele für jede entfernte Klasse (`ProgressBar`, `ReportProgress`, `create_progress_bar`)
  - Konkrete Code-Snippets für Migration (z.B. `from tqdm import tqdm` Pattern statt `ProgressBar`)
  - Deprecation-Map mit Begründung
  - Mypy-Strict-Implikation für Konsumenten die Typecheck gegen die Lib laufen lassen

- [ ] **DOCS-02**: `README.md` (DE + EN) auf v1.0-Stand: alle Verweise auf `odoo_report_helper` entfernt oder als historisch markiert. Aktuelle Architecture-Sektion. `MIGRATION.md` prominent verlinkt.

- [ ] **DOCS-03**: `RELEASE_NOTES.md` mit v1.0-Eintrag — vollständiger Changelog, Breaking-Changes-Sektion ganz oben, Link zu MIGRATION.md.

- [ ] **DOCS-04**: `SKILL.md` (`~/.claude/skills/fr-mapper/SKILL.md`) auf v1.0 aktualisiert — Project Structure Sektion zeigt nur ein Package, Version-History bekommt v1.0-Eintrag, Skill-Hierarchy-Tabelle aktualisiert.

- [ ] **DOCS-05**: Project `CLAUDE.md` aktualisiert — File-Structure-Block und Architecture-Sektion auf das single-Package-Layout.

### CI / Tooling

- [ ] **CI-01**: GitHub Actions CI-Matrix erweitert um Python 3.14 (falls Stable bis v1.0-Release). Fallback: Matrix bleibt Python 3.12 + 3.13 wenn 3.14 noch RC ist.

- [ ] **CI-02**: Mypy-Strict-Check im CI-Workflow aktiv (statt der aktuellen permissiven Konfiguration).

- [ ] **CI-03**: Performance-Benchmark-Test läuft im CI mit definiertem Threshold. Failure blockt Merge zu `develop`/`main`.

### Release-Quality-Gates

- [ ] **GATE-01**: Alle Tests grün (369 minus die legitim entfernten P-08/P-09-Tests). Test-Count nach Cleanup dokumentiert in RELEASE_NOTES.
- [ ] **GATE-02**: Ruff check + format clean.
- [ ] **GATE-03**: Mypy strict pass.
- [ ] **GATE-04**: Migration-Guide manuell von Captain reviewed.
- [ ] **GATE-05**: `uv build` produziert wheel + sdist ohne Fehler. **`uv publish` wird ausschließlich von Captain ausgeführt** — Claude führt diesen Befehl niemals aus.

### Correctness-Bug-Fixes

> Hinzugefügt 27.05.2026 nach dem Baseline-Code-Review (`.planning/BASELINE-REVIEW.md`, v0.9.7.3, deep). Der ursprüngliche v1.0-Scope war reines Tech-Debt-Cleanup; diese Bugs sind echte Korrektheitsfehler (Crashes, stille Datenkorruption, umgangene Validierung), die das Cleanup-Vorhaben sonst unverändert überlebt hätten. Bewusste Scope-Erweiterung per Captain-Entscheidung. Werden in Phase 1.1 — nach der Konsolidierung — in der finalen Package-Struktur behoben.

- [ ] **BUG-01** (Review CR-02): `add_field_to_dictionary()` indiziert `IR_MODEL.search()` ungeschützt (`model_id[0]`). Leeres Suchergebnis → `IndexError` mitten in der Iteration, `data_dictionary` bleibt korrupt. Fix: Ergebnis vor Zugriff prüfen; Regressionstest für den Leer-Fall.

- [ ] **BUG-02** (Review CR-03): `self_clean()` zerstört Calculated-Field-Parameter — `list(dict.fromkeys(value))` iteriert nur die Keys eines Inner-Dicts. `{"eq_get_payment_terms": ["p1","p2"]}` wird zu `["eq_get_payment_terms"]`. Fix: verschachtelte Struktur erhalten; Regressionstest prüft Unversehrtheit.

- [ ] **BUG-03** (Review CR-04): `check_dependencies` gibt `Tuple[bool, list]` zurück, Basis-`map_reports` nutzt den Wert als Bool — `bool((False, [...]))` ist immer `True`, Dependency-Check wird still umgangen. Fix: Contract zwischen Methode und Caller angleichen; Regressionstest beweist, dass eine fehlende Dependency den Lauf stoppt.

- [ ] **BUG-04** (Review WR-03): `build_name_search_domain({})` liefert `[]` → unbegrenzte „alle Reports für Modell"-Suche statt lautem Fehler. Fix: leeren Input guarden / laut scheitern.

- [ ] **BUG-05** (Review WR-04): `prepare_connection` URL-Parsing via `str.replace("https:", "")` behält Pfad-Komponenten (`https://host/web` → Host `host/web`). Fix: Schema + Pfad korrekt strippen.

- [ ] **BUG-06** (Review WR-05): `Report.__init__` annotiert `entry_name: str`, erhält zur Laufzeit aber ein `dict` — Basis-`self_ensure()` würde ein dict-Objekt in Odoos `name`-Feld schreiben. Fix: Typ-/Laufzeit-Handling angleichen.

- [ ] **BUG-07** (Review WR-07): `create_odoo_connection_from_yaml_object` hardcodet `auth_method='password'` — ein API-Key in der YAML wird still als Passwort behandelt. Fix: konfigurierte Auth-Methode respektieren.

---

## Out of Scope für v1.0

Explizite Ausschlüsse mit Begründung:

- **Bulk-Operationen** — Multi-Odoo-Server-Batch-Mapping, parallele Report-Registration über Server-Liste. *Warum out: v1.0 ist 100% Cleanup, keine neuen Features. Mögliche v1.1.*
- **OAuth / SSO / weitere Auth-Methoden** — v1.0 ships mit Password + API-Key only. *Warum out: Feature-Addition, kein Cleanup-Konzern. Mögliche v1.1.*
- **Report-Templates-Generator** — Scaffolding-Tool für neue YAML/FRX-Reports. *Warum out: Separates Tool-Konzept; gehört nicht zu fr-mapper.*
- **Interactive TUI** (z.B. Textual) — Eine GUI-ähnliche Console-UX. *Warum out: CLI mit Click ist die etablierte und ausreichende UX.*
- **Direkter FastReport-API-Aufruf** umgehe der Odoo-ORM-Methode `eq_render_fast_report`. *Warum out: Verletzt etablierte Daten-Pipeline. Architektur-Verletzung.*
- **Auto-PyPI-Publish via CI** — `uv publish` in der Pipeline. *Warum out: Captain-Policy ist manuelles Release. Sicherheitskontrolle gegen versehentlichen falschen Release.*
- **Backward-Compat-Aliase** für `odoo_report_helper.*` Imports. *Warum out: Hard-Break by design für v1.0. MIGRATION.md ersetzt die Alias-Phase. Wenn nötig, wird in v1.1 eine optionale Compat-Shim geliefert.*
- **DeprecationWarnings** für entfernte APIs. *Warum out: Major-Bump (v0.9.7 → v1.0) signalisiert Breaking. Migration-Guide ist der saubere Pfad.*
- **Drop Python 3.12 Support** zugunsten von 3.13+ only. *Warum out: 3.12 ist verbreitet (Odoo v17/v18-Standard). Drop wäre unnötig hart.*

---

## v2.0 (Defer, nicht Out of Scope)

Diese Items haben Wert, sind aber nach v1.0:

- Optionale Backward-Compat-Shim für `odoo_report_helper.*` Imports — als v1.1-Add-On wenn Konsumenten-Feedback hart darum bittet
- DeprecationWarning-Phase für künftige Removals (etabliert ab v1.0 als Policy)
- Erweiterte Performance-Optimierungen über `add_field_to_dictionary` hinaus (z.B. Bulk-`write()` statt einzelner Calls in `_write_field_mappings`)

---

## Traceability

<!-- Filled by gsd-roadmapper when ROADMAP.md is created. Maps each REQ-ID to its phase. -->

| Requirement | Phase | Status |
|-------------|-------|--------|
| CONS-01 | Phase 1 — Package Consolidation | Complete |
| CONS-02 | Phase 1 — Package Consolidation | Complete |
| CONS-03 | Phase 1 — Package Consolidation | Complete |
| CONS-04 | Phase 1 — Package Consolidation | Complete |
| DEAD-01 | Phase 1 — Package Consolidation | Complete |
| DEAD-02 | Phase 1 — Package Consolidation | Complete |
| DEAD-03 | Phase 1 — Package Consolidation | Complete |
| TYPE-01 | Phase 2 — Type Safety | Pending |
| TYPE-02 | Phase 2 — Type Safety | Pending |
| TYPE-03 | Phase 2 — Type Safety | Pending |
| PERF-01 | Phase 3 — Performance | Pending |
| PERF-02 | Phase 3 — Performance | Pending |
| PERF-03 | Phase 3 — Performance | Pending |
| PERF-04 | Phase 3 — Performance | Pending |
| DOCS-01 | Phase 4 — Release Preparation | Pending |
| DOCS-02 | Phase 4 — Release Preparation | Pending |
| DOCS-03 | Phase 4 — Release Preparation | Pending |
| DOCS-04 | Phase 4 — Release Preparation | Pending |
| DOCS-05 | Phase 4 — Release Preparation | Pending |
| CI-01 | Phase 4 — Release Preparation | Pending |
| CI-02 | Phase 4 — Release Preparation | Pending |
| CI-03 | Phase 4 — Release Preparation | Pending |
| GATE-01 | Phase 4 — Release Preparation | Pending |
| GATE-02 | Phase 4 — Release Preparation | Pending |
| GATE-03 | Phase 4 — Release Preparation | Pending |
| GATE-04 | Phase 4 — Release Preparation | Pending |
| GATE-05 | Phase 4 — Release Preparation | Pending |
| BUG-01 | Phase 1.1 — Correctness Bug Fixes | Pending |
| BUG-02 | Phase 1.1 — Correctness Bug Fixes | Pending |
| BUG-03 | Phase 1.1 — Correctness Bug Fixes | Pending |
| BUG-04 | Phase 1.1 — Correctness Bug Fixes | Pending |
| BUG-05 | Phase 1.1 — Correctness Bug Fixes | Pending |
| BUG-06 | Phase 1.1 — Correctness Bug Fixes | Pending |
| BUG-07 | Phase 1.1 — Correctness Bug Fixes | Pending |

**Coverage: 34/34 requirements mapped** (DEAD-04 is not in scope — it is an explicit exclusion documented in REQUIREMENTS.md; progress_bar() stays. BUG-01..BUG-07 added 27.05.2026 from the baseline review — see Correctness-Bug-Fixes section.)

---

*Erstellt: 2026-05-11. Basis: REVIEW.md (v0.9.6), Captain-Q&A 11.05.2026.*
