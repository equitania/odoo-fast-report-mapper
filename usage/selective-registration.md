# Nur ausgewählte Reports registrieren (`--select`) · Registering Selected Reports (`--select`)

> **Sprache / Language**: [DE](#deutsch) · [EN](#english)

---

## Deutsch

### Worum es geht

Statt den gesamten YAML-Ordner zu verarbeiten, kannst du mit `--select` gezielt **einzelne
Berichte** zur Registrierung auswählen. Das ist ideal, um einen einzelnen geänderten Beleg
nachzuziehen oder – nach einem Sammellauf – nur die fehlgeschlagenen Berichte erneut zu mappen,
ohne alle anderen anzufassen.

### Schritt für Schritt

```bash
odoo-fr-mapper --yaml_path=./reports_yaml --select
```

1. Nach der Verbindungsbestätigung zeigt das Tool eine nummerierte Tabelle aller YAML-Dateien
   im Ordner:
   ```
   Found 4 YAML report(s):

     #  Filename             Report Name        Model
   ---  -------------------  -----------------  --------------
     1  invoice_de.yaml      Rechnung DE        account.move
     2  delivery_slip.yaml   Lieferschein       stock.picking
     3  sale_order.yaml      Verkaufsauftrag    sale.order
     4  purchase.yaml        Bestellung         purchase.order
   ```

2. An der Eingabeaufforderung wählst du aus:
   ```
   Select reports (e.g. 1,3,5 or 'all') [all]:
   ```
   - **`all`** oder **leere Eingabe** (Standard) → alle Berichte.
   - **Kommagetrennte Nummern**, z. B. `1,3` → genau diese Berichte (1-basiert).
   - Ungültige Nummern außerhalb des Bereichs werden stillschweigend ignoriert.
   - Eine nicht-numerische Eingabe bricht mit `Invalid selection. Aborting.` ab.
   - **Zahlenbereiche wie `1-3` werden nicht unterstützt** – nutze `1,2,3`.

3. Nur die gewählten Berichte werden registriert; der weitere Ablauf (Fortschritt,
   Fehlerzusammenfassung, QWeb-Ausblendung) entspricht dem normalen Mapping.

### Ohne `--select`

Ohne das Flag werden **alle** YAML-Dateien des Ordners ohne Rückfrage verarbeitet – die
passende Variante für unbeaufsichtigte Sammelläufe.

### Mehr dazu

- Grundlagen des Mappings: [mapping-reports.md](mapping-reports.md)

---

## English

### What it does

Instead of processing the entire YAML folder, `--select` lets you pick **individual reports**
for registration. This is ideal for pushing a single changed document, or – after a bulk run –
re-mapping only the failed reports without touching the rest.

### Step by step

```bash
odoo-fr-mapper --yaml_path=./reports_yaml --select
```

1. After the connection confirmation, the tool shows a numbered table of all YAML files in the
   folder:
   ```
   Found 4 YAML report(s):

     #  Filename             Report Name        Model
   ---  -------------------  -----------------  --------------
     1  invoice_de.yaml      Rechnung DE        account.move
     2  delivery_slip.yaml   Lieferschein       stock.picking
     3  sale_order.yaml      Verkaufsauftrag    sale.order
     4  purchase.yaml        Bestellung         purchase.order
   ```

2. At the prompt, make your selection:
   ```
   Select reports (e.g. 1,3,5 or 'all') [all]:
   ```
   - **`all`** or an **empty input** (default) → all reports.
   - **Comma-separated numbers**, e.g. `1,3` → exactly those reports (1-based).
   - Invalid numbers outside the range are silently ignored.
   - A non-numeric input aborts with `Invalid selection. Aborting.`
   - **Ranges like `1-3` are not supported** – use `1,2,3`.

3. Only the selected reports are registered; the rest of the flow (progress, failure summary,
   QWeb hiding) is the same as normal mapping.

### Without `--select`

Without the flag, **all** YAML files in the folder are processed without prompting – the right
choice for unattended bulk runs.

### See also

- Mapping basics: [mapping-reports.md](mapping-reports.md)
