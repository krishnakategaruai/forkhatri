"""Live check of the voice interview (nextInterviewQuestion / interpretInterviewAnswer)
against a RUNNING API, over real HTTP and the real development database.

Run a private copy of the API with the rules engine, then point this script at it:

    AI_PROVIDER=rules .venv/Scripts/python -m uvicorn app.main:app --port <free port>
    VYAPAR_CHECK_API=http://127.0.0.1:<port> .venv/Scripts/python -m scripts.check_voice_interview

What it proves:
  * all four flows (post_job, post_local, post_project, profile) run end to end
    in English, Hindi and Telugu with realistic spoken transcripts: one question
    at a time in the request language, each answer read into a typed value with
    a read-back, confirmed with a spoken yes ("haan", "avunu"), until done;
  * only what is missing is asked: facts stated in the first answer ("2 delivery
    boys in Kukatpally, salary 15 to 18 thousand") are not asked again, the saved
    locality is offered as a yes/no, a remote project never asks the area, and a
    profile never asks what the member's profile already has;
  * control words (skip / chhodo / vaddu, yes / haan / avunu, no / nahi / kaadu,
    repeat / phir se / malli cheppandi), a required field that is skipped (asked
    again, last), an unclear answer and the scam shield all answer as documented;
  * every finished post draft is accepted by the real createOpportunity endpoint
    and meets the publish gates (salary range, project budget, local pay basis);
    every profile draft is accepted by PATCH /v1/me/profile (own_assets included);
  * the two operations are in the OpenAPI document and need only the `read` scope.

It uses seed personas (never the product owner's account). On exit it deletes
the opportunities it created, the profile it created for m_new and restores
m_new's member row, so the development database is left as it was.
"""

from __future__ import annotations

import asyncio
import json
import os
import sys
import urllib.error
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Callable

import asyncpg

SERVICE_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SERVICE_DIR))

from app.config import get_settings  # noqa: E402
from app.integrations.identity.scopes import required_scopes  # noqa: E402
from scripts.check_ai import owner_dsn  # noqa: E402

API = os.environ.get("VYAPAR_CHECK_API") or f"http://127.0.0.1:{get_settings().api_port}"

# Seed personas: each has a profile (needed to post) and a saved locality.
POSTER = {"en": "m_meena", "hi": "m_rahul", "te": "m_seed_ramesh"}   # Himayatnagar, Kukatpally, Kukatpally
NEW_MEMBER = "m_new"                                                # no profile, no locality
YES = {"en": "yes", "hi": "haan", "te": "avunu"}
TODAY = (datetime.now(timezone.utc) + timedelta(hours=5, minutes=30)).date()

passed: list[str] = []
failed: list[str] = []
created_opportunities: list[str] = []


def call(method: str, path: str, member: str, body: dict[str, Any] | None = None, lang: str = "en") -> tuple[int, Any]:
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(f"{API}{path}", data=data, method=method)
    req.add_header("X-Dev-Member-Id", member)
    req.add_header("X-Vyapar-Language", lang)
    if data:
        req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req, timeout=60) as res:
            return res.status, json.loads(res.read() or b"null")
    except urllib.error.HTTPError as e:
        raw = e.read()
        try:
            return e.code, json.loads(raw)
        except ValueError:
            return e.code, raw.decode(errors="replace")


def check(name: str, ok: bool, detail: Any = "") -> None:
    (passed if ok else failed).append(name)
    print(("PASS  " if ok else "FAIL  ") + name + ("" if ok else f"\n      {json.dumps(detail, ensure_ascii=False, default=str)[:900]}"))


def in_script(text: str | None, lang: str) -> bool:
    if not text:
        return False
    if lang == "hi":
        return any(0x0900 <= ord(c) <= 0x097F for c in text)
    if lang == "te":
        return any(0x0C00 <= ord(c) <= 0x0C7F for c in text)
    return all(ord(c) < 0x0900 for c in text)


# The other Indic script must never appear in a Hindi or Telugu string
# (Latin is fine: locality names, ₹, "ITI").
FOREIGN = {"hi": (0x0C00, 0x0C7F), "te": (0x0900, 0x097F)}
mixed_seen: list[tuple[str, str]] = []


