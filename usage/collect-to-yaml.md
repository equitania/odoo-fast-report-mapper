# Bestehende Reports zurück nach YAML sichern (Collect) · Exporting Existing Reports back to YAML (Collect)

> **Sprache / Language**: [DE](#deutsch) · [EN](#english)

---

## Deutsch

### Worum es geht

Berichte, die bereits in Odoo registriert und dort **in der Oberfläche grafisch weiter
angepasst** wurden (zusätzliche Felder, geänderte Zuordnungen, berechnete Werte), lassen sich
mit dem Collect-Modus **zurück in YAML-Dateien sichern**. So überführst du den am System
gewachsenen Stand wieder in versionierbare, weitergebbare Konfigurationsdateien – ideal vor
einer Migration, für die Übergabe an ein anderes System oder als Sicherung.

Die Auswahl ist **selektiv**: Du sicherst nur die Berichte, die du wirklich brauchst.

### Schritt für Schritt

Aktiviere den Modus in der `.env` und gib mit `--yaml_path` das **Zielverzeichnis** an, in das
die Dateien geschrieben werden:

```bash
# in .env:
ODOO_COLLECT_YAML=True

odoo-fr-mapper --yaml_path=./export
```

1. Nach der Anmeldung durchsucht das Tool Odoo nach allen registrierten FastReport-Belegen und
   zeigt sie als Auswahltabelle:
   ```
   Found 3 FastReport(s):

     #  Report Name                  Model           Company
   ---  ---------------------------  --------------  ----------------
     1  account.report_invoice_de    account.move    Musterfirma GmbH
     2  stock.delivery_report        stock.picking   Musterfirma GmbH
     3  sale.report_order            sale.order      Musterfirma GmbH
   ```
   Gibt es keine FastReports, endet der Lauf mit `No FastReport entries found in database.`

2. An der Eingabeaufforderung wählst du wie gewohnt aus:
   ```
   Select reports (e.g. 1,3,5 or 'all') [all]:
   ```
   `all`/leer = alle, `1,3` = einzelne (1-basiert, gleiche Logik wie bei `--select`).

3. Für jede ausgewählte Position werden die zugeordneten Felder, berechneten Werte und die
   benötigten Module/Abhängigkeiten eingesammelt (mit Fortschrittsanzeige pro Unternehmen) und
   in je eine YAML-Datei geschrieben.

### Ergebnis: die exportierten Dateien

- Geschrieben werden sie in das mit `--yaml_path` angegebene Verzeichnis.
- Der Dateiname enthält einen Zeitstempel, damit nichts überschrieben wird:
  ```
  <report_name>_MM_DD_YYYY_HH_MM_SS.yaml
  z. B.  account.report_invoice_de_06_30_2026_14_23_11.yaml
  ```
- Enthalten sind Felder, vorhandene Sprachfassungen und berechnete Werte – also alles, was den
  Bericht ausmacht, in genau der Form, die der Mapper beim erneuten Registrieren wieder
  einlesen kann.

### Typischer Kreislauf

1. Berichte per Mapping ausrollen → 2. in Odoo grafisch feinjustieren → 3. mit Collect zurück
nach YAML sichern → 4. die gesicherten Dateien versionieren und auf das nächste System ausrollen.

### Mehr dazu

- Wieder einspielen: [mapping-reports.md](mapping-reports.md)
- Gezielt einzelne Berichte: [selective-registration.md](selective-registration.md)

---

## English

### What it does

Reports that are already registered in Odoo and have been **further adjusted graphically in the
UI** (extra fields, changed mappings, calculated values) can be **saved back into YAML files**
with collect mode. This turns the grown, system-side state back into versionable, shareable
configuration files – ideal before a migration, for handover to another system, or as a backup.

The selection is **selective**: you save only the reports you actually need.

### Step by step

Enable the mode in `.env` and use `--yaml_path` to specify the **target directory** the files
are written to:

```bash
# in .env:
ODOO_COLLECT_YAML=True

odoo-fr-mapper --yaml_path=./export
```

1. After login the tool scans Odoo for all registered FastReport documents and shows them as a
   selection table:
   ```
   Found 3 FastReport(s):

     #  Report Name                  Model           Company
   ---  ---------------------------  --------------  ----------------
     1  account.report_invoice_de    account.move    Musterfirma GmbH
     2  stock.delivery_report        stock.picking   Musterfirma GmbH
     3  sale.report_order            sale.order      Musterfirma GmbH
   ```
   If there are no FastReports, the run ends with `No FastReport entries found in database.`

2. At the prompt, make your selection as usual:
   ```
   Select reports (e.g. 1,3,5 or 'all') [all]:
   ```
   `all`/empty = all, `1,3` = individual (1-based, same logic as `--select`).

3. For each selected entry the mapped fields, calculated values and required modules/dependencies
   are collected (with a per-company progress display) and written to one YAML file each.

### Result: the exported files

- They are written to the directory given via `--yaml_path`.
- The filename contains a timestamp so nothing gets overwritten:
  ```
  <report_name>_MM_DD_YYYY_HH_MM_SS.yaml
  e.g.  account.report_invoice_de_06_30_2026_14_23_11.yaml
  ```
- They contain fields, existing language versions and calculated values – everything that makes
  up the report, in exactly the form the mapper can read back in when registering again.

### Typical cycle

1. Roll out reports via mapping → 2. fine-tune graphically in Odoo → 3. save back to YAML with
collect → 4. version the saved files and roll them out to the next system.

### See also

- Re-import: [mapping-reports.md](mapping-reports.md)
- Target individual reports: [selective-registration.md](selective-registration.md)
