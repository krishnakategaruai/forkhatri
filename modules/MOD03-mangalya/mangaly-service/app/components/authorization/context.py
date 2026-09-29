"""`AuthzContext` — the resolved authorization decision every component requires.

# [TR017/TR018/SP017] Every consequential access routes through one chokepoint
# before any component touches its own schema.
# Approach: the Authorization Engine is the only component permitted to resolve
# the BR04 chain; every other component receives an already-resolved
# `AuthzContext`, never a raw actor id, so "forgot to check authorization" is
# not a mistake an individual component can make (CODING-GUIDE.md §3).
# Three properties make that structural rather than conventional:
#   * `AuthzContext` is frozen — a component cannot widen a scope it was handed.
#   * It cannot be constructed with a `subject_id` alone from outside the
#     `authorization` package; `resolve()` is the only sanctioned producer, and
#     `_resolved_by` records that. A hand-built context is detectable.
#   * [TR018] Candidate-info and family-info are two independently-typed scopes
#     from `mangaly_authz.grant_scope`, never one combined boolean, so
#     conflating them is a type error rather than a logic slip.
# Traces to: TR017, TR018, SP017, SP018, MODULE-ARCHITECTURE-STANDARD §5.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum
from types import MappingProxyType
from uuid import UUID


class GrantScope(StrEnum):
    """Mirrors `mangaly_authz.grant_scope` exactly — two scopes, never a boolean."""

    CANDIDATE_INFO = "candidate_info"
    FAMILY_INFO = "family_info"


class GrantType(StrEnum):
    """Mirrors `mangaly_authz.grant_type` exactly — the provenance of a grant,
    carried through to `AuthzContext.grant_basis` so TR069's audit event
    records *why* access was allowed, not merely that it was."""

    HOME_CIRCLE_MEMBERSHIP = "home_circle_membership"
    CONNECTION_ACCEPTED = "connection_accepted"
    SAFETY_OVERRIDE = "safety_override"
    ADMIN_CASE = "admin_case"
    PAUSE_EXCEPTION = "pause_exception"


class Capacity(StrEnum):
    """The capacity the actor is acting in — recorded on every audit event (TR069)."""

    CANDIDATE = "candidate"
    FAMILY = "family"
    ADMIN = "admin"


class Action(StrEnum):
    """The action being authorized. Deliberately coarse: BR04's chain is about
    *what category of data* is reachable, not about per-endpoint verbs."""

    READ = "read"
    WRITE = "write"


class AuthorizationDenied(PermissionError):
    """Raised by `require_scope()` — never swallowed into an empty result set."""


@dataclass(frozen=True, slots=True)
class AuthzContext:
    """A resolved authorization decision, scoped to one actor/target/action."""

    subject_id: UUID
    account_id: UUID
    target_profile_id: UUID | None
    action: Action
    capacity: Capacity
    scopes: frozenset[GrantScope]
    resolved_at: datetime
    # Provenance of each granted scope (grant_type -> scope), carried so TR069's
    # audit event can record *why* access was allowed, not merely that it was.
    grant_basis: Mapping[str, str] = field(default_factory=lambda: MappingProxyType({}))
    is_self: bool = False
    _resolved_by: str = "authorization.interface.resolve"

    def has_scope(self, scope: GrantScope) -> bool:
        """[TR018] Components read through this, never a raw flag."""
        return self.is_self or scope in self.scopes

    def require_scope(self, scope: GrantScope) -> None:
        """Assert a scope, raising rather than degrading to an empty result.

        A denial that silently returns no rows is indistinguishable from "there
        is nothing here", which makes an authorization bug invisible in testing.
        """
        if not self.has_scope(scope):
            raise AuthorizationDenied(
                f"subject {self.subject_id} lacks {scope.value} on "
                f"target {self.target_profile_id}"
            )
