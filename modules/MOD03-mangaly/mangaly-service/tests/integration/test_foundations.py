"""Integration tests for the cross-cutting foundations, against the real database.

Per `/docs/PreStartResearch/IMPLEMENTATION-TEST-STANDARDS.md` §4, integration
tests use real internal collaborators (real Postgres) and mock only true
external boundaries. Nothing here is mocked: these run against the live
`mangaly` database as the non-owning `mangaly_app` role, because every property
under test (RLS, `SET LOCAL` scoping, `ON CONFLICT` atomicity, account-scoped
idempotency) is a property of Postgres, not of Python — mocking the database
would test nothing.

Test names follow §4's `Given_<precondition>_When_<action>_Then_<outcome>`.

These are a Step 9 self-verification harness. Step 10 owns the full suite
mapped onto `05-test-scenarios.md`'s 229 tagged scenarios; this file does not
attempt that and does not claim its coverage.
"""

from __future__ import annotations

import asyncio
import uuid
from datetime import UTC

import pytest
import pytest_asyncio
from sqlalchemy import text

from app.components.authorization import interface as authz
from app.components.authorization.context import Action, AuthorizationDenied, GrantScope
from app.db.engine import assert_non_owning_role, create_engine, create_session_factory
from app.db.session import (
    VAR_ACCOUNT_ID,
    VAR_AUTHZ_CONTEXT,
    SessionVariableError,
    read_session_variable,
    set_account_context,
    set_authz_context,
)
from app.events import bus
from app.events.dto import ACTIVITY_SUMMARY_ALLOW_LIST, ActivitySummaryEvent
from app.idempotency import store
from app.idempotency.guard import IdempotencyConflict, idempotent
from app.rate_limiting import limiter
from app.rate_limiting.limiter import RateLimitScope


@pytest_asyncio.fixture(scope="module")
async def engine():
    eng = create_engine()
    yield eng
    await eng.dispose()


@pytest_asyncio.fixture
async def session_factory(engine):
    return create_session_factory(engine)


@pytest_asyncio.fixture
async def session(session_factory):
    async with session_factory() as s:
        yield s


# --- TR017 / SP017: non-owning role -------------------------------------------


async def test_Given_runtime_role_When_startup_check_runs_Then_it_owns_zero_tables(engine):
    owned = await assert_non_owning_role(engine)
    assert owned == 0


# --- TR017 / SP017: SET LOCAL discipline --------------------------------------


async def test_Given_no_open_transaction_When_setting_authz_context_Then_it_raises(session):
    with pytest.raises(SessionVariableError):
        await set_authz_context(session, uuid.uuid4())


async def test_Given_context_set_in_one_transaction_When_next_transaction_starts_Then_it_is_gone(
    session,
):
    subject = uuid.uuid4()
    async with session.begin():
        await set_authz_context(session, subject)
        assert await read_session_variable(session, VAR_AUTHZ_CONTEXT) == str(subject)

    async with session.begin():
        leaked = await read_session_variable(session, VAR_AUTHZ_CONTEXT)

    assert leaked == ""


async def test_Given_an_unknown_variable_name_When_set_local_called_Then_it_raises(session):
    async with session.begin():
        with pytest.raises(SessionVariableError):
            from app.db.session import set_local

            await set_local(session, "mangaly.not_a_real_variable", "x")


# --- TR017 / SP017: RLS actually restricts ------------------------------------


async def test_Given_no_session_context_When_reading_profiles_Then_zero_rows_are_visible(session):
    async with session.begin():
        count = (
            await session.execute(text("SELECT count(*) FROM mangaly_profile.profile"))
        ).scalar_one()
    assert count == 0


async def test_Given_an_unrelated_account_context_When_reading_profiles_Then_zero_rows(session):
    async with session.begin():
        await set_account_context(session, uuid.uuid4())
        await set_authz_context(session, uuid.uuid4())
        count = (
            await session.execute(text("SELECT count(*) FROM mangaly_profile.profile"))
        ).scalar_one()
    assert count == 0


# --- TR017 / TR018: the chokepoint --------------------------------------------


async def test_Given_no_transaction_When_resolve_is_called_Then_it_refuses(session):
    with pytest.raises(AuthorizationDenied):
        await authz.resolve(
            session,
            subject_id=uuid.uuid4(),
            account_id=uuid.uuid4(),
            target_profile_id=uuid.uuid4(),
            action=Action.READ,
        )


