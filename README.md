# Odoo Fast Report Mapper

[![PyPI version](https://badge.fury.io/py/odoo-fast-report-mapper-equitania.svg)](https://badge.fury.io/py/odoo-fast-report-mapper-equitania)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: AGPL v3](https://img.shields.io/badge/License-AGPL%20v3-blue.svg)](https://www.gnu.org/licenses/agpl-3.0)

**Deutsch** | [English](#english)

## 🇩🇪 Projektbeschreibung

Eine Python-Bibliothek zur Erstellung, Verwaltung und Testung von FastReport-Einträgen in Odoo-Umgebungen. Dieses Tool unterstützt die Entwicklung und Wartung von FastReport-Dokumenten für Odoo-Module.

### Hauptfunktionen

- **Report-Mapping**: Automatische Erstellung und Aktualisierung von FastReport-Einträgen in Odoo
- **Feld-Zuordnung**: Intelligente Zuordnung von Odoo-Modellfeldern zu Berichten
- **Berechnete Felder**: Unterstützung für benutzerdefinierte Berechnungen mit Parametern
- **Test-Rendering**: Validierung der FastReport-Dokumente vor der Produktionsfreigabe
- **Mehrsprachigkeit**: Unbegrenzte Sprachen via Odoo Locale-Codes (de_DE, en_US, fr_FR, etc.) mit automatischer Erkennung installierter Sprachen
- **Interaktive YAML-Sammlung**: Bei `ODOO_COLLECT_YAML=True` werden alle verfügbaren FastReports tabellarisch angezeigt — gezielte Auswahl einzelner Reports oder Export aller
- **Mehrere Exportformate**: PDF, TXT, XML, PNG, JPG, TIFF, ODS, ODT, XLS, DOC

### Workflow-Optionen

- **Workflow 0**: Nur Mapping (Standard) - Erstellt/aktualisiert Berichte in Odoo
- **Workflow 1**: Nur Testing - Testet FastReport-Rendering
- **Workflow 2**: Mapping und Testing - Beide Operationen

---

## 🇬🇧 English

A Python library for creating, managing, and testing FastReport entries in Odoo environments. This tool supports the development and maintenance of FastReport documents for Odoo modules.

### Key Features

- **Report Mapping**: Automatic creation and updating of FastReport entries in Odoo
- **Field Mapping**: Intelligent mapping of Odoo model fields to reports
- **Calculated Fields**: Support for custom calculations with parameters
- **Test Rendering**: Validation of FastReport documents before production release
- **Multi-language**: Unlimited languages via Odoo locale codes (de_DE, en_US, fr_FR, etc.) with automatic detection of installed languages
- **Interactive YAML Collection**: With `ODOO_COLLECT_YAML=True`, all available FastReports are displayed in a table — select specific reports or export all
- **Multiple Export Formats**: PDF, TXT, XML, PNG, JPG, TIFF, ODS, ODT, XLS, DOC

### Workflow Options

- **Workflow 0**: Mapping only (default) - Creates/updates reports in Odoo
- **Workflow 1**: Testing only - Tests FastReport rendering
- **Workflow 2**: Mapping and Testing - Both operations

---

## 📦 Installation

### Systemanforderungen / System Requirements

- Python (>= 3.10)
- click (>= 8.1.3)
- odoorpc-toolbox (>= 0.7.0)
- tqdm (>= 4.65.0)
- python-dotenv (>= 0.19.0)

### Mit uv installieren (empfohlen) / Install with uv (recommended)

```bash
uv pip install odoo-fast-report-mapper-equitania
```

### Mit pip installieren / Install with pip

```bash
pip install odoo-fast-report-mapper-equitania
```

### Entwicklungsumgebung / Development Environment

```bash
# Virtuelles Environment erstellen / Create virtual environment
uv venv && source .venv/bin/activate

# Abhängigkeiten + Paket im Entwicklungsmodus installieren / Install dependencies + package in dev mode
uv pip install -e .

# Mit Development-Tools (Linting, Testing, Type-Checking) / With development tools
uv pip install -e ".[dev]"
```

### Lokales Testen & Paket erstellen / Local Testing & Building

```bash
# 1. Entwicklungsumgebung aktivieren / Activate development environment
source .venv/bin/activate  # Linux/macOS
# oder / or
.venv\Scripts\activate  # Windows

# 2. Development-Dependencies installieren / Install development dependencies
uv pip install -e ".[dev]"

# 3. Code-Formatierung prüfen / Check code formatting
ruff check .
ruff format --check .

# 4. Tests ausführen / Run tests
pytest tests/ -v

# 5. Paket lokal bauen / Build package locally
uv build

# 6. Lokales Paket installieren / Install local package
uv pip install dist/odoo-fast-report-mapper-equitania-*.tar.gz

# 7. Paket testen / Test the package
odoo-fast-report-mapper --help

# 8. Paket-Integrität prüfen (optional) / Check package integrity (optional)
twine check dist/*  # Requires: uv pip install twine
```

### Version aktualisieren & veröffentlichen / Update Version & Publish

```bash
# 1. Version in __version__.py anpassen / Update version in __version__.py
# Editiere: odoo_fast_report_mapper/__version__.py
# __version__ = "0.6.1"  # Beispiel / Example

# 2. Changelog aktualisieren / Update changelog
# Dokumentiere Änderungen / Document changes

# 3. Build & Upload zu PyPI / Build & Upload to PyPI
uv build
twine upload dist/*

# 4. Git Tag erstellen / Create git tag
git tag v0.6.1
git push origin v0.6.1
```

**Hinweis:** Die Version wird zentral in `odoo_fast_report_mapper/__version__.py` verwaltet und automatisch von `pyproject.toml` übernommen.

---

## 🚀 Verwendung / Usage

### Erste Schritte / Getting Started

**1. Erstelle eine .env Datei / Create a .env file:**

```bash
# Option A: Automatisch generieren / Auto-generate template
odoo-fr-mapper --init

# Option B: Manuell kopieren / Copy manually
cp .env.example .env

# Bearbeite .env mit deinen Zugangsdaten / Edit .env with your credentials
nano .env  # oder dein bevorzugter Editor / or your preferred editor
```

**2. Konfiguriere die Verbindung / Configure the connection:**

```bash
# .env Datei Beispiel / .env file example
ODOO_URL=https://your-odoo-instance.com
ODOO_PORT=443
ODOO_USER=admin
ODOO_PASSWORD=your_password
ODOO_DATABASE=your_database
ODOO_LANGUAGE=de_DE
ODOO_WORKFLOW=0
```

### Grundlegende Verwendung / Basic Usage

```bash
# Version anzeigen / Show version
odoo-fast-report-mapper --version
odoo-fr-mapper --version

# Hilfe anzeigen / Show help
odoo-fast-report-mapper --help

# .env Template generieren / Generate .env template
odoo-fr-mapper --init

# Interaktiver Modus / Interactive mode
odoo-fast-report-mapper

# Direkter Aufruf mit YAML-Pfad / Direct call with YAML path
odoo-fast-report-mapper --yaml_path=./reports_yaml
```

### Erweiterte Beispiele / Advanced Examples

```bash
# Odoo v16 Entwicklungsdatenbank / Odoo v16 development database
odoo-fast-report-mapper --yaml_path=$HOME/gitbase/fr-core-yaml/v16/yaml

# Odoo v18 Produktionsumgebung / Odoo v18 production environment
odoo-fast-report-mapper --yaml_path=$HOME/gitbase/fr-core-yaml/v18/yaml

# Mit spezifischer .env Datei / With specific .env file
# Option 1: --env_path zeigt auf Verzeichnis / --env_path points to directory
odoo-fast-report-mapper --yaml_path=./yaml --env_path=/path/to/config/

# Option 2: --env_path zeigt direkt auf Datei / --env_path points directly to file
odoo-fast-report-mapper --yaml_path=./yaml --env_path=/path/to/config/.env

# Option 3: .env im aktuellen Verzeichnis / .env in current directory (default)
odoo-fast-report-mapper --yaml_path=./yaml

# YAML-Sammlung mit interaktiver Auswahl / YAML collection with interactive selection
# (ODOO_COLLECT_YAML=True in .env setzen / set in .env)
odoo-fr-mapper --yaml_path=./output
#   → Tabelle mit allen FastReports / Table of all FastReports
#   → Auswahl: "1,3,5" oder "all" / Select: "1,3,5" or "all"
#   → Nur ausgewählte Reports werden exportiert / Only selected reports are exported
```

---

## ⚙️ Konfiguration / Configuration

### Server-Konfiguration / Server Configuration

**WICHTIG / IMPORTANT:** Die Verbindungskonfiguration erfolgt jetzt über eine `.env` Datei für bessere Sicherheit. / Connection configuration is now done via a `.env` file for better security.

**Erstelle eine `.env` Datei / Create a `.env` file:**

```bash
# Odoo Server Connection (Required)
ODOO_URL=https://your-odoo-instance.com
ODOO_PORT=443
ODOO_USER=admin
ODOO_PASSWORD=your_password
ODOO_DATABASE=your_database
ODOO_LANGUAGE=de_DE               # Odoo locale code (de_DE, en_US, fr_FR, etc.)
                                  # Legacy codes (ger, eng) are auto-normalized

# Optional Configuration (with defaults)
ODOO_COLLECT_YAML=False           # YAML collection mode (interactive report selection)
ODOO_DISABLE_QWEB=True            # Disable QWeb reports
ODOO_WORKFLOW=0                   # 0=Mapping, 1=Testing, 2=Both
```

**Sicherheitshinweise / Security Notes:**

- ✅ Die `.env` Datei wird automatisch von `.gitignore` ausgeschlossen
- ✅ Verwende `.env.example` als Vorlage
- ⚠️ Teile niemals deine `.env` Datei mit Credentials
- ⚠️ Nutze unterschiedliche Credentials für Produktion und Entwicklung

**Migration von YAML-Konfiguration / Migration from YAML Configuration:**

Falls du bisher `config.yaml` genutzt hast, kopiere die Werte einfach in die `.env` Datei:

```bash
# Alt (DEPRECATED): --server_path=./connection_yaml
# Neu: .env Datei im aktuellen Verzeichnis
```

### Report-Konfiguration / Report Configuration

Erstelle YAML-Dateien im `reports_yaml` Ordner:

```yaml
# Benennung / Naming (Odoo locale codes)
name:
  de_DE: Deutscher_Bericht
  en_US: English_Report
  fr_FR: Rapport_Francais              # Additional languages (optional)
report_name: eq_fr_sales_report
report_model: sale.order

# Attachment - einfacher String oder sprachabhängig per Dict
# Simple string or company-language-aware dict
attachment: ('Sales_Report.pdf')
# Oder / Or (resolved per company language with fallback chain):
# attachment:
#   de_DE: "('Angebot-' + (object.name or '').replace('/','') + '.pdf')"
#   en_US: "('Quotation-' + (object.name or '').replace('/','') + '.pdf')"

print_report_name: ('Sales Report')

# Eigenschaften / Properties
report_type: fast_report
eq_export_type: pdf
eq_ignore_images: true
eq_handling_html_fields: standard
eq_multiprint: create_zip
multi: false
eq_print_button: false
attachment_use: true

# Firmen-IDs / Company IDs (optional)
company_id:
  - 1
  - 2

# Abhängigkeiten / Dependencies
dependencies:
  - sale
  - account

# Erforderliche Felder / Required Fields
report_fields:
  sale.order:
    - id
    - name
    - partner_id
    - amount_total
    - state
  sale.order.line:
    - id
    - product_id
    - quantity
    - price_unit
    - price_total

# Berechnete Felder / Calculated Fields
calculated_fields:
  payment_text:
    eq_get_payment_terms:
      - partner_id.lang
      - currency_id
```

---

## 🏗️ Architektur / Architecture

### Komponenten / Components

1. **CLI Interface** (`odoo_fast_report_mapper.py`): Befehlszeileninterface mit Click
2. **Connection Manager** (`odoo_connection.py`): odoorpc-toolbox-Integration und Verbindungsmanagement
3. **Report Processing** (`eq_report.py`): Report-Objekte und Validierung
4. **Language Utilities** (`lang_utils.py`): Sprachnormalisierung, Multi-Language-Logik, Attachment-Auflösung
5. **Utilities** (`eq_utils.py`): YAML-Verarbeitung und Hilfsfunktionen
6. **Logging** (`logging_config.py`): Zentrales Logging mit farbiger Konsolenausgabe und Rotation
7. **Progress Tracking** (`progress.py`): tqdm-basierte Fortschrittsanzeige für Mapping-Operationen

### Datenfluss / Data Flow

```
YAML-Konfiguration → Sprachnormalisierung → Report-Objekte → Odoo-Verbindung
    → FastReport-Erstellung → Multi-Language Translations (via res.lang)
```

---

## 🧪 Testing

### Unit Tests ausführen / Run Unit Tests

```bash
# Alle Tests / All tests
python -m pytest tests/

# Spezifische Test-Datei / Specific test file
python -m pytest tests/utils_test.py

# Mit Verbose-Ausgabe / With verbose output
python -m pytest tests/ -v

# Mit Coverage / With coverage
python -m pytest tests/ --cov=odoo_fast_report_mapper
```

### Manuelle Tests / Manual Testing

```bash
# .env-basierte Verbindung testen / Test .env-based connection
python -c "from odoo_fast_report_mapper import eq_utils; conn = eq_utils.create_connection_from_env(); print(conn)"

# YAML-Parsing testen / Test YAML parsing
python -c "from odoo_report_helper import utils; print(utils.parse_yaml('yaml_examples/reports_yaml/template.yaml'))"

# CLI-Hilfe prüfen / Check CLI help
odoo-fr-mapper --help
```

---

## 🛠️ Entwicklung / Development

### Paket erstellen / Build Package

```bash
# Mit UV (empfohlen / recommended)
uv build

# Paket prüfen (optional) / Check package (optional)
twine check dist/*  # Requires: uv pip install twine
```

### Code-Qualität / Code Quality

```bash
# Formatierung / Formatting
ruff format .

# Linting
ruff check .

# Typ-Überprüfung / Type checking
mypy odoo_fast_report_mapper/ odoo_report_helper/
```

---

## 🔧 Troubleshooting

### Häufige Probleme / Common Issues

#### Verbindungsfehler / Connection Errors
```bash
# SSL-Zertifikat-Probleme / SSL certificate issues
export PYTHONHTTPSVERIFY=0

# Proxy-Konfiguration / Proxy configuration
export HTTP_PROXY=http://proxy.company.com:8080
export HTTPS_PROXY=https://proxy.company.com:8080
```

#### Modul-Abhängigkeiten / Module Dependencies
```bash
# Fehlende Module prüfen / Check missing modules
odoo-fr-mapper --yaml_path=./reports 2>&1 | grep "NOT INSTALLED"
```

#### YAML-Syntaxfehler / YAML Syntax Errors
```bash
# YAML-Syntax validieren / Validate YAML syntax
python -c "import yaml; yaml.safe_load(open('your_file.yaml'))"
```

---

## 📚 Weitere Ressourcen / Additional Resources

- **FastReport für Odoo**: https://www.ownerp.com/odoo-fastreport
- **Equitania Software GmbH**: https://www.equitania.de
- **GitHub Repository**: https://github.com/equitania/odoo-fast-report-mapper
- **PyPI Package**: https://pypi.org/project/odoo-fast-report-mapper-equitania/

---

## 🤝 Mitwirkung / Contributing

Beiträge sind willkommen! Bitte lese die Entwicklungsrichtlinien und erstelle einen Pull Request.

Contributions are welcome! Please read the development guidelines and create a pull request.

### Entwicklungsrichtlinien / Development Guidelines

1. **Code Style**: Befolge PEP 8 / Follow PEP 8
2. **Tests**: Füge Tests für neue Funktionen hinzu / Add tests for new features
3. **Dokumentation**: Aktualisiere die Dokumentation / Update documentation
4. **Commit-Nachrichten**: Verwende aussagekräftige Commit-Nachrichten / Use meaningful commit messages

---

## 📄 Lizenz / License

Dieses Projekt steht unter der **AGPLv3**-Lizenz. Weitere Details findest du in der [LICENSE.txt](LICENSE.txt) Datei.

This project is licensed under the **AGPLv3** license. See the [LICENSE.txt](LICENSE.txt) file for details.

---

## 📞 Support

Bei Fragen oder Problemen:
- GitHub Issues: https://github.com/equitania/odoo-fast-report-mapper/issues
- E-Mail: info@equitania.de

For questions or issues:
- GitHub Issues: https://github.com/equitania/odoo-fast-report-mapper/issues
- Email: info@equitania.de  
