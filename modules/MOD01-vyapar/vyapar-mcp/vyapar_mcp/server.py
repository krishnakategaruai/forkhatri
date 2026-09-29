"""Vyapar MCP server.

Exposes the member-facing Vyapar operations as Model Context Protocol tools,
so an AI agent (Claude Desktop, Claude Code, any MCP client) can work on
Vyapar on behalf of one member.

It talks to Vyapar only over the public REST API with that member's personal
access token (VYAPAR_API_URL, VYAPAR_TOKEN). What the agent may do is exactly
what the token's scopes allow; the API refuses everything else (and audits
every write with the token id).
"""
from __future__ import annotations

from typing import Annotated, Any, Literal

from pydantic import Field

try:  # mcp >= 2
    from mcp.server.mcpserver import MCPServer as _Server
    from mcp.server.mcpserver.exceptions import ToolError
except ImportError:  # mcp 1.x
    from mcp.server.fastmcp import FastMCP as _Server  # type: ignore[no-redef]
    from mcp.server.fastmcp.exceptions import ToolError  # type: ignore[no-redef]
from mcp.types import ToolAnnotations

from vyapar_mcp.client import VyaparClient, VyaparError

INSTRUCTIONS = """\
Vyapar is a community marketplace for opportunities (jobs, freelance work,
local services, partnerships, training) and for business and professional
profiles. You act on behalf of ONE member, using their personal access token.

Typical flows:
- Find work: get_opportunity_feed -> get_opportunity -> why_this_opportunity
  -> create_enquiry (apply/enquire) or save_opportunity.
- Hire or find a provider: search_profiles -> get_profile -> create_enquiry
  with listing_id.
- Post work: post_opportunity, then list_matching_profiles to see who fits.
- Follow up: list_enquiries -> get_enquiry -> reply_to_enquiry.
Always confirm with the member before sending an enquiry, a reply or posting
an opportunity: these are visible to other people. Identifiers are UUIDs
returned by earlier tool calls; never invent them.
"""

mcp = _Server("vyapar", instructions=INSTRUCTIONS)
_client: VyaparClient | None = None

READ = ToolAnnotations(read_only_hint=True, open_world_hint=True)
WRITE = ToolAnnotations(read_only_hint=False, destructive_hint=False, open_world_hint=True)
WRITE_IDEMPOTENT = ToolAnnotations(read_only_hint=False, destructive_hint=False, idempotent_hint=True, open_world_hint=True)

OpportunityId = Annotated[str, Field(description="Opportunity UUID, from the feed or another tool result.")]
ListingId = Annotated[str, Field(description="Profile (listing) UUID of a business or professional.")]
EnquiryId = Annotated[str, Field(description="Enquiry UUID, from list_enquiries or create_enquiry.")]


def client() -> VyaparClient:
    global _client
    if _client is None:
        _client = VyaparClient()
    return _client


async def _call(coro) -> Any:
    try:
        return await coro
    except VyaparError as exc:
        raise ToolError(f"Vyapar refused ({exc.status} {exc.code}): {exc.message}") from exc


# ---------------------------------------------------------------------------
# Identity
# ---------------------------------------------------------------------------
@mcp.tool(annotations=READ)
async def whoami() -> dict:
    """Which Vyapar member this server acts for, and which scopes its access token holds.
    Call this first if unsure what you are allowed to do."""
    return await _call(client().get("/v1/integrations/me"))


# ---------------------------------------------------------------------------
# Opportunities: discover
# ---------------------------------------------------------------------------
@mcp.tool(annotations=READ)
async def get_opportunity_feed(
    skills: Annotated[str, Field(description="Optional comma-separated skill slugs to narrow the feed, e.g. 'python,accounting'.")] = "",
) -> dict:
    """The member's personalised opportunity feed, in sections: 'for_you' (matched to their skills and profiles),
    'explore', 'community' (shared within the community) and 'public'. Each item has id, title, type,
    location, compensation and why it was shown."""
    return await _call(client().get("/v1/opportunities/feed", skills=skills))


@mcp.tool(annotations=READ)
async def get_feed_section(
    section_key: Annotated[Literal["for_you", "explore", "near_you", "community", "public"], Field(description="Which feed section to expand.")],
) -> Any:
    """All items in one feed section (the feed itself shows only the first few of each)."""
    return await _call(client().get(f"/v1/opportunities/feed/section/{section_key}"))


@mcp.tool(annotations=READ)
async def get_opportunity(opportunity_id: OpportunityId) -> dict:
    """Full detail of one opportunity: description, requirements, compensation, location, work mode,
    deadline, how to respond, who posted it (trust context) and how many have already responded."""
    return await _call(client().get(f"/v1/opportunities/{opportunity_id}"))


@mcp.tool(annotations=READ)
async def why_this_opportunity(opportunity_id: OpportunityId) -> dict:
    """Why this opportunity was recommended to the member (matching skills, location, profile)."""
    return await _call(client().get(f"/v1/opportunities/{opportunity_id}/why"))


@mcp.tool(annotations=READ)
async def list_similar_opportunities(opportunity_id: OpportunityId) -> Any:
    """Other live opportunities similar to this one."""
    return await _call(client().get(f"/v1/opportunities/{opportunity_id}/similar"))


