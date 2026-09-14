"""End-to-end check of Discovery/Connection/Communication
(FR021/FR026/FR027/FR030/FR042/FR043/FR044/FR045/FR049) against a RUNNING
server, using seeded dev accounts (password login).

Run the API first, then: python -m scripts.check_discovery_connection
"""

from __future__ import annotations

import sys
import urllib.error
import urllib.request
from http.cookiejar import CookieJar
from json import dumps, loads
from typing import Any

BASE = "http://127.0.0.1:8000"
DEV_PASSWORD = "MangalyDev123!"

passed: list[str] = []
failed: list[str] = []


def new_session() -> urllib.request.OpenerDirector:
    return urllib.request.build_opener(urllib.request.HTTPCookieProcessor(CookieJar()))


def call_json(
    opener: urllib.request.OpenerDirector, method: str, path: str, body: dict[str, Any] | None = None
) -> tuple[int, Any]:
    data = dumps(body).encode() if body is not None else None
    req = urllib.request.Request(
        f"{BASE}{path}", data=data, method=method, headers={"Content-Type": "application/json"}
    )
    try:
        with opener.open(req, timeout=30) as res:
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


def log_in(identifier: str, password: str = DEV_PASSWORD) -> urllib.request.OpenerDirector:
    opener = new_session()
    call_json(opener, "POST", "/auth/login", {"identifier": identifier, "credential": password})
    return opener


