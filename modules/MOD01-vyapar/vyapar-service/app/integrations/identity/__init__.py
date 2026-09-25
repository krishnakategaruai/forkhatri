# [IMP37 — Refactor B] Identity adapters behind one IdentityProvider
# interface. IDENTITY_PROVIDERS (config) chooses which run and in what order;
# the first provider that recognises a credential decides. app/identity.py's
# resolve_authz_context() stays the single choke point every route uses.
from __future__ import annotations

from functools import lru_cache

from fastapi import Request

from app.config import get_settings
from app.integrations.errors import fail, request_language
from app.integrations.identity.base import (
    AUTH_ACCESS_TOKEN,
    AUTH_DEV_HEADER,
    AUTH_MEMBER_SESSION,
    IdentityProvider,
    ResolvedIdentity,
)
from app.integrations.identity.bearer_token import BearerTokenProvider
from app.integrations.identity.dev_header import DevHeaderProvider
from app.integrations.identity.forkhatri_session import ForKhatriSessionProvider

PROVIDER_FACTORIES: dict[str, type] = {
    "bearer": BearerTokenProvider,
    "dev": DevHeaderProvider,
    "forkhatri": ForKhatriSessionProvider,
}


def register_provider(name: str, factory: type) -> None:
    """For a host that ships its own adapter: register it before the app
    starts serving, then list its name in IDENTITY_PROVIDERS."""
    PROVIDER_FACTORIES[name] = factory
    configured_providers.cache_clear()


@lru_cache
def configured_providers() -> tuple[IdentityProvider, ...]:
    names = get_settings().identity_provider_names
    unknown = [n for n in names if n not in PROVIDER_FACTORIES]
    if unknown:
        raise RuntimeError(f"Unknown IDENTITY_PROVIDERS entries: {unknown}; known: {sorted(PROVIDER_FACTORIES)}")
    return tuple(PROVIDER_FACTORIES[n]() for n in names)


async def authenticate(request: Request) -> ResolvedIdentity:
    """Runs the configured providers in order. Raises 401 when none
    recognises a credential."""
    for provider in configured_providers():
        identity = await provider.resolve(request)
        if identity is not None:
            return identity
    raise fail(401, "not_authenticated", request_language(request))


__all__ = [
    "AUTH_ACCESS_TOKEN",
    "AUTH_DEV_HEADER",
    "AUTH_MEMBER_SESSION",
    "BearerTokenProvider",
    "DevHeaderProvider",
    "ForKhatriSessionProvider",
    "IdentityProvider",
    "ResolvedIdentity",
    "authenticate",
    "configured_providers",
    "register_provider",
]
