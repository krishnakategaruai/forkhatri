"""Backend response localization.

[Product-owner standing rule, 2026-09-15] ForKhatri is multilingual
(English, Hindi, Telugu) — no member-facing message may be hardcoded in
one language, including API error/success `detail` strings, since the
frontend's translation layer can't retranslate prose the server already
finalized in English. Mirrors MOD03 Mangaly's `app/i18n/__init__.py`
exactly (read, not edited) so one person maintaining translations across
modules has one mental model:

    app/i18n/locales/<lang>/<namespace>.json   (here — vyapar-service)
    vyapar-web/locales/<lang>/<namespace>.json (frontend)

Unlike Mangaly's own stated fallback tolerance (Hindi/Telugu may be
partial), the product owner's rule for Vyapar is stricter: every key
actually used by this codebase must have a real Hindi and Telugu value —
the English-fallback mechanism below exists as a safety net for a
genuinely missing key (a bug to fix), not as how Hindi/Telugu are allowed
to ship long-term.

Usage: `translate("listings.error.notFound", lang)`, or with placeholders:
`translate("opportunities.error.confirmRequired", lang, fields="type")`.
"""

from __future__ import annotations

import json
import logging
from functools import cache
from pathlib import Path
from typing import Final

logger = logging.getLogger(__name__)

SUPPORTED_LANGUAGES: Final = ("en", "hi", "te")
DEFAULT_LANGUAGE: Final = "en"
_LOCALES_DIR = Path(__file__).parent / "locales"


def is_supported(value: str | None) -> bool:
    return value in SUPPORTED_LANGUAGES


def resolve_language(requested: str | None) -> str:
    """The one place a request's language preference is decided.

    Accepts a full BCP-47 tag (`en-US`) by taking its primary subtag, the
    same way the frontend's device-locale fallback does, so the two stay
    consistent for a header like `Accept-Language: en-US,en;q=0.9`.
    """
    if not requested:
        return DEFAULT_LANGUAGE
    primary = requested.split(",")[0].split("-")[0].strip().lower()
    return primary if is_supported(primary) else DEFAULT_LANGUAGE


@cache
def _catalog(lang: str, namespace: str) -> dict[str, object]:
    """Load and cache one `<lang>/<namespace>.json` file. Cached because
    these are read on every request; the files only change via a deploy,
    never at runtime, so process-lifetime caching is correct here."""
    path = _LOCALES_DIR / lang / f"{namespace}.json"
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        logger.error("malformed i18n catalog: %s", path)
        return {}


def _lookup(catalog: dict[str, object], dotted_key: str) -> str | None:
    node: object = catalog
    for part in dotted_key.split("."):
        if not isinstance(node, dict) or part not in node:
            return None
        node = node[part]
    return node if isinstance(node, str) else None


def translate(key: str, lang: str | None = None, **params: object) -> str:
    """Resolve `"<namespace>.<dotted.path>"` to localized text. Falls back
    to English on a missing key in the requested language, then to the
    literal key itself if even English is missing it — the second case is
    a developer error (a key never added anywhere) and should be visible
    precisely because it looks wrong, unlike a genuine translation gap
    which must read as ordinary prose."""
    namespace, _, dotted = key.partition(".")
    lang = lang if is_supported(lang) else DEFAULT_LANGUAGE

    text = _lookup(_catalog(lang, namespace), dotted)
    if text is None and lang != DEFAULT_LANGUAGE:
        text = _lookup(_catalog(DEFAULT_LANGUAGE, namespace), dotted)
    if text is None:
        logger.warning("missing i18n key in every catalog: %s", key)
        return key

    for name, value in params.items():
        text = text.replace(f"{{{name}}}", str(value))
    return text
