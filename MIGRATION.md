# Migration Guide — odoo-fast-report-mapper v0.9.x → v1.0

> **Language / Sprache**: [DE](#deutsche-dokumentation) | [EN](#english-documentation)

---

## Deutsche Dokumentation

### Überblick

Version 1.0.0 schließt die Package-Konsolidierung ab, die in v0.9.x begonnen wurde.
Das Legacy-Package `odoo_report_helper` ist vollständig entfernt. Alle öffentlichen APIs
befinden sich jetzt ausschließlich in `odoo_fast_report_mapper`.

---

### 1. Breaking Changes — Import-Pfade

Alle Importe aus `odoo_report_helper` müssen auf `odoo_fast_report_mapper` umgestellt werden.

#### Import-Mapping Tabelle

| Altes Import (v0.9.x) | Neues Import (v1.0) |
|----------------------|---------------------|
| `from odoo_report_helper.odoo_connection import OdooConnection` | `from odoo_fast_report_mapper import OdooConnection` |
| `from odoo_report_helper.report import Report` | `from odoo_fast_report_mapper import Report` |
| `from odoo_report_helper.exceptions import PathDoesNotExistError` | `from odoo_fast_report_mapper import PathDoesNotExistError` |
| `from odoo_report_helper.utils import parse_yaml_folder` | `from odoo_fast_report_mapper._utils import parse_yaml_folder` |

#### Vor/Nach-Beispiele

**Vor (v0.9.x):**
```python
from odoo_report_helper.odoo_connection import OdooConnection
from odoo_report_helper.report import Report
from odoo_report_helper.exceptions import PathDoesNotExistError
from odoo_report_helper.utils import parse_yaml_folder
```

**Nach (v1.0):**
```python
from odoo_fast_report_mapper import OdooConnection
from odoo_fast_report_mapper import Report
from odoo_fast_report_mapper import PathDoesNotExistError
from odoo_fast_report_mapper._utils import parse_yaml_folder  # interne API — kein öffentlicher Re-Export
```

---

### 2. Entfernte Klassen — ProgressBar, ReportProgress, create_progress_bar

Die drei Fortschrittsanzeige-Klassen/-Funktionen wurden entfernt, da sie lediglich
thin wrappers über `tqdm` waren und keinen Mehrwert boten.

#### Entfernte öffentliche API

- `ProgressBar` — entfernt
- `ReportProgress` — entfernt
- `create_progress_bar()` — entfernt

#### Vor (v0.9.x) — mit ProgressBar:
```python
from odoo_report_helper.odoo_connection import ProgressBar

with ProgressBar(total=len(reports), desc="Mapping reports") as pb:
    for report in reports:
        process(report)
        pb.update(1)
```

#### Nach (v1.0) — direkte tqdm-Verwendung:
```python
from tqdm import tqdm

for report in tqdm(reports, desc="Mapping reports", unit="report"):
    process(report)
```

**Hinweis:** Der interne Hilfswrapper `progress_bar()` in
`odoo_fast_report_mapper._progress` ist weiterhin für den internen Bibliotheksgebrauch
vorhanden, gilt aber nicht als öffentliche API.

---

### 3. Verhaltensänderungen (Phase 1.1)

#### 3a. ValueError bei leerem name_dict

Die Funktion `build_name_search_domain({})` wirft nun einen `ValueError`, wenn
`name_dict` leer ist, anstatt stillschweigend eine unbegrenzte Suchanfrage zu produzieren.

**Vor (v0.9.x):** Leeres `name_dict` führte zu einer unbegrenzten Suche, die alle
Berichte für das Modell treffen und den ersten überschreiben konnte (Datenverfälschung).

**Nach (v1.0):**
```python
from odoo_fast_report_mapper._lang_utils import build_name_search_domain

# Wirft ValueError — verhindert unkontrollierte Suche
build_name_search_domain({})
# ValueError: Cannot build name search domain from empty name_dict
```

Stellen Sie sicher, dass alle YAML-Berichtskonfigurationen gültige `name`-Einträge
(mindestens eine Sprache) enthalten.

#### 3b. api_key hat Vorrang vor password (YAML-Loader)

Wenn sowohl `api_key` als auch `password` in der Server-YAML-Konfiguration gesetzt sind,
hat `api_key` stillschweigend Vorrang. Es wird keine Warnung ausgegeben.

```yaml
# Wenn beide gesetzt sind, wird api_key verwendet:
Server:
  url: https://odoo.example.com
  password: "your_password"   # wird ignoriert, wenn api_key gesetzt ist
  api_key: "your_api_key"     # hat Vorrang
```

> **Hinweis:** Der `.env`-basierte Loader (`ODOO_API_KEY` + `ODOO_PASSWORD`) gibt hingegen
> eine `logger.warning` aus, wenn beide Variablen gesetzt sind. Dieser Unterschied ist
> beabsichtigt (D-06).

---

### 4. Mypy Strict — Auswirkungen

Wenn Ihr Downstream-Code gegen diese Bibliothek mit `mypy --strict` typgeprüft wird,
sind folgende Anpassungen nötig:

- Alle Import-Pfade müssen auf die neuen `odoo_fast_report_mapper.*`-Module zeigen
  (veraltete `odoo_report_helper.*`-Stubs existieren nicht mehr)
- Die Typen `ProgressBar`, `ReportProgress` und `create_progress_bar` sind nicht mehr
  verfügbar — entfernen Sie alle Typ-Annotationen, die diese verwenden
- `Report.__init__` erwartet jetzt `entry_name: dict[str, str]` — ein leeres Dict oder
  ein nicht-Dict-Wert wirft `TypeError` zur Laufzeit und wird von mypy statisch erkannt

Erwartete mypy-Fehler, die nach der Migration verschwinden:
```
error: Module "odoo_report_helper" has no attribute "OdooConnection"
error: Module "odoo_report_helper.exceptions" has no attribute "PathDoesNotExistError"
error: Cannot find implementation or library stub for module "odoo_report_helper"
```

---

### 5. Schnelle Migrations-Checkliste

- [ ] Alle `from odoo_report_helper.*` Importe auf `from odoo_fast_report_mapper.*` umstellen
- [ ] `ProgressBar`, `ReportProgress` und `create_progress_bar` durch direkte `tqdm`-Verwendung ersetzen
- [ ] YAML-Berichtskonfigurationen prüfen: jeder Bericht braucht mindestens einen `name`-Eintrag
- [ ] Falls beide `api_key` und `password` in YAML gesetzt sind: sicherstellen, dass `api_key` der gewünschte Authentifizierungsweg ist
- [ ] Mit `mypy --strict odoo_fast_report_mapper/` testen und verbleibende Importfehler beheben

---

---

## English Documentation

### Overview

Version 1.0.0 completes the package consolidation begun in v0.9.x.
The legacy `odoo_report_helper` package has been fully removed. All public APIs
now live exclusively in `odoo_fast_report_mapper`.

---

### 1. Breaking Changes — Import Paths

All imports from `odoo_report_helper` must be updated to `odoo_fast_report_mapper`.

#### Import Mapping Table

| Old import (v0.9.x) | New import (v1.0) |
|---------------------|-------------------|
| `from odoo_report_helper.odoo_connection import OdooConnection` | `from odoo_fast_report_mapper import OdooConnection` |
| `from odoo_report_helper.report import Report` | `from odoo_fast_report_mapper import Report` |
| `from odoo_report_helper.exceptions import PathDoesNotExistError` | `from odoo_fast_report_mapper import PathDoesNotExistError` |
| `from odoo_report_helper.utils import parse_yaml_folder` | `from odoo_fast_report_mapper._utils import parse_yaml_folder` |

#### Before/After Examples

**Before (v0.9.x):**
```python
from odoo_report_helper.odoo_connection import OdooConnection
from odoo_report_helper.report import Report
from odoo_report_helper.exceptions import PathDoesNotExistError
from odoo_report_helper.utils import parse_yaml_folder
```

**After (v1.0):**
```python
from odoo_fast_report_mapper import OdooConnection
from odoo_fast_report_mapper import Report
from odoo_fast_report_mapper import PathDoesNotExistError
from odoo_fast_report_mapper._utils import parse_yaml_folder  # internal API — not re-exported publicly
```

---

### 2. Removed Classes — ProgressBar, ReportProgress, create_progress_bar

The three progress-display classes/functions have been removed as they were thin
wrappers over `tqdm` that provided no additional value.

#### Removed Public API

- `ProgressBar` — removed
- `ReportProgress` — removed
- `create_progress_bar()` — removed

#### Before (v0.9.x) — using ProgressBar:
```python
from odoo_report_helper.odoo_connection import ProgressBar

with ProgressBar(total=len(reports), desc="Mapping reports") as pb:
    for report in reports:
        process(report)
        pb.update(1)
```

#### After (v1.0) — direct tqdm usage:
```python
from tqdm import tqdm

for report in tqdm(reports, desc="Mapping reports", unit="report"):
    process(report)
```

**Note:** The internal helper wrapper `progress_bar()` in
`odoo_fast_report_mapper._progress` still exists for internal library use,
but it is not part of the public API.

---

### 3. Behavior Changes (Phase 1.1)

#### 3a. ValueError on empty name_dict

The function `build_name_search_domain({})` now raises `ValueError` when
`name_dict` is empty, instead of silently producing an unbounded search query.

**Before (v0.9.x):** An empty `name_dict` led to an unbounded search that could
match all reports for the model and overwrite the first one found (data corruption).

**After (v1.0):**
```python
from odoo_fast_report_mapper._lang_utils import build_name_search_domain

# Raises ValueError — prevents uncontrolled search
build_name_search_domain({})
# ValueError: Cannot build name search domain from empty name_dict
```

Ensure all YAML report configurations contain valid `name` entries
(at least one language key).

#### 3b. api_key takes precedence over password (YAML loader)

When both `api_key` and `password` are set in the **server YAML configuration**,
`api_key` takes precedence silently. No warning is emitted.

```yaml
# When both are set, api_key is used:
Server:
  url: https://odoo.example.com
  password: "your_password"   # ignored when api_key is set
  api_key: "your_api_key"     # takes precedence
```

> **Note:** The `.env`-based loader (`ODOO_API_KEY` + `ODOO_PASSWORD`) **does** emit a
> `logger.warning` when both are set. This difference is intentional (D-06).

---

### 4. Mypy Strict Implications

If your downstream code is type-checked against this library using `mypy --strict`,
the following adjustments are required:

- All import paths must point to the new `odoo_fast_report_mapper.*` modules
  (the deprecated `odoo_report_helper.*` stubs no longer exist)
- The types `ProgressBar`, `ReportProgress`, and `create_progress_bar` are no longer
  available — remove all type annotations referencing them
- `Report.__init__` now expects `entry_name: dict[str, str]` — an empty dict or a
  non-dict value raises `TypeError` at runtime and is caught statically by mypy

Expected mypy errors that disappear after migration:
```
error: Module "odoo_report_helper" has no attribute "OdooConnection"
error: Module "odoo_report_helper.exceptions" has no attribute "PathDoesNotExistError"
error: Cannot find implementation or library stub for module "odoo_report_helper"
```

---

### 5. Quick Migration Checklist

- [ ] Update all `from odoo_report_helper.*` imports to `from odoo_fast_report_mapper.*`
- [ ] Replace `ProgressBar`, `ReportProgress`, and `create_progress_bar` with direct `tqdm` usage
- [ ] Audit YAML report configurations: each report must have at least one `name` entry
- [ ] If both `api_key` and `password` are set in YAML: verify that `api_key` is the intended auth method
- [ ] Test with `mypy --strict odoo_fast_report_mapper/` and fix any remaining import errors

---

*Migration Guide for odoo-fast-report-mapper — Equitania Software GmbH*
*See also: [RELEASE_NOTES.md](RELEASE_NOTES.md) for full changelog*
