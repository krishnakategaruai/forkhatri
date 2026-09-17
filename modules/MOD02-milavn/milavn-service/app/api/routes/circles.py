"""Circle endpoints — FR020-FR025, FR028 (organization scope)."""

from __future__ import annotations

from datetime import date, datetime
from uuid import UUID

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from app.api.deps import AppSettings, CurrentMember, DbSession, Locale
from app.api.schemas import CardOut
from app.components.activity import interface as activity
from app.components.circle import interface as circle
from app.components.discovery import interface as discovery
from app.components.identity_bridge import interface as identity
from app.i18n import translate
from app.rate_limiting import RateLimitScope, enforce

router = APIRouter(prefix="/circles", tags=["circles"])


class CreateCircleRequest(BaseModel):
    name: str = Field(min_length=1, max_length=80)
    circle_type: str
    description: str | None = None
    join_policy: str = "open"  # [FR115] 'open' or 'approval'
    join_questions: list[str] = Field(default_factory=list)
    locality_city: str | None = None  # approximate home place (FR038); omit for "anywhere"
    locality_locality: str | None = None
    starts_on: str | None = None  # [FR125] ISO date — required for 'temple'/'travel'
    ends_on: str | None = None  # [FR125] a trip's last day; omit for a single day


class JoinRequest(BaseModel):
    answers: list[str] = Field(default_factory=list)  # [FR115] one per question the circle asks


class DecideRequest(BaseModel):
    approve: bool


class MemberRefRequest(BaseModel):
    member_id: UUID


class OrgScopeRequest(BaseModel):
    display_name: str = Field(min_length=1, max_length=120)


class SuggestionResponse(BaseModel):
    accept: bool


class GroupUpdateRequest(BaseModel):
    message: str = Field(min_length=1, max_length=1000)


def _out(c: circle.Circle) -> dict:
    # [FR125] "Days to go" / "concluded" are display conveniences computed at read time —
    # never stored, so they are always right relative to whenever the page is actually loaded.
    ends = c.ends_on or c.starts_on
    today = date.today().isoformat()
    return {
        "id": str(c.id),
        "name": c.name,
        "circle_type": c.circle_type,
        "type_label": circle.type_label(c.circle_type),
        "description": c.description,
        "created_by_member_id": str(c.created_by_member_id),
        "created_at": c.created_at.isoformat(),
        "member_count": c.member_count,
        "viewer_role": c.viewer_role,
        "is_open": c.circle_type in circle.OPEN_TYPES,
        "locality_city": c.locality_city,
        "locality_locality": c.locality_locality,
        "locality_label": c.locality_locality or c.locality_city,
        "near_you": c.near_you,
        "starts_on": c.starts_on,
        "ends_on": c.ends_on,
        "is_concluded": bool(ends and ends < today),
        "group_id": str(c.group_id) if c.group_id else None,
    }


@router.get("/mine")
async def mine(session: DbSession, member: CurrentMember) -> list[dict]:
    return [_out(c) for c in await circle.mine(session, member_id=member.member_id)]


@router.get("/discover")
async def discover(session: DbSession, member: CurrentMember, q: str | None = None, near: bool = False) -> list[dict]:
    """[FR025] Open circles, the viewer's own locality first; `near=true` keeps only those."""
    v = await discovery.viewer_profile(session, member.member_id)
    return [
        _out(c)
        for c in await circle.discover(
            session,
            viewer_member_id=member.member_id,
            query=q,
            viewer_city=v.city if v else None,
            viewer_locality=v.locality if v else None,
            near_only=near,
        )
    ]


@router.get("/types")
async def types() -> list[dict]:
    return [{"value": t, "label": circle.type_label(t), "is_open": t in circle.OPEN_TYPES} for t in circle.CIRCLE_TYPES]


