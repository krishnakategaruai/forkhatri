"""Circle endpoints — FR020-FR025, FR028 (organization scope)."""

from __future__ import annotations

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
    locality_city: str | None = None  # approximate home place (FR038); omit for "anywhere"
    locality_locality: str | None = None


class MemberRefRequest(BaseModel):
    member_id: UUID


class OrgScopeRequest(BaseModel):
    display_name: str = Field(min_length=1, max_length=120)


class SuggestionResponse(BaseModel):
    accept: bool


def _out(c: circle.Circle) -> dict:
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
        )
    except circle.InvalidCircle as exc:
        raise HTTPException(status_code=422, detail={"fields": exc.fields}) from exc
    return _out(c)


@router.get("/suggestions")
async def suggestions(session: DbSession, member: CurrentMember) -> list[dict]:
    """[FR022] Pending organic circle-formation suggestions for me."""
    out = []
    for s in await circle.pending_suggestions(session, member_id=member.member_id):
        names = identity.display_names_for(s["member_ids"])
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
    names = identity.display_names_for([r[0] for r in rows])
    memory = None
    try:
        memory = await circle.community_memory(session, circle_id=circle_id, viewer_member_id=member.member_id)
    except circle.NotMember:
        memory = None
    v = await discovery.viewer_profile(session, member.member_id)
    occs = await activity.list_visible(session, city=None, start=None, end=None, circle_id=circle_id)
    cards = await discovery.build_cards(session, occs, v, rank=False)
    return {
        **_out(c),
        "members": [{"member_id": str(m), "display_name": names[m].display_name, "avatar": names[m].avatar, "role": role} for (m, role, _j) in rows],
        "memory": {**memory, "first_activity_at": memory["first_activity_at"].isoformat() if memory and memory.get("first_activity_at") else None} if memory else None,
        "upcoming": [CardOut.from_card(x).model_dump(mode="json") for x in cards],
    }


@router.post("/{circle_id}/join")
async def join(circle_id: UUID, session: DbSession, member: CurrentMember, lang: Locale) -> dict:
    try:
        return _out(await circle.join(session, circle_id=circle_id, member_id=member.member_id))
    except circle.CircleNotFound as exc:
        raise HTTPException(status_code=404, detail=translate("circle.notFound", lang)) from exc
    except circle.NotMember as exc:
        raise HTTPException(status_code=403, detail="This circle is invite-only.") from exc


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