@mcp.tool(annotations=READ)
async def list_matching_profiles(opportunity_id: OpportunityId) -> Any:
    """Business and professional profiles that match an opportunity's needs. Most useful on an
    opportunity the member posted, to find people to invite."""
    return await _call(client().get(f"/v1/opportunities/{opportunity_id}/matching-profiles"))


@mcp.tool(annotations=READ)
async def list_my_opportunities() -> Any:
    """Opportunities the member has posted, with their state (draft, active, paused, closed...)."""
    return await _call(client().get("/v1/opportunities/mine"))


# ---------------------------------------------------------------------------
# Opportunities: act
# ---------------------------------------------------------------------------
@mcp.tool(annotations=WRITE_IDEMPOTENT)
async def save_opportunity(opportunity_id: OpportunityId) -> dict:
    """Save (bookmark) an opportunity for the member. Needs the opportunities:write scope."""
    return await _call(client().post(f"/v1/opportunities/{opportunity_id}/save"))


@mcp.tool(annotations=WRITE_IDEMPOTENT)
async def unsave_opportunity(opportunity_id: OpportunityId) -> dict:
    """Remove an opportunity from the member's saved list. Needs the opportunities:write scope."""
    return await _call(client().delete(f"/v1/opportunities/{opportunity_id}/save"))


@mcp.tool(annotations=WRITE)
async def mark_not_interested(
    opportunity_id: OpportunityId,
    reason: Annotated[
        Literal["too_far", "wrong_type", "not_my_capability", "value_too_low", "wrong_timing", "already_found", "not_interested"],
        Field(description="Why it does not fit; used to improve the feed."),
    ],
) -> dict:
    """Hide an opportunity from the member's feed and tell Vyapar why. Needs opportunities:write."""
    return await _call(client().post(f"/v1/opportunities/{opportunity_id}/not-interested", {"reason": reason}))


@mcp.tool(annotations=WRITE)
async def post_opportunity(
    title: Annotated[str, Field(description="Short title, e.g. 'Need a plumber for a 2BHK'.")],
    type: Annotated[
        Literal["employment", "freelance", "local_service", "partnership", "training", "community"],
        Field(description="Kind of opportunity."),
    ],
    description: Annotated[str, Field(description="What is needed, in the member's own words.")],
    location: Annotated[str, Field(description="Town or locality, e.g. 'Hyderabad' or 'Banjara Hills'.")],
    source_segment: Annotated[
        Literal["community", "public"],
        Field(description="'community' if it is the member's own or shared within the community; 'public' if copied from a public site."),
    ] = "community",
    requirements: Annotated[str | None, Field(description="Skills or experience required.")] = None,
    compensation: Annotated[str | None, Field(description="Pay or budget as text, e.g. 'Rs 8-10 LPA' or 'Rs 2,000 fixed'.")] = None,
    value_amount: Annotated[float | None, Field(description="Numeric value in rupees, if known.")] = None,
    work_mode: Annotated[Literal["on_site", "remote", "both"] | None, Field(description="Where the work happens.")] = None,
    timing: Annotated[str | None, Field(description="When, e.g. 'this weekend' or '12-month contract'.")] = None,
    required_capabilities: Annotated[list[str] | None, Field(description="Skill slugs, e.g. ['plumbing'].")] = None,
    response_method: Annotated[Literal["in_app", "external"], Field(description="'in_app' to receive enquiries in Vyapar; 'external' when responses go to source_url.")] = "in_app",
    deadline: Annotated[str | None, Field(description="ISO 8601 date-time after which it closes.")] = None,
    source_name: Annotated[str | None, Field(description="Where it came from, for public opportunities.")] = None,
    source_url: Annotated[str | None, Field(description="Link to the original, for public/external opportunities.")] = None,
    publish: Annotated[bool, Field(description="Publish right away (true) or leave as a draft for the member to review (false).")] = True,
    allow_precall: Annotated[bool, Field(description="Let people call or WhatsApp before an application is accepted (employment and local_service only).")] = False,
    precall_channel: Annotated[Literal["whatsapp_only", "call_and_whatsapp"], Field(description="With allow_precall: how people may reach the member before accepting. Anyone who uses it sees the member's phone number; tell the member that before switching it on.")] = "whatsapp_only",
) -> dict:
    """Post a new opportunity on the member's behalf. Confirm the details with the member first:
    once published it is visible to others. Needs the opportunities:write scope. Returns the
    opportunity (state 'active', or 'pending_review' when moderation holds it, or 'draft')."""
    body: dict[str, Any] = {
        "entry_mode": "create", "title": title, "type": type, "description": description, "location": location,
        "source_segment": source_segment, "requirements": requirements, "compensation": compensation,
        "value_amount": value_amount, "work_mode": work_mode, "timing": timing,
        "required_capabilities": required_capabilities or [], "response_method": response_method,
        "deadline": deadline, "source_name": source_name, "source_url": source_url,
        "allow_precall": allow_precall or None,
        "precall_channel": precall_channel if allow_precall else None,
    }
    created = await _call(client().post("/v1/opportunities", {k: v for k, v in body.items() if v is not None}))
    if not publish:
        return created
    unconfirmed = created.get("unconfirmed_fields") or []
    if unconfirmed:
        await _call(client().patch(f"/v1/opportunities/{created['id']}/confirm", {"fields": unconfirmed}))
    return await _call(client().post(f"/v1/opportunities/{created['id']}/publish"))


