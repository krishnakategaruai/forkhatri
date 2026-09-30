"""Marriage agents — public interface (DEC-V1-033, migration 059).

The product owner (2026-09-29): a marriage agent "exists without the app too,
so I don't want to kill his job, rather I want to enhance him giving the best
platform." An agent is a relationship manager of kind 'agent' (migration 052):
their clients are `rm_assignment` rows, so searching as the client, putting
profiles forward with a note, the call and meeting log and chat with the
family all come from `components/assisted_matching` unchanged. This module
adds what an independent agent needs on top:

  * applying, Mangalya's check, and the Agent membership (a plan like Gold);
  * adding clients — one at a time or many from an Excel/CSV sheet with their
    photos — as profiles "made for someone" (DEC-V1-019): the phone owner is
    told, and takes the profile over or removes it;
  * a stage per client (searching → proposal sent → meeting → engaged →
    married);
  * contact numbers: always for the agent's own clients, and for anyone in
    Discover whose family has not closed their number to agents — each look
    written down where that family reads it;
  * Excel and biodata exports, logged the same way.

The family's side: a directory of live agents to choose from, the agents
working for them, who opened their number, which exports included them, and
the switch that closes their number to agents.
"""

from __future__ import annotations

import csv
import io
import logging
import re
from dataclasses import dataclass, field
from datetime import UTC, date, datetime
from typing import Any
from uuid import UUID

from fastapi import UploadFile
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)

STAGES = ("searching", "proposal_sent", "meeting", "engaged", "married", "paused")
MAX_IMPORT_ROWS = 200
MAX_EXPORT_PEOPLE = 500

# Sheet columns an agent may fill, beyond the required ones. Each maps to the
# profile category and key it is written to (config/profile_schema.py).
OPTIONAL_COLUMNS: dict[str, tuple[str, str]] = {
    "mother_tongue": ("basics", "mother_tongue"),
    "height_cm": ("basics", "height_cm"),
    "marital_status": ("basics", "marital_status"),
    "about": ("basics", "about"),
    "religion": ("community", "religion"),
    "caste": ("community", "caste"),
    "sub_community": ("community", "sub_community"),
    "gotra": ("community", "gotra"),
    "native_place": ("community", "native_place"),
    "education": ("education_career", "highest_education_level"),
    "college": ("education_career", "college"),
    "occupation": ("education_career", "occupation"),
    "employer": ("education_career", "employer"),
    "income_band": ("education_career", "income_band"),
    "diet": ("lifestyle", "diet"),
    "family_type": ("family", "family_type"),
    "father_occupation": ("family", "father_occupation"),
    "mother_occupation": ("family", "mother_occupation"),
}
# Values stored as option keys (lower case, underscores), not free text.
_OPTION_KEYS = {
    "mother_tongue",
    "marital_status",
    "religion",
    "education",
    "income_band",
    "diet",
    "family_type",
}
REQUIRED_COLUMNS = ("name", "gender", "date_of_birth", "city", "mobile", "photo")
TEMPLATE_COLUMNS = (*REQUIRED_COLUMNS, "looking_for", "relation_of_maker", *OPTIONAL_COLUMNS)


class NotAnAgent(Exception):
    """The caller has no agent record."""


class AgentNotLive(Exception):
    """The agent is not verified yet, or their membership has lapsed."""


class ClientNotFound(Exception):
    """No such active client for this agent."""


class NotAllowed(Exception):
    """The caller may not do this for this family."""


class ImportFileUnreadable(Exception):
    """The uploaded sheet is neither a readable .xlsx nor a .csv."""


class LimitReached(Exception):
    """A fair-use limit (DEC-V1-034) stops this. `which` names it:
    contacts_per_day, contacts_per_month, contact_suspended,
    export_others_per_day or profiles_added_per_day."""

    def __init__(self, which: str, limit: int | None = None) -> None:
        super().__init__(which)
        self.which = which
        self.limit = limit


_LIMIT_SQLSTATES = {
    "MGL41": "contacts_per_day",
    "MGL42": "contacts_per_month",
    "MGL43": "contact_suspended",
}


def _limit_from(exc: Exception) -> str | None:
    orig = getattr(exc, "orig", None)
    state = getattr(orig, "sqlstate", None) or getattr(orig, "pgcode", None)
    if state in _LIMIT_SQLSTATES:
        return _LIMIT_SQLSTATES[str(state)]
    message = str(orig or exc)
    for code, which in _LIMIT_SQLSTATES.items():
        if code in message:
            return which
    return None


# ---------------------------------------------------------------------------
# Shapes
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class AgentRecord:
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
    applied_at: datetime | None
    verified_at: datetime | None
    membership_until: datetime | None

    @property
    def live(self) -> bool:
        return self.kind == "staff" or (
            self.verification_status == "verified" and self.membership_until is not None
        )


@dataclass(frozen=True, slots=True)
class DirectoryAgent:
    account_id: UUID
    display_name: str
    business_name: str | None
    business_phone: str | None
    city: str | None
    languages: list[str]
    communities: list[str]
    years_active: int | None
    about: str | None
    photo_url: str | None
    verified_at: datetime | None
    families: int
    marriages: int


@dataclass(frozen=True, slots=True)
class Client:
    assignment_id: UUID
    account_id: UUID
    name: str | None
    age: int | None
    gender: str | None
    city: str | None
    looking_for: str | None
    photo_url: str | None
    stage: str
    stage_changed_at: datetime
    origin: str
    assigned_at: datetime
    made_by_me: bool
    claimed: bool
    suggestions: int
    liked: int


@dataclass(frozen=True, slots=True)
class ContactPerson:
    account_id: UUID
    display_name: str | None
    relation: str
    phone: str | None
    email: str | None = None


@dataclass(slots=True)
class ImportRow:
    row: int
    name: str | None
    status: str  # created | failed
    account_id: UUID | None = None
    error: str | None = None
    warnings: list[str] = field(default_factory=list)


@dataclass(frozen=True, slots=True)
class FamilyAgent:
    assignment_id: UUID
    agent: DirectoryAgent | None
    stage: str
    origin: str
    assigned_at: datetime


@dataclass(frozen=True, slots=True)
class AgentActivity:
    agent_account_id: UUID
    display_name: str | None
    business_name: str | None
    kind: str  # contact | excel | biodata
    at: datetime


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _photo_url(ref: str | None) -> str | None:
    if not ref:
        return None
    from app.components.profile import interface as profile

    return profile.resolve_photo_url(ref)


def _age(dob: date | None) -> int | None:
    if dob is None:
        return None
    today = datetime.now(UTC).date()
    return today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))


def _record(row: Any) -> AgentRecord:
    return AgentRecord(
        kind=row["kind"],
        display_name=row["display_name"],
        business_name=row["business_name"],
        business_phone=row["business_phone"],
        city=row["city"],
        languages=list(row["languages"] or []),
        communities=list(row["communities"] or []),
        years_active=row["years_active"],
        about=row["about"],
        verification_status=row["verification_status"],
        applied_at=row["applied_at"],
        verified_at=row["verified_at"],
        membership_until=row["membership_until"],
    )


