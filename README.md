# Odoo Fast Report Mapper

[![PyPI version](https://badge.fury.io/py/odoo-fast-report-mapper-equitania.svg)](https://badge.fury.io/py/odoo-fast-report-mapper-equitania)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: AGPL v3](https://img.shields.io/badge/License-AGPL%20v3-blue.svg)](https://www.gnu.org/licenses/agpl-3.0)
[![Tests](https://img.shields.io/badge/tests-353%20passed-brightgreen.svg)]()

> **Language / Sprache**: [DE](#deutsche-dokumentation) | [EN](#english-documentation)

---

## Deutsche Dokumentation

### Projektübersicht

Eine Python CLI-Bibliothek zur Erstellung, Verwaltung und Testung von FastReport-Einträgen in Odoo-Umgebungen. Unterstützt das [FastReport-Modul für Odoo](https://www.ownerp.com/odoo-fastreport) von Equitania Software GmbH.

### Mehrwerte

- **Berichte automatisiert einrichten** – ein komplettes Belegset aus zentralen
  Konfigurationsdateien in einem Durchlauf registrieren, statt jeden Bericht von Hand zu pflegen.
- **Einheitlich über viele Systeme** – dieselbe Konfiguration reproduzierbar auf Test-, Abnahme-
  und Produktivumgebungen ausrollen.
- **Sicherheit vor dem Echteinsatz** – Berichte testweise erzeugen und Fehler erkennen, bevor sie
  beim Kunden landen.
- **Mehrsprachig ohne Zusatzaufwand** – Berichtsnamen werden automatisch für alle aktiven
  Odoo-Sprachen gepflegt.
- **Nichts geht verloren** – in Odoo angepasste Berichte jederzeit selektiv zurück nach YAML
  sichern, versionieren und auf ein anderes System übertragen.

### Upgrade auf v1.0

Nutzer, die von einer früheren Version upgraden, finden alle Breaking Changes und Import-Pfad-Anpassungen in der **[MIGRATION.md](MIGRATION.md)**.

### Hauptfunktionen

- **Report-Mapping**: Automatische Erstellung und Aktualisierung von `ir.actions.report`-Einträgen in Odoo
- **Feld-Zuordnung**: Intelligente Zuordnung von Odoo-Modellfeldern zu Berichten via `eq_write_report_ids`
- **Berechnete Felder**: Unterstützung für benutzerdefinierte Berechnungen mit Parametern (`eq_calculated_field_value`)
- **Test-Rendering**: Validierung der FastReport-Dokumente vor der Produktionsfreigabe (Workflow 1/2)
- **Mehrsprachigkeit**: Unbegrenzte Sprachen via Odoo Locale-Codes (de_DE, en_US, fr_FR, etc.) mit automatischer Erkennung installierter Sprachen aus `res.lang`
- **Interaktive YAML-Auswahl**: Mit `--select` gezielt einzelne YAML-Dateien zur Verarbeitung auswählen
- **YAML-Sammlung**: Bei `ODOO_COLLECT_YAML=True` werden bestehende FastReports tabellarisch angezeigt und als YAML exportiert
- **Mehrere Exportformate**: PDF, TXT, XML, PNG, JPG, TIFF, ODS, ODT, XLS, DOC

### Workflow-Optionen

| Workflow | Modus | Beschreibung |
|----------|-------|-------------|
| 0 | Nur Mapping | Erstellt/aktualisiert Berichte in Odoo (Standard) |
| 1 | Nur Testing | Testet FastReport-Rendering via `eq_render_fast_report` |
| 2 | Mapping + Testing | Beide Operationen nacheinander |

### Voraussetzungen

Python >= 3.10 und [UV](https://docs.astral.sh/uv/) müssen installiert sein.

| Betriebssystem | Python | UV |
|----------------|--------|-----|
| macOS | `brew install python@3.12` | `brew install uv` |
| Linux / WSL | `sudo apt install python3.12` | `curl -LsSf https://astral.sh/uv/install.sh \| sh` |
| Windows | [python.org](https://www.python.org/downloads/) | `powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 \| iex"` |

### Installation

```bash
# Als CLI-Tool (empfohlen)
uv tool install odoo-fast-report-mapper-equitania

# Aktualisierung
uv tool upgrade odoo-fast-report-mapper-equitania
```

### Erste Schritte

```bash
# 1. .env Template generieren
odoo-fr-mapper --init

# 2. .env mit Zugangsdaten konfigurieren
nano .env

# 3. Reports mappen
odoo-fr-mapper --yaml_path=./reports_yaml

# 4. Interaktive Auswahl einzelner YAML-Dateien
odoo-fr-mapper --yaml_path=./reports_yaml --select
```

### CLI-Optionen

```bash
odoo-fr-mapper --help              # Hilfe anzeigen
odoo-fr-mapper --version           # Version anzeigen
odoo-fr-mapper --init              # .env Template generieren
odoo-fr-mapper --yaml_path=PFAD    # YAML-Verzeichnis angeben
odoo-fr-mapper --env_path=PFAD     # .env Datei/Verzeichnis angeben
odoo-fr-mapper --select            # Interaktive YAML-Auswahl
```

### Konfiguration (.env)

```bash
# Odoo Server Verbindung (Pflicht)
ODOO_URL=https://your-odoo-instance.com
ODOO_PORT=443
ODOO_USER=admin
ODOO_DATABASE=your_database

# Authentifizierung (Pflicht — eine Variante wählen)
ODOO_PASSWORD=your_password       # Klassisch: Benutzername + Passwort
# ODOO_API_KEY=your_api_key       # Alternative: API-Key (Odoo >= 14, empfohlen ab v16)
                                  # Beide gesetzt? API-Key gewinnt mit Warnung.

# Report-Konfiguration (Pflicht)
ODOO_LANGUAGE=de_DE               # Odoo Locale-Code (de_DE, en_US, fr_FR, etc.)
                                  # Legacy-Codes (ger, eng) werden automatisch normalisiert

# Optionale Konfiguration
ODOO_COLLECT_YAML=False           # YAML-Sammlung aus Odoo (interaktive Auswahl)
ODOO_DISABLE_QWEB=True            # QWeb-Berichte nach Mapping deaktivieren
ODOO_WORKFLOW=0                   # 0=Mapping, 1=Testing, 2=Beides
```

### Report YAML-Format

```yaml
name:
  de_DE: Verkaufsauftrag
  en_US: Sales_Order
report_name: eq_fr_core_sale_order
report_model: sale.order
report_type: fast_report
eq_export_type: pdf
eq_print_button: false
eq_multiprint: create_zip
eq_handling_html_fields: standard
eq_ignore_images: false
attachment_use: true
attachment: "'Verkaufsauftrag-' + object.name + '.pdf'"
print_report_name: "'Verkaufsauftrag-' + object.name"
multi: false
company_id:
  - 1
dependencies:
  - eq_fr_core
  - sale
report_fields:
  sale.order:
    - id
    - name
    - partner_id
    - amount_total
calculated_fields:
  payment_text:
    eq_get_payment_terms:
      - partner_id.lang
      - currency_id
```

### Erweiterte Beispiele

```bash
# Odoo v18 Produktionsumgebung
odoo-fr-mapper --yaml_path=$HOME/gitbase/v18/v18-fast-report/reports/yaml

# Mit spezifischer .env Datei
odoo-fr-mapper --yaml_path=./yaml --env_path=/path/to/config/.env

# YAML-Sammlung mit interaktiver Report-Auswahl
# (ODOO_COLLECT_YAML=True in .env)
odoo-fr-mapper --yaml_path=./output
```

### Benutzerhandbuch

Ausführliche, einsatzzweck-orientierte Schritt-für-Schritt-Anleitungen (zweisprachig) liegen im
Verzeichnis **[usage/](usage/README.md)**:

| Einsatzzweck | Anleitung |
|--------------|-----------|
| Berichte aus YAML in Odoo **registrieren/aktualisieren** (Mapping, Verbindungsbestätigung, Fehlerverhalten, QWeb ausblenden) | [usage/mapping-reports.md](usage/mapping-reports.md) |
| Berichtsnamen **mehrsprachig** pflegen (automatisch für alle aktiven Odoo-Sprachen) | [usage/multilanguage.md](usage/multilanguage.md) |
| Mit `--select` gezielt **einzelne Berichte** registrieren | [usage/selective-registration.md](usage/selective-registration.md) |
| In Odoo angepasste Berichte **selektiv zurück nach YAML** sichern (Collect-Modus) | [usage/collect-to-yaml.md](usage/collect-to-yaml.md) |

### Weiterführende Abschnitte

Architektur, Entwicklung (Setup, Tests, Code-Qualität), Troubleshooting, Ressourcen und Lizenz sind als gemeinsame englischsprachige Abschnitte am Ende dieses Dokuments zu finden: [Architecture](#architecture) · [Development](#development) · [Troubleshooting](#troubleshooting) · [Resources](#resources) · [License](#license) · [Support](#support)

---

## English Documentation

### Project Overview

A Python CLI library for creating, managing, and testing FastReport entries in Odoo environments. Supports the [FastReport module for Odoo](https://www.ownerp.com/odoo-fastreport) by Equitania Software GmbH.

### Why use it

- **Automated report setup** – register a complete set of documents from central configuration
  files in a single run, instead of maintaining each report by hand.
- **Consistent across systems** – roll out the same configuration reproducibly to test, staging
  and production environments.
- **Safety before going live** – render reports for testing and catch errors before they reach
  the customer.
- **Multilingual with no extra effort** – report names are maintained automatically for all active
  Odoo languages.
- **Nothing gets lost** – save reports adjusted in Odoo selectively back to YAML at any time,
  version them and transfer them to another system.

### Upgrading to v1.0

Users upgrading from an earlier version will find all breaking changes and import path adjustments in **[MIGRATION.md](MIGRATION.md)**.

### Key Features

- **Report Mapping**: Automatic creation and updating of `ir.actions.report` entries in Odoo
- **Field Mapping**: Intelligent mapping of Odoo model fields to reports via `eq_write_report_ids`
- **Calculated Fields**: Support for custom calculations with parameters (`eq_calculated_field_value`)
- **Test Rendering**: Validation of FastReport documents before production release (Workflow 1/2)
- **Multi-language**: Unlimited languages via Odoo locale codes (de_DE, en_US, fr_FR, etc.) with automatic detection of installed languages from `res.lang`
- **Interactive YAML Selection**: With `--select`, choose specific YAML files for mapping
- **YAML Collection**: With `ODOO_COLLECT_YAML=True`, existing FastReports are listed in a table and exported as YAML
- **Multiple Export Formats**: PDF, TXT, XML, PNG, JPG, TIFF, ODS, ODT, XLS, DOC

### Workflow Options

| Workflow | Mode | Description |
|----------|------|-------------|
| 0 | Mapping only | Creates/updates reports in Odoo (default) |
| 1 | Testing only | Tests FastReport rendering via `eq_render_fast_report` |
| 2 | Mapping + Testing | Both operations sequentially |

### Prerequisites

Python >= 3.10 and [UV](https://docs.astral.sh/uv/) must be installed.

| OS | Python | UV |
|----|--------|-----|
| macOS | `brew install python@3.12` | `brew install uv` |
| Linux / WSL | `sudo apt install python3.12` | `curl -LsSf https://astral.sh/uv/install.sh \| sh` |
| Windows | [python.org](https://www.python.org/downloads/) | `powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 \| iex"` |

### Installation

```bash
# As CLI tool (recommended)
uv tool install odoo-fast-report-mapper-equitania

# Update
uv tool upgrade odoo-fast-report-mapper-equitania
```

### Getting Started

```bash
# 1. Generate .env template
odoo-fr-mapper --init

# 2. Configure .env with your credentials
nano .env

# 3. Map reports
odoo-fr-mapper --yaml_path=./reports_yaml

# 4. Interactive selection of specific YAML files
odoo-fr-mapper --yaml_path=./reports_yaml --select
```

### CLI Options

```bash
odoo-fr-mapper --help              # Show help
odoo-fr-mapper --version           # Show version
odoo-fr-mapper --init              # Generate .env template
odoo-fr-mapper --yaml_path=PATH    # Specify YAML directory
odoo-fr-mapper --env_path=PATH     # Specify .env file/directory
odoo-fr-mapper --select            # Interactive YAML selection
```

### Configuration (.env)

```bash
# Odoo Server Connection (Required)
ODOO_URL=https://your-odoo-instance.com
ODOO_PORT=443
ODOO_USER=admin
ODOO_DATABASE=your_database

# Authentication (Required — choose ONE)
ODOO_PASSWORD=your_password       # Classic username + password
# ODOO_API_KEY=your_api_key       # Alternative: API key (Odoo >= 14, recommended for v16+)
                                  # If both are set, the API key wins (with warning).

# Report Configuration (Required)
ODOO_LANGUAGE=de_DE               # Odoo locale code (de_DE, en_US, fr_FR, etc.)
                                  # Legacy codes (ger, eng) are auto-normalized

# Optional Configuration
ODOO_COLLECT_YAML=False           # YAML collection from Odoo (interactive selection)
ODOO_DISABLE_QWEB=True            # Disable QWeb reports after mapping
ODOO_WORKFLOW=0                   # 0=Mapping, 1=Testing, 2=Both
```

### Report YAML Format

```yaml
name:
  de_DE: Verkaufsauftrag
  en_US: Sales_Order
report_name: eq_fr_core_sale_order
report_model: sale.order
report_type: fast_report
eq_export_type: pdf
eq_print_button: false
eq_multiprint: create_zip
eq_handling_html_fields: standard
eq_ignore_images: false
attachment_use: true
attachment: "'Sales-Order-' + object.name + '.pdf'"
print_report_name: "'Sales-Order-' + object.name"
multi: false
company_id:
  - 1
dependencies:
  - eq_fr_core
  - sale
report_fields:
  sale.order:
    - id
    - name
    - partner_id
    - amount_total
calculated_fields:
  payment_text:
    eq_get_payment_terms:
      - partner_id.lang
      - currency_id
```

### Advanced Examples

```bash
# Odoo v18 production environment
odoo-fr-mapper --yaml_path=$HOME/gitbase/v18/v18-fast-report/reports/yaml

# With specific .env file
odoo-fr-mapper --yaml_path=./yaml --env_path=/path/to/config/.env

# YAML collection with interactive report selection
# (set ODOO_COLLECT_YAML=True in .env)
odoo-fr-mapper --yaml_path=./output
```

### User Guide

Detailed, task-oriented step-by-step guides (bilingual) live in the **[usage/](usage/README.md)**
directory:

| Use case | Guide |
|----------|-------|
| **Register/update** reports from YAML in Odoo (mapping, connection confirmation, failure handling, hiding QWeb) | [usage/mapping-reports.md](usage/mapping-reports.md) |
| Maintain report names **multilingually** (automatically for all active Odoo languages) | [usage/multilanguage.md](usage/multilanguage.md) |
| Register **individual reports** selectively with `--select` | [usage/selective-registration.md](usage/selective-registration.md) |
| Save reports adjusted in Odoo **selectively back to YAML** (collect mode) | [usage/collect-to-yaml.md](usage/collect-to-yaml.md) |

---

## Architecture

```
odoo-fast-report-mapper/
├── odoo_fast_report_mapper/          # Main package (single-package layout as of v1.0)
│   ├── __init__.py                  # Public API re-exports (OdooConnection, Report, …)
│   ├── __version__.py               # Version source (pyproject.toml dynamic)
│   ├── _cli.py                      # CLI entry point (Click)
│   ├── _connection.py               # OdooConnection: all mapping, testing, collecting logic
│   ├── _exceptions.py               # Custom exception classes
│   ├── _lang_utils.py               # Language normalization & multi-lang utilities
│   ├── _logging.py                  # Centralized logging configuration
│   ├── _odoo_types.py               # TypedDict definitions for Odoo RPC shapes
│   ├── _progress.py                 # tqdm-based progress wrapper
│   ├── _report.py                   # Report object & validation
│   ├── _utils.py                    # YAML collection, .env config, conversions
│   ├── _yaml_dumper.py              # Custom YAML serializer
│   └── py.typed                     # PEP 561 marker
├── tests/                           # Unit tests (353 tests)
├── yaml_examples/                   # Configuration templates
└── pyproject.toml                   # Package configuration
```

### Data Flow

```
YAML Config → Language Normalization → Report Objects → OdooConnection
  → Report Create/Update → Multi-Language Translations (via res.lang)
  → Field Mapping (eq_write_report_ids) → Calculated Fields
```

---

## Development

### Setup

```bash
git clone https://github.com/equitania/odoo-fast-report-mapper.git
cd odoo-fast-report-mapper
uv venv && source .venv/bin/activate
uv pip install -e ".[dev]"
```

### Testing & Quality

```bash
# Tests
python -m pytest tests/ -v
python -m pytest tests/ -v --cov --cov-report=term-missing

# Formatting & Linting
ruff format .
ruff check .

# Type checking
mypy odoo_fast_report_mapper/

# Build
uv build
```

### Commit Conventions

- `[ADD]` New features
- `[CHG]` Modifications
- `[FIX]` Bug fixes

Version is managed centrally in `odoo_fast_report_mapper/__version__.py` and automatically resolved by `pyproject.toml`.

---

## Troubleshooting

| Problem | Solution |
|---------|----------|
| `.env file not found` | Run `odoo-fr-mapper --init` or copy `.env.example` |
| `Missing required environment variables` | Check all `ODOO_*` vars are set in `.env` |
| `Module 'xyz' not installed` | Install required Odoo modules (esp. `eq_fr_core`) |
| `Model 'xyz' not found` | Target model doesn't exist in Odoo |
| `Invalid ODOO_WORKFLOW value` | Must be 0, 1, or 2 |
| Legacy lang keys (ger/eng) | Auto-normalized to de_DE/en_US; prefer locale codes |

---

## Resources

- **FastReport for Odoo**: https://www.ownerp.com/odoo-fastreport
- **Equitania Software GmbH**: https://www.equitania.de
- **GitHub**: https://github.com/equitania/odoo-fast-report-mapper
- **PyPI**: https://pypi.org/project/odoo-fast-report-mapper-equitania/

---

## License

AGPL-3.0 — see [LICENSE.txt](LICENSE.txt)

## Support

- GitHub Issues: https://github.com/equitania/odoo-fast-report-mapper/issues
- Email: info@equitania.de
