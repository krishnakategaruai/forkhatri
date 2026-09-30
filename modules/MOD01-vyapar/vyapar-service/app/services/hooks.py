# [IMP-B, 2026-09-28] Extension points between services owned by different
# workstreams.
#
# Why this file exists: several rules that belong to trust & safety,
# reputation or contact control must run inside flows another team owns
# (opportunity create/publish, the opportunity detail read, the enquiry
# read). Rather than editing those files, the owning service registers a
# small callable here, and the flow's owner adds ONE call to the matching
# `run_*` helper when they are ready. Until then the registered checks are
# also reachable through their own endpoints, so nothing depends on timing.
#
# Registries (all lists; append, never replace):
#   SEEKER_CHARGE_CHECKS   — `check(text: str, structured: dict, lang: str) -> None`
#                            raises ApiError when a job seeker would be
#                            charged. Called from opportunity create/patch/
#                            publish via `run_seeker_charge_checks(...)`.
#   OPPORTUNITY_ENRICHERS  — `async enrich(conn, ctx, lang, opportunity: dict) -> dict`
#                            returns extra keys to merge into an opportunity
#                            detail response (seeker_protection, poster
#                            badges). Called via `run_opportunity_enrichers`.
#   ENQUIRY_ENRICHERS      — `async enrich(conn, ctx, lang, enquiry: dict) -> dict`
#                            returns extra keys for an enquiry thread read
#                            (contact_actions, contact_attempts). Called via
#                            `run_enquiry_enrichers`.
#
# How the opportunities owner wires it (two lines, no import cycle: this
# module imports nothing from the services):
#
#     from app.services import hooks
#     hooks.run_seeker_charge_checks(
#         text=" ".join(filter(None, [body.title, body.description, body.requirements, body.compensation])),
#         structured=body.model_dump(), lang=lang)
#
# and for a detail read:
#
#     extra = await hooks.run_opportunity_enrichers(conn, ctx, lang, out.model_dump())
#
# Registration happens at import time of the owning service
# (`app.services.trust_safety`, `app.services.contact`); every `run_*`
# helper also imports them on first use, so the lists are never empty.
from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import Any

SeekerChargeCheck = Callable[[str, dict[str, Any], str], None]
Enricher = Callable[..., Awaitable[dict[str, Any]]]

SEEKER_CHARGE_CHECKS: list[SeekerChargeCheck] = []
OPPORTUNITY_ENRICHERS: list[Enricher] = []
ENQUIRY_ENRICHERS: list[Enricher] = []


def register_seeker_charge_check(fn: SeekerChargeCheck) -> SeekerChargeCheck:
    if fn not in SEEKER_CHARGE_CHECKS:
        SEEKER_CHARGE_CHECKS.append(fn)
    return fn


def register_opportunity_enricher(fn: Enricher) -> Enricher:
    if fn not in OPPORTUNITY_ENRICHERS:
        OPPORTUNITY_ENRICHERS.append(fn)
    return fn


def register_enquiry_enricher(fn: Enricher) -> Enricher:
    if fn not in ENQUIRY_ENRICHERS:
        ENQUIRY_ENRICHERS.append(fn)
    return fn


_REGISTRANTS = ("app.services.trust_safety", "app.services.contact", "app.reputation",
                # [Trust pack] paid on time, restriction + appeal path, applicants still waiting
                "app.services.paid_on_time", "app.services.restrictions", "app.services.close_loop")


def _ensure_registered() -> None:
    """Imports the owning services once, so a caller that runs a hook before
    anything else imported them (a script, a worker, an early import order)
    still gets every registered check. Imported lazily to avoid a cycle:
    trust_safety reads opportunities, which will call these helpers."""
    import importlib

    for name in _REGISTRANTS:
        importlib.import_module(name)


def run_seeker_charge_checks(text: str, structured: dict[str, Any] | None, lang: str) -> None:
    """Raises the first registered check's ApiError; returns None when clean."""
    _ensure_registered()
    for check in SEEKER_CHARGE_CHECKS:
        check(text or "", structured or {}, lang)


async def run_opportunity_enrichers(conn, ctx, lang: str, opportunity: dict[str, Any]) -> dict[str, Any]:
    _ensure_registered()
    extra: dict[str, Any] = {}
    for enrich in OPPORTUNITY_ENRICHERS:
        extra.update(await enrich(conn, ctx, lang, opportunity))
    return extra


async def run_enquiry_enrichers(conn, ctx, lang: str, enquiry: dict[str, Any]) -> dict[str, Any]:
    _ensure_registered()
    extra: dict[str, Any] = {}
    for enrich in ENQUIRY_ENRICHERS:
        extra.update(await enrich(conn, ctx, lang, enquiry))
    return extra
