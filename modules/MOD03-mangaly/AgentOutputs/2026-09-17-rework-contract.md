# Mangaly rework contract — 2026-09-17

Owner direction (verbatim intent): Mangaly must be a mobile-first web app that is ALSO a real desktop web app;
styling must become classy, elegant, easy; roles are relations to a particular candidate, a person can hold several
at once; only two things vary by role — profile-viewing lens and messaging; everything else is generic for every role;
the bar is a top mature matrimony app, not a POC.

This file is the shared contract between the backend and frontend build agents. Both must follow it exactly.

## 1. Identity payload — `GET /auth/me`

```json
{
  "account_id": "uuid",
  "display_name": "Lakshmi Reddy",
  "preferred_language": "en",
  "expires_at": "iso",
  "own_profile": { "profile_id": "uuid", "name": "Ananya Reddy", "looking_for": "groom", "primary_photo_url": "/media/..", "discoverable": true } | null,
  "circles": [
    { "candidate_profile_id": "uuid", "candidate_name": "Ananya Reddy", "relationship": "parent", "looking_for": "groom", "primary_photo_url": "/media/..", "member_count": 4 }
  ],
  "counts": { "unread_messages": 0, "pending_requests": 0, "unread_notifications": 0 }
}
```
Relationship vocabulary: `parent | sibling | relative | guardian`. `own_profile` present ⇒ the account is also a candidate.
A `context` is either `{kind:"self", profile_id}` or `{kind:"family", candidate_profile_id, relationship}`.
Every context-scoped endpoint accepts `?for_candidate=<candidate_profile_id>`; omitted ⇒ self. The server validates
that the caller is an active circle member for that candidate (existing `family_info` grant).

## 2. What varies by role (ONLY these)

1. **Profile lens.** `GET /profile/view/{id}?lens=story|biodata`. `story` = Hinge-style interleaved photos + prompts +
   short sections (for a candidate viewing). `biodata` = structured sections in conventional order: Basics, Religion &
   community, Education & career, Family, Lifestyle, Horoscope, About, Partner expectations (for a family member viewing).
   Both lenses respect the same disclosure rules (name/contact/extra photos after acceptance). The server returns the
   same underlying fields; the shape differs (`blocks[]` for story, `sections[]` for biodata).
2. **Messaging.** Two conversation kinds on a connection: `candidate` (the two candidates only, exists on accept — unchanged)
   and `family` (both candidates + active circle members of both sides; opened when EITHER candidate taps
   "Involve my family" on an accepted connection; the other side sees it and can join with one tap). Family members can
   only ever be in `family` conversations. Both kinds share one thread UI.

Everything else — Home, Discover, filters, shortlist, interests, Circle create/invite/manage, notifications, settings —
works identically in every context. Family members MAY send a connection request on behalf of their candidate
(`on_behalf_of_profile_id`); this reverses DEC-V1-019 by owner instruction. The request records `acting_account_id`
and the recipient sees "Sent by Ananya's mother".

## 3. New/changed endpoints (backend implements, frontend consumes)

- `GET /auth/me` — as above.
- `GET /profile/view/{id}?lens=story|biodata&for_candidate=`.
- `PATCH /profile/{category}` — new categories/keys: `basics` gains `height_cm`, `mother_tongue`, `marital_status`, `have_children`;
  `community` (new): `gotra`, `sub_community`, `native_place`; `education_career` gains `income_band`, `employer`, `college`;
  `family` (new): `family_type`, `family_values`, `father_occupation`, `mother_occupation`, `brothers`, `sisters`, `lives_with_parents`, `about_family`;
  `horoscope` gains `manglik`, `rashi`, `nakshatra`, `birth_time`, `birth_place`.
- `GET /discovery/search` — new filters: `height_min/max`, `gotra[]`, `sub_community[]`, `profession[]`, `income_band[]`,
  `mother_tongue[]`, `manglik`, `q` (uses existing tsvector), `sort=relevance|newest|recently_active`; response includes `total`.
