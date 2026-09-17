"""Live checks for FR016/TR016 private family notes (TS035–TS037) against RUNNING services.

Real product flow with real people: Lakshmi Reddy (Ananya's mother, in
Ananya's Home Circle) keeps private notes about a match (Karthik Iyer).
Ananya cannot read them and Rahul (not in the circle) cannot either. Lakshmi
asks Ananya to read one note; Ananya sees who asks and which match but not
the words, chooses to read it, and only that note is shared. A second note is
declined, cannot be re-asked unchanged, and becomes private again when edited.
Every note the check writes is deleted at the end.

Needs the seeded development data and the Mangaly API and ForKhatri identity
service:
    python -m scripts.check_family_notes
"""

import asyncio
import sys

import asyncpg

from scripts._check_support import API, IDENTITY, OWNER_DSN, Client, Results

ANANYA_ID = "2232df40-b6c9-45ef-bb49-6054c00464b5"
KARTHIK_ID = "f81b27d0-9010-4996-990c-8efddd086cfd"
LAKSHMI_MEMBERSHIP = "5142f848-523c-45a5-9703-dd55b67130a1"

NOTE_A = "Karthik's family is from Chennai too. His profile says he is open to relocating."
NOTE_B = "Ask about his work hours before we speak to his parents."


def sign_in(phone: str, password: str) -> Client:
    client = Client()
    status, body = client.json(
        "POST", f"{IDENTITY}/v1/auth/password", {"identifier": phone, "password": password}
    )
    if status != 200:
        raise RuntimeError(f"sign-in failed for {phone}: {status} {body}")
    return client


async def note_count() -> int:
    conn = await asyncpg.connect(OWNER_DSN)
    try:
        return await conn.fetchval(
            "SELECT count(*) FROM mangaly_home_circle.home_circle_note "
            "WHERE author_membership_id = $1",
            LAKSHMI_MEMBERSHIP,
        )
    finally:
        await conn.close()


def main() -> int:
    results = Results()
    if asyncio.run(note_count()) != 0:
        print("  Lakshmi already has notes this check did not write; nothing changed.")
        return 2

    ananya = sign_in("+919000000001", "MangalyDev123!")
    rahul = sign_in("+919000000002", "MangalyDev123!")
    lakshmi = sign_in("+919999900003", "ForKhatri-dev-2026")
    notes = f"{API}/home-circle/notes"
    mine = f"{notes}?membership_id={LAKSHMI_MEMBERSHIP}&subject_account_id={KARTHIK_ID}"
    created: list[str] = []

    def add(content: str, subject: str = KARTHIK_ID) -> tuple[int, dict]:
        s, b = lakshmi.json(
            "POST",
            notes,
            {
                "membership_id": LAKSHMI_MEMBERSHIP,
                "subject_account_id": subject,
                "content": content,
            },
        )
        if s == 201:
            created.append(b["id"])
        return s, b

    try:
        s, _ = add("   ")
        results.check("A blank note is rejected (422)", s == 422, s)
        s, _ = add("A note about Ananya herself", subject=ANANYA_ID)
        results.check("A note cannot be about the candidate (422)", s == 422, s)

        s, a = add(NOTE_A)
        results.check(
            "Lakshmi saves a private note (201)", s == 201 and a.get("status") == "private", s
        )
        s, b = add(NOTE_B)
        results.check("Lakshmi saves a second note (201)", s == 201, s)
        note_a, note_b = a["id"], b["id"]

        s, listed = lakshmi.json("GET", mine)
        results.check("Lakshmi sees both her notes about Karthik", s == 200 and len(listed) == 2, s)

        s, _ = ananya.json("GET", mine)
        results.check("Ananya cannot list Lakshmi's notes (TS035)", s == 404, s)
        s, _ = rahul.json("GET", mine)
        results.check("Rahul, outside the circle, cannot list them", s == 404, s)
        s, requests = ananya.json("GET", f"{notes}/requests")
        results.check("Ananya has no read requests yet", s == 200 and requests == [], requests)

        s, asked = lakshmi.json("POST", f"{notes}/{note_a}/request")
        results.check(
            "Lakshmi asks Ananya to read one note", s == 200 and asked["status"] == "requested", s
        )
        s, _ = lakshmi.json("POST", f"{notes}/{note_a}/request")
        results.check("The same note cannot be asked twice (404)", s == 404, s)

        s, requests = ananya.json("GET", f"{notes}/requests")
        request = requests[0] if s == 200 and len(requests) == 1 else {}
        results.check(
            "Ananya sees who asks and which match, not the words",
            request.get("author_name") == "Lakshmi Reddy"
            and request.get("relationship_type") == "parent"
            and request.get("subject_account_id") == KARTHIK_ID
            and "content" not in request,
            request,
        )

        s, _ = rahul.json("POST", f"{notes}/{note_a}/read")
        results.check("Rahul cannot read the note (404)", s == 404, s)
        s, read = ananya.json("POST", f"{notes}/{note_a}/read")
        results.check(
            "Ananya reads it and gets exactly the words",
            s == 200 and read.get("content") == NOTE_A,
            s,
        )

        s, shared = ananya.json("GET", f"{notes}/shared")
        results.check(
            "Only that note is shared with Ananya (TS036)",
            s == 200 and [n["id"] for n in shared] == [note_a],
            [n["id"] for n in shared] if s == 200 else s,
        )
        s, _ = lakshmi.json("PATCH", f"{notes}/{note_a}", {"content": "Changed after reading"})
        results.check("A shared note cannot be rewritten (404)", s == 404, s)

        lakshmi.json("POST", f"{notes}/{note_b}/request")
        s, _ = ananya.json("POST", f"{notes}/{note_b}/decline")
        results.check("Ananya says not now to the second note (204)", s == 204, s)
        s, listed = lakshmi.json("GET", mine)
        statuses = {n["id"]: n["status"] for n in listed} if s == 200 else {}
        results.check(
            "Lakshmi sees one read and one not now, with no reason",
            statuses == {note_a: "shared", note_b: "declined"},
            statuses,
        )
        s, _ = lakshmi.json("POST", f"{notes}/{note_b}/request")
        results.check("A declined note cannot be re-asked unchanged (404)", s == 404, s)
        s, edited = lakshmi.json(
            "PATCH", f"{notes}/{note_b}", {"content": NOTE_B + " Evenings only."}
        )
        results.check(
            "Editing it makes it private again",
            s == 200 and edited.get("status") == "private",
            s,
        )
        s, shared = ananya.json("GET", f"{notes}/shared")
        results.check(
            "The declined note never reached Ananya",
            s == 200 and [n["id"] for n in shared] == [note_a],
        )
    finally:
        for note_id in created:
            lakshmi.json("DELETE", f"{notes}/{note_id}")
        remaining = asyncio.run(note_count())
        results.check("cleanup: every note this check wrote is deleted", remaining == 0, remaining)
    return results.finish()


if __name__ == "__main__":
    sys.exit(main())
