"""Vyapar service layer.

[Refactor A, 2026-09-21] Every business rule and every SQL statement lives
here, one module per domain. REST routers, the agent (MCP) server, webhooks
and background jobs are all front doors that call these functions; none of
them re-implements a rule.

Convention: a service function takes `(conn, ctx, ...typed inputs)` — an
asyncpg connection that already carries `vyapar.authz_context` (so RLS still
decides what the caller may see), the caller's `AuthzContext`, the
language when it produces translated text, and typed inputs. It returns a
pydantic model (or a list of them) and raises `app.errors.ApiError` for a
translated, coded failure.
"""