async def test_Given_no_grant_exists_When_resolve_runs_Then_context_has_no_scopes(session):
    subject, target = uuid.uuid4(), uuid.uuid4()
    async with session.begin():
        ctx = await authz.resolve(
            session,
            subject_id=subject,
            account_id=subject,
            target_profile_id=target,
            action=Action.READ,
        )
        assert ctx.scopes == frozenset()
        assert ctx.is_self is False
        assert ctx.has_scope(GrantScope.CANDIDATE_INFO) is False
        with pytest.raises(AuthorizationDenied):
            ctx.require_scope(GrantScope.CANDIDATE_INFO)
        await session.rollback()


async def test_Given_an_active_grant_When_resolve_runs_Then_only_that_scope_is_present(session):
    subject, target = uuid.uuid4(), uuid.uuid4()
    async with session.begin():
        await set_authz_context(session, subject)
        await session.execute(
            text(
                "INSERT INTO mangaly_authz.grant "
                "(subject_id, target_profile_id, scope, grant_type, source_component) "
                "VALUES (:s, :t, 'family_info', 'home_circle_membership', 'home_circle')"
            ),
            {"s": str(subject), "t": str(target)},
        )
        ctx = await authz.resolve(
            session,
            subject_id=subject,
            account_id=subject,
            target_profile_id=target,
            action=Action.READ,
        )
        # [TR018] Two independently-typed scopes, never one combined boolean.
        assert ctx.has_scope(GrantScope.FAMILY_INFO) is True
        assert ctx.has_scope(GrantScope.CANDIDATE_INFO) is False
        assert ctx.grant_basis["family_info"] == "home_circle_membership"
        await session.rollback()


async def test_Given_a_resolved_context_When_a_component_tries_to_widen_it_Then_it_cannot(session):
    async with session.begin():
        subject = uuid.uuid4()
        ctx = await authz.resolve(
            session,
            subject_id=subject,
            account_id=subject,
            target_profile_id=None,
            action=Action.READ,
        )
        with pytest.raises((AttributeError, TypeError)):
            ctx.scopes = frozenset({GrantScope.CANDIDATE_INFO})  # type: ignore[misc]
        await session.rollback()


# --- TR069 / SP069: transactional outbox --------------------------------------


async def test_Given_no_transaction_When_publishing_an_event_Then_it_refuses(session):
    with pytest.raises(bus.OutboxPublishError):
        await bus.publish(
            session,
            schema="mangaly_profile",
            aggregate_id=uuid.uuid4(),
            event_type="test.event",
            payload={"a": 1},
        )


async def test_Given_an_unknown_schema_When_publishing_Then_it_refuses(session):
    async with session.begin():
        with pytest.raises(bus.OutboxPublishError):
            await bus.publish(
                session,
                schema="mangaly_identity",
                aggregate_id=uuid.uuid4(),
                event_type="test.event",
                payload={},
            )
        await session.rollback()


async def test_Given_a_payload_with_a_domain_object_When_publishing_Then_it_refuses(session):
    class Domain:
        secret = "row contents"

    async with session.begin():
        with pytest.raises(bus.OutboxPublishError):
            await bus.publish(
                session,
                schema="mangaly_profile",
                aggregate_id=uuid.uuid4(),
                event_type="test.event",
                payload={"obj": Domain()},
            )
        await session.rollback()


async def test_Given_the_state_change_rolls_back_When_it_had_published_Then_the_event_is_gone(
    session_factory,
):
    aggregate = uuid.uuid4()
    async with session_factory() as s:
        async with s.begin():
            await bus.publish(
                s,
                schema="mangaly_profile",
                aggregate_id=aggregate,
                event_type="test.atomicity",
                payload={"aggregate_id": aggregate},
            )
            await s.rollback()

    # Read back as the dispatcher — the only role the split RLS policy allows
    # to SELECT from an outbox table.
    async with session_factory() as s:
        async with s.begin():
            from app.db.session import set_dispatcher_context

            await set_dispatcher_context(s)
            found = (
                await s.execute(
                    text(
                        "SELECT count(*) FROM mangaly_profile.outbox_event "
                        "WHERE aggregate_id = :a"
                    ),
                    {"a": str(aggregate)},
                )
            ).scalar_one()
    assert found == 0