@router.post("", status_code=status.HTTP_201_CREATED)
async def create(body: CreateCircleRequest, session: DbSession, member: CurrentMember, settings: AppSettings) -> dict:
    """[FR020/FR021] Create with an enum-enforced type; creator seeds the organizer membership."""
    await enforce(session, scope=RateLimitScope.CIRCLE_CREATE, subject=str(member.member_id), limit_max=10, window_seconds=3600)
    try:
        c = await circle.create(
            session,
            creator_member_id=member.member_id,
            name=body.name,
            circle_type=body.circle_type,
            description=body.description,
            locality_city=body.locality_city,
            locality_locality=body.locality_locality,
            join_policy=body.join_policy,
            join_questions=body.join_questions,
            starts_on=body.starts_on,
            ends_on=body.ends_on,
        )
    except circle.InvalidCircle as exc:
        raise HTTPException(status_code=422, detail={"fields": exc.fields}) from exc
    return _out(c)


@router.get("/suggestions")
async def suggestions(session: DbSession, member: CurrentMember) -> list[dict]:
    """[FR022] Pending organic circle-formation suggestions for me."""
    out = []
    for s in await circle.pending_suggestions(session, member_id=member.member_id):
        names = await identity.display_names_for(s["member_ids"])
        out.append(
            {
                "id": str(s["id"]),
                "name": s["name"],
                "created_at": s["created_at"].isoformat(),
                "members": [{"member_id": str(m), "display_name": names[m].display_name, "avatar": names[m].avatar} for m in s["member_ids"]],
            }
        )
    return out


@router.post("/suggestions/{suggestion_id}/respond")
async def respond(suggestion_id: UUID, body: SuggestionResponse, session: DbSession, member: CurrentMember) -> dict:
    c = await circle.respond_suggestion(session, suggestion_id=suggestion_id, member_id=member.member_id, accept=body.accept)
    return {"created": _out(c) if c else None}


@router.post("/suggestions/run")
async def run_suggestions(session: DbSession, member: CurrentMember) -> dict:
    """[TR17] Dev/ops trigger for the nightly co-participation job."""
    return {"created": await circle.run_suggestion_job(session)}


@router.get("/organizations")
async def organizations(session: DbSession, member: CurrentMember) -> list[dict]:
    return [
        {"organization_scope_id": str(o["organization_scope_id"]), "display_name": o["display_name"], "created_by_member_id": str(o["created_by_member_id"])}
        for o in await circle.list_organization_scopes(session)
    ]


@router.post("/organizations", status_code=201)
async def create_organization(body: OrgScopeRequest, session: DbSession, member: CurrentMember) -> dict:
    """[FR028/TR23] Deliberately minimal scope tag — no roster, roles, verification or billing."""
    o = await circle.create_organization_scope(session, creator_member_id=member.member_id, display_name=body.display_name)
    return {"organization_scope_id": str(o["organization_scope_id"]), "display_name": o["display_name"]}


@router.get("/{circle_id}")
async def detail(circle_id: UUID, session: DbSession, member: CurrentMember, lang: Locale) -> dict:
    try:
        c = await circle.get(session, circle_id=circle_id, viewer_member_id=member.member_id)
    except circle.CircleNotFound as exc:
        raise HTTPException(status_code=404, detail=translate("circle.notFound", lang)) from exc
    rows = await circle.members(session, circle_id=circle_id, viewer_member_id=member.member_id)
    names = await identity.display_names_for([r[0] for r in rows])
    memory = None
    try:
        memory = await circle.community_memory(session, circle_id=circle_id, viewer_member_id=member.member_id)
    except circle.NotMember:
        memory = None
    v = await discovery.viewer_profile(session, member.member_id)
    occs = await activity.list_visible(session, city=None, start=None, end=None, circle_id=circle_id)
    cards = await discovery.build_cards(session, occs, v, rank=False)
    # [FR115] What the viewer needs to know about getting in, and what the organizer must act on.
    my_request = await circle.my_request_status(session, circle_id=circle_id, member_id=member.member_id)
    requests = await circle.pending_requests(session, circle_id=circle_id, viewer_member_id=member.member_id) if c.viewer_role in ("organizer", "assistant") else []
    return {
        **_out(c),
        "join_policy": c.join_policy,
        "join_questions": list(c.join_questions),
        "my_request_status": my_request,
        "join_requests": requests,
        # [FR123] The umbrella this circle sits under, if any.
        "group": await circle.group_of(session, circle_id=circle_id),
        "members": [{"member_id": str(m), "display_name": names[m].display_name, "avatar": names[m].avatar, "role": role} for (m, role, _j) in rows],
        "memory": {**memory, "first_activity_at": memory["first_activity_at"].isoformat() if memory and memory.get("first_activity_at") else None} if memory else None,
        "upcoming": [CardOut.from_card(x).model_dump(mode="json") for x in cards],
    }


