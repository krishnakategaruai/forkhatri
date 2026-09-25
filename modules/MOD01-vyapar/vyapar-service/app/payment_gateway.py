# [IMP37 — Refactor B] Import shim. The PaymentGateway seam (TR051) moved to
# app/integrations/payments/gateway.py so every host-facing adapter lives
# under app/integrations/. Existing imports (`from app.payment_gateway
# import ...`) keep working unchanged through this module.
from app.integrations.payments.gateway import (  # noqa: F401
    CheckoutSession,
    DevSandboxGateway,
    GatewayEvent,
    GatewayUnavailable,
    PaymentGateway,
    RazorpayGateway,
    get_gateway,
    parse_razorpay_event,
)
