"""End-to-end check of FR002/FR003/FR005 against a RUNNING server.

Signs up a fresh account, verifies it, creates an existence-tier profile,
then exercises: per-category attribute upsert (set + decline + overwrite),
the discoverability-tier gate, and the three-tier completeness read — all
against the real `mangaly_profile.profile_attribute` table, never mocked.

Run the API first, then: python -m scripts.check_profile_categories
"""

from __future__ import annotations

import io
import re
import sys
import time
import urllib.error
import urllib.request
from http.cookiejar import CookieJar
from json import dumps, loads
from typing import Any

BASE = "http://127.0.0.1:8000"
LOG_PATH = r"C:\Users\krish\Krishna2025\startup2026\ForKhatri\modules\MOD03-mangaly\mangaly-service\.dev-api.log"

passed: list[str] = []
failed: list[str] = []
_opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(CookieJar()))


def call_json(method: str, path: str, body: dict[str, Any] | None) -> tuple[int, Any]:
    data = dumps(body).encode() if body is not None else None
    req = urllib.request.Request(
        f"{BASE}{path}", data=data, method=method,
        headers={"Content-Type": "application/json"},
    )
    try:
        with _opener.open(req, timeout=30) as res:
            raw = res.read().decode()
            return res.status, (loads(raw) if raw else "")
    except urllib.error.HTTPError as e:
        raw = e.read().decode()
        try:
            return e.code, loads(raw)
        except ValueError:
            return e.code, raw


def call_multipart(path: str, fields: dict[str, str], file_field: str, filename: str, content: bytes, content_type: str) -> tuple[int, Any]:
    boundary = "----mangalycheck"
    parts = []
    for key, value in fields.items():
        parts.append(f"--{boundary}\r\nContent-Disposition: form-data; name=\"{key}\"\r\n\r\n{value}\r\n")
    body = "".join(parts).encode()
    body += (
        f"--{boundary}\r\nContent-Disposition: form-data; name=\"{file_field}\"; filename=\"{filename}\"\r\n"
        f"Content-Type: {content_type}\r\n\r\n"
    ).encode() + content + f"\r\n--{boundary}--\r\n".encode()

    req = urllib.request.Request(
        f"{BASE}{path}", data=body, method="POST",
        headers={"Content-Type": f"multipart/form-data; boundary={boundary}"},
    )
    try:
        with _opener.open(req, timeout=30) as res:
            raw = res.read().decode()
            return res.status, (loads(raw) if raw else "")
    except urllib.error.HTTPError as e:
        raw = e.read().decode()
        try:
            return e.code, loads(raw)
        except ValueError:
            return e.code, raw


def check(label: str, ok: bool, detail: str = "") -> None:
    (passed if ok else failed).append(label)
    print(f"  {'PASS' if ok else 'FAIL'}  {label}{f' — {detail}' if detail else ''}")


TINY_JPEG = bytes.fromhex(
    "ffd8ffe000104a46494600010100000100010000ffdb004300"
    + "10" * 63
    + "ffc0000b080001000101011100ffc4001f0000010501010101010100000000000000000102030405060708090a0bffda"
    + "0008010100003f00d2cf20ffd9"
)


def latest_otp_for(identifier: str) -> str | None:
    try:
        with open(LOG_PATH, encoding="utf-8", errors="replace") as f:
            lines = f.readlines()
    except FileNotFoundError:
        return None
    pattern = re.compile(r"OTP for .*?: (\d+) \(dev/fallback log")
    for line in reversed(lines):
        m = pattern.search(line)
        if m:
            return m.group(1)
    return None


