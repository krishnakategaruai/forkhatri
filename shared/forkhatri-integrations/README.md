# ForKhatri shared integrations

One place for the things every module needs from the outside world:

| Part | What it does | Use it as |
|---|---|---|
| `payments` | Take a payment, check it, refund it, pay a person out, read the provider's webhook | `from forkhatri_integrations import payments` |
| `messaging` | Send SMS, WhatsApp, email and push | `from forkhatri_integrations import messaging` |
| `delivery` | Send what a module queued in its outbox, with retries and backoff | `from forkhatri_integrations import delivery` |

It uses the Python standard library only. It never reads a module's `.env`: the module passes its own settings in.

**No real vendor is connected yet.** The owner picks vendors later (see [BACKLOG.md](BACKLOG.md)). Until then these adapters exist:

| Part | Adapter | Meaning |
|---|---|---|
| payments | `none` | Payments are off. Every call raises `PaymentsNotConfigured`, so a screen can say so plainly. |
| payments | `sandbox` | Local development only (refused unless the module says it runs locally). No money moves. It signs its own webhook events, so a module's real webhook path can be tested. |
| payments | `payment_services` | HTTP client for the planned ForKhatri Payment Services module (MOD06). The contract is at the top of `payments/adapters.py`. |
| messaging | `console` | Local development only. Writes the message to the log. |
| messaging | `disabled` | The channel is off. Nothing is sent and the caller is told. |

## Install

Each service installs it into its own virtualenv (already done on this machine):

```
<service>/.venv/Scripts/python -m pip install -e shared/forkhatri-integrations
```

Counsel and Vyapar list it in `requirements.txt`. Every module imports it only inside its opt-in adapter, so a service without it installed still runs as before.

## How each module uses it today

All adoption is **opt-in by configuration**. Every module's current default behaviour is unchanged.

| Module | Payments | Messaging and delivery | Switch it on with |
|---|---|---|---|
| Platform sign-in (identity-service) | none | Sign-in codes by SMS and email through the shared senders | `SMS_PROVIDER=shared` / `EMAIL_PROVIDER=shared`, plus `SHARED_SMS_SENDER` / `SHARED_EMAIL_SENDER` (and `SMS_DLT_TEMPLATE_ID` for Indian SMS) |
| Vyapar (MOD01) | `SharedLibraryGateway` in `app/integrations/payments/gateway.py`; the webhook route also accepts `X-ForKhatri-Signature` | In-app only today (not changed) | `PAYMENT_GATEWAY=shared:<adapter>` (default stays `dev_sandbox`) |
| Milavn (MOD02) | `SharedLibraryPaymentServices` in `app/components/payments/interface.py`; `/payments/events` also accepts shared-library signed events | Its `notification_outbox` is ready for a `delivery.Dispatcher` store (backlog) | `PAYMENTS_PROVIDER=shared:<adapter>` |
| Mangalya (MOD03) | `SharedLibraryGateway` in `app/components/billing/gateway.py` | In-app only today (not changed) | `PAYMENT_GATEWAY=shared:<adapter>` (empty = current Razorpay/sandbox rule); `PAYMENTS_ALLOW_SANDBOX=true` for `shared:sandbox` |
| Counsel (MOD04) | `SharedPaymentProvider` in `app/components/money.py`, plus `POST /payments/events` | Its `delivery` queue is sent by `delivery.Dispatcher` every minute (`app/components/outbound.py`) with senders from `SMS_PROVIDER`, `WHATSAPP_PROVIDER`, `EMAIL_PROVIDER` and `PUSH_PROVIDER` | `PAYMENT_PROVIDER=sandbox`, `payment_services` or a vendor name (default stays `mock`); add `email`, `sms`, `whatsapp` or `push` to `NOTIFICATION_CHANNELS` |

The horoscope service (Node) has no payments or messaging.

## Adding a real vendor later (one file each)

Payments: write a class with the `payments.PaymentGateway` methods (`create_charge`, `get_charge_status`, `verify_return`, `cancel_charge`, `refund`, `create_payout`, `parse_event`). Put it in `payments/<vendor>.py` and register it in `payments/__init__.py`:

```python
register_gateway("razorpay", lambda key_id="", key_secret="", webhook_secret="", **_: RazorpayGateway(key_id, key_secret, webhook_secret))
```

Messaging: write a class with `name`, `channel`, `available`, `live` and `async send(message) -> SendResult`. Put it in `messaging/<vendor>.py` and register it:

```python
register_sender("sms", "msg91", lambda channel, auth_key="", sender_id="", **_: Msg91Sender(auth_key, sender_id))
```

Then set the module's setting to the new name (for example `PAYMENT_GATEWAY=shared:razorpay`) and pass the vendor keys through the module's settings. No module code changes.

Rules for every adapter:

- **Money:** amounts are integers in paise, an idempotency key goes on every call, and webhooks are verified against the raw body.
- **Retries:** timeouts and 5xx responses return `retryable=True`; a wrong number or a refused template returns `retryable=False`.
- **Logging:** never log a full phone number, email address or one-time code (use `_common.mask`).

## Tests

```
<any service>/.venv/Scripts/python -m unittest discover -s shared/forkhatri-integrations/tests
```
