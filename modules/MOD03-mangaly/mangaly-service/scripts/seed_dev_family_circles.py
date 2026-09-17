"""Give each seeded development family a real Home Circle (FR007/FR008).

`seed_dev_families.py` writes the four Hyderabad families straight into the
database but deliberately stops short of Home Circle membership, because a
membership is not just a row: accepting an invitation is what issues the
`family_info` authorization grant that lets a parent act in the candidate's
search. So this script drives the real product flow over HTTP — the candidate
invites, each family member signs in and accepts — and the grant is issued by
the same code a real user would run.

HTTP only, deliberately: no database driver is imported, so the script starts
instantly even on a loaded machine (importing asyncpg/SQLAlchemy costs minutes
here, which made an earlier version look hung).

Idempotent: a family member who is already in the circle is left alone.

Run the Mangaly API and the ForKhatri identity service, and first:
    python -m scripts.seed_dev_families
    python -m scripts.reindex_discovery
    (platform) python scripts/import_module_identities.py
then:
    python -m scripts.seed_dev_family_circles
"""

from __future__ import annotations

import sys
import urllib.error
import urllib.request
from http.cookiejar import CookieJar
from json import dumps, loads
from typing import Any

API = "http://127.0.0.1:8000"
IDENTITY = "http://127.0.0.1:8100"
ENTRANCE_ORIGIN = "http://localhost:3100"
PASSWORD = "MangalyDev123!"

# Each family: the candidate, then the three people who help them.
FAMILIES: list[dict[str, Any]] = [
    {
        "candidate": ("+9110010001", "Meera Sharma"),
        "members": [
            ("+9110010002", "Rajesh Sharma", "parent"),
            ("+9110010003", "Nikhil Sharma", "sibling"),
            ("+9110010004", "Sunita Kapoor", "relative"),
        ],
    },
    {
        "candidate": ("+9110020001", "Arjun Khanna"),
        "members": [
            ("+9110020002", "Kavita Khanna", "parent"),
            ("+9110020003", "Riya Khanna", "sibling"),
            ("+9110020004", "Mohan Khanna", "relative"),
        ],
    },
    {
        "candidate": ("+9110030001", "Ishita Malhotra"),
        "members": [
            ("+9110030002", "Suresh Malhotra", "parent"),
            ("+9110030003", "Aditya Malhotra", "sibling"),
            ("+9110030004", "Neha Sethi", "relative"),
        ],
    },
    {
        "candidate": ("+9110040001", "Rohan Bhatia"),
        "members": [
            ("+9110040002", "Anjali Bhatia", "parent"),
            ("+9110040003", "Tanvi Bhatia", "sibling"),
            ("+9110040004", "Vikas Bhatia", "relative"),
        ],
    },
]


class Client:
    def __init__(self) -> None:
        self._opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(CookieJar()))

    def json(self, method: str, url: str, body: dict | None = None) -> tuple[int, Any]:
        data = dumps(body).encode() if body is not None else None
        request = urllib.request.Request(
            url,
            data=data,
            method=method,
            headers={"Content-Type": "application/json", "Origin": ENTRANCE_ORIGIN},
        )
        try:
            with self._opener.open(request, timeout=30) as response:
                raw = response.read().decode()
                return response.status, (loads(raw) if raw else "")
        except urllib.error.HTTPError as exc:
            raw = exc.read().decode()
            return exc.code, (loads(raw) if raw else "")


def sign_in(phone: str) -> Client | None:
    client = Client()
    status, _ = client.json(
        "POST", f"{IDENTITY}/v1/auth/password", {"identifier": phone, "password": PASSWORD}
    )
    if status != 200:
        return None
    status, _ = client.json("GET", f"{API}/auth/me")
    return client if status == 200 else None


def main() -> int:
    print("\nHome Circles for the seeded development families\n")
    created = 0
    for family in FAMILIES:
        candidate_phone, candidate_name = family["candidate"]
        members: list[tuple[str, str, str]] = family["members"]
        candidate = sign_in(candidate_phone)
        if candidate is None:
            print(f"  SKIP  {candidate_name} cannot sign in — run the platform's import first.")
            continue

        status, existing = candidate.json("GET", f"{API}/home-circle/members")
        already = {m.get("member_name") for m in existing} if status == 200 else set()

        for phone, name, relationship in members:
            if name in already:
                print(f"  ok    {name} is already in {candidate_name}'s circle ({relationship})")
                continue
            status, body = candidate.json(
                "POST",
                f"{API}/home-circle/invite",
                {"invitee_identifier": phone, "relationship_type": relationship},
            )
            if status not in (200, 201, 409):
                print(f"  FAIL  {candidate_name} could not invite {name}: {status} {body}")
                continue

            member = sign_in(phone)
            if member is None:
                print(f"  FAIL  {name} cannot sign in — run the platform's import first.")
                continue
            status, pending = member.json("GET", f"{API}/home-circle/invitations/pending")
            invitation = next(
                (i["id"] for i in pending or [] if i.get("relationship_type") == relationship), None
            )
            if invitation is None:
                print(f"  FAIL  {name} has no pending invitation to accept")
                continue
            status, body = member.json("POST", f"{API}/home-circle/invitations/{invitation}/accept")
            if status not in (200, 201):
                print(f"  FAIL  {name} could not accept: {status} {body}")
                continue
            created += 1
            print(f"  new   {name} joined {candidate_name}'s circle as {relationship}")

    print(f"\n  {created} membership(s) created\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
