"""End-to-end check for structured opportunities, structured applications,
the applicant pipeline and the taxonomy tree (backend workstream A).

Walks the real product flow over the REST API as seeded members, against a
running Vyapar API (a private port, never the owner's live 8011 unless you
mean it):

  job:      m_sunita (Kapoor Caterers) drafts "Kitchen helper and baker" with
            a salary on a job refused for a budget field -> publish refused
            without a salary -> salary added -> suggestions (qualification,
            timings) -> published; compensation_label in en and hi.
            m_meena applies with ONE TAP (no message; profile snapshot and a
            built message), m_ravi applies with a written message.
            Poster lists applicants (by match, stage filter, cursor), compares
            them, shortlists and hires Meena (thread accepted), declines Ravi
            (thread closed, Ravi notified in Hindi), Ravi cannot re-apply,
            hired is final, an outsider sees nothing (404), events in outbox.
  project:  m_vikram (Sethi Textiles) posts a fixed-budget bookkeeping
            project with a screening question; m_anita's proposal is refused
            without a bid, with milestones that don't add up, and without the
            screening answer, then accepted with all three.
  taxonomy: GET /v1/taxonomy/tree in Telugu has the new categories and
            roles; first-run scoped skills come from the DB tree.
  hooks:    workstream B's hooks wired here: a fee in the text, in a
            structured text field or `candidate_pays: true` is refused on
            create, patch and publish (seeker_charge_not_allowed); the job
            detail carries seeker_protection and poster_badges; the thread
            carries contact_actions only after hiring.
  compat:   a short enquiry on a listing is still refused (message_too_short).

Everything it creates is deleted at the end (finally), the daily enquiry
counters it used are restored, and a sweep over every vyapar_* table
confirms no row still mentions any id it created.

Usage (from vyapar-service/):
    .venv/Scripts/python scripts/check_structured_hiring.py --api http://127.0.0.1:<port>

The API must run with DEV_MODE=true (X-Dev-Member-Id). The cleanup connects
as the migration owner using ../07a-db-implementation/.env (DB_HOST, DB_PORT,
DB_NAME, DB_OWNER_USER, DB_OWNER_PASSWORD).
"""
from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
from collections import Counter
from pathlib import Path

import asyncpg

EMPLOYER, BAKER, HELPER = "m_sunita", "m_meena", "m_ravi"
CLIENT, ACCOUNTANT, OUTSIDER = "m_vikram", "m_anita", "m_rahul"
RESULTS: list[tuple[bool, str]] = []


def check(cond: bool, label: str) -> None:
    RESULTS.append((bool(cond), label))
    print(("  PASS  " if cond else "  FAIL  ") + label)


class Api:
    def __init__(self, base: str) -> None:
        self.base = base.rstrip("/")

    def call(self, method: str, path: str, member: str, body: dict | None = None, lang: str = "en") -> tuple[int, dict]:
        req = urllib.request.Request(
            self.base + path, method=method, data=json.dumps(body).encode() if body is not None else None,
            headers={"X-Dev-Member-Id": member, "Content-Type": "application/json", "X-Vyapar-Language": lang},
        )
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                raw = resp.read()
                return resp.status, (json.loads(raw) if raw else {})
        except urllib.error.HTTPError as exc:
            raw = exc.read()
            try:
                return exc.code, json.loads(raw)
            except ValueError:
                return exc.code, {"raw": raw.decode(errors="replace")}


def owner_dsn() -> str:
    env_path = Path(__file__).resolve().parents[2] / "07a-db-implementation" / ".env"
    values: dict[str, str] = {}
    for line in env_path.read_text(encoding="utf-8").splitlines():
        line = line.split("#", 1)[0].strip()
        if "=" in line:
            k, v = line.split("=", 1)
            values[k.strip()] = v.strip()
    values.update({k: v for k, v in os.environ.items() if k.startswith("DB_")})
    return (f"postgres://{values['DB_OWNER_USER']}:{values['DB_OWNER_PASSWORD']}"
            f"@{values['DB_HOST']}:{values['DB_PORT']}/{values['DB_NAME']}")


def code(body: dict) -> str | None:
    return (body.get("error") or {}).get("code")


