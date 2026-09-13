# ForKhatri Unified Umbrella App Interpretation

**Status:** Product-owner interpretation for all modules  
**Date:** 2026-09-13  
**Scope:** ForKhatri parent application and its modules  

## Purpose

This document records the intended relationship between ForKhatri and the modules that were planned separately in the repository.

The product decision is:

> ForKhatri is one umbrella application. Vyapar, Milavn, Mangaly, Counsel, Dashboard, Payment Services, and Loans & Finance are modules inside that application.

The modules may retain separate business boundaries, requirements, internal components, databases, services, operating models, and release plans. Those internal boundaries must not become separate user-facing applications or separate platform identities.

This document corrects interpretations that could cause the implementation to create multiple apps or multiple unrelated logins. It does not redesign the modules or invent new cross-module business behavior.

## Final interpretation

ForKhatri should be experienced as:

```text
ForKhatri application
├── One sign-up and sign-in
├── One member identity and account
├── One session and account settings area
├── One shared app shell and navigation
├── Dashboard / home
├── Vyapar
├── Milavn
├── Mangaly
├── Counsel
├── Payment Services
├── Loans & Finance
└── Shared notifications, trust, help, safety, and governance surfaces
```

The user should be able to move between modules without creating another account, signing in again, or feeling that they have left the ForKhatri application.

## What the source documents intended

The high-level product sources consistently describe ForKhatri as the parent ecosystem:

- The Complete High-Level Business Requirements document calls ForKhatri a community ecosystem with a common platform foundation and seven core modules.
- The Master Product Requirements Document describes a platform plus business modules, unified identity, common trust, a central Dashboard, and one future AI/community assistant.
- The Brand Foundation describes one ForKhatri brand, mission, trust model, and community philosophy.
- The Founder Execution Roadmap describes one product lifecycle and introduces modules as parts of the larger ForKhatri strategy.
- `modules/modules.md` explicitly describes ForKhatri as one ecosystem with unified member identity and trust beneath the modules.
- `ARCHITECTURE.md` states that ForKhatri is the single system in scope and defines one Web Client for the platform.

Therefore, the parent relationship is not an invention added by this document. It is the correct reading of the original product direction.

## What was misunderstood or expressed dangerously

### 1. “Independent module” was allowed to sound like “independent app”

The product documents use phrases such as “independently managed,” “independently capable,” and “each module has its own lifecycle.” These should mean:

- separate business capability;
- separate requirements and delivery artifacts;
- separate domain ownership;
- separate operating responsibilities;
- separate KPIs and revenue logic; and
- the ability to evolve without rewriting unrelated modules.

They must not mean:

- a separate consumer application;
- a separate ForKhatri account;
- a separate platform login;
- a second member identity;
- a separate global profile; or
- a separate user-facing brand by default.

### 2. Module-level login screens were treated as account boundaries

Several module UX and UI documents contain screens named “Sign Up,” “Log In,” “Forgot Password,” or “OTP.” Those screens are valid as module entry flows only if they are implemented as ForKhatri identity flows.

They must not create module-specific credentials or accounts. The correct interpretation is:

```text
ForKhatri Sign up / Sign in
        ↓
Shared member identity
        ↓
Module onboarding or module access
```

The module may explain why a user is entering it, but the authentication authority remains the parent platform.

### 3. Mangaly’s interim login implementation was mistaken for the final product model

Mangaly’s later technical documents explicitly record an interim account and credential system because Mangaly is being built before the shared Identity & Trust Service exists. They also record migration debt into the future platform identity service.

That is a build-order workaround, not the desired product architecture. Mangaly must ultimately use the same ForKhatri identity as every other module. Its separate service and database are privacy and security boundaries, not permission to become a separate app.

### 4. Separate services and databases were mistaken for separate applications

The architecture deliberately isolates some backend components:

- Mangaly has a dedicated service and database because of sensitive matrimonial, family, privacy, and safety data.
- Payment Services and Payments Infrastructure are separated because their responsibilities and payment-data risks differ.
- Loans & Finance is isolated because of financial and regulatory risk.
- Lower-risk modules can run as packages inside the Core Platform modular monolith.

These are implementation boundaries behind one application. The user-facing application, identity, navigation, and product relationship remain unified.

### 5. Module-specific roles were confused with separate users

A person may act as a candidate, parent, organizer, business owner, professional, customer, participant, merchant, or administrator in different contexts. These are contextual roles and permissions attached to one ForKhatri identity.

They must not be modeled as unrelated accounts merely because different modules use different role names.

Mangaly’s “parent” terminology is a matrimonial family responsibility category. It is unrelated to the “parent application” or ForKhatri umbrella concept.

## Corrected rules for the parent application

These rules should govern all future BR, FR, UX, UI, architecture, implementation, and test work.

### Identity and authentication

1. ForKhatri owns the canonical member identity.
2. A member has one ForKhatri account and one canonical `member_id`.
3. Sign-up, sign-in, OTP, password reset, session management, logout, and account deletion are parent-platform capabilities.
4. Modules may request authentication and authorization, but they must not create a second member identity.
5. A module-specific profile, workspace, Home Circle, organizer role, professional listing, or business role is linked to the existing member identity.
6. A module may have additional domain verification, but domain verification is not a second login.

