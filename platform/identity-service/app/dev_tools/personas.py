"""Development personas: a small, named set of members to act as.

Ids were checked against `identity.member` (2026-09-14). `krishna` and `new-member`
are created by `scripts/seed_dev_members.py`; the others come from
`scripts/import_module_identities.py`. Module data belongs to the modules and is
not created here: Mangaly and Milavn create a member's link rows on first entry.
"""

from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

OWNER_MEMBER_ID = UUID("a0000000-0000-4000-8000-000000000001")
NEW_MEMBER_ID = UUID("a0000000-0000-4000-8000-000000000002")
MANGALY_PARENT_MEMBER_ID = UUID("a0000000-0000-4000-8000-000000000003")


@dataclass(frozen=True, slots=True)
class Persona:
    key: str
    member_id: UUID
    description: str
    for_automated_tests: bool


PERSONAS: tuple[Persona, ...] = (
    Persona(
        "krishna",
        OWNER_MEMBER_ID,
        "Product owner's own account (+919999900001). Never use in automated tests.",
        for_automated_tests=False,
    ),
    Persona(
        "asha",
        UUID("11111111-1111-1111-1111-111111111111"),
        "Asha Reddy: a Mangaly candidate profile and Milavn activity.",
        for_automated_tests=True,
    ),
    Persona(
        "new-member",
        NEW_MEMBER_ID,
        "A fresh member with no module data at seed time.",
        for_automated_tests=True,
    ),
    Persona(
        "mangaly-family",
        UUID("22222222-2222-2222-2222-222222222222"),
        "Vikram Rao: Home Circle family member on Asha's Mangaly profile; also in Milavn.",
        for_automated_tests=True,
    ),
    Persona(
        "mangaly-parent",
        MANGALY_PARENT_MEMBER_ID,
        "Lakshmi Reddy: Ananya Reddy's mother, a Mangaly Home Circle family member (not a candidate).",
        for_automated_tests=True,
    ),
    Persona(
        "milavn-moderator",
        UUID("99999999-9999-9999-9999-999999999999"),
        "Milavn Moderator: moderation scope granted by Milavn.",
        for_automated_tests=True,
    ),
)

BY_KEY = {persona.key: persona for persona in PERSONAS}
