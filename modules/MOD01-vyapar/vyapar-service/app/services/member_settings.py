# [Product-owner standing i18n rule, 2026-09-15] Persists the member's
# language choice server-side (`members.language`, already modeled and
# already read by `resolve_language`'s `X-Vyapar-Language` header override
# on every subsequent request) so the preference survives across devices —
# the frontend's localStorage copy (`vyapar-web/lib/i18n/provider.tsx`) is
# only the same-device fast path, not the source of truth. Its own small
# service rather than folded into first_run — a post-onboarding
# language change from a settings/language-switcher UI is a different
# concern from the first-run flow, even though both touch the same column.
# Traces to: product-owner i18n rule, 2026-09-15 (not a numbered FR)
from __future__ import annotations

from typing import Literal

import asyncpg
from pydantic import BaseModel

from app.taxonomy_cache import labels_for


class LanguagePatch(BaseModel):
    language: Literal["en", "hi", "te", "mr", "kn"]


class ProfileBrief(BaseModel):
    id: str
    kind: str  # business | professional
    name: str
    headline: str | None
    locality: str
    state: str
    verification_state: str
    capability_labels: list[str]


class MemberProfiles(BaseModel):
    """[Owner, 2026-09-22: "in my profile we can enhance profile information
    about business / or skill; keep both models, any one can be an option,
    without any nothing can move forward"] The member's own two profile
    kinds, each optional, and the one flag that gates the actions that
    need a profile behind them (posting, enquiring)."""
    business: ProfileBrief | None
    professional: ProfileBrief | None
    complete: bool  # at least one of the two exists (not archived)


class MemberMeOut(BaseModel):
    id: str
    display_name: str
    language: str
    is_operator: bool
    operator_permissions: list[str]
    profiles: MemberProfiles | None = None


class LanguageOut(BaseModel):
    language: str


async def member_profiles(conn: asyncpg.Connection, member_id: str, lang: str) -> MemberProfiles:
    """The caller's most recent non-archived listing of each kind. RLS
    already shows a member every one of their own rows, drafts included."""
    rows = await conn.fetch(
        """SELECT DISTINCT ON (kind) id, kind, name, headline, locality, state, verification_state, capabilities
             FROM vyapar_listings.listings
            WHERE owner_id = $1 AND state <> 'archived'
            ORDER BY kind, (state LIKE 'active%') DESC, updated_at DESC""",
        member_id,
    )
    by_kind = {
        r["kind"]: ProfileBrief(
            id=str(r["id"]), kind=r["kind"], name=r["name"], headline=r["headline"], locality=r["locality"],
            state=r["state"], verification_state=r["verification_state"],
            capability_labels=labels_for(list(r["capabilities"]), lang),
        )
        for r in rows
    }
    return MemberProfiles(business=by_kind.get("business"), professional=by_kind.get("professional"), complete=bool(by_kind))


async def get_me(conn: asyncpg.Connection, lang: str = "en") -> MemberMeOut:
    """The caller's own display name, language and operator permissions —
    lets Profile show operator tools (verification/moderation queues) only
    to operators, instead of links everyone would hit a 403 on."""
    row = await conn.fetchrow(
        """SELECT id, display_name, language, is_operator, operator_permissions
           FROM vyapar_identity.members WHERE id = current_setting('vyapar.authz_context', true)"""
    )
    return MemberMeOut(
        id=row["id"], display_name=row["display_name"], language=row["language"],
        is_operator=row["is_operator"], operator_permissions=list(row["operator_permissions"]),
        profiles=await member_profiles(conn, row["id"], lang),
    )


async def set_member_language(conn: asyncpg.Connection, language: str) -> LanguageOut:
    await conn.execute(
        "UPDATE vyapar_identity.members SET language = $1, updated_at = now() WHERE id = current_setting('vyapar.authz_context', true)",
        language,
    )
    return LanguageOut(language=language)
