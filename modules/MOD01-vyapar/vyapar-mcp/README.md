# vyapar-mcp

A [Model Context Protocol](https://modelcontextprotocol.io) server that lets an AI agent work on Vyapar for one member. Claude Desktop, Claude Code and any other MCP client can use it.

- It talks to Vyapar **only through the public REST API**, using that member's personal access token.
- It never reads the database, and it shares no code with `vyapar-service`. You can run it on any machine that can reach the API.
- The agent can do exactly what the token's scopes allow. The API refuses everything else, and it audits every write with the token's id.

## 1. Create a personal access token

Tokens are created from the member's own session. A token cannot create another token.

```bash
curl -X POST http://localhost:8011/v1/integrations/tokens \
  -H "X-Dev-Member-Id: m_krishna" \
  -H "Content-Type: application/json" \
  -d '{"name": "Claude Desktop", "scopes": ["read", "opportunities:write", "enquiries:write"], "expires_in_days": 30}'
```

- The `-H "X-Dev-Member-Id: ..."` header only works in development. In a real deployment the member makes this call from their signed-in session.
- The response contains `token` (`vyp_...`) **once**. Store it now.
- To list your tokens, call `GET /v1/integrations/tokens`.
- To revoke a token, call `DELETE /v1/integrations/tokens/{id}`. Revocation takes effect on the next request.

| Scope | Allows |
|---|---|
| `read` | every read tool |
| `opportunities:write` | `save_opportunity`, `unsave_opportunity`, `mark_not_interested`, `post_opportunity`, `publish_opportunity` |
| `opportunities:write` (also) | `save_search`, `delete_saved_search`, `set_applicant_stage`, `draft_opportunity`, `check_seeker_charge` |
| `listings:write` | `save_profile`, `unsave_profile`, `update_contact_preferences`, `upsert_listing_packages`, `request_listing_package` |
| `enquiries:write` | `create_enquiry`, `reply_to_enquiry`, `accept_enquiry`, `close_enquiry`, `withdraw_enquiry`, `record_contact_attempt`, `record_opportunity_contact_attempt` |
| `partnerships:write` | `create_partnership_request`, `respond_partnership` |
| `reviews:write` | `submit_review`, `answer_paid_on_time` |
| `notifications:write` | `mark_notification_read` |
| `contracts:write` | `create_contract`, `fund_milestone`, `approve_milestone` |

`fund_milestone` only opens a checkout: it returns a `checkout_url` the member opens to pay, and the milestone becomes funded only when that payment is confirmed. `buy_boost` is refused for every access token (`not_available_to_tokens`), because boosts and plans stay with the member in person.

Some actions stay with the member in person, whatever scopes a token holds:
- payments and plans;
- privacy and account deletion;
- verification documents;
- reports and appeals;
- operator tools;
- managing tokens and webhooks.

## 2. Install

```bash
cd modules/MOD01-vyapar/vyapar-mcp
python -m venv .venv
.venv/Scripts/python -m pip install -r requirements.txt      # Windows
# .venv/bin/python -m pip install -r requirements.txt        # macOS / Linux
```

It needs Python 3.11 or later and the official `mcp` SDK, version 2.2 or later.

## 3. Configure

| Variable | Meaning | Default |
|---|---|---|
| `VYAPAR_API_URL` | Base URL of the Vyapar API | `http://localhost:8011` |
| `VYAPAR_TOKEN` | The personal access token (`vyp_...`) | none (required) |
| `VYAPAR_LANGUAGE` | `en`, `hi` or `te`. Localizes labels and error messages. | `en` |

### Claude Desktop

Add this to `claude_desktop_config.json`:
- on Windows, the file is at `%APPDATA%\Claude\claude_desktop_config.json`;
- on macOS, it is at `~/Library/Application Support/Claude/claude_desktop_config.json`.

```json
{
  "mcpServers": {
    "vyapar": {
      "command": "C:\\Users\\you\\ForKhatri\\modules\\MOD01-vyapar\\vyapar-mcp\\.venv\\Scripts\\python.exe",
      "args": ["-m", "vyapar_mcp"],
      "cwd": "C:\\Users\\you\\ForKhatri\\modules\\MOD01-vyapar\\vyapar-mcp",
      "env": {
        "VYAPAR_API_URL": "http://localhost:8011",
        "VYAPAR_TOKEN": "vyp_paste_your_token_here",
        "VYAPAR_LANGUAGE": "en"
      }
    }
  }
}
```

### Claude Code

```bash
claude mcp add vyapar \
  --env VYAPAR_API_URL=http://localhost:8011 \
  --env VYAPAR_TOKEN=vyp_paste_your_token_here \
  -- /path/to/vyapar-mcp/.venv/Scripts/python.exe -m vyapar_mcp
```

You can also put it in a project's `.mcp.json`:

```json
{
  "mcpServers": {
    "vyapar": {
      "command": "/path/to/vyapar-mcp/.venv/Scripts/python.exe",
      "args": ["-m", "vyapar_mcp"],
      "env": { "VYAPAR_API_URL": "http://localhost:8011", "VYAPAR_TOKEN": "vyp_..." }
    }
  }
}
```

## Tools

| Tool | What it does | API call |
|---|---|---|
| `whoami` | Which member the server acts for, and the token's scopes | `GET /v1/integrations/me` |
| `get_opportunity_feed` | Personalised feed in sections (for you, explore, community, public). Takes an optional skills filter. | `GET /v1/opportunities/feed` |
| `get_feed_section` | Every item in one feed section | `GET /v1/opportunities/feed/section/{key}` |
| `get_opportunity` | Full opportunity detail | `GET /v1/opportunities/{id}` |
| `why_this_opportunity` | Why it was recommended | `GET /v1/opportunities/{id}/why` |
| `list_similar_opportunities` | Similar live opportunities | `GET /v1/opportunities/{id}/similar` |
| `list_matching_profiles` | Profiles that match an opportunity | `GET /v1/opportunities/{id}/matching-profiles` |
| `list_my_opportunities` | The member's own postings | `GET /v1/opportunities/mine` |
| `save_opportunity` / `unsave_opportunity` | Bookmark an opportunity, or remove the bookmark | `POST` / `DELETE /v1/opportunities/{id}/save` |
| `mark_not_interested` | Hide an opportunity, with a reason | `POST /v1/opportunities/{id}/not-interested` |
| `post_opportunity` | Create an opportunity and, optionally, confirm and publish it | `POST /v1/opportunities`, then `/confirm` and `/publish` |
| `publish_opportunity` | Publish a draft | `POST /v1/opportunities/{id}/publish` |
| `create_enquiry` | Apply to an opportunity or enquire with a profile | `POST /v1/enquiries` |
| `list_enquiries` / `get_enquiry` | Enquiry conversations | `GET /v1/enquiries/mine`, `GET /v1/enquiries/{id}` |
| `reply_to_enquiry` | Send a message in a conversation | `POST /v1/enquiries/{id}/messages` |
| `get_activity` | Saved items, applications and postings in one view | `GET /v1/activity` |
| `list_notifications` / `get_unread_notification_count` / `mark_notification_read` | The member's notification inbox | `/v1/notifications...` |
| `search_profiles` | Search businesses and professionals, with a `kind` filter | `GET /v1/listings/search` |
| `get_profile` | Full profile | `GET /v1/listings/{id}` |
| `list_similar_profiles` | Similar profiles | `GET /v1/listings/{id}/similar` |
| `list_profile_reviews` | Published reviews | `GET /v1/listings/{id}/reviews` |
| `list_my_profiles` | The member's own profiles | `GET /v1/listings/mine` |
| `save_profile` / `unsave_profile` | Save a profile, or remove it from the saved list | `POST` / `DELETE /v1/listings/{id}/save` |
| `search_opportunities` | Feed with real filters (q, skills, type, work_mode, radius_km, availability, and an optional current `lat`/`lng` used for distance only, never stored) and sort (relevance, distance, freshness, verified_first, salary_high). Cards carry `distance_km`, `poster_badges`, `seeker_protection`. | `GET /v1/opportunities/feed` |
| `save_search` / `list_saved_searches` / `delete_saved_search` | Saved searches, optionally with alerts | `/v1/opportunities/saved-searches` |
| `accept_enquiry` / `close_enquiry` / `withdraw_enquiry` | Enquiry lifecycle | `POST /v1/enquiries/{id}/accept`, `/close`, `/withdraw` |
| `get_contact_actions` | Call / WhatsApp actions after acceptance, per the other person's call hours, days, daily cap and channels | `GET /v1/enquiries/{id}/contact-actions` |
| `record_contact_attempt` | Record a call or WhatsApp now (counts toward the callee's daily cap) | `POST /v1/enquiries/{id}/contact-attempts` |
| `get_opportunity_contact_actions` | Call / WhatsApp the poster before applying, when the post allows it (`allow_precall`) | `GET /v1/opportunities/{id}/contact-actions` |
| `record_opportunity_contact_attempt` | Record a pre-accept tap: counts toward the poster's cap, notifies them, opens an application | `POST /v1/opportunities/{id}/contact-attempts` |
| `get_contact_preferences` / `update_contact_preferences` | The member's own contact rules, or one listing's overrides | `GET`/`PATCH /v1/listings/contact-preferences`, `/v1/listings/{id}/contact-preferences` |
| `list_partnerships` / `get_partnership` | Partnership requests | `GET /v1/partnership-requests/mine`, `/{id}` |
| `create_partnership_request` / `respond_partnership` | Send, accept, decline, withdraw, restrict or close | `POST /v1/partnership-requests`, `/{id}/{action}` |
| `list_review_invites` / `submit_review` | Review a completed interaction | `GET /v1/reviews/invite/{kind}/{id}`, `POST /v1/reviews` |
| `get_member_badges` | Count-based badges, no star score | `GET /v1/members/{id}/badges` |
| `list_boost_products` / `buy_boost` | Boost packs and preparing a boost order | `GET /v1/promotions/options`, `POST /v1/promotions`, `/confirm-purchase` |
| `list_listing_packages` / `upsert_listing_packages` / `request_listing_package` | Basic / standard / premium service packages | `/v1/listings/{id}/packages...` |
| `check_seeker_charge` | Pre-check a draft against "nobody charges job seekers" | `POST /v1/opportunities/seeker-charge-check` |
| `list_applicants` / `set_applicant_stage` | Applicant pipeline on the member's opportunity | `GET /v1/opportunities/{id}/applicants`, `POST .../applicants/{enquiry_id}/stage` |
| `draft_opportunity` / `get_ai_shortlist` | AI draft from a plain brief; AI-ranked applicants | `POST /v1/ai/draft-opportunity`, `GET /v1/opportunities/{id}/ai-shortlist` |
| `create_contract` / `fund_milestone` / `approve_milestone` | Milestone contracts | `POST /v1/contracts`, `.../milestones/{mid}/fund`, `.../approve` |
| `check_scam_shield` | Pre-check a post, a reply to an applicant or a package for any charge on applicants (en/hi/te/Hinglish) | `POST /v1/trust/scam-check` |
| `list_paid_on_time_questions` / `answer_paid_on_time` | "Were you paid on time?" for the person who was paid | `GET /v1/paid-on-time/asks`, `POST .../{id}/answer` |
| `get_paid_on_time` | A payer's "Paid on time: 12 of 13" (after 3 answers) | `GET /v1/members/{id}/paid-on-time` |
| `list_my_restrictions` | What is restricted, why, and the appeal path | `GET /v1/me/restrictions` |
| `get_close_check` | Applicants still waiting before a post is closed | `GET /v1/opportunities/{id}/close-check` |
| `list_profession_rules` | Council rules on advertising (advocates, architects, CAs) | `GET /v1/profession-rules` |

Every write sends an `Idempotency-Key`, so an agent that retries after a timeout cannot post twice. Read tools are marked read-only, so clients can auto-approve them. Tools that contact another person tell the agent to confirm with the member first. Those tools are `create_enquiry`, `reply_to_enquiry`, `post_opportunity`, `create_partnership_request`, `respond_partnership`, `submit_review`, `request_listing_package` and `create_contract`.

When the API refuses a call, the tool returns an error that includes Vyapar's stable error code, for example `Vyapar refused (403 scope_required): ...`.
