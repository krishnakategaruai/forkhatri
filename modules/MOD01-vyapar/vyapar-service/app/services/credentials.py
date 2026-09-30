# [Trust pack, 2026-09-30 — VISION-2040 item 4] Council-verified badges.
#
# Why: a client cannot easily tell whether a CA, doctor, physiotherapist,
# advocate or architect is really registered, and fake profiles are common.
# The badge names the register and the date someone last really checked it
# ("Registered with Bar Council of Telangana · checked on 30 Sep 2026").
#
# How:
#   * The member claims a register entry on their one profile: type, council,
#     number (and a DigiLocker document URI for a DigiLocker document).
#     Formats are checked here; a claim is one row per profile and type.
#   * The claim goes to the configured CredentialRegistry adapter
#     (app/integrations/credentials/). The dev stub answers "not checked" —
#     never "verified" — so the row stays `claimed`, `check_source` is
#     `dev_stub`, and `last_checked_at` stays empty.
#   * A claim that the registry could not settle is also put in the EXISTING
#     operator verification queue (a `credential` verification record naming
#     the council and number). An operator checks the public register by hand
#     and approves or rejects it there; `on_verification_decided` then marks
#     the claim verified (source `operator`, checked now, valid 12 months) or
#     failed. The badge reads "Pending check" until then.
#   * The hourly trust pass expires verified claims whose year is up and puts
#     them back in the queue; the member is told.
# Public: claimed and verified entries show on a visible profile (the Bar
# Council's own website rule lists the enrolment number); failed and expired
# ones only to the owner.
# Traces to: FR06, FR09, FR10, FR47, VISION-2040 item 4, BACKLOG B6
from __future__ import annotations

import re
from datetime import date, datetime, timedelta, timezone
from typing import Literal

import asyncpg
from pydantic import BaseModel, Field

from app.audit import audit
from app.config import get_settings
from app.errors import ApiError
from app.i18n import translate
from app.identity import AuthzContext
from app.integrations.credentials import CredentialClaim, get_registry

CredentialType = Literal[
    "icai_membership", "medical_council_registration", "allied_health_registration",
    "bar_council_enrolment", "coa_registration", "digilocker_document",
]
CREDENTIAL_TYPES: tuple[str, ...] = (
    "icai_membership", "medical_council_registration", "allied_health_registration",
    "bar_council_enrolment", "coa_registration", "digilocker_document",
)

# The register each type is checked against. A fixed council is used as-is;
# otherwise the member names theirs and it must look like one of these.
FIXED_COUNCIL = {
    "icai_membership": "Institute of Chartered Accountants of India",
    "allied_health_registration": "National Commission for Allied and Healthcare Professions",
    "coa_registration": "Council of Architecture",
}
COUNCIL_SUGGESTIONS = {
    "bar_council_enrolment": ["Bar Council of Telangana", "Bar Council of Andhra Pradesh", "Bar Council of Delhi",
                              "Bar Council of Maharashtra and Goa", "Bar Council of Karnataka", "Bar Council of Tamil Nadu and Puducherry"],
    "medical_council_registration": ["National Medical Commission", "Telangana State Medical Council", "Andhra Pradesh Medical Council",
                                     "Delhi Medical Council", "Maharashtra Medical Council", "Karnataka Medical Council"],
    "digilocker_document": [],
}
_COUNCIL_RULE = {
    "bar_council_enrolment": re.compile(r"^Bar Council of [A-Za-z&,. ]{3,80}$"),
    "medical_council_registration": re.compile(r"^(?:National Medical Commission|[A-Za-z&. ]{3,60} Medical Council)$"),
    "digilocker_document": re.compile(r"^.{3,120}$"),  # the issuing body, e.g. "Osmania University"
}
# Number formats, as the registers print them.
#   ICAI membership: six digits (e.g. 212345).
#   State Bar Council enrolment: STATE/number/year (e.g. TS/1234/2015, MAH/5678/2010, D/123/2005).
#   Council of Architecture: CA/year/number (e.g. CA/2010/12345).
#   Medical council / NCAHP registration: letters, digits, / and - (formats differ by council).
#   DigiLocker: the document number; the URI is separate.
_NUMBER_RULE = {
    "icai_membership": re.compile(r"^\d{6}$"),
    "bar_council_enrolment": re.compile(r"^[A-Z]{1,5}\s?[/-]\s?\d{1,6}\s?[/-]\s?(?:19|20)\d{2}$"),
    "coa_registration": re.compile(r"^CA\s?/\s?(?:19|20)\d{2}\s?/\s?\d{3,6}$"),
    "medical_council_registration": re.compile(r"^[A-Z0-9][A-Z0-9/\- ]{2,24}$"),
    "allied_health_registration": re.compile(r"^[A-Z0-9][A-Z0-9/\- ]{2,29}$"),
    "digilocker_document": re.compile(r"^[A-Z0-9][A-Z0-9/\- ]{2,39}$"),
}
_DIGILOCKER_URI = re.compile(r"^in\.gov\.[a-z0-9.]+-[A-Za-z0-9]+-[A-Za-z0-9/\-]+$")
PUBLIC_STATUSES = ("claimed", "verified")