def _directory_agent(row: Any) -> DirectoryAgent:
    return DirectoryAgent(
        account_id=row["account_id"],
        display_name=row["display_name"],
        business_name=row["business_name"],
        business_phone=row["business_phone"],
        city=row["city"],
        languages=list(row["languages"] or []),
        communities=list(row["communities"] or []),
        years_active=row["years_active"],
        about=row["about"],
        photo_url=_photo_url(row["photo_ref"]),
        verified_at=row["verified_at"],
        families=int(row["families"] or 0),
        marriages=int(row["marriages"] or 0),
    )


async def _may_decide_for(session: AsyncSession, *, acting: UUID, member: UUID) -> bool:
    """The candidate, or a parent or guardian in their circle — the people
    who answer requests for the family (the owner's 2026-09-21 rule)."""
    if acting == member:
        return True
    return bool(
        (
            await session.execute(
                text(
                    "SELECT EXISTS (SELECT 1 FROM mangaly_home_circle.membership m "
                    "WHERE m.candidate_profile_id = :c AND m.member_account_id = :me "
                    "AND m.status = 'active' AND m.relationship_type::text IN ('parent', 'guardian'))"
                ),
                {"c": member, "me": acting},
            )
        ).scalar_one()
    )


# ---------------------------------------------------------------------------
# The agent's own record and membership
# ---------------------------------------------------------------------------


async def my_record(session: AsyncSession) -> AgentRecord | None:
    row = (
        (await session.execute(text("SELECT * FROM mangaly_operations.my_agent_record()")))
        .mappings()
        .first()
    )
    return _record(row) if row else None


async def apply(
    session: AsyncSession,
    *,
    display_name: str,
    business_name: str | None,
    business_phone: str | None,
    city: str,
    languages: list[str],
    communities: list[str],
    years_active: int | None,
    about: str | None,
) -> AgentRecord:
    """Apply to be an agent, or update the details. A new application waits
    for Mangalya's check; details change freely afterwards."""
    await session.execute(
        text(
            "SELECT mangaly_operations.apply_as_agent(:name, :biz, :phone, :city, "
            "CAST(:langs AS text[]), CAST(:comms AS text[]), :years, :about)"
        ),
        {
            "name": display_name,
            "biz": business_name,
            "phone": business_phone,
            "city": city,
            "langs": languages,
            "comms": communities,
            "years": years_active,
            "about": about,
        },
    )
    record = await my_record(session)
    assert record is not None
    return record


# ---------------------------------------------------------------------------
# Clients (the agent seat: bound as an RM by `api/rm_deps.RmAccount`)
# ---------------------------------------------------------------------------


async def list_clients(session: AsyncSession, *, agent_account_id: UUID) -> list[Client]:
    rows = (
        (
            await session.execute(
                text(
                    "SELECT a.id, a.member_account_id, a.stage, a.stage_changed_at, a.origin, a.assigned_at, "
                    "  (SELECT count(*) FROM mangaly_operations.rm_suggestion s WHERE s.assignment_id = a.id) AS suggestions, "
                    "  (SELECT count(*) FROM mangaly_operations.rm_suggestion s "
                    "    WHERE s.assignment_id = a.id AND s.member_decision = 'liked') AS liked "
                    "FROM mangaly_operations.rm_assignment a "
                    "WHERE a.rm_account_id = :me AND a.status = 'active' "
                    "ORDER BY a.stage_changed_at DESC"
                ),
                {"me": agent_account_id},
            )
        )
        .mappings()
        .all()
    )
    ids = [r["member_account_id"] for r in rows]
    cores = await _cores(session, ids)
    out: list[Client] = []
    for r in rows:
        c = cores.get(r["member_account_id"], {})
        out.append(
            Client(
                assignment_id=r["id"],
                account_id=r["member_account_id"],
                name=c.get("name"),
                age=_age(c.get("date_of_birth")),
                gender=c.get("gender"),
                city=c.get("city"),
                looking_for=c.get("looking_for"),
                photo_url=_photo_url(c.get("photo_ref")),
                stage=r["stage"],
                stage_changed_at=r["stage_changed_at"],
                origin=r["origin"],
                assigned_at=r["assigned_at"],
                made_by_me=bool(c.get("made_by_me")),
                claimed=bool(c.get("claimed")),
                suggestions=int(r["suggestions"]),
                liked=int(r["liked"]),
            )
        )
    return out


async def _cores(session: AsyncSession, ids: list[UUID]) -> dict[UUID, dict[str, Any]]:
    if not ids:
        return {}
    rows = await session.execute(
        text("SELECT * FROM mangaly_operations.agent_client_cores(CAST(:ids AS uuid[]))"),
        {"ids": [str(i) for i in ids]},
    )
    return {r["account_id"]: dict(r) for r in rows.mappings()}


async def set_stage(session: AsyncSession, *, assignment_id: UUID, stage: str) -> None:
    if stage not in STAGES:
        raise ValueError("unknown stage")
    ok = (
        await session.execute(
            text("SELECT mangaly_operations.set_client_stage(:a, :s)"),
            {"a": assignment_id, "s": stage},
        )
    ).scalar_one()
    if not ok:
        raise ClientNotFound


async def add_client(
    session: AsyncSession,
    *,
    agent_account_id: UUID,
    phone: str,
    name: str,
    date_of_birth: date,
    gender: str,
    looking_for: str,
    city: str,
    photo: UploadFile,
    lang: str,
    attributes: dict[str, dict[str, Any]] | None = None,
) -> tuple[UUID, list[str]]:
    """Make a client's profile (DEC-V1-019's "made for someone", the agent as
    maker) and the client row that joins it to the agent. Returns the new
    account and any optional field that could not be saved.

    Raises the same errors as the parent flow: `platform.MemberExists` (the
    number already has a ForKhatri account — that family chooses the agent
    instead), `platform.InvalidPhone`, `profile.TooYoung`, `UnsupportedMedia`."""
    from app.components.identity_bridge import platform
    from app.components.profile import interface as profile
    from app.db.session import set_account_context, set_authz_context

    child_id, digits = await platform.provision_member(
        phone=phone, display_name=name, preferred_language=lang
    )
    # The platform hands back a still-unclaimed member for a number it already
    # provisioned; if Mangalya already has that person, it is the same answer
    # as "this number has an account" — never a server error.
    from sqlalchemy.exc import DBAPIError

    try:
        async with session.begin_nested():
            await session.execute(
                text("SELECT mangaly_identity.create_account_for_child(:id, :phone, :name)"),
                {"id": child_id, "phone": digits, "name": name},
            )
    except DBAPIError as exc:
        if "already exists" in str(exc):
            raise platform.MemberExists from exc
        raise
    warnings: list[str] = []
    await set_account_context(session, child_id)
    await set_authz_context(session, child_id)
    try:
        await profile.create_profile(
            session,
            account_id=child_id,
            name=name,
            date_of_birth=date_of_birth,
            gender=gender,
            city_locality=city,
            photo=photo,
            looking_for=looking_for,
        )
        for category, values in (attributes or {}).items():
            from app.components.profile.models import FieldState

            try:
                async with session.begin_nested():
                    await profile.update_category(
                        session,
                        account_id=child_id,
                        category=category,
                        attributes={k: (FieldState.VALUE, v) for k, v in values.items()},
                    )
            except Exception:  # noqa: BLE001 — an optional field never sinks the row
                warnings.extend(values.keys())
        await session.execute(
            text(
                "UPDATE mangaly_profile.profile SET created_by_account_id = :maker, updated_at = now() "
                "WHERE account_id = :child"
            ),
            {"maker": agent_account_id, "child": child_id},
        )
    finally:
        await set_account_context(session, agent_account_id)
        await set_authz_context(session, agent_account_id)
    await session.execute(
        text(
            "INSERT INTO mangaly_operations.rm_assignment (rm_account_id, member_account_id, origin, rm_kind) "
            "VALUES (:agent, :child, 'added_by_agent', 'agent')"
        ),
        {"agent": agent_account_id, "child": child_id},
    )
    return child_id, warnings