async def test_Given_a_committed_event_When_read_without_dispatcher_role_Then_it_is_invisible(
    session_factory,
):
    aggregate = uuid.uuid4()
    async with session_factory() as s:
        async with s.begin():
            await bus.publish(
                s,
                schema="mangaly_profile",
                aggregate_id=aggregate,
                event_type="test.dispatcher_only",
                payload={"aggregate_id": aggregate},
            )

    async with session_factory() as s:
        async with s.begin():
            without_role = (
                await s.execute(
                    text(
                        "SELECT count(*) FROM mangaly_profile.outbox_event "
                        "WHERE aggregate_id = :a"
                    ),
                    {"a": str(aggregate)},
                )
            ).scalar_one()

    async with session_factory() as s:
        async with s.begin():
            from app.db.session import set_dispatcher_context

            await set_dispatcher_context(s)
            with_role = (
                await s.execute(
                    text(
                        "SELECT count(*) FROM mangaly_profile.outbox_event "
                        "WHERE aggregate_id = :a"
                    ),
                    {"a": str(aggregate)},
                )
            ).scalar_one()

    assert without_role == 0
    assert with_role == 1


# --- TR081 / SP081: the cross-boundary DTO ------------------------------------


def test_Given_the_activity_summary_dto_When_serialised_Then_only_allow_listed_fields_appear():
    from datetime import datetime

    event = ActivitySummaryEvent(
        account_id=uuid.uuid4(),
        lifecycle_state="concluded",
        previous_lifecycle_state="active",
        occurred_at=datetime.now(UTC),
    )
    payload = event.to_payload()
    assert set(payload) == ACTIVITY_SUMMARY_ALLOW_LIST


def test_Given_the_activity_summary_dto_When_an_undeclared_field_is_set_Then_it_raises():
    from datetime import datetime

    event = ActivitySummaryEvent(
        account_id=uuid.uuid4(),
        lifecycle_state="active",
        previous_lifecycle_state=None,
        occurred_at=datetime.now(UTC),
    )
    # `slots=True` means an undeclared attribute cannot be attached at all, so a
    # future domain field cannot ride along into the published payload.
    with pytest.raises((AttributeError, TypeError)):
        event.counterparty_name = "leak"  # type: ignore[attr-defined]


# --- TR037 / SP037: the shared rate limiter -----------------------------------


async def test_Given_a_limit_of_five_When_six_calls_are_made_Then_the_sixth_is_refused(session):
    subject = f"+9199{uuid.uuid4().hex[:8]}"
    async with session.begin():
        results = [
            await limiter.check_and_increment(
                session,
                scope=RateLimitScope.LOGIN_FAILURE,
                subject=subject,
                limit_max=5,
                window_seconds=900,
            )
            for _ in range(6)
        ]
        await session.rollback()
    assert [r.allowed for r in results] == [True, True, True, True, True, False]


async def test_Given_concurrent_calls_at_the_boundary_When_they_race_Then_exactly_limit_max_pass(
    session_factory,
):
    """SP037's caution: a read-then-write pair reintroduces the race. This proves
    the single atomic UPSERT does not."""
    subject = f"+9199{uuid.uuid4().hex[:8]}"
    limit_max = 5
    concurrency = 20

    async def one_call() -> bool:
        async with session_factory() as s:
            async with s.begin():
                result = await limiter.check_and_increment(
                    s,
                    scope=RateLimitScope.VERIFIER_INVITE,
                    subject=subject,
                    limit_max=limit_max,
                    window_seconds=604800,
                )
                return result.allowed

    outcomes = await asyncio.gather(*(one_call() for _ in range(concurrency)))
    assert sum(outcomes) == limit_max


async def test_Given_a_raw_identifier_When_a_key_is_built_Then_the_identifier_is_not_stored(
    session,
):
    subject = "+919812345678"
    key = limiter.build_key(RateLimitScope.OTP_RESEND, subject)
    assert subject not in key
    assert key.startswith("otp_resend:")


async def test_Given_the_limit_is_exceeded_When_enforce_is_called_Then_it_raises(session):
    subject = f"+9199{uuid.uuid4().hex[:8]}"
    async with session.begin():
        await limiter.enforce(
            session,
            scope=RateLimitScope.SIGNUP,
            subject=subject,
            limit_max=1,
            window_seconds=3600,
        )
        with pytest.raises(limiter.RateLimitExceeded):
            await limiter.enforce(
                session,
                scope=RateLimitScope.SIGNUP,
                subject=subject,
                limit_max=1,
                window_seconds=3600,
            )
        await session.rollback()


# --- TR102 / SP102: account-scoped idempotency --------------------------------