@mcp.tool(annotations=WRITE)
async def publish_opportunity(opportunity_id: OpportunityId) -> dict:
    """Publish one of the member's draft opportunities. Needs opportunities:write."""
    return await _call(client().post(f"/v1/opportunities/{opportunity_id}/publish"))


# ---------------------------------------------------------------------------
# Enquiries (apply / enquire / reply)
# ---------------------------------------------------------------------------
@mcp.tool(annotations=WRITE)
async def create_enquiry(
    message: Annotated[str, Field(description="The member's message to the other person. Confirm it with the member before sending.")],
    opportunity_id: Annotated[str | None, Field(description="Set to apply to / enquire about an opportunity.")] = None,
    listing_id: Annotated[str | None, Field(description="Set to contact a business or professional profile.")] = None,
    sub_choice: Annotated[str | None, Field(description="Optional sub-choice some opportunity types ask for (e.g. which service).")] = None,
    attachment_url: Annotated[str | None, Field(description="Optional URL of an attachment already uploaded.")] = None,
) -> dict:
    """Apply to an opportunity or send an enquiry to a profile (exactly one of opportunity_id or
    listing_id). This contacts another member. Needs the enquiries:write scope. Retrying the
    same call is safe: each call carries an Idempotency-Key."""
    if bool(opportunity_id) == bool(listing_id):
        raise ToolError("Give exactly one of opportunity_id or listing_id.")
    body = {"message": message, "opportunity_id": opportunity_id, "listing_id": listing_id,
            "sub_choice": sub_choice, "attachment_url": attachment_url}
    return await _call(client().post("/v1/enquiries", {k: v for k, v in body.items() if v is not None}))


@mcp.tool(annotations=READ)
async def list_enquiries(
    role: Annotated[Literal["sent", "received", "all"], Field(description="'sent' = the member asked; 'received' = others asked the member.")] = "all",
) -> Any:
    """The member's enquiry conversations with their state and last activity."""
    return await _call(client().get("/v1/enquiries/mine", role=role))


@mcp.tool(annotations=READ)
async def get_enquiry(enquiry_id: EnquiryId) -> dict:
    """One enquiry conversation with all its messages."""
    return await _call(client().get(f"/v1/enquiries/{enquiry_id}"))


@mcp.tool(annotations=WRITE)
async def reply_to_enquiry(
    enquiry_id: EnquiryId,
    body: Annotated[str, Field(description="Reply text. Confirm it with the member before sending.")],
    attachment_url: Annotated[str | None, Field(description="Optional URL of an attachment already uploaded.")] = None,
) -> dict:
    """Send a message in an enquiry conversation. Needs the enquiries:write scope."""
    payload = {"body": body}
    if attachment_url:
        payload["attachment_url"] = attachment_url
    return await _call(client().post(f"/v1/enquiries/{enquiry_id}/messages", payload))


# ---------------------------------------------------------------------------
# Activity and notifications
# ---------------------------------------------------------------------------
@mcp.tool(annotations=READ)
async def get_activity() -> dict:
    """The member's activity overview: saved opportunities, applications and enquiries in progress,
    and their own postings."""
    return await _call(client().get("/v1/activity"))


@mcp.tool(annotations=READ)
async def list_notifications() -> Any:
    """The member's notification inbox, newest first."""
    return await _call(client().get("/v1/notifications"))


@mcp.tool(annotations=READ)
async def get_unread_notification_count() -> dict:
    """How many notifications the member has not read yet."""
    return await _call(client().get("/v1/notifications/unread-count"))


@mcp.tool(annotations=WRITE_IDEMPOTENT)
async def mark_notification_read(
    notification_id: Annotated[str, Field(description="Notification UUID from list_notifications.")],
) -> dict:
    """Mark one notification as read. Needs the notifications:write scope."""
    return await _call(client().post(f"/v1/notifications/{notification_id}/read"))


