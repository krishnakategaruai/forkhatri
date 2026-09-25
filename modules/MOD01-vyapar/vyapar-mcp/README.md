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
| `listings:write` | `save_profile`, `unsave_profile` |
| `enquiries:write` | `create_enquiry`, `reply_to_enquiry` |
| `notifications:write` | `mark_notification_read` |

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

Every write sends an `Idempotency-Key`, so an agent that retries after a timeout cannot post twice. Read tools are marked read-only, so clients can auto-approve them. Tools that contact another person tell the agent to confirm with the member first. Those tools are `create_enquiry`, `reply_to_enquiry` and `post_opportunity`.

When the API refuses a call, the tool returns an error that includes Vyapar's stable error code, for example `Vyapar refused (403 scope_required): ...`.
