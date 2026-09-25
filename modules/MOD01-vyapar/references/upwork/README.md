# Real Upwork app screenshots — product owner reference (2026-09-17)

Real phone screenshots the product owner shared directly, saved here so any agent can `Read` them
as ground truth for Upwork's actual screens instead of relying on written descriptions. WorkIndia
screenshots were attempted but failed to upload — none are available yet; do not fabricate a
WorkIndia reference in their place, ask for them again if needed.

- `01-data-notice.jpg` — Upwork's data-collection consent banner: logo, title, one short paragraph,
  a single primary action ("Learn More"), two secondary text links (Privacy Policy, Cookie Policy),
  "Powered by Transcend" attribution. Minimal, not a full-screen blocker — sits as a bottom sheet
  over the app, dismissible with an X.
- `02-my-proposals-loading.jpg` — bottom nav is exactly 5 items: **Jobs, Proposals, Contracts,
  Messages, Alerts** (Proposals is the active tab here, bold + underline). Top bar: small circular
  avatar (left), screen title, a settings gear (right). Tabs under the title: **Active / Referrals /
  Archived**.
- `03-contracts.jpg` — Contracts screen: "Earnings available now: $0.00" as the first thing shown,
  with a "..." expand control. "Active contracts" section with a real empty state (heading + one
  sentence + a single primary button "Search for new projects"). Below it, a second distinct card
  — "Direct contracts" — explaining a related but different capability ("Create simple contracts
  with your non-Upwork clients... Create a direct contract"). Two clearly separated empty/secondary
  states stacked, not merged into one.
- `04-my-proposals-tabs.jpg` — Active proposals tab reveals a SECOND row of state filters:
  **Offers (0) / Invites (0) / Discussing (0) / Submitted (0)** — each with a live count in
  parentheses. Empty state here uses a friendly folder illustration + bold "You have no offers" +
  nothing else (no CTA needed on this particular empty state, unlike Contracts' empty state which
  does have one).

## What this is useful for in Vyapar

- The **Active / Referrals / Archived** + **Offers / Invites / Discussing / Submitted** two-level
  tab pattern is the real precedent for how Vyapar's own Enquiries list (Sent/Received) could
  expose enquiry state as a second row of count-badged filter chips instead of one flat list —
  relevant to FR23's Open/Awaiting Response/In Progress/Resolved/Closed states.
  Cite this file (not memory) if implementing that.
- Every empty state here follows the same shape: one friendly heading, one short explanatory
  sentence, at most one primary action — and NOT every empty state needs a CTA (Submitted-proposals
  empty state has none; Active-contracts empty state has one relevant CTA). Match this restraint
  rather than adding a button to every empty state reflexively.
- The bottom nav is 5 flat, always-visible, labelled items — worth noting as a genuine Upwork
  precedent, though it does NOT override the product owner's own explicit 2026-09-14 decision that
  Vyapar itself uses a floating command hub instead of a boxed tab bar; it is a comparable data
  point for research, not an instruction to change Vyapar's nav pattern back.