# --- bulk add ---------------------------------------------------------------


def _header_key(value: object) -> str:
    return re.sub(r"[^a-z0-9]+", "_", str(value or "").strip().lower()).strip("_")


def read_sheet(filename: str, content: bytes) -> list[dict[str, Any]]:
    """Rows of an .xlsx or .csv sheet as dicts keyed by the normalised header
    ("Date of birth" → date_of_birth). Blank rows are skipped."""
    rows: list[list[Any]]
    if filename.lower().endswith(".xlsx"):
        try:
            from openpyxl import load_workbook

            book = load_workbook(io.BytesIO(content), read_only=True, data_only=True)
            sheet = book.worksheets[0]
            rows = [list(r) for r in sheet.iter_rows(values_only=True)]
        except Exception as exc:  # noqa: BLE001
            raise ImportFileUnreadable from exc
    elif filename.lower().endswith(".csv"):
        try:
            decoded = content.decode("utf-8-sig")
        except UnicodeDecodeError as exc:
            raise ImportFileUnreadable from exc
        rows = [list(r) for r in csv.reader(io.StringIO(decoded))]
    else:
        raise ImportFileUnreadable
    if not rows:
        return []
    headers = [_header_key(h) for h in rows[0]]
    out = []
    for r in rows[1:]:
        if not any(str(v).strip() for v in r if v is not None):
            continue
        out.append({h: v for h, v in zip(headers, r, strict=False) if h})
    return out


def _parse_date(value: Any) -> date | None:
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    raw = str(value or "").strip()
    for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y", "%d.%m.%Y"):
        try:
            return datetime.strptime(raw, fmt).date()
        except ValueError:
            continue
    return None


def _gender(value: Any) -> str | None:
    raw = str(value or "").strip().lower()
    if raw in ("m", "male", "man", "boy", "groom"):
        return "male"
    if raw in ("f", "female", "woman", "girl", "bride"):
        return "female"
    return None


def _option(value: Any) -> str:
    return re.sub(r"[^a-z0-9]+", "_", str(value).strip().lower()).strip("_")


def _cell(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, float) and value.is_integer():
        return str(int(value))
    return str(value).strip()


async def import_clients(
    session: AsyncSession,
    *,
    agent_account_id: UUID,
    rows: list[dict[str, Any]],
    photos: dict[str, UploadFile],
    lang: str,
) -> list[ImportRow]:
    """Add every row of the sheet as a client. Each row is its own savepoint:
    one bad row is reported and the rest are still added."""
    from app.components.identity_bridge import platform
    from app.components.profile import interface as profile
    from app.components.profile.storage import UnsupportedMedia

    results: list[ImportRow] = []
    q = await quota(session)
    room = (q.profiles_added_per_day - q.added_today) if q else MAX_IMPORT_ROWS
    for index, raw in enumerate(rows[:MAX_IMPORT_ROWS], start=2):
        name = _cell(raw.get("name"))
        result = ImportRow(row=index, name=name or None, status="failed")
        results.append(result)
        if room <= 0:
            result.error = "daily_limit"
            continue
        missing = [c for c in REQUIRED_COLUMNS if not _cell(raw.get(c))]
        if missing:
            result.error = "missing:" + ",".join(missing)
            continue
        gender = _gender(raw.get("gender"))
        dob = _parse_date(raw.get("date_of_birth"))
        if gender is None:
            result.error = "bad:gender"
            continue
        if dob is None:
            result.error = "bad:date_of_birth"
            continue
        looking_for = _cell(raw.get("looking_for")).lower() or (
            "bride" if gender == "male" else "groom"
        )
        if looking_for not in ("bride", "groom"):
            result.error = "bad:looking_for"
            continue
        photo = photos.get(_cell(raw.get("photo")).lower())
        if photo is None:
            result.error = "photo_not_uploaded"
            continue
        attributes: dict[str, dict[str, Any]] = {}
        for column, (category, key) in OPTIONAL_COLUMNS.items():
            value = _cell(raw.get(column))
            if not value:
                continue
            if column == "height_cm":
                try:
                    attributes.setdefault(category, {})[key] = int(float(value))
                except ValueError:
                    result.warnings.append(column)
                continue
            attributes.setdefault(category, {})[key] = (
                _option(value) if column in _OPTION_KEYS else value
            )
        await photo.seek(0)
        try:
            async with session.begin_nested():
                account, warnings = await add_client(
                    session,
                    agent_account_id=agent_account_id,
                    phone=_cell(raw.get("mobile")),
                    name=name,
                    date_of_birth=dob,
                    gender=gender,
                    looking_for=looking_for,
                    city=_cell(raw.get("city")),
                    photo=photo,
                    lang=lang,
                    attributes=attributes,
                )
            result.status = "created"
            result.account_id = account
            room -= 1
            result.warnings.extend(warnings)
        except platform.MemberExists:
            result.error = "number_has_account"
        except platform.InvalidPhone:
            result.error = "bad:mobile"
        except platform.PlatformIdentityUnavailable:
            result.error = "identity_unavailable"
        except profile.TooYoung:
            result.error = "too_young"
        except UnsupportedMedia:
            result.error = "bad:photo"
        except Exception:  # noqa: BLE001 — reported per row, never a 500 for the whole sheet
            logger.exception("agent import row %s failed", index)
            result.error = "unexpected"
    return results


