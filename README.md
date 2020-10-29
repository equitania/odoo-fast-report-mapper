Odoo-fast-report-mapper
============
This is a simple python library to create FastReport entries in an Odoo environment.

## Installation

### odoo-fast-report-mapper requires:

- Python (>= 3.6)
- click (>= 7.1.2)
- OdooRPC (>= 0.7.0)
- PyYaml (>= 5.3.1)

Use the package manager [pip](https://pip.pypa.io/en/stable/) to install odoo-fast-report-mapper.

```bash
pip install odoo-fast-report-mapper
```

---

## Usage


```python
import odoo_fast_report_mapper
  
odoo_fast_report_mapper.welcome()  # Display welcome message
odoo_fast_report_mapper.start_odoo_fast_report_mapper()  # Start click program
```

```bash
Options:
  --server_path TEXT  Server configuration folder
  --report_path TEXT  Reports folder
  --help              Show this message and exit.
```
---

## Options
>You can check out the full license [here](https://github.com/IgorAntun/node-chat/blob/master/LICENSE)

This project is licensed under the terms of the **MIT** license.