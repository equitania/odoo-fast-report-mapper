# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**odoo-fast-report-mapper** is a Python CLI tool for creating and managing FastReport entries in Odoo environments. It is part of the PyPi-Projects collection within the Equitania Software GmbH ecosystem and supports the FastReport module for Odoo (https://www.ownerp.com/odoo-fastreport).

## Core Architecture

### Main Components

1. **CLI Interface** (`odoo_fast_report_mapper/odoo_fast_report_mapper.py`):
   - Entry point using Click framework
   - Handles command-line arguments for server and YAML paths
   - Orchestrates the mapping workflow

2. **Connection Management** (`odoo_report_helper/odoo_connection.py`):
   - `OdooConnection` class for OdooRPC integration
   - Handles login, report mapping, and dependency validation
   - Manages calculated fields and report testing

3. **Report Processing** (`odoo_fast_report_mapper/eq_report.py`):
   - Report object definitions and validation
   - YAML-based report configuration processing

4. **Utility Functions** (`odoo_fast_report_mapper/eq_utils.py`):
   - YAML file collection and parsing
   - Connection configuration management

### Configuration System

The tool uses a two-folder configuration approach:

1. **Server Configuration** (`connection_yaml/`):
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
# Interactive mode (prompts for paths)
odoo-fast-report-mapper

# Direct execution with paths
odoo-fast-report-mapper --server_path=./connection_yaml --yaml_path=./reports_yaml

# Development examples
odoo-fast-report-mapper --server_path=$HOME/gitbase/dev-helpers/yaml/v16-yaml-con --yaml_path=$HOME/gitbase/fr-core-yaml/v16/yaml
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
├── odoo_fast_report_mapper/          # Main package
│   ├── odoo_fast_report_mapper.py   # CLI entry point
│   ├── eq_odoo_connection.py        # Odoo connection wrapper
│   ├── eq_report.py                 # Report objects
│   ├── eq_utils.py                  # Utility functions
│   └── MyDumper.py                  # YAML dumper
├── odoo_report_helper/              # Helper package
│   ├── odoo_connection.py           # Core connection class
│   ├── report.py                    # Report processing
│   ├── utils.py                     # Utility functions
│   └── exceptions.py                # Custom exceptions
├── yaml_examples/                   # Configuration templates
│   ├── connection_yaml/             # Server config examples
│   └── reports_yaml/                # Report config examples
├── tests/                           # Unit tests
├── helper_scripts/                  # Development tools
└── setup.py                        # Package configuration
```

## Dependencies

### Core Dependencies
- **OdooRPC** (>=0.10.1): Odoo XML-RPC client
- **Click** (>=8.1.3): Command-line interface framework
- **PyYAML** (>=5.4.1): YAML parsing and processing

### Python Requirements
- Python >= 3.8
- UTF-8 encoding support for international characters

## Configuration Examples

### Server Configuration (config.yaml)
```yaml
Server:
  url: https://odoo.example.com
  port: 443
  user: admin
  password: your_password
  database: your_db
  language: ger                  # ger or eng
  collect_yaml: False            # Collection mode
  disable_qweb: True             # Disable QWeb reports
  workflow: 0                    # 0=mapping, 1=testing, 2=both
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