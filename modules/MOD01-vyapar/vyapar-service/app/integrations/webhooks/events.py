# [IMP37] The webhook event catalogue. Every type here is written to the
# transactional outbox either by publish_with_outbox() (operator events) or
# by migration 016's triggers (member events). "operator" events carry no
# audience and reach only an operator's all-events subscription.
from __future__ import annotations

from app.i18n import translate

# type -> (outbox source, operator_only)
EVENT_TYPES: dict[str, tuple[str, bool]] = {
    "opportunity.published": ("opportunity", False),
    "opportunity.reactivated": ("opportunity", False),
    "opportunity.paused": ("opportunity", False),
    "opportunity.stale": ("opportunity", False),
    "opportunity.expired": ("opportunity", False),
    "opportunity.closed": ("opportunity", False),
    "opportunity.removed": ("opportunity", False),
    "opportunity.queue_decided": ("opportunity", True),
    "listing.published": ("listing", False),
    "listing.suspended": ("listing", False),
    "listing.archived": ("listing", False),
    "listing.verification_verified": ("listing", False),
    "listing.verification_revoked": ("listing", False),
    "listing.verification_expired": ("listing", False),
    "taxonomy.changed": ("listing", True),
    "enquiry.received": ("enquiry", False),
    "enquiry.replied": ("enquiry", False),
    "enquiry.message_received": ("enquiry", False),
    "enquiry.state_changed": ("enquiry", False),
    "partnership.requested": ("enquiry", False),
    "partnership.accepted": ("enquiry", False),
    "partnership.declined": ("enquiry", False),
    "partnership.withdrawn": ("enquiry", False),
    "partnership.restricted": ("enquiry", False),
    "partnership.closed": ("enquiry", False),
    "review.published": ("review", False),
    "review.disputed": ("review", False),
    "review.hidden": ("review", False),
    "review.removed": ("review", False),
}

WILDCARD = "*"
PING = "ping"


def describe(event_type: str, lang: str) -> str:
    return translate(f"integrations.event.{event_type.replace('.', '_')}", lang)


def catalogue(lang: str) -> list[dict]:
    return [
        {"type": t, "operator_only": op, "description": describe(t, lang)}
        for t, (_, op) in EVENT_TYPES.items()
    ]