### User experience

1. The application opens with ForKhatri branding and the shared session.
2. Module entry points appear inside the ForKhatri navigation and Dashboard experience.
3. A module may have its own onboarding journey, but it starts after the shared ForKhatri identity is established.
4. Module screens may use module terminology and visual patterns, but the application shell must remain recognizable as ForKhatri.
5. Switching modules must not require re-authentication unless a genuinely higher-risk authorization step requires explicit confirmation.
6. Notifications and deep links must return the user to the relevant module inside the same ForKhatri application context.

### Data and backend boundaries

1. Module data ownership remains real and must be preserved.
2. Sensitive data may remain in isolated databases or services.
3. Backend isolation must not create separate consumer identity systems.
4. Cross-module access must use explicit contracts, events, or authorized service calls.
5. The parent platform owns identity, authentication, global account lifecycle, shared trust foundations, common notification infrastructure, and platform governance.
6. Modules own their domain records and domain-specific permissions.

### Account lifecycle

1. Account deletion, deactivation, reactivation, and recovery begin at the ForKhatri identity layer.
2. The parent identity layer orchestrates the effect on module data.
3. A module must not leave behind an orphaned independent account when a member leaves ForKhatri.
4. A member may pause or leave one module without automatically deleting the ForKhatri account or unrelated module participation, subject to the module’s own rules.

## Module-by-module interpretation

| Module | Correct parent-app interpretation | What remains module-specific |
|---|---|---|
| Vyapar | A ForKhatri module opened from the shared app and shared identity. | Business profiles, professional listings, opportunities, enquiries, reputation signals, promotions, and business workspace behavior. |
| Milavn | A ForKhatri module for real-world community participation, using the shared member account. | Activities, events, circles, participation, organizer capabilities, location/privacy behavior, and event trust signals. |
| Mangaly | A ForKhatri module, not a separate matrimonial app. Its sensitive service/database boundary is internal. | Matrimonial profile, Home Circle, family authorization, discovery, compatibility, selective sharing, communication, safety, and Mangaly operations. |
| Counsel | A ForKhatri module accessed through the shared account. | Expert profiles, credentials, consultation requests, appointments, and consultation-specific workflows. |
| Dashboard | The parent application’s central home and context surface, not a separate module app. | Personalization, local information, cross-module surfacing, prioritization, and dashboard-owned records. |
| Payment Services | A ForKhatri module accessed through the shared account. | Bill payments, receipts, benefits, coupons, merchant relationships, and payment-service business rules. |
| Loans & Finance | A ForKhatri module accessed through the shared account. | Financial-product discovery, eligibility, referral/application tracking, partner workflows, and financial education. |

## What should be kept versus corrected

### Keep

- Separate module requirements and SDLC documents.
- Separate module domain ownership.
- Separate internal components where the domain requires them.
- Separate databases or services for sensitive or regulated capabilities.
- Module-specific verification and authorization rules.
- Module-specific business models, KPIs, and operating workflows.
- Explicit contracts for cross-module communication.

### Correct

- Replace “module login” with “ForKhatri login with module entry/onboarding.”
- Replace “module account” with “module profile, role, or workspace linked to the ForKhatri account.”
- Replace “separate app” language with “module surface inside the ForKhatri app,” unless a future product decision explicitly changes that.
- Treat Mangaly’s interim credentials as migration debt, not a final identity decision.
- Ensure every module’s UX starts from the shared app shell and shared session.
- Make the parent identity and app-shell responsibility explicit in every future module architecture document.

## Documentation findings requiring later cleanup

These findings do not require redesigning the modules now, but they should be corrected before implementation begins:

1. `docs/PreStartResearch/PROCESS-README.md` contains an older module-wave and status picture that no longer matches the newer module artifacts and architecture decisions.
2. `modules/modules.md` still has a Draft status and blank approval area even though later architecture documents treat its decomposition as sealed input.
3. Some module UX/UI documents repeat login and sign-up screens without explicitly stating that the screens use the shared ForKhatri identity.
4. Mangaly’s interim identity implementation needs an explicit parent-platform migration boundary and migration plan.
5. Future module documents should include a standard statement: “This module is a domain capability inside the ForKhatri application and does not own a separate platform login.”
6. The root architecture should be treated as the authority for the single Web Client and shared Identity & Trust direction, while module architecture documents describe internal service boundaries only.

## Non-goals of this document

This document does not:

- merge module requirements into one undifferentiated specification;
- decide the final cross-module product workflows;
- invent dependencies between modules;
- remove module-level privacy or security isolation;
- decide the launch order;
- redesign Mangaly’s family roles;
- replace the existing module BR, FR, UX, UI, ER, or security documents; or
- claim that all modules are already implemented.

## Final decision

The correct mental model is:

> One ForKhatri application, one member identity, one shared app shell, and multiple independently bounded business modules inside it.

The modules are separate in planning and internal engineering responsibility. They are not separate user-facing products by default, and they must not require separate logins.

