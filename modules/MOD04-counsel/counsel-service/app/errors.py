"""One error shape for every handler: {"detail": {"code", "message"}}.
Codes are stable identifiers the web client translates; the message is the
English fallback."""

from __future__ import annotations

from fastapi import HTTPException


class DomainError(HTTPException):
    def __init__(self, code: str, message: str, status: int = 400, **extra):
        super().__init__(status_code=status, detail={"code": code, "message": message, **extra})
        self.code = code


def not_found(what: str = "resource") -> DomainError:
    return DomainError("not_found", f"{what} not found", 404)


def forbidden(message: str = "Not allowed") -> DomainError:
    return DomainError("forbidden", message, 403)


def invalid(code: str, message: str) -> DomainError:
    return DomainError(code, message, 422)
