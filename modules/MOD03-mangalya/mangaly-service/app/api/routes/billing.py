"""Billing endpoints (DEC-V1-031): the plan catalogue, the caller's plan,
checkout (order → confirm / webhook), cancel, and the two "interested in you"
lists Gold unlocks. Thin HTTP layer over `components/billing/interface.py`.

Never gated here or anywhere: viewing profiles, receiving and answering
requests, chat, family features, reporting, blocking, verification.
"""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, HTTPException, Request, Response, status
from pydantic import BaseModel, Field

from app.api.deps import AppSettings, AuthenticatedAccount, DbSession, Locale
from app.components.authorization import interface as authz
from app.components.authorization.context import AuthorizationDenied
from app.components.billing import gateway as gw
from app.components.billing import interface as billing
from app.components.discovery import interface as discovery
from app.components.safety import interface as safety
from app.config import plans as catalogue
from app.i18n import translate

router = APIRouter(prefix="/billing", tags=["billing"])


async def _context(session: DbSession, account_id: UUID, for_candidate: UUID | None) -> UUID:
    try:
        return await authz.resolve_context_account(
            session, acting_account_id=account_id, for_candidate=for_candidate
        )
    except AuthorizationDenied as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN) from exc


def upgrade_required_error(exc: billing.UpgradeRequired, lang: str) -> HTTPException:
    """The one shape every gated action answers with: 402, `upgrade_required`,
    the plan needed, and a sentence a person can read."""
    if exc.flag == catalogue.DAILY_REQUESTS and exc.limit is not None:
        message = translate("billing.error.dailyLimit", lang, limit=exc.limit)
    else:
        message = translate(
            "billing.error.upgradeRequired",
            lang,
            plan=translate(f"billing.plan.{exc.plan_needed}.name", lang),
        )
    return HTTPException(
        status_code=status.HTTP_402_PAYMENT_REQUIRED,
        detail={
            "code": "upgrade_required",
            "feature": exc.flag,
            "plan_needed": exc.plan_needed,
            "used": exc.used,
            "limit": exc.limit,
            "message": message,
        },
    )


# ---------------------------------------------------------------------------
# Catalogue
# ---------------------------------------------------------------------------


class TermOut(BaseModel):
    months: int
    amount_paise: int
    gst_paise: int
    total_paise: int
    label: str


class PlanOut(BaseModel):
    code: str
    name: str
    blurb: str
    includes: str | None
    terms: list[TermOut]
    entitlements: dict[str, bool | int | None]
    features: list[str]


class CatalogueOut(BaseModel):
    version: str
    currency: str
    gst_rate_bps: int
    plans: list[PlanOut]


def _plan_out(plan: catalogue.Plan, lang: str, terms: tuple[catalogue.Term, ...] | None = None) -> PlanOut:
    ents = plan.entitlements
    if plan.code in catalogue.ADD_ON_PLANS:
        # An agent plan adds no member entitlements; its blurb says what it is.
        features = [translate(f"billing.plan.{plan.code}.feature{i}", lang) for i in (1, 2, 3)]
    else:
        features = [
            translate("billing.feature.daily_requests_unlimited", lang)
            if ents.daily_requests is catalogue.UNLIMITED
            else translate("billing.feature.daily_requests_limited", lang, limit=ents.daily_requests)
        ]
        features += [translate(f"billing.feature.{f}", lang) for f in catalogue.BOOLEAN_FLAGS if ents.flag(f)]
    return PlanOut(
        code=plan.code,
        name=translate(f"billing.plan.{plan.code}.name", lang),
        blurb=translate(f"billing.plan.{plan.code}.blurb", lang),
        includes=plan.includes,
        terms=[
            TermOut(
                months=t.months,
                amount_paise=t.amount_paise,
                gst_paise=t.gst_paise,
                total_paise=t.total_paise,
                label=translate("billing.term.months", lang, months=t.months),
            )
            for t in (plan.terms if terms is None else terms)
        ],
        entitlements=ents.as_dict(),
        features=features,
    )


@router.get("/plans", response_model=CatalogueOut)
async def list_plans(session: DbSession, lang: Locale, codes: str | None = None) -> CatalogueOut:
    """The member plans, or the plans named in `codes` (e.g. `AGENT` or
    `AGENT_CONNECT`), each at the price in force — an administrator's price
    from `plan_price` when set, the catalogue's otherwise."""
    wanted = (
        [c for c in codes.split(",") if c in catalogue.PLANS]
        if codes
        else list(catalogue.PLAN_ORDER)
    )
    plans = []
    for c in wanted:
        terms = await billing.effective_terms(session, plan_code=c)
        plans.append(_plan_out(catalogue.PLANS[c], lang, terms))
    return CatalogueOut(
        version=catalogue.CATALOGUE_VERSION,
        currency=catalogue.CURRENCY,
        gst_rate_bps=catalogue.GST_RATE_BPS,
        plans=plans,
    )


