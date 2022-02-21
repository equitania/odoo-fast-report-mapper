# Odoo-fast-report-mapper
====================================================================================    
This is a simple python library to create/collect FastReport entries in/from an Odoo environment.  Also to test the rendering of FastReport documents.
It is a helper tool for our Odoo modules. https://www.myodoo.de/myodoo-fast-report.

## Installation

### odoo-fast-report-mapper requires:

- Python (>= 3.6)
- click (>= 7.1.2)
- OdooRPC (>= 0.8.0)
- PyYaml (>= 3.12)

Use the package manager [pip](https://pip.pypa.io/en/stable/) to install odoo-fast-report-mapper.

```bash
pip install odoo-fast-report-mapper-equitania
```

---

## Usage

```bash
$ odoo-fr-mapper --help
usage: odoo-fr-mapper [--help] [--server_path] [--yaml_path]
```

```bash
Optional arguments:
  --server_path     Server configuration folder
  --yaml_path       Yaml folder
  --help            Show this message and exit.
```

---

## example

```bash
odoo-fr-mapper --server_path=./connection_yaml --yaml_path=./reports_yaml 
# v12 basis dbs
odoo-fr-mapper --server_path=$HOME/gitbase/dev-helpers/yaml/v12-yaml-con --yaml_path=$HOME/gitbase/fr-core-yaml/v12/yaml
# v13 basis dbs
odoo-fr-mapper --server_path=$HOME/gitbase/dev-helpers/yaml/v13-yaml-con --yaml_path=$HOME/gitbase/fr-core-yaml/v13/yaml
```

## Options

> You can check out the full license [here](https://github.com/equitania/odoo-fast-report-mapper/blob/master/LICENSE.txt)

This project is licensed under the terms of the **AGPLv3** license.