def foreign(text: Any, lang: str) -> bool:
    lo, hi = FOREIGN.get(lang, (1, 0))
    return isinstance(text, str) and any(lo <= ord(ch) <= hi for ch in text)


def scan(lang: str, payload: Any, where: str) -> None:
    """Record every string in a response that mixes in the other script."""
    if isinstance(payload, dict):
        for k, v in payload.items():
            scan(lang, v, f"{where}.{k}")
    elif isinstance(payload, list):
        for i, v in enumerate(payload):
            scan(lang, v, f"{where}[{i}]")
    elif foreign(payload, lang):
        mixed_seen.append((where, payload))


def check_catalog_scripts() -> None:
    def walk(d: Any, path: str = ""):
        if isinstance(d, dict):
            for k, v in d.items():
                yield from walk(v, f"{path}.{k}" if path else k)
        else:
            yield path, d
    for lang in ("hi", "te"):
        catalog = json.loads((SERVICE_DIR / "app" / "i18n" / "locales" / lang / "voice.json").read_text(encoding="utf-8"))
        bad = [(k, v) for k, v in walk(catalog) if foreign(v, lang)]
        check(f"script/{lang}: voice.json has no letters from the other Indic script", not bad, bad)


def nxt(member: str, flow: str, lang: str, answers: dict, skipped: list[str] | None = None) -> dict:
    s, d = call("POST", "/v1/voice/interview/next", member, {"flow": flow, "language": lang, "answers": answers, "skipped": skipped or []}, lang)
    assert s == 200, (s, d)
    scan(lang, d, f"next/{flow}")
    return d


def interpret(member: str, flow: str, field: str, lang: str, text: str, answers: dict | None = None) -> dict:
    s, d = call("POST", "/v1/voice/interview/interpret", member,
                {"flow": flow, "field": field, "language": lang, "text": text, "answers": answers or {}}, lang)
    assert s == 200, (s, d)
    scan(lang, {k: v for k, v in d.items() if k in ("readback", "reprompt")}, f"interpret/{flow}.{field}")
    return d


# ---- one spoken interview ----------------------------------------------------------

def run_interview(label: str, member: str, flow: str, lang: str, said: dict[str, str],
                  expect_asked: list[str], checks: dict[str, Callable[[Any], bool]]) -> dict:
    """Plays the conversation the way the web client does: ask, hear, read back,
    hear "yes", merge (including what the first answer also stated), next."""
    answers: dict[str, Any] = {}
    skipped: list[str] = []
    asked: list[str] = []
    step = None
    for _ in range(15):
        step = nxt(member, flow, lang, answers, skipped)
        if step["done"]:
            break
        field = step["field"]
        asked.append(field)
        check(f"{label}: '{field}' asked in {lang} ({step['progress']['asked']}/{step['progress']['total']})",
              in_script(step["question"], lang) and step["kind"] in ("text", "choice", "number", "yesno"), step)
        text = said[field]
        heard = interpret(member, flow, field, lang, text, answers)
        if heard["intent"] == "skip":
            check(f"{label}: '{text}' skips {field}", step["optional"] and heard["reprompt"] is None, heard)
            skipped.append(field)
            continue
        ok = heard["understood"] and (field not in checks or checks[field](heard["value"]))
        check(f"{label}: '{text}' -> {field}", ok, heard)
        if not heard["understood"]:
            skipped.append(field)
            continue
        if heard["needs_confirmation"]:
            check(f"{label}: read-back for {field} is in {lang}", in_script(heard["readback"], lang) or lang == "en", heard["readback"])
            confirm = interpret(member, flow, field, lang, YES[lang], answers)
            check(f"{label}: '{YES[lang]}' confirms the read-back", confirm["intent"] == "yes", confirm)
        answers[field] = heard["value"]
        answers.update(heard.get("also") or {})
    check(f"{label}: finished", bool(step and step["done"]), step)
    check(f"{label}: asked only {expect_asked}", asked == expect_asked, asked)
    return step or {}


