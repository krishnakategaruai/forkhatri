---
project: ForKhatri
artifact: Parent Application Data Model
step: 7a
status: Ready for Review
---

# Parent Application Data Model

## Decision

The static parent webpage introduces no new business-domain database. It renders demo state and defines integration contracts only.

## Future parent-owned records

If persistence is required later, the parent platform may own records such as:

- `member_id` reference to Identity & Trust;
- dashboard preferences;
- parent-level notification index/read state;
- module availability/configuration;
- parent-level navigation preferences.

The parent shell must not duplicate module-owned records such as matrimonial profiles, events, business listings, payment transactions, or loan applications.

## Identity rule

`member_id` is the canonical identity reference. No parent-shell or module-specific login table is introduced by this webpage.

## Cross-module rule

Module data is consumed through explicit contracts or privacy-filtered events. The parent page never queries a module database directly.

