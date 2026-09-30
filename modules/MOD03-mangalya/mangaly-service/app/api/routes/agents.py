"""Marriage agent endpoints (DEC-V1-033) — thin HTTP layer over
`components/agents/interface.py`.

Anyone signed in:
    GET  /agents/me                         my agent record (null if none)
    POST /agents/me                         apply, or update my details
    GET  /agents/offline-media/{id}/{file}  an offline profile's photo or biodata

Agent seat (`AgentAccount`: verified, membership live, bound as an RM):
    GET   /agents/clients                        clients with stage and counts
    POST  /agents/clients                        add one client (a profile made for them)
    POST  /agents/clients/import                 add many from an .xlsx/.csv sheet plus photos
    GET   /agents/clients/template               the sheet to fill
    PATCH /agents/clients/{assignment}/stage
    GET   /agents/clients/{assignment}/shared    what I shared with them, and their answers
    GET   /agents/contact/{account}              numbers (each look is written down for the family)
    POST  /agents/contact-open                   which of these people I may call
    POST  /agents/export/excel                   an .xlsx of biodata (logged)
    POST  /agents/export/biodata                 biodata for the print page (logged)
    GET   /agents/offline                        biodata of people not on Mangalya
    POST  /agents/offline                        add one
    POST  /agents/offline/{id}/archive
    POST  /agents/share                          profiles → clients
    GET   /agents/quota                          fair-use limits used (DEC-V1-034)

Family seat (the candidate, or a parent/guardian with `for_candidate`):
    GET  /agents/directory
    GET  /agents/dashboard                       Agent Connect, our agents, everything shared, activity
    POST /agents/choose | /agents/release
    PATCH /agents/privacy                        may verified agents see our number
    POST /agents/shared/{suggestion}/answer      liked | passed | ask
    GET  /agents/reports/suspects?day=           agents who opened our number before that day
    GET  /agents/reports | POST /agents/reports  report an unwanted call or message

Mangalya administrators (`Moderator`):
    GET  /agents/admin/applications
    POST /agents/admin/applications/{account}/review
    GET  /agents/admin/prices | PATCH /agents/admin/prices
    GET  /agents/admin/limits | PATCH /agents/admin/limits
"""

from __future__ import annotations

from datetime import date, datetime
from typing import Annotated, Any, Literal
from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from fastapi.responses import FileResponse, Response
from pydantic import BaseModel, Field

from app.api.deps import AuthenticatedAccount, DbSession, Locale
from app.api.operator_deps import Moderator
from app.api.rm_deps import RmAccount
from app.components.agents import interface as agents
from app.components.authorization import interface as authz
from app.components.authorization.context import AuthorizationDenied
from app.config import plans as catalogue
from app.i18n import translate

router = APIRouter(prefix="/agents", tags=["agents"])


def _error(code: int, key: str, lang: str, **params: object) -> HTTPException:
    return HTTPException(
        status_code=code,
        detail={"code": key, "message": translate(f"agents.error.{key}", lang, **params)},
    )


def _iso(value: datetime | date | None) -> str | None:
    return value.isoformat() if value else None


async def get_agent_account(session: DbSession, rm_account_id: RmAccount, lang: Locale) -> UUID:
    """An RM seat that is an independent agent (not Mangalya staff)."""
    from sqlalchemy import text

    if not (await session.execute(text("SELECT mangaly_operations.is_agent()"))).scalar_one():
        raise _error(status.HTTP_403_FORBIDDEN, "notAgent", lang)
    return rm_account_id


AgentAccount = Annotated[UUID, Depends(get_agent_account)]


async def _family(session: DbSession, account_id: UUID, for_candidate: UUID | None) -> UUID:
    try:
        return await authz.resolve_context_account(
            session, acting_account_id=account_id, for_candidate=for_candidate
        )
    except AuthorizationDenied as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN) from exc


# ---------------------------------------------------------------------------
# Shapes
# ---------------------------------------------------------------------------


class AgentRecordOut(BaseModel):
    kind: str
    display_name: str
    business_name: str | None
    business_phone: str | None
    city: str | None
    languages: list[str]
    communities: list[str]
    years_active: int | None
    about: str | None
    verification_status: str
    applied_at: str | None
    verified_at: str | None
    membership_until: str | None
    live: bool


def _record_out(r: agents.AgentRecord) -> AgentRecordOut:
    return AgentRecordOut(
        kind=r.kind,
        display_name=r.display_name,
        business_name=r.business_name,
        business_phone=r.business_phone,
        city=r.city,
        languages=r.languages,
        communities=r.communities,
        years_active=r.years_active,
        about=r.about,
        verification_status=r.verification_status,
        applied_at=_iso(r.applied_at),
        verified_at=_iso(r.verified_at),
        membership_until=_iso(r.membership_until),
        live=r.live,
    )