def structured_for(draft: dict) -> dict:
    """draft -> createOpportunity.structured, as the web composer maps it."""
    t = draft["type"]
    if t == "employment":
        e = draft["employment"]
        return {k: e[k] for k in ("salary_min_paise", "salary_max_paise", "incentive_type", "openings", "shift", "job_timings",
                                  "min_qualification", "experience_min_months", "experience_max_months", "requires_assets")}
    if t == "freelance":
        f = draft["freelance"]
        return {k: f[k] for k in ("budget_type", "budget_min_paise", "budget_max_paise", "hourly_rate_min_paise", "hourly_rate_max_paise", "duration")}
    ls = draft["local_service"]
    return {k: ls[k] for k in ("preferred_date", "budget_paise", "urgency")}


def create_from(label: str, member: str, lang: str, draft: dict) -> dict | None:
    body = {
        "title": draft["title"], "type": draft["type"], "description": draft["description"], "location": draft["location"],
        "work_mode": draft["work_mode"], "required_capabilities": draft["required_capabilities"], "source_segment": "community",
        "structured": structured_for(draft),
    }
    if draft.get("compensation"):
        body["compensation"] = draft["compensation"]
    if draft.get("deadline"):
        body["deadline"] = f"{draft['deadline']}T23:59:00+05:30"
    s, opp = call("POST", "/v1/opportunities", member, body, lang)
    check(f"{label}: createOpportunity accepts the draft", s == 201, opp)
    if s != 201:
        return None
    created_opportunities.append(opp["id"])
    st = opp["structured"]
    if draft["type"] == "employment":
        gate = st["salary_min_paise"] is not None and st["salary_max_paise"] is not None
    elif draft["type"] == "freelance":
        gate = bool(st["budget_min_paise"] or st["budget_max_paise"] or st["hourly_rate_min_paise"] or st["hourly_rate_max_paise"])
    else:
        gate = st["budget_paise"] is not None or bool((opp.get("compensation") or "").strip())
    check(f"{label}: meets the publish pay gate ({opp.get('compensation_label')})", gate, opp)
    return opp


# ---- the flows -------------------------------------------------------------------------

def check_post_job() -> None:
    m = POSTER["en"]
    done = run_interview("job/en", m, "post_job", "en", {
        "work": "I need 2 delivery boys in Kukatpally, salary 15 to 18 thousand",
        "job_timings": "nine in the morning to six in the evening",
        "min_qualification": "10th pass",
        "experience": "no, freshers are fine",
        "requires_assets": "bike and a smartphone",
    }, ["work", "job_timings", "min_qualification", "experience", "requires_assets"], {
        "work": lambda v: v["title"] == "Delivery boys" and "delivery" in v["required_capabilities"],
        "job_timings": lambda v: v == {"job_timings": "9 am to 6 pm", "shift": "day"},
        "min_qualification": lambda v: v == "10th",
        "experience": lambda v: v["min_months"] == 0,
        "requires_assets": lambda v: v == ["two_wheeler", "smartphone"],
    })
    d = done.get("draft") or {}
    e = d.get("employment") or {}
    check("job/en: the first answer filled area, pay and headcount", d.get("location") == "Kukatpally"
          and e.get("salary_min_paise") == 1_500_000 and e.get("salary_max_paise") == 1_800_000 and e.get("openings") == 2, d)
    check("job/en: summary reads in glossary formats", any(i["value_label"] == "₹15,000 to ₹18,000 a month" for i in done.get("summary") or [])
          and any(i["value_label"] == "2 people" for i in done.get("summary") or []), done.get("summary"))
    if d:
        create_from("job/en", m, "en", d)

    m = POSTER["hi"]
    done = run_interview("job/hi", m, "post_job", "hi", {
        "work": "मुझे दुकान के लिए दो हेल्पर चाहिए",
        "location": "haan",
        "salary": "पंद्रह से अठारह हज़ार महीना",
        "job_timings": "सुबह 9 से शाम 6 बजे तक",
        "min_qualification": "दसवीं पास",
        "experience": "nahi, naya chalega",
        "requires_assets": "chhodo",
    }, ["work", "location", "salary", "job_timings", "min_qualification", "experience", "requires_assets"], {
        "location": lambda v: v == "Kukatpally",
        "salary": lambda v: v == {"min_paise": 1_500_000, "max_paise": 1_800_000},
        "job_timings": lambda v: v["job_timings"] == "सुबह 9 से शाम 6 बजे तक",
        "min_qualification": lambda v: v == "10th",
        "experience": lambda v: v["min_months"] == 0,
    })
    d = done.get("draft") or {}
    check("job/hi: 'दो हेल्पर' in the first answer gave 2 openings", (d.get("employment") or {}).get("openings") == 2, d)
    if d:
        create_from("job/hi", m, "hi", d)

    m = POSTER["te"]
    done = run_interview("job/te", m, "post_job", "te", {
        "work": "షాప్‌లో పని చేయడానికి ఇద్దరు హెల్పర్లు కావాలి",
        "location": "avunu",
        "salary": "పదిహేను నుండి పద్దెనిమిది వేలు",
        "job_timings": "ఉదయం 9 నుండి సాయంత్రం 6 వరకు",
        "min_qualification": "పదో తరగతి",
        "experience": "vaddu",
        "requires_assets": "లేదు",
    }, ["work", "location", "salary", "job_timings", "min_qualification", "experience", "requires_assets"], {
        "salary": lambda v: v == {"min_paise": 1_500_000, "max_paise": 1_800_000},
        "job_timings": lambda v: v["job_timings"] == "ఉదయం 9 నుండి సాయంత్రం 6 వరకు",
        "requires_assets": lambda v: v == [],
    })
    d = done.get("draft") or {}
    check("job/te: 'ఇద్దరు' in the first answer gave 2 openings", (d.get("employment") or {}).get("openings") == 2, d)
    if d:
        create_from("job/te", m, "te", d)


