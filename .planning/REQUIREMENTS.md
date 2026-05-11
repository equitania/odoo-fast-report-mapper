# Requirements — odoo-fast-report-mapper v1.0

**Milestone:** v1.0 Cleanup
**Scope:** Reines Tech-Debt-Cleanup. Keine neuen Features. Breaking-Changes erlaubt (Semver-Major-Bump).
**Audience:** Equitania intern, ownerp-demodata, externe Odoo-Partner, PyPI-Public-User
**Source:** REVIEW.md (v0.9.6 Code Review, 11.05.2026) + Codebase-Map + Captain-Entscheidungen vom 11.05.2026

---

## v1.0 Requirements

### Consolidation

- [ ] **CONS-01**: `odoo_report_helper/` package wird vollständig in `odoo_fast_report_mapper/` aufgelöst. Inhalte (`OdooConnection`, `Report`, `utils`, `exceptions`) wandern als Untermodule (z.B. `odoo_fast_report_mapper/_connection.py`, `_report.py`, `_utils.py`, `exceptions.py`). Nach v1.0 existiert nur noch ein Package.

- [ ] **CONS-02**: Circular import zwischen den zwei Packages ist eliminiert. Alle Tests können auch in Isolation kollektiert werden (`pytest tests/test_odoo_connection.py` allein darf nicht mehr scheitern).

- [ ] **CONS-03**: Override-Smell aufgelöst — `EqOdooConnection` erweitert die Basis statt sie zu überschreiben. Gemeinsame Logik liegt in einer Basisklasse (oder in Modul-Funktionen), nicht doppelt.

- [ ] **CONS-04**: Tot-aber-defekte Base-Class-Pfade entfernt (B-01/B-03 Fixes in v0.9.7 waren Pflaster — v1.0 entfernt den toten Code statt ihn zu reparieren).

### Dead-Code-Removal

- [ ] **DEAD-01**: `ProgressBar`-Klasse aus `progress.py` entfernt. Konsumenten nutzen `tqdm` direkt (siehe MIGRATION.md). Tests für `ProgressBar` entfernt.

- [ ] **DEAD-02**: `create_progress_bar()`-Factory entfernt. Tests entfernt.

- [ ] **DEAD-03**: `ReportProgress`-Klasse mit ihren statischen Methoden (`mapping_progress`, `field_progress`, `testing_progress`) entfernt. Tests entfernt.

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

(Pending — roadmapper agent fills this section after ROADMAP.md generation.)

---

*Erstellt: 2026-05-11. Basis: REVIEW.md (v0.9.6), Captain-Q&A 11.05.2026.*
