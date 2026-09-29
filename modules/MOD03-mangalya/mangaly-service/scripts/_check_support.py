"""Shared helpers for the live check scripts.

Every check signs in through ForKhatri as the development member reserved for
automated tests ("New Member", created by the identity service's
`scripts/seed_dev_members.py`), uses a real portrait photo, and removes every
Mangaly row and file it created before it exits. The development database is
the one the product owner clicks through, so a check must never leave people
behind in Discover.
"""

from __future__ import annotations

import asyncio
import os
import sys
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from http.cookiejar import CookieJar
from json import dumps, loads
from pathlib import Path
from typing import Any

import asyncpg

# A check normally runs against the local API on 8000; MANGALY_CHECK_API points it
# at another instance (a second copy on a free port, so a running server is left alone).
API = os.environ.get("MANGALY_CHECK_API", "http://127.0.0.1:8000")
IDENTITY = "http://127.0.0.1:8100"
ENTRANCE_ORIGIN = "http://localhost:3100"
TEST_MEMBER_PHONE = "+919999900002"
TEST_MEMBER_PASSWORD = "ForKhatri-dev-2026"
OWNER_DSN = "postgresql://mangaly_owner:mangaly_owner_dev_password@localhost:5433/mangaly"
MEDIA_ROOT = Path(__file__).resolve().parents[1] / ".local-media"
PORTRAIT = Path(__file__).resolve().parent / "assets" / "check-portrait.jpg"


class Client:
    """A cookie-carrying HTTP client signed in to ForKhatri."""

    def __init__(self) -> None:
        self._opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(CookieJar()))

    def _send(self, req: urllib.request.Request) -> tuple[int, Any]:
        try:
            with self._opener.open(req, timeout=30) as res:
                raw = res.read()
                return res.status, _decode(raw)
        except urllib.error.HTTPError as e:
            return e.code, _decode(e.read())

    def json(self, method: str, url: str, body: dict[str, Any] | None = None) -> tuple[int, Any]:
        data = dumps(body).encode() if body is not None else None
        headers = {"Content-Type": "application/json", "Origin": ENTRANCE_ORIGIN}
        return self._send(urllib.request.Request(url, data=data, method=method, headers=headers))

    def multipart(
        self, url: str, fields: dict[str, str], file_name: str, content: bytes, content_type: str
    ) -> tuple[int, Any]:
        boundary = "----mangalycheck"
        parts = [
            f'--{boundary}\r\nContent-Disposition: form-data; name="{key}"\r\n\r\n{value}\r\n'
            for key, value in fields.items()
        ]
        photo_header = (
            f"--{boundary}\r\n"
            f'Content-Disposition: form-data; name="photo"; filename="{file_name}"\r\n'
            f"Content-Type: {content_type}\r\n\r\n"
        )
        body = (
            "".join(parts).encode()
            + photo_header.encode()
            + content
            + f"\r\n--{boundary}--\r\n".encode()
        )
        headers = {"Content-Type": f"multipart/form-data; boundary={boundary}"}
        return self._send(urllib.request.Request(url, data=body, method="POST", headers=headers))

    def raw_status(self, url: str) -> int:
        status, _ = self._send(urllib.request.Request(url, method="GET"))
        return status


def _decode(raw: bytes) -> Any:
    if not raw:
        return ""
    try:
        return loads(raw.decode())
    except (ValueError, UnicodeDecodeError):
        return raw[:80]


def portrait() -> bytes:
    return PORTRAIT.read_bytes()


def services_up() -> bool:
    for url in (f"{API}/health", f"{IDENTITY}/health"):
        try:
            with urllib.request.urlopen(url, timeout=5) as res:
                if res.status != 200:
                    return False
        except Exception:
            return False
    return True


def sign_in_test_member() -> tuple[Client, str]:
    """Sign in as the automated-test member and return the client and account id."""
    client = Client()
    status, body = client.json(
        "POST",
        f"{IDENTITY}/v1/auth/password",
        {"identifier": TEST_MEMBER_PHONE, "password": TEST_MEMBER_PASSWORD},
    )
    if status != 200:
        raise RuntimeError(f"test member sign-in failed: {status} {body}")
    status, me = client.json("GET", f"{API}/auth/me")
    if status != 200:
        raise RuntimeError(f"Mangaly did not accept the ForKhatri session: {status} {me}")
    return client, str(me["account_id"])


async def _profile_id(conn: asyncpg.Connection, account_id: str) -> Any:
    return await conn.fetchval(
        "SELECT id FROM mangaly_profile.profile WHERE account_id = $1", account_id
    )


def has_profile(account_id: str) -> bool:
    async def run() -> bool:
        conn = await asyncpg.connect(OWNER_DSN)
        try:
            return await _profile_id(conn, account_id) is not None
        finally:
            await conn.close()

    return asyncio.run(run())


def remove_profile(account_id: str) -> None:
    """Delete the profile the check created: attributes, photos (rows and files),
    the Discovery index row and the profile itself. The member link row stays,
    because the member belongs to the ForKhatri identity service, not the check."""

    async def run() -> None:
        conn = await asyncpg.connect(OWNER_DSN)
        try:
            async with conn.transaction():
                profile_id = await _profile_id(conn, account_id)
                if profile_id is None:
                    return
                refs = await conn.fetch(
                    "SELECT storage_ref FROM mangaly_profile.profile_media WHERE profile_id = $1",
                    profile_id,
                )
                await conn.execute(
                    "DELETE FROM mangaly_discovery.discovery_profile_index WHERE profile_id = $1",
                    account_id,
                )
                await conn.execute(
                    "DELETE FROM mangaly_profile.profile_attribute WHERE profile_id = $1",
                    profile_id,
                )
                await conn.execute(
                    "DELETE FROM mangaly_profile.profile_media WHERE profile_id = $1", profile_id
                )
                await conn.execute("DELETE FROM mangaly_profile.profile WHERE id = $1", profile_id)
            for row in refs:
                path = MEDIA_ROOT / str(row["storage_ref"]).removeprefix("local://")
                path.unlink(missing_ok=True)
            folder = MEDIA_ROOT / str(profile_id)
            if folder.is_dir() and not any(folder.iterdir()):
                folder.rmdir()
        finally:
            await conn.close()

    asyncio.run(run())


@dataclass
class Results:
    passed: list[str] = field(default_factory=list)
    failed: list[str] = field(default_factory=list)

    def check(self, label: str, ok: bool, detail: object = "") -> None:
        (self.passed if ok else self.failed).append(label)
        suffix = f" — {detail}" if detail != "" else ""
        print(f"  {'PASS' if ok else 'FAIL'}  {label}{suffix}")

    def finish(self) -> int:
        print(f"\n  {len(self.passed)} passed, {len(self.failed)} failed\n")
        return 1 if self.failed else 0


def refuse_if_profile_exists(account_id: str) -> None:
    if has_profile(account_id):
        print(
            "  The automated-test member already has a Mangaly profile that this check did not "
            "create. Nothing was changed; remove that profile first."
        )
        sys.exit(2)
