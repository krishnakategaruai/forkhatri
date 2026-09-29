"""Live check of the AI endpoints (IMP42 — workstream C) against a RUNNING API.

Run a private copy of the API with the rules engine and a small daily limit,
then point this script at it:

    AI_PROVIDER=rules AI_DAILY_LIMIT=15 .venv/Scripts/python -m uvicorn app.main:app --port <free port>
    VYAPAR_CHECK_API=http://127.0.0.1:<port> VYAPAR_CHECK_AI_LIMIT=15 .venv/Scripts/python -m scripts.check_ai

What it proves, over real HTTP and the real database:
  * draftOpportunity reads English, Hindi, Telugu and Hinglish into the typed
    draft (type, money in paise, qualification, assets, urgency ...), keeps
    capability slugs inside the taxonomy, drops phone numbers, and asks for
    what is missing in the request language;
  * readOpportunityImage answers `unsupported_without_ai` (501, localized)
    under the rules engine, and rejects a missing upload;
  * getAiShortlist ranks the real applicants of a seed opportunity 1–10 with
    localized reasons/risks, is poster-only (403), and is empty with no applicants;
  * getPostingTips gives rule tips (e.g. lower the qualification) from a draft
    and from a posted opportunity, poster-only;
  * improveProposal returns a cover text and a bid range from similar opportunities;
  * the per-member daily cap answers 429 `ai_limit_reached` at exactly the limit;
  * every call left one ai_events row with a hash, never the text;
  * the OpenAPI document lists the five operation ids.

It uses seed personas (never the product owner's account), writes no
opportunity, enquiry or proposal (the AI endpoints never do), and on exit
deletes the ai_events rows it caused and restores each member's AI rate-limit
counter, so the development database is left exactly as it was.
"""

from __future__ import annotations

import asyncio
import json
import os
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import asyncpg

SERVICE_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SERVICE_DIR))

from app.config import get_settings  # noqa: E402

API = os.environ.get("VYAPAR_CHECK_API") or f"http://127.0.0.1:{get_settings().api_port}"
LIMIT = int(os.environ.get("VYAPAR_CHECK_AI_LIMIT", "0") or 0)

# Seed data (07a-db-implementation/seeds.sql).
POSTER = "m_deepak"          # posted the villa 3D-visualiser opportunity
APPLICANT = "m_priya"        # applied to it
OPP_WITH_APPLICANT = "00000000-0000-4000-8000-000000000103"
POSTER_NO_APPLICANTS = "m_sunita"
OPP_NO_APPLICANTS = "00000000-0000-4000-8000-000000000105"
DRAFTER = "m_meena"
LIMIT_MEMBER = "m_arjun"
FE1_DRAFTER = "m_rahul"      # the FE1 regression cases, on their own daily allowance
MEMBERS = [POSTER, APPLICANT, POSTER_NO_APPLICANTS, DRAFTER, LIMIT_MEMBER, FE1_DRAFTER]

passed: list[str] = []
failed: list[str] = []


def owner_dsn() -> str:
    env: dict[str, str] = {}
    for line in (SERVICE_DIR.parent / "07a-db-implementation" / ".env").read_text(encoding="utf-8").splitlines():
        if "=" in line and not line.lstrip().startswith("#"):
            k, v = line.split("=", 1)
            env[k.strip()] = v.strip()
    return f"postgresql://{env['DB_OWNER_USER']}:{env['DB_OWNER_PASSWORD']}@{env['DB_HOST']}:{env['DB_PORT']}/{env['DB_NAME']}"


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
    print(("PASS  " if ok else "FAIL  ") + name + ("" if ok else f"\n      {str(detail)[:600]}"))


def err_code(body: Any) -> str | None:
    return body.get("error", {}).get("code") if isinstance(body, dict) else None


def is_script(text: str, lo: int, hi: int) -> bool:
    return any(lo <= ord(c) <= hi for c in text)


# ---- checks -----------------------------------------------------------------