class ApplyBody(BaseModel):
    display_name: str = Field(min_length=2, max_length=120)
    business_name: str | None = Field(default=None, max_length=160)
    business_phone: str | None = Field(default=None, max_length=32)
    city: str = Field(min_length=2, max_length=120)
    languages: list[str] = Field(default_factory=list, max_length=8)
    communities: list[str] = Field(default_factory=list, max_length=12)
    years_active: int | None = Field(default=None, ge=0, le=80)
    about: str | None = Field(default=None, max_length=1200)


class DirectoryAgentOut(BaseModel):
    account_id: str
    display_name: str
    business_name: str | None
    business_phone: str | None
    city: str | None
    languages: list[str]
    communities: list[str]
    years_active: int | None
    about: str | None
    photo_url: str | None
    verified_at: str | None
    families: int
    marriages: int


def _directory_out(a: agents.DirectoryAgent) -> DirectoryAgentOut:
    return DirectoryAgentOut(
        account_id=str(a.account_id),
        display_name=a.display_name,
        business_name=a.business_name,
        business_phone=a.business_phone,
        city=a.city,
        languages=a.languages,
        communities=a.communities,
        years_active=a.years_active,
        about=a.about,
        photo_url=a.photo_url,
        verified_at=_iso(a.verified_at),
        families=a.families,
        marriages=a.marriages,
    )


class ClientOut(BaseModel):
    assignment_id: str
    account_id: str
    name: str | None
    age: int | None
    gender: str | None
    city: str | None
    looking_for: str | None
    photo_url: str | None
    stage: str
    stage_changed_at: str
    origin: str
    assigned_at: str
    made_by_me: bool
    claimed: bool
    suggestions: int
    liked: int


class ImportRowOut(BaseModel):
    row: int
    name: str | None
    status: str
    account_id: str | None
    error: str | None
    warnings: list[str]


class ContactOut(BaseModel):
    account_id: str
    display_name: str | None
    relation: str
    phone: str | None
    email: str | None = None


def _contact_out(p: agents.ContactPerson) -> ContactOut:
    return ContactOut(
        account_id=str(p.account_id),
        display_name=p.display_name,
        relation=p.relation,
        phone=p.phone,
        email=p.email,
    )


_LIMIT_KEYS = {
    "contacts_per_day": "contactsPerDay",
    "contacts_per_month": "contactsPerMonth",
    "contact_suspended": "contactSuspended",
    "export_others_per_day": "exportOthersPerDay",
    "profiles_added_per_day": "profilesAddedPerDay",
}


async def _limit_error(session: DbSession, exc: agents.LimitReached, lang: str) -> HTTPException:
    """429 with the agent's own numbers in the sentence (DEC-V1-034)."""
    q = await agents.quota(session)
    limit = {
        "contacts_per_day": q.contacts_per_day if q else None,
        "contacts_per_month": q.contacts_per_month if q else None,
        "export_others_per_day": q.export_others_per_day if q else None,
        "profiles_added_per_day": q.profiles_added_per_day if q else None,
    }.get(exc.which)
    left = exc.limit if exc.which == "export_others_per_day" else None
    code = (
        status.HTTP_403_FORBIDDEN
        if exc.which == "contact_suspended"
        else status.HTTP_429_TOO_MANY_REQUESTS
    )
    return _error(code, _LIMIT_KEYS[exc.which], lang, limit=limit or 0, left=left or 0)


class IdsBody(BaseModel):
    ids: list[UUID] = Field(min_length=1, max_length=agents.MAX_EXPORT_PEOPLE)


class OfflineOut(BaseModel):
    id: str
    name: str
    gender: str
    age: int | None
    date_of_birth: str | None
    city: str | None
    details: dict[str, Any]
    photo_urls: list[str]
    biodata_url: str | None
    biodata_kind: str | None
    contact_note: str | None
    created_at: str


def _offline_out(o: agents.OfflineProfile) -> OfflineOut:
    return OfflineOut(
        id=str(o.id),
        name=o.name,
        gender=o.gender,
        age=o.age,
        date_of_birth=_iso(o.date_of_birth),
        city=o.city,
        details=o.details,
        photo_urls=o.photo_urls,
        biodata_url=o.biodata_url,
        biodata_kind=o.biodata_kind,
        contact_note=o.contact_note,
        created_at=o.created_at.isoformat(),
    )


class ShareBody(BaseModel):
    assignment_ids: list[UUID] = Field(min_length=1, max_length=100)
    member_ids: list[UUID] = Field(default_factory=list, max_length=100)
    offline_ids: list[UUID] = Field(default_factory=list, max_length=100)
    note: str | None = Field(default=None, max_length=1000)


class SharedOut(BaseModel):
    suggestion_id: str
    assignment_id: str
    agent_account_id: str
    note: str | None
    shared_at: str
    decision: str | None
    decided_at: str | None
    question: str | None
    member_account_id: str | None
    person: dict[str, Any] | None = None  # the Discover card of a Mangalya member
    offline: OfflineOut | None = None


