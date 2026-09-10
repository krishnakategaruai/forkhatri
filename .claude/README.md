# SDLC Traceable Pipeline — Claude Code Plugin

A 15-agent pipeline for building large projects with full, bidirectional
traceability from business intent to deployed code. No skills are used —
every agent is a focused, single-purpose subagent, because each one does
one job in one place; there's no cross-cutting policy here that would
justify a skill layer.

## Philosophy

This system does not promise nothing will go wrong. It promises that if
something does go wrong, you can find exactly where and why — every
artifact traces back to the business need that justified it, every
decision is recorded with its rejected alternatives, and every step is
signed off by a named human role before the next step begins.

## The 15 agents

| # | Agent | Role played | Produces |
|---|---|---|---|
| 0 | `module-agent` | Solution Architect / PM | `/modules/modules.md` |
| 0b | `solution-architecture-agent` | Chief Architect | `/ARCHITECTURE.md` |
| 1 | `business-requirements-agent` | Product Manager | `01-business-requirements.md` |
| 2 | `functional-requirements-agent` | Product Manager / BA | `02-functional-requirements.md` |
| 3 | `ux-agent` | UX Lead | `03-ux.md` |
| 4 | `ui-agent` | UI/Design Director | `04-ui.md` |
| 5 | `test-scenarios-agent` | Principal QA | `05-test-scenarios.md` |
| 6 | `impact-analysis-agent` | Architect / Director | `06-impact-analysis.md` |
| 7 | `tech-reqs-er-model-agent` | Architect | `07-tech-reqs.md`, `07a-er-model.md`, `07b-component-diagram.md` |
| 8 | `security-performance-agent` | Security Lead | `08-security-performance.md` |
| 9 | `implementation-agent` | Eng Manager / Tech Lead | `09-implementation.md`, `09a-external-dependencies.md` + actual code |
| 10 | `test-automation-agent` | Principal QA | `10-test-automation.md` + actual tests |
| 11 | `test-execution-agent` | QA Manager | `11-test-execution.md` |
| 12 | `improvement-agent` | Tech Lead | `12-improvement.md` |
| 13 | `monitoring-agent` | Ops/SRE Manager | `13-monitoring.md` |
| 14 | `deploy-docs-agent` | Release Manager / Director | `14-deploy-docs.md` (changelog) |

Plus one shared subagent, `researcher`, invoked by any of the 15 whenever a
single item's status is `Needs Research` (max 2 self-loop attempts before
escalating to a human as `Blocked`).

## How the pipeline runs

- **Module Agent runs once per project.** It splits a large problem
  statement into independent Modules along business-capability boundaries
  (never technical layers), checked against four named anti-patterns and
  producing an acyclic dependency map.
- **Solution Architecture Agent runs once per project, immediately after
  Module Agent.** Module Agent decides business boundaries; this agent
  decides how those boundaries become running software — tech stack,
  deployment topology, and a concrete resolution for every cross-module
  dependency and shared concern Module Agent flagged but didn't design.
  Uses the C4 model (Context + Container diagrams) plus the same ADR
  format used throughout the rest of this pipeline. Steps 1-5
  (Business Req through Test Scenarios) for any module may proceed in
  parallel without waiting on this file, since that work is
  architecture-agnostic — but no module may enter Step 6 (Impact
  Analysis) until `/ARCHITECTURE.md` is Sealed.
- **Each module then runs its own full 14-step chain, independently.**
  Modules do not run in lockstep with each other — MOD01 can be at Step 9
  while MOD02 is still at Step 2.
- **Within one module, steps are strictly sequential and batch-complete.**
  A step is not sealed until every item in it (every BR, every FR, etc.)
  has reached `Approved` status. The next agent does not begin until the
  previous step's file is `Sealed`.
- **Each agent loops over every item from the previous step, one at a
  time, with full focus** — not in parallel, not partially. An item that
  is `Blocked` doesn't halt the rest of the loop; the agent keeps working
  the other items and returns to blocked ones once a human resolves them.

## Folder structure a project using this plugin should have