class CredentialIn(BaseModel):
    credential_type: CredentialType
    registration_number: str = Field(min_length=3, max_length=60)
    council: str | None = Field(default=None, max_length=120, description="Required for Bar Council, medical council and DigiLocker (the issuer); fixed for ICAI, NCAHP and CoA")
    registered_on: date | None = Field(default=None, description="Date of enrolment / registration, when known")
    document_uri: str | None = Field(default=None, max_length=200, description="DigiLocker document URI (digilocker_document only)")


class CouncilBadgeOut(BaseModel):
    """What a viewer sees on a profile. Only claimed and verified entries are public."""
    id: str
    credential_type: str
    type_label: str
    council: str
    registration_number: str
    registered_on: str | None
    status: Literal["claimed", "verified", "expired", "failed"]
    label: str = Field(description='"Registered with Bar Council of Telangana" or "Bar Council of Telangana: pending check"')
    checked_on: str | None = Field(description="ISO date of the last real check (operator or live registry); null when never checked")
    checked_on_label: str | None = Field(description='"Checked on 30 Sep 2026", or "Pending check"')
    check_source: str | None = Field(description="dev_stub | registry | operator")


class CredentialOut(CouncilBadgeOut):
    """The owner's view: the same plus what happened on the last attempt."""
    last_attempt_at: str | None
    expires_at: str | None
    verification_record_id: str | None
    check_note: str | None
    listing_id: str


class CredentialTypeOut(BaseModel):
    credential_type: str
    label: str
    fixed_council: str | None
    council_suggestions: list[str]
    number_hint: str
    needs_document_uri: bool


def _date_label(dt: datetime | date, lang: str) -> str:
    from app.services.contact import to_local

    d = to_local(dt).date() if isinstance(dt, datetime) else dt
    return f"{d.day} {translate(f'contact.date.month.m{d.month}', lang)} {d.year}"


def _badge_fields(r: asyncpg.Record, lang: str) -> dict:
    status = r["status"]
    council = r["council"]
    if status == "verified":
        label = translate("verification.council.badge.verified", lang, council=council)
    elif status == "claimed":
        label = translate("verification.council.badge.claimed", lang, council=council)
    else:
        label = translate(f"verification.council.badge.{status}", lang, council=council)
    checked = r["last_checked_at"]
    if status == "verified" and checked:
        checked_label = translate("verification.council.checkedOn", lang, date=_date_label(checked, lang))
    elif status == "claimed":
        checked_label = translate("verification.council.pendingCheck", lang)
    else:
        checked_label = translate("verification.council.checkedOn", lang, date=_date_label(checked, lang)) if checked else None
    return dict(
        id=str(r["id"]), credential_type=r["credential_type"],
        type_label=translate(f"verification.council.type.{r['credential_type']}", lang),
        council=council, registration_number=r["registration_number"],
        registered_on=r["registered_on"].isoformat() if r["registered_on"] else None,
        status=status, label=label, checked_on=checked.date().isoformat() if checked else None,
        checked_on_label=checked_label, check_source=r["check_source"],
    )


