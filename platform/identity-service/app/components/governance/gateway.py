"""Federated module queues for the Admin & Governance Console (TR-PLAT-01, ADR-012).

The console never reads a module's tables. For each module in MODULE_API_URLS it asks
the module for its view manifest (`GET {base}/{module}/admin/manifest`), then calls
the list, detail and action endpoints that manifest names. It calls them server to
server with the admin's own ForKhatri session cookie, so the module resolves the same
person through its Identity Bridge and its own chokepoint decides. The platform gate
in front (the admin must hold the view's `required_permission_scope`) is a second
lock, not a replacement. Every action is also written to the platform audit log.
"""

from __future__ import annotations

import asyncio
import re
import time
from typing import Any
from urllib.parse import quote

import httpx

from app.config.settings import Settings
from app.errors import DomainError

_MANIFEST_TTL_SECONDS = 60.0
_manifest_cache: dict[str, tuple[float, list[dict[str, Any]]]] = {}
_SAFE_PATH = re.compile(r"^/[A-Za-z0-9_\-/{}.]*$")
_SAFE_ID = re.compile(r"^[A-Za-z0-9_\-.:]{1,120}$")


def _normalise_views(module: str, manifest: Any) -> list[dict[str, Any]]:
    """Milavn ships a single descriptor; later modules ship {views: [...]}. Both are valid."""
    raw = manifest.get("views") if isinstance(manifest, dict) and "views" in manifest else [manifest]
    views = []
    for view in raw if isinstance(raw, list) else []:
        if not isinstance(view, dict):
            continue
        paths = [view.get("list_endpoint"), view.get("detail_endpoint"), *(view.get("action_endpoints") or [])]
        if not all(isinstance(p, str) and _SAFE_PATH.match(p) and "//" not in p for p in paths):
            continue  # a path that could leave the module's own API is never followed
        views.append(
            {
                "module_id": module,
                "view_id": str(view.get("view_id") or "queue"),
                "title": str(view.get("title") or module),
                "nav_group": str(view.get("nav_group") or "moderation"),
                "required_permission_scope": str(view.get("required_permission_scope") or f"{module}.moderate"),
                "list_endpoint": view["list_endpoint"],
                "detail_endpoint": view["detail_endpoint"],
                "action_endpoint": (view.get("action_endpoints") or [None])[0],
            }
        )
    return views


def _headers(settings: Settings, session_token: str, lang: str) -> dict[str, str]:
    return {
        "Cookie": f"{settings.session_cookie_name}={session_token}",
        "Accept": "application/json",
        "Accept-Language": lang,
        "X-ForKhatri-Console": "1",
    }


async def _manifest(client: httpx.AsyncClient, settings: Settings, module: str, base: str, token: str, lang: str) -> list[dict[str, Any]]:
    cached = _manifest_cache.get(f"{module}:{lang}")
    if cached and time.monotonic() - cached[0] < _MANIFEST_TTL_SECONDS:
        return cached[1]
    response = await client.get(f"{base.rstrip('/')}/{module}/admin/manifest", headers=_headers(settings, token, lang))
    response.raise_for_status()
    views = _normalise_views(module, response.json())
    _manifest_cache[f"{module}:{lang}"] = (time.monotonic(), views)
    return views


def _error_code(exc: Exception) -> str:
    if isinstance(exc, httpx.HTTPStatusError):
        status = exc.response.status_code
        if status in (401, 403, 404):
            return "no_access"
        return f"module_error_{status}"
    if isinstance(exc, httpx.HTTPError):
        return "module_unreachable"
    return "module_bad_response"


async def queues(settings: Settings, *, token: str, lang: str, scopes: frozenset[str]) -> list[dict[str, Any]]:
    """Every module view this admin is appointed to, with its items (or why they are missing)."""
    modules = {m: url for m, url in settings.admin_modules.items() if any(s.startswith(f"{m}.") for s in scopes)}

    async with httpx.AsyncClient(timeout=settings.admin_gateway_timeout_seconds) as client:

        async def one_module(module: str, base: str) -> list[dict[str, Any]]:
            try:
                views = await _manifest(client, settings, module, base, token, lang)
            except Exception as exc:  # noqa: BLE001 - one module down must not blank the console
                code = _error_code(exc)
                if isinstance(exc, httpx.HTTPStatusError) and exc.response.status_code == 404:
                    code = "not_connected"  # the module has not published admin views yet
                return [{"module_id": module, "view_id": None, "title": module, "error": code, "items": []}]
            out = []
            for view in views:
                if view["required_permission_scope"] not in scopes:
                    continue
                try:
                    r = await client.get(f"{base.rstrip('/')}{view['list_endpoint']}", headers=_headers(settings, token, lang))
                    r.raise_for_status()
                    items = r.json()
                    if isinstance(items, dict):
                        items = items.get("items", [])
                    out.append({**_public(view), "error": None, "items": items if isinstance(items, list) else []})
                except Exception as exc:  # noqa: BLE001
                    out.append({**_public(view), "error": _error_code(exc), "items": []})
            return out

        results = await asyncio.gather(*(one_module(m, u) for m, u in modules.items()))
    return [view for group in results for view in group]


