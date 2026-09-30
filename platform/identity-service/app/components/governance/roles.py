"""The role catalogue of the Admin & Governance Console.

A role is held over an area (scope) for a term:
  platform  national office bearers and platform staff, over the whole of ForKhatri
  chapter   a state or city chapter of the samaj (and the chapters under it)
  module    one module (Mangalya, Milavn, Vyapar, ...)

Nobody has any administrative power by default. Roles are code, not rows, so the
permission each role carries is reviewed like any other change. Researched against
Google Workspace (role + organisational unit), Slack (owner / admin / narrow system
roles), Facebook Groups (admin vs moderator), Discourse (staff vs moderators) and
Rotary / Lions district structures (office bearers with yearly terms).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

ScopeKind = Literal["platform", "module", "chapter"]

# Platform permissions. Module permissions are "<module>.<action>" (see MODULE_ACTIONS).
MEMBERS_VIEW = "members.view"
MEMBERS_CONTACT = "members.contact"  # see a member's full phone and email (each view is audited)
MEMBERS_SUSPEND = "members.suspend"  # time-boxed suspension, lift, sign out everywhere
MEMBERS_BAN = "members.ban"  # propose a permanent ban (always needs a second person)
ROLES_VIEW = "roles.view"
ROLES_MANAGE = "roles.manage"
APPROVALS_DECIDE = "approvals.decide"
ORG_VIEW = "org.view"
ORG_MANAGE = "org.manage"
CHAPTER_MANAGE = "chapter.manage"  # appoint office bearers inside one's own chapter
AUDIT_VIEW = "audit.view"
MODULES_MANAGE = "modules.manage"

ALL_PERMISSIONS = (
    MEMBERS_VIEW,
    MEMBERS_CONTACT,
    MEMBERS_SUSPEND,
    MEMBERS_BAN,
    ROLES_VIEW,
    ROLES_MANAGE,
    APPROVALS_DECIDE,
    ORG_VIEW,
    ORG_MANAGE,
    CHAPTER_MANAGE,
    AUDIT_VIEW,
    MODULES_MANAGE,
)

# What a module lets the console do. A module's own chokepoint still decides; the
# platform only says who the samaj has appointed (identity resolve → admin_scopes).
# "commercial": each module's own pricing tiers, orders and refunds. Tiers differ per
# module and stay module data (PRODUCT-GUARDRAILS); the platform only appoints who may see them.
MODULE_ACTIONS = ("moderate", "verify", "commercial")


@dataclass(frozen=True, slots=True)
class Role:
    key: str
    scope_kind: ScopeKind
    permissions: tuple[str, ...]
    module_actions: tuple[str, ...] = ()
    # Granting a sensitive role needs a second person unless an owner grants it.
    sensitive: bool = False


_OFFICE = (
    MEMBERS_VIEW,
    MEMBERS_SUSPEND,
    MEMBERS_BAN,
    ROLES_VIEW,
    ROLES_MANAGE,
    APPROVALS_DECIDE,
    ORG_VIEW,
    ORG_MANAGE,
    AUDIT_VIEW,
)

ROLES: dict[str, Role] = {
    r.key: r
    for r in (
        Role("owner", "platform", ALL_PERMISSIONS, MODULE_ACTIONS, sensitive=True),
        Role("president", "platform", _OFFICE, ("moderate",), sensitive=True),
        Role("secretary", "platform", _OFFICE, ("moderate",), sensitive=True),
        Role("treasurer", "platform", (MEMBERS_VIEW, ORG_VIEW, AUDIT_VIEW), ("commercial",), sensitive=True),
        Role(
            "grievance_officer",
            "platform",
            (MEMBERS_VIEW, MEMBERS_CONTACT, MEMBERS_SUSPEND, MEMBERS_BAN, APPROVALS_DECIDE, ORG_VIEW, AUDIT_VIEW),
            ("moderate",),
            sensitive=True,
        ),
        Role("data_protection_officer", "platform", (MEMBERS_VIEW, MEMBERS_CONTACT, AUDIT_VIEW), sensitive=True),
        Role("auditor", "platform", (MEMBERS_VIEW, ROLES_VIEW, ORG_VIEW, AUDIT_VIEW)),
        Role("chapter_head", "chapter", (ORG_VIEW, ROLES_VIEW, CHAPTER_MANAGE)),
        Role("chapter_secretary", "chapter", (ORG_VIEW, ROLES_VIEW)),
        Role("moderator", "module", (MEMBERS_VIEW,), ("moderate",)),
        Role("verifier", "module", (), ("verify",)),
    )
}

# The order the console lists roles in: national office first, then staff, chapters, modules.
ROLE_ORDER = tuple(ROLES)

# Codes every suspension, ban and approval must carry. The console shows each in the
# reader's language; free text goes in the note beside it.
REASON_CODES = (
    "harassment",
    "fraud_scam",
    "fake_profile",
    "impersonation",
    "inappropriate_content",
    "underage",
    "spam",
    "safety_threat",
    "legal_order",
    "member_request",
    "other",
)

SUSPENSION_DAYS = (1, 3, 7, 30)
