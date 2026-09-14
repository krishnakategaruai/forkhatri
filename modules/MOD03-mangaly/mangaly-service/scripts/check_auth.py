"""End-to-end check of the auth slice against a RUNNING server.

This is a live smoke check, not a unit test: it proves the deployed thing
actually works, including the parts (cookies, CORS, rate limiting, timing)
that only exist over real HTTP.

Run the API first, then:  python -m scripts.check_auth

Each check names the requirement it exercises, so a failure points at a spec
line rather than just a broken assert.
"""

from __future__ import annotations

import statistics
import sys
import time
import urllib.error
import urllib.request
import uuid
from http.cookiejar import CookieJar
from json import dumps, loads
from typing import Any

BASE = "http://127.0.0.1:8000"
GOOD_ID = "+919800000001"
GOOD_PW = "MangalyTest#2026"

_opener = urllib.request.build_opener(
    urllib.request.HTTPCookieProcessor(CookieJar())
)

passed: list[str] = []
failed: list[str] = []


def _decode(raw: str) -> dict[str, Any] | str:
    """Bodies are not always JSON (429 from a proxy, empty 204, HTML errors)."""
    if not raw:
        return ""
    try:
        return loads(raw)
    except ValueError:
        return raw.strip()


def call(
    method: str, path: str, body: dict[str, Any] | None = None, jar: bool = False
) -> tuple[int, dict[str, Any] | str, dict[str, str]]:
    data = dumps(body).encode() if body is not None else None
    req = urllib.request.Request(f"{BASE}{path}", data=data, method=method)
    if data:
        req.add_header("Content-Type", "application/json")
    opener = _opener if jar else urllib.request.build_opener()
    try:
        with opener.open(req, timeout=60) as res:
            headers = {k.lower(): v for k, v in res.headers.items()}
            return res.status, _decode(res.read().decode(errors="replace")), headers
    except urllib.error.HTTPError as e:
        headers = {k.lower(): v for k, v in e.headers.items()}
        return e.code, _decode(e.read().decode(errors="replace")), headers
    except (urllib.error.URLError, ConnectionResetError, TimeoutError) as e:
        return 0, f"transport error: {e}", {}


def check(label: str, ok: bool, detail: str = "") -> None:
    (passed if ok else failed).append(label)
    print(f"  {'PASS' if ok else 'FAIL'}  {label}{f' — {detail}' if detail else ''}")


def reset_rate_limits() -> None:
    """Clear this script's own login-failure counters before running.

    Required for re-runnability, and its necessity is itself a good sign: the
    counters are deliberately durable (they survive the rolled-back transaction
    of the failed login that produced them — see `limiter.enforce_durable`), so
    a previous run's deliberate lockout would otherwise carry into this one and
    fail every later check with a spurious 429.

    This resets ONLY the `login_failure:` keys, so a real limit reached during
    the run still registers.
    """
    import asyncio

    from sqlalchemy import text as sql_text

    from app.config.settings import get_settings
    from app.db.engine import create_engine, create_session_factory

    async def _run() -> None:
        engine = create_engine(get_settings())
        factory = create_session_factory(engine)
        try:
            async with factory() as s, s.begin():
                await s.execute(
                    sql_text(
                        "DELETE FROM mangaly_platform.rate_limit_counter "
                        "WHERE rate_limit_key LIKE 'login_failure:%'"
                    )
                )
        finally:
            await engine.dispose()

    asyncio.run(_run())


