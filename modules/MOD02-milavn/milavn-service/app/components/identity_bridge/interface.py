"""Identity Bridge — thin, schema-less (architecture.md §2.1).

# [FR076-FR080, FR088, TR46, TR47, ADR-004] Authentication is owned by the
# parent ForKhatri platform's Identity & Trust Service. This module never
# stores credentials, sessions, OTPs or identity data — it holds a
# `member_id` reference and resolves display facts through this bridge.
# Approach: until the platform wiring lands, a development stand-in resolves
# the `X-Milavn-Member-Id` header against `config/dev_identities.json`. The
# public interface (`resolve`, `display_names_for`) is the same shape the
# real bridge will keep, so swapping the stub for a platform call is a change
# inside this package only.
# Traces to: TR46, TR47, TR01, architecture.md §1 (Identity & Trust edge).
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from functools import cache
from uuid import UUID

from app.config.settings import get_settings


@dataclass(frozen=True, slots=True)
class MemberIdentity:
    member_id: UUID
    display_name: str
    handle: str
    avatar: str | None
    identity_level: int
    scopes: tuple[str, ...]

    @property
    def is_moderator(self) -> bool:
        return "milavn.moderate" in self.scopes


@cache
def _registry() -> dict[UUID, MemberIdentity]:
    settings = get_settings()
    if not settings.dev_identity_enabled:
        return {}
    data = json.loads(settings.dev_identities_path.read_text(encoding="utf-8"))
    out: dict[UUID, MemberIdentity] = {}
    for m in data["members"]:
        mid = UUID(m["member_id"])
        out[mid] = MemberIdentity(
            member_id=mid,
            display_name=m["display_name"],
            handle=m["handle"],
            avatar=m.get("avatar"),
            identity_level=int(m.get("identity_level", 0)),
            scopes=tuple(m.get("scopes", [])),
        )
    return out


def resolve(member_id: UUID) -> MemberIdentity | None:
    return _registry().get(member_id)


def list_dev_members() -> list[MemberIdentity]:
    return list(_registry().values())


def display_names_for(member_ids: list[UUID]) -> dict[UUID, MemberIdentity]:
    reg = _registry()
    result: dict[UUID, MemberIdentity] = {}
    for mid in member_ids:
        ident = reg.get(mid)
        if ident is None:
            ident = MemberIdentity(mid, "Community member", "member", None, 0, ())
        result[mid] = ident
    return result
