# Phase 1: Package Consolidation - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-05-28
**Phase:** 1-Package Consolidation
**Areas discussed:** Klassen-Architektur, Submodul-Naming-Konvention, Dead-Base-Code-Scope, Test-File-Reorganisation

---

## Klassen-Architektur

| Option | Description | Selected |
|--------|-------------|----------|
| Single merged class | OdooConnection und EqOdooConnection zu einer Klasse mergen. Klarstes Mental Model, kein Override-Smell mehr möglich. Aligned mit PROJECT.md 'Vereinfacht das Mental Model'. | ✓ |
| Base + sauberer Extension | Zwei Klassen behalten, aber Override-Smell auflösen — z.B. Base = nur Low-Level RPC, Extension = Report-spezifische Logik. | |
| Modul-Funktionen + Single Class | Eine Connection-Klasse behält nur State. Report-Logik wandert in modulare Funktionen. Funktional statt OO. | |

**User's choice:** Single merged class.
**Notes:** Drives all downstream decisions — the override-smell that PROJECT.md flagged is structurally eliminated only by merging.

| Option | Description | Selected |
|--------|-------------|----------|
| OdooConnection | Drop Eq-Prefix. Klarster Name nach Konsolidierung. Success Criteria #3 deutet das an. | ✓ |
| EqOdooConnection | Behält Equitania-Spezifika im Namen — signalisiert: diese Klasse ist nicht generic. | |
| FastReportMapper | Domain-orientierter Name. Bigger rename, mehr Konsumenten-Impact. | |

**User's choice:** OdooConnection.

| Option | Description | Selected |
|--------|-------------|----------|
| Parallel mergen → Report | EqReport überschreibt entry_name (string → dict) und fügt 7 Felder hinzu. Same pattern wie Connection. | ✓ |
| Nur EqReport behalten, umbenennen zu Report | Die alte Base 'Report' ist ohnehin unbenutzbar für Eq-Use-Case. Einfach löschen. | |
| Dataclass statt Klasse | Report ist im Wesentlichen ein Daten-Container. Mit @dataclass leaner. | |

**User's choice:** Parallel mergen → Report.

| Option | Description | Selected |
|--------|-------------|----------|
| Bleibt in utils-Modul | create_connection_from_env() bleibt im _utils.py Modul. Saubere Trennung: Klasse = State, Factory = Konstruktion. | ✓ |
| Classmethod auf OdooConnection | OdooConnection.from_env() als classmethod. Pythonic, aber bindet Env-Parsing-Konvention an die Klasse. | |
| Modul-Level-Function direkt neben Klasse | In _connection.py. Eng gekoppelt, aber vermischt Concerns. | |

**User's choice:** Bleibt in utils-Modul.

---

## Submodul-Naming-Konvention

| Option | Description | Selected |
|--------|-------------|----------|
| Public (connection.py, report.py) | Kein Underscore-Prefix. Konsumenten können sub-path importieren. Signal: stabile API. | |
| Private (_connection.py, _report.py) | Mit Underscore-Prefix. Public API nur über __init__.py re-exports. Signal: 'Submodul-Struktur ist Implementation Detail'. | ✓ |
| Hybrid | Bewusst getrennt nach Stabilitätsversprechen. | |

**User's choice:** Private mit Underscore-Prefix.
**Notes:** REQUIREMENTS.md hat das vorgeschlagen, Captain hat es bestätigt. Gibt v1.x-Refactoring-Freiheit.

| Option | Description | Selected |
|--------|-------------|----------|
| Klassen + Factory + Exceptions | OdooConnection, Report, create_connection_from_env, alle Custom Exceptions. 99% Konsumenten-Use-Case. | ✓ |
| Nur die Klassen | Strenger, mehr Tippen für Konsumenten. | |
| Alles — Klassen, Funktionen, Helpers | Maximaler Komfort, aber breite stabile API-Oberfläche. | |

**User's choice:** Klassen + Factory + Exceptions.

| Option | Description | Selected |
|--------|-------------|----------|
| Alle private mit Underscore | _lang_utils.py, _logging.py, _yaml_dumper.py. Konsistent. MyDumper bei Gelegenheit umbenennen. | ✓ |
| Public (lang_utils.py, logging_config.py) | Behalten ohne Underscore. Inkonsistent zu _connection.py. | |
| lang_utils privat, Rest behalten | Nur _lang_utils.py umbenennen (war Quelle des circular imports). | |

**User's choice:** Alle private mit Underscore.

| Option | Description | Selected |
|--------|-------------|----------|
| Bleibt als _progress.py mit context manager | Nur progress_bar() context manager bleibt. ~50 LOC statt 208 LOC. | ✓ |
| Löschen, tqdm direkt importieren | 5-Zeilen-Funktion ist kein Modul wert. Inline mit `from tqdm import tqdm`. | |
| progress_bar in _utils.py mergen | Eine Helper-Funktion ist kein eigenes Modul wert. | |

**User's choice:** _progress.py mit context manager.

---

## Dead-Base-Code-Scope