async def _shared_out(session: DbSession, items: list[agents.SharedProfile]) -> list[SharedOut]:
    from app.api.routes.rm import _people

    people = await _people(session, [s.member_account_id for s in items if s.member_account_id])
    return [
        SharedOut(
            suggestion_id=str(s.suggestion_id),
            assignment_id=str(s.assignment_id),
            agent_account_id=str(s.agent_account_id),
            note=s.note,
            shared_at=s.shared_at.isoformat(),
            decision=s.decision,
            decided_at=_iso(s.decided_at),
            question=s.question,
            member_account_id=str(s.member_account_id) if s.member_account_id else None,
            person=(p.model_dump() if (p := people.get(s.member_account_id)) else None)
            if s.member_account_id
            else None,
            offline=_offline_out(s.offline) if s.offline else None,
        )
        for s in items
    ]


# ---------------------------------------------------------------------------
# Anyone signed in
# ---------------------------------------------------------------------------


@router.get("/me", response_model=AgentRecordOut | None)
async def me(session: DbSession, account_id: AuthenticatedAccount) -> AgentRecordOut | None:
    record = await agents.my_record(session)
    return _record_out(record) if record else None


@router.post("/me", response_model=AgentRecordOut)
async def apply(
    body: ApplyBody, session: DbSession, account_id: AuthenticatedAccount, lang: Locale
) -> AgentRecordOut:
    """Apply to be a marriage agent (Mangalya checks the details before the
    agent goes live), or update the details later."""
    try:
        async with session.begin_nested():
            record = await agents.apply(
                session,
                display_name=body.display_name.strip(),
                business_name=(body.business_name or "").strip() or None,
                business_phone=(body.business_phone or "").strip() or None,
                city=body.city.strip(),
                languages=[x.strip() for x in body.languages if x.strip()],
                communities=[x.strip() for x in body.communities if x.strip()],
                years_active=body.years_active,
                about=(body.about or "").strip() or None,
            )
    except Exception as exc:
        if "already Mangalya staff" in str(exc):
            raise _error(status.HTTP_409_CONFLICT, "alreadyStaff", lang) from exc
        raise
    return _record_out(record)


@router.get("/offline-media/{offline_id}/{filename}")
async def offline_media(
    offline_id: UUID,
    filename: str,
    session: DbSession,
    account_id: AuthenticatedAccount,
    lang: Locale,
) -> FileResponse:
    # The agent reads their own files in their RM seat; a family in theirs.
    from app.components.assisted_matching import interface as assisted
    from app.db.session import VAR_OPERATOR_ROLE, set_local

    if await assisted.is_rm(session, account_id=account_id):
        await set_local(session, VAR_OPERATOR_ROLE, "relationship_manager")
    path = await agents.offline_media_path(session, offline_id=offline_id, filename=filename)
    if path is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    return FileResponse(path, headers={"Cache-Control": "private, max-age=300"})


# ---------------------------------------------------------------------------
# Agent seat
# ---------------------------------------------------------------------------


def _client_out(c: agents.Client) -> ClientOut:
    return ClientOut(
        assignment_id=str(c.assignment_id),
        account_id=str(c.account_id),
        name=c.name,
        age=c.age,
        gender=c.gender,
        city=c.city,
        looking_for=c.looking_for,
        photo_url=c.photo_url,
        stage=c.stage,
        stage_changed_at=c.stage_changed_at.isoformat(),
        origin=c.origin,
        assigned_at=c.assigned_at.isoformat(),
        made_by_me=c.made_by_me,
        claimed=c.claimed,
        suggestions=c.suggestions,
        liked=c.liked,
    )


@router.get("/clients", response_model=list[ClientOut])
async def clients(session: DbSession, agent: AgentAccount) -> list[ClientOut]:
    return [_client_out(c) for c in await agents.list_clients(session, agent_account_id=agent)]


async def _require_face_check(session: DbSession, agent: UUID, lang: str) -> None:
    # [DEC-V1-025] Whoever makes a profile for someone is a phone- and
    # face-verified person — the parent rule, applied to agents too.
    from app.components.trust import interface as trust

    if not await trust.is_face_verified(session, account_id=agent):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "code": "verification_required",
                "message": translate("verification.error.required", lang),
            },
        )


def _consent_required(lang: str) -> HTTPException:
    return _error(status.HTTP_422_UNPROCESSABLE_ENTITY, "consentRequired", lang)