def _owner_out(r: asyncpg.Record, lang: str) -> CredentialOut:
    return CredentialOut(
        **_badge_fields(r, lang),
        last_attempt_at=r["last_attempt_at"].isoformat() if r["last_attempt_at"] else None,
        expires_at=r["expires_at"].isoformat() if r["expires_at"] else None,
        verification_record_id=str(r["verification_record_id"]) if r["verification_record_id"] else None,
        check_note=r["check_note"], listing_id=str(r["listing_id"]),
    )


async def badges_for_listings(conn: asyncpg.Connection, lang: str, listing_ids: list) -> dict[str, list[CouncilBadgeOut]]:
    ids = [i for i in listing_ids if i]
    if not ids:
        return {}
    rows = await conn.fetch(
        """SELECT * FROM vyapar_listings.council_credentials
            WHERE listing_id = ANY($1::uuid[]) AND status = ANY($2::text[]) ORDER BY status DESC, created_at""",
        [str(i) for i in ids], list(PUBLIC_STATUSES),
    )
    out: dict[str, list[CouncilBadgeOut]] = {}
    for r in rows:
        out.setdefault(str(r["listing_id"]), []).append(CouncilBadgeOut(**_badge_fields(r, lang)))
    return out


def list_credential_types(lang: str) -> list[CredentialTypeOut]:
    return [
        CredentialTypeOut(
            credential_type=t, label=translate(f"verification.council.type.{t}", lang),
            fixed_council=FIXED_COUNCIL.get(t), council_suggestions=COUNCIL_SUGGESTIONS.get(t, []),
            number_hint=translate(f"verification.council.numberHint.{t}", lang),
            needs_document_uri=t == "digilocker_document",
        )
        for t in CREDENTIAL_TYPES
    ]


async def _profile(conn: asyncpg.Connection, ctx: AuthzContext, lang: str) -> asyncpg.Record:
    from app.services.profile import profile_row

    row = await profile_row(conn, ctx.member_id)
    if row is None:
        raise ApiError(403, "listings.error.profileRequired", lang)
    return row


def _normalise_number(credential_type: str, value: str) -> str:
    v = re.sub(r"\s+", " ", value.strip().upper())
    if credential_type in ("bar_council_enrolment", "coa_registration"):
        v = re.sub(r"\s*([/-])\s*", r"\1", v)
    return v


def _validate(body: CredentialIn, lang: str) -> tuple[str, str]:
    number = _normalise_number(body.credential_type, body.registration_number)
    if not _NUMBER_RULE[body.credential_type].match(number):
        raise ApiError(422, f"verification.council.error.numberFormat.{body.credential_type}", lang,
                       error_code="credential_number_invalid", extra={"field": "registration_number"})
    council = FIXED_COUNCIL.get(body.credential_type) or re.sub(r"\s+", " ", (body.council or "").strip())
    rule = _COUNCIL_RULE.get(body.credential_type)
    if rule is not None and not rule.match(council):
        raise ApiError(422, f"verification.council.error.councilRequired.{body.credential_type}", lang,
                       error_code="credential_council_invalid", extra={"field": "council"})
    if body.credential_type == "digilocker_document" and not (body.document_uri and _DIGILOCKER_URI.match(body.document_uri.strip())):
        raise ApiError(422, "verification.council.error.documentUri", lang, error_code="credential_document_uri_invalid",
                       extra={"field": "document_uri"})
    return number, council


