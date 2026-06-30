# Benutzerhandbuch · User Guide — Odoo Fast Report Mapper

> **Sprache / Language**: [DE](#deutsch) · [EN](#english)

Dieses Verzeichnis bündelt die einsatzzweck-orientierten Anleitungen für den Fast Report Mapper.
Die Kurzfassung steht in der [README](../README.md); hier findest du die Schritt-für-Schritt-Details.

This directory collects the task-oriented guides for the Fast Report Mapper. The short version
lives in the [README](../README.md); the step-by-step details are here.

---

## Deutsch

### Einsatzzwecke

| Anleitung | Wofür |
|-----------|-------|
| [mapping-reports.md](mapping-reports.md) | Berichte aus YAML in Odoo **registrieren/aktualisieren** (Mapping), Verbindungsbestätigung, Fehlerverhalten, QWeb-Berichte ausblenden |
| [multilanguage.md](multilanguage.md) | Berichtsnamen **mehrsprachig** pflegen – automatisch für alle aktiven Odoo-Sprachen |
| [selective-registration.md](selective-registration.md) | Mit `--select` gezielt **einzelne Berichte** registrieren |
| [collect-to-yaml.md](collect-to-yaml.md) | In Odoo angepasste Berichte **selektiv zurück nach YAML** sichern (Collect-Modus) |

### Schnelleinstieg

```bash
odoo-fr-mapper --init                          # .env-Vorlage anlegen
odoo-fr-mapper --yaml_path=./reports_yaml       # alle Berichte registrieren
odoo-fr-mapper --yaml_path=./reports_yaml --select   # nur ausgewählte
```

> Für KI-Agenten: Eine dichte, maschinenlesbare Kommando-Referenz liegt in
> [AGENT.md](AGENT.md) (englisch).

---

## English

### Use cases

| Guide | Purpose |
|-------|---------|
| [mapping-reports.md](mapping-reports.md) | **Register/update** reports from YAML in Odoo (mapping), connection confirmation, failure handling, hiding QWeb reports |
| [multilanguage.md](multilanguage.md) | Maintain report names **multilingually** – automatically for all active Odoo languages |
| [selective-registration.md](selective-registration.md) | Register **individual reports** selectively with `--select` |
| [collect-to-yaml.md](collect-to-yaml.md) | Save reports adjusted in Odoo **selectively back to YAML** (collect mode) |

### Quick start

```bash
odoo-fr-mapper --init                          # create .env template
odoo-fr-mapper --yaml_path=./reports_yaml       # register all reports
odoo-fr-mapper --yaml_path=./reports_yaml --select   # selected only
```

> For AI agents: a dense, machine-readable command reference lives in
> [AGENT.md](AGENT.md).
