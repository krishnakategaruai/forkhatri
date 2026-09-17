# ForKhatri: shared instructions for every Claude session

## Browser testing: one Chrome per workstream

Several sessions work on this repository at the same time. Each one has its own
Chrome DevTools MCP server with a separate Chrome profile, so no session blocks or
closes another session's browser.

| You are working on | Use only these tools | Chrome profile |
|---|---|---|
| Platform, entrance, identity service, deployment, or coordinating across modules | `mcp__chrome-devtools-main__*` | `forkhatri-main-profile` |
| `modules/MOD01-vyapar/` | `mcp__chrome-devtools-vyapar__*` | `forkhatri-mod01-vyapar-profile` |
| `modules/MOD02-milavn/` | `mcp__chrome-devtools-milavn__*` | `forkhatri-mod02-milavn-profile` |
| `modules/MOD03-mangaly/` | `mcp__chrome-devtools-mangaly__*` | `forkhatri-mod03-mangaly-profile` |
| `modules/MOD04-counsel/` | `mcp__chrome-devtools-counsel__*` | `forkhatri-mod04-counsel-profile` |
| `modules/MOD05-dashboard/` | `mcp__chrome-devtools-dashboard__*` | `forkhatri-mod05-dashboard-profile` |
| `modules/MOD06-payment-services/` | `mcp__chrome-devtools-payments__*` | `forkhatri-mod06-payment-services-profile` |
| `modules/MOD07-loans-finance/` | `mcp__chrome-devtools-finance__*` | `forkhatri-mod07-loans-finance-profile` |

Profiles live in `C:\Users\krish\.cache\chrome-devtools-mcp\`.

Rules:
- Use only your own row's tools, even if other rows' tools are available in your session.
- Never close, kill or restart a Chrome process you did not start. If your browser reports "already running for <profile>", check which profile it names. If the profile is not yours, you are using the wrong server.
- Each profile keeps its own ForKhatri sign-in (see "Development sign-in for testing" below). Sign in once with a development member (see `docs/ParentApp/09-implementation.md`) and it lasts 30 days. Automated tests must not use "Sign out on all devices" on the product owner's account (`+919999900001`).

## Development sign-in for testing

Every module uses the one ForKhatri sign-in; no module builds its own login.
Switching person takes one tap and no password:

- **People testing by hand:** open http://localhost:3100, then avatar → "Act as (development)". Signed out, use the small "Development: act as…" link on the sign-in screen.
- **Personas:**
  - `asha`: data in Mangaly and Milavn.
  - `new-member`: no module data at seed time.
  - `mangaly-family`: Vikram Rao.
  - `mangaly-parent`: Lakshmi Reddy, Ananya Reddy's mother, not a candidate.
  - `milavn-moderator`.
  - `krishna`: the product owner's account, for people only, never automated tests.
- **Automated tests:** don't drive the sign-in screens. Run `platform/identity-service/.venv/Scripts/python platform/identity-service/scripts/dev_session.py <persona> --storage-state <file>` for a Playwright storageState, or `--cookie-header` for curl.
- **Sign-out in tests:** use normal sign-out, never "Sign out on all devices" on a shared persona.
- **Password sign-in:** still available for end-to-end checks: `+919800000001` or `+919999900001`, password `ForKhatri-dev-2026`.