def template_workbook() -> bytes:
    """The sheet an agent fills: one header row and one example row."""
    from openpyxl import Workbook

    book = Workbook()
    sheet = book.active
    sheet.title = "Clients"
    sheet.append(list(TEMPLATE_COLUMNS))
    example = {
        "name": "Sravani Reddy",
        "gender": "female",
        "date_of_birth": "1998-03-14",
        "city": "Hyderabad",
        "mobile": "9876543210",
        "photo": "sravani.jpg",
        "looking_for": "groom",
        "mother_tongue": "telugu",
        "height_cm": 162,
        "religion": "hindu",
        "education": "masters",
        "occupation": "Software engineer",
    }
    sheet.append([example.get(c, "") for c in TEMPLATE_COLUMNS])
    for i, column in enumerate(TEMPLATE_COLUMNS, start=1):
        sheet.column_dimensions[sheet.cell(row=1, column=i).column_letter].width = max(
            14, len(column) + 4
        )
    buffer = io.BytesIO()
    book.save(buffer)
    return buffer.getvalue()


# ---------------------------------------------------------------------------
# Contact numbers
# ---------------------------------------------------------------------------


async def contact(
    session: AsyncSession, *, member_account_id: UUID, via: str = "eye"
) -> list[ContactPerson]:
    """The number and email this agent may open for one person — written down
    for that family as opened. Empty when the family closed their details.

    Behind the eye button (DEC-V1-034): a family who is not the agent's client
    uses one of the day's and the month's opens, unless the agent opened them
    in the last 30 days. `via="export"` never opens a new family. Raises
    `LimitReached` when a limit or a suspension stops it."""
    from sqlalchemy.exc import DBAPIError

    try:
        async with session.begin_nested():
            rows = (
                (
                    await session.execute(
                        text("SELECT * FROM mangaly_operations.agent_contact(:m, :via)"),
                        {"m": member_account_id, "via": via},
                    )
                )
                .mappings()
                .all()
            )
    except DBAPIError as exc:
        which = _limit_from(exc)
        if which is None:
            raise
        raise LimitReached(which) from exc
    return [
        ContactPerson(
            account_id=r["account_id"],
            display_name=r["display_name"],
            relation=r["relation"],
            phone=r["phone"],
            email=r["email"],
        )
        for r in rows
    ]


@dataclass(frozen=True, slots=True)
class Quota:
    contacts_today: int
    contacts_per_day: int
    contacts_month: int
    contacts_per_month: int
    exported_others_today: int
    export_others_per_day: int
    added_today: int
    profiles_added_per_day: int
    contact_suspended: bool


async def quota(session: AsyncSession) -> Quota | None:
    row = (
        (await session.execute(text("SELECT * FROM mangaly_operations.agent_quota()")))
        .mappings()
        .first()
    )
    return Quota(**{k: row[k] for k in Quota.__slots__}) if row else None


async def opened_recently(session: AsyncSession, *, member_ids: list[UUID]) -> set[UUID]:
    """People this agent opened in the last 30 days (opening again is free)."""
    if not member_ids:
        return set()
    rows = await session.execute(
        text(
            "SELECT account_id FROM mangaly_operations.agent_opened_recently(CAST(:ids AS uuid[]))"
        ),
        {"ids": [str(i) for i in member_ids]},
    )
    return {r[0] for r in rows}


async def require_room_to_add(session: AsyncSession, count: int = 1) -> int:
    """How many more profiles the agent may add today; raises when none."""
    q = await quota(session)
    if q is None:
        return count
    room = max(q.profiles_added_per_day - q.added_today, 0)
    if room <= 0:
        raise LimitReached("profiles_added_per_day", q.profiles_added_per_day)
    return room


async def contact_open(session: AsyncSession, *, member_ids: list[UUID]) -> set[UUID]:
    if not member_ids:
        return set()
    rows = await session.execute(
        text("SELECT account_id FROM mangaly_operations.agent_contact_open(CAST(:ids AS uuid[]))"),
        {"ids": [str(i) for i in member_ids]},
    )
    return {r[0] for r in rows}


# ---------------------------------------------------------------------------
# Exports
# ---------------------------------------------------------------------------


@dataclass(slots=True)
class BiodataEntry:
    account_id: UUID
    is_client: bool
    name: str | None
    age: int | None
    gender: str | None
    city: str | None
    photo_url: str | None
    biodata: dict[str, dict[str, Any]]
    contacts: list[ContactPerson]


async def biodata_entries(
    session: AsyncSession, *, agent_account_id: UUID, member_ids: list[UUID], with_contacts: bool
) -> list[BiodataEntry]:
    """What an export holds for each person: a client's whole biodata, or the
    public biodata anyone signed in sees for everyone else (never a name the
    person has not opened). Numbers only where `contact` would give them."""
    from app.components.discovery import interface as discovery
    from app.components.profile import interface as profile

    ids = list(dict.fromkeys(member_ids))[:MAX_EXPORT_PEOPLE]
    cores = await _cores(session, ids)
    others = [i for i in ids if i not in cores]
    cards = await discovery.cards_for(session, account_ids=others)
    opened = await discovery.open_cards_for(session, account_ids=others)
    index_rows = (
        (
            await session.execute(
                text(
                    "SELECT profile_id, gender, locality FROM mangaly_discovery.discovery_profile_index "
                    "WHERE profile_id = ANY(CAST(:ids AS uuid[])) AND searchable"
                ),
                {"ids": [str(i) for i in others]},
            )
        )
        .mappings()
        .all()
    )
    index = {r["profile_id"]: r for r in index_rows}
    may_open = await contact_open(session, member_ids=ids) if with_contacts else set()

    entries: list[BiodataEntry] = []
    for account in ids:
        if account in cores:
            core = cores[account]
            rows = await session.execute(
                text("SELECT * FROM mangaly_operations.agent_client_biodata(:m)"), {"m": account}
            )
            bio: dict[str, dict[str, Any]] = {}
            for r in rows.mappings():
                bio.setdefault(r["category"], {})[r["attribute_key"]] = r["value"]
            entry = BiodataEntry(
                account_id=account,
                is_client=True,
                name=core["name"],
                age=_age(core["date_of_birth"]),
                gender=core["gender"],
                city=core["city"],
                photo_url=_photo_url(core["photo_ref"]),
                biodata=bio,
                contacts=[],
            )
        elif account in index:
            card = cards.get(account)
            open_card = opened.get(account)
            entry = BiodataEntry(
                account_id=account,
                is_client=False,
                name=open_card.first_name if open_card else None,
                age=card.age if card else None,
                gender=index[account]["gender"],
                city=index[account]["locality"],
                photo_url=card.photo_url if card else None,
                biodata=await profile.public_biodata(session, account_id=account),
                contacts=[],
            )
        else:
            continue  # not a client and not in Discover: nothing to export
        if account in may_open:
            # A client's numbers always; anyone else's only if the agent opened
            # them with the eye in the last 30 days — an export never opens a
            # new family (DEC-V1-034).
            entry.contacts = await contact(
                session, member_account_id=account, via="eye" if entry.is_client else "export"
            )
        entries.append(entry)
    return entries


