# [IMP37 — Refactor B] Integration management API: personal access tokens
# and outbound webhook subscriptions, plus `GET /v1/integrations/me` so an
# agent can check who it is acting for and with which scopes.
#
# Everything except /me requires the member's own session: an access token
# can never list, mint or revoke credentials or change where events go
# (enforced centrally by the token scope policy AND explicitly here).
# All queries run on get_conn's connection, so RLS (migrations 015/016)
# limits every read and write to the caller's own rows.
# Traces to: REFACTOR-PLAN.md §B
from __future__ import annotations

from typing import Annotated

import asyncpg
from fastapi import APIRouter, Depends, Query, Request
from pydantic import BaseModel, Field

from app.config import get_settings
from app.db import get_conn
from app.deps import Locale
from app.i18n import translate
from app.identity import AuthzContext, require_member_session, resolve_authz_context
from app.integrations import tokens
from app.integrations.errors import fail
from app.integrations.identity.scopes import ALL_SCOPES
from app.integrations.webhooks import subscriptions
from app.integrations.webhooks.dispatcher import target_problem
from app.integrations.webhooks.events import EVENT_TYPES, WILDCARD, catalogue

router = APIRouter(prefix="/v1/integrations", tags=["integrations"])

Ctx = Annotated[AuthzContext, Depends(resolve_authz_context)]
Conn = Annotated[asyncpg.Connection, Depends(get_conn)]


# ---------------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------------
class WhoAmI(BaseModel):
    member_id: str
    auth_method: str
    scopes: list[str]
    access_token_id: str | None = None


class ScopeInfo(BaseModel):
    scope: str
    description: str


class AccessTokenCreate(BaseModel):
    name: str = Field(min_length=1, max_length=80, description="A label so you can recognise the token later, e.g. 'Claude Desktop'.")
    scopes: list[str] = Field(min_length=1, description="Subset of GET /v1/integrations/scopes.")
    expires_in_days: int | None = Field(default=None, ge=1, description="Defaults to 90; at most 365.")


class AccessTokenOut(BaseModel):
    id: str
    name: str
    prefix: str
    scopes: list[str]
    status: str
    created_at: str
    expires_at: str
    last_used_at: str | None = None
    revoked_at: str | None = None


class AccessTokenCreated(AccessTokenOut):
    token: str = Field(description="The token itself. Shown exactly once; store it now.")


class WebhookCreate(BaseModel):
    url: str = Field(max_length=2000)
    event_types: list[str] = Field(min_length=1, description="Event types from GET /v1/integrations/webhooks/events, or ['*'].")
    description: str | None = Field(default=None, max_length=200)
    all_events: bool = Field(default=False, description="Operators only: receive every event, not only events about you.")


class WebhookOut(BaseModel):
    id: str
    url: str
    description: str | None = None
    event_types: list[str]
    all_events: bool
    secret_prefix: str
    active: bool
    failure_streak: int
    created_at: str


class WebhookCreated(WebhookOut):
    secret: str = Field(description="Signing secret for X-Vyapar-Signature. Shown exactly once.")


class WebhookEventType(BaseModel):
    type: str
    operator_only: bool
    description: str


class WebhookDelivery(BaseModel):
    id: int
    event_id: str
    event_type: str
    status: str
    attempts: int
    last_status_code: int | None = None
    last_error: str | None = None
    created_at: str
    delivered_at: str | None = None
    next_attempt_at: str | None = None


class Ack(BaseModel):
    ok: bool = True


# ---------------------------------------------------------------------------
# Who am I
# ---------------------------------------------------------------------------
@router.get("/me", response_model=WhoAmI, operation_id="getIntegrationIdentity",
            summary="Who the caller is acting as, how it authenticated, and its scopes")
async def who_am_i(ctx: Ctx) -> WhoAmI:
    return WhoAmI(
        member_id=ctx.member_id,
        auth_method=ctx.auth_method,
        scopes=sorted(ctx.scopes) if ctx.scopes is not None else list(ALL_SCOPES),
        access_token_id=ctx.credential_id,
    )


@router.get("/scopes", response_model=list[ScopeInfo], operation_id="listAccessTokenScopes",
            summary="Scopes an access token can be granted")
async def list_scopes(request: Request, ctx: Ctx, lang: Locale) -> list[ScopeInfo]:
    require_member_session(request, ctx)
    return [ScopeInfo(scope=s, description=translate(f"integrations.scope.{s}", lang)) for s in ALL_SCOPES]


# ---------------------------------------------------------------------------
# Personal access tokens
# ---------------------------------------------------------------------------
@router.get("/tokens", response_model=list[AccessTokenOut], operation_id="listAccessTokens",
            summary="Your personal access tokens (never the token values)")
async def list_access_tokens(request: Request, ctx: Ctx, conn: Conn) -> list[dict]:
    require_member_session(request, ctx)
    return await tokens.list_tokens(conn, ctx.member_id)


@router.post("/tokens", status_code=201, response_model=AccessTokenCreated, operation_id="createAccessToken",
             summary="Create a personal access token; the value is returned only in this response")
