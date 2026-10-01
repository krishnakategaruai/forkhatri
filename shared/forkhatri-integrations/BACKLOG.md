# Shared integrations backlog

The owner will choose the real providers later (owner, 1 Oct 2026). Each choice below becomes one adapter file in this library plus the keys in the module's settings. Candidates are listed with what they're known for, not as recommendations. Check each vendor's current pricing and terms when choosing.

## V. Vendors to choose (owner decision)

| # | Need | Candidates | Notes |
|---|---|---|---|
| V1 | **Payment gateway** (UPI, cards, netbanking) | Razorpay, Cashfree, PhonePe PG, PayU, Juspay; Stripe for payers outside India | Vyapar and Mangalya already have Razorpay-shaped code, which can be moved in here as the first adapter. Needs a merchant account with KYC. |
| V2 | **Payouts to consultants and organisers** | RazorpayX, Cashfree Payouts, or the chosen gateway's marketplace or route product | Counsel already stores UPI or bank details, encrypted. A marketplace or split-settlement product may also settle GST and TDS questions (Counsel T3). |
| V3 | **SMS** (sign-in codes, reminders) | MSG91, Gupshup, Kaleyra, Exotel, Twilio, AWS SNS | Indian SMS needs **DLT registration** (entity, header and templates) with a telecom operator before any vendor can send. `SMS_DLT_TEMPLATE_ID` is already a platform setting. |
| V4 | **WhatsApp** (booking confirmations, reminders) | Meta WhatsApp Cloud API directly, Gupshup, Interakt, WATI, Twilio | Needs a WhatsApp Business account, a verified business, and approved message templates per language (English, Hindi, Telugu). |
| V5 | **Email** | Resend (the platform already uses it for sign-in email), Amazon SES, Postmark, SendGrid, Zoho ZeptoMail | Needs a verified sending domain (SPF, DKIM, DMARC). |
| V6 | **Push** | Web Push with our own VAPID keys (no vendor, free), Firebase Cloud Messaging, OneSignal | ForKhatri is a mobile-first web app, so Web Push is enough. Vyapar already has a VAPID stub. |
| V7 | **Malware scanning of uploads** | ClamAV (free, runs on our server) | Counsel already supports it (`MALWARE_SCANNER=clamav`). The scanner could move in here if other modules take uploads. |

## B. Build once vendors are chosen

| # | Item | Notes |
|---|---|---|
| B1 | Write the chosen gateway adapter, then switch each module to `shared:<vendor>` | Move Vyapar's and Mangalya's Razorpay code in here so there is one Razorpay adapter, not two. Each module keeps its own webhook route. |
| B2 | Write the SMS, WhatsApp, email and push sender adapters | Platform sign-in switches with `SMS_PROVIDER=shared`. Counsel switches with `NOTIFICATION_CHANNELS`. |
| B3 | **Contact lookup for modules** | Modules don't hold phone numbers or email addresses; the platform does. Counsel's delivery dispatcher marks rows "skipped: no destination" until the platform offers a consented contact lookup, or its notification service does delivery itself. This is a platform decision (see ARCHITECTURE.md ADR-006). |
| B4 | Milavn delivery | Milavn writes a `notification_outbox` that nothing reads yet. Give it a `delivery.OutboxStore` like Counsel's (`counsel-service/app/components/outbound.py`). This belongs to the Milavn workstream. |
| B5 | Vyapar and Mangalya notifications outside the app | Both are in-app only today. Add an outbox and a dispatcher when they need SMS, WhatsApp or push. |
| B6 | Per-person preferences and quiet hours | Which channels a person wants, and no messages at night. These belong with contact lookup (B3). |
| B7 | MOD06 Payment Services | When MOD06 is built, it implements the `payment_services` contract in `payments/adapters.py`, and every module switches with configuration alone (`shared:payment_services`). |
| B8 | GST on platform fees and TDS on payouts | Needs an accountant's rules (Counsel T3). The gateway's processing fee is already reported per charge where the vendor gives it. |
