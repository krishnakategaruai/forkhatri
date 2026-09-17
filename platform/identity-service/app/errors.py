"""Domain errors rendered as `{"detail": {"code", "message"}}` (07-tech-reqs.md TR13)."""

from __future__ import annotations


class DomainError(Exception):
    def __init__(self, code: str, message: str, status_code: int = 400) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.status_code = status_code