# ---------------------------------------------------------------------------
# Businesses and professionals
# ---------------------------------------------------------------------------
@mcp.tool(annotations=READ)
async def search_profiles(
    q: Annotated[str | None, Field(description="Free-text search, e.g. 'GST filing' or 'interior designer'.")] = None,
    kind: Annotated[Literal["any", "business", "professional"], Field(description="Only businesses, only professionals, or both.")] = "any",
    category: Annotated[str | None, Field(description="Category slug, e.g. 'accounting_tax'.")] = None,
    locality: Annotated[str | None, Field(description="Locality or town, e.g. 'Banjara Hills'.")] = None,
    radius_km: Annotated[int | None, Field(description="Search radius around the locality, in km.")] = None,
    service_mode: Annotated[Literal["on_site", "remote", "both"] | None, Field(description="How the service is delivered.")] = None,
    availability: Annotated[Literal["now", "this_week", "later"] | None, Field(description="How soon they can start.")] = None,
    verified_only: Annotated[bool, Field(description="Only profiles whose business or credentials are verified.")] = False,
    skills: Annotated[str, Field(description="Comma-separated skill slugs to require.")] = "",
    sort_by: Annotated[Literal["relevance", "distance", "freshness", "verified_first"], Field(description="Result order.")] = "relevance",
    limit: Annotated[int, Field(ge=1, le=50, description="Maximum results.")] = 20,
) -> dict:
    """Search business and professional profiles. Each result has the profile (id, kind, name,
    headline, categories, capabilities, locality, verification) and why it matched. When nothing
    matches, the response suggests ways to broaden the search."""
    data = await _call(client().get(
        "/v1/listings/search", q=q, category=category, locality=locality, radius_km=radius_km,
        service_mode=service_mode, availability=availability, verified_only=str(verified_only).lower(),
        skills=skills, sort_by=sort_by, limit=limit,
    ))
    if kind != "any" and isinstance(data, dict):
        data["results"] = [r for r in data.get("results", []) if (r.get("listing") or {}).get("kind") == kind]
    return data


@mcp.tool(annotations=READ)
async def get_profile(listing_id: ListingId) -> dict:
    """Full business or professional profile: services, capabilities, locality, experience,
    languages, availability, verification and reputation."""
    return await _call(client().get(f"/v1/listings/{listing_id}"))


@mcp.tool(annotations=READ)
async def list_similar_profiles(listing_id: ListingId) -> Any:
    """Other profiles similar to this one."""
    return await _call(client().get(f"/v1/listings/{listing_id}/similar"))


@mcp.tool(annotations=READ)
async def list_profile_reviews(listing_id: ListingId) -> Any:
    """Published reviews of a profile."""
    return await _call(client().get(f"/v1/listings/{listing_id}/reviews"))


@mcp.tool(annotations=READ)
async def list_my_profiles() -> Any:
    """The member's own business and professional profiles."""
    return await _call(client().get("/v1/listings/mine"))


@mcp.tool(annotations=WRITE_IDEMPOTENT)
async def save_profile(listing_id: ListingId) -> dict:
    """Save a profile to the member's saved list. Needs the listings:write scope."""
    return await _call(client().post(f"/v1/listings/{listing_id}/save"))


@mcp.tool(annotations=WRITE_IDEMPOTENT)
async def unsave_profile(listing_id: ListingId) -> dict:
    """Remove a profile from the member's saved list. Needs the listings:write scope."""
    return await _call(client().delete(f"/v1/listings/{listing_id}/save"))


# ---------------------------------------------------------------------------
# Enquiry lifecycle (IMP-B)
# ---------------------------------------------------------------------------
@mcp.tool(annotations=WRITE)
async def accept_enquiry(enquiry_id: EnquiryId) -> dict:
    """Accept an enquiry the member RECEIVED (provider side). After this the two people can see each
    other's contact actions (call / WhatsApp). Needs enquiries:write."""
    return await _call(client().post(f"/v1/enquiries/{enquiry_id}/accept"))


@mcp.tool(annotations=WRITE)
async def close_enquiry(enquiry_id: EnquiryId) -> dict:
    """Close an enquiry thread that is in progress or resolved. Both sides may then be invited to
    review each other. Needs enquiries:write."""
    return await _call(client().post(f"/v1/enquiries/{enquiry_id}/close"))


@mcp.tool(annotations=WRITE)
async def withdraw_enquiry(enquiry_id: EnquiryId) -> dict:
    """Withdraw an enquiry the member SENT. Needs enquiries:write."""
    return await _call(client().post(f"/v1/enquiries/{enquiry_id}/withdraw"))


@mcp.tool(annotations=READ)
async def get_contact_actions(enquiry_id: EnquiryId) -> dict:
    """Call / WhatsApp actions for an accepted enquiry, shaped by the other person's preferences
    (call hours, days, daily cap, channels). `revealed` is false before acceptance. Each action has an
    href (tel: or wa.me), available_now, and next_window when not available."""
    return await _call(client().get(f"/v1/enquiries/{enquiry_id}/contact-actions"))


@mcp.tool(annotations=WRITE)
async def record_contact_attempt(
    enquiry_id: EnquiryId,
    channel: Annotated[Literal["call", "whatsapp"], Field(description="Which action the member is using now.")],
) -> dict:
    """Record that the member is calling or messaging the other person now (so their daily cap and
    'you called X on ...' history are real). Refused with daily_cap_reached when the cap is hit.
    Needs enquiries:write."""
    return await _call(client().post(f"/v1/enquiries/{enquiry_id}/contact-attempts", {"channel": channel}))


@mcp.tool(annotations=READ)
async def get_opportunity_contact_actions(opportunity_id: OpportunityId) -> dict:
    """Call / WhatsApp the poster BEFORE applying, when the post allows it (allow_precall, jobs and local
    services only). Each action has href only when it can be used right now; otherwise href is null and
    reason is outside_hours, day_off, daily_cap_reached, not_matching, caller_limit_reached or
    precall_off. Top-level reason precall_off / own_post / no_contact means there is nothing to tap."""
    return await _call(client().get(f"/v1/opportunities/{opportunity_id}/contact-actions"))