async def require_room_to_export(session: AsyncSession, *, others: int) -> None:
    """Profiles that are not the agent's clients count against a daily
    export limit (DEC-V1-034); clients never do."""
    if others <= 0:
        return
    q = await quota(session)
    if q is not None and q.exported_others_today + others > q.export_others_per_day:
        raise LimitReached(
            "export_others_per_day", max(q.export_others_per_day - q.exported_others_today, 0)
        )


async def record_export(
    session: AsyncSession,
    *,
    agent_account_id: UUID,
    kind: str,
    member_ids: list[UUID],
    others_count: int = 0,
) -> None:
    if not member_ids:
        return
    # Reopening the same print page (or downloading the same sheet again)
    # within ten minutes is one export, not a new line in the family's list.
    await session.execute(
        text(
            "INSERT INTO mangaly_operations.agent_export (agent_account_id, kind, member_ids, others_count) "
            "SELECT :a, :k, CAST(:ids AS uuid[]), :o "
            "WHERE NOT EXISTS (SELECT 1 FROM mangaly_operations.agent_export e "
            "  WHERE e.agent_account_id = :a AND e.kind = :k AND e.member_ids = CAST(:ids AS uuid[]) "
            "    AND e.created_at > now() - interval '10 minutes')"
        ),
        {"a": agent_account_id, "k": kind, "ids": [str(i) for i in member_ids], "o": others_count},
    )


def _flat(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, list):
        return ", ".join(_flat(v) for v in value)
    if isinstance(value, dict):
        return ", ".join(
            f"{k}: {_flat(v)}" for k, v in value.items() if k not in ("lat", "lon", "id")
        )
    return (
        str(value).replace("_", " ")
        if isinstance(value, str) and re.fullmatch(r"[a-z0-9_]+", value)
        else str(value)
    )


def excel_workbook(
    entries: list[BiodataEntry], *, agent_name: str, labels: dict[str, str]
) -> bytes:
    """One row per person: the core facts, the biodata sections as columns,
    and the numbers the agent may see. Stamped with the agent and the date,
    so a forwarded sheet says whose it is."""
    from openpyxl import Workbook
    from openpyxl.styles import Font

    keys: list[tuple[str, str]] = []
    for e in entries:
        for category, values in e.biodata.items():
            if category in (
                "partner_preference",
                "self_scales",
                "outlook",
                "openly",
                "in_my_words",
            ):
                continue
            for key in values:
                if key in ("birth_place_geo",):
                    continue
                # One column per fact, even when the profile keeps it in two categories.
                if all(k != key for _, k in keys):
                    keys.append((category, key))
    book = Workbook()
    sheet = book.active
    sheet.title = "Biodata"
    sheet.append(
        [labels["stamp"].format(agent=agent_name, date=datetime.now(UTC).strftime("%d/%m/%Y"))]
    )
    sheet["A1"].font = Font(italic=True)
    header = [
        labels["name"],
        labels["age"],
        labels["gender"],
        labels["city"],
        labels["client"],
        labels["phones"],
    ]
    header += [labels.get(f"{c}.{k}", k.replace("_", " ").capitalize()) for c, k in keys]
    sheet.append(header)
    for cell in sheet[2]:
        cell.font = Font(bold=True)
    for e in entries:
        phones = "; ".join(
            f"{p.display_name or ''} ({labels.get('relation.' + p.relation, p.relation)}): {p.phone}"
            for p in e.contacts
        )
        row = [
            e.name or "",
            e.age or "",
            e.gender or "",
            e.city or "",
            labels["yes"] if e.is_client else "",
            phones,
        ]
        row += [
            _flat(
                next(
                    (
                        vals[k]
                        for vals in e.biodata.values()
                        if isinstance(vals, dict) and k in vals
                    ),
                    None,
                )
            )
            for _, k in keys
        ]
        sheet.append(row)
    for column in sheet.columns:
        letter = column[0].column_letter
        sheet.column_dimensions[letter].width = min(
            40, max(12, *(len(str(c.value or "")) for c in column[1:6]))
        )
    buffer = io.BytesIO()
    book.save(buffer)
    return buffer.getvalue()


# ---------------------------------------------------------------------------
# The family's side
# ---------------------------------------------------------------------------


async def directory(session: AsyncSession, *, city: str | None = None) -> list[DirectoryAgent]:
    rows = (
        (await session.execute(text("SELECT * FROM mangaly_operations.agent_directory()")))
        .mappings()
        .all()
    )
    agents = [_directory_agent(r) for r in rows]
    if city:
        wanted = city.strip().lower()
        agents.sort(key=lambda a: 0 if (a.city or "").strip().lower() == wanted else 1)
    return agents


async def choose(session: AsyncSession, *, member_account_id: UUID, agent_account_id: UUID) -> UUID:
    try:
        async with session.begin_nested():
            assignment = (
                await session.execute(
                    text("SELECT mangaly_operations.choose_agent(:m, :a)"),
                    {"m": member_account_id, "a": agent_account_id},
                )
            ).scalar_one()
    except Exception as exc:
        if "insufficient_privilege" in repr(exc) or "the candidate or a parent" in str(exc):
            raise NotAllowed from exc
        raise ClientNotFound from exc
    from app.components.notification_bridge import interface as notifications

    await notifications.notify(
        session,
        recipients=[agent_account_id],
        subject_account_id=agent_account_id,
        kind="agent_chosen",
        payload={"assignment_id": assignment},
        link=f"/rm/console/{assignment}",
    )
    return assignment


async def release(
    session: AsyncSession, *, member_account_id: UUID, agent_account_id: UUID
) -> bool:
    try:
        async with session.begin_nested():
            return bool(
                (
                    await session.execute(
                        text("SELECT mangaly_operations.release_agent(:m, :a)"),
                        {"m": member_account_id, "a": agent_account_id},
                    )
                ).scalar_one()
            )
    except Exception as exc:
        raise NotAllowed from exc


async def family_agents(session: AsyncSession, *, member_account_id: UUID) -> list[FamilyAgent]:
    rows = (
        (
            await session.execute(
                text("SELECT * FROM mangaly_operations.agents_of(:m)"), {"m": member_account_id}
            )
        )
        .mappings()
        .all()
    )
    live = {a.account_id: a for a in await directory(session)}
    return [
        FamilyAgent(
            assignment_id=r["assignment_id"],
            agent=live.get(r["agent_account_id"]),
            stage=r["stage"],
            origin=r["origin"],
            assigned_at=r["assigned_at"],
        )
        for r in rows
    ]


async def activity_for_family(
    session: AsyncSession, *, member_account_id: UUID
) -> list[AgentActivity]:
    """Who opened the family's number, and which exports included them —
    newest first."""
    views = (
        (
            await session.execute(
                text("SELECT * FROM mangaly_operations.contact_views_of(:m)"),
                {"m": member_account_id},
            )
        )
        .mappings()
        .all()
    )
    exports = (
        (
            await session.execute(
                text("SELECT * FROM mangaly_operations.exports_of(:m)"), {"m": member_account_id}
            )
        )
        .mappings()
        .all()
    )
    items = [
        AgentActivity(
            v["agent_account_id"], v["display_name"], v["business_name"], "contact", v["viewed_at"]
        )
        for v in views
    ] + [
        AgentActivity(
            e["agent_account_id"], e["display_name"], e["business_name"], e["kind"], e["created_at"]
        )
        for e in exports
    ]
    return sorted(items, key=lambda a: a.at, reverse=True)