async def _run_registry(conn: asyncpg.Connection, row: asyncpg.Record, holder_name: str) -> asyncpg.Record:
    """Asks the configured registry and records exactly what it said. Only a
    real lookup ever sets last_checked_at or `verified`."""
    result = await get_registry().check(CredentialClaim(
        credential_type=row["credential_type"], council=row["council"], registration_number=row["registration_number"],
        holder_name=holder_name, registered_on=row["registered_on"], document_uri=row["document_uri"],
    ))
    now = datetime.now(timezone.utc)
    if result.source == "registry" and result.checked_at and result.outcome == "verified":
        return await conn.fetchrow(
            """UPDATE vyapar_listings.council_credentials SET status = 'verified', check_source = 'registry',
                 last_attempt_at = $2, last_checked_at = $3, verified_at = $3, expires_at = $3 + make_interval(days => $4),
                 check_note = NULL, updated_at = now() WHERE id = $1 RETURNING *""",
            row["id"], now, result.checked_at, get_settings().credential_recheck_days)
    if result.source == "registry" and result.checked_at and result.outcome in ("not_found", "lapsed"):
        return await conn.fetchrow(
            """UPDATE vyapar_listings.council_credentials SET status = 'failed', check_source = 'registry',
                 last_attempt_at = $2, last_checked_at = $3, check_note = $4, updated_at = now() WHERE id = $1 RETURNING *""",
            row["id"], now, result.checked_at, result.outcome)
    # Nothing was checked (the dev stub, or a registry error): record the
    # attempt only; the claim waits for an operator.
    return await conn.fetchrow(
        """UPDATE vyapar_listings.council_credentials SET check_source = $2, last_attempt_at = $3, updated_at = now()
            WHERE id = $1 RETURNING *""",
        row["id"], result.source, now)


async def _queue_for_operator(conn: asyncpg.Connection, ctx: AuthzContext, lang: str, row: asyncpg.Record) -> asyncpg.Record:
    """The existing verification queue is where a person checks it (FR09/FR47)."""
    from app.services import verification

    type_label = translate("verification.council.type." + row["credential_type"], "en")
    name = f"{type_label}: {row['registration_number']}"
    if row["document_uri"]:
        name += f" ({row['document_uri']})"
    record = await verification.submit_listing_verification(
        conn, ctx, lang, listing_id=str(row["listing_id"]),
        body=verification.VerificationCreate(document_type="credential", issuer=row["council"], credential_name=name[:200]),
    )
    return await conn.fetchrow(
        "UPDATE vyapar_listings.council_credentials SET verification_record_id = $2, updated_at = now() WHERE id = $1 RETURNING *",
        row["id"], record.id)


async def add_credential(conn: asyncpg.Connection, ctx: AuthzContext, lang: str, body: CredentialIn) -> CredentialOut:
    profile = await _profile(conn, ctx, lang)
    number, council = _validate(body, lang)
    exists = await conn.fetchval(
        "SELECT id FROM vyapar_listings.council_credentials WHERE listing_id = $1 AND credential_type = $2",
        profile["id"], body.credential_type)
    if exists:
        raise ApiError(409, "verification.council.error.exists", lang, error_code="credential_exists",
                       extra={"credential_id": str(exists)})
    row = await conn.fetchrow(
        """INSERT INTO vyapar_listings.council_credentials
             (listing_id, member_id, credential_type, council, registration_number, registered_on, document_uri)
           VALUES ($1, $2, $3, $4, $5, $6, $7) RETURNING *""",
        profile["id"], ctx.member_id, body.credential_type, council, number, body.registered_on,
        body.document_uri.strip() if body.document_uri else None)
    row = await _run_registry(conn, row, profile["name"])
    if row["status"] == "claimed":
        row = await _queue_for_operator(conn, ctx, lang, row)
    await audit(conn, actor_id=ctx.member_id, action="credential.claimed", object_kind="listing", object_id=str(profile["id"]),
                reason_code=body.credential_type, details={"credential_id": str(row["id"]), "status": row["status"],
                                                           "check_source": row["check_source"]})
    return _owner_out(row, lang)


