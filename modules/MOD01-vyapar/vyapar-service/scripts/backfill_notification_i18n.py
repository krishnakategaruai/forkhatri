"""Backfill notification templates so existing inbox rows render in the reader's language.

[IMP-B, owner 2026-09-30] Notifications used to be stored as text rendered
once, in whatever language the recipient row said at write time (usually
English). New rows carry their template (params._i18n) or all three
languages (params._texts, migration 027). This one-off pass gives existing
rows a template spec wherever every placeholder can be filled truthfully:

  * strong_match           -> notifications.strongMatch, {title} from the post
  * saved_search_match     -> notifications.savedSearchMatch, {count} from the ids, {name} from the stored title
  * digest                 -> notifications.digest, {count} from params
  * verification_reminder  -> notifications.verificationReminder, {name} from the listing
  * trust & safety notices -> their own keys; action/reason/outcome/decision codes become translatable values
  * any other row whose template_id is a notifications.* key and whose params
    already hold every placeholder.

Rows that can't be filled truthfully keep their stored text (the renderer
falls back to it). Idempotent: rows that already have _i18n or _texts are
skipped. Runs as the owner role (it writes every member's rows).

    .venv/Scripts/python scripts/backfill_notification_i18n.py [--dry-run]
"""
from __future__ import annotations

import asyncio
import json
import os
import re
import sys
from pathlib import Path

import asyncpg

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.i18n import _catalog  # noqa: E402

OWNER_DSN = os.environ.get("VYAPAR_OWNER_DSN", "postgres://vyapar_owner:vyapar_owner_dev_password@localhost:5433/vyapar")
GRIEVANCE = "grievance@forkhatri.example"
TEMPLATE_KEY = {"strong_match": "strongMatch", "saved_search_match": "savedSearchMatch", "verification_reminder": "verificationReminder"}
TRUST_KEYS = {"action": "trust_safety.action.", "reason": "trust_safety.reasonCode.",
              "outcome": "reviews.outcome.", "decision": "trust_safety.appealDecision."}
PLACEHOLDER = re.compile(r"\{(\w+)\}")


def placeholders(key: str) -> set[str]:
    node = _catalog("en", "notifications").get(key) or {}
    return {m for part in ("title", "body") for m in PLACEHOLDER.findall(node.get(part, "") or "")}


async def spec_for(conn, row) -> dict | None:
    params = row["params"] if isinstance(row["params"], dict) else json.loads(row["params"] or "{}")
    if "_i18n" in params or "_texts" in params:
        return None
    key = TEMPLATE_KEY.get(row["template_id"], row["template_id"])
    if key not in _catalog("en", "notifications"):
        return None
    values: dict = {}
    key_values: dict = {}
    if row["template_id"] == "strong_match":
        title = None
        if params.get("opportunity_id"):
            title = await conn.fetchval("SELECT title FROM vyapar_opportunities.opportunities WHERE id = $1::uuid", params["opportunity_id"])
        if not title:
            m = re.match(r"^[^:]+:\s*(.+)$", row["title"] or "")
            title = m.group(1) if m else None
        if not title:
            return None
        values["title"] = title
    elif row["template_id"] == "saved_search_match":
        ids = params.get("opportunity_ids") or []
        m = re.search(r"[\"“](.+?)[\"”]", row["title"] or "")
        values.update(count=len(ids), name=m.group(1) if m else "")
    elif row["template_id"] == "verification_reminder":
        name = await conn.fetchval("SELECT name FROM vyapar_listings.listings WHERE id = $1::uuid", params.get("listing_id"))
        if not name:
            return None
        values["name"] = name
    else:
        for k, v in params.items():
            if k in TRUST_KEYS:
                key_values[k] = f"{TRUST_KEYS[k]}{v}"
            elif isinstance(v, (str, int, float)):
                values[k] = v
        values.setdefault("contact", GRIEVANCE)
    if not placeholders(key) <= set(values) | set(key_values):
        # Last resort: read the values back out of the text the recipient was
        # shown, by matching it against the template in each language. These
        # are exactly the values that were displayed, so re-rendering is truthful.
        parsed = reverse_parse(key, row["title"], row["body"])
        if parsed is None:
            return None
        values, key_values = parsed, {}
    return {"title": f"notifications.{key}.title", "body": f"notifications.{key}.body", "values": values, "key_values": key_values}


def _template_regex(text: str) -> re.Pattern:
    parts = re.split(r"(\{\w+\})", text)
    out, seen = [], set()
    for part in parts:
        m = re.fullmatch(r"\{(\w+)\}", part)
        if m and m.group(1) not in seen:
            seen.add(m.group(1))
            out.append(f"(?P<{m.group(1)}>.+?)")
        elif m:
            out.append(f"(?P={m.group(1)})")
        else:
            out.append(re.escape(part))
    return re.compile("^" + "".join(out) + "$", re.S)


def reverse_parse(key: str, title: str | None, body: str | None) -> dict | None:
    for lang in ("en", "hi", "te", "mr", "kn"):
        node = _catalog(lang, "notifications").get(key) or {}
        values: dict = {}
        ok = True
        for part, stored in (("title", title), ("body", body)):
            template = node.get(part)
            if not template:
                continue
            m = _template_regex(template).match(stored or "")
            if m is None:
                ok = False
                break
            values.update(m.groupdict())
        if ok and placeholders(key) <= set(values):
            return values
    return None


async def main(dry_run: bool) -> None:
    conn = await asyncpg.connect(OWNER_DSN)
    rows = await conn.fetch("SELECT id, template_id, title, body, params FROM vyapar_integration.notifications")
    done = skipped = 0
    for r in rows:
        spec = await spec_for(conn, r)
        if spec is None:
            skipped += 1
            continue
        done += 1
        if not dry_run:
            await conn.execute(
                "UPDATE vyapar_integration.notifications SET params = params || jsonb_build_object('_i18n', $2::jsonb) WHERE id = $1",
                r["id"], json.dumps(spec, ensure_ascii=False),
            )
    await conn.close()
    print(f"{'would backfill' if dry_run else 'backfilled'} {done} rows; left {skipped} as stored (already templated or not derivable)")


if __name__ == "__main__":
    asyncio.run(main("--dry-run" in sys.argv))
