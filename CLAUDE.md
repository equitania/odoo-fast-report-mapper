# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**odoo-fast-report-mapper** is a Python CLI tool for creating and managing FastReport entries in Odoo environments. It is part of the PyPi-Projects collection within the Equitania Software GmbH ecosystem and supports the FastReport module for Odoo (https://www.ownerp.com/odoo-fastreport).

## Core Architecture

### Main Components

1. **CLI Interface** (`odoo_fast_report_mapper/_cli.py`):
   - Entry point using Click framework
   - Handles command-line arguments for server and YAML paths
   - Orchestrates the mapping workflow

2. **Connection Management** (`odoo_fast_report_mapper/_connection.py`):
   - `OdooConnection` — single merged class (no inheritance hierarchy as of v1.0)
   - Handles login, report mapping, testing, collecting, dependency validation, and calculated fields

3. **Report Processing** (`odoo_fast_report_mapper/_report.py`):
   - `Report` object definitions and validation
   - YAML-based report configuration processing

4. **Utility Functions** (`odoo_fast_report_mapper/_utils.py`):
   - YAML file collection and parsing
   - `.env`-based connection configuration management (`create_connection_from_env`)

### Configuration System

The tool uses `.env`-based configuration:

1. **Server Configuration** (`.env` file):
   - Server connection details (URL, port, credentials)
   - Database and language settings
   - Workflow configuration (mapping, testing, or both)

2. **Report Configuration** (`reports_yaml/`):
   - Report definitions with bilingual naming
   - Field mappings for Odoo models
   - Calculated fields and dependencies

## Development Commands

### Environment Setup
```bash
# Create and activate virtual environment
uv venv && venv+

# Install dependencies
uvpip

# Install package in editable mode
uv pip install -e .
```

### Running the Tool
```bash
# Generate .env template (first-time setup)
odoo-fr-mapper --init

# Map all reports (connection from .env in current directory)
odoo-fast-report-mapper --yaml_path=./reports_yaml

# Map selected reports interactively
odoo-fr-mapper --yaml_path=./reports_yaml --select

# Custom .env location
odoo-fr-mapper --env_path=./connections/ --yaml_path=./yaml/
```

### Testing
```bash
# Run unit tests
python -m pytest tests/

# Run specific test file
python -m pytest tests/utils_test.py

# Run with verbose output
python -m pytest tests/ -v
```

### Package Management
```bash
# Build package
uv build

# Check package contents
python setup.py check

# Install locally built package
uv pip install dist/odoo-fast-report-mapper-equitania-*.tar.gz
```

## Key Features

### Workflow Types
- **Workflow 0**: Only mapping (default) - Creates/updates reports in Odoo
- **Workflow 1**: Only testing - Tests FastReport rendering
- **Workflow 2**: Mapping and testing - Both operations

### Report Configuration
- **Bilingual Support**: German and English report names
- **Field Mapping**: Automatic field-to-report association
- **Calculated Fields**: Custom field calculations with parameters
- **Dependencies**: Module dependency validation
- **Multi-company**: Company-specific report filtering

### Export Types
Supports multiple FastReport export formats:
- PDF (default), TXT, XML, PNG, JPG, TIFF, ODS, ODT, XLS, DOC

## File Structure

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
├── tests/                           # Unit tests
├── yaml_examples/                   # Configuration templates
│   └── reports_yaml/                # Report config examples
└── pyproject.toml                   # Package configuration & build system
```

## Dependencies

### Core Dependencies
- **odoorpc-toolbox** (>=0.7.0): Odoo RPC client with internalized OdooRPC
- **Click** (>=8.1.3): Command-line interface framework
- **PyYAML** (>=5.4.1): YAML parsing and processing

### Python Requirements
- Python >= 3.12
- UTF-8 encoding support for international characters

## Configuration Examples

### Server Configuration (.env)
```bash
# Odoo Server Connection
ODOO_URL=https://odoo.example.com
ODOO_PORT=443
ODOO_USER=admin
ODOO_DATABASE=your_db
ODOO_LANGUAGE=de_DE            # Odoo locale code (legacy: ger, eng)

# Authentication — set ONE (ODOO_API_KEY takes precedence, Odoo >= 14)
ODOO_PASSWORD=your_password
# ODOO_API_KEY=your_api_key

# Workflow: 0=mapping (default), 1=testing, 2=both
ODOO_WORKFLOW=0
```

### Report Configuration (template.yaml)
```yaml
name:
  ger: Deutscher_Report
  eng: English_Report
report_name: eq_fr_report_name
report_model: sale.order
report_type: fast_report
eq_export_type: pdf
dependencies:
  - sale
  - account
report_fields:
  sale.order:
    - id
    - name
    - partner_id
    - amount_total
calculated_fields:
  field_name:
    function_name:
      - parameter1
      - parameter2
```

## Error Handling

The tool includes comprehensive error handling for:
- Connection failures (network, authentication)
- Missing dependencies in Odoo
- Invalid YAML configurations
- Report mapping conflicts

## Development Notes

### Code Style
- UTF-8 encoding for all files
- German/English bilingual support
- AGPLv3 license compliance
- Click framework for CLI consistency

### Testing Strategy
- Unit tests for utility functions
- Connection testing with mock servers
- YAML parsing validation
- Report mapping verification

### Version Management
- Semantic versioning in setup.py
- Equitania Software GmbH copyright headers
- GitHub repository synchronization