async def agents_may_see_contact(session: AsyncSession, *, member_account_id: UUID) -> bool | None:
    return (
        await session.execute(
            text("SELECT mangaly_profile.agents_may_see_contact(:m)"), {"m": member_account_id}
        )
    ).scalar_one_or_none()


async def set_agents_may_see_contact(
    session: AsyncSession, *, acting: UUID, member_account_id: UUID, open_: bool
) -> None:
    if not await _may_decide_for(session, acting=acting, member=member_account_id):
        raise NotAllowed
    await session.execute(
        text("SELECT mangaly_profile.set_agents_may_see_contact(:m, :o)"),
        {"m": member_account_id, "o": open_},
    )


# ---------------------------------------------------------------------------
# Mangalya's check (moderators, 'operations' operator role)
# ---------------------------------------------------------------------------


async def applications(session: AsyncSession) -> list[tuple[UUID, AgentRecord]]:
    rows = (
        (await session.execute(text("SELECT * FROM mangaly_operations.agent_applications()")))
        .mappings()
        .all()
    )
    return [(r["account_id"], _record({**r, "kind": "agent"})) for r in rows]


async def review(session: AsyncSession, *, account_id: UUID, status: str) -> bool:
    ok = bool(
        (
            await session.execute(
                text("SELECT mangaly_operations.review_agent(:a, :s)"),
                {"a": account_id, "s": status},
            )
        ).scalar_one()
    )
    if ok:
        from app.components.notification_bridge import interface as notifications

        await notifications.notify(
            session,
            recipients=[account_id],
            subject_account_id=account_id,
            kind=f"agent_{status}",
            payload={},
            link="/agent",
        )
    return ok


async def may_decide_for(session: AsyncSession, *, acting: UUID, member: UUID) -> bool:
    return await _may_decide_for(session, acting=acting, member=member)


# ---------------------------------------------------------------------------
# Part 2 (owner, 2026-09-29): families connect to agents; agents share
# profiles on Mangalya and beyond into the family's agent dashboard.
# ---------------------------------------------------------------------------

OFFLINE_DETAIL_KEYS = (
    "height_cm",
    "mother_tongue",
    "religion",
    "caste",
    "sub_community",
    "gotra",
    "education",
    "occupation",
    "employer",
    "income",
    "native_place",
    "family",
    "rashi",
    "nakshatra",
    "about",
)
_IMAGE_TYPES = {"image/jpeg": "jpg", "image/png": "png", "image/webp": "webp"}
_BIODATA_TYPES = {**_IMAGE_TYPES, "application/pdf": "pdf"}
_MAX_BIODATA_BYTES = 10 * 1024 * 1024


class NeedsAgentConnect(Exception):
    """The family does not hold Agent Connect."""


@dataclass(frozen=True, slots=True)
class OfflineProfile:
    id: UUID
    name: str
    gender: str
    age: int | None
    date_of_birth: date | None
    city: str | None
    details: dict[str, Any]
    photo_urls: list[str]
    biodata_url: str | None
    biodata_kind: str | None  # pdf | image
    contact_note: str | None
    created_at: datetime


@dataclass(frozen=True, slots=True)
class SharedProfile:
    """One profile an agent shared with the family: a Mangalya member (the
    Discover card) or an offline biodata."""

    suggestion_id: UUID
    assignment_id: UUID
    agent_account_id: UUID
    note: str | None
    shared_at: datetime
    decision: str | None
    decided_at: datetime | None
    question: str | None
    member_account_id: UUID | None
    offline: OfflineProfile | None


def _offline_url(offline_id: UUID, ref: str) -> str:
    return f"/agents/offline-media/{offline_id}/{ref.rsplit('/', 1)[-1]}"


def _offline(row: Any) -> OfflineProfile:
    biodata_ref = row["biodata_ref"]
    return OfflineProfile(
        id=row["id"],
        name=row["name"],
        gender=row["gender"],
        age=_age(row["date_of_birth"]),
        date_of_birth=row["date_of_birth"],
        city=row["city"],
        details=dict(row["details"] or {}),
        photo_urls=[_offline_url(row["id"], r) for r in (row["photo_refs"] or [])],
        biodata_url=_offline_url(row["id"], biodata_ref) if biodata_ref else None,
        biodata_kind=("pdf" if biodata_ref.endswith(".pdf") else "image") if biodata_ref else None,
        contact_note=row["contact_note"],
        created_at=row["created_at"],
    )


_OFFLINE_COLUMNS = "id, name, gender, date_of_birth, city, details, photo_refs, biodata_ref, contact_note, created_at"


async def _save_offline_file(
    offline_id: UUID, upload: UploadFile, *, allowed: dict[str, str]
) -> str:
    """Local-disk stand-in with profile/storage.py's contract: a checked type
    and size, a random name, a local:// reference under the media root."""
    import uuid as uuid_module

    from app.components.profile import storage
    from app.components.profile.storage import UnsupportedMedia

    content_type = (upload.content_type or "").split(";")[0].strip()
    ext = allowed.get(content_type)
    if ext is None:
        raise UnsupportedMedia(f"unsupported content type: {content_type!r}")
    data = await upload.read()
    if not data or len(data) > _MAX_BIODATA_BYTES:
        raise UnsupportedMedia("empty or too large")
    ref = f"local://offline-{offline_id}/{uuid_module.uuid4()}.{ext}"
    path = storage.local_path(ref)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)
    return ref


async def create_offline_profile(
    session: AsyncSession,
    *,
    agent_account_id: UUID,
    name: str,
    gender: str,
    date_of_birth: date | None,
    city: str | None,
    details: dict[str, Any],
    contact_note: str | None,
    photos: list[UploadFile],
    biodata: UploadFile | None,
) -> OfflineProfile:
    """A biodata the agent holds for someone who is not on Mangalya. The agent
    confirms the family's permission (the route checks the box); the record is
    the agent's own and reaches only the families the agent shares it with."""
    import json
    import uuid as uuid_module

    offline_id = uuid_module.uuid4()
    photo_refs = [await _save_offline_file(offline_id, p, allowed=_IMAGE_TYPES) for p in photos[:6]]
    biodata_ref = (
        await _save_offline_file(offline_id, biodata, allowed=_BIODATA_TYPES)
        if biodata is not None
        else None
    )
    clean = {k: v for k, v in details.items() if k in OFFLINE_DETAIL_KEYS and v not in (None, "")}
    row = (
        (
            await session.execute(
                text(
                    "INSERT INTO mangaly_operations.offline_profile "
                    "(id, agent_account_id, name, gender, date_of_birth, city, details, photo_refs, biodata_ref, "
                    " contact_note, consent_confirmed_at) "
                    "VALUES (:id, :agent, :name, :gender, :dob, :city, CAST(:details AS jsonb), "
                    " CAST(:photos AS text[]), :biodata, :contact, now()) "
                    f"RETURNING {_OFFLINE_COLUMNS}"
                ),
                {
                    "id": offline_id,
                    "agent": agent_account_id,
                    "name": name,
                    "gender": gender,
                    "dob": date_of_birth,
                    "city": city,
                    "details": json.dumps(clean, ensure_ascii=False),
                    "photos": photo_refs,
                    "biodata": biodata_ref,
                    "contact": contact_note,
                },
            )
        )
        .mappings()
        .one()
    )
    return _offline(row)


