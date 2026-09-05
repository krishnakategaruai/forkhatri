---
project: [Project Name]
pipeline_version: sdlc-traceable-pipeline v1.0.0
updated: YYYY-MM-DD
---

# Process log — [Project Name]

This file is copied once per project (not per module) and updated by
whichever agent is currently active, every time it seals a step. It is the
single place a new team member (or a human checking in mid-project) reads
to understand where things stand, without opening every module's files.

**Every agent, on sealing its step for a given module, appends one line
here.** Do not batch updates — append immediately on seal so this file is
never stale relative to the actual pipeline state.

## How to read this file

Each row is one sealed step, for one module. Multiple modules progress
independently (each fully completes one module's 14 steps before that
module is "done," but different modules can be at different steps
simultaneously — there is no cross-module lockstep).

## Modules in this project

| Module | Current step | Status |
|---|---|---|
| MOD01 | | |

## Log (append-only — newest at the bottom)

| Date | Module | Step sealed | Sealed by (agent) | Approver | Notes |
|---|---|---|---|---|---|
| YYYY-MM-DD | MOD01 | 00-module-agent | module-agent | Solution Architect + PM | Initial decomposition into N modules |

## Open items across the whole project

[Any blocker significant enough to affect more than one module — e.g. an
undeclared cross-module dependency found during Impact Analysis — gets
noted here in addition to living in its module's own file, so it's visible
without having to check every module individually.]

## Change Requests

| CR ID | Module(s) affected | Summary | Status |
|---|---|---|---|

(Each CR is documented in full inside `/change-requests/CRxx.md` — this
table is just the index. A CR edits existing artifacts in place with a
dated, referenced comment; it does not create parallel "v2" files.)
