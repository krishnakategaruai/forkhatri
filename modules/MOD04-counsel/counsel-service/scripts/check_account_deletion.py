"""Repeatable check of Counsel account deletion (docs/ParentApp/ACCOUNT-DELETION.md).

Counsel has no pytest suite; run this against the dev stack (API :8014, identity :8100, db :5433):
    .venv/Scripts/python scripts/check_account_deletion.py
It builds realistic data for throwaway member #34 (consumer AND expert) with QA members #1 (consumer)
and #2 (expert), erases #34 through the member endpoint, asserts the contract, then removes every
test leftover (QA identity rows stay). Exit code 0 means every assertion held."""

import asyncio, hashlib, struct, subprocess, sys, time, zlib
from pathlib import Path

import asyncpg
import httpx

SVC = Path(__file__).resolve().parents[1]
ROOT = SVC.parents[2]
PY = ROOT / "platform" / "identity-service" / ".venv" / "Scripts" / "python.exe"
DS = ROOT / "platform" / "identity-service" / "scripts" / "dev_session.py"
API = "http://127.0.0.1:8014"
ENV = dict(l.split("=", 1) for l in (SVC / ".env").read_text(encoding="utf-8").splitlines() if "=" in l and not l.startswith("#"))
U = lambda n: f"c2000000-0000-4000-8000-0000000000{n:02d}"
M = U(34)


def sess(n):
    for _ in range(4):
        out = subprocess.run([str(PY), str(DS), U(n), "--cookie-header"], capture_output=True, text=True, cwd=str(ROOT)).stdout
        lines = [l for l in out.splitlines() if l.startswith("Cookie:")]
        if lines:
            return httpx.Client(base_url=API, cookies={"fk_session": lines[0].split("fk_session=")[1].strip()}, timeout=30)
        time.sleep(1)
    raise SystemExit(f"cannot sign in #{n}")


def png():
    def ch(t, d):
        c = struct.pack(">I", len(d)) + t + d
        return c + struct.pack(">I", zlib.crc32(t + d) & 0xFFFFFFFF)
    return b"\x89PNG\r\n\x1a\n" + ch(b"IHDR", struct.pack(">IIBBBBB", 8, 1, 8, 2, 0, 0, 0)) + ch(b"IDAT", zlib.compress(b"\x00\xff\x00\x00" * 8)) + ch(b"IEND", b"")


def ok(r, *codes):
    assert r.status_code in (codes or (200, 201)), (r.request.url, r.status_code, r.text[:300])
    return r.json() if r.headers.get("content-type", "").startswith("application/json") else r


FAILS = []


def check(name, cond, extra=""):
    print(("PASS " if cond else "FAIL ") + name + (f"  {extra}" if extra and not cond else ""))
    if not cond:
        FAILS.append(name)


COLS = {
    "member": ["member_id"], "provider": ["member_id", "reviewed_by"], "booking": ["seeker_id", "provider_id", "cancelled_by"],
    "purchase": ["buyer_id", "provider_id"], "payout": ["provider_id"], "review": ["reviewer_id", "provider_id"], "message": ["sender_id"],
    "note": ["owner_id", "updated_by"], "action_item": ["owner_id", "created_by"], "file": ["owner_id"], "call_feedback": ["member_id"],
    "recording_consent": ["member_id"], "session_event": ["member_id"], "dispute": ["opened_by", "decided_by"], "report": ["reporter_id", "decided_by"],
    "notification": ["member_id"], "delivery": ["member_id"], "block": ["member_id", "blocked_id"], "saved_provider": ["member_id", "provider_id"],
    "time_request": ["seeker_id", "provider_id"], "expertise_request": ["proposed_by", "decided_by"], "provider_evidence": ["provider_id", "reviewed_by"],
    "verification": ["provider_id", "verified_by"], "availability_rule": ["provider_id"], "availability_exception": ["provider_id"],
    "payout_method": ["provider_id"], "provider_expertise": ["provider_id"], "badge_award": ["provider_id"], "search_impression": ["provider_id"],
    "profile_view": ["provider_id"], "service": ["provider_id"], "audit_log": ["actor_id"],
}


async def references(c, mid):
    out = {}
    for t, cols in COLS.items():
        cond = " OR ".join(f"{x}::text=$1" for x in cols)
        if t == "audit_log":
            cond += " OR target_id=$1 OR detail::text LIKE '%'||$1||'%'"
        n = await c.fetchval(f"SELECT count(*) FROM {t} WHERE {cond}", mid)
        if n:
            out[t] = n
    return out


