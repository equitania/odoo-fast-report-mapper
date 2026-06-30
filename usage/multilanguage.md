# Mehrsprachige Berichtsnamen · Multi-language Report Names

> **Sprache / Language**: [DE](#deutsch) · [EN](#english)

---

## Deutsch

### Worum es geht

Berichtsbezeichnungen werden automatisch in **allen in Odoo aktiven Sprachen** gepflegt. Du
hinterlegst die Übersetzungen einmal in der YAML-Datei, der Mapper schreibt sie beim
Registrieren in die jeweilige Sprachfassung des Belegs. Anwender sehen die Druckbezeichnung
also immer in ihrer eigenen Sprache – ohne dass du in Odoo nachpflegen musst.

### So definierst du Übersetzungen

Im `name:`-Block der YAML-Datei nutzt du Odoo-Locale-Codes als Schlüssel:

```yaml
name:
  de_DE: Rechnung
  en_US: Invoice
  fr_FR: Facture
```

- **Primärsprache** ist `ODOO_LANGUAGE` aus der `.env` (z. B. `de_DE`). Sie bestimmt den
  Standard-Anzeigenamen, unter dem der Bericht in Odoo gesucht und zuerst geschrieben wird.
- Es werden **nur Sprachen geschrieben, die in Odoo installiert/aktiv sind.** Übersetzungen für
  nicht installierte Sprachen werden stillschweigend übersprungen – die YAML darf also ruhig
  mehr Sprachen enthalten als ein konkretes System nutzt.
- **Legacy-Schlüssel** `ger` und `eng` werden automatisch zu `de_DE` bzw. `en_US` normalisiert.
  Auch gemischte Angaben (z. B. `ger` zusammen mit `en_US`) werden vollständig umgesetzt.
  Empfehlung: in neuen Dateien direkt Locale-Codes verwenden.

### Druckdateiname und Anhänge

- **`print_report_name`** (der angezeigte/gedruckte Belegtitel) kann ebenfalls je Sprache
  angegeben werden:
  ```yaml
  print_report_name:
    de_DE: "'Rechnung-' + object.name"
    en_US: "'Invoice-' + object.name"
  ```
  Wird stattdessen nur ein einzelner Text angegeben, gilt dieser für alle installierten Sprachen.
- **`attachment`** (der Dateiname einer automatisch gespeicherten PDF) ist in Odoo **nicht**
  übersetzbar – hier wird genau ein Wert gesetzt. Der Mapper wählt ihn anhand der
  Unternehmenssprache, ersatzweise der Primärsprache aus der `.env`.

### Praxistipp

Pflege deine Belegnamen konsequent zweisprachig (mindestens `de_DE`/`en_US`). So sind deine
YAML-Dateien sofort auf jedem Kundensystem einsetzbar – unabhängig davon, welche Sprachen dort
gerade aktiv sind.

---

## English

### What it does

Report names are maintained automatically in **all languages active in Odoo**. You provide the
translations once in the YAML file; the mapper writes them into the respective language version
of the document during registration. Users always see the print label in their own language –
without you having to maintain it in Odoo.

### Defining translations

In the `name:` block of the YAML file, use Odoo locale codes as keys:

```yaml
name:
  de_DE: Rechnung
  en_US: Invoice
  fr_FR: Facture
```

- The **primary language** is `ODOO_LANGUAGE` from `.env` (e.g. `de_DE`). It determines the
  default display name under which the report is searched and first written in Odoo.
- Only **languages that are installed/active in Odoo are written.** Translations for languages
  that aren't installed are silently skipped – so a YAML file may safely contain more languages
  than a given system uses.
- **Legacy keys** `ger` and `eng` are auto-normalized to `de_DE` / `en_US`. Mixed entries (e.g.
  `ger` together with `en_US`) are fully resolved. Recommendation: use locale codes directly in
  new files.

### Print filename and attachments

- **`print_report_name`** (the displayed/printed document title) can also be given per language:
  ```yaml
  print_report_name:
    de_DE: "'Rechnung-' + object.name"
    en_US: "'Invoice-' + object.name"
  ```
  If a single string is given instead, it applies to all installed languages.
- **`attachment`** (the filename of an auto-saved PDF) is **not** translatable in Odoo – a single
  value is set. The mapper picks it based on the company language, falling back to the primary
  language from `.env`.

### Practical tip

Maintain your document names consistently bilingually (at least `de_DE`/`en_US`). That way your
YAML files are immediately usable on any customer system – regardless of which languages happen
to be active there.