async def main(api_base: str) -> int:
    api = Api(api_base)
    db = await asyncpg.connect(owner_dsn())
    opp_ids: set[str] = set()
    enquiry_ids: set[str] = set()
    sent: Counter[str] = Counter()  # enquiries that passed the daily cap, per member
    started_at = await db.fetchval("SELECT now()")
    try:
        # ------------------------------------------------------------ taxonomy
        print("\n== Taxonomy tree ==")
        st, tree = api.call("GET", "/v1/taxonomy/tree", EMPLOYER, lang="te")
        cats = {c["slug"]: c for c in tree.get("categories", [])}
        check(st == 200 and tree.get("language") == "te", "getTaxonomyTree answers in Telugu")
        check({"hospitality_housekeeping", "sales_telecalling", "office_admin", "healthcare"} <= set(cats), "new categories present")
        cook = next((c for c in cats.get("hospitality_housekeeping", {}).get("children", []) if c["slug"] == "cook"), None)
        check(cook is not None and cook["label"] == "వంటవారు" and bool(cook["description"]), "cook sits under Hospitality with a Telugu label and description")
        check(all(c["children"] for c in cats.values()), "every category has at least one skill or role")
        st, scoped = api.call("GET", "/v1/first-run/scoped-capability-options?categories=home_repair", EMPLOYER)
        slugs = {o["slug"] for o in scoped} if st == 200 else set()
        check({"carpenter", "painter", "ac_technician", "plumbing"} <= slugs and "software" not in slugs, "first-run scoped skills come from the DB tree")

        # ------------------------------------------------------------ job
        print("\n== Employment: structured job ==")
        draft = {
            "title": "Kitchen helper and baker for catering unit",
            "type": "employment",
            "description": "Help our catering kitchen in Secunderabad with prep and daily baking for wedding orders.",
            "location": "Secunderabad",
            "work_mode": "on_site",
            "required_capabilities": ["bakery", "catering"],
            "response_method": "in_app",
            "source_segment": "community",
        }
        st, res = api.call("POST", "/v1/opportunities", EMPLOYER, {**draft, "structured": {"budget_min_paise": 100000}})
        check(st == 422 and code(res) == "structured_field_not_for_type", "a freelance budget on a job is refused")
        # workstream B's "nobody charges job seekers" hook, on create
        st, res = api.call("POST", "/v1/opportunities", EMPLOYER, {**draft, "description": draft["description"] + " Pay ₹500 uniform charge on joining."})
        check(st == 422 and code(res) == "seeker_charge_not_allowed", "create refused when the text charges the applicant (hook)")
        st, res = api.call("POST", "/v1/opportunities", EMPLOYER, {**draft, "candidate_pays": True})
        check(st == 422 and code(res) == "seeker_charge_not_allowed" and res["error"]["details"].get("field") == "candidate_pays", "create refused when candidate_pays is true (hook)")
        st, job = api.call("POST", "/v1/opportunities", EMPLOYER, {**draft, "structured": {
            "openings": 2, "shift": "day", "min_qualification": "graduate", "english_level": "basic",
            "experience_min_months": 12, "requires_assets": ["Smartphone", "smartphone"],
        }})
        check(st == 201, f"job draft created ({st})")
        job_id = job["id"]
        opp_ids.add(job_id)
        check(job["structured"]["requires_assets"] == ["smartphone"] and job["structured"]["budget_type"] is None, "structured fields normalised; other types' fields null")
        st, res = api.call("POST", f"/v1/opportunities/{job_id}/publish", EMPLOYER)
        check(st == 422 and code(res) == "salary_required", "publish refused without a salary range")
        st, res = api.call("PATCH", f"/v1/opportunities/{job_id}", EMPLOYER, {"structured": {"salary_min_paise": 2400000, "salary_max_paise": 1800000}})
        check(st == 422 and code(res) == "salary_range_invalid", "salary min above max refused")
        st, job = api.call("PATCH", f"/v1/opportunities/{job_id}", EMPLOYER, {"structured": {
            "salary_min_paise": 1800000, "salary_max_paise": 2400000, "incentive_type": "fixed_plus_incentive", "incentive_max_paise": 300000,
        }})
        check(st == 200 and job["structured"]["openings"] == 2, "patch is partial: earlier fields kept")
        check(job["compensation"] == "₹18,000 to ₹24,000 a month + incentives up to ₹3,000", f"compensation kept in sync ({job.get('compensation')})")
        st, sug = api.call("GET", f"/v1/opportunities/{job_id}/suggestions", EMPLOYER)
        codes = [s["code"] for s in sug.get("suggestions", [])]
        check(st == 200 and {"lower_qualification", "add_job_timings", "add_interview_details"} <= set(codes) and "add_salary" not in codes,
              f"suggestions reflect what is missing or restrictive ({codes})")
        st, _ = api.call("GET", f"/v1/opportunities/{job_id}/suggestions", BAKER)
        check(st == 404, "suggestions are poster-only")
        st, res = api.call("PATCH", f"/v1/opportunities/{job_id}", EMPLOYER, {"structured": {
            "interview_details": "Bring a registration fee of ₹300 to the interview"}})
        check(st == 422 and code(res) == "seeker_charge_not_allowed", "patch refused when a structured text field charges the applicant (hook)")
        st, job = api.call("PATCH", f"/v1/opportunities/{job_id}", EMPLOYER, {"structured": {
            "min_qualification": "10th", "job_timings": "7 am to 4 pm, Sunday off", "interview_details": "Walk in at our Secunderabad kitchen, 11 am to 1 pm",
        }})
        st, sug = api.call("GET", f"/v1/opportunities/{job_id}/suggestions", EMPLOYER)
        check("lower_qualification" not in [s["code"] for s in sug["suggestions"]], "suggestion disappears once acted on")
        st, job = api.call("POST", f"/v1/opportunities/{job_id}/publish", EMPLOYER)
        check(st == 200 and job["state"] == "active", "job published")
        st, hi_view = api.call("GET", f"/v1/opportunities/{job_id}", BAKER, lang="hi")
        check(st == 200 and hi_view["compensation_label"].startswith("₹18,000 से ₹24,000 प्रति माह"), f"compensation_label localized ({hi_view.get('compensation_label')})")
        sp = hi_view.get("seeker_protection") or {}
        check(sp.get("applies") is True and sp.get("report_reason") == "asked_for_money" and bool(sp.get("title")), "detail carries seeker_protection on a job (enricher hook)")
        st, en_view = api.call("GET", f"/v1/opportunities/{job_id}", BAKER)
        st, te_view = api.call("GET", f"/v1/opportunities/{job_id}", BAKER, lang="te")
        check(en_view["seeker_protection"]["title"] == "Nobody may charge people who apply"
              and "అప్లై చేసినవారి" in te_view["seeker_protection"]["title"] and "అభ్యర్థు" not in te_view["seeker_protection"]["body"],
              f"glossary term 'applicant' in the protection notice ({en_view['seeker_protection']['title']} / {te_view['seeker_protection']['title']})")
        check(isinstance(hi_view.get("poster_badges"), list), f"detail carries poster_badges (enricher hook) ({[b.get('key') for b in hi_view.get('poster_badges', [])]})")

        print("\n== Employment: applications ==")
        st, meena_app = api.call("POST", "/v1/enquiries", BAKER, {"opportunity_id": job_id, "message": ""}, lang="te")
        if st == 201:
            enquiry_ids.add(meena_app["id"]); sent[BAKER] += 1
        check(st == 201 and meena_app["applied_via"] == "one_tap" and meena_app["action_type"] == "apply", f"one-tap apply with no message ({st})")
        snap = meena_app.get("profile_snapshot") or {}
        check(snap.get("name") == "Meena Sahni" and "bakery" in snap.get("capabilities", []) and snap.get("experience_years") == 5, "profile snapshot stored")
        st, thread = api.call("GET", f"/v1/enquiries/{meena_app['id']}", EMPLOYER)
        check(st == 200 and thread["messages"] and "5" in thread["messages"][0]["body"], "poster's thread opens with a message built from the profile")
        first = thread["messages"][0]
        check(first["body"].startswith("Hello, I'd like to apply.") and first["templated"] and first["message_language"] == "en",
              f"one-tap message applied from Telugu reads in the poster's English ({first['body'][:40]})")
        st, own = api.call("GET", f"/v1/enquiries/{meena_app['id']}", BAKER, lang="te")
        check(own["messages"][0]["body"].startswith("నమస్తే") and own["messages"][0]["message_language"] == "te", "and in Telugu for a Telugu reader")
        stored = await db.fetchrow("SELECT template_key, content_language FROM vyapar_enquiries.enquiry_messages WHERE enquiry_id = $1", meena_app["id"])
        check(stored["template_key"] == "oneTap" and stored["content_language"] == "te", "stored as a template key plus the snapshot")
        st, res = api.call("POST", "/v1/enquiries", HELPER, {"opportunity_id": job_id, "message": "", "bid_amount_paise": 100000})
        check(st == 422 and code(res) == "proposal_fields_not_allowed", "a bid on a job application is refused")
        st, ravi_app = api.call("POST", "/v1/enquiries", HELPER, {
            "opportunity_id": job_id,
            "message": "I have helped in wedding kitchens for two years and can start on Monday.",
        }, lang="hi")
        if st == 201:
            enquiry_ids.add(ravi_app["id"]); sent[HELPER] += 1
        check(st == 201 and ravi_app["applied_via"] == "form" and ravi_app["stage"] == "new", f"written application ({st})")

        print("\n== Employment: the poster's pipeline ==")
        st, page = api.call("GET", f"/v1/opportunities/{job_id}/applicants?sort=match", EMPLOYER)
        check(st == 200 and page["total"] == 2 and page["stage_counts"]["new"] == 2, "listOpportunityApplicants returns both, with stage counts")
        check(page["items"][0]["sender_id"] == BAKER and page["items"][0]["match_score"] > page["items"][1]["match_score"],
              f"sorted by match: the baker first ({[(i['name'], i['match_score']) for i in page['items']]})")
        check("capability_fit" in page["items"][0]["match_signals"] and page["items"][0]["match_reasons"], "match reasons come from the ranking allow-list")
        # One skills verdict from the real overlap (job needs bakery + catering)
        meena_row = next(i for i in page["items"] if i["sender_id"] == BAKER)
        ravi_row = next(i for i in page["items"] if i["sender_id"] == HELPER)
        sm = meena_row["skills_match"]
        check(sm["state"] == "some" and sm["kind"] == "reason" and sm["text"] == "Has 1 of 2 skills: Baking", f"some skills: one precise reason ({sm['text']})")
        check(meena_row["missing_skills"] == [{"slug": "catering", "label": "Catering"}] and sm["missing_text"] == "Missing: Catering",
              f"missing_skills lists what is lacking ({meena_row['missing_skills']}, {sm['missing_text']})")
        skill_lines = [r for r in meena_row["match_reasons"] + meena_row["match_risks"] if "skill" in r.lower()]
        check(skill_lines == [sm["text"]] and not any("your capabilities" in r for r in meena_row["match_reasons"]),
              f"exactly one skills line, worded for the poster ({meena_row['match_reasons']} / {meena_row['match_risks']})")
        rs = ravi_row["skills_match"]
        check(meena_row["message_templated"] and meena_row["message_preview"].startswith("Hello") and meena_row["message_language"] == "en",
              "board preview of a one-tap application is in the poster's language")
        check(not ravi_row["message_templated"] and ravi_row["message_language"] == "hi" and ravi_row["message_preview"].startswith("I have helped"),
              "a written note is shown as written, with its language for a later Translate")
        check("Has the experience you asked for" not in ravi_row["match_reasons"] and ravi_row["match_score"] <= 30,
              f"experience counts only in the matching trade ({ravi_row['match_reasons']}, score {ravi_row['match_score']})")
        st, hi_page = api.call("GET", f"/v1/opportunities/{job_id}/applicants?sort=match", EMPLOYER, lang="hi")
        hm = next(i for i in hi_page["items"] if i["sender_id"] == BAKER)
        check(hm["message_preview"].startswith("नमस्ते"), "the same preview renders in Hindi for a Hindi reader")
        check(rs["state"] == "none" and rs["kind"] == "risk" and rs["text"] in ravi_row["match_risks"] and rs["text"] not in ravi_row["match_reasons"],
              f"no skills: a risk, not a reason ({rs['text']})")
        st, ai = api.call("GET", f"/v1/opportunities/{job_id}/ai-shortlist", EMPLOYER)
        ai_meena = next((i for i in ai.get("items", []) if i["sender_id"] == BAKER), None) if st == 200 else None
        codes_r = [r["code"] for r in (ai_meena or {}).get("reasons", [])]
        codes_k = [r["code"] for r in (ai_meena or {}).get("risks", [])]
        check(ai_meena is not None and "capability_fit" not in codes_r and "partial_capability_overlap" in codes_k,
              f"AI shortlist: partial overlap is only a risk, never also 'has the skills' ({codes_r} / {codes_k})")
        st, p1 = api.call("GET", f"/v1/opportunities/{job_id}/applicants?limit=1", EMPLOYER)
        st2, p2 = api.call("GET", f"/v1/opportunities/{job_id}/applicants?limit=1&cursor={urllib.parse.quote(p1.get('next_cursor') or '')}", EMPLOYER)
        check(p1.get("next_cursor") and st2 == 200 and p2["items"][0]["enquiry_id"] != p1["items"][0]["enquiry_id"] and p2["next_cursor"] is None, "cursor pagination")
        st, _ = api.call("GET", f"/v1/opportunities/{job_id}/applicants", OUTSIDER)
        check(st == 404, "an outsider cannot list applicants")
        st, _ = api.call("GET", f"/v1/opportunities/{job_id}/applicants", BAKER)
        check(st == 404, "an applicant cannot list other applicants")
        st, cmp_ = api.call("GET", f"/v1/opportunities/{job_id}/applicants/compare?ids={meena_app['id']},{ravi_app['id']}", EMPLOYER)
        check(st == 200 and [i["enquiry_id"] for i in cmp_["items"]] == [meena_app["id"], ravi_app["id"]] and cmp_["required_capability_labels"], "compareApplicants keeps the requested order")
        st, res = api.call("GET", f"/v1/opportunities/{job_id}/applicants/compare?ids={meena_app['id']}", EMPLOYER)
        check(st == 422 and code(res) == "compare_count", "compare needs at least two")

        st, before = api.call("GET", f"/v1/enquiries/{meena_app['id']}", BAKER)
        check(st == 200 and before.get("contact_actions") == [] and before.get("contact_attempts") == [], "before hiring: no contact actions on the thread (enricher hook)")
        st, pbefore = api.call("GET", f"/v1/enquiries/{meena_app['id']}", EMPLOYER)
        check(st == 200 and pbefore.get("contact_actions") == [] and meena_row["contact_actions"] == [] and not meena_row["contact_revealed"],
              "before shortlisting: the poster has no number either")
        check(pbefore.get("can_contact_counterpart") is False and pbefore.get("counterpart_can_contact") is False
              and before.get("can_contact_counterpart") is False and before.get("counterpart_can_contact") is False,
              "before shortlisting: neither side may contact the other")
        st, res = api.call("POST", f"/v1/opportunities/{job_id}/applicants/{meena_app['id']}/contact-attempts", EMPLOYER, {"channel": "call"})
        check(st == 400 and code(res) == "not_revealed", "a call tap before shortlisting is refused")

        print("\n== Shortlist: the poster may call ==")
        st, a = api.call("POST", f"/v1/opportunities/{job_id}/applicants/{meena_app['id']}/stage", EMPLOYER, {"stage": "shortlisted"})
        check(st == 200 and a["stage"] == "shortlisted" and a["thread_state"] == "open", "shortlisted; thread still open")
        acts = {c["channel"]: c for c in a.get("contact_actions", [])}
        check(a.get("contact_revealed") and acts.get("call", {}).get("href") == "tel:+919000000008" and acts["call"]["available_now"]
              and acts["call"]["reason"] is None and acts["call"]["window"] is None and "whatsapp" in acts,
              f"shortlisted: the poster gets Call and WhatsApp, no call hours ({list(acts)})")
        st, page = api.call("GET", f"/v1/opportunities/{job_id}/applicants?stage=shortlisted", EMPLOYER)
        check(st == 200 and page["items"] and page["items"][0]["contact_actions"], "listOpportunityApplicants carries the shortlisted applicant's contact actions")
        st, pthread = api.call("GET", f"/v1/enquiries/{meena_app['id']}", EMPLOYER)
        check(st == 200 and any(c["channel"] == "call" and c["href"] == "tel:+919000000008" for c in pthread.get("contact_actions", [])),
              "the poster's thread shows the applicant's Call")
        st, athread = api.call("GET", f"/v1/enquiries/{meena_app['id']}", BAKER)
        check(st == 200 and athread.get("contact_actions") == [], "the applicant still does not see the poster's number (no pre-call on this post)")
        check(pthread.get("can_contact_counterpart") is True and pthread.get("counterpart_can_contact") is False,
              "poster's thread flags: can contact the applicant; the applicant cannot contact them")
        check(athread.get("can_contact_counterpart") is False and athread.get("counterpart_can_contact") is True,
              "applicant's thread flags: the poster may contact them; they cannot yet")
        st, notes = api.call("GET", "/v1/notifications", BAKER)
        sl = [n for n in notes if n["kind"] == "applicantShortlisted" and meena_app["id"] in (n.get("link") or "")] if st == 200 else []
        check(len(sl) == 1 and "Sunita Kapoor" in (sl[0]["body"] or "") and "call" in (sl[0]["body"] or ""),
              f"the applicant is told they may be called ({sl[0]['title'] if sl else None})")
        n_audit = await db.fetchval(
            "SELECT count(*) FROM vyapar_integration.audit_events WHERE object_id = $1 AND action = 'applicant_contact_revealed'", meena_app["id"])
        check(n_audit == 1, "the reveal is in the audit log")
        st, tapped = api.call("POST", f"/v1/opportunities/{job_id}/applicants/{meena_app['id']}/contact-attempts", EMPLOYER, {"channel": "call"})
        check(st == 201 and tapped["contact_revealed"], f"the poster's call tap is recorded ({st})")
        st, athread = api.call("GET", f"/v1/enquiries/{meena_app['id']}", BAKER)
        att = athread.get("contact_attempts", [])
        check(len(att) == 1 and att[0]["caller_id"] == EMPLOYER and att[0]["mine"] is False, "the applicant sees the call in the thread's contact log")

        # Leaving the shortlist hides the number again (back to new, then declined)
        st, a = api.call("POST", f"/v1/opportunities/{job_id}/applicants/{ravi_app['id']}/stage", EMPLOYER, {"stage": "shortlisted"})
        check(st == 200 and any(c["href"] == "tel:+919000000003" for c in a["contact_actions"] if c["channel"] == "call"), "second applicant shortlisted: number shown")
        st, a = api.call("POST", f"/v1/opportunities/{job_id}/applicants/{ravi_app['id']}/stage", EMPLOYER, {"stage": "new"})
        check(st == 200 and a["contact_actions"] == [] and not a["contact_revealed"], "back to new: number hidden")
        st, pthread = api.call("GET", f"/v1/enquiries/{ravi_app['id']}", EMPLOYER)
        check(st == 200 and pthread.get("contact_actions") == [], "back to new: hidden in the thread too")
        st, a = api.call("POST", f"/v1/opportunities/{job_id}/applicants/{ravi_app['id']}/stage", EMPLOYER, {"stage": "shortlisted"})
        check(st == 200 and a["contact_revealed"], "shortlisted again: shown again")
        st, _ = api.call("POST", f"/v1/opportunities/{job_id}/applicants/{meena_app['id']}/stage", BAKER, {"stage": "hired"})
        check(st == 404, "an applicant cannot move their own stage")
        st, a = api.call("POST", f"/v1/opportunities/{job_id}/applicants/{meena_app['id']}/stage", EMPLOYER, {"stage": "hired"})
        check(st == 200 and a["stage"] == "hired" and a["thread_state"] == "in_progress", "hired: thread accepted through the accept path")
        st, after = api.call("GET", f"/v1/enquiries/{meena_app['id']}", BAKER)
        channels = [c.get("channel") for c in after.get("contact_actions", [])]
        check(st == 200 and channels and all("channel" in c and "available_now" in c for c in after["contact_actions"]),
              f"after hiring: the thread offers contact actions (enricher hook) ({channels})")
        check(after.get("can_contact_counterpart") is True and after.get("counterpart_can_contact") is True, "after hiring: both sides may contact each other")
        st, res = api.call("POST", f"/v1/opportunities/{job_id}/applicants/{meena_app['id']}/stage", EMPLOYER, {"stage": "declined"})
        check(st == 409 and code(res) == "stage_final", "hired is final")
        st, a = api.call("POST", f"/v1/opportunities/{job_id}/applicants/{ravi_app['id']}/stage", EMPLOYER, {"stage": "declined"})
        check(st == 200 and a["stage"] == "declined" and a["thread_state"] == "closed", "declined without typing anything; thread closed")
        check(a["contact_actions"] == [] and not a["contact_revealed"], "declined from the shortlist: number hidden")
        st, pthread = api.call("GET", f"/v1/enquiries/{ravi_app['id']}", EMPLOYER)
        check(st == 200 and pthread.get("contact_actions") == [], "declined: hidden in the poster's thread")
        st, res = api.call("POST", f"/v1/opportunities/{job_id}/applicants/{ravi_app['id']}/contact-attempts", EMPLOYER, {"channel": "call"})
        check(st == 400 and code(res) == "not_revealed", "a call tap after declining is refused")
        hidden = await db.fetchval(
            "SELECT count(*) FROM vyapar_integration.audit_events WHERE object_id = $1 AND action = 'applicant_contact_hidden'", ravi_app["id"])
        revealed = await db.fetchval(
            "SELECT count(*) FROM vyapar_integration.audit_events WHERE object_id = $1 AND action = 'applicant_contact_revealed'", ravi_app["id"])
        check(revealed == 2 and hidden == 2, f"every reveal and every hide is audited ({revealed} revealed, {hidden} hidden)")
        st, notes = api.call("GET", "/v1/notifications", HELPER, lang="hi")  # inbox renders in the reader's language
        mine = [n for n in notes if n["kind"] == "applicantDeclined" and ravi_app["id"] in (n.get("link") or "")] if st == 200 else []
        check(len(mine) == 1 and "आवेदन" in mine[0]["title"], "the declined applicant is notified in their own language (Hindi)")
        st, notes = api.call("GET", "/v1/notifications", BAKER)
        check(any(n["kind"] == "applicantHired" for n in notes), "the hired applicant is notified")
        st, res = api.call("POST", "/v1/enquiries", HELPER, {"opportunity_id": job_id, "message": "Please reconsider my application for the kitchen role."})
        check(st == 409 and code(res) == "already_declined", "a declined applicant cannot re-apply")
        st, page = api.call("GET", f"/v1/opportunities/{job_id}/applicants?stage=declined", EMPLOYER)
        check(st == 200 and page["total"] == 1 and page["stage_counts"] == {"new": 0, "shortlisted": 0, "hired": 1, "declined": 1}, "stage filter and counts")
        events = [r["event_type"] for r in await db.fetch(
            "SELECT event_type FROM vyapar_enquiries.outbox_event WHERE created_at >= $1 AND payload->>'opportunity_id' = $2 ORDER BY id", started_at, job_id)]
        check({"applicant.shortlisted", "applicant.hired", "applicant.declined"} <= set(events), f"applicant domain events in the outbox ({events})")

        # ------------------------------------------------------------ project
        print("\n== Freelance: structured proposal ==")
        st, res = api.call("POST", "/v1/opportunities", CLIENT, {
            "title": "Bookkeeping and GST returns for a wholesale textile shop",
            "type": "freelance", "location": "Charminar", "work_mode": "both", "response_method": "in_app", "source_segment": "community",
            "description": "Three months of bookkeeping in Tally and monthly GST returns for our wholesale textile shop in Charminar.",
            "required_capabilities": ["accounting", "gst_filing"],
            "structured": {"salary_min_paise": 100000},
        })
        check(st == 422 and code(res) == "structured_field_not_for_type", "a salary on a project is refused")
        st, proj = api.call("POST", "/v1/opportunities", CLIENT, {
            "title": "Bookkeeping and GST returns for a wholesale textile shop",
            "type": "freelance", "location": "Charminar", "work_mode": "both", "response_method": "in_app", "source_segment": "community",
            "description": "Three months of bookkeeping in Tally and monthly GST returns for our wholesale textile shop in Charminar.",
            "required_capabilities": ["accounting", "gst_filing"],
            "structured": {"duration": "1_3_months", "experience_level": "intermediate",
                           "screening_questions": [{"text": "Have you filed GST returns for a wholesale trader before?"}]},
        })
        check(st == 201, f"project draft ({st})")
        proj_id = proj["id"]
        opp_ids.add(proj_id)
        qid = proj["structured"]["screening_questions"][0]["id"]
        check(qid == "q1", "screening question gets a stable id")
        st, res = api.call("POST", f"/v1/opportunities/{proj_id}/publish", CLIENT)
        check(st == 422 and code(res) == "budget_required", "publish refused without a budget")
        st, proj = api.call("PATCH", f"/v1/opportunities/{proj_id}", CLIENT, {"structured": {"budget_type": "fixed", "budget_min_paise": 4000000, "budget_max_paise": 6000000}})
        check(st == 200 and proj["compensation"] == "Fixed price ₹40,000 to ₹60,000", f"budget compensation ({proj.get('compensation')})")
        # Publish runs the same hook over the stored row. Every write path now
        # refuses a fee, so only a draft saved before the rule existed can
        # carry one: simulate exactly that legacy row on this run's own draft.
        await db.execute("UPDATE vyapar_opportunities.opportunities SET requirements = 'Security deposit of ₹2,000 before starting' WHERE id = $1", proj_id)
        st, res = api.call("POST", f"/v1/opportunities/{proj_id}/publish", CLIENT)
        check(st == 422 and code(res) == "seeker_charge_not_allowed", "publish refused for a legacy draft asking a deposit (hook)")
        st, _ = api.call("PATCH", f"/v1/opportunities/{proj_id}", CLIENT, {"requirements": "Tally and GST portal experience"})
        st, proj = api.call("POST", f"/v1/opportunities/{proj_id}/publish", CLIENT)
        check(st == 200 and proj["state"] == "active", "project published")
        st, pview = api.call("GET", f"/v1/opportunities/{proj_id}", ACCOUNTANT)
        check(st == 200 and pview.get("seeker_protection") is None, "no seeker_protection notice on a project (employment only)")

        base = {"opportunity_id": proj_id, "message": "I keep books for four wholesale traders in Begum Bazaar and file their GST every month."}
        st, res = api.call("POST", "/v1/enquiries", ACCOUNTANT, base)
        check(st == 422 and code(res) == "bid_required", "a proposal needs a bid and a timeline")
        bid = {"bid_amount_paise": 4500000, "timeline_days": 90}
        st, res = api.call("POST", "/v1/enquiries", ACCOUNTANT, {**base, **bid, "milestones": [
            {"title": "Books set up in Tally", "amount_paise": 1500000, "due_days": 15},
            {"title": "Three months of GST returns", "amount_paise": 2000000, "due_days": 90}]})
        check(st == 422 and code(res) == "milestones_total", "milestones must add up to the bid")
        milestones = [{"title": "Books set up in Tally", "amount_paise": 1500000, "due_days": 15},
                      {"title": "Three months of GST returns", "amount_paise": 3000000, "due_days": 90}]
        st, res = api.call("POST", "/v1/enquiries", ACCOUNTANT, {**base, **bid, "milestones": milestones})
        check(st == 422 and code(res) == "screening_answers_required", "every screening question must be answered")
        st, res = api.call("POST", "/v1/enquiries", ACCOUNTANT, {**base, **bid, "milestones": milestones, "message": "Short"})
        check(st == 422 and code(res) == "message_too_short", "a proposal message still needs 20 characters")
        st, prop = api.call("POST", "/v1/enquiries", ACCOUNTANT, {**base, **bid, "milestones": milestones,
                                                                  "screening_answers": [{"question_id": qid, "answer": "Yes, monthly GSTR-1 and GSTR-3B for four wholesale shops."}]})
        if st == 201:
            enquiry_ids.add(prop["id"]); sent[ACCOUNTANT] += 1
        check(st == 201 and prop["action_type"] == "propose" and prop["bid_type"] == "fixed" and len(prop["milestones"]) == 2, f"structured proposal accepted ({st})")
        st, page = api.call("GET", f"/v1/opportunities/{proj_id}/applicants", CLIENT)
        item = page["items"][0] if st == 200 and page["items"] else {}
        check(item.get("bid_amount_paise") == 4500000 and item.get("timeline_days") == 90
              and item.get("screening_answers", [{}])[0].get("question", "").startswith("Have you filed"), "poster sees bid, timeline and answered question")
        check("value_fit" in item.get("match_signals", []) or item.get("match_score", 0) >= 60, f"a bid inside the budget scores well ({item.get('match_score')})")
        ps = item.get("skills_match") or {}
        check(ps.get("state") == "all" and ps.get("text") == "Has all 2 required skills" and item.get("missing_skills") == []
              and item["match_reasons"][:1] == [ps.get("text")], f"all skills: one reason ({ps.get('text')})")
        check("Bid is within your budget" in item["match_reasons"], f"reasons worded for the poster ({item['match_reasons']})")

        # ------------------------------------------------------------ local service
        print("\n== Local service ==")
        st, svc_opp = api.call("POST", "/v1/opportunities", CLIENT, {
            "title": "Leaking tap and bathroom pipe repair at our shop",
            "type": "local_service", "location": "Charminar", "work_mode": "on_site", "response_method": "in_app", "source_segment": "community",
            "description": "The wash-area tap and a pipe under the basin leak. Need a plumber to fix both.",
            "required_capabilities": ["plumbing"],
            "structured": {"urgency": "this_week", "budget_paise": 150000, "preferred_date": "2026-10-03"},
        })
        if st == 201:
            opp_ids.add(svc_opp["id"])
        check(st == 201 and svc_opp["compensation"] == "Budget ₹1,500" and svc_opp["structured"]["preferred_date"] == "2026-10-03", f"local service with date, budget and urgency ({st})")
        st, svc_opp = api.call("POST", f"/v1/opportunities/{svc_opp['id']}/publish", CLIENT)
        check(st == 200, "local service published (no money gate)")
        st, enq = api.call("POST", "/v1/enquiries", HELPER, {"opportunity_id": svc_opp["id"], "message": "I can come on Friday morning with parts for both repairs."})
        if st == 201:
            enquiry_ids.add(enq["id"]); sent[HELPER] += 1
        check(st == 201 and enq["action_type"] == "enquire", f"a response to a local service is stored as 'enquire' (was a CHECK violation) ({st})")

        # ------------------------------------------------------------ pay labels
        print("\n== Pay labels in the viewer's language ==")
        legacy = {"title": "Plumber for a leaking kitchen sink, 2BHK", "type": "local_service", "location": "Charminar",
                  "work_mode": "on_site", "response_method": "in_app", "source_segment": "community",
                  "description": "Kitchen sink trap is leaking. Please bring fittings and quote before starting work.",
                  "required_capabilities": ["plumbing"], "compensation": "Pay per visit"}
        st, lp = api.call("POST", "/v1/opportunities", CLIENT, legacy)
        if st == 201:
            opp_ids.add(lp["id"])
        st, lp_te = api.call("GET", f"/v1/opportunities/{lp['id']}", CLIENT, lang="te")
        check(st == 200 and lp_te["compensation_label"] == "ఒక్కో విజిట్‌కు చెల్లింపు" and lp_te["pay_period"] == "visit"
              and lp_te["compensation"] == "Pay per visit", f"'Pay per visit' localized in Telugu, stored text unchanged ({lp_te.get('compensation_label')})")
        st, lp2 = api.call("PATCH", f"/v1/opportunities/{lp['id']}", CLIENT, {"compensation": "from ₹300 per visit"})
        st, lp_hi = api.call("GET", f"/v1/opportunities/{lp['id']}", CLIENT, lang="hi")
        check(lp_hi.get("compensation_label") == "₹300 प्रति विज़िट से शुरू", f"'from ₹300 per visit' in Hindi ({lp_hi.get('compensation_label')})")
        yearly = {**legacy, "title": "Frontend developer (React) for a billing product", "type": "employment",
                  "description": "Build the customer-facing web app for our billing product with a small team.",
                  "required_capabilities": ["react", "software"], "work_mode": "both", "compensation": "₹9–14 LPA"}
        st, yp = api.call("POST", "/v1/opportunities", CLIENT, yearly)
        if st == 201:
            opp_ids.add(yp["id"])
        st, yp_te = api.call("GET", f"/v1/opportunities/{yp['id']}", CLIENT, lang="te")
        check(st == 200 and "LPA" not in yp_te["compensation_label"] and "లక్షలు" in yp_te["compensation_label"],
              f"yearly pay: no 'LPA', localized lakh ({yp_te.get('compensation_label')})")
        check(yp_te["pay_period"] == "year" and yp_te["pay_monthly_min_paise"] == 7500000 and yp_te["pay_monthly_max_paise"] == 11700000,
              f"yearly pay: monthly figures rounded to ₹1,000 ({yp_te['pay_monthly_min_paise']}, {yp_te['pay_monthly_max_paise']})")
        st, keep = api.call("PATCH", f"/v1/opportunities/{yp['id']}", CLIENT, {"compensation": "Best in industry"})
        st, keep = api.call("GET", f"/v1/opportunities/{yp['id']}", CLIENT, lang="te")
        check(keep["compensation_label"] == "Best in industry" and keep["pay_period"] is None, "unparseable free text stays as written")
        st, jte = api.call("GET", f"/v1/opportunities/{job_id}", BAKER, lang="te")
        check(jte["pay_period"] == "month" and jte["pay_monthly_min_paise"] == 1800000 and jte["pay_monthly_max_paise"] == 2400000
              and jte["compensation_label"].startswith("నెలకు"), f"structured salary: monthly facts and Telugu label ({jte['compensation_label']})")

        print("\n== Discover rows: skill categories are paid work ==")
        max_imp = await db.fetchval("SELECT coalesce(max(id), 0) FROM vyapar_commercial.impressions")
        st, rows = api.call("GET", "/v1/opportunities/feed/rows", "m_priya")
        shown = {i["id"] for r in rows.get("rows", []) for i in r["items"]}
        await db.execute("DELETE FROM vyapar_commercial.impressions WHERE id > $1 AND surface = 'feed' AND member_id IS NULL AND target_id = ANY($2::uuid[])",
                         max_imp, list(shown))  # the check's own impressions, not the owner's
        cat_rows = [r for r in rows.get("rows", []) if r["key"].startswith("category:")]
        bad = [(r["key"], i["title"]) for r in cat_rows for i in r["items"] if i["type"] not in ("employment", "freelance", "local_service")]
        check(st == 200 and not bad, f"no grant, programme or community post in a skill-category row ({bad or [r['key'] for r in cat_rows]})")
        grants = [i["title"] for r in cat_rows for i in r["items"] if "grant" in i["title"].lower() or "seed fund" in i["title"].lower()]
        check(not grants, "T-Hub grant / Startup India seed fund are not in Priya's Software & IT row")
        near = next((r for r in rows.get("rows", []) if r["key"] == "near_you"), None)
        near_bad = [i["title"] for i in (near or {}).get("items", []) if i["type"] not in ("employment", "freelance", "local_service")
                    and not set(i["required_capabilities"]) & {"software", "react", "python"}]
        check(not near_bad, f"a grant tagged with a merely related skill is not 'related work' in Near you ({near_bad})")
        keys = [r["key"] for r in rows.get("rows", [])]
        check(rows.get("has_personal_rows") is True and any(k in ("for_you", "near_you") or k.startswith("category:") for k in keys),
              f"sparse data still gives personal rows ({keys})")
        check((rows.get("viewer_categories") or [None])[0] == "software_it", f"viewer_categories puts the member's trade first ({rows.get('viewer_categories')})")
        expired_ids = {r["id"] for r in await db.fetch(
            "SELECT id::text FROM vyapar_opportunities.opportunities WHERE deadline < now()")}
        max_imp = await db.fetchval("SELECT coalesce(max(id), 0) FROM vyapar_commercial.impressions")
        st, rows2 = api.call("GET", "/v1/opportunities/feed/rows", "m_new")
        st3, results = api.call("GET", "/v1/opportunities/feed/results", "m_priya")
        shown2 = {i["id"] for r in rows2.get("rows", []) for i in r["items"]}
        result_ids = {i["id"] for i in results.get("items", [])} if st3 == 200 else set()
        await db.execute("DELETE FROM vyapar_commercial.impressions WHERE id > $1 AND member_id IS NULL AND target_id = ANY($2::uuid[])",
                         max_imp, list(shown2 | result_ids))
        check(rows2.get("has_personal_rows") is False, f"a member with no skills or place gets no 'picked for you' ({[r['key'] for r in rows2.get('rows', [])]})")
        leaked = (shown | shown2 | result_ids) & expired_ids
        check(not leaked, f"no past-deadline post in any row or result ({len(expired_ids)} past their date in data, leaked {len(leaked)})")
        starting = [i for r in rows.get("rows", []) + rows2.get("rows", []) if r["key"] == "starting_now" for i in r["items"]]
        check(all(not i["deadline_passed"] for i in starting), "Starting this week holds only posts still open")

        print("\n== Expired posts refuse applications ==")
        st, ex = api.call("POST", "/v1/opportunities", CLIENT, {**legacy, "title": "Tap washer replacement at our Charminar shop",
                                                                "compensation": "₹250 per visit", "deadline": "2026-12-31T18:00:00+05:30"})
        if st == 201:
            opp_ids.add(ex["id"])
        st, ex = api.call("POST", f"/v1/opportunities/{ex['id']}/publish", CLIENT)
        # time passes: the post's last date is now yesterday (the one thing a check cannot wait for)
        await db.execute("UPDATE vyapar_opportunities.opportunities SET deadline = now() - interval '1 day' WHERE id = $1", ex["id"])
        st, res = api.call("POST", "/v1/enquiries", HELPER, {"opportunity_id": ex["id"], "message": "I can replace the washer this evening, 30 minutes of work."})
        check(st == 400 and code(res) == "opportunity_expired" and "expired" in res["error"]["message"], f"Apply on an expired post is refused clearly ({code(res)})")
        st, exv = api.call("GET", f"/v1/opportunities/{ex['id']}", HELPER, lang="te")
        check(st == 200 and exv["deadline_passed"] is True, "the post reads as Expired (deadline_passed)")

        print("\n== Lifecycle: active -> expired, then renew ==")
        st, res = api.call("POST", "/v1/opportunities/jobs/expire", CLIENT)
        check(st == 200 and res.get("expired", 0) >= 1, f"the expiry pass runs ({res})")
        st, exv = api.call("GET", f"/v1/opportunities/{ex['id']}", CLIENT)
        check(exv["state"] == "expired" and exv["state_reason"] == "deadline_passed", f"the post's state is now expired ({exv['state']})")
        left = await db.fetchval("SELECT count(*) FROM vyapar_opportunities.opportunities WHERE state IN ('active','paused','stale') AND deadline < now()")
        check(left == 0, f"no active, paused or stale post is left past its date (seeded 103 and 111 included) ({left})")
        st, notes = api.call("GET", "/v1/notifications", CLIENT)
        mine = [n for n in notes if n["kind"] == "opportunityExpired" and ex["id"] in (n.get("link") or "")]
        check(len(mine) == 1 and mine[0]["title"].startswith("Your post expired") and "Renew" in (mine[0]["body"] or ""),
              f"the poster is told, with a way back ({mine[0]['title'] if mine else None})")
        ev = await db.fetchval("SELECT count(*) FROM vyapar_opportunities.outbox_event WHERE event_type = 'opportunity.expired' AND payload->>'id' = $1", ex["id"])
        check(ev == 1, "opportunity.expired domain event in the outbox")
        st, res = api.call("POST", "/v1/opportunities/jobs/expire", CLIENT)
        st, notes = api.call("GET", "/v1/notifications", CLIENT)
        check(len([n for n in notes if n["kind"] == "opportunityExpired" and ex["id"] in (n.get("link") or "")]) == 1, "a second pass changes nothing (idempotent)")
        st, res = api.call("POST", f"/v1/opportunities/{ex['id']}/renew", CLIENT, {"deadline": "2020-01-01T00:00:00+05:30"})
        check(st == 422 and code(res) == "deadline_in_past", "renew refuses a last date in the past")
        st, ren = api.call("POST", f"/v1/opportunities/{ex['id']}/renew", CLIENT)
        check(st == 200 and ren["state"] == "active" and ren["deadline_passed"] is False and ren["state_reason"] is None,
              f"renew brings it back with a new last date ({ren.get('deadline')})")
        st, app2 = api.call("POST", "/v1/enquiries", HELPER, {"opportunity_id": ex["id"], "message": "I can replace the washer this evening, 30 minutes of work."})
        if st == 201:
            enquiry_ids.add(app2["id"]); sent[HELPER] += 1
        check(st == 201, f"after renewing, applying works again ({st})")

        # ------------------------------------------------------------ compat
        print("\n== Existing behaviour ==")
        listing_id = await db.fetchval(
            "SELECT id::text FROM vyapar_listings.listings WHERE owner_id = $1 AND state IN ('active_verified','active_unverified') ORDER BY created_at LIMIT 1", BAKER)
        st, res = api.call("POST", "/v1/enquiries", OUTSIDER, {"listing_id": listing_id, "message": "Hi"})
        check(st == 422 and code(res) == "message_too_short", "a short enquiry on a listing is still refused")
        st, mine = api.call("GET", "/v1/opportunities/mine", EMPLOYER)
        check(st == 200 and any(o["id"] == job_id and "structured" in o for o in mine), "listMyOpportunities carries the structured block")
    finally:
        await cleanup(db, opp_ids, enquiry_ids, sent, started_at)
        await db.close()

    failed = [label for ok, label in RESULTS if not ok]
    print(f"\n{len(RESULTS) - len(failed)}/{len(RESULTS)} checks passed")
    for label in failed:
        print("  failed:", label)
    return 1 if failed else 0