async def list_offline_profiles(
    session: AsyncSession, *, agent_account_id: UUID
) -> list[OfflineProfile]:
    rows = (
        (
            await session.execute(
                text(
                    f"SELECT {_OFFLINE_COLUMNS} FROM mangaly_operations.offline_profile "
                    "WHERE agent_account_id = :me AND archived_at IS NULL ORDER BY created_at DESC"
                ),
                {"me": agent_account_id},
            )
        )
        .mappings()
        .all()
    )
    return [_offline(r) for r in rows]


async def archive_offline_profile(session: AsyncSession, *, offline_id: UUID) -> bool:
    result = await session.execute(
        text(
            "UPDATE mangaly_operations.offline_profile SET archived_at = now(), updated_at = now() "
            "WHERE id = :id AND archived_at IS NULL"
        ),
        {"id": offline_id},
    )
    return bool(result.rowcount)


async def share(
    session: AsyncSession,
    *,
    agent_account_id: UUID,
    assignment_ids: list[UUID],
    member_ids: list[UUID],
    offline_ids: list[UUID],
    note: str | None,
) -> int:
    """Share profiles with clients: every chosen profile to every chosen
    client (a day's batch to one family, or one profile to several). A share
    is never a request (the RM suggestion rule). Each family is told once.
    Returns how many new shares were made."""
    from app.components.assisted_matching import interface as assisted
    from app.components.notification_bridge import interface as notifications

    note = (note or "").strip()[: assisted.NOTE_MAX_LENGTH] or None
    made = 0
    rm = await assisted.rm_summary(session, rm_account_id=agent_account_id)
    for assignment_id in dict.fromkeys(assignment_ids):
        assignment = await assisted.get_assignment(
            session, rm_account_id=agent_account_id, assignment_id=assignment_id
        )
        if assignment is None or assignment.status != "active":
            raise ClientNotFound
        before = made
        for member in dict.fromkeys(member_ids):
            if member == assignment.member_account_id:
                continue
            result = await session.execute(
                text(
                    "INSERT INTO mangaly_operations.rm_suggestion (assignment_id, suggested_account_id, note) "
                    "VALUES (:a, :s, :note) ON CONFLICT (assignment_id, suggested_account_id) DO NOTHING"
                ),
                {"a": assignment.id, "s": member, "note": note},
            )
            made += result.rowcount or 0
        for offline in dict.fromkeys(offline_ids):
            result = await session.execute(
                text(
                    "INSERT INTO mangaly_operations.rm_suggestion (assignment_id, offline_profile_id, note) "
                    "SELECT :a, o.id, :note FROM mangaly_operations.offline_profile o "
                    "WHERE o.id = :o AND o.archived_at IS NULL "
                    "ON CONFLICT (assignment_id, offline_profile_id) WHERE offline_profile_id IS NOT NULL "
                    "DO NOTHING"
                ),
                {"a": assignment.id, "o": offline, "note": note},
            )
            made += result.rowcount or 0
        if made > before:
            await notifications.notify_circle(
                session,
                candidate_account_id=assignment.member_account_id,
                kind="rm_suggested",
                payload={
                    "rm_name": rm.display_name if rm else None,
                    "member_name": assignment.member_name,
                },
                link="/agents",
            )
    return made


async def agent_connect_until(session: AsyncSession, *, member_account_id: UUID) -> datetime | None:
    return (
        await session.execute(
            text("SELECT mangaly_operations.agent_connect_until(:m)"), {"m": member_account_id}
        )
    ).scalar_one_or_none()


async def shared_with_family(
    session: AsyncSession, *, member_account_id: UUID
) -> list[SharedProfile]:
    """Everything the family's agents shared, newest first (RLS: the family
    reads its own assignments' suggestions and the offline profiles in them)."""
    rows = (
        (
            await session.execute(
                text(
                    "SELECT s.id, s.assignment_id, a.rm_account_id, s.note, s.created_at, s.member_decision, "
                    "       s.decided_at, s.question, s.suggested_account_id, s.offline_profile_id "
                    "FROM mangaly_operations.rm_suggestion s "
                    "JOIN mangaly_operations.rm_assignment a ON a.id = s.assignment_id "
                    "WHERE a.member_account_id = :m AND a.rm_kind = 'agent' AND a.status = 'active' "
                    "ORDER BY s.created_at DESC"
                ),
                {"m": member_account_id},
            )
        )
        .mappings()
        .all()
    )
    offline_ids = [r["offline_profile_id"] for r in rows if r["offline_profile_id"]]
    offline: dict[UUID, OfflineProfile] = {}
    if offline_ids:
        found = await session.execute(
            text(
                f"SELECT {_OFFLINE_COLUMNS} FROM mangaly_operations.offline_profile "
                "WHERE id = ANY(CAST(:ids AS uuid[]))"
            ),
            {"ids": [str(i) for i in offline_ids]},
        )
        offline = {r["id"]: _offline(r) for r in found.mappings()}
    return [
        SharedProfile(
            suggestion_id=r["id"],
            assignment_id=r["assignment_id"],
            agent_account_id=r["rm_account_id"],
            note=r["note"],
            shared_at=r["created_at"],
            decision=r["member_decision"],
            decided_at=r["decided_at"],
            question=r["question"],
            member_account_id=r["suggested_account_id"],
            offline=offline.get(r["offline_profile_id"]) if r["offline_profile_id"] else None,
        )
        for r in rows
        if r["suggested_account_id"] or r["offline_profile_id"] in offline
    ]