@mcp.tool(annotations=WRITE)
async def record_opportunity_contact_attempt(
    opportunity_id: OpportunityId,
    channel: Annotated[Literal["call", "whatsapp"], Field(description="Which action the member is using now.")],
) -> dict:
    """Record that the member is calling or messaging the poster now (before applying). Counts toward the
    poster's daily cap (max 3 taps per post per day for one caller), notifies the poster, and opens a
    lightweight application for the member if they have none. Confirm with the member first.
    Needs enquiries:write."""
    return await _call(client().post(f"/v1/opportunities/{opportunity_id}/contact-attempts", {"channel": channel}))


# ---------------------------------------------------------------------------
# Partnerships (IMP-B)
# ---------------------------------------------------------------------------
PartnershipId = Annotated[str, Field(description="Partnership request UUID from list_partnerships.")]


@mcp.tool(annotations=READ)
async def list_partnerships() -> Any:
    """The member's partnership requests, sent and received, with state."""
    return await _call(client().get("/v1/partnership-requests/mine"))


@mcp.tool(annotations=READ)
async def get_partnership(request_id: PartnershipId) -> dict:
    """One partnership request in full (need, offer, expectations, timing, next step, both listings,
    and contacts once accepted)."""
    return await _call(client().get(f"/v1/partnership-requests/{request_id}"))


@mcp.tool(annotations=WRITE)
async def respond_partnership(
    request_id: PartnershipId,
    action: Annotated[Literal["accept", "decline", "withdraw", "restrict", "close"], Field(description="accept/decline/restrict as recipient; withdraw as sender; close once accepted.")],
) -> dict:
    """Accept, decline, restrict, withdraw or close a partnership request. Confirm with the member
    first. Needs partnerships:write."""
    return await _call(client().post(f"/v1/partnership-requests/{request_id}/{action}"))


@mcp.tool(annotations=WRITE)
async def create_partnership_request(
    recipient_listing_id: Annotated[str, Field(description="The business/professional profile to partner with.")],
    need: Annotated[str, Field(description="What the member needs (10-500 chars).")],
    offer: Annotated[str, Field(description="What the member offers (10-500 chars).")],
    expectations: Annotated[str, Field(description="What a good partnership looks like (10-500 chars).")],
    category: Annotated[str, Field(description="Category, e.g. 'accounting_tax'.")],
    locality: Annotated[str, Field(description="Where, e.g. 'Abids'.")],
    timing: Annotated[str, Field(description="When (10-500 chars).")],
    next_step: Annotated[str, Field(description="Proposed next step (10-500 chars).")],
    sender_listing_id: Annotated[str | None, Field(description="Which of the member's own profiles sends it; default: their newest active one.")] = None,
) -> dict:
    """Send a partnership request to another business or professional. Confirm every field with the
    member first: it is sent to another person. Needs partnerships:write."""
    body = {"recipient_listing_id": recipient_listing_id, "sender_listing_id": sender_listing_id, "need": need,
            "offer": offer, "expectations": expectations, "category": category, "locality": locality,
            "timing": timing, "next_step": next_step}
    return await _call(client().post("/v1/partnership-requests", {k: v for k, v in body.items() if v is not None}))


# ---------------------------------------------------------------------------
# Reviews (IMP-B)
# ---------------------------------------------------------------------------
@mcp.tool(annotations=READ)
async def list_review_invites(
    interaction_kind: Annotated[Literal["enquiry", "partnership"], Field(description="What the review is about.")],
    interaction_id: Annotated[str, Field(description="The enquiry or partnership request UUID.")],
) -> dict:
    """Whether the member may review this interaction now (can_review, expiry, allowed tags)."""
    return await _call(client().get(f"/v1/reviews/invite/{interaction_kind}/{interaction_id}"))


@mcp.tool(annotations=WRITE)
async def submit_review(
    interaction_kind: Annotated[Literal["enquiry", "partnership"], Field(description="What the review is about.")],
    interaction_id: Annotated[str, Field(description="The enquiry or partnership request UUID.")],
    recommend: Annotated[bool, Field(description="Would the member recommend the other person?")],
    tags: Annotated[list[str] | None, Field(description="Up to 3 tags from list_review_invites.")] = None,
    comment: Annotated[str | None, Field(description="Optional comment, 20-500 characters.")] = None,
) -> dict:
    """Submit a recommend / don't-recommend review with tags for a completed interaction. Confirm the
    wording with the member first. Needs reviews:write."""
    body = {"interaction_kind": interaction_kind, "interaction_id": interaction_id, "recommend": recommend,
            "tags": tags or [], "comment": comment}
    return await _call(client().post("/v1/reviews", {k: v for k, v in body.items() if v is not None}))


@mcp.tool(annotations=READ)
async def get_member_badges(
    member_id: Annotated[str, Field(description="Member id, e.g. the poster_id or owner_id on a result.")],
) -> dict:
    """A member's count-based badges (responds fast, reliable, rising, top recommended, verified
    business, repeat hires) with localized labels. Never a star score."""
    return await _call(client().get(f"/v1/members/{member_id}/badges"))