```
/project-root
  /modules
    modules.md
    /MOD01-<slug>
      01-business-requirements.md
      02-functional-requirements.md
      03-ux.md
      04-ui.md
      05-test-scenarios.md
      06-impact-analysis.md
      07-tech-reqs.md
      07a-er-model.md
      07b-component-diagram.md
      08-security-performance.md
      09-implementation.md
      09a-external-dependencies.md
      10-test-automation.md
      11-test-execution.md
      12-improvement.md
      13-monitoring.md
      14-deploy-docs.md
      workflow-table.md
      evidence-graph.md
    /MOD02-<slug>
      ...
  /change-requests
    CR01.md
  ARCHITECTURE.md   <- produced by solution-architecture-agent, once per
                        project, right after modules.md is approved
  IMPLEMENTATION-TEST-STANDARDS.md   <- copied from templates/, filled in
                                         once per project, read by Steps 9 & 10
  PROCESS-README.md   <- copied from templates/PROCESS-README-TEMPLATE.md
                         once per project, updated by every agent on seal
```

## Setting up a new project

1. Copy `templates/PROCESS-README-TEMPLATE.md` to the project root as
   `PROCESS-README.md`.
2. Copy `templates/IMPLEMENTATION-TEST-STANDARDS-TEMPLATE.md` to the
   project root as `IMPLEMENTATION-TEST-STANDARDS.md` and fill in this
   project's actual naming conventions, test naming convention, and
   protected paths — this is a **mandatory read** for the Implementation
   Agent (Step 9) and Test Automation Agent (Step 10) on every module, not
   optional reference material.
3. Invoke `module-agent` with the raw problem statement.
4. Once `modules.md` is approved, invoke `business-requirements-agent` for
   each module — this creates that module's folder and
   `workflow-table.md` / `evidence-graph.md` from the templates.
5. From there, invoke each subsequent agent once its predecessor's file is
   `Sealed`, per module.

## The one hook in this plugin

`hooks/scripts/check-referential-integrity.sh` runs before any write into
a module's step files. It confirms every ID referenced via `Traces from`
or `Depends on` actually exists in that module's `workflow-table.md`
before the write is allowed. This is the only deterministic control in the
system — everything else (approvals, sealing a step, resolving a CR) is
human judgment at a named gate, by design. Adding more hooks was
considered and deliberately rejected: this pipeline's safety comes from
who reviews what, not from automated gatekeeping layered on top of every
action.

## Templates

`/templates` holds the reference format for every artifact type — the
same formats embedded in each agent's own instructions, provided here as
quick-reference copies. These are templates only, with no filled-in
example data, so nothing here should be mistaken for a real project's
content.

## Quality methods this pipeline uses (and why)

- **ISO/IEC/IEEE 29148** nine-point requirement quality gate (Necessary,
  Appropriate, Unambiguous, Complete, Singular, Feasible, Verifiable,
  Correct, Conforming) — applied to every item in every step, plus a
  set-level gate (comprehensive, consistent, prioritized, no duplicates)
  per step file.
- **ISO 29148 sentence form** — `[condition], the system shall [action]
  [object] [constraint]` — mandatory for Functional Requirements.
- **STRIDE threat modeling** (Spoofing, Tampering, Repudiation,
  Information disclosure, Denial of service, Elevation of privilege) —
  the actual method behind Step 8's security analysis, run before
  implementation, not after.
- **Test pyramid distribution** — test scenarios are tagged Unit /
  Integration / E2E, with a set-level check flagging E2E-heavy suites.
- **Change Impact Analysis** — Step 6 splits explicitly into dependency
  identification and risk assessment as two distinct sub-sections, never
  blended into one vague paragraph.
- **Architecture Decision Records (Y-statement form)** — every Decisions
  section is append-only; corrections supersede explicitly rather than
  overwriting history.
- **Keep a Changelog** — Step 14 maintains a running `Unreleased` section,
  categorized into Added/Changed/Deprecated/Removed/Fixed/Security, sealed
  into a dated semantic version only at actual release.
- **C4 model** (Context + Container diagrams at project level, plus a
  **Component diagram per module** at Step 7) plus **Architecture
  Decision Records** — used once per project by the Solution Architecture
  Agent for system-wide structure, and once per module by the Tech
  Reqs/ER Model agent for that module's internal structure. This is
  deliberate: the project-level file stays lean (Context + Container +
  cross-module ADRs only), while each module gets its own properly-scoped
  architecture artifact via C4's Component level rather than the
  project-level file growing to hold every module's internals.
- **SBOM-adjacent dependency tracking** — Implementation (Step 9)
  produces `09a-external-dependencies.md` as a companion output,
  following the real-world practice of generating a dependency manifest
  during/right after build (when exact resolved versions are actually
  known). Any dependency not already vetted by Security & Performance
  (Step 8) triggers a scoped, supplementary STRIDE pass before
  Implementation can seal — new dependencies don't silently bypass the
  shift-left security gate just because they were discovered mid-build.
