"""Start a profile from a family's biodata (D13, Q3 — owner, 2026-10-06).

A biodata is the family's own format: a PDF or a photo on WhatsApp with the
name, birth details, studies, work, family and horoscope. Mangalya reads it
into the profile's closed field list and the family checks every line before
anything is used. Nothing is guessed into storage.

Privacy (Q3, decided 2026-10-06):
  * Reading happens only after the family ticks one clear consent line.
  * The file is read from memory and never written to disk by the reader; it
    is gone when the request ends. It is kept only if the family chooses
    "attach" — and then only after the profile is published, through
    `save_document()` below (a child's data is never stored before publish).
  * Without an AI key (or when the call fails) the reader answers "not
    available" and the family attaches the file and types, which always works.

The AI answer is validated field by field against fixed vocabularies, exactly
like the matchmaker's reader (`compatibility/understand.py`): an unknown
field or value is dropped, never stored.
"""

from __future__ import annotations

import base64
import json
import logging
import re
import uuid
from datetime import date
from pathlib import Path
from typing import Any, Final

from app.components.profile import storage
from app.components.profile.horoscope_fields import NAKSHATRAS, RASHIS, TIME_RE
from app.config.settings import get_settings

logger = logging.getLogger(__name__)

MAX_BYTES: Final = 10 * 1024 * 1024
EDUCATION: Final = ("high_school", "diploma", "bachelors", "professional", "masters", "doctorate", "other")
MARITAL: Final = ("never_married", "divorced", "widowed", "awaiting_divorce")
_KINDS: Final = {"application/pdf": "pdf", "image/jpeg": "jpg", "image/png": "png", "image/webp": "webp"}


class UnsupportedDocument(ValueError):
    """Not a PDF, JPEG, PNG or WebP, empty, or too large."""


def sniff(data: bytes) -> str:
    """The file's real type from its first bytes (labels from phones lie)."""
    if data[:5] == b"%PDF-":
        return "application/pdf"
    if data[:3] == bytes([0xFF, 0xD8, 0xFF]):
        return "image/jpeg"
    if data[:8] == bytes([0x89, 0x50, 0x4E, 0x47, 0x0D, 0x0A, 0x1A, 0x0A]):
        return "image/png"
    if data[:4] == b"RIFF" and data[8:12] == b"WEBP":
        return "image/webp"
    return ""


def check(data: bytes) -> str:
    if not data:
        raise UnsupportedDocument("empty file")
    if len(data) > MAX_BYTES:
        raise UnsupportedDocument("too large")
    kind = sniff(data)
    if kind not in _KINDS:
        raise UnsupportedDocument("unsupported type")
    return kind


def reader_available() -> bool:
    key = get_settings().anthropic_api_key
    return bool(key) and not key.startswith("CHANGE_ME")


# --- Validation: the only way a read value reaches the family's form ---------

def _text(value: Any, limit: int = 120) -> str | None:
    if not isinstance(value, str):
        return None
    cleaned = re.sub(r"\s+", " ", value).strip()
    return cleaned[:limit] or None


def _enum(value: Any, allowed: tuple[str, ...]) -> str | None:
    v = str(value or "").strip().lower()
    return v if v in allowed else None


def clean_fields(raw: Any) -> dict[str, Any]:
    if not isinstance(raw, dict):
        return {}
    out: dict[str, Any] = {}
    for key in ("name", "city", "native_place", "occupation", "gotra", "education_other"):
        if (v := _text(raw.get(key))) is not None:
            out[key] = v
    dob = _text(raw.get("date_of_birth"), 10)
    if dob:
        try:
            parsed = date.fromisoformat(dob)
            if 1940 <= parsed.year <= date.today().year:
                out["date_of_birth"] = parsed.isoformat()
        except ValueError:
            pass
    if (g := _enum(raw.get("gender"), ("female", "male"))) is not None:
        out["gender"] = g
    if (e := _enum(raw.get("education_level"), EDUCATION)) is not None:
        out["education_level"] = e
    if (m := _enum(raw.get("marital_status"), MARITAL)) is not None:
        out["marital_status"] = m
    if (r := _enum(raw.get("rashi"), RASHIS)) is not None:
        out["rashi"] = r
    if (n := _enum(raw.get("nakshatra"), NAKSHATRAS)) is not None:
        out["nakshatra"] = n
    bt = _text(raw.get("birth_time"), 5)
    if bt and TIME_RE.match(bt):
        out["birth_time"] = bt
    try:
        h = int(raw.get("height_cm") or 0)
        if 120 <= h <= 220:
            out["height_cm"] = h
    except (TypeError, ValueError):
        pass
    if out.get("education_level") != "other":
        out.pop("education_other", None)
    return out


