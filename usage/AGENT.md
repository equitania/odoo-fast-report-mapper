<!--
  Capability Card — generated/maintained via the `cli-capability-card` skill.
  Audience: an LLM/agent that wants to USE this tool. Keep it dense and current.
  Regenerate the command table with scripts/introspect_cli.py after CLI changes.
-->
# odoo-fast-report-mapper — Agent Capability Card

> Map, test, and collect FastReport report definitions in an Odoo instance from local YAML files, driven by an `.env` connection config. Single-command CLI; behaviour is selected by flags + env vars, not subcommands.

- **Invoke:** `odoo-fr-mapper [OPTIONS]` (alias: `odoo-fast-report-mapper`)
- **Install:** `uv pip install -e .` (from repo) · or `uv pip install odoo-fast-report-mapper-equitania`
- **Version:** 1.0.2 · Python `>=3.10`
- **Framework:** Click · **Human docs:** `README.md`, `MIGRATION.md`, `yaml_examples/`

## Capabilities at a glance
- Create/update `ir.actions.report` FastReport records in Odoo from a folder of YAML report definitions (workflow 0, default).
- Test FastReport rendering of mapped reports via the Odoo API without re-mapping (workflow 1).
- Do both — map then test sequentially (workflow 2).
- Collect/export existing FastReport entries FROM Odoo back into YAML files (reverse direction, `ODOO_COLLECT_YAML=True`).
- Interactively pick which YAML files to process from a table, instead of processing the whole folder (`--select`).
- Authenticate with either classic password or an Odoo API key (>=14), with a pre-login server-version check.
- Bootstrap a ready-to-edit `.env` template into the current directory (`--init`).
- Bilingual (DE/EN) report naming and locale-aware language handling (`ODOO_LANGUAGE`).

## Command reference

| Command | Purpose | Args / Flags |
|---|---|---|
| `odoo-fr-mapper` | Odoo FastReport Mapper - Map, test and manage FastReport entries in Odoo. | `--version`, `--init`, `--yaml_path TEXT`, `--env_path TEXT`, `--select` |

Notation: `[ARG]` optional positional · `ARG` required positional · `a|b` choice · `--flag` boolean.

Flag detail:
- `--version` — print version and exit.
- `--init` — write an `.env` template into the current directory and exit (no connection made).
- `--yaml_path TEXT` — folder containing YAML report definition files. Required for mapping/testing.
- `--env_path TEXT` — path to an `.env` file **or** a directory containing one. Default: `.env` in CWD. Accepts a dir (`./connections/` → `./connections/.env`), an absolute file, or a relative file.
- `--select` — show an interactive table of the YAML files and prompt for indices (`1,3,5`) or `all`.

## Recipes

### First-time setup
```bash
odoo-fr-mapper --init
# edit the generated .env: ODOO_URL, ODOO_PORT, ODOO_USER, ODOO_DATABASE,
# ODOO_LANGUAGE, and ONE of ODOO_PASSWORD / ODOO_API_KEY
```
Writes `.env` to the CWD and exits. No network call.

### Map all reports in a folder (default workflow)
```bash
odoo-fr-mapper --yaml_path=./reports_yaml
```
With `ODOO_WORKFLOW=0` (default), creates/updates `ir.actions.report` records for every YAML in the folder. Reads connection from `./.env`.

### Map only selected reports interactively
```bash
odoo-fr-mapper --yaml_path=./reports_yaml --select
```
Prints a table (filename · report name · model); enter `1,3,5` or `all`.

### Test rendering only (no mapping)
```bash
# in .env: ODOO_WORKFLOW=1
odoo-fr-mapper --yaml_path=./reports_yaml
```
Calls the FastReport API to render each mapped report; reports failures. Set `ODOO_WORKFLOW=2` to map AND test in one run.

### Use a connection profile from another directory
```bash
odoo-fr-mapper --env_path=./connections/prod.env --yaml_path=./reports_yaml
# or a directory holding a .env:
odoo-fr-mapper --env_path=./connections/ --yaml_path=./reports_yaml
```
Lets one YAML folder be mapped against different Odoo targets.

### Export existing reports FROM Odoo to YAML
```bash
# in .env: ODOO_COLLECT_YAML=True
odoo-fr-mapper --yaml_path=./reports_yaml
```
Shows an interactive selection of Odoo-side FastReport entries, then writes them as YAML into `--yaml_path`.

## Guardrails & gotchas
- **Mutating:** mapping (`ODOO_WORKFLOW` 0/2) creates/overwrites `ir.actions.report` records in the live Odoo DB. There is no `--dry-run`; point it at a test DB first.
- **`.env` is mandatory for any connection.** Without `--env_path`, it looks for `.env` in the CWD. If absent there, it auto-discovers upward through parent directories — the loaded path is logged as a warning, so check which `.env` was actually used before trusting the target (risk of hitting a parent project's prod credentials).
- **Auth:** set exactly one of `ODOO_PASSWORD` / `ODOO_API_KEY`. If both are set, `ODOO_API_KEY` wins (with a warning). API-key auth is rejected pre-login on Odoo < 14.
- **Transport:** an `https`/`jsonrpc+ssl` URL verifies SSL (Python default context). Plain HTTP triggers an explicit warning.
- **Interactive prompts:** `--select` and collect-mode (`ODOO_COLLECT_YAML=True`) block on stdin. Omit `--select` and keep `ODOO_COLLECT_YAML=False` for unattended runs.
- **`ODOO_DISABLE_QWEB`** defaults to `True` — mapping disables the corresponding QWeb reports. Set `False` to keep them.
- **Credentials in YAML are deprecated.** Put connection secrets in `.env`, never in the report YAML files.

## Machine-readable outputs
None. The tool communicates via human-readable logs and interactive tables; there is no `--json`/structured-output mode. Parse exit code (`0` success) and log lines, or inspect the resulting Odoo records / collected YAML files directly.

## Deeper docs
- `README.md` — full prose usage, bilingual.
- `MIGRATION.md` — migrating from the legacy YAML-connection format to `.env`.
- `yaml_examples/reports_yaml/` — report-definition YAML templates (fields, calculated fields, dependencies).
- Run `odoo-fr-mapper --help` for the embedded `.env` reference.