async def cleanup(db: asyncpg.Connection, opp_ids: set[str], enquiry_ids: set[str], sent: Counter, started_at) -> None:
    print("\n== Cleanup ==")
    # Enquiries this run may have created but failed to record (defensive).
    if opp_ids:
        enquiry_ids.update(r["id"] for r in await db.fetch(
            "SELECT id::text FROM vyapar_enquiries.enquiries WHERE opportunity_id = ANY($1::uuid[])", list(opp_ids)))
    ids = sorted(opp_ids | enquiry_ids)
    if not ids:
        print("  nothing to clean")
        return
    patterns = [f"%{i}%" for i in ids]
    n: dict[str, str] = {}
    async with db.transaction():
        n["notifications"] = await db.execute(
            "DELETE FROM vyapar_integration.notifications WHERE created_at >= $1 AND (link LIKE ANY($2) OR params::text LIKE ANY($2) OR idempotency_key LIKE ANY($2))",
            started_at, patterns)
        n["webhook_deliveries"] = await db.execute(
            "DELETE FROM vyapar_integration.webhook_deliveries WHERE created_at >= $1 AND payload::text LIKE ANY($2)", started_at, patterns)
        for table in ("vyapar_enquiries.outbox_event", "vyapar_opportunities.outbox_event", "vyapar_reviews.outbox_event"):
            n[table] = await db.execute(f"DELETE FROM {table} WHERE created_at >= $1 AND payload::text LIKE ANY($2)", started_at, patterns)
        n["review_invites"] = await db.execute(
            "DELETE FROM vyapar_reviews.review_invites WHERE interaction_kind = 'enquiry' AND interaction_id = ANY($1::uuid[])", list(enquiry_ids))
        n["audit_events"] = await db.execute(
            "DELETE FROM vyapar_integration.audit_events WHERE at >= $1 AND (object_id LIKE ANY($2) OR details::text LIKE ANY($2))", started_at, patterns)
        n["impressions"] = await db.execute("DELETE FROM vyapar_commercial.impressions WHERE target_id = ANY($1::uuid[])", list(opp_ids))
        n["analytics_events"] = await db.execute("DELETE FROM vyapar_analytics.analytics_events WHERE at >= $1 AND object_id = ANY($2::text[])", started_at, ids)
        n["enquiries"] = await db.execute("DELETE FROM vyapar_enquiries.enquiries WHERE id = ANY($1::uuid[])", list(enquiry_ids))
        n["opportunities"] = await db.execute("DELETE FROM vyapar_opportunities.opportunities WHERE id = ANY($1::uuid[])", list(opp_ids))
        for member, count in sent.items():
            key = f"enquiry:{member}:day"
            await db.execute(
                """UPDATE vyapar_platform.rate_limit_counter SET hit_count = greatest(hit_count - $2, 0)
                    WHERE rate_limit_key = $1 AND window_start = (SELECT max(window_start) FROM vyapar_platform.rate_limit_counter WHERE rate_limit_key = $1)""",
                key, count)
            await db.execute("DELETE FROM vyapar_platform.rate_limit_counter WHERE rate_limit_key = $1 AND hit_count = 0", key)
    for k, v in n.items():
        print(f"  {k}: {v}")
    tables = await db.fetch("SELECT schemaname, tablename FROM pg_tables WHERE schemaname LIKE 'vyapar\\_%' ORDER BY 1, 2")
    leftovers = []
    for t in tables:
        count = await db.fetchval(f'SELECT count(*) FROM "{t["schemaname"]}"."{t["tablename"]}" x WHERE x::text LIKE ANY($1)', patterns)
        if count:
            leftovers.append(f"{t['schemaname']}.{t['tablename']}={count}")
    check(not leftovers, f"no leftover rows mention the test ids ({', '.join(leftovers) or 'clean'})")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--api", default=os.environ.get("VYAPAR_CHECK_API_BASE"), help="Base URL of a running Vyapar API (or VYAPAR_CHECK_API_BASE)")
    args = parser.parse_args()
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")  # rupee sign, Hindi and Telugu on a Windows console
    if not args.api:
        parser.error("--api (or VYAPAR_CHECK_API_BASE) is required")
    sys.exit(asyncio.run(main(args.api)))
