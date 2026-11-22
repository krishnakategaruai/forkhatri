# MOD04 Counsel — Glossary

**Document status:** 2026-11-22. Terms as used in the product and code.

| Term | Meaning |
|---|---|
| Counsel | ForKhatri module MOD04: paid one-to-one advice marketplace (web 3014, API 8014) |
| Seeker | Member who books or asks (code role `seeker`; buyer for purchases) |
| Consultant / provider | Member offering advice (table `provider`; UI "consultant") |
| Expertise area | A taxonomy entry such as Legal or Finance & Tax (26 seeded); "regulated" areas have compliance rules |
| Evidence | A claim by a consultant (experience, qualification, certification, registration, business, portfolio) with optional private proof |
| Verification dimension | One thing an admin checked: identity, contact, experience, qualification, certification, registration, business, portfolio. There is no single "verified" stamp |
| Compliance rule | Per area and country: dimensions that must be verified before a service can go active, the disclaimer key, and whether recording is allowed |
| Service | A consultation a consultant sells: title, minutes, price, formats, rules |
| Slot | A bookable start time computed from weekly windows or fixed times, exceptions, notice, advance and buffer |
| Window / fixed slot | Weekly open range cut every 15 minutes / one exact start time |
| Custom time (time request) | A seeker's proposed time outside listed slots; consultant accepts (held for payment) or declines |
| Available now | Consultant online for 30/60/120 minutes; next 5-minute mark bookable |
| Booking | The commercial unit and state machine; pending_payment, confirmed, in_progress, completed, cancelled_by_seeker, cancelled_by_provider, no_show_seeker, no_show_provider, expired |
| Hold / pay_by | Time an accepted custom-time booking waits for payment (max 24 h) |
| Snapshot | Price, fee and cancellation policy copied onto the booking at creation |
| Gross | The amount charged for the booking (today equals the service price) |
| Platform fee | ForKhatri's fee. Built as percent (default 2) taken from the consultant's price; owner definition is an additional fee for using Counsel (gap G-01) |
| Provider payable | Amount owed to the consultant before refunds (today price minus fee) |
| Ledger | `ledger_entry` rows recording gross, fee, payable, refund, payout |
| Payout hold | 24 h after completion before payout is allowed |
| Payout method | UPI id or bank account + IFSC, stored encrypted |
| Sandbox / mock | Test payment modes where no money moves |
| Follow-up | 1-3 cheaper check-ins with the same consultant after a completed consultation (table `package`) |
| Paid question | Written question with a price and 1-7 day answer time; auto-refund if unanswered |
| Purchase | A follow-up or question bought (table `purchase`) |
| Room | Browser call workspace for a booking: call, chat, notes, actions, files |
| Ticket | Single-use 60-second token for the room WebSocket |
| STUN / TURN | WebRTC helpers: STUN finds addresses (Google STUN in use); TURN relays media (not available today) |
| Peer-to-peer | Media flows directly between the two browsers; the server only relays signalling |
| Recap | After-call summary of shared notes, actions, files (AI summary only if enabled) |
| Badge / level | Milestone earned from real numbers (consultations, clients, repeat_trust, highly_rated, on_time, reliable, hours, verified_professional, tenure) |
| Standing | new, rising, established, senior, distinguished; shown, does not change price or ranking |
| Best match | Default ranking: 0.35 relevance, 0.20 trust, 0.15 experience, 0.10 proven, 0.10 satisfaction, 0.10 reliability |
| Bayesian rating | Rating pulled toward the platform average using 5 imaginary reviews |
| Reply time | Median hours to answer time requests and questions over 180 days (shown from 2 samples) |
| Impression / profile view | Counters for how often a consultant appeared in search / was viewed (unique per day, hashed) |
| Near me | Distance to the nearest of 45 listed cities (online consultations; nearness is local knowledge) |
| Dispute | A participant's claim on a booking, decided by admin with a refund percent |
| Report | A member flag on a provider, service, booking, message or member |
| Block | Pair-wise refusal to book or ask (API only today) |
| Audit log | Append-only record of money, trust and privacy actions |
| Erased member | A member whose Counsel data was deleted; shown as "Deleted member" |
| Admin | Member with platform scope `counsel.admin` or listed in ADMIN_MEMBER_IDS (dev) |
| Hub | ForKhatri entrance web app (3100) |
| MOD06 / MOD07 | Payment Services / Loans & Finance modules (Welfare Trust lives in MOD07) |
| BR / FR / SCR / API / TBL / TC | Business requirement / functional requirement / screen / endpoint / table / test case IDs |
| Erase | Delete or detach every row and file about a member in one transaction (`privacy.erase_member`); added 2026-11-22 |
| Tombstone / stand-in id | One-way id `sha256("counsel-erased:" + member + service key)` that retained rows point at instead of the real id; shown as "Deleted member" |
| Deletion receipt | Row in `erased_member` plus an audit line with counts; proof that erasure was done |
| Kind A / kind B | A: ForKhatri account deleted, identity erases in all modules. B: "Delete my data in Counsel" only; the ForKhatri account stays |
| nothing_to_delete | Answer of a repeated erase: idempotent, nothing left |