@router.post("/{circle_id}/join")
async def join(circle_id: UUID, body: JoinRequest | None, session: DbSession, member: CurrentMember, lang: Locale) -> dict:
    """[FR020/FR115] Join an open circle, or ask to join one that screens first."""
    try:
        result = await circle.request_join(session, circle_id=circle_id, member_id=member.member_id, answers=body.answers if body else None)
    except circle.CircleNotFound as exc:
        raise HTTPException(status_code=404, detail=translate("circle.notFound", lang)) from exc
    if result in ("pending", "already_pending"):
        return {"status": "pending"}
    return {"status": "joined", **_out(await circle.get(session, circle_id=circle_id, viewer_member_id=member.member_id))}


class PollOptionIn(BaseModel):
    label: str
    option_time: datetime | None = None
    occurrence_id: UUID | None = None


class CreatePollRequest(BaseModel):
    question: str = Field(min_length=1, max_length=160)
    kind: str = "date"  # [FR120] 'date' (which day?) or 'activity' (which one shall we go to?)
    options: list[PollOptionIn] = Field(default_factory=list)


class VoteRequest(BaseModel):
    option_id: UUID
    picked: bool = True


class GroupRequest(BaseModel):
    name: str = Field(min_length=1, max_length=80)
    description: str | None = None


class AttachGroupRequest(BaseModel):
    group_id: UUID | None = None


class FundraiserRequest(BaseModel):
    title: str = Field(min_length=1, max_length=120)
    purpose: str | None = None
    target_paise: int | None = None
    closes_on: str | None = None


class PledgeRequest(BaseModel):
    amount_paise: int | None = None  # None takes the promise back
    note: str | None = None


class MarkPaidRequest(BaseModel):
    member_id: UUID
    paid: bool = True


@router.get("/groups")
async def list_groups(session: DbSession, member: CurrentMember) -> list[dict]:
    """[FR123] Umbrellas a circle can sit under."""
    return await circle.groups(session)


@router.post("/groups", status_code=201)
async def create_group(body: GroupRequest, session: DbSession, member: CurrentMember) -> dict:
    """[FR123] Start an umbrella for chapters in different cities."""
    try:
        group_id = await circle.create_group(session, name=body.name, description=body.description, member_id=member.member_id)
    except circle.InvalidCircle as exc:
        raise HTTPException(status_code=422, detail={"fields": exc.fields}) from exc
    return {"id": str(group_id)}


@router.get("/groups/{group_id}/chapters")
async def group_chapters(group_id: UUID, session: DbSession, member: CurrentMember) -> list[dict]:
    """[FR123] The chapters under one umbrella."""
    return await circle.chapters(session, group_id=group_id)


@router.get("/groups/{group_id}")
async def group_detail(group_id: UUID, session: DbSession, member: CurrentMember, lang: Locale) -> dict:
    """[FR123/FR126] The umbrella's own page: its chapters and its update feed."""
    detail = await circle.group_detail(session, group_id=group_id, viewer_member_id=member.member_id)
    if detail is None:
        raise HTTPException(status_code=404, detail=translate("circle.notFound", lang))
    return detail


@router.post("/groups/{group_id}/updates", status_code=201)
async def post_group_update(group_id: UUID, body: GroupUpdateRequest, session: DbSession, member: CurrentMember, lang: Locale) -> dict:
    """[FR126] One message to every chapter — only the umbrella's own admin may post it."""
    try:
        update_id = await circle.post_group_update(session, group_id=group_id, member_id=member.member_id, message=body.message)
    except circle.NotGroupAdmin as exc:
        raise HTTPException(status_code=403, detail=translate("samaj.notAdmin", lang)) from exc
    except circle.InvalidGroupUpdate as exc:
        raise HTTPException(status_code=422, detail=translate("samaj.tooMany", lang)) from exc
    return {"id": str(update_id)}