async def test_Given_a_repeated_key_When_the_endpoint_is_called_again_Then_it_is_not_re_executed(
    session_factory,
):
    account = uuid.uuid4()
    key = uuid.uuid4().hex
    body = {"name": "A"}
    executions = 0

    for _ in range(2):
        async with session_factory() as s:
            async with s.begin():
                await set_account_context(s, account)
                async with idempotent(
                    s,
                    account_id=account,
                    idempotency_key=key,
                    endpoint="POST /test",
                    request_payload=body,
                ) as outcome:
                    if not outcome.replayed:
                        executions += 1
                        outcome.set_result(201, {"id": "abc"})

    assert executions == 1


async def test_Given_the_same_key_under_a_different_account_When_looked_up_Then_no_snapshot_leaks(
    session_factory,
):
    """SP102's Critical finding, re-verified from the application side."""
    account_a, account_b = uuid.uuid4(), uuid.uuid4()
    key = uuid.uuid4().hex
    body = {"x": 1}
    fingerprint = store.request_fingerprint(body)

    async with session_factory() as s:
        async with s.begin():
            await set_account_context(s, account_a)
            async with idempotent(
                s, account_id=account_a, idempotency_key=key,
                endpoint="POST /test", request_payload=body,
            ) as outcome:
                outcome.set_result(201, {"owner": "A"})

    async with session_factory() as s:
        async with s.begin():
            await set_account_context(s, account_b)
            found = await store.lookup(
                s,
                account_id=account_b,
                idempotency_key=key,
                endpoint="POST /test",
                request_hash=fingerprint,
            )
    assert found is None


async def test_Given_a_reused_key_with_a_changed_payload_When_called_Then_it_is_rejected(
    session_factory,
):
    account = uuid.uuid4()
    key = uuid.uuid4().hex

    async with session_factory() as s:
        async with s.begin():
            await set_account_context(s, account)
            async with idempotent(
                s, account_id=account, idempotency_key=key,
                endpoint="POST /test", request_payload={"v": 1},
            ) as outcome:
                outcome.set_result(201, {"ok": True})

    with pytest.raises(IdempotencyConflict):
        async with session_factory() as s:
            async with s.begin():
                await set_account_context(s, account)
                async with idempotent(
                    s, account_id=account, idempotency_key=key,
                    endpoint="POST /test", request_payload={"v": 2},
                ):
                    pass


async def test_Given_no_idempotency_key_When_the_guard_wraps_a_call_Then_it_passes_through(
    session_factory,
):
    account = uuid.uuid4()
    async with session_factory() as s:
        async with s.begin():
            await set_account_context(s, account)
            async with idempotent(
                s, account_id=account, idempotency_key=None,
                endpoint="POST /test", request_payload={},
            ) as outcome:
                assert outcome.replayed is False


async def test_Given_an_idempotency_row_When_read_without_account_context_Then_rls_hides_it(
    session_factory,
):
    account = uuid.uuid4()
    key = uuid.uuid4().hex
    async with session_factory() as s:
        async with s.begin():
            await set_account_context(s, account)
            async with idempotent(
                s, account_id=account, idempotency_key=key,
                endpoint="POST /test", request_payload={},
            ) as outcome:
                outcome.set_result(200, {})

    async with session_factory() as s:
        async with s.begin():
            visible = (
                await s.execute(
                    text(
                        "SELECT count(*) FROM mangaly_platform.idempotency_key "
                        "WHERE idempotency_key = :k"
                    ),
                    {"k": key},
                )
            ).scalar_one()
    assert visible == 0


# --- Session-variable name conformance ----------------------------------------


async def test_Given_the_declared_variable_names_When_compared_to_schema_policies_Then_they_match(
    session,
):
    """The RLS policies name their session variables in SQL; `db/session.py` names
    them in Python. This asserts the two lists have not drifted.

    Both policy expressions AND function bodies are scanned: `mangaly.authz_context`
    is referenced inside `mangaly_authz.has_scope()` / `is_self()` rather than
    inline in most policy predicates, so scanning `pg_policy` alone would
    wrongly report it as unused.
    """
    async with session.begin():
        policy_exprs = (
            await session.execute(
                text(
                    "SELECT coalesce(pg_get_expr(polqual, polrelid), '') || ' ' || "
                    "coalesce(pg_get_expr(polwithcheck, polrelid), '') FROM pg_policy"
                )
            )
        ).scalars().all()
        function_bodies = (
            await session.execute(
                text(
                    "SELECT prosrc FROM pg_proc p JOIN pg_namespace n "
                    "ON n.oid = p.pronamespace WHERE n.nspname LIKE 'mangaly%'"
                )
            )
        ).scalars().all()

    corpus = " ".join([*policy_exprs, *function_bodies])
    assert VAR_ACCOUNT_ID in corpus
    assert VAR_AUTHZ_CONTEXT in corpus