@router.post("/clients", status_code=status.HTTP_201_CREATED)
async def add_client(
    session: DbSession,
    agent: AgentAccount,
    lang: Locale,
    mobile: str = Form(..., min_length=6, max_length=32),  # noqa: B008
    name: str = Form(..., min_length=1, max_length=200),  # noqa: B008
    date_of_birth: date = Form(...),  # noqa: B008
    gender: Literal["male", "female"] = Form(...),  # noqa: B008
    looking_for: Literal["bride", "groom"] = Form(...),  # noqa: B008
    city: str = Form(..., min_length=1, max_length=200),  # noqa: B008
    consent: bool = Form(False),  # noqa: B008
    photo: UploadFile = File(...),  # noqa: B008
) -> dict[str, str]:
    """One client: a profile made for them (the phone owner is told, and takes
    it over or removes it), joined to this agent."""
    from app.components.identity_bridge import platform
    from app.components.profile import interface as profile
    from app.components.profile.storage import UnsupportedMedia

    if not consent:
        raise _consent_required(lang)
    await _require_face_check(session, agent, lang)
    try:
        await agents.require_room_to_add(session)
    except agents.LimitReached as exc:
        raise await _limit_error(session, exc, lang) from exc
    try:
        account, _ = await agents.add_client(
            session,
            agent_account_id=agent,
            phone=mobile,
            name=name.strip(),
            date_of_birth=date_of_birth,
            gender=gender,
            looking_for=looking_for,
            city=city.strip(),
            photo=photo,
            lang=lang,
        )
    except platform.MemberExists as exc:
        raise _error(status.HTTP_409_CONFLICT, "numberHasAccount", lang) from exc
    except platform.InvalidPhone as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=translate("profile.error.childPhone", lang),
        ) from exc
    except platform.PlatformIdentityUnavailable as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="identity unavailable"
        ) from exc
    except profile.TooYoung as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=translate("profile.error.tooYoung", lang, years=exc.required_years),
        ) from exc
    except UnsupportedMedia as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=translate("profile.error.unsupportedPhoto", lang),
        ) from exc
    return {"account_id": str(account)}


@router.post("/clients/import", response_model=list[ImportRowOut])
async def import_clients(
    session: DbSession,
    agent: AgentAccount,
    lang: Locale,
    sheet: UploadFile = File(...),  # noqa: B008
    photos: list[UploadFile] = File(default=[]),  # noqa: B008
    consent: bool = Form(False),  # noqa: B008
) -> list[ImportRowOut]:
    """Many clients at once: an .xlsx or .csv (the template's columns) and the
    photos it names in its `photo` column. Each row succeeds or fails alone."""
    if not consent:
        raise _consent_required(lang)
    await _require_face_check(session, agent, lang)
    content = await sheet.read()
    try:
        rows = agents.read_sheet(sheet.filename or "", content)
    except agents.ImportFileUnreadable as exc:
        raise _error(status.HTTP_422_UNPROCESSABLE_ENTITY, "sheetUnreadable", lang) from exc
    if not rows:
        raise _error(status.HTTP_422_UNPROCESSABLE_ENTITY, "sheetEmpty", lang)
    if len(rows) > agents.MAX_IMPORT_ROWS:
        raise _error(
            status.HTTP_422_UNPROCESSABLE_ENTITY, "sheetTooLong", lang, limit=agents.MAX_IMPORT_ROWS
        )
    by_name = {(p.filename or "").strip().lower(): p for p in photos if p.filename}
    results = await agents.import_clients(
        session, agent_account_id=agent, rows=rows, photos=by_name, lang=lang
    )
    return [
        ImportRowOut(
            row=r.row,
            name=r.name,
            status=r.status,
            account_id=str(r.account_id) if r.account_id else None,
            error=r.error,
            warnings=r.warnings,
        )
        for r in results
    ]


@router.get("/clients/template")
async def template(agent: AgentAccount) -> Response:
    return Response(
        content=agents.template_workbook(),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": 'attachment; filename="mangaly-clients.xlsx"'},
    )


class StageBody(BaseModel):
    stage: Literal["searching", "proposal_sent", "meeting", "engaged", "married", "paused"]


@router.patch("/clients/{assignment_id}/stage", status_code=status.HTTP_204_NO_CONTENT)
async def set_stage(
    assignment_id: UUID, body: StageBody, session: DbSession, agent: AgentAccount, lang: Locale
) -> None:
    try:
        await agents.set_stage(session, assignment_id=assignment_id, stage=body.stage)
    except agents.ClientNotFound as exc:
        raise _error(status.HTTP_404_NOT_FOUND, "clientNotFound", lang) from exc


@router.get("/clients/{assignment_id}/shared", response_model=list[SharedOut])
async def shared_with_client(
    assignment_id: UUID, session: DbSession, agent: AgentAccount
) -> list[SharedOut]:
    return await _shared_out(
        session, await agents.shared_by_agent(session, assignment_id=assignment_id)
    )


@router.get("/contact/{member_account_id}", response_model=list[ContactOut])
async def contact(
    member_account_id: UUID, session: DbSession, agent: AgentAccount, lang: Locale
) -> list[ContactOut]:
    try:
        people = await agents.contact(session, member_account_id=member_account_id)
    except agents.LimitReached as exc:
        raise await _limit_error(session, exc, lang) from exc
    if not people:
        raise _error(status.HTTP_403_FORBIDDEN, "contactClosed", lang)
    return [_contact_out(p) for p in people]


class ContactStateOut(BaseModel):
    open: list[str]
    opened: list[str]


@router.post("/contact-open", response_model=ContactStateOut)
async def contact_open(body: IdsBody, session: DbSession, agent: AgentAccount) -> ContactStateOut:
    """Which of these people the agent may open (the eye is drawn), and which
    they opened in the last 30 days (opening again is free)."""
    ids = list(body.ids)
    return ContactStateOut(
        open=[str(i) for i in await agents.contact_open(session, member_ids=ids)],
        opened=[str(i) for i in await agents.opened_recently(session, member_ids=ids)],
    )


