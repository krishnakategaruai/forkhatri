# [IMP37 — Refactor B] Access-token scopes and the one policy that maps a
# request to the scope it needs.
#
# Why a central map rather than a decorator on each route: a token must be
# DENIED by default. A per-route `require_scope` that someone forgets to add
# would silently hand an agent full write access to that route; a central,
# default-deny map cannot be forgotten. Routes (and workstream A's services)
# may still add `require_scope(...)` for a finer rule — both checks apply.
#
# Rules for a request made with an access token:
#   * member-only areas are never reachable with a token, whatever its
#     scopes: operator tools (/v1/admin, /internal), dev tooling (/v1/dev),
#     money and plans (payments, promotions, campaigns, entitlements,
#     workspace), privacy/account actions, legal acceptance, verification
#     documents, reports/appeals, and credential management itself
#     (/v1/integrations, except GET /v1/integrations/me). A leaked token can
#     never mint more tokens, move money or delete an account.
#   * GET/HEAD on anything else needs `read`.
#   * a write needs the scope of the area it touches (table below).
#   * any write path not in the table is refused.
# Member sessions implicitly hold every scope; this policy is not applied.
from __future__ import annotations

ALL_SCOPES: tuple[str, ...] = (
    "read",
    "opportunities:write",
    "listings:write",
    "enquiries:write",
    "reviews:write",
    "partnerships:write",
    "notifications:write",
    # [IMP-B, 2026-09-28] workstream D's contracts & milestone payments API.
    # Funding a milestone only OPENS a checkout; the member still completes
    # the payment in person, so money never moves on a token alone.
    "contracts:write",
)

READ_METHODS = frozenset({"GET", "HEAD"})

# Path prefixes a token may never use.
TOKEN_FORBIDDEN_PREFIXES: tuple[str, ...] = (
    "/v1/admin",
    # [IMP-ADMIN — ADR-012] the Admin & Governance Console's federated views
    # (manifest, queues, case detail, actions). Operator-only, member session only.
    "/vyapar/admin",
    "/internal",
    "/v1/dev",
    "/v1/payments",
    "/v1/promotions",
    "/v1/campaigns",
    "/v1/entitlements",
    "/v1/workspace",
    "/v1/privacy",
    "/v1/preferences",
    "/v1/legal",
    "/v1/reports",
    "/v1/appeals",
    "/v1/first-run",
    "/v1/members/me",
    "/v1/integrations",
)
TOKEN_ALLOWED_EXCEPTIONS: frozenset[tuple[str, str]] = frozenset({
    ("GET", "/v1/integrations/me"),
    ("GET", "/v1/credentials/types"),  # [Trust pack] the list of registers is public reference data
})

# Listing verification documents and phone OTP stay with the member in person.
# [Trust pack] council register claims too: a person claims their own enrolment number.
TOKEN_FORBIDDEN_SEGMENTS: tuple[str, ...] = ("/verification", "/otp/", "/credential-ref/", "/credentials")

# Write path prefix -> scope. Order matters only for readability; prefixes do not overlap.
WRITE_SCOPE_BY_PREFIX: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("/v1/opportunities", ("opportunities:write",)),
    ("/v1/listings", ("listings:write",)),
    ("/v1/me/profile", ("listings:write",)),  # [Backend A] the one profile is a listing
    ("/v1/enquiries", ("enquiries:write",)),
    ("/v1/reviews", ("reviews:write",)),
    ("/v1/partnership-requests", ("partnerships:write",)),
    ("/v1/notifications", ("notifications:write",)),
    ("/v1/contracts", ("contracts:write",)),
    # AI routes only draft and suggest; nothing is written until the member confirms.
    ("/v1/ai", ("read",)),
    # [Voice interview] asks and reads answers; returns a draft, writes nothing.
    ("/v1/voice", ("read",)),
    # An attachment is uploaded on the way to posting an opportunity,
    # writing a listing or replying to an enquiry — any of those scopes will do.
    ("/v1/uploads", ("opportunities:write", "listings:write", "enquiries:write")),
    # Client-observed analytics events (impressions, scroll depth) carry no
    # state change and follow the member's own analytics consent.
    ("/v1/events", ("read",)),
    # [Trust pack] "Were you paid on time?" is a reputation answer, like a review.
    ("/v1/paid-on-time", ("reviews:write",)),
    # The scam-shield pre-check stores nothing.
    ("/v1/trust/scam-check", ("read",)),
)

# [IMP-B/L1] Writes whose area is decided by the path's last segment, checked
# before the prefix table: a pre-accept call tap on an opportunity records a
# contact and may open an application, so it needs enquiries:write.
WRITE_SCOPE_BY_SUFFIX: tuple[tuple[str, str, tuple[str, ...]], ...] = (
    ("/v1/opportunities/", "/contact-attempts", ("enquiries:write",)),
)

DENY = "__deny__"


def _under(path: str, prefix: str) -> bool:
    return path == prefix or path.startswith(prefix + "/")


def required_scopes(method: str, path: str) -> tuple[str, ...] | str:
    """Returns the scopes of which the token must hold at least one, or DENY."""
    method = method.upper()
    if (method, path.rstrip("/")) in TOKEN_ALLOWED_EXCEPTIONS:
        return ("read",)
    if any(_under(path, p) for p in TOKEN_FORBIDDEN_PREFIXES):
        return DENY
    if any(seg in path for seg in TOKEN_FORBIDDEN_SEGMENTS):
        return DENY
    if method in READ_METHODS:
        return ("read",)
    for prefix, suffix, scopes in WRITE_SCOPE_BY_SUFFIX:
        if path.startswith(prefix) and path.rstrip("/").endswith(suffix):
            return scopes
    for prefix, scopes in WRITE_SCOPE_BY_PREFIX:
        if _under(path, prefix):
            return scopes
    return DENY
