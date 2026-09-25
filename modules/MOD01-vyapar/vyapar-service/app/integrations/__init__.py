# [IMP37 — Refactor B] Integration edges. Everything a host platform or an
# external system plugs into lives under this package, behind a small
# interface, so the Vyapar core never imports a host:
#
#   identity/       who is calling — IdentityProvider adapters (dev header,
#                   ForKhatri session, personal access token)
#   tokens.py       personal access tokens (agents act on behalf of a member)
#   webhooks/       outbound, signed event deliveries fed by the outbox
#   http_middleware Idempotency-Key replay and per-token write auditing
#   notifications/  NotificationChannel adapters (in-app, web push)
#   payments/       PaymentGateway adapters (Razorpay, dev sandbox)
#   storage/        ObjectStorage adapter (local filesystem in dev)
#
# INTEGRATION-GUIDE.md (module root) explains how a new host supplies its own
# adapter for each seam.
