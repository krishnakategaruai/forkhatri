---
project: [Project Name]
applies_to: 09-implementation-agent, 10-test-automation-agent
status: Draft | Approved
updated: YYYY-MM-DD
---

# Implementation & Test Automation Standards — [Project Name]

**Read this file is a mandatory pre-req for both the Implementation Agent
(Step 9) and the Test Automation Agent (Step 10), before either writes a
single line of code.** It exists because naming and structure conventions
are project/stack-specific — nothing here is a universal law, most of it
is "the project picked one option from several valid ones, now hold the
line on it consistently." Where a section cites a real convention, the
source is named; where it's a project choice among several legitimate
options, that's stated too, so nobody mistakes a house-style pick for an
external standard.

Fill this in once per project (technology stack rarely changes per
module), then only revise it the way `CLAUDE.md` is revised in the
blog-style AI-native SDLC: when an agent gets something wrong twice, the
correction goes in Section 8, permanently.

## 1. Naming conventions

Pick the convention for this project's actual language/stack and record
it — do not leave these as open questions per requirement; that's what
this file is for.

| Element | Convention (fill in) | Example |
|---|---|---|
| Files | e.g. `kebab-case.ts`, `PascalCase.java` | |
| Folders | | |
| Classes / Types | e.g. `PascalCase` | |
| Functions / Methods | e.g. `camelCase`, `snake_case` | |
| Variables / Constants | e.g. `camelCase`, `UPPER_SNAKE_CASE` for true constants | |
| Branches | e.g. `feature/BR01-fr03-claim-status` (include the FR ID so a branch traces back to this pipeline's IDs) | |
| Commit messages | **Conventional Commits** — `type(scope): description`, where `type` is one of `feat`, `fix`, `docs`, `refactor`, `test`, `chore`. This is a real, widely-used external convention, not a project-specific pick, and it's what most changelog-generation tooling (including Step 14's Keep a Changelog output) expects as input. | `fix(claims-api): correct status polling interval per FR01` |

## 2. Requirement-level comment block (Implementation Agent, Step 9)

Per the pipeline rule: **no code is written for a requirement until its
comment block is complete.** The comment is per-requirement, not per-line.

**Exact format:**

```
// [TR0x] <one-line statement of intent>
// Approach: <why this approach was chosen, one or two sentences>
// Traces to: FR0x, SP0x (list every requirement this block of code satisfies)
```

Example:

```javascript
// [TR03] Poll claims-core for status changes every 60s.
// Approach: no event bus exists on claims-core (see IA01), so polling is
// used instead of a webhook; accepted trade-off is up-to-60s staleness.
// Traces to: FR01, SP02
function pollClaimStatus(claimId) {
  ...
}
```

A file with implementation code but no such block above it, for any
requirement, is not compliant — the Implementation Agent's Definition of
Done treats this as a blocking gap, not a style nit.

## 3. Protected / frozen paths

List anything Implementation must never touch without a separate,
explicitly-approved change:

| Path | Why it's frozen | Who can approve an exception |
|---|---|---|
| e.g. `src/legacy/v1/**` | Frozen pending v2 migration | Platform team lead |
| e.g. `**/generated/**` | Auto-generated, hand-edits get overwritten | N/A — regenerate instead |

## 4. Test naming convention (Test Automation Agent, Step 10)

There is no single universal correct answer here — real-world practice
uses several different conventions side by side (e.g.
`MethodName_StateUnderTest_ExpectedBehavior`,
`Should_ExpectedBehavior_When_StateUnderTest`, or full
`Given_Precondition_When_Action_Then_Outcome` BDD-style names). What
matters more than which one is picked is that the whole project uses the
**same one**, consistently, so tests remain scannable as a form of living
documentation.

**This project's chosen convention:** [fill in — recommend
`Given_<precondition>_When_<action>_Then_<outcome>` by default, since it
maps directly onto the Given/When/Then scenarios Step 5 already writes,
requiring no translation between the two]

**Test body structure — Arrange/Act/Assert (or Given/When/Then, its
direct equivalent):**
- One clear **Arrange** section (setup/preconditions)
- A single **Act** (the one action under test — not several)
- A single logical **Assert** (a test verifying multiple unrelated
  behaviors should be split, not asserted together)
- Cyclomatic complexity of a test should be effectively 1 — no
  conditional branching inside a test. If you need an `if` inside a test,
  that's two tests.

**Mocking rules per layer** (ties back to the Unit/Integration/E2E tag
Step 5 assigned to each scenario):
- **Unit:** mock all external dependencies (network, database, other
  services) — a unit test with a live dependency has drifted into being
  an integration test and should be re-tagged, not left mislabeled.
- **Integration:** use real internal collaborators; mock only true
  external boundaries (third-party APIs, payment gateways).
- **E2E:** no mocking — this is the one layer meant to prove the whole
  stack is actually wired together correctly.

## 5. Commands

| Command | Purpose | Healthy output example |
|---|---|---|
| e.g. `make build` | Build | `Build succeeded` |
| e.g. `make test` | Run test suite | `All tests passed (N/N)` |
| e.g. `make lint` | Lint | `0 warnings` |

## 6. Things this project's agents keep getting wrong

A living, append-only correction log — same rule the blog's `CLAUDE.md`
uses: when an agent repeats a mistake twice, the correction goes here
permanently, not just fixed once in the moment.

| Date added | Mistake | Correction |
|---|---|---|
| | | |

## 7. Revision history

| Date | Change | Reason / Ref |
|---|---|---|

## Approval

Engineering Manager / Tech Lead — [ ] Approved — name, date
