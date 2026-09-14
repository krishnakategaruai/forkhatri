"""End-to-end check of the Home Circle cluster (FR007/008/009/010/014/016)
against a RUNNING server, using two real seeded dev accounts (password login,
never the OTP flow — see `seed_dev_accounts.py`'s own docstring for why).

Run the API first, then: python -m scripts.check_home_circle
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
CANDIDATE_IDENTIFIER = "+919000000001"  # Ananya Reddy (seeded)
INVITEE_IDENTIFIER = "+919000000002"  # Rahul Varma (seeded)

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


def log_in(identifier: str) -> urllib.request.OpenerDirector:
    opener = new_session()
    call_json(opener, "POST", "/auth/login", {"identifier": identifier, "credential": DEV_PASSWORD})
    return opener


def main() -> int:
    print("\nMangaly Home Circle — live checks (FR007/FR008/FR009/FR010/FR014/FR016)\n")

    try:
        with urllib.request.urlopen(f"{BASE}/health", timeout=5) as res:
            if res.status != 200:
                raise RuntimeError
    except Exception:
        print(f"  API not reachable at {BASE}. Start it first.")
        return 2

    candidate = log_in(CANDIDATE_IDENTIFIER)
    invitee = log_in(INVITEE_IDENTIFIER)

    s, b = call_json(candidate, "GET", "/auth/me")
    check("prerequisite: candidate password login works", s == 200, f"{s} {b}")
    candidate_account_id = b.get("account_id") if isinstance(b, dict) else None
    s, b = call_json(invitee, "GET", "/auth/me")
    check("prerequisite: invitee password login works", s == 200, f"{s} {b}")

    # -- FR007: invite --------------------------------------------------------
    s, b = call_json(
        candidate,
        "POST",
        "/home-circle/invite",
        {"invitee_identifier": INVITEE_IDENTIFIER, "relationship_type": "sibling"},
    )
    check("FR007 invite creates a pending invitation (201)", s == 201 and "invitation_id" in b, f"{s} {b}")
    invitation_id = b.get("invitation_id") if isinstance(b, dict) else None

    # -- FR007 failure outcome: self-invite ------------------------------------
    s, b = call_json(
        candidate,
        "POST",
        "/home-circle/invite",
        {"invitee_identifier": CANDIDATE_IDENTIFIER, "relationship_type": "relative"},
    )
    check("Inviting yourself is rejected (422)", s == 422, f"{s} {b}")

    # -- Duplicate pending invite -----------------------------------------------
    s, b = call_json(
        candidate,
        "POST",
        "/home-circle/invite",
        {"invitee_identifier": INVITEE_IDENTIFIER, "relationship_type": "sibling"},
    )
    check("Duplicate pending invite for same identifier is rejected (409)", s == 409, f"{s} {b}")

    # -- FR008: the invitee sees it in their own pending list ------------------
    s, b = call_json(invitee, "GET", "/home-circle/invitations/pending")
    check(
        "FR008 invitee's own pending-invitations list contains it",
        s == 200 and isinstance(b, list) and any(i["id"] == invitation_id for i in b),
        f"{s} {b}",
    )
    check(
        "Pending invitation carries the relationship claim (FR008 acceptance criterion)",
        isinstance(b, list) and any(i["id"] == invitation_id and i["relationship_type"] == "sibling" for i in b),
        f"{b}",
    )

    # -- A third, uninvolved account sees nothing pending ----------------------
    third = log_in("+919000000003")
    s, b = call_json(third, "GET", "/home-circle/invitations/pending")
    check("An uninvolved account's pending list is empty", s == 200 and b == [], f"{s} {b}")

    # -- FR008: accept ----------------------------------------------------------
    s, b = call_json(invitee, "POST", f"/home-circle/invitations/{invitation_id}/accept")
    check("FR008 accept creates a membership (201)", s == 201 and "membership_id" in b, f"{s} {b}")
    membership_id = b.get("membership_id") if isinstance(b, dict) else None

    # -- Accepting again fails (already responded) ------------------------------
    s, b = call_json(invitee, "POST", f"/home-circle/invitations/{invitation_id}/accept")
    check("Re-accepting an already-accepted invitation is rejected (404)", s == 404, f"{s} {b}")

    # -- The candidate now sees the member ---------------------------------------
    s, b = call_json(candidate, "GET", "/home-circle/members")
    check(
        "Candidate's member list shows the new member with the right relationship",
        s == 200
        and isinstance(b, list)
        and any(m["membership_id"] == membership_id and m["relationship_type"] == "sibling" for m in b),
        f"{s} {b}",
    )

    # -- FR009: decline path (separate invitation) -------------------------------
    s, b = call_json(
        candidate,
        "POST",
        "/home-circle/invite",
        {"invitee_identifier": "+919000000004", "relationship_type": "relative"},
    )
    decline_invitation_id = b.get("invitation_id") if isinstance(b, dict) else None
    fourth = log_in("+919000000004")
    s, b = call_json(fourth, "POST", f"/home-circle/invitations/{decline_invitation_id}/decline")
    check("FR009 decline succeeds (204)", s == 204, f"{s} {b}")
    s, b = call_json(candidate, "GET", "/home-circle/members")
    check(
        "A declined invitation never becomes a membership",
        s == 200 and isinstance(b, list) and all(m["membership_id"] != decline_invitation_id for m in b),
        f"{b}",
    )

    # -- FR014: suggest -----------------------------------------------------------
    s, b = call_json(
        invitee,
        "POST",
        "/home-circle/suggest",
        {
            "membership_id": membership_id,
            "suggested_profile_id": "11111111-1111-1111-1111-111111111111",
            "note": "Seems like a good match!",
        },
    )
    check("FR014 suggest succeeds for an active member (201)", s == 201 and "suggestion_id" in b, f"{s} {b}")

    # -- FR016: private note, family-only by default -----------------------------
    s, b = call_json(
        invitee, "POST", "/home-circle/notes", {"membership_id": membership_id, "content": "Private family note."}
    )
    check("FR016 write_note succeeds (201)", s == 201 and "note_id" in b, f"{s} {b}")
    note_id = b.get("note_id") if isinstance(b, dict) else None

    s, b = call_json(invitee, "GET", f"/home-circle/notes?candidate_account_id={candidate_account_id}")
    check(
        "The author (family member) can see their own note immediately",
        s == 200 and isinstance(b, list) and any(n["id"] == note_id for n in b),
        f"{s} {b}",
    )

    s, b = call_json(candidate, "GET", "/home-circle/notes")
    check(
        "The candidate CANNOT see the note before it is forwarded (family-only by default)",
        s == 200 and isinstance(b, list) and not any(n["id"] == note_id for n in b),
        f"{s} {b}",
    )

    s, b = call_json(candidate, "GET", "/home-circle/notes/pending")
    check(
        "The candidate CAN see that a note is pending (id only, blind)",
        s == 200 and isinstance(b, list) and any(n["id"] == note_id for n in b),
        f"{s} {b}",
    )

    s, b = call_json(candidate, "POST", f"/home-circle/notes/{note_id}/forward")
    check("The candidate approves forwarding (204)", s == 204, f"{s} {b}")

    s, b = call_json(candidate, "GET", "/home-circle/notes")
    check(
        "After approval, the candidate now sees the note's content",
        s == 200
        and isinstance(b, list)
        and any(n["id"] == note_id and n["content"] == "Private family note." for n in b),
        f"{s} {b}",
    )

    # -- FR010: candidate removes the member --------------------------------------
    s, b = call_json(candidate, "DELETE", f"/home-circle/members/{membership_id}")
    check("FR010 candidate removes a member (204)", s == 204, f"{s} {b}")
    s, b = call_json(candidate, "GET", "/home-circle/members")
    check(
        "Removed member no longer appears in the active list",
        s == 200 and isinstance(b, list) and not any(m["membership_id"] == membership_id for m in b),
        f"{s} {b}",
    )

    # -- FR010: voluntary leave (separate membership) -----------------------------
    s, b = call_json(
        candidate, "POST", "/home-circle/invite", {"invitee_identifier": "+919000000003", "relationship_type": "relative"}
    )
    leave_invitation_id = b.get("invitation_id") if isinstance(b, dict) else None
    s, b = call_json(third, "POST", f"/home-circle/invitations/{leave_invitation_id}/accept")
    leave_membership_id = b.get("membership_id") if isinstance(b, dict) else None
    s, b = call_json(third, "POST", f"/home-circle/members/{leave_membership_id}/leave")
    check("FR010 member leaves voluntarily, no approval required (204)", s == 204, f"{s} {b}")

    print(f"\n  {len(passed)} passed, {len(failed)} failed\n")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