def _public(view: dict[str, Any]) -> dict[str, Any]:
    return {k: view[k] for k in ("module_id", "view_id", "title", "nav_group", "required_permission_scope")}


async def _view(settings: Settings, module: str, view_id: str, token: str, lang: str, scopes: frozenset[str]) -> tuple[str, dict[str, Any]]:
    base = settings.admin_modules.get(module)
    if base is None:
        raise DomainError("module_unknown", "This module is not connected to the console.", 404)
    async with httpx.AsyncClient(timeout=settings.admin_gateway_timeout_seconds) as client:
        try:
            views = await _manifest(client, settings, module, base, token, lang)
        except Exception as exc:  # noqa: BLE001
            raise DomainError(_error_code(exc), "The module could not be reached.", 502) from exc
    view = next((v for v in views if v["view_id"] == view_id), None)
    if view is None:
        raise DomainError("view_unknown", "This queue does not exist.", 404)
    if view["required_permission_scope"] not in scopes:
        raise DomainError("admin_forbidden", "You are not appointed to this queue.", 403)
    return base.rstrip("/"), view


def _fill(template: str, **values: str) -> str:
    for key, value in values.items():
        if not _SAFE_ID.match(value):
            raise DomainError("validation_failed", "Invalid identifier.", 422)
        template = template.replace("{" + key + "}", quote(value, safe=""))
    return template


async def _forward(method: str, url: str, headers: dict[str, str], settings: Settings, body: dict[str, Any] | None = None) -> Any:
    async with httpx.AsyncClient(timeout=settings.admin_gateway_timeout_seconds) as client:
        try:
            response = await client.request(method, url, headers=headers, json=body)
        except httpx.HTTPError as exc:
            raise DomainError("module_unreachable", "The module could not be reached.", 502) from exc
    if response.status_code >= 400:
        message = "The module refused this action."
        try:
            detail = response.json().get("detail")
            if isinstance(detail, str):
                message = detail
            elif isinstance(detail, dict) and isinstance(detail.get("message"), str):
                message = detail["message"]
        except ValueError:
            pass
        status = response.status_code if response.status_code in (403, 404, 409, 422) else 502
        raise DomainError("module_refused", message, status)
    return response.json()


async def detail(settings: Settings, *, module: str, view_id: str, item_id: str, token: str, lang: str, scopes: frozenset[str]) -> Any:
    base, view = await _view(settings, module, view_id, token, lang, scopes)
    return await _forward("GET", base + _fill(view["detail_endpoint"], item_id=item_id), _headers(settings, token, lang), settings)


async def act(
    settings: Settings,
    *,
    module: str,
    view_id: str,
    item_id: str,
    action_id: str,
    body: dict[str, Any],
    token: str,
    lang: str,
    scopes: frozenset[str],
) -> Any:
    base, view = await _view(settings, module, view_id, token, lang, scopes)
    if not view["action_endpoint"]:
        raise DomainError("view_read_only", "This queue has no actions.", 409)
    url = base + _fill(view["action_endpoint"], item_id=item_id, action_id=action_id)
    return await _forward("POST", url, _headers(settings, token, lang), settings, body)


async def member_summaries(settings: Settings, *, member_id: str, token: str, lang: str, scopes: frozenset[str]) -> list[dict[str, Any]]:
    """What each module knows about one person, as that module chooses to show it (TR-PLAT-01 extension).

    `GET {base}/{module}/admin/members/{member_id}/summary` answers
    `{ "plan": {"tier", "name", "status", "renews_at"?} | null, "facts": [{"label", "value"}], "flags": [str], "deep_link"? }`.
    Pricing tiers are module data (PRODUCT-GUARDRAILS: tiers are module-owned) and differ
    per module, so the console shows each module's own tier side by side and never
    merges them into one platform plan. A module without the endpoint is simply omitted.
    """
    if not _SAFE_ID.match(member_id):
        raise DomainError("validation_failed", "Invalid identifier.", 422)
    modules = {m: url for m, url in settings.admin_modules.items() if any(s.startswith(f"{m}.") for s in scopes)}

    async with httpx.AsyncClient(timeout=settings.admin_gateway_timeout_seconds) as client:

        async def one(module: str, base: str) -> dict[str, Any] | None:
            try:
                r = await client.get(
                    f"{base.rstrip('/')}/{module}/admin/members/{quote(member_id, safe='')}/summary",
                    headers=_headers(settings, token, lang),
                )
                if r.status_code == 404:
                    return None
                r.raise_for_status()
                body = r.json()
                return {"module_id": module, "error": None, **(body if isinstance(body, dict) else {})}
            except Exception as exc:  # noqa: BLE001
                return {"module_id": module, "error": _error_code(exc)}

        results = await asyncio.gather(*(one(m, u) for m, u in modules.items()))
    return [r for r in results if r is not None]
