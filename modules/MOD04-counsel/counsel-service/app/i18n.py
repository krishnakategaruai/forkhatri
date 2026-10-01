"""Server-side text (notifications, system messages) is keyed; the web client
renders keys in the reader's language. Only expertise names need a language
pick on the server, for search and API responses."""

from __future__ import annotations

from fastapi import Request

SUPPORTED = ("en", "hi", "te")


def request_language(request: Request) -> str:
    lang = (request.headers.get("X-Counsel-Language") or "en").split("-")[0].lower()
    return lang if lang in SUPPORTED else "en"


def area_name(row, lang: str) -> str:
    return row.get(f"name_{lang}") or row.get("name_en") or row.get("id")