# ---------------------------------------------------------------------------
# My plan
# ---------------------------------------------------------------------------


class UsageOut(BaseModel):
    requests_sent_today: int
    daily_requests: int | None


class MyPlanOut(BaseModel):
    account_id: str
    plan_code: str
    plan_name: str
    ends_at: datetime | None
    started_at: datetime | None
    term_months: int | None
    auto_renew: bool
    cancelled_at: datetime | None
    entitlements: dict[str, bool | int | None]
    usage: UsageOut


async def _my_plan(session: DbSession, ctx: UUID, lang: str) -> MyPlanOut:
    state = await billing.resolve_plan(session, account_id=ctx)
    used = await billing.requests_sent_today(session, account_id=ctx)
    return MyPlanOut(
        account_id=str(ctx),
        plan_code=state.code,
        plan_name=translate(f"billing.plan.{state.code}.name", lang),
        ends_at=state.ends_at,
        started_at=state.started_at,
        term_months=state.term_months,
        auto_renew=state.auto_renew,
        cancelled_at=state.cancelled_at,
        entitlements=state.entitlements.as_dict(),
        usage=UsageOut(requests_sent_today=used, daily_requests=state.entitlements.daily_requests),
    )


@router.get("/me", response_model=MyPlanOut)
async def my_plan(
    session: DbSession, account_id: AuthenticatedAccount, lang: Locale, for_candidate: UUID | None = None
) -> MyPlanOut:
    """The context's plan: the caller's own, or the candidate's when acting for them."""
    ctx = await _context(session, account_id, for_candidate)
    return await _my_plan(session, ctx, lang)


# ---------------------------------------------------------------------------
# Checkout
# ---------------------------------------------------------------------------


class CreateOrderBody(BaseModel):
    plan_code: str = Field(pattern=r"^[A-Z_]+$")
    term_months: int


class OrderOut(BaseModel):
    id: str
    plan_code: str
    term_months: int
    amount_paise: int
    gst_paise: int
    total_paise: int
    currency: str
    status: str
    gateway: str
    gateway_order_id: str | None
    created_at: datetime
    paid_at: datetime | None


class CheckoutOut(BaseModel):
    order: OrderOut
    # What Razorpay Checkout needs; `key_id` is None for the sandbox, which is
    # the client's signal to show the development "Pay (sandbox)" button.
    key_id: str | None
    gateway_order_id: str
    amount_paise: int
    currency: str
    sandbox: bool


def _order_out(o: billing.OrderSummary) -> OrderOut:
    return OrderOut(
        id=str(o.id),
        plan_code=o.plan_code,
        term_months=o.term_months,
        amount_paise=o.amount_paise,
        gst_paise=o.gst_paise,
        total_paise=o.total_paise,
        currency=o.currency,
        status=o.status,
        gateway=o.gateway,
        gateway_order_id=o.gateway_order_id,
        created_at=o.created_at,
        paid_at=o.paid_at,
    )


@router.post("/orders", response_model=CheckoutOut, status_code=status.HTTP_201_CREATED)
async def create_order(
    body: CreateOrderBody,
    session: DbSession,
    account_id: AuthenticatedAccount,
    settings: AppSettings,
    lang: Locale,
) -> CheckoutOut:
    """A plan is bought by the account that will hold it (the candidate). A
    parent buys for their child from the child's own signed-in account, or
    the child buys; there is no buying into someone else's account."""
    try:
        order, gateway_order = await billing.create_order(
            session,
            account_id=account_id,
            plan_code=body.plan_code,
            term_months=body.term_months,
            settings=settings,
        )
    except billing.UnknownPlanOrTerm as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=translate("billing.error.unknownPlan", lang),
        ) from exc
    return CheckoutOut(
        order=_order_out(order),
        key_id=gateway_order.key_id,
        gateway_order_id=gateway_order.gateway_order_id,
        amount_paise=gateway_order.amount_paise,
        currency=gateway_order.currency,
        sandbox=gateway_order.gateway == gw.DevSandboxGateway.name,
    )


class ConfirmBody(BaseModel):
    gateway_payment_id: str = Field(min_length=1, max_length=100)
    signature: str = Field(min_length=1, max_length=200)


class ConfirmOut(BaseModel):
    order: OrderOut
    plan: MyPlanOut


@router.post("/orders/{order_id}/confirm", response_model=ConfirmOut)
async def confirm_order(
    order_id: UUID,
    body: ConfirmBody,
    session: DbSession,
    account_id: AuthenticatedAccount,
    settings: AppSettings,
    lang: Locale,
) -> ConfirmOut:
    """Razorpay Checkout's success handler posts `razorpay_payment_id` and
    `razorpay_signature` here; the HMAC is checked before anything activates."""
    try:
        order, _ = await billing.confirm_order(
            session,
            account_id=account_id,
            order_id=order_id,
            gateway_payment_id=body.gateway_payment_id,
            signature=body.signature,
            settings=settings,
        )
    except billing.OrderNotFound as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=translate("billing.error.orderNotFound", lang)
        ) from exc
    except billing.PaymentNotVerified as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=translate("billing.error.paymentNotVerified", lang),
        ) from exc
    return ConfirmOut(order=_order_out(order), plan=await _my_plan(session, account_id, lang))


