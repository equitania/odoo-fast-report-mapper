# Copyright 2014-now Equitania Software GmbH - Pforzheim - Germany
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

"""
Language utility functions for multi-language support.

Provides backward compatibility mapping between legacy language keys (ger/eng)
and Odoo locale codes (de_DE/en_US), plus helper functions for dynamic
language handling in report name dictionaries.
"""

# Backward compatibility mapping: legacy keys -> Odoo locale codes
LEGACY_LANG_MAP = {
    "ger": "de_DE",
    "eng": "en_US",
}

# Reverse mapping for collection mode
LOCALE_TO_LEGACY = {v: k for k, v in LEGACY_LANG_MAP.items()}


def normalize_language_code(lang_code: str) -> str:
    """Convert legacy 'ger'/'eng' to Odoo locale codes, pass through valid locales.

    Args:
        lang_code: Language code, either legacy ('ger', 'eng') or Odoo locale ('de_DE', 'fr_FR').

    Returns:
        Odoo locale code string.
    """
    return LEGACY_LANG_MAP.get(lang_code, lang_code)


def normalize_name_dict(name_dict: dict) -> dict:
    """Convert legacy name dict keys to Odoo locale codes.

    {'ger': 'X', 'eng': 'Y'} -> {'de_DE': 'X', 'en_US': 'Y'}
    Already-normalized dicts pass through unchanged.

    Args:
        name_dict: Dictionary mapping language keys to report names.

    Returns:
        Dictionary with Odoo locale codes as keys.
    """
    normalized = {}
    for key, value in name_dict.items():
        normalized[normalize_language_code(key)] = value
    return normalized


def get_primary_lang(name_dict: dict) -> str:
    """Return primary language code from name dict.

    Priority: de_DE > any key starting with 'de' > first key.

    Args:
        name_dict: Dictionary mapping language codes to report names.

    Returns:
        The primary language code string.
    """
    if "de_DE" in name_dict:
        return "de_DE"
    for key in name_dict:
        if key.startswith("de"):
            return key
    return next(iter(name_dict))


def build_name_search_domain(name_dict: dict) -> list:
    """Build an OR-domain for searching by all name variants.

    Returns Odoo domain list that matches any name value from the dict,
    including ' (PDF)' suffix variants.

    Args:
        name_dict: Dictionary mapping language codes to report names.

    Returns:
        Odoo domain list with OR operators.
    """
    all_variants = []
    for name in name_dict.values():
        all_variants.append(("name", "=ilike", name))
        all_variants.append(("name", "=ilike", name + " (PDF)"))
    # Build OR chain: n-1 '|' operators for n conditions
    if len(all_variants) <= 1:
        return all_variants
    or_operators = ["|"] * (len(all_variants) - 1)
    return or_operators + all_variants


def resolve_attachment_value(attachment, company_lang, fallback_lang=None):
    """Resolve per-language attachment dict to single string value.

    Unlike print_report_name (translatable, written per language via with_context),
    attachment is a plain Char field — NOT translatable. Only one value is written,
    resolved based on the company's language.

    Fallback chain: company_lang -> fallback_lang -> get_primary_lang() -> first value.
    Strings pass through unchanged (backward compatibility).

    Args:
        attachment: Either a string (legacy) or dict mapping locale codes to values.
        company_lang: Odoo locale code from res.company.partner_id.lang (e.g. 'de_DE').
        fallback_lang: Optional fallback locale code (e.g. connection language).

    Returns:
        Single string value for the attachment field.
    """
    if not isinstance(attachment, dict):
        return attachment
    if company_lang in attachment:
        return attachment[company_lang]
    if fallback_lang and fallback_lang in attachment:
        return attachment[fallback_lang]
    primary = get_primary_lang(attachment)
    if primary in attachment:
        return attachment[primary]
    return next(iter(attachment.values()))