class QuotaOut(BaseModel):
    contacts_today: int
    contacts_per_day: int
    contacts_month: int
    contacts_per_month: int
    exported_others_today: int
    export_others_per_day: int
    added_today: int
    profiles_added_per_day: int
    contact_suspended: bool


@router.get("/quota", response_model=QuotaOut)
async def quota(session: DbSession, agent: AgentAccount) -> QuotaOut:
    """What the agent has used of each fair-use limit (DEC-V1-034)."""
    q = await agents.quota(session)
    if q is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    return QuotaOut(**{k: getattr(q, k) for k in QuotaOut.model_fields})


def _export_labels(lang: str) -> dict[str, str]:
    keys = ("stamp", "name", "age", "gender", "city", "client", "phones", "yes")
    labels = {k: translate(f"agents.export.{k}", lang) for k in keys}
    for relation in ("self", "mother", "father", "guardian", "parent"):
        labels[f"relation.{relation}"] = translate(f"agents.relation.{relation}", lang)
    return labels


class ExportBody(IdsBody):
    with_contacts: bool = True


@router.post("/export/excel")
async def export_excel(
    body: ExportBody, session: DbSession, agent: AgentAccount, lang: Locale
) -> Response:
    """An .xlsx of the chosen people's biodata, stamped with the agent's name.
    Written down for every family in it."""
    entries = await agents.biodata_entries(
        session, agent_account_id=agent, member_ids=list(body.ids), with_contacts=body.with_contacts
    )
    if not entries:
        raise _error(status.HTTP_404_NOT_FOUND, "nothingToExport", lang)
    others = sum(1 for e in entries if not e.is_client)
    try:
        await agents.require_room_to_export(session, others=others)
    except agents.LimitReached as exc:
        raise await _limit_error(session, exc, lang) from exc
    record = await agents.my_record(session)
    name = (record.business_name or record.display_name) if record else ""
    await agents.record_export(
        session,
        agent_account_id=agent,
        kind="excel",
        member_ids=[e.account_id for e in entries],
        others_count=others,
    )
    content = agents.excel_workbook(entries, agent_name=name, labels=_export_labels(lang))
    return Response(
        content=content,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={
            "Content-Disposition": f'attachment; filename="mangaly-biodata-{date.today().isoformat()}.xlsx"'
        },
    )


class BiodataOut(BaseModel):
    account_id: str
    is_client: bool
    name: str | None
    age: int | None
    gender: str | None
    city: str | None
    photo_url: str | None
    biodata: dict[str, dict[str, Any]]
    contacts: list[ContactOut]


class BiodataExportOut(BaseModel):
    agent_name: str
    agent_phone: str | None
    made_on: str
    people: list[BiodataOut]


@router.post("/export/biodata", response_model=BiodataExportOut)
async def export_biodata(
    body: ExportBody, session: DbSession, agent: AgentAccount, lang: Locale
) -> BiodataExportOut:
    """Biodata for the print page (one page per person, saved as PDF by the
    browser), stamped with the agent. Written down for every family in it."""
    entries = await agents.biodata_entries(
        session, agent_account_id=agent, member_ids=list(body.ids), with_contacts=body.with_contacts
    )
    if not entries:
        raise _error(status.HTTP_404_NOT_FOUND, "nothingToExport", lang)
    others = sum(1 for e in entries if not e.is_client)
    try:
        await agents.require_room_to_export(session, others=others)
    except agents.LimitReached as exc:
        raise await _limit_error(session, exc, lang) from exc
    record = await agents.my_record(session)
    await agents.record_export(
        session,
        agent_account_id=agent,
        kind="biodata",
        member_ids=[e.account_id for e in entries],
        others_count=others,
    )
    return BiodataExportOut(
        agent_name=(record.business_name or record.display_name) if record else "",
        agent_phone=record.business_phone if record else None,
        made_on=date.today().isoformat(),
        people=[
            BiodataOut(
                account_id=str(e.account_id),
                is_client=e.is_client,
                name=e.name,
                age=e.age,
                gender=e.gender,
                city=e.city,
                photo_url=e.photo_url,
                biodata={
                    c: v
                    for c, v in e.biodata.items()
                    if c
                    not in ("partner_preference", "self_scales", "outlook", "openly", "in_my_words")
                },
                contacts=[_contact_out(p) for p in e.contacts],
            )
            for e in entries
        ],
    )


@router.get("/offline", response_model=list[OfflineOut])
async def offline_list(session: DbSession, agent: AgentAccount) -> list[OfflineOut]:
    return [
        _offline_out(o) for o in await agents.list_offline_profiles(session, agent_account_id=agent)
    ]


