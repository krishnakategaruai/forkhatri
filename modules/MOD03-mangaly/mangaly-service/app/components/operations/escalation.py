"""Tier 3/4 exits: on-call paging and the CSAM report packet (DEC-V1-009/011).

# [TR065/SP065] The taxonomy's most severe exits must be built integrations,
# not policy text. This module is where a Tier 3/4 classification leaves the
# database: `page_for_case()` fires the pager and records
# `mangaly_operations.paging_event`; `assemble_csam_packet()` builds the
# DEC-V1-011 field-schema packet into `csam_report_packet`.
#
# Vendor calls are behind a `Pager` protocol. `PagerDutyPager` speaks the
# Events API v2 (`routing_key`, `event_action: trigger`, `dedup_key`); it is
# used only when PAGERDUTY_ROUTING_KEY holds a real value. Otherwise
# `LogOnlyPager` records the page in the log and in the table with
# dispatch_status='logged' — so development never makes a network call and
# the exit is still visible as data. The same rule applies to the CSAM
# channel: a placeholder endpoint means the packet is stored for manual
# portal submission (CSAM_REPORT_FALLBACK_MODE) and the pager is fired, which
# is exactly what a human then acts on.
#
# Summaries carry event type and identifiers only, never content (SP098).
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any, Protocol
from uuid import UUID

import httpx
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.config.paging import PAGING_TRIGGER_TIERS, PagingTrigger
from app.config.settings import Settings, get_settings
from app.config.thresholds import SafetyTier
from app.events import bus

logger = logging.getLogger(__name__)

__all__ = [
    "LogOnlyPager",
    "PageResult",
    "Pager",
    "PagerDutyPager",
    "assemble_csam_packet",
    "get_pager",
    "page_for_case",
]


def _is_placeholder(value: str | None) -> bool:
    return not value or "CHANGE_ME" in value


@dataclass(frozen=True, slots=True)
class PageResult:
    vendor: str
    vendor_ref: str | None
    status: str  # 'sent' | 'logged' | 'failed'


class Pager(Protocol):
    vendor: str

    async def page(self, trigger: PagingTrigger) -> PageResult: ...


class LogOnlyPager:
    """Development / no-key fallback: the page is a log line and a table row."""

    vendor = "log_only"

    async def page(self, trigger: PagingTrigger) -> PageResult:
        logger.warning(
            "ON-CALL PAGE (log only; PAGERDUTY_ROUTING_KEY not configured): tier=%s case=%s dedup=%s",
            int(trigger.tier),
            trigger.case_id,
            trigger.dedup_key,
        )
        return PageResult(self.vendor, None, "logged")


class PagerDutyPager:
    """PagerDuty Events API v2 `trigger` event."""

    vendor = "pagerduty"

    def __init__(self, *, routing_key: str, events_api_url: str, timeout_seconds: float = 5.0) -> None:
        self._routing_key = routing_key
        self._url = events_api_url
        self._timeout = timeout_seconds

    async def page(self, trigger: PagingTrigger) -> PageResult:
        body = {
            "routing_key": self._routing_key,
            "event_action": "trigger",
            "dedup_key": trigger.dedup_key,
            "payload": {
                "summary": trigger.summary,
                "severity": "critical" if trigger.tier is SafetyTier.CRITICAL else "error",
                "source": "mangaly-service",
                "component": "safety_intelligence",
                "group": "mangaly-safety",
                "class": f"tier-{int(trigger.tier)}",
                "custom_details": {"case_id": trigger.case_id},
            },
        }
        try:
            async with httpx.AsyncClient(timeout=self._timeout) as client:
                response = await client.post(self._url, json=body)
            if response.status_code // 100 == 2:
                ref = str(response.json().get("dedup_key") or trigger.dedup_key)
                return PageResult(self.vendor, ref, "sent")
            logger.error("PagerDuty rejected page for case %s: %s", trigger.case_id, response.status_code)
            return PageResult(self.vendor, None, "failed")
        except httpx.HTTPError as exc:
            logger.error("PagerDuty unreachable for case %s: %s", trigger.case_id, exc)
            return PageResult(self.vendor, None, "failed")


def get_pager(settings: Settings | None = None) -> Pager:
    settings = settings or get_settings()
    if settings.paging_vendor == "pagerduty" and not _is_placeholder(settings.pagerduty_routing_key):
        return PagerDutyPager(
            routing_key=settings.pagerduty_routing_key,
            events_api_url=settings.pagerduty_events_api_url,
        )
    return LogOnlyPager()


async def page_for_case(
    session: AsyncSession,
    *,
    case_id: UUID,
    tier: SafetyTier,
    reference: str,
    pager: Pager | None = None,
) -> UUID | None:
    """Fire the on-call page for a Tier 3/4 case and record it. Returns the
    paging_event id, or None when the tier does not page (never raises on a
    vendor failure: the failure is recorded as dispatch_status='failed')."""
    if tier not in PAGING_TRIGGER_TIERS:
        return None
    trigger = PagingTrigger(
        case_id=str(case_id),
        tier=tier,
        dedup_key=f"mangaly-safety-case-{case_id}",
        summary=f"Mangaly safety Tier {int(tier)} case {case_id} ({reference})",
    )
    result = await (pager or get_pager()).page(trigger)
    event_id = (
        await session.execute(
            text(
                "SELECT mangaly_operations.record_paging_event(:case_id, :tier, :vendor, :ref, :dedup, :status, :summary)"
            ),
            {
                "case_id": case_id,
                "tier": int(tier),
                "vendor": result.vendor,
                "ref": result.vendor_ref,
                "dedup": trigger.dedup_key,
                "status": result.status,
                "summary": trigger.summary,
            },
        )
    ).scalar_one()
    await bus.publish(
        session,
        schema="mangaly_operations",
        aggregate_id=case_id,
        event_type="OnCallPaged",
        payload={
            "case_id": str(case_id),
            "tier": int(tier),
            "vendor": result.vendor,
            "dispatch_status": result.status,
            "paging_event_id": str(event_id),
        },
    )
    return event_id


async def assemble_csam_packet(
    session: AsyncSession,
    *,
    case_id: UUID,
    report_id: UUID,
    reported_account_id: UUID,
    conversation_id: UUID | None,
    message_id: UUID | None,
    detection_signal_id: UUID | None,
    detection_category: str,
    classified_at: datetime,
    settings: Settings | None = None,
) -> UUID:
    """Build the DEC-V1-011 packet (pointers and provenance only — never the
    material inlined) and store it. Dispatch follows CSAM_REPORT_FALLBACK_MODE:
    with no real endpoint configured the packet is stored for manual portal
    submission; the pager for the same case is fired by the caller."""
    settings = settings or get_settings()
    context_row = (
        await session.execute(
            text("SELECT mangaly_operations.packet_context(:account, :conversation)"),
            {"account": reported_account_id, "conversation": conversation_id},
        )
    ).scalar_one_or_none()
    context: dict[str, Any]
    if isinstance(context_row, dict):
        context = context_row
    elif isinstance(context_row, str):
        context = json.loads(context_row)
    else:
        context = {}

    payload: dict[str, Any] = {
        "reporting_platform": {
            "mangaly_case_id": str(case_id),
            "classification_timestamp": classified_at.isoformat(),
            "reporting_component": "safety_intelligence",
        },
        "reported_account": {
            "account_id": str(reported_account_id),
            "profile_id": context.get("profile_id"),
            "phone_identifier": context.get("phone_identifier"),
            "email_identifier": context.get("email_identifier"),
            "account_created_at": context.get("account_created_at"),
            "identifier_verified_at": context.get("identifier_verified_at"),
        },
        "associated_context": {
            "connection_id": context.get("connection_id"),
            "conversation_id": str(conversation_id) if conversation_id else None,
        },
        "capture_provenance": {
            "detection_signal_id": str(detection_signal_id) if detection_signal_id else None,
            "detected_at": classified_at.isoformat(),
            "ip_address_at_send": None,  # not carried in session data today
            "client_platform": "web",
        },
        "flagged_content_reference": {
            "report_id": str(report_id),
            "message_id": str(message_id) if message_id else None,
            "evidence_document_ref": f"mangaly_safety.report:{report_id}#evidence",
        },
        "incident_summary": {
            "severity_tier": 4,
            "detection_category": detection_category,
            "human_reviewer_summary": None,  # filled by the reviewer who confirms, never generated
        },
        "reporting_channel": {
            "reported_to": None,
            "reported_at": None,
            "reporting_reference_id": None,
        },
    }

    mode = settings.csam_report_fallback_mode
    if _is_placeholder(settings.csam_report_endpoint) or _is_placeholder(settings.csam_report_api_key):
        dispatch_status = "stored_for_manual_portal"
        submitted_to = "cybercrime_portal"
    else:
        # A programmatic channel is configured. cybercrime.gov.in's submission
        # mechanism is unconfirmed (DEC-V1-011 blocker), so no network call is
        # made here; the packet is stored and flagged for the configured
        # dispatcher to pick up.
        dispatch_status = "pending_dispatch"
        submitted_to = "cybercrime_portal"

    packet_id = (
        await session.execute(
            text(
                "SELECT mangaly_operations.store_csam_packet(:case_id, CAST(:payload AS jsonb), :to, :mode, :status)"
            ),
            {
                "case_id": case_id,
                "payload": json.dumps(payload, default=str),
                "to": submitted_to,
                "mode": mode,
                "status": dispatch_status,
            },
        )
    ).scalar_one()
    logger.warning(
        "CSAM packet %s assembled for case %s (mode=%s status=%s)", packet_id, case_id, mode, dispatch_status
    )
    await bus.publish(
        session,
        schema="mangaly_operations",
        aggregate_id=case_id,
        event_type="CsamPacketAssembled",
        payload={
            "case_id": str(case_id),
            "packet_id": str(packet_id),
            "dispatch_mode": mode,
            "dispatch_status": dispatch_status,
            "assembled_at": datetime.now(UTC).isoformat(),
        },
    )
    return packet_id