def check_post_local() -> None:
    tomorrow = (TODAY + timedelta(days=1)).isoformat()
    m = POSTER["en"]
    done = run_interview("local/en", m, "post_local", "en", {
        "work": "My kitchen tap is leaking, I need a plumber", "location": "yes", "when": "tomorrow morning", "budget": "500 rupees",
    }, ["work", "location", "when", "budget"], {
        "work": lambda v: "plumbing" in v["required_capabilities"],
        "location": lambda v: v == "Himayatnagar",
        "when": lambda v: v == {"preferred_date": tomorrow, "urgency": "this_week"},
        "budget": lambda v: v == {"budget_paise": 50_000, "compensation": None},
    })
    if done.get("draft"):
        create_from("local/en", m, "en", done["draft"])

    m = POSTER["hi"]
    done = run_interview("local/hi", m, "post_local", "hi", {
        "work": "kitchen ka nal tapak raha hai, plumber chahiye", "location": "nahi, Madhapur", "when": "kal", "budget": "तीन सौ प्रति विज़िट",
    }, ["work", "location", "when", "budget"], {
        "location": lambda v: v == "Madhapur",
        "when": lambda v: v["preferred_date"] == tomorrow,
        "budget": lambda v: v == {"budget_paise": None, "compensation": "₹300 per visit"},
    })
    d = done.get("draft") or {}
    check("local/hi: a pay basis instead of a budget travels as compensation", d.get("compensation") == "₹300 per visit"
          and "budget" not in (d.get("missing") or []), d)
    if d:
        opp = create_from("local/hi", m, "hi", d)
        if opp:
            check("local/hi: the post shows the pay basis in Hindi", opp.get("compensation_label") == "₹300 प्रति विज़िट", opp.get("compensation_label"))

    m = POSTER["te"]
    done = run_interview("local/te", m, "post_local", "te", {
        "work": "ఇంట్లో ఫ్యాన్ రిపేర్ చేయాలి", "location": "Kukatpally lo", "when": "repu udayam", "budget": "matladukundam",
    }, ["work", "location", "when", "budget"], {
        "location": lambda v: v == "Kukatpally",
        "when": lambda v: v["preferred_date"] == tomorrow,
        "budget": lambda v: v == {"budget_paise": None, "compensation": "negotiable"},
    })
    if done.get("draft"):
        create_from("local/te", m, "te", done["draft"])


