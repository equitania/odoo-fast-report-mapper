# Odoo Fast Report Mapper

[![PyPI version](https://badge.fury.io/py/odoo-fast-report-mapper-equitania.svg)](https://badge.fury.io/py/odoo-fast-report-mapper-equitania)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: AGPL v3](https://img.shields.io/badge/License-AGPL%20v3-blue.svg)](https://www.gnu.org/licenses/agpl-3.0)

**Deutsch** | [English](#english)

## 🇩🇪 Projektbeschreibung

Eine Python-Bibliothek zur Erstellung, Verwaltung und Testung von FastReport-Einträgen in Odoo-Umgebungen. Dieses Tool unterstützt die Entwicklung und Wartung von FastReport-Dokumenten für Odoo-Module.

### Hauptfunktionen

- **Report-Mapping**: Automatische Erstellung und Aktualisierung von FastReport-Einträgen in Odoo
- **Feld-Zuordnung**: Intelligente Zuordnung von Odoo-Modellfeldern zu Berichten
- **Berechnete Felder**: Unterstützung für benutzerdefinierte Berechnungen mit Parametern
- **Test-Rendering**: Validierung der FastReport-Dokumente vor der Produktionsfreigabe
- **Mehrsprachigkeit**: Deutsche und englische Berichtsnamen
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
- **Multi-language**: German and English report names
- **Multiple Export Formats**: PDF, TXT, XML, PNG, JPG, TIFF, ODS, ODT, XLS, DOC

### Workflow Options

- **Workflow 0**: Mapping only (default) - Creates/updates reports in Odoo
- **Workflow 1**: Testing only - Tests FastReport rendering
- **Workflow 2**: Mapping and Testing - Both operations

---

## 📦 Installation

### Systemanforderungen / System Requirements

- Python (>= 3.8)
- click (>= 8.1.3)
- OdooRPC (>= 0.10.1)
- PyYAML (>= 5.4.1)

### Mit pip installieren / Install with pip

```bash
pip install odoo-fast-report-mapper-equitania
```

### Entwicklungsumgebung / Development Environment

```bash
# Virtuelles Environment erstellen / Create virtual environment
uv venv && source .venv/bin/activate

# oder mit traditionellem pip / or with traditional pip
python -m venv .venv && source .venv/bin/activate

# Abhängigkeiten installieren / Install dependencies
pip install -r requirements.txt

# Paket im Entwicklungsmodus installieren / Install package in development mode
pip install -e .
```

### Lokales Testen & Paket erstellen / Local Testing & Building

```bash
# 1. Entwicklungsumgebung aktivieren / Activate development environment
source .venv/bin/activate  # Linux/macOS
# oder / or
.venv\Scripts\activate  # Windows

# 2. Development-Dependencies installieren / Install development dependencies
pip install -r requirements-dev.txt

# 3. Code-Formatierung prüfen / Check code formatting
black odoo_fast_report_mapper/ odoo_report_helper/ --check
flake8 odoo_fast_report_mapper/ odoo_report_helper/

# 4. Tests ausführen / Run tests
pytest tests/ -v

# 5. Paket lokal bauen / Build package locally
uv build
# oder mit setuptools / or with setuptools
python setup.py sdist bdist_wheel

# 6. Lokales Paket installieren / Install local package
pip install dist/odoo-fast-report-mapper-equitania-*.tar.gz

# 7. Paket testen / Test the package
odoo-fast-report-mapper --help

# 8. Paket-Integrität prüfen / Check package integrity
twine check dist/*
```

### Version aktualisieren & veröffentlichen / Update Version & Publish

```bash
# 1. Version in setup.py anpassen / Update version in setup.py
# version="0.1.25"  # Beispiel / Example

# 2. Changelog aktualisieren / Update changelog
# Dokumentiere Änderungen / Document changes

# 3. Build & Upload zu PyPI / Build & Upload to PyPI
uv build
twine upload dist/*

# 4. Git Tag erstellen / Create git tag
git tag v0.1.25
git push origin v0.1.25
```

---

## 🚀 Verwendung / Usage

### Grundlegende Verwendung / Basic Usage

```bash
# Interaktiver Modus / Interactive mode
odoo-fast-report-mapper

# Direkter Aufruf mit Parametern / Direct call with parameters
odoo-fast-report-mapper --server_path=./connection_yaml --yaml_path=./reports_yaml

# Hilfe anzeigen / Show help
odoo-fast-report-mapper --help
```

### Erweiterte Beispiele / Advanced Examples

```bash
# Odoo v16 Entwicklungsdatenbank / Odoo v16 development database
odoo-fast-report-mapper \
  --server_path=$HOME/gitbase/dev-helpers/yaml/v16-yaml-con \
  --yaml_path=$HOME/gitbase/fr-core-yaml/v16/yaml

# Odoo v18 Produktionsumgebung / Odoo v18 production environment
odoo-fast-report-mapper \
  --server_path=$HOME/gitbase/dev-helpers/yaml/v18-yaml-con \
  --yaml_path=$HOME/gitbase/fr-core-yaml/v18/yaml
```

---

## ⚙️ Konfiguration / Configuration

### Server-Konfiguration / Server Configuration

Erstelle eine `config.yaml` Datei im `connection_yaml` Ordner:

```yaml
Server:
  url: https://your-odoo-instance.com
  port: 443
  user: admin
  password: your_password
  database: your_database
  language: ger                    # ger oder eng / ger or eng
  collect_yaml: False              # YAML-Sammelmodus / YAML collection mode
  disable_qweb: True               # QWeb-Berichte deaktivieren / Disable QWeb reports
  workflow: 0                      # 0=Mapping, 1=Testing, 2=Beides / 0=Mapping, 1=Testing, 2=Both
```

### Report-Konfiguration / Report Configuration

Erstelle YAML-Dateien im `reports_yaml` Ordner:

```yaml
# Benennung / Naming
name:
  ger: Deutscher_Bericht
  eng: English_Report
report_name: eq_fr_sales_report
report_model: sale.order
attachment: ('Sales_Report.pdf')
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
2. **Connection Manager** (`odoo_connection.py`): OdooRPC-Integration und Verbindungsmanagement
3. **Report Processing** (`eq_report.py`): Report-Objekte und Validierung
4. **Utilities** (`eq_utils.py`): YAML-Verarbeitung und Hilfsfunktionen

### Datenfluss / Data Flow

```
YAML-Konfiguration → Report-Objekte → Odoo-Verbindung → FastReport-Erstellung
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
# Verbindung testen / Test connection
python -c "from odoo_report_helper import utils; print(utils.prepare_connection('https://demo.odoo.com', 443))"

# YAML-Parsing testen / Test YAML parsing
python -c "from odoo_report_helper import utils; print(utils.parse_yaml('yaml_examples/reports_yaml/template.yaml'))"
```

---

## 🛠️ Entwicklung / Development

### Paket erstellen / Build Package

```bash
# Mit setuptools / With setuptools
python setup.py sdist bdist_wheel

# Mit UV (empfohlen / recommended)
uv build

# Paket prüfen / Check package
twine check dist/*
```

### Code-Qualität / Code Quality

```bash
# Formatierung / Formatting
black odoo_fast_report_mapper/ odoo_report_helper/

# Linting
flake8 odoo_fast_report_mapper/ odoo_report_helper/

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
odoo-fast-report-mapper --server_path=./config --yaml_path=./reports 2>&1 | grep "NOT INSTALLED"
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