# ---------------------------------------------------------------------------
# Boosts (IMP-B). Buying is a payment: the API allows it only for the member in
# person, so buy_boost prepares the order and returns the payment link/id.
# ---------------------------------------------------------------------------
@mcp.tool(annotations=READ)
async def list_boost_products(
    target_kind: Annotated[Literal["listing", "opportunity"], Field(description="What would be boosted.")],
    target_id: Annotated[str, Field(description="The listing or opportunity UUID.")],
) -> dict:
    """Boost packs (duration, price incl. tax) available for one listing or opportunity, plus
    eligibility. Read-only."""
    return await _call(client().get("/v1/promotions/options", target_kind=target_kind, target_id=target_id))


@mcp.tool(annotations=WRITE)
async def buy_boost(
    target_kind: Annotated[Literal["listing", "opportunity"], Field(description="What to boost.")],
    target_id: Annotated[str, Field(description="The listing or opportunity UUID.")],
    product_id: Annotated[str | None, Field(description="A pack id from list_boost_products (or give custom_days instead).")] = None,
    custom_days: Annotated[int | None, Field(ge=1, le=30, description="Custom length in days instead of a pack.")] = None,
    audience_locality: Annotated[str | None, Field(description="Optional locality to narrow who sees it.")] = None,
) -> dict:
    """Prepare a boost order and its payment step (the member confirmed the disclosure). Money moves
    only when the member completes the payment themselves. The API keeps payments with the member in
    person, so under an access token this returns 'not_available_to_tokens'."""
    if bool(product_id) == bool(custom_days):
        raise ToolError("Give exactly one of product_id or custom_days.")
    body: dict[str, Any] = {"target_kind": target_kind, "target_id": target_id, "product_id": product_id,
                            "custom_days": custom_days, "audience_locality": audience_locality}
    created = await _call(client().post("/v1/promotions", {k: v for k, v in body.items() if v is not None}))
    promotion_id = created.get("id") or created.get("promotion_id")
    if not promotion_id:
        return created
    return await _call(client().post(f"/v1/promotions/{promotion_id}/confirm-purchase", {"confirmed": True}))


# ---------------------------------------------------------------------------
# Contact preferences (IMP-B)
# ---------------------------------------------------------------------------
@mcp.tool(annotations=READ)
async def get_contact_preferences(
    listing_id: Annotated[str | None, Field(description="A listing of the member's, for that listing's overrides; omit for the member's defaults.")] = None,
) -> dict:
    """How the member allows others to call or message them: call hours (HH:MM, IST), call days,
    max calls per day, calls_from (anyone | matching_only), WhatsApp on/off, calls on/off."""
    if listing_id:
        return await _call(client().get(f"/v1/listings/{listing_id}/contact-preferences"))
    return await _call(client().get("/v1/listings/contact-preferences"))


@mcp.tool(annotations=WRITE_IDEMPOTENT)
async def update_contact_preferences(
    call_hours_start: Annotated[str | None, Field(description="HH:MM local time, e.g. '09:00'.")] = None,
    call_hours_end: Annotated[str | None, Field(description="HH:MM local time, e.g. '18:00'.")] = None,
    call_days: Annotated[list[str] | None, Field(description="e.g. ['mon','tue','wed','thu','fri','sat']; empty list = every day.")] = None,
    max_calls_per_day: Annotated[int | None, Field(ge=1, le=500, description="Daily call cap.")] = None,
    calls_from: Annotated[Literal["anyone", "matching_only"] | None, Field(description="Who may call.")] = None,
    whatsapp_ok: Annotated[bool | None, Field(description="Allow WhatsApp.")] = None,
    call_ok: Annotated[bool | None, Field(description="Allow phone calls.")] = None,
    reset: Annotated[list[str] | None, Field(description="Field names to reset to default (member) or inherit (listing).")] = None,
    listing_id: Annotated[str | None, Field(description="Set to override for one listing only.")] = None,
) -> dict:
    """Update the member's contact preferences (or one listing's overrides). Needs listings:write."""
    body = {"call_hours_start": call_hours_start, "call_hours_end": call_hours_end, "call_days": call_days,
            "max_calls_per_day": max_calls_per_day, "calls_from": calls_from, "whatsapp_ok": whatsapp_ok,
            "call_ok": call_ok, "reset": reset or []}
    payload = {k: v for k, v in body.items() if v is not None}
    path = f"/v1/listings/{listing_id}/contact-preferences" if listing_id else "/v1/listings/contact-preferences"
    return await _call(client().patch(path, payload))


# ---------------------------------------------------------------------------
# Service packages (IMP-B)
# ---------------------------------------------------------------------------
@mcp.tool(annotations=READ)
async def list_listing_packages(listing_id: ListingId) -> Any:
    """A profile's priced service packages (basic / standard / premium): price, delivery days,
    revisions, what is included."""
    return await _call(client().get(f"/v1/listings/{listing_id}/packages"))


