# MOD04 Counsel — Traceability matrix

**Document status:** 2026-11-22, "as built". BR (01) -> FR (02) -> SCR (03) -> API (API-REFERENCE.md) -> TBL (07a) -> TC (05). Tests column: "manual" because no automated Counsel tests exist.

| BR | FR | SCR | API | TBL | TC |
|---|---|---|---|---|---|
| BR-01 onboarding and verification | FR-001..009 | SCR-13, 11, 18, 19, 20 | 021-030, 088-096 | 05, 06, 07, 08, 02, 03, 04, 29 | TC-001..006 |
| BR-02 discovery | FR-010..017 | SCR-01, 02, 03, 09 | 006-008, 013-020 | 05, 09, 23, 39, 40 | TC-007..012, 044 |
| BR-03 reputation, badges, reviews | FR-070..072 | SCR-03, 06, 11 | 018, 038, 053 | 22, 32, 12 | TC-035, 036 |
| BR-04 pricing and fees | FR-040, 041, FR-020 | SCR-04, 14, 06, 17, 24 | 019, 031-033, 102-103 | 09, 12, 14, 30 | TC-047, 048 |
| BR-05 scheduling | FR-021..023, 030, 031 | SCR-04, 15, 11 | 020, 034-037, 043, 056-060, 072 | 10, 11, 12, 31 | TC-013, 014, 016-018 |
| BR-06 payment, cancellation, refunds | FR-030, 032, 034, 042, 043, 091 | SCR-04, 06, 22 | 043-050, 075, 099-100 | 12, 13, 14, 27 | TC-015, 019-022, 038, 043 |
| BR-07 payouts and earnings | FR-033, 044..046 | SCR-16, 11 | 039-042 | 12, 14, 15, 36 | TC-023, 024 |
| BR-08 consultation room | FR-060..068 | SCR-07, 06 | 051-052, 073, 074, 076-086, 110 | 16..21, 38 | TC-028..034 |
| BR-09 follow-ups and questions | FR-050, 051 | SCR-04, 05, 14, 11 | 061-071 | 33, 34, 35 | TC-025..027 |
| BR-10 notifications and reminders | FR-080..082, 035 | SCR-08 | 009-010 | 24, 25 | TC-037 |
| BR-11 safety, moderation, admin | FR-090..093 | SCR-17..24, 03 | 011-012, 055, 087..104 | 26, 27, 28, 29, 30 | TC-038, 040 |
| BR-12 privacy | FR-100..103 | SCR-10 | 003-005, 107-109 | 37, 29 | TC-039, 042 |
| BR-13 languages | FR-110, 111 | all | all (X-Counsel-Language) | 02 | TC-044, 045 |
| BR-14 boundaries | (no feature; by omission) | - | - | - | - |
| BR-15 growth insights | FR-073 | SCR-11 | 038 | 39, 40 | none |
| Identity (supporting) | FR-120 | SCR-25 | 001, 002 | 01 | TC-041 |

## FR -> API detail (selected)
FR-012 -> API-015; FR-013 -> API-016; FR-030 -> API-043, 045; FR-031 -> API-056..060; FR-032 -> API-048; FR-033 -> API-049; FR-034 -> API-050; FR-045 -> API-042; FR-050 -> API-061..063, 065..069; FR-051 -> API-064, 070, 071; FR-060 -> API-002, 076, 110; FR-100 -> API-003; FR-101 -> API-004, 005; FR-103 -> API-107..109.

## Endpoints with no matching screen call (API only)
API-011, 012 (blocks), API-055 is used by SCR-03 only for providers, API-073 (recap rebuild), API-075 (gateway), API-104 (audit log, no admin screen), API-105 (media), API-106 (banner), API-107..109 (platform).
