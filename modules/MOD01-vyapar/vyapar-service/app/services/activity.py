# [TR055] Activity screen's groups (FR55) — moved out of the feed module in
# Refactor A so the Activity capability has its own service.
# Traces to: FR23, FR26, FR27, FR55, TR055
from __future__ import annotations

import asyncpg
from pydantic import BaseModel

from app.identity import AuthzContext


# ---------------------------------------------------------------------------
# [TR055] Activity — six groups via one parameterized query pattern over
# member_opportunity/member_listing, not six separately-built endpoints.
# Traces to: FR55, TR055
# ---------------------------------------------------------------------------
class ActivityItem(BaseModel):
    kind: str  # "listing" | "opportunity"
    id: str
    title: str
    group: str
    # [Real gap found via third critique pass, fixed here] rows carried no
    # status at all — every other list in the app (Enquiries, Businesses,
    # Discover) resolves a real lifecycle state to a translated label; this
    # was the one list that didn't. Each kind's own real state column now
    # travels through (opportunity: active/paused/stale/expired/closed/
    # removed; listing: draft/pending_review/active_unverified/
    # active_verified/suspended/archived; enquiry: FR23's states;
    # partnership: FR25/26's states) — the frontend resolves it via each
    # kind's own existing state-label map, never a second one here.
    status: str | None = None


class ActivityResponse(BaseModel):
    saved: list[ActivityItem]
    posted: list[ActivityItem]
    recently_viewed: list[ActivityItem]
    shared: list[ActivityItem]
    completed: list[ActivityItem]
    responded: list[ActivityItem] = []
    to_review: list[ActivityItem] = []  # [FR27] open review invites — "Write a review" rows
    partnerships: list[ActivityItem] = []  # [FR26] "Accepted requests appear in Activity"


async def get_activity(
    conn: asyncpg.Connection,
    ctx: AuthzContext,
) -> ActivityResponse:
    opp_rows = await conn.fetch(
        """SELECT mo.*, o.title, o.state AS opp_state FROM vyapar_opportunities.member_opportunity mo
           JOIN vyapar_opportunities.opportunities o ON o.id = mo.opportunity_id
           WHERE mo.member_id = $1""",
        ctx.member_id,
    )
    listing_rows = await conn.fetch(
        """SELECT ml.*, l.name AS title, l.state AS listing_state FROM vyapar_listings.member_listing ml
           JOIN vyapar_listings.listings l ON l.id = ml.listing_id
           WHERE ml.member_id = $1""",
        ctx.member_id,
    )
    posted_rows = await conn.fetch(
        "SELECT id, title, state FROM vyapar_opportunities.opportunities WHERE poster_id = $1", ctx.member_id
    )
    # [FR55/FR23 — closes IMP14's own noted gap] "Responded" now has a real
    # home: every enquiry the member sent, joined back to its target's
    # title (listing or opportunity — CHECK on the enquiries table
    # guarantees exactly one of the two is set).
    enquiry_rows = await conn.fetch(
        """SELECT e.id, e.listing_id, e.opportunity_id, e.state,
                  COALESCE(l.name, o.title) AS title
           FROM vyapar_enquiries.enquiries e
           LEFT JOIN vyapar_listings.listings l ON l.id = e.listing_id
           LEFT JOIN vyapar_opportunities.opportunities o ON o.id = e.opportunity_id
           WHERE e.sender_id = $1
           ORDER BY e.last_activity_at DESC""",
        ctx.member_id,
    )

    # [FR27] invites still open (unused, unexpired, not yet reviewed) — each
    # row links to the thread, where the review composer opens in place.
    invite_rows = await conn.fetch(
        """SELECT i.interaction_kind, i.interaction_id, l.name AS title
           FROM vyapar_reviews.review_invites i
           LEFT JOIN vyapar_listings.listings l ON l.id = i.subject_listing_id
           WHERE i.member_id = $1 AND i.used_at IS NULL AND i.expires_at > now()
             AND NOT EXISTS (SELECT 1 FROM vyapar_reviews.reviews r
                             WHERE r.interaction_kind = i.interaction_kind AND r.interaction_id = i.interaction_id AND r.author_id = $1)
           ORDER BY i.expires_at""",
        ctx.member_id,
    )
    # [FR26] partnership requests sent or received, titled by the OTHER listing
    partnership_rows = await conn.fetch(
        """SELECT p.id, p.state, CASE WHEN p.sender_id = $1 THEN rl.name ELSE sl.name END AS title
           FROM vyapar_enquiries.partnership_requests p
           LEFT JOIN vyapar_listings.listings sl ON sl.id = p.sender_listing_id
           LEFT JOIN vyapar_listings.listings rl ON rl.id = p.recipient_listing_id
           WHERE p.sender_id = $1 OR p.recipient_id = $1
           ORDER BY p.updated_at DESC""",
        ctx.member_id,
    )

    def item(kind: str, id_, title: str, group: str, status: str | None = None) -> ActivityItem:
        return ActivityItem(kind=kind, id=str(id_), title=title, group=group, status=status)

    saved = [item("opportunity", r["opportunity_id"], r["title"], "saved", r["opp_state"]) for r in opp_rows if r["saved_at"]]
    saved += [item("listing", r["listing_id"], r["title"], "saved", r["listing_state"]) for r in listing_rows if r["saved_at"]]
    shared = [item("opportunity", r["opportunity_id"], r["title"], "shared", r["opp_state"]) for r in opp_rows if r["shared_at"]]
    viewed = [item("opportunity", r["opportunity_id"], r["title"], "recently_viewed", r["opp_state"]) for r in opp_rows if r["viewed_at"]]
    viewed += [item("listing", r["listing_id"], r["title"], "recently_viewed", r["listing_state"]) for r in listing_rows if r["viewed_at"]]
    completed = [item("opportunity", r["opportunity_id"], r["title"], "completed", r["opp_state"]) for r in opp_rows if r["completed_at"]]
    posted = [item("opportunity", r["id"], r["title"], "posted", r["state"]) for r in posted_rows]
    responded = [item("enquiry", r["id"], r["title"] or "", "responded", r["state"]) for r in enquiry_rows]

    # [Same fix] a review invite has no lifecycle state of its own beyond
    # "still open" (the query above already filters to unused/unexpired) —
    # "open" is real, not a placeholder, since that's the only state an
    # item in this specific group can ever be in.
    to_review = [item(r["interaction_kind"], r["interaction_id"], r["title"] or "", "to_review", "open") for r in invite_rows]
    partnerships = [item("partnership", r["id"], r["title"] or "", "partnerships", r["state"]) for r in partnership_rows]

    return ActivityResponse(
        saved=saved, posted=posted, recently_viewed=viewed, shared=shared, completed=completed, responded=responded,
        to_review=to_review, partnerships=partnerships,
    )