async def list_my_credentials(conn: asyncpg.Connection, ctx: AuthzContext, lang: str) -> list[CredentialOut]:
    rows = await conn.fetch(
        "SELECT * FROM vyapar_listings.council_credentials WHERE member_id = $1 ORDER BY created_at", ctx.member_id)
    return [_owner_out(r, lang) for r in rows]


async def _own(conn: asyncpg.Connection, ctx: AuthzContext, lang: str, credential_id: str) -> asyncpg.Record:
    try:
        row = await conn.fetchrow(
            "SELECT * FROM vyapar_listings.council_credentials WHERE id = $1 AND member_id = $2", credential_id, ctx.member_id)
    except asyncpg.DataError:
        row = None
    if row is None:
        raise ApiError(404, "verification.council.error.notFound", lang, error_code="credential_not_found")
    return row


async def recheck_credential(conn: asyncpg.Connection, ctx: AuthzContext, lang: str, credential_id: str) -> CredentialOut:
    """Ask the registry again (and, when it cannot settle it, the operator
    queue again if the last request there was already decided)."""
    row = await _own(conn, ctx, lang, credential_id)
    profile = await _profile(conn, ctx, lang)
    if row["status"] in ("expired", "failed"):
        row = await conn.fetchrow(
            "UPDATE vyapar_listings.council_credentials SET status = 'claimed', updated_at = now() WHERE id = $1 RETURNING *", row["id"])
    row = await _run_registry(conn, row, profile["name"])
    if row["status"] == "claimed":
        pending = row["verification_record_id"] and await conn.fetchval(
            "SELECT state = 'pending' FROM vyapar_listings.verification_records WHERE id = $1", row["verification_record_id"])
        if not pending:
            row = await _queue_for_operator(conn, ctx, lang, row)
    return _owner_out(row, lang)


class DeletedOut(BaseModel):
    deleted: bool


async def delete_credential(conn: asyncpg.Connection, ctx: AuthzContext, lang: str, credential_id: str) -> DeletedOut:
    row = await _own(conn, ctx, lang, credential_id)
    await conn.execute("DELETE FROM vyapar_listings.council_credentials WHERE id = $1", row["id"])
    return DeletedOut(deleted=True)


async def on_verification_decided(conn: asyncpg.Connection, record_id, new_state: str, operator_id: str, note: str | None) -> None:
    """Called from verification._decide: an operator checked the register by hand."""
    if new_state == "verified":
        await conn.execute(
            """UPDATE vyapar_listings.council_credentials SET status = 'verified', check_source = 'operator',
                 last_checked_at = now(), last_attempt_at = now(), verified_at = now(),
                 expires_at = now() + make_interval(days => $3), checked_by = $2, check_note = $4, updated_at = now()
               WHERE verification_record_id = $1""",
            record_id, operator_id, get_settings().credential_recheck_days, note)
    elif new_state == "rejected":
        await conn.execute(
            """UPDATE vyapar_listings.council_credentials SET status = 'failed', check_source = 'operator',
                 last_checked_at = now(), last_attempt_at = now(), checked_by = $2, check_note = $3, updated_at = now()
               WHERE verification_record_id = $1""",
            record_id, operator_id, note)


async def run_credential_expiry(conn: asyncpg.Connection) -> int:
    """A verified register entry is good for a year; after that the badge
    stops saying "Registered" until it is checked again. Runs inside the
    hourly trust pass (dispatcher context); the member is told."""
    from app.notifications import notify_member

    rows = await conn.fetch(
        """UPDATE vyapar_listings.council_credentials SET status = 'expired', updated_at = now()
            WHERE status = 'verified' AND expires_at < now() RETURNING id, member_id, council, credential_type""")
    for r in rows:
        await notify_member(
            conn, member_id=r["member_id"], template="councilCredentialExpired", link="/profile/credentials",
            idempotency_key=f"council_credential_expired:{r['id']}:{datetime.now(timezone.utc).date().isoformat()}",
            params={"council": r["council"]},
        )
    return len(rows)