| Option | Description | Selected |
|--------|-------------|----------|
| Eq-Version übernehmen, Base-Code weg | Die Eq-Version ist die Production-Logik. v0.9.7 Pflaster verschwinden automatisch. | ✓ |
| Beide-Versionen verschmelzen / vereinheitlichen | Tiefes Review: Gibt es Code-Pfade in der Base, die in der Eq-Version verloren würden? | |
| Eq-Version + Base-Tests weg | Wie Option 1, aber explizit auch test_odoo_connection.py + test_report.py + test_helper_utils.py löschen. | |

**User's choice:** Eq-Version übernehmen.

| Option | Description | Selected |
|--------|-------------|----------|
| Inline mergen in OdooConnection | login, authenticate, version-checks als Methoden in die neue Klasse. Eliminiert super()-Calls. | ✓ |
| Wie Modul-Funktionen ausgliedern | Statt Methoden → freie Funktionen in _utils.py. | |
| Als private Methoden behalten (_login, _authenticate) | Klar als 'internal' markiert. | |

**User's choice:** Inline mergen in OdooConnection.

| Option | Description | Selected |
|--------|-------------|----------|
| Implizit weg mit der Base | Da die Base-Klassen verschwinden, verschwinden die Patches automatisch. Keine separate Aktion. | ✓ |
| Vor dem Löschen in MIGRATION.md dokumentieren | MIGRATION.md erwähnt explizit, dass die Logik in der Eq-Version gleich bleibt. | |
| Prüfen, ob die Eq-Version den Fix unabhängig auch hat | Sanity-check. | |

**User's choice:** Implizit weg mit der Base.

| Option | Description | Selected |
|--------|-------------|----------|
| Exceptions in _exceptions.py, utils ein-by-eins | exceptions.py → _exceptions.py. Helper aus utils.py case-by-case in _utils.py mergen. | ✓ |
| Alles in _utils.py konsolidieren | Schmaler, aber vermischt Concerns. | |
| Dead-Drop check: nur was wirklich benutzt wird | Aggressiv: grep -r alle Imports, alles ungenutzte sofort raus. | |

**User's choice:** Exceptions in _exceptions.py, utils selektiv.

---

## Test-File-Reorganisation

| Option | Description | Selected |
|--------|-------------|----------|
| Mergen zu test_connection.py | Beide Files testen die gleiche Klasse. Eq-Tests übernehmen, Base-Tests die nicht-redundante Aspekte. | ✓ |
| test_eq_odoo_connection.py umbenennen, test_odoo_connection.py löschen | Aggressiv: nur die Eq-Tests sind Production-Code. Riskant. | |
| Prüfen welche Base-Tests unique coverage haben | Vorsichtig: erst Coverage-Gap-Analyse. | |

**User's choice:** Mergen zu test_connection.py.

| Option | Description | Selected |
|--------|-------------|----------|
| Symmetrisch mergen → test_report.py + test_utils.py | Konsistent zur Connection-Entscheidung. 13 Test-Files → ~9. | ✓ |
| Einzeln prüfen, manche getrennt | Report-Tests merge, utils-Tests trennen. | |
| Komplette Test-Reorg by Feature | test_connection_login.py, test_connection_mapping.py, etc. Bigger Refactor. | |

**User's choice:** Symmetrisch mergen.

| Option | Description | Selected |
|--------|-------------|----------|
| Drastisch zurückschneiden (~30 LOC) | Nur progress_bar() context manager testen. ~220 LOC weg. Konsistent mit DEAD-01/02/03. | ✓ |
| test_progress.py löschen, progress_bar() in test_utils.py | Wenn _progress.py nur 1 Funktion hat. | |
| test_progress.py beibehalten, klein | Klare 1:1-Mapping Modul → Test-File. | |

**User's choice:** Drastisch zurückschneiden.

| Option | Description | Selected |
|--------|-------------|----------|
| pytest --cov vor/nach + Diff | Baseline coverage.xml auf develop, nach Phase 1 nochmal. Modul-Level-Diff. Verlust nur für gelöschten Dead-Code akzeptabel. | ✓ |
| Test-Count vor/nach (369 → X) | Einfacher Zähler. | |
| Manuelle Test-Inventur in PLAN.md | Audit-Trail-Tabelle. | |

**User's choice:** pytest --cov vor/nach + Diff.

---

## Claude's Discretion

- Commit strategy (atomic vs. mega-commit) — Planner-Sache. [ADD]/[CHG]/[FIX] prefix convention gilt.
- Order of operations within the phase (move-first vs. delete-first) — Planner-Sache.
- CLI module renaming (`odoo_fast_report_mapper.py` → `_cli.py`) — empfohlen für Konsistenz, aber Planner kann bestätigen oder skippen.
- Sub-module file boundaries within `_utils.py` — keep it one file or split bei ~300 LOC.

## Deferred Ideas

- `LoggerManager._loggers` class-level mutable dict refactor — fragile area, deferred zu v1.x oder Phase 2.
- CLI by-feature test reorganization — out of Phase 1 scope.
- Type hints throughout — Phase 2 (TYPE-01).
- `add_field_to_dictionary` RPC-call reduction — Phase 3 (PERF-01).
- Tiefere YAML-Dumper-Semantik-Refactor — über das Rename hinaus deferred.