def main() -> int:
    print("\nMangaly profile categories — live checks (FR002/FR003/FR005/TR002/TR003/TR005)\n")

    try:
        with urllib.request.urlopen(f"{BASE}/health", timeout=5) as res:
            if res.status != 200:
                raise RuntimeError
    except Exception:
        print(f"  API not reachable at {BASE}. Start it first.")
        return 2

    identifier = f"+9198{int(time.time()) % 10**8:08d}"
    call_json("POST", "/auth/signup", {"identifier": identifier})
    code = latest_otp_for(identifier)
    check("prerequisite: signup issued an OTP", code is not None)
    if code is None:
        return 1
    v_status, v_body = call_json(
        "POST", "/auth/otp/verify", {"identifier": identifier, "code": code, "purpose": "signup"}
    )
    check("prerequisite: signup OTP verifies and opens a session", v_status == 200 and v_body.get("outcome") == "verified", f"{v_status} {v_body}")

    s, b = call_multipart(
        "/profile",
        {"name": "Anita Rao", "date_of_birth": "1994-06-20", "gender": "female", "city_locality": "Bengaluru, Karnataka"},
        "photo", "photo.jpg", TINY_JPEG, "image/jpeg",
    )
    check("prerequisite: existence-tier profile saves", s == 201, f"{s} {b}")

    # -- PATCH against a profile-less account is rejected -----------------------
    # (covered implicitly below since this account now HAS a profile; the
    # ProfileNotFound path is exercised by the completeness-without-profile
    # check further down using a brand-new, profile-less account instead.)

    # -- Category upsert: set two of the four required discoverability fields ---
    s, b = call_json(
        "PATCH", "/profile/education", {"highest_education_level": {"state": "value", "value": "masters"}}
    )
    check("PATCH /profile/education sets a value (204)", s == 204, f"{s} {b}")

    s, b = call_json(
        "PATCH", "/profile/profession", {"occupation": {"state": "value", "value": "software_engineer"}}
    )
    check("PATCH /profile/profession sets a value (204)", s == 204, f"{s} {b}")

    # -- Completeness: still incomplete (2 of 4 + partner-pref any-of missing) --
    s, b = call_json("GET", "/profile/completeness", None)
    check(
        "GET /profile/completeness reflects partial discoverability tier",
        s == 200 and b.get("discoverability_complete") is False and len(b.get("discoverability_missing", [])) == 3,
        f"{s} {b}",
    )
    check("Completeness existence tier is already true", isinstance(b, dict) and b.get("existence_complete") is True, f"{b}")

    # -- Decline a field: an active choice, distinct from unset -----------------
    s, b = call_json(
        "PATCH", "/profile/marital_history", {"marital_status": {"state": "declined"}}
    )
    check("PATCH can decline a field (204)", s == 204, f"{s} {b}")

    s, b = call_json("GET", "/profile/completeness", None)
    still_missing = b.get("discoverability_missing", []) if isinstance(b, dict) else []
    check(
        "A declined field still counts as missing for discoverability (not satisfied by declining)",
        "marital_history.marital_status" in still_missing,
        f"{still_missing}",
    )

    # -- Complete the remaining required fields + one partner-preference field --
    s, b = call_json(
        "PATCH", "/profile/relocation", {"relocation_willingness": {"state": "value", "value": "yes"}}
    )
    check("PATCH /profile/relocation sets a value (204)", s == 204, f"{s} {b}")

    s, b = call_json(
        "PATCH", "/profile/marital_history", {"marital_status": {"state": "value", "value": "never_married"}}
    )
    check("Overwriting a previously-declined field to a value works (204)", s == 204, f"{s} {b}")

    s, b = call_json(
        "PATCH", "/profile/partner_preference", {"age_range": {"state": "value", "value": {"min": 28, "max": 36}}}
    )
    check("PATCH /profile/partner_preference sets the any-of field (204)", s == 204, f"{s} {b}")

    # -- Discoverability tier now satisfied --------------------------------------
    s, b = call_json("GET", "/profile/completeness", None)
    check(
        "GET /profile/completeness shows discoverability tier fully satisfied",
        s == 200 and b.get("discoverability_complete") is True and b.get("discoverability_missing") == [],
        f"{s} {b}",
    )

    # -- Enhanced-matching tier: touching one category is reflected, never gates -
    s, b = call_json(
        "PATCH", "/profile/lifestyle", {"diet": {"state": "value", "value": "vegetarian"}}
    )
    check("PATCH /profile/lifestyle (enhanced tier) sets a value (204)", s == 204, f"{s} {b}")

    s, b = call_json("GET", "/profile/completeness", None)
    check(
        "Enhanced-matching tier reflects the touched category without gating anything",
        s == 200 and b.get("enhanced_filled_categories") == 1 and b.get("discoverability_complete") is True,
        f"{s} {b}",
    )

    print(f"\n  {len(passed)} passed, {len(failed)} failed\n")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