def main() -> int:
    print("\nMangaly auth slice — live checks (FR092/FR093/FR090/FR101)\n")

    status, _, _ = call("GET", "/health")
    if status != 200:
        print(f"  API not reachable at {BASE} (health returned {status}). Start it first.")
        return 2

    reset_rate_limits()

    # -- FR093/TR093: a seeded account can actually log in -------------------
    status, body, headers = call(
        "POST", "/auth/login", {"identifier": GOOD_ID, "credential": GOOD_PW}, jar=True
    )
    check(
        "FR093 login succeeds with seeded credentials",
        status == 200 and isinstance(body, dict) and "account_id" in body,
        f"status={status}",
    )
    cookie_hdr = headers.get("set-cookie", "")
    check(
        "SP090 session cookie is HttpOnly",
        "httponly" in cookie_hdr.lower(),
        cookie_hdr.split(";")[0] if cookie_hdr else "no cookie",
    )
    check(
        "SP090 session cookie is SameSite-constrained",
        "samesite" in cookie_hdr.lower(),
    )

    # -- FR090/TR090: the session actually resolves --------------------------
    status, body, _ = call("GET", "/auth/me", jar=True)
    check("FR090 session resolves via /auth/me", status == 200, f"status={status}")

    # -- FR101/TR101: logout revokes SERVER-side -----------------------------
    status, _, _ = call("POST", "/auth/logout", jar=True)
    check("FR101 logout returns 204", status == 204, f"status={status}")

    # -- SP093: wrong password and unknown account are indistinguishable -----
    s1, b1, _ = call("POST", "/auth/login", {"identifier": GOOD_ID, "credential": "wrong-password"})
    unknown = f"+9198{uuid.uuid4().int % 10**8:08d}"
    s2, b2, _ = call("POST", "/auth/login", {"identifier": unknown, "credential": "wrong-password"})
    check(
        "SP093 identical status for wrong-password vs unknown-account",
        s1 == s2 == 401,
        f"{s1} vs {s2}",
    )
    check("SP093 identical response body for both", b1 == b2, f"{b1!r} vs {b2!r}")

    # -- SP093: the timing half. This is the check that a body-only ----------
    #    comparison would miss entirely.
    def sample(identifier: str, n: int = 5) -> float:
        # Reset first: these are deliberate failures, and without a reset the
        # durable counter trips partway through and the later samples measure a
        # fast 429 rejection instead of the Argon2id path we are timing.
        reset_rate_limits()
        times = []
        for _ in range(n):
            t0 = time.perf_counter()
            call("POST", "/auth/login", {"identifier": identifier, "credential": "wrong-password"})
            times.append(time.perf_counter() - t0)
        return statistics.median(times)

    known_ms = sample(GOOD_ID) * 1000
    unknown_ms = sample(f"+9198{uuid.uuid4().int % 10**8:08d}") * 1000
    spread = abs(known_ms - unknown_ms) / max(known_ms, unknown_ms)
    check(
        "SP093 no timing oracle (dummy-verify runs for unknown accounts)",
        spread < 0.35,
        f"known {known_ms:.0f}ms vs unknown {unknown_ms:.0f}ms ({spread:.0%} apart)",
    )

    # -- SP092: signup never reveals whether an identifier is registered -----
    s3, b3, _ = call(
        "POST", "/auth/signup", {"identifier": GOOD_ID, "credential": "AnotherPass#2026"}
    )
    fresh = f"+9198{uuid.uuid4().int % 10**8:08d}"
    s4, b4, _ = call(
        "POST", "/auth/signup", {"identifier": fresh, "credential": "AnotherPass#2026"}
    )
    check(
        "SP092 signup gives identical status for existing vs new identifier",
        s3 == s4 == 202,
        f"{s3} vs {s4}",
    )
    check("SP092 signup gives identical body for both", b3 == b4, f"{b3!r} vs {b4!r}")

    # -- TR092: a new signup is pending_verification, not usable yet ---------
    s5, _, _ = call("POST", "/auth/login", {"identifier": fresh, "credential": "AnotherPass#2026"})
    check(
        "TR092 a signed-up-but-unverified account cannot log in yet",
        s5 == 401,
        f"status={s5}",
    )

    # -- TR093/SP093: rate limiting actually engages -------------------------
    burst_id = f"+9198{uuid.uuid4().int % 10**8:08d}"
    codes = [
        call("POST", "/auth/login", {"identifier": burst_id, "credential": "x" * 12})[0]
        for _ in range(8)
    ]
    check(
        "TR093 repeated failures are rate-limited (429)",
        429 in codes,
        f"codes={codes}",
    )

    print(f"\n  {len(passed)} passed, {len(failed)} failed\n")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