@router.post("/{circle_id}/group")
async def attach_group(circle_id: UUID, body: AttachGroupRequest, session: DbSession, member: CurrentMember, lang: Locale) -> dict:
    """[FR123] Put this circle under an umbrella, or take it out."""
    ok = await circle.set_group(session, circle_id=circle_id, actor_member_id=member.member_id, group_id=body.group_id)
    if not ok:
        raise HTTPException(status_code=403, detail=translate("circle.notOrganizer", lang))
    return {"ok": True}


@router.get("/{circle_id}/fundraisers")
async def circle_fundraisers(circle_id: UUID, session: DbSession, member: CurrentMember) -> list[dict]:
    """[FR124] The circle's drives and their totals (never individual amounts)."""
    return await circle.fundraisers(session, circle_id=circle_id, member_id=member.member_id)


@router.post("/{circle_id}/fundraisers", status_code=201)
async def create_fundraiser(circle_id: UUID, body: FundraiserRequest, session: DbSession, member: CurrentMember) -> dict:
    """[FR124] Start a drive for something the community needs."""
    try:
        fundraiser_id = await circle.create_fundraiser(
            session,
            circle_id=circle_id,
            member_id=member.member_id,
            title=body.title,
            purpose=body.purpose,
            target_paise=body.target_paise,
            closes_on=body.closes_on,
        )
    except circle.InvalidFundraiser as exc:
        raise HTTPException(status_code=422, detail={"fields": exc.fields}) from exc
    return {"id": str(fundraiser_id)}


@router.post("/{circle_id}/fundraisers/{fundraiser_id}/pledge", status_code=204)
async def pledge(circle_id: UUID, fundraiser_id: UUID, body: PledgeRequest, session: DbSession, member: CurrentMember) -> None:
    """[FR124] Promise an amount (or take the promise back). No money moves — blocker B1."""
    try:
        await circle.pledge(session, fundraiser_id=fundraiser_id, member_id=member.member_id, amount_paise=body.amount_paise, note=body.note)
    except circle.InvalidFundraiser as exc:
        raise HTTPException(status_code=422, detail={"fields": exc.fields}) from exc


@router.get("/{circle_id}/fundraisers/{fundraiser_id}/pledges")
async def pledge_list(circle_id: UUID, fundraiser_id: UUID, session: DbSession, member: CurrentMember) -> list[dict]:
    """[FR124] Organizers only — who promised what, so it can be reconciled."""
    return await circle.pledge_list(session, fundraiser_id=fundraiser_id, viewer_member_id=member.member_id)


@router.post("/{circle_id}/fundraisers/{fundraiser_id}/paid")
async def mark_paid(circle_id: UUID, fundraiser_id: UUID, body: MarkPaidRequest, session: DbSession, member: CurrentMember, lang: Locale) -> dict:
    """[FR124] The organizer ticks off what has actually arrived."""
    ok = await circle.mark_pledge_paid(session, fundraiser_id=fundraiser_id, member_id=body.member_id, actor_member_id=member.member_id, paid=body.paid)
    if not ok:
        raise HTTPException(status_code=403, detail=translate("circle.notOrganizer", lang))
    return {"ok": True}


@router.post("/{circle_id}/fundraisers/{fundraiser_id}/close", status_code=204)
async def close_fundraiser(circle_id: UUID, fundraiser_id: UUID, session: DbSession, member: CurrentMember) -> None:
    """[FR124] The drive is over."""
    await circle.close_fundraiser(session, fundraiser_id=fundraiser_id, actor_member_id=member.member_id)


@router.get("/{circle_id}/polls")
async def circle_polls(circle_id: UUID, session: DbSession, member: CurrentMember) -> list[dict]:
    """[FR120] The circle's questions. RLS returns nothing to anyone outside it."""
    return await circle.polls(session, circle_id=circle_id, member_id=member.member_id)


