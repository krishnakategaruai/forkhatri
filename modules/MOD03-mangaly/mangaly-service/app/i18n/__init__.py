"""Backend response localization — ADR-010's other half.

`/ARCHITECTURE.md` ADR-010 fixes ONE i18n convention with two runtime
realizations: react-i18next on the frontend (`mangaly-web/lib/i18n/`,
`mangaly-web/locales/`) and "locale-aware Pydantic response shaping" here.
Before this module existed, every API error/status message was a literal
English string written directly into `api/routes/*.py` — that bypassed the
frontend's translation layer entirely, since there is nothing for React to
translate once the server has already produced final English prose. A Hindi-
or Telugu-preferring user got English from every 401/422/429 regardless of
their selected language.

Structure deliberately mirrors the frontend's, so one person maintaining
translations has one mental model, not two:

    app/i18n/locales/<lang>/<namespace>.json   (here)
    mangaly-web/locales/<lang>/<namespace>.json (frontend)

Same fallback rule as the frontend: English is complete, Hindi/Telugu may be
partial, and a missing key in a non-English catalog resolves to its English
text rather than raising or returning a raw key — a partial translation must
never look like a bug.

Usage: `translate("auth.error.invalidCredentials", lang)`, or with
placeholders: `translate("auth.error.credentialTooShort", lang, min=10)`.
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

    Accepts a full BCP-47 tag (`en-US`) by taking its primary subtag, the same
    way the frontend's device-locale fallback does, so the two stay consistent
    for a header like `Accept-Language: en-US,en;q=0.9`.
    """
    if not requested:
        return DEFAULT_LANGUAGE
    primary = requested.split(",")[0].split("-")[0].strip().lower()
    return primary if is_supported(primary) else DEFAULT_LANGUAGE


@cache
def _catalog(lang: str, namespace: str) -> dict[str, object]:
    """Load and cache one `<lang>/<namespace>.json` file.

    Cached because these are read on every request; the files only change via
    a deploy, never at runtime, so process-lifetime caching is correct rather
    than a premature optimization.
    """
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
    """Resolve `"<namespace>.<dotted.path>"` to localized text.

    Falls back to English on a missing key in the requested language, then to
    the literal key itself if even English is missing it — the second case is
    a developer error (a key that was never added anywhere) and should be
    visible precisely because it looks wrong, unlike a genuine missing
    translation which must look like ordinary English text.
    """
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