def check_post_project() -> None:
    m = POSTER["en"]
    done = run_interview("project/en", m, "post_project", "en", {
        "work": "A website for my bakery with online orders", "budget": "fifty thousand", "deadline": "in two weeks",
        "work_mode": "from their own place",
    }, ["work", "budget", "deadline", "work_mode"], {
        "budget": lambda v: v == {"budget_type": "fixed", "min_paise": 5_000_000, "max_paise": 5_000_000},
        "deadline": lambda v: v == {"deadline": (TODAY + timedelta(days=14)).isoformat(), "duration": "1_4_weeks"},
        "work_mode": lambda v: v == "remote",
    })
    d = done.get("draft") or {}
    check("project/en: remote work never asks the area", d.get("work_mode") == "remote" and d.get("location") is None
          and d.get("deadline") == (TODAY + timedelta(days=14)).isoformat(), d)
    if d:
        create_from("project/en", m, "en", d)

    m = POSTER["hi"]
    done = run_interview("project/hi", m, "post_project", "hi", {
        "work": "मेरी कोचिंग क्लास के लिए एक लोगो बनवाना है", "budget": "पाँच हज़ार", "deadline": "15 तारीख तक",
        "work_mode": "मेरे पास आकर", "location": "haan",
    }, ["work", "budget", "deadline", "work_mode", "location"], {
        "budget": lambda v: v["min_paise"] == 500_000,
        "deadline": lambda v: v["deadline"] is not None and v["deadline"].endswith("-15"),
        "work_mode": lambda v: v == "on_site",
    })
    if done.get("draft"):
        create_from("project/hi", m, "hi", done["draft"])

    m = POSTER["te"]
    done = run_interview("project/te", m, "post_project", "te", {
        "work": "నా షాప్‌కి ఒక వీడియో కావాలి", "budget": "గంటకు ఐదొందలు", "deadline": "రెండు వారాల్లో",
        "work_mode": "ఏదైనా పర్లేదు", "location": "avunu",
    }, ["work", "budget", "deadline", "work_mode", "location"], {
        "budget": lambda v: v == {"budget_type": "hourly", "min_paise": 50_000, "max_paise": 50_000},
        "work_mode": lambda v: v == "both",
    })
    if done.get("draft"):
        create_from("project/te", m, "te", done["draft"])


async def check_profile(owner: asyncpg.Connection) -> None:
    # Known-field skipping: Meena's profile has her name, area, skills and years.
    step = nxt("m_meena", "profile", "en", {})
    check("profile: a full profile is asked only what it lacks", step["field"] == "own_assets" and step["progress"]["total"] == 1
          and step["optional"] is True and step["kind"] == "choice", step)
    step = nxt("m_meena", "profile", "en", {"own_assets": "none"})
    check("profile: 'none' chip means nothing", step["done"] and step["draft"]["own_assets"] == [] and step["draft"]["draft_type"] == "profile", step)

    member_before = await owner.fetchrow("SELECT locality, lat, lng, updated_at FROM vyapar_identity.members WHERE id = $1", NEW_MEMBER)
    listings_before = {r["id"] for r in await owner.fetch("SELECT id FROM vyapar_listings.listings WHERE owner_id = $1", NEW_MEMBER)}
    runs = [
        ("en", {"work": "I am an electrician, 5 years", "locality": "Boduppal", "own_assets": "bike and my own tools"},
         ["work", "locality", "own_assets"],
         {"work": lambda v: "electrical" in v["required_capabilities"], "own_assets": lambda v: v == ["two_wheeler", "own_tools"]},
         {"capabilities": ["electrical"], "locality": "Boduppal", "experience_years": 5, "own_assets": ["two_wheeler", "own_tools"]}),
        ("hi", {"work": "मैं इलेक्ट्रीशियन का काम करता हूँ, कुकटपल्ली में", "experience_years": "paanch saal", "own_assets": "nahi"},
         ["work", "experience_years", "own_assets"],
         {"work": lambda v: v["required_capabilities"] == ["electrical"], "experience_years": lambda v: v == 5},
         {"capabilities": ["electrical"], "locality": "Kukatpally", "experience_years": 5, "own_assets": []}),
        ("te", {"work": "నేను టైలర్ పని చేస్తాను", "locality": "కూకట్‌పల్లి లో", "experience_years": "పది సంవత్సరాలు", "own_assets": "skip"},
         ["work", "locality", "experience_years", "own_assets"],
         {"work": lambda v: "tailoring" in v["required_capabilities"], "locality": lambda v: v == "Kukatpally", "experience_years": lambda v: v == 10},
         {"capabilities": ["tailoring"], "locality": "Kukatpally", "experience_years": 10}),
    ]
    try:
        for lang, said, asked, checks, expect in runs:
            done = run_interview(f"profile/{lang}", NEW_MEMBER, "profile", lang, said, asked, checks)
            draft = {k: v for k, v in (done.get("draft") or {}).items() if v is not None and k != "draft_type"}
            s, prof = call("PATCH", "/v1/me/profile", NEW_MEMBER, draft, lang)
            p = (prof or {}).get("profile") or {}
            ok = s == 200 and all(p.get(k) == v for k, v in expect.items())
            check(f"profile/{lang}: PATCH /v1/me/profile accepts the draft", ok, {"status": s, "draft": draft, "profile": {k: p.get(k) for k in expect}})
            # back to a member with no profile before the next language
            await owner.execute("DELETE FROM vyapar_listings.listings WHERE owner_id = $1 AND NOT (id = ANY($2::uuid[]))", NEW_MEMBER, list(listings_before))
            await owner.execute("UPDATE vyapar_identity.members SET locality = $2, lat = $3, lng = $4, updated_at = $5 WHERE id = $1",
                                NEW_MEMBER, *member_before.values())
    finally:
        await owner.execute("DELETE FROM vyapar_listings.listings WHERE owner_id = $1 AND NOT (id = ANY($2::uuid[]))", NEW_MEMBER, list(listings_before))
        await owner.execute("UPDATE vyapar_identity.members SET locality = $2, lat = $3, lng = $4, updated_at = $5 WHERE id = $1",
                            NEW_MEMBER, *member_before.values())


