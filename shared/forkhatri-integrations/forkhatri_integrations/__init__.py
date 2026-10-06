"""ForKhatri shared integration seams.

Three independent parts, each with one public interface module:

- `forkhatri_integrations.payments`  — take money, refund it, pay people out.
- `forkhatri_integrations.messaging` — send SMS, WhatsApp, email and push.
- `forkhatri_integrations.delivery`  — dispatch a module's outbox with retries.
- `forkhatri_integrations.places`    — live India place search (state, district, city, area).

Every part is chosen by name (`get_gateway("sandbox")`, `get_sender("sms", "console")`)
with configuration passed in by the calling module from its own settings. The
library never reads a module's `.env`. Real vendors are added later as one
adapter file plus one `register_*` call; see BACKLOG.md for the candidates.
"""

__version__ = "0.1.0"