@router.post("/webhook", status_code=status.HTTP_200_OK)
async def webhook(request: Request, session: DbSession, settings: AppSettings) -> Response:
    """Razorpay → us. Signature-verified against RAZORPAY_WEBHOOK_SECRET,
    idempotent on the event id. No member is signed in here; the order is
    found by the gateway's ids through a definer function."""
    raw = await request.body()
    try:
        outcome = await billing.process_webhook(
            session, raw_body=raw, headers=dict(request.headers), settings=settings
        )
    except gw.WebhookRejected as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="signature") from exc
    return Response(content=outcome, media_type="text/plain")


@router.post("/dev/pay/{order_id}", response_model=ConfirmOut)
async def sandbox_pay(
    order_id: UUID,
    session: DbSession,
    account_id: AuthenticatedAccount,
    settings: AppSettings,
    lang: Locale,
) -> ConfirmOut:
    """DEVELOPMENT ONLY. Marks the caller's own sandbox order paid. Refuses
    (409) the moment real Razorpay keys are configured."""
    try:
        order, _ = await billing.sandbox_pay(
            session, account_id=account_id, order_id=order_id, settings=settings
        )
    except billing.SandboxUnavailable as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=translate("billing.error.sandboxUnavailable", lang),
        ) from exc
    except billing.OrderNotFound as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=translate("billing.error.orderNotFound", lang)
        ) from exc
    return ConfirmOut(order=_order_out(order), plan=await _my_plan(session, account_id, lang))


@router.post("/cancel", response_model=MyPlanOut)
async def cancel(session: DbSession, account_id: AuthenticatedAccount, lang: Locale) -> MyPlanOut:
    """Auto-renew off. The plan runs to its end date; nothing is refunded here."""
    await billing.cancel_auto_renew(session, account_id=account_id)
    return await _my_plan(session, account_id, lang)


# ---------------------------------------------------------------------------
# Who is interested in you
# ---------------------------------------------------------------------------


class InterestedPersonOut(BaseModel):
    account_id: str
    at: datetime
    photo_url: str | None = None
    age: int | None = None
    locality: str | None = None
    profession: str | None = None


class InterestedListOut(BaseModel):
    count: int
    locked: bool
    plan_needed: str | None
    people: list[InterestedPersonOut]


class InterestedOut(BaseModel):
    shortlisted: InterestedListOut
    viewed: InterestedListOut


async def _interested_list(
    session: DbSession,
    *,
    people: list[billing.InterestedPerson],
    unlocked: bool,
    hidden: set[UUID],
    flag: str,
) -> InterestedListOut:
    visible = [p for p in people if p.account_id not in hidden]
    if not unlocked:
        # A teaser: how many, never who. Free members see locked faces.
        return InterestedListOut(
            count=len(visible), locked=True, plan_needed=catalogue.plan_needed_for(flag), people=[]
        )
    cards = await discovery.cards_for(session, account_ids=[p.account_id for p in visible])
    out = []
    for p in visible:
        card = cards.get(p.account_id)
        snippet = await discovery.get_snippet(session, account_id=p.account_id)
        out.append(
            InterestedPersonOut(
                account_id=str(p.account_id),
                at=p.at,
                photo_url=card.photo_url if card else None,
                age=card.age if card else None,
                locality=snippet.locality if snippet else None,
                profession=snippet.profession if snippet else None,
            )
        )
    return InterestedListOut(count=len(visible), locked=False, plan_needed=None, people=out)


@router.get("/interested", response_model=InterestedOut)
async def interested(
    session: DbSession, account_id: AuthenticatedAccount, for_candidate: UUID | None = None
) -> InterestedOut:
    """Who shortlisted and who viewed the context's profile. Free: counts with
    locked faces. Gold: the people. Blocked people never appear."""
    ctx = await _context(session, account_id, for_candidate)
    ents = await billing.entitlements_for(session, account_id=ctx)
    hidden = await safety.blocked_ids(session, account_id=ctx)
    return InterestedOut(
        shortlisted=await _interested_list(
            session,
            people=await billing.who_shortlisted(session, account_id=ctx),
            unlocked=ents.see_who_shortlisted_you,
            hidden=hidden,
            flag=catalogue.SEE_WHO_SHORTLISTED_YOU,
        ),
        viewed=await _interested_list(
            session,
            people=await billing.who_viewed(session, account_id=ctx),
            unlocked=ents.see_who_viewed_you,
            hidden=hidden,
            flag=catalogue.SEE_WHO_VIEWED_YOU,
        ),
    )
