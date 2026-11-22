# MOD03 Mangalya - Glossary (2026-11-22)

| Term | Meaning |
|---|---|
| Mangalya | The ForKhatri matrimony module (MOD03). Spelled "Mangaly" in older docs; inner folders and code still use `mangaly-`. |
| Candidate | The person to be married; owns the profile and the plan entitlements. |
| Home Circle | A candidate's family group: parents, guardian, siblings, relatives, each with an exact relation. |
| Role / relation | Role = parent, guardian, sibling, relative. Relation = exact (mother, father, paternal uncle ...), migration 040. |
| Managed profile | A profile a parent made for a son or daughter, kept under the parent until the child takes over (migration 065). |
| Take over | The child signs in with the number the parent gave and answers "is this you?"; consent time is stored. |
| Maker gate | Old rule: only a face-verified person may create a profile for someone else (DEC-V1-025). DEC-V1-035 makes the check optional; server change pending. |
| Face match / "photos confirmed" | Browser comparison of a live capture with the member's own photos; server passes only if distance < 0.45; expires after 2 years; limits in 08. |
| Discover | Photo wall of mutual-preference matches. |
| For you | Titled rows of matches, each with one honest reason; score never shown. |
| Strong / Good match | The only words shown from the hidden 1-10 engine score (8+ and 7.5+). |
| AI matchmaker | The family's own words read into a closed list of wishes with 1-10 importance, plus six 1-10 scales (DEC-V1-031). |
| Must-have | Importance 10; removes someone only when a stated fact clearly misses it, in both directions. |
| Guna Milan / Ashtakoota | North-Indian 36-point matching, 8 kootas. |
| Porutham | South-Indian 10-point matching; Rajju and Vedha essential. |
| Manglik / Mangal dosha | Mars-placement tradition; calculated separately, never part of the 36. |
| Rashi, Nakshatra, Gotra | Moon sign, birth star, lineage. |
| Jathakam / kundli | The horoscope chart (Telugu / Hindi words). |
| Biodata | The family's one-page profile (PDF or photo). The biodata reader fills the form from it after a consent line. |
| Incognito chat | Candidate-to-candidate session chat; deleted when either leaves or after 30 minutes idle. |
| Direct chat | Ordinary kept one-to-one chat between linked people. |
| Families' group | Optional group chat of both candidates and both circles; each message names writer and relation. |
| Request | A connection request; the candidate, mother, father or guardian may answer. |
| Waiting period | 90 days after a decline, 21 days after a withdrawal. |
| Broker / Agent | A marriage agent with a membership: holds clients, shares profiles, exports biodata; contact limits apply. |
| RM | Relationship manager for the Assisted plan. |
| Gold / Assisted / Agent / Agent Connect | Plans. They buy capability, never visibility. Prices shown with GST included. |
| Wedding arrangements | After a match: stages first_meeting, families_agreed, wedding_fixed; places and partner offers. |
| Guides | Help articles in en, hi, te, mr, kn. |
| Device draft | A profile in progress saved in IndexedDB on the device until published. |
| Operator | Operations staff handling cases, reports, suspensions. |
| RLS | Row-level security in PostgreSQL: the database decides which rows a caller sees. |
| DEC-V1-xxx | Numbered owner or product decision in `v1-decisions.md`. |
| DPDP | India's Digital Personal Data Protection Act; duties start about May 2027. |
