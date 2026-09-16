# [Product-owner standing i18n rule] Resolve the caller's language for
# every localized response, the same shape as Mangaly's `api/deps.py`
# (read, not edited): `X-Vyapar-Language` takes priority — it carries the
# frontend's actual resolved i18next language (the member's saved choice,
# per `vyapar-web/lib/i18n/provider.tsx`), which is more specific than the
# browser's `Accept-Language` and is what should win once a member has
# made an explicit choice. `Accept-Language` remains the fallback for any
# caller that doesn't send the custom header (a script, a future
# non-web client).
# Traces to: product-owner i18n rule, 2026-09-15 (not a numbered FR)
from __future__ import annotations

from typing import Annotated

from fastapi import Depends, Header

from app.i18n import resolve_language


def get_locale(
    x_vyapar_language: str | None = Header(default=None, alias="X-Vyapar-Language"),
    accept_language: str | None = Header(default=None, alias="Accept-Language"),
) -> str:
    return resolve_language(x_vyapar_language or accept_language)


Locale = Annotated[str, Depends(get_locale)]