@mcp.tool(annotations=WRITE_IDEMPOTENT)
async def upsert_listing_packages(
    listing_id: ListingId,
    packages: Annotated[list[dict], Field(description="Up to 3 objects: {tier: basic|standard|premium, name, price_paise, description?, delivery_days?, revisions?, includes?: [..], name_hi?, name_te?, description_hi?, description_te?}.")],
) -> Any:
    """Create or update package tiers on one of the member's own profiles (max 3). Needs listings:write."""
    return await _call(client().request("PUT", f"/v1/listings/{listing_id}/packages", json={"packages": packages}))


@mcp.tool(annotations=WRITE)
async def request_listing_package(
    listing_id: ListingId,
    package_id: Annotated[str, Field(description="Package UUID from list_listing_packages.")],
    message: Annotated[str, Field(description="The member's message to the provider (20-1000 chars). Confirm it first.")],
) -> dict:
    """Request a specific package from a provider: opens an enquiry tagged with that package.
    Contacts another person. Needs listings:write."""
    return await _call(client().post(f"/v1/listings/{listing_id}/packages/{package_id}/request", {"message": message}))


# ---------------------------------------------------------------------------
# Saved searches (IMP-B)
# ---------------------------------------------------------------------------
@mcp.tool(annotations=WRITE)
async def save_search(
    query: Annotated[str, Field(description="Free text, may be empty.")] = "",
    skills: Annotated[list[str] | None, Field(description="Capability slugs.")] = None,
    type: Annotated[Literal["employment", "freelance", "local_service", "partnership", "training", "community"] | None, Field(description="Opportunity type.")] = None,
    work_mode: Annotated[Literal["on_site", "remote", "both"] | None, Field(description="Where the work happens.")] = None,
    radius_km: Annotated[int | None, Field(ge=1, le=500, description="Distance limit from the member.")] = None,
    availability: Annotated[Literal["now", "this_week", "later"] | None, Field(description="Urgency bucket.")] = None,
    alert: Annotated[bool, Field(description="Notify the member when new opportunities match (under their daily cap).")] = False,
    name: Annotated[str | None, Field(description="A short label for the search.")] = None,
) -> dict:
    """Save an opportunity search (the feed's own filters) for the member, optionally with alerts.
    Needs opportunities:write."""
    filters = {"skills": skills or [], "type": type, "work_mode": work_mode, "radius_km": radius_km, "availability": availability}
    body = {"query": query, "filters": {k: v for k, v in filters.items() if v is not None}, "alert": alert, "name": name}
    return await _call(client().post("/v1/opportunities/saved-searches", {k: v for k, v in body.items() if v is not None}))


@mcp.tool(annotations=READ)
async def list_saved_searches() -> Any:
    """The member's saved opportunity searches."""
    return await _call(client().get("/v1/opportunities/saved-searches"))


@mcp.tool(annotations=WRITE)
async def delete_saved_search(
    search_id: Annotated[str, Field(description="Saved search UUID from list_saved_searches.")],
) -> dict:
    """Delete one saved search. Needs opportunities:write."""
    return await _call(client().delete(f"/v1/opportunities/saved-searches/{search_id}"))


@mcp.tool(annotations=READ)
async def search_opportunities(
    q: Annotated[str | None, Field(description="Free text over title, skills, description, location.")] = None,
    skills: Annotated[str, Field(description="Comma-separated capability slugs.")] = "",
    type: Annotated[Literal["employment", "freelance", "local_service", "partnership", "training", "community"] | None, Field(description="Opportunity type.")] = None,
    work_mode: Annotated[Literal["on_site", "remote", "both"] | None, Field(description="Where the work happens.")] = None,
    radius_km: Annotated[int | None, Field(ge=1, le=500, description="Only within this distance (km) of the member.")] = None,
    availability: Annotated[Literal["now", "this_week", "later"] | None, Field(description="now = urgent / deadline within 7 days.")] = None,
    sort: Annotated[Literal["relevance", "distance", "freshness", "verified_first", "salary_high"], Field(description="Result order.")] = "relevance",
    lat: Annotated[float | None, Field(ge=-90, le=90, description="The member's current latitude, for distance and radius only (never stored). Send with lng.")] = None,
    lng: Annotated[float | None, Field(ge=-180, le=180, description="The member's current longitude. Send with lat.")] = None,
) -> dict:
    """The member's feed with real filters and sorting applied to every section. Cards carry
    distance_km, the poster's badges and, for jobs, the seeker-protection notice."""
    return await _call(client().get("/v1/opportunities/feed", q=q, skills=skills, type=type, work_mode=work_mode,
                                    radius_km=radius_km, availability=availability, sort=sort, lat=lat, lng=lng))


@mcp.tool(annotations=READ)
async def check_seeker_charge(
    text: Annotated[str, Field(description="The opportunity's title, description, requirements and compensation, joined.")],
    type: Annotated[str, Field(description="Opportunity type.")] = "employment",
    candidate_pays: Annotated[bool, Field(description="Whether the draft asks applicants to pay anything.")] = False,
) -> dict:
    """Check a draft opportunity against the 'nobody charges job seekers' rule before posting.
    Returns allowed=false with code seeker_charge_not_allowed when a fee, deposit or kit charge is asked."""
    return await _call(client().post("/v1/opportunities/seeker-charge-check",
                                     {"text": text, "structured": {"type": type, "candidate_pays": candidate_pays}}))


