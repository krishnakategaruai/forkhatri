"""End-to-end check of FR001 (minimum-viable-profile save) against a RUNNING server.

Signs up a fresh account, verifies it via OTP (reusing the auth slice this
depends on), then exercises profile creation: missing fields, underage
rejection, a successful save with a real photo upload, and the duplicate-
profile guard.

Run the API first, then: python -m scripts.check_profile
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


def call_json(method: str, path: str, body: dict[str, Any]) -> tuple[int, Any]:
    req = urllib.request.Request(
        f"{BASE}{path}", data=dumps(body).encode(), method=method,
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
    print("\nMangaly profile slice — live checks (FR001/TR001/SP001)\n")

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

    # -- FR001 failure outcome: missing required fields -----------------------
    s, b = call_multipart(
        "/profile",
        {"name": "", "date_of_birth": "1996-04-12", "gender": "female", "city_locality": "Hyderabad"},
        "photo", "photo.jpg", TINY_JPEG, "image/jpeg",
    )
    check("FR001 missing name is rejected (422)", s == 422, f"{s} {b}")

    # -- TR041/DEC-V1-005: marriageable-age gate -------------------------------
    s, b = call_multipart(
        "/profile",
        {"name": "Too Young", "date_of_birth": "2015-01-01", "gender": "female", "city_locality": "Hyderabad"},
        "photo", "photo.jpg", TINY_JPEG, "image/jpeg",
    )
    check("TR041/DEC-V1-005 underage profile is rejected (422)", s == 422, f"{s} {b}")

    # -- Unsupported media type -------------------------------------------------
    s, b = call_multipart(
        "/profile",
        {"name": "Bad Photo", "date_of_birth": "1996-04-12", "gender": "female", "city_locality": "Hyderabad"},
        "photo", "photo.txt", b"not a photo", "text/plain",
    )
    check("Unsupported photo content-type is rejected (422)", s == 422, f"{s} {b}")

    # -- Success path -----------------------------------------------------------
    s, b = call_multipart(
        "/profile",
        {"name": "Priya Sharma", "date_of_birth": "1996-04-12", "gender": "female", "city_locality": "Hyderabad, Telangana"},
        "photo", "photo.jpg", TINY_JPEG, "image/jpeg",
    )
    check("FR001 valid profile saves (201)", s == 201, f"{s} {b}")
    check("Saved profile has a resolved photo_url", isinstance(b, dict) and bool(b.get("photo_url")), f"{b}")

    # -- Duplicate guard ----------------------------------------------------------
    s, b = call_multipart(
        "/profile",
        {"name": "Priya Again", "date_of_birth": "1996-04-12", "gender": "female", "city_locality": "Hyderabad"},
        "photo", "photo.jpg", TINY_JPEG, "image/jpeg",
    )
    check("Second profile for same account is rejected (409)", s == 409, f"{s} {b}")

    # -- Read-back ----------------------------------------------------------------
    req = urllib.request.Request(f"{BASE}/profile/me", method="GET")
    try:
        with _opener.open(req, timeout=15) as res:
            s, b = res.status, loads(res.read().decode())
    except urllib.error.HTTPError as e:
        s, b = e.code, e.read().decode()
    check("GET /profile/me returns the saved profile", s == 200 and b.get("name") == "Priya Sharma", f"{s} {b}")

    # -- The photo URL is actually servable ---------------------------------------
    photo_url = b.get("photo_url") if isinstance(b, dict) else None
    if photo_url:
        try:
            with urllib.request.urlopen(f"{BASE}{photo_url}", timeout=15) as res:
                check("Saved photo is actually retrievable via its URL", res.status == 200, f"status={res.status}")
        except urllib.error.HTTPError as e:
            check("Saved photo is actually retrievable via its URL", False, f"status={e.code}")

    print(f"\n  {len(passed)} passed, {len(failed)} failed\n")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
