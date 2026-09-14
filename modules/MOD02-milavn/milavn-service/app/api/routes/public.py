"""Public page endpoints — FR046, FR047, FR048, FR049, FR050.

# [TR33/TR34/TR36] The public Occurrence page is served without login; the
# response carries all eight required content elements (TR34's fixed
# contract) so the web app's server-rendered route emits meaningful HTML and
# SEO metadata on first paint (FR048). A non-public item is a 404, never a
# 403 that confirms existence (FR050) — enforced by RLS underneath as well.
# Traces to: TR33, TR34, TR35, TR36.
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

from app.api.deps import DbSession, Locale, OptionalMember
from app.api.schemas import CardOut
from app.components.activity import interface as activity
from app.components.discovery import interface as discovery
from app.components.identity_bridge import interface as identity
from app.components.trust import interface as trust
from app.i18n import translate

router = APIRouter(prefix="/public", tags=["public"])

SAFETY_GUIDELINES = [
    "Tell someone where you're going and when you expect to be back.",
    "Meet at the stated public place first; the organizer's identity is visible to you as an RSVP'd participant.",
    "Carry water, basic first aid, and a charged phone.",
    "If anything feels off, leave — and report it from the activity page.",
]


class PublicPage(BaseModel):
    """[FR047] Eight required elements: title, description, time/location, organizer identity+trust,
    capacity/spots, safety guidelines (if high-risk), RSVP CTA, share affordances."""

    card: CardOut
    description: str | None
    organizer: dict
    capacity: int | None
    spots_left: int | None
    safety_guidelines: list[str]
    rsvp_cta: dict
    share: dict
    seo: dict
    series: dict | None
    viewer_role: str | None


@router.get("/occurrences/{slug}", response_model=PublicPage)
async def public_occurrence(slug: str, session: DbSession, member: OptionalMember, lang: Locale) -> PublicPage:
    try:
        occ = await activity.get_by_slug(session, slug=slug)
    except activity.OccurrenceNotFound as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=translate("occurrence.notFound", lang)) from exc
    # [FR050] Only public-marked items have a reachable public page; an
    # authenticated member who can see a circle-scoped item still gets it via
    # the authenticated route, never here.
    if occ.visibility_scope != "public" and member is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=translate("occurrence.notFound", lang))
    v = await discovery.viewer_profile(session, member.member_id) if member else None
    cards = await discovery.build_cards(session, [occ], v, rank=False)
    card = CardOut.from_card(cards[0])
    host = identity.display_names_for([occ.creator_member_id])[occ.creator_member_id]
    org_trust = await trust.trust_for(session, subject_type="organizer", subject_id=occ.creator_member_id)
    org_labels = trust.label_text(await trust.reputation_labels(session, member_id=occ.creator_member_id))
    series = None
    if occ.activity_id:
        series = await activity.series_summary(session, activity_id=occ.activity_id)
        series["first_at"] = series["first_at"].isoformat() if series.get("first_at") else None
    role = None
    if member:
        from app.components.authorization import interface as authz

        role = (await authz.occurrence_role(session, occurrence_id=occ.id, member_id=member.member_id)).value
    share_path = f"/a/{occ.canonical_url_slug}"
    return PublicPage(
        card=card,
        description=occ.description,
        organizer={
            "display_name": host.display_name,
            "avatar": host.avatar,
            "trust_label": org_trust.label,
            "trust_level": org_trust.level,
            "trust_positive": org_trust.positive,
            "reputation": org_labels,
            "member_id": str(occ.creator_member_id),
        },
        capacity=occ.capacity,
        spots_left=card.spots_left,
        safety_guidelines=SAFETY_GUIDELINES if occ.high_risk else [],
        rsvp_cta={"authenticated": member is not None, "viewer_status": card.viewer_status},
        share={
            "path": share_path,
            "channels": ["whatsapp", "instagram", "sms", "email", "copy", "qr"],
            "text": f"{occ.title} — {card.location_label}. Join me on Milavn.",
        },
        seo={
            "title": f"{occ.title} · Milavn",
            "description": (occ.description or f"{card.category_label} in {card.location_label}, hosted by {host.display_name}.")[:160],
            "image": card.cover_image_url,
        },
        series=series,
        viewer_role=role,
    )