def check_controls_and_edges() -> None:
    m = POSTER["en"]
    cases = [
        ("en", "skip", "skip"), ("hi", "chhodo", "skip"), ("te", "vaddu", "skip"),
        ("en", "yes", "yes"), ("hi", "haan", "yes"), ("te", "avunu", "yes"),
        ("en", "no", "no"), ("hi", "nahi", "no"), ("te", "kaadu", "no"),
        ("en", "repeat", "repeat"), ("hi", "phir se", "repeat"), ("te", "malli cheppandi", "repeat"),
    ]
    for lang, text, intent in cases:
        d = interpret(m, "post_job", "requires_assets" if intent == "skip" else "salary", lang, text)
        check(f"control/{lang}: '{text}' is {intent}", d["intent"] == intent and not d["understood"], d)
    d = interpret(m, "post_job", "salary", "hi", "phir se")
    check("control: repeat asks the same question again", d["reprompt"] == "आप हर महीने कितनी सैलरी देंगे?", d)
    d = interpret(m, "post_job", "salary", "en", "skip")
    check("control: skipping a required field says it is needed", d["intent"] == "skip" and d["reprompt"].startswith("We need this one."), d)
    step = nxt(m, "post_job", "en", {"work": {"title": "Cook", "description": "Cook", "required_capabilities": []}, "location": "Ameerpet",
                                    "openings": 1, "job_timings": {"job_timings": "9 am to 6 pm", "shift": "day"},
                                    "min_qualification": "any", "experience": {"min_months": 0}, "requires_assets": []}, ["salary"])
    check("control: a skipped required field is asked again, last", step["field"] == "salary" and step["question"].startswith("We need this one."), step)
    d = interpret(m, "post_job", "salary", "en", "blah blah")
    check("unclear: names what was missed and asks again", d["intent"] == "unclear"
          and d["reprompt"] == "Sorry, I didn't catch the amount. How much will you pay each month?", d)
    d = interpret(m, "post_job", "location", "hi", "nahi")
    check("location yes/no: 'nahi' asks for the area", d["intent"] == "no" and d["reprompt"] == "ठीक है। काम किस इलाके में है?", d)
    d = interpret(m, "post_job", "requires_assets", "hi", "haan")
    check("yes without detail: asks which ones", not d["understood"] and "बाइक" in (d["reprompt"] or ""), d)
    d = interpret(m, "post_job", "salary", "en", "700 a day")
    check("salary: a day wage is read back with its month", d["value"] == {"min_paise": 1_820_000, "max_paise": 1_820_000}
          and "₹700 a day" in d["readback"] and "₹18,200 a month" in d["readback"], d)
    d = interpret(m, "post_job", "openings", "te", "ఇద్దరు")
    check("openings/te: 'ఇద్దరు' is 2 people", d["value"] == 2 and d["readback"] == "నేను విన్నది: 2 మంది. సరేనా?", d)
    d = interpret(m, "post_job", "location", "en", "Kukatpally lo")
    check("location: 'Kukatpally lo' reads back as 'in Kukatpally'", d["value"] == "Kukatpally" and "in Kukatpally" in d["readback"], d)

    # Scam shield: a fee asked of applicants is refused in the poster's language, nothing is read.
    for lang, text in (("hi", "डिलीवरी बॉय चाहिए, रजिस्ट्रेशन फीस 500 रुपये देनी होगी"),
                       ("en", "Need a sales executive, candidates must pay ₹2,000 security deposit"),
                       ("te", "హెల్పర్ కావాలి, జాయినింగ్ ఫీజు కట్టాలి")):
        d = interpret(m, "post_job", "work", lang, text)
        check(f"scam shield/{lang}: a fee on applicants is refused with the reason", not d["understood"] and d["value"] is None
              and in_script(d["reprompt"], lang) and d["intent"] == "answer", d)

    s, d = call("POST", "/v1/voice/interview/interpret", m, {"flow": "post_job", "field": "budget", "text": "500"})
    check("errors: a field from another flow is 422 voice_unknown_field", s == 422 and (d.get("error") or {}).get("code") == "voice_unknown_field", d)
    s, d = call("POST", "/v1/voice/interview/next", m, {"flow": "post_everything"})
    check("errors: an unknown flow is 422", s == 422, d)


