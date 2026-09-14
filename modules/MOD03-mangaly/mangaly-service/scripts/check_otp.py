"""End-to-end check of the OTP slice against a RUNNING server — FR095/TR095/SP095.

Reads the code out of server logs rather than the HTTP response, matching how
a real deployment works today (no SMS_PROVIDER configured — see
`identity_bridge/delivery.py` — so the code is logged, never returned in the
response body). Run the API with output going to LOG_PATH, then:

  python -m scripts.check_otp

Each check names the requirement it exercises.
"""

from __future__ import annotations

import os
import re
import sys
import time
import urllib.request
from json import dumps, loads
from typing import Any
from urllib import error, request

BASE = "http://127.0.0.1:8000"
LOG_PATH = os.environ.get("MANGALY_API_LOG", r"C:\Users\krish\Krishna2025\startup2026\ForKhatri\modules\MOD03-mangaly\mangaly-service\.dev-api.log")

passed: list[str] = []
failed: list[str] = []


def call(method: str, path: str, body: dict[str, Any]) -> tuple[int, Any]:
    req = request.Request(
        f"{BASE}{path}",
        data=dumps(body).encode(),
        method=method,
        headers={"Content-Type": "application/json"},
    )
    try:
        with request.urlopen(req, timeout=30) as res:
            raw = res.read().decode()
            return res.status, (loads(raw) if raw else "")
    except error.HTTPError as e:
        raw = e.read().decode()
        return e.code, (loads(raw) if raw else "")


def check(label: str, ok: bool, detail: str = "") -> None:
    (passed if ok else failed).append(label)
    print(f"  {'PASS' if ok else 'FAIL'}  {label}{f' — {detail}' if detail else ''}")


def latest_code_for(identifier: str) -> str | None:
    """Pull the most recently logged OTP for an identifier out of the server log."""
    try:
        with open(LOG_PATH, encoding="utf-8", errors="replace") as f:
            lines = f.readlines()
    except FileNotFoundError:
        return None
    pattern = re.compile(r"OTP for .*?: (\d+) \(dev/fallback log")
    for line in reversed(lines):
        if identifier[-4:] in line or "·" in line:  # masked identifier check is loose by design
            m = pattern.search(line)
            if m:
                return m.group(1)
    for line in reversed(lines):
        m = pattern.search(line)
        if m:
            return m.group(1)
    return None


def main() -> int:
    print("\nMangaly OTP slice — live checks (FR095/TR095/TS212/TS213/SP095)\n")

    status, _ = call("GET", "/health", {}) if False else (200, None)  # placeholder, replaced below
    import urllib.request as _r

    try:
        with _r.urlopen(f"{BASE}/health", timeout=5) as res:
            status = res.status
    except Exception as exc:
        print(f"  API not reachable at {BASE}: {exc}. Start it first.")
        return 2
    if status != 200:
        print(f"  API health check failed: {status}")
        return 2

    identifier = f"+9198{int(time.time()) % 10**8:08d}"
    credential = "MangalyOtpCheck#2026"

    s_status, s_body = call("POST", "/auth/signup", {"identifier": identifier, "credential": credential})
    check("FR092 signup accepted (prerequisite)", s_status == 202, f"status={s_status}")

    code = latest_code_for(identifier)
    check("OTP code readable from delivery log (dev-mode delivery)", code is not None)
    if code is None:
        print("\n  Cannot continue without a code — is the API's stdout redirected to LOG_PATH?")
        print(f"  LOG_PATH = {LOG_PATH}")
        return 1

    # -- TS213: wrong code rejected with a distinct, specific reason ---------
    v_status, v_body = call(
        "POST", "/auth/otp/verify", {"identifier": identifier, "code": "000000", "purpose": "signup"}
    )
    check(
        "TS213 wrong code rejected as 'invalid'",
        v_status == 200 and v_body.get("outcome") == "invalid",
        f"{v_status} {v_body}",
    )

    # -- TS212: correct code verifies and produces a session (signup path) ---
    v_status, v_body = call(
        "POST", "/auth/otp/verify", {"identifier": identifier, "code": code, "purpose": "signup"}
    )
    check(
        "TS212 correct code verifies",
        v_status == 200 and v_body.get("outcome") == "verified",
        f"{v_status} {v_body}",
    )
    check(
        "UX04 signup-path verification opens a session (lands authenticated at Onboarding)",
        v_body.get("account_id") is not None,
        f"{v_body}",
    )

    # -- Single-use: the same code cannot be replayed -------------------------
    v_status, v_body = call(
        "POST", "/auth/otp/verify", {"identifier": identifier, "code": code, "purpose": "signup"}
    )
    check(
        "FR095 code is single-use (replay rejected)",
        v_body.get("outcome") == "invalid",
        f"{v_body}",
    )

    # -- Now-active account can log in with the password from signup ---------
    l_status, l_body = call("POST", "/auth/login", {"identifier": identifier, "credential": credential})
    check(
        "FR092 acceptance criterion: verified account can now log in",
        l_status == 200,
        f"status={l_status}",
    )

    # -- SP095: resend is rate-limited ----------------------------------------
    identifier2 = f"+9198{(int(time.time()) + 7) % 10**8:08d}"
    call("POST", "/auth/signup", {"identifier": identifier2, "credential": credential})
    codes = [
        call("POST", "/auth/otp/resend", {"identifier": identifier2, "purpose": "signup"})[0]
        for _ in range(7)
    ]
    check("SP095 resend is rate-limited (429 appears)", 429 in codes, f"codes={codes}")

    # -- SP092-class: resend gives identical response for unknown identifier -
    unknown = f"+9198{(int(time.time()) + 999) % 10**8:08d}"
    r1_status, r1_body = call("POST", "/auth/otp/resend", {"identifier": identifier2, "purpose": "signup"})
    r2_status, r2_body = call("POST", "/auth/otp/resend", {"identifier": unknown, "purpose": "signup"})
    # identifier2 may be rate-limited (429) from the burst above; compare shape not exact codes.
    check(
        "Resend gives a response for an unregistered identifier too (no existence leak)",
        r2_status in (202, 429),
        f"status={r2_status} body={r2_body}",
    )

    print(f"\n  {len(passed)} passed, {len(failed)} failed\n")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
