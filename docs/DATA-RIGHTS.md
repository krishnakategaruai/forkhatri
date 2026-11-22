# Data rights: what a member can delete, and what stays (2026-11-22)

Plain words for the owner. Built as described; the deletion screens have not yet been checked in a browser. Every "legal basis" below is a working assumption marked **needs lawyer**: nothing here is legal advice.

## 1. What a member can delete

Both kinds are immediate (no waiting period). The member confirms with their password or a fresh one-time code and types the word DELETE. Three attempts per hour.

- **Kind A, "Delete my ForKhatri account"** (hub account sheet): the ForKhatri identity (phone, email, name, password, sessions) and the member's data in every module (Vyapar, Milavn, Mangalya, Counsel), including photos, files and notifications. The member is signed out everywhere at once. An admin must give up their admin role first.
- **Kind B, "Delete my data in this module"** (that module's own settings): everything that module holds about the member. The ForKhatri identity and the other modules stay, and the member can come back to the module later as a new member.

If one module cannot finish at once, the member is already signed out and cannot sign in; the system retries for up to 7 days and the admin console shows stuck deletions.

## 2. What other people see afterwards

Where the deleted member's name was shown, others see "Deleted member", with no contact details. Open jobs and listings are removed; future events are cancelled and attendees told; Milavn circles pass to another organiser; Counsel bookings in the future are cancelled with the other side told and a refund recorded; completed Counsel consultations stay for the other person as "Deleted member". Exception today: Mangalya one-to-one chats are removed for both sides (see open decisions).

## 3. What is retained, why, and for how long

No retained record keeps a name, phone, email, photo or free text; the member is replaced by a one-way tombstone that cannot be turned back into the person.

| Where | Retained | Why (needs lawyer) | How long |
|---|---|---|---|
| Platform (identity) | Security and audit log rows (tombstone only); the deletion receipt | Security log retention; proof that deletion was done | Logs: DPDP Rules suggest 1 year (needs lawyer). Audit log and receipt: no period decided (owner must set one) |
| Vyapar | Payment orders; safety cases and reports; audit log; contracts as seen by the other party (tombstoned) | Tax and payment records; protecting other members; the other party's own record | Not decided (needs lawyer); sandbox holds no real money today |
| Milavn | Payments (paid tickets, pledges, a ticket with a refund pending); reports and blocks about or by the member; receipt | Payment records; safety so a harmful person cannot simply return | Not decided (needs lawyer) |
| Mangalya | Reports, cases, suspensions and appeals (tombstone, text removed); paid orders; receipt. A managed profile the child has taken over stays with the child | Safety of other families; payment records | Not decided (needs lawyer) |
| Counsel | Consultations other people took part in (stand-in id, the brief blanked); payment and tax rows where money moved, and the ledger; star ratings without text; report and dispute records; audit trail; receipt | Other party's record; tax and payment law; dispute handling | Not decided (needs lawyer) |

The member is shown this list in plain words on the confirmation page.

## 4. How a member uses these rights

- **Delete:** as in section 1. Hub for kind A; each module's settings for kind B.
- **Export:** members can download their data from some modules (Counsel's export was extended to cover its data). There is no single ForKhatri-wide export yet. Which modules offer export, and in what form, is not verified here.
- **Support:** no grievance officer is named yet (see section 5).

## 5. Not yet built

- Grievance officer (a named person members can write to, with a response time).
- Consent notice and consent record at sign-up.
- Age gate (minimum age check).
- A single ForKhatri-wide data export.
- Browser checks of the deletion screens (type-checked and API-proven only).
- Sign-up block for banned members (see below).

## 6. Decisions waiting for the owner

1. **Counsel unpaid earnings.** An expert's earnings that are eligible but not yet paid out cannot be paid after payout details are deleted. Today they are lost; the member is warned before confirming. Options: pay out before deletion is allowed, keep a minimal payout record until paid, or accept the loss. The payout-retention path is untested.
2. **Banned members signing up again.** A ban is only flagged in the deletion receipt; sign-up is not blocked. Decide whether to block returns (this needs a retained identifier, which needs a lawyer).
3. **Mangalya one-to-one chats.** The contract says the other person should see "Deleted member"; as built the chats are removed for both sides. Decide whether to keep the other person's copy.
4. **Retention periods and legal basis** for every row in section 3, including the audit log.

## 7. Where the detail is

Contract and platform as-built: [ParentApp/ACCOUNT-DELETION.md](ParentApp/ACCOUNT-DELETION.md). Per-table detail: each module's `ACCOUNT-DELETION.md` ([Vyapar](../modules/MOD01-vyapar/ACCOUNT-DELETION.md), [Milavn](../modules/MOD02-milavn/ACCOUNT-DELETION.md), [Mangalya](../modules/MOD03-mangalya/ACCOUNT-DELETION.md), [Counsel](../modules/MOD04-counsel/ACCOUNT-DELETION.md)). Privacy findings: [ParentApp/08-security-performance.md](ParentApp/08-security-performance.md) section C13.
