# [DEV STAND-IN — NOT a council register] Answers every lookup with
# "not checked". It exists so the whole claim -> check -> badge path runs in
# development without inventing a result. A real adapter replaces it by name
# (CREDENTIAL_REGISTRY) once a register or DigiLocker access is contracted.
from __future__ import annotations

from app.integrations.credentials.base import CredentialClaim, RegistryResult


class DevStubRegistry:
    name = "dev_stub"

    async def check(self, claim: CredentialClaim) -> RegistryResult:
        return RegistryResult(outcome="not_checked", source="dev_stub", checked_at=None, detail="no_registry_connected")
