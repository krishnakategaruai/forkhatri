"""Shared response models — the card contract every discovery surface returns (FR006)."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel

from app.components.discovery.interface import Card


class CardOut(BaseModel):
    id: str
    slug: str
    title: str
    intent_category: str
    category_label: str
    time_start: datetime
    time_end: datetime | None
    location_label: str
    distance_label: str | None
    host_member_id: str
    host_name: str
    host_avatar: str | None
    going_count: int
    interested_count: int
    capacity: int | None
    spots_left: int | None
    trust_level: str
    trust_label: str
    trust_positive: bool
    why_reason: str
    why_factor: str
    viewer_status: str | None
    cover_image_url: str | None
    visibility_scope: str
    circle_id: str | None
    high_risk: bool
    status: str
    is_recurring: bool
    lat: float | None
    lng: float | None

    @classmethod
    def from_card(cls, c: Card) -> CardOut:
        return cls(
            id=str(c.id),
            slug=c.slug,
            title=c.title,
            intent_category=c.intent_category,
            category_label=c.category_label,
            time_start=c.time_start,
            time_end=c.time_end,
            location_label=c.location_label,
            distance_label=c.distance_label,
            host_member_id=str(c.host_member_id),
            host_name=c.host_name,
            host_avatar=c.host_avatar,
            going_count=c.going_count,
            interested_count=c.interested_count,
            capacity=c.capacity,
            spots_left=c.spots_left,
            trust_level=c.trust_level,
            trust_label=c.trust_label,
            trust_positive=c.trust_positive,
            why_reason=c.why_reason,
            why_factor=c.why_factor,
            viewer_status=c.viewer_status,
            cover_image_url=c.cover_image_url,
            visibility_scope=c.visibility_scope,
            circle_id=str(c.circle_id) if c.circle_id else None,
            high_risk=c.high_risk,
            status=c.status,
            is_recurring=c.is_recurring,
            lat=c.lat,
            lng=c.lng,
        )