@router.post("/offline", response_model=OfflineOut, status_code=status.HTTP_201_CREATED)
async def offline_add(
    session: DbSession,
    agent: AgentAccount,
    lang: Locale,
    name: str = Form(..., min_length=1, max_length=200),  # noqa: B008
    gender: Literal["male", "female"] = Form(...),  # noqa: B008
    date_of_birth: date | None = Form(None),  # noqa: B008
    city: str | None = Form(None, max_length=200),  # noqa: B008
    contact_note: str | None = Form(None, max_length=500),  # noqa: B008
    details: str = Form("{}", max_length=8000),  # noqa: B008 — JSON object of OFFLINE_DETAIL_KEYS
    consent: bool = Form(False),  # noqa: B008
    photos: list[UploadFile] = File(default=[]),  # noqa: B008
    biodata: UploadFile | None = File(None),  # noqa: B008
) -> OfflineOut:
    """A biodata of someone not on Mangalya (a photo or the biodata file is
    required: families expect to see the person)."""
    import json

    from app.components.profile.storage import UnsupportedMedia

    if not consent:
        raise _consent_required(lang)
    # A browser sends an empty file for an empty file field.
    photos = [p for p in photos if p.filename]
    if biodata is not None and not biodata.filename:
        biodata = None
    if not photos and biodata is None:
        raise _error(status.HTTP_422_UNPROCESSABLE_ENTITY, "offlineNeedsPhoto", lang)
    try:
        await agents.require_room_to_add(session)
    except agents.LimitReached as exc:
        raise await _limit_error(session, exc, lang) from exc
    try:
        parsed = json.loads(details or "{}")
        if not isinstance(parsed, dict):
            raise ValueError
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="details"
        ) from exc
    try:
        created = await agents.create_offline_profile(
            session,
            agent_account_id=agent,
            name=name.strip(),
            gender=gender,
            date_of_birth=date_of_birth,
            city=(city or "").strip() or None,
            details=parsed,
            contact_note=(contact_note or "").strip() or None,
            photos=photos,
            biodata=biodata,
        )
    except UnsupportedMedia as exc:
        raise _error(status.HTTP_422_UNPROCESSABLE_ENTITY, "unsupportedFile", lang) from exc
    return _offline_out(created)


@router.post("/offline/{offline_id}/archive", status_code=status.HTTP_204_NO_CONTENT)
async def offline_archive(offline_id: UUID, session: DbSession, agent: AgentAccount) -> None:
    await agents.archive_offline_profile(session, offline_id=offline_id)


@router.post("/share")
async def share(
    body: ShareBody, session: DbSession, agent: AgentAccount, lang: Locale
) -> dict[str, int]:
    if not body.member_ids and not body.offline_ids:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="nothing to share"
        )
    try:
        made = await agents.share(
            session,
            agent_account_id=agent,
            assignment_ids=list(body.assignment_ids),
            member_ids=list(body.member_ids),
            offline_ids=list(body.offline_ids),
            note=body.note,
        )
    except agents.ClientNotFound as exc:
        raise _error(status.HTTP_404_NOT_FOUND, "clientNotFound", lang) from exc
    return {"shared": made}


# ---------------------------------------------------------------------------
# Family seat
# ---------------------------------------------------------------------------


@router.get("/directory", response_model=list[DirectoryAgentOut])
async def directory(
    session: DbSession, account_id: AuthenticatedAccount, city: str | None = None
) -> list[DirectoryAgentOut]:
    return [_directory_out(a) for a in await agents.directory(session, city=city)]


class FamilyAgentOut(BaseModel):
    assignment_id: str
    agent: DirectoryAgentOut | None
    stage: str
    origin: str
    assigned_at: str


class ActivityOut(BaseModel):
    agent_account_id: str
    display_name: str | None
    business_name: str | None
    kind: str
    at: str


class DashboardOut(BaseModel):
    candidate_account_id: str
    may_decide: bool
    agent_connect_until: str | None
    agents_may_see_contact: bool | None
    agents: list[FamilyAgentOut]
    shared: list[SharedOut]
    activity: list[ActivityOut]


@router.get("/dashboard", response_model=DashboardOut)
async def dashboard(
    session: DbSession, account_id: AuthenticatedAccount, for_candidate: UUID | None = None
) -> DashboardOut:
    """The family's agent dashboard: whether they hold Agent Connect, the
    agents working for them, everything shared (both kinds), and who opened
    their number or exported them."""
    member = await _family(session, account_id, for_candidate)
    family_agents = await agents.family_agents(session, member_account_id=member)
    until = await agents.agent_connect_until(session, member_account_id=member)
    return DashboardOut(
        candidate_account_id=str(member),
        may_decide=await agents.may_decide_for(session, acting=account_id, member=member),
        agent_connect_until=_iso(until),
        agents_may_see_contact=await agents.agents_may_see_contact(
            session, member_account_id=member
        ),
        agents=[
            FamilyAgentOut(
                assignment_id=str(f.assignment_id),
                agent=_directory_out(f.agent) if f.agent else None,
                stage=f.stage,
                origin=f.origin,
                assigned_at=f.assigned_at.isoformat(),
            )
            for f in family_agents
        ],
        shared=await _shared_out(
            session, await agents.shared_with_family(session, member_account_id=member)
        ),
        activity=[
            ActivityOut(
                agent_account_id=str(a.agent_account_id),
                display_name=a.display_name,
                business_name=a.business_name,
                kind=a.kind,
                at=a.at.isoformat(),
            )
            for a in await agents.activity_for_family(session, member_account_id=member)
        ],
    )