_SYSTEM = (
    "You read an Indian marriage biodata (a PDF or a photo) for a matrimony app. "
    "Copy only what the document actually states about the candidate; leave a field "
    "out when it is not there. Never guess. Dates as YYYY-MM-DD, time of birth as "
    "24-hour HH:MM. Height in centimetres. Map the studies to one level: "
    "high_school, diploma, bachelors, professional (CA, MBBS, LLB and similar), "
    "masters, doctorate, or other (then put the words in education_other). "
    "Rashi and nakshatra use these exact keys: rashi " + ", ".join(RASHIS) + "; nakshatra "
    + ", ".join(NAKSHATRAS) + ". Do not copy phone numbers, addresses or parents' names."
)

_STR = {"type": "string"}
_SCHEMA: Final[dict[str, Any]] = {
    "type": "object",
    "properties": {
        "name": _STR,
        "date_of_birth": _STR,
        "gender": {"type": "string", "enum": ["female", "male"]},
        "city": _STR,
        "native_place": _STR,
        "education_level": {"type": "string", "enum": list(EDUCATION)},
        "education_other": _STR,
        "occupation": _STR,
        "marital_status": {"type": "string", "enum": list(MARITAL)},
        "height_cm": {"type": "integer"},
        "birth_time": _STR,
        "rashi": {"type": "string", "enum": list(RASHIS)},
        "nakshatra": {"type": "string", "enum": list(NAKSHATRAS)},
        "gotra": _STR,
    },
    "required": [],
    "additionalProperties": False,
}


async def read(data: bytes, content_type: str) -> dict[str, Any] | None:
    """Read the file with Claude. None when no key is set or the call fails —
    the family then types, so the screen always works."""
    if not reader_available():
        return None
    import anthropic

    settings = get_settings()
    encoded = base64.standard_b64encode(data).decode("ascii")
    block: dict[str, Any] = (
        {"type": "document", "source": {"type": "base64", "media_type": "application/pdf", "data": encoded}}
        if content_type == "application/pdf"
        else {"type": "image", "source": {"type": "base64", "media_type": content_type, "data": encoded}}
    )
    try:
        async with anthropic.AsyncAnthropic(
            api_key=settings.anthropic_api_key, timeout=60.0, max_retries=1
        ) as client:
            response = await client.beta.messages.create(
                model=settings.matchmaker_model,
                max_tokens=2000,
                system=_SYSTEM,
                messages=[
                    {
                        "role": "user",
                        "content": [block, {"type": "text", "text": "Read this biodata."}],
                    }
                ],
                output_config={"effort": "low", "format": {"type": "json_schema", "schema": _SCHEMA}},
                betas=["server-side-fallback-2026-07-01"],
                fallbacks="default",
            )
    except (anthropic.APIConnectionError, anthropic.RateLimitError, anthropic.APIStatusError) as exc:
        logger.warning("biodata reader unavailable (%s); family types instead", type(exc).__name__)
        return None
    if response.stop_reason == "refusal":
        return None
    text = next((b.text for b in response.content if b.type == "text"), "")
    try:
        return clean_fields(json.loads(text))
    except json.JSONDecodeError:
        return None


# --- An attached file, kept after publish (owner only) ------------------------

def save_document(profile_id: uuid.UUID, data: bytes) -> tuple[str, str]:
    """Store an attached biodata or horoscope file; returns (storage_ref, type)."""
    content_type = check(data)
    directory = storage._LOCAL_MEDIA_ROOT / str(profile_id) / "documents"  # noqa: SLF001
    directory.mkdir(parents=True, exist_ok=True)
    filename = f"{uuid.uuid4()}.{_KINDS[content_type]}"
    (directory / filename).write_bytes(data)
    return f"local://{profile_id}/documents/{filename}", content_type


def document_path(storage_ref: str) -> Path:
    return storage.local_path(storage_ref)


def delete_document_file(storage_ref: str) -> None:
    try:
        document_path(storage_ref).unlink(missing_ok=True)
    except (OSError, ValueError):
        logger.warning("could not delete an attached document file")
