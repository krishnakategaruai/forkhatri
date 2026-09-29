# [IMP-ADMIN — Admin & Governance Console, ADR-012 / TR-PLAT-01] Host admin
# scopes -> Vyapar operator permissions.
#
# The host platform grants console access as scopes on the resolved session
# (ForKhatri: `admin_scopes` in POST /internal/v1/sessions/resolve). Vyapar's
# own authorization — the route chokepoints and the RLS helper
# vyapar_identity.is_operator(permission) — speaks five permission names, the
# same ones members.operator_permissions holds. This table is the one place
# the two vocabularies meet; the core never reads a host scope name.
#
# Unknown scopes are ignored (another module's `milavn.moderate`, or a scope
# Vyapar does not know yet), so a host adding scopes can never widen Vyapar
# access by accident.
from __future__ import annotations

from collections.abc import Iterable

SCOPE_MODERATE = "vyapar.moderate"
SCOPE_VERIFY = "vyapar.verify"
SCOPE_COMMERCIAL = "vyapar.commercial"
SCOPE_ANALYTICS = "vyapar.analytics"

ADMIN_SCOPE_PERMISSIONS: dict[str, frozenset[str]] = {
    SCOPE_MODERATE: frozenset({"moderation", "content"}),
    SCOPE_VERIFY: frozenset({"verification"}),
    SCOPE_COMMERCIAL: frozenset({"commercial"}),
    SCOPE_ANALYTICS: frozenset({"analytics"}),
}

# The permission names the database accepts (members.operator_permissions
# CHECK and vyapar_identity.session_permissions()).
OPERATOR_PERMISSIONS: frozenset[str] = frozenset({"verification", "content", "commercial", "analytics", "moderation"})


def permissions_for_scopes(scopes: Iterable[str] | None) -> frozenset[str]:
    if not scopes:
        return frozenset()
    granted: set[str] = set()
    for scope in scopes:
        if isinstance(scope, str):
            granted |= ADMIN_SCOPE_PERMISSIONS.get(scope.strip(), frozenset())
    return frozenset(granted)


def parse_scope_list(value: str | None) -> list[str]:
    """`"vyapar.moderate, vyapar.verify"` -> ["vyapar.moderate", "vyapar.verify"]."""
    return [s.strip() for s in (value or "").split(",") if s.strip()]
