from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from typing import Literal, Protocol

Outcome = Literal["verified", "not_found", "lapsed", "not_checked", "error"]


@dataclass(frozen=True)
class CredentialClaim:
    credential_type: str        # icai_membership | medical_council_registration | ...
    council: str                # the register, e.g. "Bar Council of Telangana"
    registration_number: str
    holder_name: str            # the profile's person, to compare with the register
    registered_on: date | None = None
    document_uri: str | None = None


@dataclass(frozen=True)
class RegistryResult:
    outcome: Outcome
    source: Literal["dev_stub", "registry"]
    checked_at: datetime | None     # None when nothing was actually checked
    register_name: str | None = None  # the name on the register, when a lookup returned one
    detail: str | None = None       # a short machine reason (never shown raw)


class CredentialRegistry(Protocol):
    name: str

    async def check(self, claim: CredentialClaim) -> RegistryResult:
        """Look the claim up. Must return outcome="not_checked" (never
        "verified") when no real lookup happened."""
        ...