class ChooseBody(BaseModel):
    agent_account_id: UUID
    for_candidate: UUID | None = None


@router.post("/choose", status_code=status.HTTP_201_CREATED)
async def choose(
    body: ChooseBody, session: DbSession, account_id: AuthenticatedAccount, lang: Locale
) -> dict[str, str]:
    member = await _family(session, account_id, body.for_candidate)
    if await agents.agent_connect_until(session, member_account_id=member) is None:
        raise _error(status.HTTP_402_PAYMENT_REQUIRED, "needsAgentConnect", lang)
    try:
        assignment = await agents.choose(
            session, member_account_id=member, agent_account_id=body.agent_account_id
        )
    except agents.NotAllowed as exc:
        raise _error(status.HTTP_403_FORBIDDEN, "parentsDecide", lang) from exc
    except agents.ClientNotFound as exc:
        raise _error(status.HTTP_404_NOT_FOUND, "agentNotLive", lang) from exc
    return {"assignment_id": str(assignment)}


@router.post("/release", status_code=status.HTTP_204_NO_CONTENT)
async def release(
    body: ChooseBody, session: DbSession, account_id: AuthenticatedAccount, lang: Locale
) -> None:
    member = await _family(session, account_id, body.for_candidate)
    try:
        await agents.release(
            session, member_account_id=member, agent_account_id=body.agent_account_id
        )
    except agents.NotAllowed as exc:
        raise _error(status.HTTP_403_FORBIDDEN, "parentsDecide", lang) from exc


class PrivacyBody(BaseModel):
    open: bool
    for_candidate: UUID | None = None


@router.patch("/privacy", status_code=status.HTTP_204_NO_CONTENT)
async def privacy(
    body: PrivacyBody, session: DbSession, account_id: AuthenticatedAccount, lang: Locale
) -> None:
    member = await _family(session, account_id, body.for_candidate)
    try:
        await agents.set_agents_may_see_contact(
            session, acting=account_id, member_account_id=member, open_=body.open
        )
    except agents.NotAllowed as exc:
        raise _error(status.HTTP_403_FORBIDDEN, "parentsDecide", lang) from exc


class AnswerBody(BaseModel):
    decision: Literal["liked", "passed", "ask"]
    question: str | None = Field(default=None, max_length=1000)
    for_candidate: UUID | None = None


@router.post("/shared/{suggestion_id}/answer", response_model=SharedOut)
async def answer(
    suggestion_id: UUID,
    body: AnswerBody,
    session: DbSession,
    account_id: AuthenticatedAccount,
    lang: Locale,
) -> SharedOut:
    from app.components.assisted_matching import interface as assisted

    member = await _family(session, account_id, body.for_candidate)
    if body.decision == "ask" and not (body.question or "").strip():
        raise _error(status.HTTP_422_UNPROCESSABLE_ENTITY, "questionRequired", lang)
    try:
        await assisted.decide_suggestion(
            session,
            suggestion_id=suggestion_id,
            decision=body.decision,
            member_account_id=member,
            question=body.question,
        )
    except assisted.NotFound as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND) from exc
    items = [
        s
        for s in await agents.shared_with_family(session, member_account_id=member)
        if s.suggestion_id == suggestion_id
    ]
    if not items:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    return (await _shared_out(session, items))[0]


# ---------------------------------------------------------------------------
# Mangalya administrators
# ---------------------------------------------------------------------------


class ApplicationOut(AgentRecordOut):
    account_id: str


@router.get("/admin/applications", response_model=list[ApplicationOut])
async def admin_applications(session: DbSession, operator: Moderator) -> list[ApplicationOut]:
    return [
        ApplicationOut(account_id=str(account), **_record_out(record).model_dump())
        for account, record in await agents.applications(session)
    ]


class ReviewBody(BaseModel):
    status: Literal["verified", "rejected"]


@router.post("/admin/applications/{account}/review", status_code=status.HTTP_204_NO_CONTENT)
async def admin_review(
    account: UUID, body: ReviewBody, session: DbSession, operator: Moderator
) -> None:
    if not await agents.review(session, account_id=account, status=body.status):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)


class PriceOut(BaseModel):
    plan_code: str
    term_months: int
    amount_paise: int
    catalogue_paise: int | None
    active: bool


@router.get("/admin/prices", response_model=list[PriceOut])
async def admin_prices(session: DbSession, operator: Moderator) -> list[PriceOut]:
    """Every plan term: the price in force, and the catalogue placeholder."""
    from sqlalchemy import text

    rows = {
        (r["plan_code"], r["term_months"]): r
        for r in (
            await session.execute(
                text(
                    "SELECT plan_code, term_months, amount_paise, active FROM mangaly_billing.plan_price"
                )
            )
        ).mappings()
    }
    out: list[PriceOut] = []
    for code in (*catalogue.PLAN_ORDER, *catalogue.ADD_ON_PLANS):
        plan = catalogue.PLANS[code]
        base = {t.months: t.amount_paise for t in plan.terms}
        for months in (3, 6, 12):
            override = rows.get((code, months))
            if override is None and months not in base:
                continue
            out.append(
                PriceOut(
                    plan_code=code,
                    term_months=months,
                    amount_paise=int(override["amount_paise"]) if override else base[months],
                    catalogue_paise=base.get(months),
                    active=bool(override["active"]) if override else True,
                )
            )
    return out