def check_drafts() -> None:
    s, d = call("POST", "/v1/ai/draft-opportunity", DRAFTER, {
        "text": "Hiring 5 delivery boys in Kukatpally. Salary 15k-18k per month + incentives. Own bike and driving licence "
                "required. 10th pass, freshers ok. Timings 9am to 7pm. Walk-in interview Mon-Sat 11am. Call 9876543210",
        "language": "en",
    })
    e = (d or {}).get("employment") or {}
    check("draft/en: employment with typed fields", s == 200 and d["type"] == "employment" and e.get("salary_min_paise") == 1_500_000
          and e.get("salary_max_paise") == 1_800_000 and e.get("openings") == 5 and e.get("min_qualification") == "10th"
          and e.get("experience_min_months") == 0 and set(e.get("requires_assets") or []) >= {"two_wheeler", "driving_licence"}
          and e.get("incentive_type") == "fixed_plus_incentive" and d.get("location") == "Kukatpally", d)
    check("draft/en: phone number never in the draft", s == 200 and "9876543210" not in json.dumps(d), d.get("description") if isinstance(d, dict) else d)
    check("draft/en: capabilities are taxonomy slugs with labels", s == 200 and "delivery" in d["required_capabilities"]
          and len(d["capability_labels"]) == len(d["required_capabilities"]), d)
    check("draft/en: source is rules under AI_PROVIDER=rules", s == 200 and d["source"] == "rules", d)

    s, d = call("POST", "/v1/ai/draft-opportunity", DRAFTER, {
        "text": "Kukatpally में 3 सेल्स स्टाफ चाहिए। वेतन 12000 से 15000 महीना। 12वीं पास। 1 साल अनुभव।", "language": "hi",
    })
    e = (d or {}).get("employment") or {}
    check("draft/hi: Hindi read into salary, 12th, 12 months", s == 200 and d["type"] == "employment"
          and e.get("salary_min_paise") == 1_200_000 and e.get("min_qualification") == "12th" and e.get("experience_min_months") == 12, d)
    check("draft/hi: asks for missing timings, in Hindi", s == 200 and "job_timings" in d["missing"]
          and len(d["questions"]) == len(d["missing"]) and all(is_script(q, 0x0900, 0x097F) for q in d["questions"]), d)

    s, d = call("POST", "/v1/ai/draft-opportunity", DRAFTER, {
        "text": "Madhapur లో ప్లంబర్ కావాలి ఈరోజు, కిచెన్ సింక్ లీక్ అవుతోంది. బడ్జెట్ రూ 800", "language": "te", "entry": "voice",
    })
    ls = (d or {}).get("local_service") or {}
    check("draft/te: Telugu local service, today, ₹800 in paise", s == 200 and d["type"] == "local_service"
          and ls.get("urgency") == "today" and ls.get("budget_paise") == 80_000 and "plumbing" in d["required_capabilities"]
          and d.get("location") == "Madhapur", d)
    check("draft/te: labels in Telugu", s == 200 and all(is_script(x, 0x0C00, 0x0C7F) or x.isascii() for x in d["capability_labels"]), d)

    s, d = call("POST", "/v1/ai/draft-opportunity", DRAFTER, {
        "text": "bhai urgent electrician chahiye aaj Begumpet mein, fan aur switch board ka kaam, 500 rs",
    })
    check("draft/Hinglish: local service in Begumpet", s == 200 and d["type"] == "local_service" and d.get("location") == "Begumpet"
          and "electrical" in d["required_capabilities"], d)

    s, d = call("POST", "/v1/ai/draft-opportunity", DRAFTER, {
        "text": "Need a React developer, freelance project, budget 40k to 60k, 1 month, remote. Have you built a dashboard before?",
    })
    f = (d or {}).get("freelance") or {}
    check("draft/freelance: budget, duration, screening question", s == 200 and d["type"] == "freelance"
          and f.get("budget_type") == "fixed" and f.get("budget_max_paise") == 6_000_000 and f.get("duration") == "1_3_months"
          and f.get("screening_questions") == [{"text": "Have you built a dashboard before?"}], d)

    s, d = call("POST", "/v1/ai/draft-opportunity", DRAFTER, {"text": "x" * 7000})
    check("draft: over-long text is 422 text_too_long", s == 422 and err_code(d) == "text_too_long", d)
    s, d = call("POST", "/v1/ai/draft-opportunity", DRAFTER, {"text": "hello", "language": "fr"})
    check("draft: unknown language is a validation error", s == 422 and err_code(d) == "validation_error", d)