# ---------------------------------------------------------------------------
# Hiring pipeline, AI drafting and contracts — thin wrappers over the routes
# sibling workstreams ship (routers/ai.py, routers/contracts.py per
# references/imp-backend-d.md, and the applicant pipeline in imp-backend-a.md). A route not yet deployed
# answers with the API's own 404 error, surfaced as a ToolError.
# ---------------------------------------------------------------------------
@mcp.tool(annotations=READ)
async def list_applicants(opportunity_id: OpportunityId) -> Any:
    """Applicants (enquiries) on one of the member's opportunities, with their pipeline stage."""
    return await _call(client().get(f"/v1/opportunities/{opportunity_id}/applicants"))


@mcp.tool(annotations=WRITE)
async def set_applicant_stage(
    opportunity_id: OpportunityId,
    enquiry_id: EnquiryId,
    stage: Annotated[str, Field(description="Pipeline stage, e.g. new | shortlisted | interviewing | offered | hired | rejected.")],
    note: Annotated[str | None, Field(description="Optional note for the member's own records.")] = None,
) -> dict:
    """Move an applicant to a pipeline stage on the member's opportunity. Needs opportunities:write."""
    body = {"stage": stage}
    if note:
        body["note"] = note
    return await _call(client().post(f"/v1/opportunities/{opportunity_id}/applicants/{enquiry_id}/stage", body))


@mcp.tool(annotations=WRITE)
async def draft_opportunity(
    text: Annotated[str, Field(description="What the member needs, in their own words (English, Hindi, Telugu or Hinglish).")],
    language: Annotated[Literal["en", "hi", "te"] | None, Field(description="Language to draft in.")] = None,
) -> dict:
    """Ask Vyapar to draft a structured opportunity from a plain brief. Returns a draft for the member
    to review; nothing is posted."""
    body = {"text": text, "language": language}
    return await _call(client().post("/v1/ai/draft-opportunity", {k: v for k, v in body.items() if v is not None}))


@mcp.tool(annotations=READ)
async def get_ai_shortlist(opportunity_id: OpportunityId) -> Any:
    """An AI-ranked shortlist of applicants for the member's opportunity, with reasons."""
    return await _call(client().get(f"/v1/opportunities/{opportunity_id}/ai-shortlist"))


ContractId = Annotated[str, Field(description="Contract UUID.")]


@mcp.tool(annotations=WRITE)
async def create_contract(
    enquiry_id: Annotated[str, Field(description="The accepted enquiry this contract comes from.")],
    title: Annotated[str, Field(description="Contract title (3-140 chars).")],
    total_paise: Annotated[int, Field(gt=0, description="Fixed: the sum of the milestones. Hourly: the budget ceiling.")],
    milestones: Annotated[list[dict] | None, Field(description="[{title, amount_paise, description?, due_date?}] in order (fixed-price).")] = None,
    kind: Annotated[Literal["fixed", "hourly"], Field(description="Fixed-price milestones or hourly.")] = "fixed",
    hourly_rate_paise: Annotated[int | None, Field(description="Hourly contracts only.")] = None,
    weekly_hours_cap: Annotated[float | None, Field(description="Hourly contracts only.")] = None,
    description: Annotated[str | None, Field(description="Scope in plain words.")] = None,
    propose: Annotated[bool, Field(description="Send to the provider straight away.")] = False,
) -> dict:
    """Create a contract (as the client) from an accepted enquiry. Confirm the amounts with the member first.
    Needs the contracts:write scope."""
    body = {"enquiry_id": enquiry_id, "title": title, "total_paise": total_paise, "milestones": milestones or [],
            "kind": kind, "hourly_rate_paise": hourly_rate_paise, "weekly_hours_cap": weekly_hours_cap,
            "description": description, "propose": propose}
    return await _call(client().post("/v1/contracts", {k: v for k, v in body.items() if v is not None}))


@mcp.tool(annotations=WRITE)
async def fund_milestone(
    contract_id: ContractId,
    milestone_id: Annotated[str, Field(description="Milestone UUID.")],
) -> dict:
    """Fund a milestone as the client: returns a checkout_url (FundingOut) the member opens to pay; the
    milestone becomes funded only when the payment is confirmed. Needs contracts:write."""
    return await _call(client().post(f"/v1/contracts/{contract_id}/milestones/{milestone_id}/fund"))


@mcp.tool(annotations=WRITE)
async def approve_milestone(
    contract_id: ContractId,
    milestone_id: Annotated[str, Field(description="Milestone UUID.")],
) -> dict:
    """Approve a submitted milestone as the client, releasing it to the provider. Confirm with the
    member first. Needs contracts:write."""
    return await _call(client().post(f"/v1/contracts/{contract_id}/milestones/{milestone_id}/approve"))


def main() -> None:
    import logging

    # httpx logs every request at INFO; keep stderr for real problems only.
    logging.getLogger("httpx").setLevel(logging.WARNING)
    mcp.run()


if __name__ == "__main__":
    main()