def main() -> int:
    print("\nMangaly Discovery/Connection/Communication — live checks\n")

    try:
        with urllib.request.urlopen(f"{BASE}/health", timeout=5) as res:
            if res.status != 200:
                raise RuntimeError
    except Exception:
        print(f"  API not reachable at {BASE}. Start it first.")
        return 2

    ananya = log_in("+919000000001")  # Hyderabad, masters, vegetarian, open_to_discussion
    rahul = log_in("+919000000002")  # Bengaluru, bachelors, non_vegetarian, yes

    s, me = call_json(ananya, "GET", "/auth/me")
    check("prerequisite: Ananya logs in", s == 200, f"{s} {me}")
    ananya_id = me.get("account_id")

    s, me2 = call_json(rahul, "GET", "/auth/me")
    check("prerequisite: Rahul logs in", s == 200, f"{s} {me2}")
    rahul_id = me2.get("account_id")

    # -- FR021/FR026: search returns a demographic snippet, ranked -------------
    s, results = call_json(ananya, "GET", "/discovery/search")
    check("FR021/FR026 search succeeds (200)", s == 200 and isinstance(results, list), f"{s} {results}")
    check(
        "Search results never carry a numeric 'popularity' or name/photo field",
        isinstance(results, list)
        and all(set(r.keys()) == {"candidate_account_id", "score", "locality", "education_level", "profession"} for r in results),
        f"{results}",
    )
    rahul_result = next((r for r in results if r["candidate_account_id"] == rahul_id), None)
    check("Rahul (searchable, seeded) appears in Ananya's search results", rahul_result is not None, f"{results}")

    # -- FR030/FR031: compatibility reasons, never a score ----------------------
    s, reasons = call_json(ananya, "GET", f"/discovery/compatibility/{rahul_id}")
    check("FR030 compatibility endpoint succeeds (200)", s == 200 and isinstance(reasons, list), f"{s} {reasons}")
    check(
        "Every reason carries a source tag, never a numeric score field",
        isinstance(reasons, list) and all(set(r.keys()) == {"text", "source"} for r in reasons),
        f"{reasons}",
    )

    # -- Pre-connection: full profile is NOT visible -----------------------------
    s, profile_view = call_json(ananya, "GET", f"/profile/view/{rahul_id}")
    check(
        "Full profile is NOT visible before a connection is accepted (FR021)",
        s == 200 and profile_view is None,
        f"{s} {profile_view}",
    )

    # -- Cleanup: a prior run of this script may have left a pending/accepted
    # connection between these two fixed seeded accounts — decline any
    # pending one so this run starts from a clean slate (repeatable runs,
    # not a real product concern: real users are never the same fixed pair
    # every single time).
    s, rahul_incoming = call_json(rahul, "GET", "/connections/incoming")
    for pending in rahul_incoming if isinstance(rahul_incoming, list) else []:
        if pending["acting_account_id"] == ananya_id:
            call_json(rahul, "POST", f"/connections/{pending['id']}/decline")

    # -- FR042: send a connection request -----------------------------------------
    s, conn = call_json(ananya, "POST", "/connections", {"target_account_id": rahul_id})
    check(
        "FR042 send connection request succeeds (201)",
        s == 201 and conn.get("status") == "pending",
        f"{s} {conn}",
    )
    connection_id = conn.get("id")

    # -- Self-connection is rejected ------------------------------------------------
    s, b = call_json(ananya, "POST", "/connections", {"target_account_id": ananya_id})
    check("Connecting to yourself is rejected (422)", s == 422, f"{s} {b}")

    # -- Duplicate pending request is rejected ---------------------------------------
    s, b = call_json(ananya, "POST", "/connections", {"target_account_id": rahul_id})
    check("Duplicate pending connection request is rejected (409)", s == 409, f"{s} {b}")

    # -- FR043: recipient sees it in their incoming list ------------------------------
    s, incoming = call_json(rahul, "GET", "/connections/incoming")
    check(
        "FR043 recipient sees the request in their incoming list",
        s == 200 and any(c["id"] == connection_id for c in incoming),
        f"{s} {incoming}",
    )

    # -- FR043: full review context is available BEFORE any decision -------------------
    s, review = call_json(rahul, "GET", f"/connections/{connection_id}")
    check("Full connection detail visible before deciding", s == 200 and review is not None, f"{s} {review}")
    s, reasons_for_recipient = call_json(rahul, "GET", f"/discovery/compatibility/{ananya_id}")
    check(
        "Compatibility context is visible to the recipient before deciding (never gated behind acceptance)",
        s == 200,
        f"{s} {reasons_for_recipient}",
    )

    # -- FR049: messaging is blocked before acceptance -----------------------------------
    s, b = call_json(rahul, "POST", f"/messages/{connection_id}", {"content": "Hi!"})
    check("Messaging is blocked before the connection is accepted (403)", s == 403, f"{s} {b}")

    # -- FR043/FR044: accept -----------------------------------------------------------------
    s, b = call_json(rahul, "POST", f"/connections/{connection_id}/accept")
    check("FR043 accept succeeds (204)", s == 204, f"{s} {b}")

    s, b = call_json(rahul, "POST", f"/connections/{connection_id}/accept")
    check("Re-accepting an already-decided connection is rejected (404)", s == 404, f"{s} {b}")

    # -- Post-acceptance: full profile IS now visible, both directions -------------------
    s, ananya_view_of_rahul = call_json(ananya, "GET", f"/profile/view/{rahul_id}")
    check(
        "Ananya can now see Rahul's full profile post-acceptance",
        s == 200 and ananya_view_of_rahul is not None and ananya_view_of_rahul.get("name") == "Rahul Varma",
        f"{s} {ananya_view_of_rahul}",
    )
    s, rahul_view_of_ananya = call_json(rahul, "GET", f"/profile/view/{ananya_id}")
    check(
        "Rahul can now see Ananya's full profile post-acceptance (bidirectional)",
        s == 200 and rahul_view_of_ananya is not None and rahul_view_of_ananya.get("name") == "Ananya Reddy",
        f"{s} {rahul_view_of_ananya}",
    )

    # -- FR049: messaging now works, zero prior contact exchange --------------------------
    s, msg = call_json(ananya, "POST", f"/messages/{connection_id}", {"content": "Hi Rahul, nice to connect!"})
    check("FR049 send message succeeds post-acceptance (201)", s == 201, f"{s} {msg}")

    s, thread = call_json(rahul, "GET", f"/messages/{connection_id}")
    check(
        "Rahul (the other party) can read the message",
        s == 200 and isinstance(thread, list) and any(m["content"] == "Hi Rahul, nice to connect!" for m in thread),
        f"{s} {thread}",
    )

    s, reply = call_json(rahul, "POST", f"/messages/{connection_id}", {"content": "Likewise!"})
    check("Rahul can reply in the same thread (201)", s == 201, f"{s} {reply}")

    s, ananya_convos = call_json(ananya, "GET", "/messages")
    check(
        "The conversation appears in Ananya's conversation list",
        s == 200 and any(c["connection_id"] == connection_id for c in ananya_convos),
        f"{s} {ananya_convos}",
    )

    # -- FR045: no single-active-connection constraint — a second, different target ------
    # Accounts 3 and 4's dev passwords were changed by earlier live
    # password-reset testing (FR094) — use the password each actually has
    # now rather than assuming the original seed value still works.
    third = log_in("+919000000003", "NewSecret!2026")
    s, third_me = call_json(third, "GET", "/auth/me")
    check("prerequisite: third account logs in for the FR045 check", s == 200, f"{s} {third_me}")
    third_id = third_me.get("account_id") if isinstance(third_me, dict) else None

    s, third_incoming = call_json(third, "GET", "/connections/incoming")
    for pending in third_incoming if isinstance(third_incoming, list) else []:
        if pending["acting_account_id"] == ananya_id:
            call_json(third, "POST", f"/connections/{pending['id']}/decline")

    s, conn2 = call_json(ananya, "POST", "/connections", {"target_account_id": third_id})
    check("FR045 a candidate can hold multiple concurrent connections (201)", s == 201, f"{s} {conn2}")

    print(f"\n  {len(passed)} passed, {len(failed)} failed\n")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
