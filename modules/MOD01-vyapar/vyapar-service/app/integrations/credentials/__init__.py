# [Trust pack, 2026-09-30] Council / register lookups behind one interface.
#
# `CredentialRegistry.check(claim)` asks a register whether a claimed number
# is real and current. Real registers (ICAI "Trace a Member", NMC / state
# medical councils, NCAHP, State Bar Councils, Council of Architecture,
# DigiLocker via API Setu) are vendor integrations logged as blockers in
# 09a-external-dependencies.md; no official lookup API was verified for any
# of them except DigiLocker's requester API, which needs registration.
#
# Until one is wired, `DevStubRegistry` answers every check with
# `outcome="not_checked", source="dev_stub"`. It never says "verified":
# the badge then reads "Pending check" until an operator checks the public
# register by hand through the existing verification queue. Configuration
# picks the adapter (CREDENTIAL_REGISTRY in .env); an unknown name falls
# back to the stub rather than pretending.
from __future__ import annotations

from app.integrations.credentials.base import CredentialClaim, CredentialRegistry, RegistryResult
from app.integrations.credentials.dev_stub import DevStubRegistry

_REGISTRIES: dict[str, type[CredentialRegistry]] = {"dev_stub": DevStubRegistry}


def get_registry() -> CredentialRegistry:
    from app.config import get_settings

    cls = _REGISTRIES.get((get_settings().credential_registry or "dev_stub").strip().lower(), DevStubRegistry)
    return cls()


__all__ = ["CredentialClaim", "CredentialRegistry", "RegistryResult", "DevStubRegistry", "get_registry"]
