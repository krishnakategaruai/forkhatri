"""Hand-written event payload DTOs.

# [TR069/SP069] Audit events carry actor, capacity and the resolved
# authorization basis — never row contents.
# Approach: one small factory (`audit_payload`) all callers use, so the three
# fields SP069 requires cannot be forgotten one endpoint at a time, and nothing
# else can be smuggled in (`events.bus.publish` rejects non-scalar values).
# Traces to: TR069, SP069.

# [TR081/SP081] `mangaly.activity_summary` — the module's ONLY cross-boundary
# data flow — is an explicit, hand-written allow-list DTO with no serializer
# reflection over the domain model.
# Approach: SP081 calls this "the highest-value finding in this cluster" and is
# specific about why a normal serializer is unacceptable: the realistic failure
# is a future field added to the domain object silently appearing in the
# published event, and once on the broker it is unrecallable. So this DTO
#   * lists its fields literally, as a frozen dataclass with `slots=True` (an
#     attribute that is not declared cannot be set at all);
#   * builds its payload in an explicit dict literal rather than `asdict()`,
#     `__dict__`, or `model_dump()` — there is no reflection anywhere in the
#     path, which is what makes "a new domain field cannot leak" true by
#     construction rather than by review;
#   * exposes `ALLOW_LIST` so SP081's required build-blocking contract test
#     asserts against a declared constant rather than re-deriving the expected
#     field set from the same code it is testing.
# Traces to: TR081, SP081, ARCHITECTURE.md (Mangaly -> MOD05 Dashboard edge).
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any, Final
from uuid import UUID

from app.components.authorization.context import AuthzContext


def audit_payload(
    authz: AuthzContext,
    *,
    extra_identifiers: Mapping[str, UUID | str | int | bool | None] | None = None,
) -> dict[str, Any]:
    """[TR069/SP069] Build the actor/capacity/authorization-basis payload.

    `extra_identifiers` is for identifiers only (a report id, a connection id).
    `events.bus.publish` rejects anything that is not a scalar or UUID, so a
    caller cannot widen this into a row dump.
    """
    payload: dict[str, Any] = {
        "actor_subject_id": authz.subject_id,
        "actor_account_id": authz.account_id,
        "capacity": authz.capacity.value,
        "action": authz.action.value,
        "target_profile_id": authz.target_profile_id,
        # The resolved basis, so the trail records *why* access was allowed.
        "authz_scopes": sorted(scope.value for scope in authz.scopes),
        "authz_is_self": authz.is_self,
        "authz_resolved_at": authz.resolved_at.isoformat(),
    }
    if extra_identifiers:
        overlap = set(extra_identifiers) & set(payload)
        if overlap:
            raise ValueError(f"extra_identifiers may not shadow audit fields: {sorted(overlap)}")
        payload.update(extra_identifiers)
    return payload


# --- TR081/SP081: the cross-boundary activity-summary contract ----------------

ACTIVITY_SUMMARY_EVENT_TYPE: Final[str] = "mangaly.activity_summary"

# The complete, closed set of keys that may ever appear on this event. SP081
# requires an automated contract test to assert the published payload against
# exactly this and fail the build on any addition.
ACTIVITY_SUMMARY_ALLOW_LIST: Final[frozenset[str]] = frozenset(
    {
        "event_type",
        "schema_version",
        "account_id",
        "lifecycle_state",
        "previous_lifecycle_state",
        "occurred_at",
    }
)


@dataclass(frozen=True, slots=True)
class ActivitySummaryEvent:
    """The only Mangaly payload that leaves the module's isolation boundary.

    Deliberately carries no profile name, no match, no connection, no counterparty
    and no free-text field of any kind. `lifecycle_state` is a closed vocabulary
    from `mangaly_lifecycle`, not user-supplied content.
    """

    account_id: UUID
    lifecycle_state: str
    previous_lifecycle_state: str | None
    occurred_at: datetime
    schema_version: int = 1

    def to_payload(self) -> dict[str, Any]:
        """Explicit dict literal — no `asdict`, no `__dict__`, no reflection.

        If a field is added to this dataclass and not added here, it does NOT
        get published. That asymmetry is intentional: the safe failure is
        omission, never accidental disclosure.
        """
        payload = {
            "event_type": ACTIVITY_SUMMARY_EVENT_TYPE,
            "schema_version": self.schema_version,
            "account_id": self.account_id,
            "lifecycle_state": self.lifecycle_state,
            "previous_lifecycle_state": self.previous_lifecycle_state,
            "occurred_at": self.occurred_at.astimezone(UTC).isoformat(),
        }
        # Belt and braces: assert the produced payload against the declared
        # allow-list at runtime too, so a mistake here fails at publish time in
        # any environment, not only when the CI contract test happens to run.
        unexpected = set(payload) - ACTIVITY_SUMMARY_ALLOW_LIST
        if unexpected:
            raise ValueError(
                f"activity_summary payload contains non-allow-listed field(s) "
                f"{sorted(unexpected)} — this event crosses Mangaly's isolation "
                "boundary and is unrecallable once published (SP081)."
            )
        return payload
