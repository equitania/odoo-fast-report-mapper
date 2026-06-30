# Reports in Odoo registrieren (Mapping) · Registering Reports in Odoo (Mapping)

> **Sprache / Language**: [DE](#deutsch) · [EN](#english)

---

## Deutsch

### Worum es geht

Beim **Mapping** überträgt der Fast Report Mapper deine FastReport-Belege aus zentralen
YAML-Konfigurationsdateien in Odoo. Für jeden Bericht wird der zugehörige Druckeintrag im
Odoo-System angelegt oder aktualisiert, die benötigten Modellfelder werden zugeordnet und –
falls definiert – berechnete Zusatzangaben hinterlegt. Statt jeden Beleg von Hand in Odoo zu
pflegen, rollst du so ein komplettes, reproduzierbares Berichtsset in einem Durchlauf aus.

### Voraussetzungen

- Eine konfigurierte `.env` mit Verbindungsdaten (siehe `odoo-fr-mapper --init`).
- Ein Ordner mit YAML-Berichtsdefinitionen (`--yaml_path`).
- Das Modul **`eq_fr_core`** (und die je Bericht benötigten Module) muss in Odoo installiert sein.
- `ODOO_WORKFLOW=0` (Standard – nur Mapping).

### Schritt für Schritt

```bash
# Alle Berichte eines Ordners registrieren/aktualisieren
odoo-fr-mapper --yaml_path=./reports_yaml
```

1. **Verbindungs-Zusammenfassung & Bestätigung.** Vor jedem Login zeigt das Tool eine
   Übersicht und fragt nach – so verbindest du dich nie versehentlich gegen das falsche System:

   ```
   ┌──────────────────────────────────────────┐
   │   Connection Summary                       │
   ├──────────────────────────────────────────┤
   │   .env:     /pfad/zu/.env                  │
   │   Server:   https://odoo.example.com       │
   │   Database: your_database                  │
   │   User:     admin@example.com              │
   │   Auth:     Password                        │
   │   Workflow: Mapping only                    │
   └──────────────────────────────────────────┘

   Proceed? [Y/n]:
   ```
   Mit `n` brichst du gefahrlos ab (kein Login).

2. **Registrierung.** Nach der Anmeldung werden zuerst die installierten Sprachen ermittelt,
   dann läuft das Mapping mit Fortschrittsanzeige:
   ```
   Installed languages: ['de_DE', 'en_US']
   → Mapping 12 reports to Odoo...
     [1/12] eq_fr_core_sale_order
     ✓ Completed: eq_fr_core_sale_order
   → Writing field mappings to 5 models...
     [1/5] Updating sale.order (8 fields)...
   ✓ Field mapping completed successfully
   ```

3. **Robust gegen Einzelfehler.** Schlägt ein einzelner Bericht fehl, bricht der Lauf **nicht**
   ab – die übrigen werden weiterverarbeitet. Am Ende erhältst du eine Zusammenfassung mit dem
   Tipp, gezielt nur die fehlgeschlagenen Berichte erneut zu registrieren:
   ```
   ⚠ 1 of 12 report(s) failed:
     - eq_fr_core_invoice: Model 'account.move' not found

   Tip: Re-run failed reports individually with:
     odoo-fr-mapper --yaml_path=./reports_yaml --select
   ```

### QWeb-Standardberichte ausblenden

Mit `ODOO_DISABLE_QWEB=True` (Standard) werden nach dem Mapping die klassischen
QWeb-Druckeinträge (PDF/HTML/Text) aus den Druckmenüs entfernt, sodass Anwender nur noch die
FastReport-Belege sehen. Die Datensätze bleiben in der Datenbank erhalten – ausgeblendet wird
lediglich der Menüeintrag.

- **`True` (Produktion):** Anwender sollen ausschließlich FastReport-Druckoptionen sehen.
- **`False` (Migration/Test):** QWeb-Berichte werden parallel weiter benötigt.

Hinweis: Die Ausblendung wirkt **global** auf alle QWeb-Berichte der Datenbank, nicht nur auf
die gerade gemappten.

### Mehr dazu

- Mehrsprachige Berichtsnamen: [multilanguage.md](multilanguage.md)
- Nur ausgewählte Berichte registrieren: [selective-registration.md](selective-registration.md)
- Bestehende Berichte zurück nach YAML sichern: [collect-to-yaml.md](collect-to-yaml.md)

---

## English

### What it does

**Mapping** transfers your FastReport documents from central YAML configuration files into
Odoo. For each report the corresponding print entry is created or updated, the required model
fields are mapped and – if defined – calculated values are attached. Instead of maintaining
every document by hand, you roll out a complete, reproducible report set in a single run.

### Prerequisites

- A configured `.env` with connection details (see `odoo-fr-mapper --init`).
- A folder of YAML report definitions (`--yaml_path`).
- The **`eq_fr_core`** module (and the modules each report needs) installed in Odoo.
- `ODOO_WORKFLOW=0` (default – mapping only).

### Step by step

```bash
# Register/update all reports in a folder
odoo-fr-mapper --yaml_path=./reports_yaml
```

1. **Connection summary & confirmation.** Before every login the tool shows a summary and asks
   to proceed – so you never connect to the wrong system by accident:

   ```
   ┌──────────────────────────────────────────┐
   │   Connection Summary                       │
   ├──────────────────────────────────────────┤
   │   .env:     /path/to/.env                  │
   │   Server:   https://odoo.example.com       │
   │   Database: your_database                  │
   │   User:     admin@example.com              │
   │   Auth:     Password                        │
   │   Workflow: Mapping only                    │
   └──────────────────────────────────────────┘

   Proceed? [Y/n]:
   ```
   Answer `n` to abort safely (no login).

2. **Registration.** After login the installed languages are detected, then mapping runs with a
   progress display:
   ```
   Installed languages: ['de_DE', 'en_US']
   → Mapping 12 reports to Odoo...
     [1/12] eq_fr_core_sale_order
     ✓ Completed: eq_fr_core_sale_order
   → Writing field mappings to 5 models...
     [1/5] Updating sale.order (8 fields)...
   ✓ Field mapping completed successfully
   ```

3. **Resilient to single failures.** If an individual report fails, the run does **not** stop –
   the others are processed. At the end you get a summary with a tip to re-run only the failed
   reports:
   ```
   ⚠ 1 of 12 report(s) failed:
     - eq_fr_core_invoice: Model 'account.move' not found

   Tip: Re-run failed reports individually with:
     odoo-fr-mapper --yaml_path=./reports_yaml --select
   ```

### Hiding QWeb standard reports

With `ODOO_DISABLE_QWEB=True` (default), the classic QWeb print entries (PDF/HTML/text) are
removed from the print menus after mapping, so users only see the FastReport documents. The
records remain in the database – only the menu entry is hidden.

- **`True` (production):** users should see FastReport print options exclusively.
- **`False` (migration/test):** QWeb reports are still needed in parallel.

Note: hiding acts **globally** on all QWeb reports in the database, not just the ones just mapped.

### See also

- Multi-language report names: [multilanguage.md](multilanguage.md)
- Register only selected reports: [selective-registration.md](selective-registration.md)
- Save existing reports back to YAML: [collect-to-yaml.md](collect-to-yaml.md)
