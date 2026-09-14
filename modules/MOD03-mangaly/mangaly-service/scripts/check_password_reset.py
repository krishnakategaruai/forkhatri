"""End-to-end check of FR094 (forgot/reset password) against a RUNNING server.

Run the API first, then: python -m scripts.check_password_reset
"""

from __future__ import annotations

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


def check(label: str, ok: bool, detail: str = "") -> None:
    (passed if ok else failed).append(label)
    print(f"  {'PASS' if ok else 'FAIL'}  {label}{f' — {detail}' if detail else ''}")


def latest_otp_for() -> str | None:
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
    print("\nMangaly password reset — live checks (FR094/TR094)\n")

    try:
        with urllib.request.urlopen(f"{BASE}/health", timeout=5) as res:
            if res.status != 200:
                raise RuntimeError
    except Exception:
        print(f"  API not reachable at {BASE}. Start it first.")
        return 2

    identifier = f"+9198{int(time.time()) % 10**8:08d}"
    s, b = call_json("POST", "/auth/signup", {"identifier": identifier})
    code = latest_otp_for()
    v_status, v_body = call_json(
        "POST", "/auth/otp/verify", {"identifier": identifier, "code": code, "purpose": "signup"}
    )
    check("prerequisite: fresh account signed up and verified", v_status == 200, f"{v_status} {v_body}")

    # -- FR094: request a reset ---------------------------------------------------
    s, b = call_json("POST", "/auth/reset/request", {"identifier": identifier})
    check("Reset request accepted (202)", s == 202, f"{s} {b}")

    reset_code = latest_otp_for()
    check("A reset OTP was actually issued", reset_code is not None and reset_code != code)

    # -- Anti-enumeration: unknown identifier gets the identical response --------
    s, b_unknown = call_json("POST", "/auth/reset/request", {"identifier": "+919999999999"})
    check(
        "Unknown identifier gets the identical response shape (SP094 anti-enumeration)",
        s == 202 and b_unknown.get("message") == b.get("message"),
        f"{s} {b_unknown}",
    )

    # -- Wrong code is rejected ----------------------------------------------------
    s, b = call_json(
        "POST", "/auth/reset/confirm",
        {"identifier": identifier, "code": "000000", "new_credential": "Sup3rSecret!2026"},
    )
    check("Wrong reset code is rejected", s == 200 and b.get("outcome") == "invalid", f"{s} {b}")

    # -- Weak new credential is rejected -------------------------------------------
    s, b = call_json(
        "POST", "/auth/reset/confirm",
        {"identifier": identifier, "code": reset_code, "new_credential": "aaaa"},
    )
    check("A weak new credential is rejected (422)", s == 422, f"{s} {b}")

    # -- Correct code + strong new credential succeeds -----------------------------
    s, b = call_json(
        "POST", "/auth/reset/confirm",
        {"identifier": identifier, "code": reset_code, "new_credential": "Sup3rSecret!2026"},
    )
    check("Correct code + strong password resets successfully", s == 200 and b.get("outcome") == "verified", f"{s} {b}")

    # -- The code is single-use: re-using it now fails -----------------------------
    s, b = call_json(
        "POST", "/auth/reset/confirm",
        {"identifier": identifier, "code": reset_code, "new_credential": "AnotherOne!2026"},
    )
    check("The same reset code cannot be reused (single-use)", b.get("outcome") != "verified", f"{s} {b}")

    # -- The new password actually works for login ---------------------------------
    s, b = call_json("POST", "/auth/login", {"identifier": identifier, "credential": "Sup3rSecret!2026"})
    check("Logging in with the NEW password succeeds", s == 200, f"{s} {b}")

    print(f"\n  {len(passed)} passed, {len(failed)} failed\n")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