def check_contract() -> None:
    s, doc = call("GET", "/openapi.json", POSTER["en"])
    ops = {op.get("operationId") for p in (doc.get("paths") or {}).values() for op in p.values() if isinstance(op, dict)} if s == 200 else set()
    check("openapi: nextInterviewQuestion and interpretInterviewAnswer", {"nextInterviewQuestion", "interpretInterviewAnswer"} <= ops, s)
    check("token scope: both need only `read`", required_scopes("POST", "/v1/voice/interview/next") == ("read",)
          and required_scopes("POST", "/v1/voice/interview/interpret") == ("read",))
    step = nxt(POSTER["te"], "post_job", "te", {})
    check("next: first question is the work, in Telugu, 1 of 8", step["field"] == "work" and step["question"] == "మీకు ఏ పని చేసేవాళ్ళు కావాలి?"
          and step["progress"] == {"asked": 1, "total": 8}, step)
    step = nxt(POSTER["hi"], "post_local", "hi", {"work": {"title": "नल ठीक करना", "description": "नल ठीक करना", "required_capabilities": ["plumbing"]}})
    check("next: the saved area is offered as a yes/no", step["field"] == "location" and step["kind"] == "yesno"
          and step["question"] == "क्या Kukatpally आना होगा?", step)


async def main() -> int:
    owner = await asyncpg.connect(owner_dsn())
    started = datetime.now(timezone.utc)
    try:
        print(f"Checking {API}\n")
        check_catalog_scripts()
        check_contract()
        check_controls_and_edges()
        check_post_job()
        check_post_local()
        check_post_project()
        await check_profile(owner)
        check("script: no question, hint, read-back, reprompt or summary mixed Hindi and Telugu letters", not mixed_seen, mixed_seen[:10])
    finally:
        if created_opportunities:
            await owner.execute("DELETE FROM vyapar_opportunities.opportunities WHERE id = ANY($1::uuid[])", created_opportunities)
        left = await owner.fetchval(
            "SELECT count(*) FROM vyapar_opportunities.opportunities WHERE poster_id = ANY($1) AND created_at >= $2",
            list(POSTER.values()), started)
        await owner.close()
        print(f"\ncleanup: {len(created_opportunities)} draft posts deleted ({left} left from this run); m_new restored")
    print(f"\n{len(passed)} passed, {len(failed)} failed")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
