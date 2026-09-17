"""Identifier normalisation and masking (07-tech-reqs.md TR13)."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Literal

from email_validator import EmailNotValidError, validate_email

_E164 = re.compile(r"^\+[1-9]\d{7,14}$")
_INDIAN_MOBILE = re.compile(r"^[6-9]\d{9}$")
_SEPARATORS = re.compile(r"[\s\-().]")


class InvalidIdentifier(ValueError):
    pass


@dataclass(frozen=True, slots=True)
class Identifier:
    kind: Literal["phone", "email"]
    value: str

    @property
    def channel(self) -> Literal["sms", "email"]:
        return "sms" if self.kind == "phone" else "email"

    def hint(self) -> str:
        return mask_phone(self.value) if self.kind == "phone" else mask_email(self.value)


def normalize(raw: str) -> Identifier:
    candidate = raw.strip()
    if "@" in candidate:
        try:
            email = validate_email(candidate, check_deliverability=False).normalized
        except EmailNotValidError as exc:
            raise InvalidIdentifier("Enter a valid email address.") from exc
        return Identifier("email", email.lower())

    digits = _SEPARATORS.sub("", candidate)
    if digits.startswith("+"):
        if _E164.match(digits):
            return Identifier("phone", digits)
        raise InvalidIdentifier("Enter a valid mobile number.")
    if len(digits) == 11 and digits.startswith("0"):
        digits = digits[1:]
    elif len(digits) == 12 and digits.startswith("91"):
        digits = digits[2:]
    if _INDIAN_MOBILE.match(digits):
        return Identifier("phone", f"+91{digits}")
    raise InvalidIdentifier("Enter a valid mobile number or email address.")


def mask_phone(phone: str) -> str:
    return f"{phone[:3]}••••••{phone[-4:]}"


def mask_email(email: str) -> str:
    local, _, domain = email.partition("@")
    return f"{local[:1]}•••@{domain}"