class PriceBody(BaseModel):
    plan_code: Literal["GOLD", "ASSISTED", "AGENT", "AGENT_CONNECT"]
    term_months: Literal[3, 6, 12]
    amount_paise: int = Field(gt=0, le=100_000_000)
    active: bool = True


@router.patch("/admin/prices", status_code=status.HTTP_204_NO_CONTENT)
async def admin_set_price(body: PriceBody, session: DbSession, operator: Moderator) -> None:
    """An administrator sets a plan term's price (the owner's rule for Agent
    Connect: "a premium tier which admin can decide")."""
    from sqlalchemy import text

    await session.execute(
        text("SELECT mangaly_billing.set_plan_price(:p, :m, :a, :act)"),
        {"p": body.plan_code, "m": body.term_months, "a": body.amount_paise, "act": body.active},
    )


# ---------------------------------------------------------------------------
# [DEC-V1-034] Unwanted calls: the family's report
# ---------------------------------------------------------------------------


class SuspectOut(BaseModel):
    agent_account_id: str
    display_name: str | None
    business_name: str | None
    city: str | None
    last_at: str


@router.get("/reports/suspects", response_model=list[SuspectOut])
async def report_suspects(
    session: DbSession,
    account_id: AuthenticatedAccount,
    day: date,
    for_candidate: UUID | None = None,
) -> list[SuspectOut]:
    """The agents who opened or exported the family's number in the 30 days
    up to `day`, shown on the report form so the family can name one."""
    member = await _family(session, account_id, for_candidate)
    return [
        SuspectOut(
            agent_account_id=str(s.agent_account_id),
            display_name=s.display_name,
            business_name=s.business_name,
            city=s.city,
            last_at=s.last_at.isoformat(),
        )
        for s in await agents.suspects(session, member_account_id=member, day=day)
    ]


class ReportBody(BaseModel):
    channel: Literal["call", "whatsapp", "sms", "email"]
    happened_on: date
    note: str | None = Field(default=None, max_length=2000)
    named_agent_id: UUID | None = None
    for_candidate: UUID | None = None


class ReportOut(BaseModel):
    id: str
    channel: str
    happened_on: str
    note: str | None
    named_agent_id: str | None
    status: str
    created_at: str


@router.post("/reports", status_code=status.HTTP_201_CREATED)
async def report(
    body: ReportBody, session: DbSession, account_id: AuthenticatedAccount, lang: Locale
) -> dict[str, str]:
    from sqlalchemy.exc import DBAPIError

    member = await _family(session, account_id, body.for_candidate)
    try:
        async with session.begin_nested():
            report_id = await agents.report_unwanted_contact(
                session,
                member_account_id=member,
                channel=body.channel,
                happened_on=body.happened_on,
                note=body.note,
                named_agent_id=body.named_agent_id,
            )
    except DBAPIError as exc:
        message = str(exc.orig)
        if "date out of range" in message or "not an agent" in message:
            raise _error(status.HTTP_422_UNPROCESSABLE_ENTITY, "reportDate", lang) from exc
        if "the family reports" in message:
            raise _error(status.HTTP_403_FORBIDDEN, "familyReports", lang) from exc
        raise
    return {"report_id": str(report_id)}


@router.get("/reports", response_model=list[ReportOut])
async def reports(
    session: DbSession, account_id: AuthenticatedAccount, for_candidate: UUID | None = None
) -> list[ReportOut]:
    member = await _family(session, account_id, for_candidate)
    return [
        ReportOut(
            id=str(r.id),
            channel=r.channel,
            happened_on=r.happened_on.isoformat(),
            note=r.note,
            named_agent_id=str(r.named_agent_id) if r.named_agent_id else None,
            status=r.status,
            created_at=r.created_at.isoformat(),
        )
        for r in await agents.reports_of(session, member_account_id=member)
    ]


class LimitBody(BaseModel):
    name: Literal[
        "contacts_per_day",
        "contacts_per_month",
        "export_others_per_day",
        "profiles_added_per_day",
        "reports_to_suspend",
    ]
    value: int = Field(ge=0, le=100_000)


@router.get("/admin/limits", response_model=dict[str, int])
async def admin_limits(session: DbSession, operator: Moderator) -> dict[str, int]:
    return await agents.limits(session)


@router.patch("/admin/limits", status_code=status.HTTP_204_NO_CONTENT)
async def admin_set_limit(body: LimitBody, session: DbSession, operator: Moderator) -> None:
    """Administrators tune the fair-use limits without a code change."""
    await agents.set_limit(session, name=body.name, value=body.value)
