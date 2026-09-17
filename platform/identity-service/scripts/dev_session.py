"""Development only: open a ForKhatri session for a persona without a password.

Calls `POST /dev/v1/sessions` with `X-ForKhatri-Dev-Token` (DEV_TOOLS_TOKEN, read
from the environment or this service's `.env`) and gives the session to a test:

    # Playwright storageState (cookie for every localhost port: 3000, 3001, 3100, 8000, 8001, 8100)
    .venv\\Scripts\\python scripts\\dev_session.py asha --storage-state ..\\..\\modules\\MOD02-milavn\\.logs\\asha.json

    # A Cookie header for curl (the only mode that prints the session token)
    .venv\\Scripts\\python scripts\\dev_session.py new-member --cookie-header

Personas: asha, new-member, mangaly-family, mangaly-parent, milavn-moderator (or a member uuid).
`krishna` is the owner's account and is refused: tests never act as the owner.
Without an output option nothing secret is printed. Requires the identity service
running with ENVIRONMENT=development and DEV_TOOLS_ENABLED=true.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime
from pathlib import Path
from uuid import UUID

import httpx

SERVICE_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SERVICE_DIR))

from app.config.settings import get_settings  # noqa: E402


def _is_uuid(value: str) -> bool:
    try:
        UUID(value)
    except ValueError:
        return False
    return True


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("target", help="persona key (asha, new-member, mangaly-family, mangaly-parent, milavn-moderator) or member uuid")
    parser.add_argument("--storage-state", type=Path, help="write a Playwright storageState JSON file here")
    parser.add_argument("--cookie-header", action="store_true", help="print 'Cookie: <name>=<token>' to stdout")
    parser.add_argument("--base-url", default=os.environ.get("IDENTITY_URL"), help="identity service URL (default from .env)")
    parser.add_argument("--cookie-domain", default="localhost", help="cookie domain for storageState (default localhost)")
    args = parser.parse_args()

    settings = get_settings()
    if settings.environment != "development":
        print("Refusing: development sessions exist only in development.", file=sys.stderr)
        return 2
    token = os.environ.get("DEV_TOOLS_TOKEN") or settings.dev_tools_token
    if len(token) < 32:
        print("DEV_TOOLS_TOKEN (32+ characters) is not set in the environment or platform/identity-service/.env.", file=sys.stderr)
        return 2
    base_url = (args.base_url or f"http://{settings.api_host}:{settings.api_port}").rstrip("/")
    body = {"member_id": args.target} if _is_uuid(args.target) else {"persona": args.target}

    try:
        response = httpx.post(
            f"{base_url}/dev/v1/sessions", json=body, headers={"X-ForKhatri-Dev-Token": token}, timeout=15
        )
    except httpx.HTTPError as exc:
        print(f"Identity service unreachable at {base_url}: {exc}", file=sys.stderr)
        return 1
    if response.status_code != 200:
        try:
            detail = response.json().get("detail")
        except ValueError:
            detail = None
        if response.status_code == 404 and not isinstance(detail, dict):
            print("The /dev/v1 router is not mounted: set DEV_TOOLS_ENABLED=true and restart the service.", file=sys.stderr)
        else:
            print(f"Refused ({response.status_code}): {detail}", file=sys.stderr)
        return 1

    data = response.json()
    member = data["member"]
    cookie = {
        "name": data["cookie_name"],
        "value": data["session_token"],
        "domain": args.cookie_domain,
        "path": "/",
        "expires": int(datetime.fromisoformat(data["expires_at"]).timestamp()),
        "httpOnly": True,
        "secure": settings.session_cookie_secure,
        "sameSite": "Lax",
    }
    print(f"Signed in as {member['display_name']} ({member['member_id']}).", file=sys.stderr)
    if args.storage_state:
        args.storage_state.parent.mkdir(parents=True, exist_ok=True)
        args.storage_state.write_text(json.dumps({"cookies": [cookie], "origins": []}, indent=2), encoding="utf-8")
        print(f"Playwright storageState written to {args.storage_state}", file=sys.stderr)
    if args.cookie_header:
        print(f"Cookie: {cookie['name']}={cookie['value']}")
    if not args.storage_state and not args.cookie_header:
        print("Nothing secret printed. Use --storage-state PATH or --cookie-header.", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
