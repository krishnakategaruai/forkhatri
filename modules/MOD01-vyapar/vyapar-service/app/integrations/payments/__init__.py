# [IMP37] Payment adapters (TR051 PaymentGateway seam). A host with its own
# payment service implements the PaymentGateway protocol in gateway.py and
# returns it from get_gateway() for its PAYMENT_GATEWAY value.
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