def check_image() -> None:
    s, d = call("POST", "/v1/ai/read-opportunity-image", DRAFTER, {"image_url": "https://example.com/notice.jpg", "language": "hi"})
    check("image: rules engine answers 501 unsupported_without_ai", s == 501 and err_code(d) == "unsupported_without_ai", d)
    check("image: the message is in Hindi", s == 501 and is_script(d["error"]["message"], 0x0900, 0x097F), d)
    s, d = call("POST", "/v1/ai/read-opportunity-image", DRAFTER, {"upload_id": "does-not-exist.jpg"})
    check("image: unknown upload is 422 image_not_found", s == 422 and err_code(d) == "image_not_found", d)
    s, d = call("POST", "/v1/ai/read-opportunity-image", DRAFTER, {"upload_id": "../.env"})
    check("image: path traversal refused", s == 422 and err_code(d) == "image_not_found", d)
    s, d = call("POST", "/v1/ai/read-opportunity-image", DRAFTER, {})
    check("image: nothing given is 422 image_required", s == 422 and err_code(d) == "image_required", d)


def check_shortlist() -> None:
    s, d = call("GET", f"/v1/opportunities/{OPP_WITH_APPLICANT}/ai-shortlist", POSTER, lang="te")
    ok = s == 200 and d["applicant_count"] >= 1 and all(1 <= it["match_score"] <= 10 for it in d["items"])
    check("shortlist: poster gets applicants scored 1–10", ok, d)
    if ok:
        mine = next((it for it in d["items"] if it["sender_id"] == APPLICANT), None)
        check("shortlist: the seed applicant is in it", mine is not None, d)
        # Priya is a software developer; the villa work asks for architecture and
        # interior design. Nearby and verified must not make her look like a fit.
        check("shortlist: no required skill caps the score at 3 and says why", mine is not None and mine["match_score"] <= 3
              and "no_capability_overlap" in [r["code"] for r in mine["risks"]]
              and "experience_fit" not in [r["code"] for r in mine["reasons"]], mine)
        texts = [x["text"] for it in d["items"] for x in it["reasons"] + it["risks"]]
        check("shortlist: reasons and risks localized (Telugu)", bool(texts) and all(is_script(t, 0x0C00, 0x0C7F) for t in texts), texts)
        check("shortlist: sorted by score", [it["match_score"] for it in d["items"]] == sorted((it["match_score"] for it in d["items"]), reverse=True), d)
    s, d = call("GET", f"/v1/opportunities/{OPP_WITH_APPLICANT}/ai-shortlist", APPLICANT)
    check("shortlist: an applicant is refused (403 poster_only)", s == 403 and err_code(d) == "poster_only", d)
    s, d = call("GET", f"/v1/opportunities/{OPP_NO_APPLICANTS}/ai-shortlist", POSTER_NO_APPLICANTS)
    check("shortlist: no applicants gives an empty list", s == 200 and d["applicant_count"] == 0 and d["items"] == [], d)
    s, d = call("GET", "/v1/opportunities/not-a-uuid/ai-shortlist", POSTER)
    check("shortlist: bad id is 404", s == 404 and err_code(d) == "opportunity_not_found", d)


def check_tips() -> None:
    s, d = call("POST", "/v1/ai/posting-tips", DRAFTER, {"language": "hi", "draft": {
        "type": "employment", "title": "Sales executive", "description": "Sales job",
        "employment": {"min_qualification": "graduate", "english_level": "fluent"},
    }})
    codes = [t["code"] for t in (d or {}).get("tips", [])] if s == 200 else []
    check("tips/draft: rule tips include lower_min_qualification and add_salary", s == 200
          and {"lower_min_qualification", "add_salary", "add_location"} <= set(codes), d)
    check("tips/draft: text in Hindi, high impact first", s == 200 and all(is_script(t["text"], 0x0900, 0x097F) for t in d["tips"])
          and d["tips"][0]["impact"] == "high", d)
    s, d = call("POST", "/v1/ai/posting-tips", POSTER, {"opportunity_id": OPP_WITH_APPLICANT})
    check("tips/opportunity: poster gets tips for the posted opportunity", s == 200 and len(d["tips"]) >= 1, d)
    s, d = call("POST", "/v1/ai/posting-tips", APPLICANT, {"opportunity_id": OPP_WITH_APPLICANT})
    check("tips/opportunity: someone else's opportunity is 403", s == 403 and err_code(d) == "poster_only", d)
    s, d = call("POST", "/v1/ai/posting-tips", DRAFTER, {})
    check("tips: neither draft nor id is 422", s == 422 and err_code(d) == "draft_or_opportunity_required", d)


