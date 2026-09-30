# [TR021] In-app notification inbox — HTTP front door only. The inbox reads,
# the strong-match matcher, the digest and the scheduled loop live in
# app/services/notifications.py.
# Traces to: FR21, TR021, SP021
from __future__ import annotations

import asyncpg
from fastapi import APIRouter, Depends, Query

from app.db import get_conn
from app.deps import Locale
from app.errors import ERROR_RESPONSES
from app.identity import AuthzContext, resolve_authz_context
from app.services import notifications as svc
from app.services.notifications import (  # noqa: F401  schemas used below; background passes re-exported for main.py
    NotificationOut,
    ReadOut,
    UnreadCountOut,
    notification_loop,
)
from app.services.pagination import DEFAULT_LIMIT, MAX_LIMIT, Page

router = APIRouter(prefix="/v1/notifications", tags=["notifications"], responses=ERROR_RESPONSES)


@router.get("", response_model=list[NotificationOut], operation_id="listNotifications", summary="List the member's notifications")
async def list_notifications(
    lang: Locale,
    ctx: AuthzContext = Depends(resolve_authz_context),
    conn: asyncpg.Connection = Depends(get_conn, scope="function"),
) -> list[NotificationOut]:
    return await svc.list_notifications(conn, ctx, lang)


@router.get("/page", response_model=Page[NotificationOut], operation_id="listNotificationsPage", summary="List all of the member's notifications, one page at a time")
async def list_notifications_page(
    lang: Locale,
    limit: int = Query(default=DEFAULT_LIMIT, ge=1, le=MAX_LIMIT),
    cursor: str | None = None,
    ctx: AuthzContext = Depends(resolve_authz_context),
    conn: asyncpg.Connection = Depends(get_conn, scope="function"),
) -> Page[NotificationOut]:
    return await svc.list_notifications_page(conn, ctx, lang, limit=limit, cursor=cursor)


@router.get("/unread-count", response_model=UnreadCountOut, operation_id="getUnreadNotificationCount", summary="Get the number of unread notifications")
async def unread_count(
    ctx: AuthzContext = Depends(resolve_authz_context),
    conn: asyncpg.Connection = Depends(get_conn, scope="function"),
) -> UnreadCountOut:
    return await svc.get_unread_notification_count(conn, ctx)


@router.post("/{notification_id}/read", response_model=ReadOut, operation_id="markNotificationRead", summary="Mark one notification as read")
async def mark_read(
    notification_id: str,
    ctx: AuthzContext = Depends(resolve_authz_context),
    conn: asyncpg.Connection = Depends(get_conn, scope="function"),
) -> ReadOut:
    return await svc.mark_notification_read(conn, ctx, notification_id=notification_id)


@router.post("/read-all", response_model=ReadOut, operation_id="markAllNotificationsRead", summary="Mark all notifications as read")
async def mark_all_read(
    ctx: AuthzContext = Depends(resolve_authz_context),
    conn: asyncpg.Connection = Depends(get_conn, scope="function"),
) -> ReadOut:
    return await svc.mark_all_notifications_read(conn, ctx)