async def create_access_token(body: AccessTokenCreate, request: Request, ctx: Ctx, conn: Conn, lang: Locale) -> dict:
    require_member_session(request, ctx)
    settings = get_settings()
    unknown = sorted(set(body.scopes) - set(ALL_SCOPES))
    if unknown:
        raise fail(422, "invalid_scopes", lang, scopes=", ".join(unknown))
    days = body.expires_in_days or settings.access_token_default_days
    if days > settings.access_token_max_days:
        raise fail(422, "invalid_expiry", lang, days=settings.access_token_max_days)
    if await tokens.count_active(conn, ctx.member_id) >= settings.access_token_max_active_per_member:
        raise fail(409, "too_many_tokens", lang, limit=settings.access_token_max_active_per_member)
    created = await tokens.create_token(conn, member_id=ctx.member_id, name=body.name.strip(), scopes=body.scopes, days=days)
    from app.audit import audit

    await audit(conn, actor_id=ctx.member_id, action="access_token.create", object_kind="access_token",
                object_id=created["id"], details={"scopes": created["scopes"], "expires_at": created["expires_at"]})
    return created


@router.delete("/tokens/{token_id}", response_model=AccessTokenOut, operation_id="revokeAccessToken",
               summary="Revoke a personal access token immediately")
async def revoke_access_token(token_id: str, request: Request, ctx: Ctx, conn: Conn, lang: Locale) -> dict:
    require_member_session(request, ctx)
    try:
        revoked = await tokens.revoke_token(conn, ctx.member_id, token_id)
    except asyncpg.DataError:
        revoked = None
    if revoked is None:
        raise fail(404, "token_not_found", lang)
    from app.audit import audit

    await audit(conn, actor_id=ctx.member_id, action="access_token.revoke", object_kind="access_token", object_id=token_id)
    return revoked


# ---------------------------------------------------------------------------
# Webhooks
# ---------------------------------------------------------------------------
@router.get("/webhooks/events", response_model=list[WebhookEventType], operation_id="listWebhookEventTypes",
            summary="Event types a webhook can subscribe to")
async def list_event_types(request: Request, ctx: Ctx, lang: Locale) -> list[dict]:
    require_member_session(request, ctx)
    return catalogue(lang)


@router.get("/webhooks", response_model=list[WebhookOut], operation_id="listWebhookSubscriptions",
            summary="Your webhook subscriptions")
async def list_webhooks(request: Request, ctx: Ctx, conn: Conn) -> list[dict]:
    require_member_session(request, ctx)
    return await subscriptions.list_for(conn, ctx.member_id)


@router.post("/webhooks", status_code=201, response_model=WebhookCreated, operation_id="createWebhookSubscription",
             summary="Subscribe a URL to events; the signing secret is returned only in this response")
async def create_webhook(body: WebhookCreate, request: Request, ctx: Ctx, conn: Conn, lang: Locale) -> dict:
    require_member_session(request, ctx)
    settings = get_settings()
    problem = target_problem(body.url.strip())
    if problem:
        raise fail(422, problem, lang)
    types = sorted(set(body.event_types))
    unknown = [t for t in types if t != WILDCARD and t not in EVENT_TYPES]
    if unknown:
        raise fail(422, "invalid_event_types", lang, types=", ".join(unknown))
    if body.all_events and not ctx.is_operator:
        raise fail(403, "all_events_operator_only", lang)
    if await subscriptions.count_live(conn, ctx.member_id) >= settings.webhook_max_per_member:
        raise fail(409, "too_many_webhooks", lang, limit=settings.webhook_max_per_member)
    created = await subscriptions.create(conn, member_id=ctx.member_id, url=body.url.strip(), event_types=types,
                                         description=body.description, all_events=body.all_events)
    from app.audit import audit

    await audit(conn, actor_id=ctx.member_id, action="webhook.create", object_kind="webhook_subscription",
                object_id=created["id"], details={"event_types": types, "all_events": body.all_events})
    return created


@router.delete("/webhooks/{subscription_id}", response_model=Ack, operation_id="deleteWebhookSubscription",
               summary="Delete a webhook subscription (its delivery log is kept)")
async def delete_webhook(subscription_id: str, request: Request, ctx: Ctx, conn: Conn, lang: Locale) -> Ack:
    require_member_session(request, ctx)
    if not await subscriptions.delete(conn, ctx.member_id, subscription_id):
        raise fail(404, "webhook_not_found", lang)
    from app.audit import audit

    await audit(conn, actor_id=ctx.member_id, action="webhook.delete", object_kind="webhook_subscription", object_id=subscription_id)
    return Ack()


@router.post("/webhooks/{subscription_id}/test", response_model=WebhookDelivery, operation_id="testWebhookSubscription",
             summary="Send a signed `ping` event now and return the delivery outcome")
async def test_webhook(subscription_id: str, request: Request, ctx: Ctx, conn: Conn, lang: Locale) -> dict:
    require_member_session(request, ctx)
    sub = await subscriptions.get(conn, ctx.member_id, subscription_id)
    if sub is None:
        raise fail(404, "webhook_not_found", lang)
    return await subscriptions.send_test_ping(conn, ctx.member_id, sub)


@router.get("/webhooks/{subscription_id}/deliveries", response_model=list[WebhookDelivery],
            operation_id="listWebhookDeliveries", summary="Recent delivery attempts for a subscription")
async def list_deliveries(subscription_id: str, request: Request, ctx: Ctx, conn: Conn, lang: Locale,
                          limit: int = Query(default=50, ge=1, le=200)) -> list[dict]:
    require_member_session(request, ctx)
    if await subscriptions.get(conn, ctx.member_id, subscription_id) is None:
        raise fail(404, "webhook_not_found", lang)
    return await subscriptions.deliveries(conn, ctx.member_id, subscription_id, limit)