def check_proposal() -> None:
    s, d = call("POST", "/v1/ai/improve-proposal", APPLICANT, {
        "opportunity_id": OPP_WITH_APPLICANT, "text": "I can do this. Call me on 9876543210", "language": "en",
    })
    check("proposal: cover text and improvements returned", s == 200 and len(d["cover_text"]) > 10 and isinstance(d["improvements"], list), d)
    check("proposal: phone number dropped from the cover text", s == 200 and "9876543210" not in d["cover_text"], d.get("cover_text") if isinstance(d, dict) else d)
    check("proposal: remove_contact_details suggested", s == 200 and "remove_contact_details" in [i["code"] for i in d["improvements"]], d)
    check("proposal: bid range from similar opportunities or the poster's budget", s == 200
          and d["bid"]["basis"] in ("capability_overlap", "same_type", "poster_budget", "none")
          and (d["bid"]["basis"] == "none" or (d["bid"]["min_paise"] or 0) <= (d["bid"]["median_paise"] or 0) <= (d["bid"]["max_paise"] or 0)), d)
    s, d = call("POST", "/v1/ai/improve-proposal", APPLICANT, {"opportunity_id": OPP_WITH_APPLICANT, "text": "", "language": "te"})
    check("proposal: empty draft gets a full Telugu cover text", s == 200 and is_script(d["cover_text"], 0x0C00, 0x0C7F), d)
    s, d = call("POST", "/v1/ai/improve-proposal", APPLICANT, {"opportunity_id": OPP_WITH_APPLICANT, "text": ""})
    check("proposal: never claims unrelated experience or skills", s == 200 and "experience in this" not in d["cover_text"]
          and "Software" not in d["cover_text"], d.get("cover_text") if isinstance(d, dict) else d)
    check("proposal: hints do not repeat what the suggested text already says", s == 200
          and "state_availability" not in [i["code"] for i in d["improvements"]], d)


