# Mangaly backlog

Items the owner has asked for that are not yet designed or built. Each moves
into the SDLC pipeline (BR → FR → UX → …) when it is picked up.

| # | Item | Asked | Notes |
|---|------|-------|-------|
| B1 | **Horoscope / kundali matching: design** | Owner, 2026-09-24 | Guna Milan (Ashtakoota, 36 points) and Manglik/dosha check from each person's birth date, time and place (the `horoscope` profile section already stores these). Needs: a calm, respectful presentation (never a pass/fail stamp on a person), an opt-in per family (many families do not use it), who may see a match score (parents vs candidates), and an astrologer-verified calculation source. Design first, then build. |
| B2 | **Recommendation engine** | Owner, 2026-09-24 | Go beyond today's rule-based "For you" shelves: learn from each family's saves, requests, accepts and declines (and the parents' suggestions) to rank matches, with the two-way "looking for" rule and privacy boundaries always applied, and a plain-language "why this person" for every recommendation. Must stay explainable, never popularity-driven (existing rule), and must not leak one family's behaviour to another. |

## Owner decisions (2026-09-25) — being implemented

- **Waiting period:** after a decline, the sender's side cannot ask the same person again for 90 days (and does not see them in Discover); after withdrawing a request, 21 days. The person who declined may still reach out any time. (Research: LinkedIn blocks re-inviting for 3 weeks after a withdrawal; Shaadi.com lets the decliner accept later with no wait.)
- **Parents after connection:** parents and guardians see the match's full name once both accept; contact details only when the candidate shares them or approves a request made from the profile.
- **Siblings and relatives** can only suggest a profile to the candidate and parents; only the candidate, a parent or a guardian can send a request.
- **Vikram (test persona)** gets a new family of his own; his stale access to Asha's profile is removed.
- **17 leftover test accounts** from the retired Mangaly-only sign-in are deleted.
- **City names** stay in English for now.
