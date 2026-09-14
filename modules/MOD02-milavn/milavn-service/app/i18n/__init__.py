"""Backend response localisation — ADR-010's server-side half.

# [FR002, ADR-010] Every API error/status message resolves through the
# caller's language (`X-Milavn-Language` header, then `Accept-Language`) so a
# Hindi- or Telugu-preferring member never receives English-only error prose
# the frontend cannot translate after the fact.
# Approach: `app/i18n/locales/<lang>/common.json`, English complete, hi/te
# partial with English fallback per key — a partial translation is never a bug.
# Traces to: FR002, TR01, ADR-010.
"""

from __future__ import annotations

import json
from contextvars import ContextVar
from functools import cache
from pathlib import Path
from typing import Final

SUPPORTED_LANGUAGES: Final = ("en", "hi", "te")
DEFAULT_LANGUAGE: Final = "en"
_LOCALES_DIR = Path(__file__).parent / "locales"

# The acting request's language, bound once by the middleware in `main.py` so
# deep call sites (card building, reason rendering) never need it threaded
# through as a parameter.
current_language: ContextVar[str] = ContextVar("milavn_language", default=DEFAULT_LANGUAGE)


def resolve_language(requested: str | None) -> str:
    if not requested:
        return DEFAULT_LANGUAGE
    primary = requested.split(",")[0].split("-")[0].strip().lower()
    return primary if primary in SUPPORTED_LANGUAGES else DEFAULT_LANGUAGE


@cache
def _catalog(lang: str) -> dict[str, str]:
    path = _LOCALES_DIR / lang / "common.json"
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def translate(key: str, lang: str, **params: object) -> str:
    template = _catalog(lang).get(key) or _catalog(DEFAULT_LANGUAGE).get(key) or key
    try:
        return template.format(**params)
    except (KeyError, IndexError):
        return template