def check_fe1_regressions() -> None:
    """The five rules-reader bugs FE1 found in the browser (2026-09-29)."""
    def draft(text: str, lang: str = "en") -> tuple[int, Any]:
        return call("POST", "/v1/ai/draft-opportunity", FE1_DRAFTER, {"text": text, "language": lang})

    # (1) a software deliverable is freelance work, never a local service
    s, d = draft("Need someone to build a React dashboard with sales charts for our shop. Budget 30k, 2 weeks.")
    check("FE1-1: 'React dashboard' is freelance", s == 200 and d["type"] == "freelance", d)
    s, d2 = draft("React dashboard for my store - show daily orders and sales charts")
    check("FE1-1: short 'React dashboard' notice is freelance too", s == 200 and d2["type"] == "freelance", d2)
    s, d3 = draft("Need a plumber today for leaking tap at home")
    check("FE1-1: a real home repair stays a local service", s == 200 and d3["type"] == "local_service", d3)

    # (2) skills in context, not bare substrings
    check("FE1-2: 'sales charts' does not add the sales skill, React stays", s == 200
          and "sales" not in d["required_capabilities"] and "react" in d["required_capabilities"], d)
    s, d = draft("Hiring sales executive, 2 years experience in field sales")
    check("FE1-2: 'sales executive' does add the sales skill", s == 200 and "sales" in d["required_capabilities"], d)

    # (3) a label before a colon is not the title, and the title is not cut at the colon
    s, d = draft("Job opening: Sales executive for our showroom in Ameerpet")
    check("FE1-3: 'Job opening:' label dropped, the role is the title", s == 200 and d["title"] == "Sales executive for our showroom in Ameerpet", d)
    s, d = draft("Urgent:\nDelivery boys needed in Kukatpally, salary 15000")
    check("FE1-3: label on its own line, title from the next line", s == 200 and d["title"].startswith("Delivery boys needed in Kukatpally"), d)

    # (4) Devanagari places; "se … tak" and "nundi … varaku" ranges
    s, d = draft("Delivery boys needed in कुकटपल्ली, salary 12k to 15k")
    check("FE1-4: Devanagari place inside an English sentence", s == 200 and d["location"] == "कुकटपल्ली", d)
    s, d = draft("डिलीवरी बॉय चाहिए। स्थान: कुकटपल्ली। वेतन 12 से 15 हज़ार तक", "hi")
    e = (d or {}).get("employment") or {}
    check("FE1-4: 'स्थान:' label and '12 से 15 हज़ार तक' range", s == 200 and d["type"] == "employment" and d["location"] == "कुकटपल्ली"
          and (e.get("salary_min_paise"), e.get("salary_max_paise")) == (1_200_000, 1_500_000), d)
    s, d = draft("Salary 12000 nundi 15000 varaku, delivery boys kavali Madhapur lo", "te")
    e = (d or {}).get("employment") or {}
    check("FE1-4: 'nundi … varaku' is a range", s == 200 and (e.get("salary_min_paise"), e.get("salary_max_paise")) == (1_200_000, 1_500_000), d)
    s, d = draft("Salary 12000 se 15000 tak, delivery boys chahiye Ameerpet mein", "hi")
    e = (d or {}).get("employment") or {}
    check("FE1-4: 'se … tak' is a range", s == 200 and (e.get("salary_min_paise"), e.get("salary_max_paise")) == (1_200_000, 1_500_000)
          and d["location"] == "Ameerpet", d)

    # (5) never suggest bidding under the poster's stated range without saying why
    s, d = call("POST", "/v1/ai/improve-proposal", APPLICANT, {"opportunity_id": OPP_WITH_APPLICANT, "text": "", "language": "hi"})
    b = (d or {}).get("bid") or {}
    check("FE1-5: live bid never below the poster's stated minimum", s == 200 and b.get("poster_min_paise")
          and (b.get("min_paise") or 0) >= b["poster_min_paise"], b)
    check("FE1-5: the bid carries a note, in Hindi", s == 200 and b.get("note") and is_script(b["note"]["text"], 0x0900, 0x097F), b)
    from app.services.ai import suggest_bid  # the same function the endpoint uses

    low = suggest_bid([2_000_000, 3_000_000, 5_000_000], 7, "same_type", 4_000_000, 6_000_000, "en")
    check("FE1-5: cheaper similar work is raised to the poster's floor, with a reason",
          low.min_paise == 4_000_000 and low.max_paise == 5_000_000 and low.note and low.note.code == "clamped_to_poster_budget"
          and "₹20,000–₹50,000" in low.note.text and "₹40,000–₹60,000" in low.note.text, low)
    high = suggest_bid([7_000_000, 8_000_000, 9_000_000], 4, "same_type", 4_000_000, 6_000_000, "en")
    check("FE1-5: dearer similar work is held at the poster's ceiling, with a reason",
          high.min_paise == high.max_paise == 6_000_000 and high.note and high.note.code == "market_above_poster_budget", high)


def check_limit(pre_count: int) -> None:
    if not LIMIT:
        print("SKIP  daily limit (set VYAPAR_CHECK_AI_LIMIT to the server's AI_DAILY_LIMIT)")
        return
    allowed = max(0, LIMIT - pre_count)
    statuses = [call("POST", "/v1/ai/posting-tips", LIMIT_MEMBER, {"draft": {"type": "freelance"}})[0] for _ in range(allowed)]
    s, d = call("POST", "/v1/ai/posting-tips", LIMIT_MEMBER, {"draft": {"type": "freelance"}}, lang="te")
    check(f"limit: {allowed} calls allowed, then 429 ai_limit_reached", all(x == 200 for x in statuses) and s == 429
          and err_code(d) == "ai_limit_reached", (statuses[-3:], s, d))
    check("limit: message localized (Telugu)", s == 429 and is_script(d["error"]["message"], 0x0C00, 0x0C7F), d)