- `POST/DELETE /shortlist/{profile_id}`, `GET /shortlist` (context-scoped).
- `GET /connection/incoming|sent` — already exist; add `?for_candidate=`; add `POST /connection/{id}/withdraw`.
- `POST /safety/block/{profile_id}`, `DELETE /safety/block/{profile_id}`, `POST /safety/report` `{profile_id, reason, details}`.
  Blocked profiles vanish from both sides' discovery and lists.
- `GET /notifications?for_candidate=` → `[{id, kind, title, body, link, created_at, read_at}]`; `POST /notifications/read`.
  Kinds: `request_received`, `request_accepted`, `invitation_received`, `suggestion_received`, `family_conversation_opened`, `note_forwarded`.
- `POST /home-circle/invite` — allowed for any signed-in account; paths per FR007 (candidate→family, family→candidate by phone, member→relative).
  A member without an own profile may invite a candidate: the invite then targets the candidate's account.
- `POST /conversations/{connection_id}/family/open`, `GET /conversations?for_candidate=` lists both kinds with `kind`, `unread_count`, `last_message`.

Migrations: raw SQL files continuing the existing numbering in `07a-db-implementation/migrations/` (030+), idempotent,
applied by the backend agent to localhost:5433/mangaly. RLS policies for new tables follow existing patterns.

## 4. Seed data (backend agent)

Realistic Khatri-community people across Hyderabad, Bengaluru, Chennai, Mumbai, Delhi, Pune, Vijayawada, Visakhapatnam:
~40 candidates (balanced bride/groom), each with 3–5 photos (downloaded into `mangaly-service/.local-media/` as now, sourced
from randomuser.me / picsum), full biodata incl. gotra/height/income/family, 2–3 prompts, partner preferences.
At least: one person who is BOTH a candidate and a sibling in another candidate's circle; one parent in two circles;
Ananya Reddy keeps her identity; `mangaly-parent` (Lakshmi Reddy) stays in Ananya's circle; ~10 accepted connections
with candidate conversations; 3 family conversations; shortlists; a few incoming requests for Ananya and Asha.
Seeds are idempotent and never delete the platform personas.

## 5. Frontend contract (frontend agent)

Breakpoints: `sm <640`, `md ≥768` (two columns where it helps), `lg ≥1024` (left sidebar nav 260px; content max 1120px; bottom bar hidden).
Design system (see research 2026-09-17): paper/ivory light canvas, charcoal ink dark canvas, ONE accent (deep vermilion "sindoor"),
serif display face for names and headings (Fraunces via next/font), Plus Jakarta Sans for UI, hairline borders, tonal
surfaces, no gradients/glass/glow/shadows, 200ms ease-out motion tokens, skeletons for every list.
Context switcher lives in the sidebar (desktop) and the top bar (mobile) and is visible on every screen.
i18n: every string in en/hi/te.

## 6. Owner clarification (2026-09-17, after the contract was first written)

"A parent in the Home Circle must be able to send a request, but that doesn't mean you forget that the parent is also a
user; his relation may vary with others, and he still can search users and add them into a circle." Therefore:

- **Every account is a full user first.** An account with no own profile and no circles still gets Home, Discover,
  Circle (create by inviting), Shortlist, Messages (family conversations it is party to), Notifications, Settings.
  Nothing routes such an account away from Home; nothing shows it a thinner screen.
- **Discover without a context.** `GET /discovery/search` with no `for_candidate` and no own profile is allowed in
  *browse mode*: the caller must pass `looking_for=bride|groom` explicitly (the UI asks once, remembers per device);
  results are the normal discoverable set; cards offer "Save" and "Suggest to…"/"Invite to circle"; "Send interest"
  is offered only inside a candidate context (self or family).
- **People search for circles.** `GET /home-circle/people?q=` searches ForKhatri members (via the identity service's
  existing member lookup, by name or phone) so anyone can find a person and invite them with a relationship. Response:
  `[{account_id, display_name, phone_masked, has_profile}]`. The invite form is available in every context and to
  accounts with no context.
- **Relationship is per membership.** The same account can be `parent` in one circle and `relative` in another; the
  `/auth/me.circles[]` list carries one entry per membership with its own `relationship`. Never store a role on the account.
- **On-behalf request** is an *additional* capability granted by membership (`parent|guardian|sibling|relative` alike),
  not a substitute for the member's own generic capabilities.
