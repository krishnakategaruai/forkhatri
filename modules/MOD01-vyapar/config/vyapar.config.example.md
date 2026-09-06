---
purpose: Placeholder configuration entries for MOD01-Vyapar third-party/config
  dependencies identified during Business Requirements (Step 1) and
  Functional Requirements (Step 2). Populate real values in the actual
  deployment secret store — this file documents what exists and why, never
  real credentials.
status: Placeholder — created autonomously per standing instruction to
  represent config needs as placeholder entries rather than open questions.
updated: 2026-09-06
---

# MOD01-Vyapar — Configuration placeholders

These are the external/config dependencies BR- and FR-level analysis
already knows this module will need. Downstream Tech Reqs (Step 7) and
Security & Performance (Step 8) own the authoritative schema and
secret-management mechanism (e.g., environment variables via the platform's
secrets manager, per ADR-004's Identity & Trust Service boundary for
anything identity/KYC-related). This file exists so no BR/FR was left
blocked pending "which vendor" or "what exact number" — that decision is
deferred to whichever later step actually integrates the vendor or tunes
the value, consistent with ADR-004 (Identity & Trust Service is the sole
owner of external KYC-provider calls; Vyapar itself never calls a
verification provider directly, per ARCHITECTURE.md's container diagram).

| Key | Purpose | Owner (per ARCHITECTURE.md) | Placeholder value |
|---|---|---|---|
| `BUSINESS_REGISTRY_VERIFICATION_API_ENDPOINT` | Business identity/ownership check (e.g., GST/company-registry-class lookup) invoked via Identity & Trust Service's external KYC integration, not directly by Vyapar (FR02/FR03) | Identity & Trust Service (external KYC/PAN/GST APIs, ARCHITECTURE.md System Context) | `<TO_BE_SET_AT_INTEGRATION_TIME>` |
| `PROFESSIONAL_LICENSE_VERIFICATION_API_ENDPOINT` | Professional credential/license lookup (domain-specific registry, varies per profession) (FR04) | Identity & Trust Service | `<TO_BE_SET_AT_INTEGRATION_TIME>` |
| `VYAPAR_VERIFICATION_SLA_DAYS` | Business-rule threshold: max days a Level-3 Vyapar verification request may sit before automatic escalation to human review (BR01, FR07) | Vyapar module (business rule, not infra) | `5` (default assumption — revisit with real data once V1 traffic exists) |
| `VYAPAR_PROMOTION_TIER_CONFIG` | Defines the promotion/subscription tiers referenced by BR07/FR52 (verified-listing promotions) and their visual-distinction rule (commercial vs. organic, per Dashboard's fair-exposure principle) | Vyapar module | `<TO_BE_DEFINED_AT_TECH_REQS_STEP>` |
| `OBJECT_STORAGE_BUCKET_VYAPAR_MEDIA` | Bucket/container reference for business/professional profile media and verification evidence uploads | Shared Object Storage/CDN (ARCHITECTURE.md) | `<TO_BE_SET_AT_INTEGRATION_TIME>` |
| `VYAPAR_REVERIFICATION_CADENCE_DAYS` | Business-rule threshold: how often a `Verified` profile/listing must automatically re-run Level-3 checks (BR01 DEC-001, FR08) | Vyapar module (business rule, not infra) | `180` (default assumption — revisit with real data once V1 traffic exists) |
| `VYAPAR_MIN_PARTNERSHIP_VERIFICATION_LEVEL` | Minimum member verification level (per Identity & Trust Service's tiering) required by both parties before a `Partnership` request may be created or remain active (BR05, FR33/FR36) | Vyapar module (business rule), enforced against Identity & Trust Service's verification-level data | `Level-2` |
| `VYAPAR_ENQUIRY_RESPONSE_SLA_DAYS` | Elapsed-time transparency threshold shown to a submitter when a poster has not yet responded to a `BusinessEnquiry` — a display threshold only, not an auto-transition trigger (BR06, FR43) | Vyapar module (business rule, not infra) | `3` (default assumption — revisit with real data once V1 traffic exists) |
| `VYAPAR_SEARCH_INDEX_REFRESH_INTERVAL_SECONDS` | Maximum bounded staleness window for the shared Search Service index reflecting closed/rejected/lapsed listings (BR04, FR29) | Vyapar module, via shared Search Service integration (ADR-007) | `60` (default assumption — revisit at Tech Reqs/Security & Performance step for real performance tuning) |

No BR or FR in `01-business-requirements.md` / `02-functional-requirements.md`
is blocked by these placeholders — they are recorded here per this
project's autonomous-execution instruction ("represent config values as
placeholder entries, not open questions") so Step 7 (Tech Reqs) has a
documented starting inventory rather than rediscovering these needs from
scratch.