@router.post("/{circle_id}/polls", status_code=201)
async def create_poll(circle_id: UUID, body: CreatePollRequest, session: DbSession, member: CurrentMember) -> dict:
    """[FR120] Ask the circle which day, or which activity."""
    try:
        poll_id = await circle.create_poll(
            session,
            circle_id=circle_id,
            member_id=member.member_id,
            question=body.question,
            kind=body.kind,
            options=[o.model_dump() for o in body.options],
        )
    except circle.InvalidPoll as exc:
        raise HTTPException(status_code=422, detail={"fields": exc.fields}) from exc
    return {"id": str(poll_id)}


@router.post("/{circle_id}/polls/{poll_id}/vote", status_code=204)
async def vote_in_poll(circle_id: UUID, poll_id: UUID, body: VoteRequest, session: DbSession, member: CurrentMember) -> None:
    """[FR120] Pick an option or take it back; several picks are allowed."""
    await circle.vote(session, poll_id=poll_id, option_id=body.option_id, member_id=member.member_id, picked=body.picked)


@router.post("/{circle_id}/polls/{poll_id}/close", status_code=204)
async def close_poll(circle_id: UUID, poll_id: UUID, session: DbSession, member: CurrentMember) -> None:
    """[FR120] Settled — only the person who asked can do this."""
    await circle.close_poll(session, poll_id=poll_id, member_id=member.member_id)


@router.get("/{circle_id}/join-prompt")
async def join_prompt(circle_id: UUID, session: DbSession, member: CurrentMember, lang: Locale) -> dict:
    """[FR115] The questions to answer before asking to join — readable without being a member."""
    prompt = await circle.join_prompt(session, circle_id=circle_id, member_id=member.member_id)
    if prompt is None:
        raise HTTPException(status_code=404, detail=translate("circle.notFound", lang))
    return prompt


class RoleRequest(BaseModel):
    member_id: UUID
    role: str  # [FR121] 'assistant' to share the work, 'member' to step back down


@router.post("/{circle_id}/roles")
async def set_circle_role(circle_id: UUID, body: RoleRequest, session: DbSession, member: CurrentMember, lang: Locale) -> dict:
    """[FR121] Ask someone to help run this circle."""
    ok = await circle.set_role(session, circle_id=circle_id, actor_member_id=member.member_id, member_id=body.member_id, role=body.role)
    if not ok:
        raise HTTPException(status_code=403, detail=translate("circle.notOrganizer", lang))
    return {"ok": True, "role": body.role}


@router.get("/{circle_id}/requests")
async def join_requests(circle_id: UUID, session: DbSession, member: CurrentMember) -> list[dict]:
    """[FR115] Organizer only — the definer returns nothing to anyone else."""
    return await circle.pending_requests(session, circle_id=circle_id, viewer_member_id=member.member_id)


@router.post("/{circle_id}/requests/{request_id}/decide")
async def decide_join_request(circle_id: UUID, request_id: UUID, body: DecideRequest, session: DbSession, member: CurrentMember, lang: Locale) -> dict:
    """[FR115] The organizer lets someone in, or does not."""
    try:
        await circle.decide_request(session, circle_id=circle_id, request_id=request_id, actor_member_id=member.member_id, approve=body.approve)
    except circle.NotMember as exc:
        raise HTTPException(status_code=403, detail=translate("circle.notOrganizer", lang)) from exc
    return {"ok": True, "approved": body.approve}


@router.post("/{circle_id}/leave")
async def leave(circle_id: UUID, session: DbSession, member: CurrentMember) -> dict:
    await circle.leave(session, circle_id=circle_id, member_id=member.member_id)
    return {"ok": True}


@router.post("/{circle_id}/members", status_code=201)
async def add_member(circle_id: UUID, body: MemberRefRequest, session: DbSession, member: CurrentMember, lang: Locale) -> dict:
    try:
        await circle.add_member(session, circle_id=circle_id, actor_member_id=member.member_id, member_id=body.member_id)
    except circle.CircleNotFound as exc:
        raise HTTPException(status_code=404, detail=translate("circle.notFound", lang)) from exc
    except circle.NotMember as exc:
        raise HTTPException(status_code=403, detail="Only the circle creator can add members.") from exc
    return {"ok": True}
