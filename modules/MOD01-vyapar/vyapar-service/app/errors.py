# [Refactor A, 2026-09-21] One error envelope for every API error.
# Why: an agent or an SDK needs a stable, machine-readable reason, while a
# person needs a message in their own language. The web app today reads
# `detail` (a translated string, or for a few errors an object with
# `message`/`code` plus extra fields), so `detail` stays exactly as it was
# and a new `error` object is added beside it:
#
#     {"detail": "<unchanged>",
#      "error": {"code": "opportunity_not_found", "message": "<localized>",
#                "details": {...}}}
#
# The code is derived from the translation key the message already uses
# (`common.error.opportunityNotFound` -> `opportunity_not_found`), so codes
# and messages can never drift apart and no second catalogue of codes has
# to be maintained. Services raise `ApiError`; it is an HTTPException, so
# any existing `except HTTPException` keeps working unchanged.
# Traces to: REFACTOR-PLAN.md §A (error envelope)
from __future__ import annotations

import re
from typing import Any

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.i18n import resolve_language, translate

_CAMEL_BOUNDARY = re.compile(r"(?<=[a-z0-9])(?=[A-Z])")
_CODE_LIKE = re.compile(r"^[a-z][a-z0-9_]*$")

_STATUS_CODES = {
    400: "bad_request",
    401: "unauthorized",
    402: "payment_required",
    403: "forbidden",
    404: "not_found",
    405: "method_not_allowed",
    409: "conflict",
    410: "gone",
    413: "payload_too_large",
    422: "unprocessable",
    429: "rate_limited",
    500: "internal_error",
    502: "bad_gateway",
    503: "service_unavailable",
}


# Last segments that several namespaces share (`campaigns.error.notFound`,
# `enquiries.error.notFound`, ...). For these the code is qualified with the
# namespace (`campaigns_not_found`) so it still says WHAT was not found. The
# list is fixed on purpose: computing it from the catalogues would silently
# rename an existing code the day a new namespace reused a segment.
_AMBIGUOUS_SEGMENTS = frozenset({
    "notFound", "invalidTransition", "permissionRequired", "productNotFound",
    "dailyCapReached", "senderOnly", "targetNotActive",
})


def _snake(text: str) -> str:
    return _CAMEL_BOUNDARY.sub("_", text).lower()


def code_from_key(key: str) -> str:
    """`common.error.opportunityNotFound` -> `opportunity_not_found`;
    `campaigns.error.notFound` -> `campaigns_not_found`."""
    namespace = key.split(".", 1)[0]
    last = key.rsplit(".", 1)[-1]
    if last in _AMBIGUOUS_SEGMENTS:
        return f"{_snake(namespace)}_{_snake(last)}"
    return _snake(last)


class ErrorBody(BaseModel):
    code: str = Field(description="Stable, machine-readable reason, e.g. opportunity_not_found")
    message: str = Field(description="Human-readable message in the caller's language")
    details: dict[str, Any] = Field(default_factory=dict)


class ErrorResponse(BaseModel):
    """Shape of every error response. `detail` is kept for existing clients."""

    detail: Any = None
    error: ErrorBody


# Attached to every router so each operation in the OpenAPI document lists
# the error shape it can return (SDK and agent-tool generators read this).
ERROR_RESPONSES: dict[int | str, dict[str, Any]] = {
    400: {"model": ErrorResponse, "description": "The request is not allowed in the current state"},
    401: {"model": ErrorResponse, "description": "No valid session or credential"},
    403: {"model": ErrorResponse, "description": "The caller lacks the permission or role required"},
    404: {"model": ErrorResponse, "description": "Not found, or not visible to the caller"},
    409: {"model": ErrorResponse, "description": "Conflicts with an existing record"},
    422: {"model": ErrorResponse, "description": "Missing or invalid fields"},
    429: {"model": ErrorResponse, "description": "A rate limit or cap was reached"},
}


class ApiError(HTTPException):
    """A translated, coded API error.

    `ApiError(404, "common.error.opportunityNotFound", lang)` produces the
    same `detail` string as the old `HTTPException(404, detail=translate(...))`.
    When `code` or `extra` is given, `detail` is the object shape a few
    endpoints already used (`{"message", "code"?, **extra}`), in that order.
    `error_code` overrides only the envelope's code (for keys whose last
    segment is a variable, e.g. `verification.error.invalidFormat.gst`)
    and leaves `detail` untouched.
    """

    def __init__(
        self,
        status_code: int,
        key: str,
        lang: str | None,
        *,
        code: str | None = None,
        extra: dict[str, Any] | None = None,
        error_code: str | None = None,
        headers: dict[str, str] | None = None,
        **params: Any,
    ) -> None:
        message = translate(key, lang, **params)
        self.key = key
        self.message = message
        self.code = error_code or code or code_from_key(key)
        self.params = params
        self.extra = dict(extra or {})
        if code is not None or extra:
            detail: Any = {"message": message}
            if code is not None:
                detail["code"] = code
            detail.update(self.extra)
        else:
            detail = message
        super().__init__(status_code=status_code, detail=detail, headers=headers)


def _envelope(status_code: int, detail: Any, exc: Exception | None) -> dict[str, Any]:
    if isinstance(exc, ApiError):
        details: dict[str, Any] = {"i18n_key": exc.key}
        details.update({k: v for k, v in exc.params.items()})
        details.update(exc.extra)
        return {"code": exc.code, "message": exc.message, "details": details}
    if isinstance(detail, dict):
        message = detail.get("message")
        code = detail.get("code")
        rest = {k: v for k, v in detail.items() if k not in ("message", "code")}
        return {
            "code": code if isinstance(code, str) else _STATUS_CODES.get(status_code, "error"),
            "message": message if isinstance(message, str) else "",
            "details": rest,
        }
    if isinstance(detail, str):
        code = detail if _CODE_LIKE.match(detail) else _STATUS_CODES.get(status_code, "error")
        return {"code": code, "message": detail, "details": {}}
    return {"code": _STATUS_CODES.get(status_code, "error"), "message": "", "details": {}}


def _request_lang(request: Request) -> str:
    return resolve_language(request.headers.get("X-Vyapar-Language") or request.headers.get("Accept-Language"))


async def _http_exception_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
    headers = getattr(exc, "headers", None)
    if exc.status_code in (204, 304):
        from starlette.responses import Response

        return Response(status_code=exc.status_code, headers=headers)
    body = {"detail": exc.detail, "error": _envelope(exc.status_code, exc.detail, exc)}
    if not body["error"]["message"]:
        body["error"]["message"] = translate("common.error.generic", _request_lang(request))
    return JSONResponse(jsonable_encoder(body), status_code=exc.status_code, headers=headers)


async def _validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    errors = jsonable_encoder(exc.errors())
    body = {
        "detail": errors,
        "error": {
            "code": "validation_error",
            "message": translate("common.error.validation", _request_lang(request)),
            "details": {"errors": errors},
        },
    }
    return JSONResponse(body, status_code=422)


def register_error_handlers(app: FastAPI) -> None:
    app.add_exception_handler(StarletteHTTPException, _http_exception_handler)
    app.add_exception_handler(RequestValidationError, _validation_exception_handler)