def check_openapi() -> None:
    with urllib.request.urlopen(f"{API}/openapi.json", timeout=30) as res:
        doc = json.loads(res.read())
    ops = {op.get("operationId") for path in doc["paths"].values() for op in path.values() if isinstance(op, dict)}
    wanted = {"draftOpportunity", "readOpportunityImage", "getAiShortlist", "getPostingTips", "improveProposal"}
    check("openapi: five operation ids published", wanted <= ops, wanted - ops)


async def main() -> int:
    started = datetime.now(timezone.utc)
    owner = await asyncpg.connect(owner_dsn())
    keys = [f"ai:{m}" for m in MEMBERS]
    before = {
        (r["rate_limit_key"], r["window_start"]): r["hit_count"]
        for r in await owner.fetch("SELECT rate_limit_key, window_start, hit_count FROM vyapar_platform.rate_limit_counter WHERE rate_limit_key = ANY($1)", keys)
    }
    pre_limit = await owner.fetchval(
        """SELECT coalesce(max(hit_count), 0) FROM vyapar_platform.rate_limit_counter
            WHERE rate_limit_key = $1 AND window_start = to_timestamp(floor(extract(epoch FROM now()) / 86400) * 86400)""",
        f"ai:{LIMIT_MEMBER}",
    )
    events_before = {r["id"] for r in await owner.fetch("SELECT id FROM vyapar_integration.ai_events WHERE member_id = ANY($1)", MEMBERS)}
    try:
        print(f"Checking {API}\n")
        check_openapi()
        check_drafts()
        check_image()
        check_shortlist()
        check_tips()
        check_proposal()
        check_fe1_regressions()
        check_limit(int(pre_limit or 0))

        rows = await owner.fetch(
            "SELECT * FROM vyapar_integration.ai_events WHERE member_id = ANY($1) AND created_at >= $2 ORDER BY created_at", MEMBERS, started,
        )
        kinds = {r["kind"] for r in rows}
        check("audit: ai_events rows for every kind", {"draft", "read_image", "shortlist", "tips", "proposal"} <= kinds, kinds)
        check("audit: rules provider, no model, hashed input", bool(rows) and all(r["provider"] == "rules" and r["model"] is None
              and len(r["input_hash"]) == 64 for r in rows), [dict(r) for r in rows[:2]])
        check("audit: image refusal recorded as unsupported_without_ai",
              any(r["kind"] == "read_image" and r["outcome"] == "unsupported_without_ai" for r in rows), [r["outcome"] for r in rows])
        text_cols = {c["column_name"] for c in await owner.fetch(
            "SELECT column_name FROM information_schema.columns WHERE table_schema='vyapar_integration' AND table_name='ai_events'")}
        check("audit: no column holds the input text", not ({"text", "input", "prompt", "body"} & text_cols), text_cols)
    finally:
        # Leave the shared development database exactly as it was.
        deleted = await owner.execute(
            "DELETE FROM vyapar_integration.ai_events WHERE member_id = ANY($1) AND created_at >= $2 AND NOT (id = ANY($3::uuid[]))",
            MEMBERS, started, list(events_before),
        )
        now_rows = await owner.fetch(
            "SELECT rate_limit_key, window_start, hit_count FROM vyapar_platform.rate_limit_counter WHERE rate_limit_key = ANY($1)", keys,
        )
        for r in now_rows:
            k = (r["rate_limit_key"], r["window_start"])
            if k in before:
                await owner.execute("UPDATE vyapar_platform.rate_limit_counter SET hit_count = $3 WHERE rate_limit_key = $1 AND window_start = $2", k[0], k[1], before[k])
            else:
                await owner.execute("DELETE FROM vyapar_platform.rate_limit_counter WHERE rate_limit_key = $1 AND window_start = $2", k[0], k[1])
        await owner.close()
        print(f"\ncleanup: {deleted} ai_events rows removed, {len(now_rows)} rate-limit counters restored")

    print(f"\n{len(passed)} passed, {len(failed)} failed")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