def setup(c34, c1, c2):
    ids = {}
    for name, c, area in (("e34", c34, "career"), ("e2", c2, "technology")):
        ok(c.put("/provide/profile", json={"headline": f"Deletion check {name}", "intro": "Throwaway expert.", "city": "Hyderabad", "expertise": [{"id": area, "years": 5, "primary": True}]}))
        ok(c.post("/provide/photo", files={"file": ("p.png", png(), "image/png")}))
        ev = ok(c.post("/provide/evidence", json={"kind": "qualification", "title": "MBA test", "issuer": "Test Univ", "year_from": 2015, "year_to": 2017}))
        ok(c.post(f"/provide/evidence/{ev['id']}/document", files={"file": ("cert.pdf", b"%PDF-1.4\n%test\n", "application/pdf")}))
        ok(c.put("/provide/availability/rules", json=[{"weekday": d, "start_time": "09:00", "end_time": "18:00", "kind": "window"} for d in range(7)]))
        ok(c.put("/provide/payout-method", json={"kind": "upi", "holder_name": "Delete Test", "upi_id": f"deltest{name}@okbank"}))
        ids["svc_" + name] = ok(c.post("/provide/services", json={"title": f"Test consult {name}", "description": "A test", "outcomes": ["a plan"], "area_id": area, "duration_min": 30,
                                                                 "price_minor": 50000, "min_notice_hours": 0, "recording_allowed": True, "allow_custom_time": True}))["id"]
        ok(c.post("/provide/expertise-requests", json={"name": "Test niche " + name, "note": "please add"}), 200, 201)
        ok(c.post("/provide/submit"), 200, 201, 409, 422)
    return ids


async def cleanup(c, pre_receipts, root):
    # Remove everything this check created (QA identity rows stay).
    for n in (1, 2, 34):
        httpx.post(f"{API}/internal/v1/members/{U(n)}/erase", headers={"X-ForKhatri-Service": "identity", "X-ForKhatri-Service-Key": ENV["PLATFORM_SERVICE_KEY"]})
    import uuid
    # Only the stand-in ids of the three throwaway members; never any other erased member.
    tombs = [uuid.UUID(bytes=hashlib.sha256(f"counsel-erased:{U(n)}:{ENV['PLATFORM_SERVICE_KEY']}".encode()).digest()[:16], version=4) for n in (1, 2, 34)]
    ts = [str(x) for x in tombs]
    keys = [r[0] for r in await c.fetch("SELECT storage_key FROM file WHERE booking_id IN (SELECT id FROM booking WHERE seeker_id=ANY($1) OR provider_id=ANY($1))", tombs)]
    await c.execute("DELETE FROM booking WHERE seeker_id=ANY($1) OR provider_id=ANY($1)", tombs)
    await c.execute("DELETE FROM purchase WHERE buyer_id=ANY($1) OR provider_id=ANY($1)", tombs)
    await c.execute("DELETE FROM service WHERE provider_id=ANY($1)", tombs)
    await c.execute("DELETE FROM payout WHERE provider_id=ANY($1)", tombs)
    await c.execute("DELETE FROM provider WHERE member_id=ANY($1)", tombs)
    await c.execute("DELETE FROM report WHERE reporter_id=ANY($1) OR target_id=ANY($2)", tombs, ts)
    await c.execute("DELETE FROM audit_log WHERE actor_id=ANY($1) OR target_id=ANY($2)", tombs, ts)
    await c.execute("DELETE FROM member WHERE member_id=ANY($1)", tombs)
    await c.execute("DELETE FROM erased_member WHERE member_id=ANY($1)", tombs)
    for k in keys:
        (root / k).unlink(missing_ok=True)