async def shared_by_agent(session: AsyncSession, *, assignment_id: UUID) -> list[SharedProfile]:
    """The agent's copy of what they shared with one client, and how the
    family answered (agent seat; RLS through the assignment)."""
    rows = (
        (
            await session.execute(
                text(
                    "SELECT s.id, s.assignment_id, a.rm_account_id, s.note, s.created_at, s.member_decision, "
                    "       s.decided_at, s.question, s.suggested_account_id, s.offline_profile_id "
                    "FROM mangaly_operations.rm_suggestion s "
                    "JOIN mangaly_operations.rm_assignment a ON a.id = s.assignment_id "
                    "WHERE s.assignment_id = :a ORDER BY s.created_at DESC"
                ),
                {"a": assignment_id},
            )
        )
        .mappings()
        .all()
    )
    offline_ids = [r["offline_profile_id"] for r in rows if r["offline_profile_id"]]
    offline: dict[UUID, OfflineProfile] = {}
    if offline_ids:
        found = await session.execute(
            text(
                f"SELECT {_OFFLINE_COLUMNS} FROM mangaly_operations.offline_profile "
                "WHERE id = ANY(CAST(:ids AS uuid[]))"
            ),
            {"ids": [str(i) for i in offline_ids]},
        )
        offline = {r["id"]: _offline(r) for r in found.mappings()}
    return [
        SharedProfile(
            suggestion_id=r["id"],
            assignment_id=r["assignment_id"],
            agent_account_id=r["rm_account_id"],
            note=r["note"],
            shared_at=r["created_at"],
            decision=r["member_decision"],
            decided_at=r["decided_at"],
            question=r["question"],
            member_account_id=r["suggested_account_id"],
            offline=offline.get(r["offline_profile_id"]) if r["offline_profile_id"] else None,
        )
        for r in rows
    ]


async def offline_media_path(session: AsyncSession, *, offline_id: UUID, filename: str):
    """The file behind an offline profile's photo or biodata, if the caller may
    see it; else None."""
    from app.components.profile import storage

    if not re.fullmatch(r"[0-9a-f-]{36}\.(jpg|png|webp|pdf)", filename):
        return None
    ref = f"local://offline-{offline_id}/{filename}"
    visible = (
        await session.execute(
            text("SELECT mangaly_operations.offline_media_visible(:r)"), {"r": ref}
        )
    ).scalar_one()
    if not visible:
        return None
    path = storage.local_path(ref)
    return path if path.exists() else None


# ---------------------------------------------------------------------------
# Unwanted calls (DEC-V1-034). The owner (2026-09-29): a family that gets spam
# calls reports it, and "we can find out who took" their number — every look
# behind the eye is written down, so the report names the agents who opened
# or exported that family's number in the 30 days before.
# ---------------------------------------------------------------------------

REPORT_CHANNELS = ("call", "whatsapp", "sms", "email")
LIMIT_NAMES = (
    "contacts_per_day",
    "contacts_per_month",
    "export_others_per_day",
    "profiles_added_per_day",
    "reports_to_suspend",
)


@dataclass(frozen=True, slots=True)
class Suspect:
    agent_account_id: UUID
    display_name: str | None
    business_name: str | None
    city: str | None
    last_at: datetime


@dataclass(frozen=True, slots=True)
class ContactReport:
    id: UUID
    channel: str
    happened_on: date
    note: str | None
    named_agent_id: UUID | None
    status: str
    created_at: datetime


async def suspects(session: AsyncSession, *, member_account_id: UUID, day: date) -> list[Suspect]:
    rows = await session.execute(
        text("SELECT * FROM mangaly_operations.contact_suspects(:m, :d)"),
        {"m": member_account_id, "d": day},
    )
    return [
        Suspect(
            r["agent_account_id"], r["display_name"], r["business_name"], r["city"], r["last_at"]
        )
        for r in rows.mappings()
    ]


async def report_unwanted_contact(
    session: AsyncSession,
    *,
    member_account_id: UUID,
    channel: str,
    happened_on: date,
    note: str | None,
    named_agent_id: UUID | None,
) -> UUID:
    """Write the report; the database attaches the suspects and shuts the eye
    of an agent enough different families have pointed at. That agent is told."""
    if channel not in REPORT_CHANNELS:
        raise ValueError("unknown channel")
    row = (
        (
            await session.execute(
                text("SELECT * FROM mangaly_operations.report_contact_misuse(:m, :c, :d, :n, :a)"),
                {
                    "m": member_account_id,
                    "c": channel,
                    "d": happened_on,
                    "n": note,
                    "a": named_agent_id,
                },
            )
        )
        .mappings()
        .one()
    )
    if row["suspended_agent"] is not None:
        from app.components.notification_bridge import interface as notifications

        await notifications.notify(
            session,
            recipients=[row["suspended_agent"]],
            subject_account_id=row["suspended_agent"],
            kind="agent_contact_suspended",
            payload={},
            link="/agent",
        )
    return row["report_id"]


async def reports_of(session: AsyncSession, *, member_account_id: UUID) -> list[ContactReport]:
    rows = await session.execute(
        text(
            "SELECT id, channel, happened_on, note, named_agent_id, status, created_at "
            "FROM mangaly_operations.contact_report WHERE member_account_id = :m "
            "ORDER BY created_at DESC LIMIT 50"
        ),
        {"m": member_account_id},
    )
    return [ContactReport(**dict(r)) for r in rows.mappings()]


async def admin_reports(session: AsyncSession) -> list[dict[str, Any]]:
    rows = await session.execute(text("SELECT * FROM mangaly_operations.contact_reports_admin()"))
    return [dict(r) for r in rows.mappings()]


async def review_report(
    session: AsyncSession,
    *,
    report_id: UUID,
    status: str,
    agent_account_id: UUID | None,
    note: str | None,
) -> bool:
    ok = bool(
        (
            await session.execute(
                text("SELECT mangaly_operations.review_contact_report(:r, :s, :a, :n)"),
                {"r": report_id, "s": status, "a": agent_account_id, "n": note},
            )
        ).scalar_one()
    )
    if ok:
        from app.components.notification_bridge import interface as notifications

        reporter = (
            await session.execute(
                text(
                    "SELECT reported_by, member_account_id FROM mangaly_operations.contact_report WHERE id = :r"
                ),
                {"r": report_id},
            )
        ).first()
        if reporter is not None:
            await notifications.notify(
                session,
                recipients=[reporter[0]],
                subject_account_id=reporter[1],
                kind=f"contact_report_{status}",
                payload={},
                link="/me/contact-safety",
            )
        if status == "suspended" and agent_account_id is not None:
            await notifications.notify(
                session,
                recipients=[agent_account_id],
                subject_account_id=agent_account_id,
                kind="agent_suspended",
                payload={},
                link="/agent",
            )
    return ok


async def lift_contact_suspension(session: AsyncSession, *, agent_account_id: UUID) -> bool:
    return bool(
        (
            await session.execute(
                text("SELECT mangaly_operations.lift_contact_suspension(:a)"),
                {"a": agent_account_id},
            )
        ).scalar_one()
    )


async def limits(session: AsyncSession) -> dict[str, int]:
    rows = await session.execute(text("SELECT name, value FROM mangaly_operations.agent_limit"))
    return {r[0]: int(r[1]) for r in rows}


async def set_limit(session: AsyncSession, *, name: str, value: int) -> None:
    if name not in LIMIT_NAMES:
        raise ValueError("unknown limit")
    await session.execute(
        text("SELECT mangaly_operations.set_agent_limit(:n, :v)"), {"n": name, "v": value}
    )