async def main():
    c = await asyncpg.connect(host=ENV["DB_HOST"], port=int(ENV["DB_PORT"]), user=ENV["DB_OWNER_USER"], password=ENV["DB_OWNER_PASSWORD"], database=ENV["DB_NAME"], server_settings={"search_path": "counsel"})
    pre_receipts = {r[0] for r in await c.fetch("SELECT member_id FROM erased_member")}
    root = SVC / ENV.get("STORAGE_ROOT", ".local-files")
    if "--cleanup-only" in sys.argv:  # remove leftovers of an earlier interrupted run
        await cleanup(c, set(), root)
        return
    c34, c1, c2 = sess(34), sess(1), sess(2)
    ids = setup(c34, c1, c2)
    await c.execute("UPDATE provider SET status='approved' WHERE member_id::text = ANY($1)", [M, U(2)])  # staff approval is out of scope here
    slots = lambda sid: ok(httpx.get(f"{API}/services/{sid}/slots", params={"days": 10}))["slots"]

    def book(cl, sid, idx, brief):
        b = ok(cl.post("/bookings", json={"service_id": sid, "starts_at": slots(sid)[idx], "brief": brief}))
        ok(cl.post(f"/bookings/{b['id']}/pay", json={"proof": {}}))
        return b["id"]

    chat = lambda cl, bid, text: ok(cl.post(f"/bookings/{bid}/messages", json={"body": text}))
    B1 = book(c1, ids["svc_e34"], 0, "Ananya asks 34")
    chat(c1, B1, "Hello from Ananya"); chat(c34, B1, "Hello from 34 the expert")
    ok(c34.post(f"/bookings/{B1}/files", files={"file": ("plan34.txt", b"secret plan of 34", "text/plain")}))
    ok(c1.post(f"/bookings/{B1}/files", files={"file": ("cv-ananya.txt", b"ananya cv", "text/plain")}))
    ok(c34.put(f"/bookings/{B1}/note", json={"body": "private note 34", "version": 0, "private": True}))
    ok(c34.post(f"/bookings/{B1}/actions", json={"text": "34 action", "owner_id": U(1)}), 200, 201, 422)
    ok(c34.post(f"/bookings/{B1}/recording-consent", json={}), 200, 201, 409, 422)
    ok(c34.post(f"/bookings/{B1}/call-feedback", json={"good": True, "issues": []}), 200, 201, 409, 422)
    ok(c34.post(f"/bookings/{B1}/complete", json={}))
    ok(c1.post(f"/bookings/{B1}/review", json={"overall": 5, "expertise": 5, "communication": 5, "professionalism": 5, "punctuality": 5, "body": "Great expert 34"}))
    B2 = book(c1, ids["svc_e34"], 3, "Ananya future session with 34")
    B3 = book(c34, ids["svc_e2"], 0, "34 asks Rohan")
    chat(c34, B3, "Hi Rohan from 34"); chat(c2, B3, "Hi, Rohan here")
    ok(c34.post(f"/bookings/{B3}/files", files={"file": ("cv34.txt", b"34 cv", "text/plain")}))
    ok(c2.post(f"/bookings/{B3}/files", files={"file": ("rohan-notes.txt", b"rohan notes", "text/plain")}))
    ok(c34.put(f"/bookings/{B3}/note", json={"body": "34 private note", "version": 0, "private": True}))
    ok(c2.post(f"/bookings/{B3}/complete", json={}))
    ok(c34.post(f"/bookings/{B3}/review", json={"overall": 4, "expertise": 4, "communication": 4, "professionalism": 4, "punctuality": 4, "body": "34 wrote about Rohan"}))
    ok(c34.post(f"/bookings/{B3}/dispute", json={"reason": "34 dispute text"}), 200, 201)
    B4 = book(c34, ids["svc_e2"], 3, "34 future with Rohan")
    pk = ok(c34.post(f"/provide/services/{ids['svc_e34']}/packages", json={"sessions": 2, "price_minor": 90000}))
    pu = ok(c1.post(f"/packages/{pk['id']}/buy", json={})); ok(c1.post(f"/purchases/{pu['id']}/pay", json={"proof": {}}))
    ok(c2.put(f"/provide/services/{ids['svc_e2']}/offers", json={"question_price_minor": 20000, "question_answer_days": 3}), 200, 201, 422)
    q = ok(c34.post(f"/services/{ids['svc_e2']}/questions", json={"body": "34 asks a written question to Rohan"})); ok(c34.post(f"/purchases/{q['id']}/pay", json={"proof": {}}))
    ok(c34.post(f"/services/{ids['svc_e2']}/time-requests", json={"starts_at": slots(ids['svc_e2'])[8], "brief": "34 custom time", "note": "n"}), 200, 201, 409, 422)
    ok(c34.put(f"/me/saved/{U(2)}")); ok(c2.put(f"/me/saved/{M}")); ok(c34.post(f"/me/blocks/{U(1)}"))
    ok(c34.post("/reports", json={"target_kind": "member", "target_id": U(1), "reason": "spam", "detail": "34 report text"}))
    ok(c1.post("/reports", json={"target_kind": "member", "target_id": M, "reason": "rude", "detail": "ananya reports 34"}))

    before = await references(c, M)
    files_before = [r[0] for r in await c.fetch("SELECT storage_key FROM file WHERE owner_id::text=$1", M)] + [r[0] for r in await c.fetch("SELECT document_url FROM provider_evidence WHERE provider_id::text=$1", M)]
    others_before = {"ananya_file": await c.fetchval("SELECT count(*) FROM file WHERE owner_id::text=$1", U(1)), "rohan_file": await c.fetchval("SELECT count(*) FROM file WHERE owner_id::text=$1", U(2)),
                     "ananya_msg": await c.fetchval("SELECT count(*) FROM message WHERE sender_id::text=$1", U(1)), "rohan_msg": await c.fetchval("SELECT count(*) FROM message WHERE sender_id::text=$1", U(2)),
                     "rohan_provider": await c.fetchval("SELECT count(*) FROM provider WHERE member_id::text=$1", U(2))}
    print("rows before:", before)
    check("test data covers 25+ stores", len(before) >= 25, str(len(before)))
    check("old paths: warning list", ok(c34.get("/me/deletion-check"))["blockers"] != [])

    r = c34.post("/me/delete-account-data", json={"confirm": "nope"})
    check("wrong confirm word refused", r.status_code == 422)
    res = ok(c34.post("/me/delete-account-data", json={"confirm": "DELETE"}))
    print("erase response:", res)
    check("status done + contract shape", res["status"] == "done" and res["module"] == "counsel" and "deleted" in res and "retained" in res and res["files_removed"] >= 4)

    after = await references(c, M)
    check("zero rows reference the real member id", after == {}, str(after))
    check("no files of #34 on disk", not any((root / k).exists() for k in files_before) and not [p for p in root.rglob("*") if p.is_file() and M in str(p)])
    t = hashlib.sha256(f"counsel-erased:{M}:{ENV['PLATFORM_SERVICE_KEY']}".encode()).digest()[:16]
    import uuid
    tomb = str(uuid.UUID(bytes=t, version=4))
    check("tombstone shown as Deleted member", await c.fetchval("SELECT display_name FROM member WHERE member_id::text=$1", tomb) == "Deleted member")
    check("others intact (files, messages, expert profile)", others_before == {
        "ananya_file": await c.fetchval("SELECT count(*) FROM file WHERE owner_id::text=$1", U(1)), "rohan_file": await c.fetchval("SELECT count(*) FROM file WHERE owner_id::text=$1", U(2)),
        "ananya_msg": await c.fetchval("SELECT count(*) FROM message WHERE sender_id::text=$1", U(1)), "rohan_msg": await c.fetchval("SELECT count(*) FROM message WHERE sender_id::text=$1", U(2)),
        "rohan_provider": await c.fetchval("SELECT count(*) FROM provider WHERE member_id::text=$1", U(2))})
    st = {r["id"]: r["status"] for r in await c.fetch("SELECT id::text id, status FROM booking WHERE id::text = ANY($1)", [B1, B2, B3, B4])}
    check("completed consultations kept, future ones cancelled", st[B1] == "completed" and st[B3] == "completed" and st[B2] == "cancelled_by_provider" and st[B4] == "cancelled_by_seeker", str(st))
    check("consumer refund row for cancelled expert booking", await c.fetchval("SELECT refund_minor FROM booking WHERE id::text=$1", B2) == 50000)
    check("other parties notified", await c.fetchval("SELECT count(*) FROM notification WHERE kind LIKE '%_deleted' AND member_id::text IN ($1,$2)", U(1), U(2)) >= 4)
    check("brief of deleted consumer blanked, other party's brief kept", await c.fetchval("SELECT brief FROM booking WHERE id::text=$1", B3) == "" and await c.fetchval("SELECT brief FROM booking WHERE id::text=$1", B1) != "")
    check("payments retained only under tombstone", await c.fetchval("SELECT count(*) FROM payment WHERE booking_id IN (SELECT id FROM booking WHERE seeker_id::text=$1 OR provider_id::text=$1)", tomb) >= 3)
    again = httpx.post(f"{API}/internal/v1/members/{M}/erase", headers={"X-ForKhatri-Service": "identity", "X-ForKhatri-Service-Key": ENV["PLATFORM_SERVICE_KEY"]}).json()
    check("second erase is safe (nothing_to_delete)", again["status"] == "nothing_to_delete", str(again))
    check("internal erase refuses missing key", httpx.post(f"{API}/internal/v1/members/{M}/erase").status_code in (401, 422))
    me = ok(c34.get("/me"))
    check("old session re-enters as a brand-new empty member", me["provider_status"] is None and me["upcoming"] == 0)

    await cleanup(c, pre_receipts, root)
    await c.close()
    print("FAILED: " + ", ".join(FAILS) if FAILS else "ALL CHECKS PASSED")
    sys.exit(1 if FAILS else 0)


asyncio.run(main())
