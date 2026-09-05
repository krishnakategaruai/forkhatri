---
module: MODxx
updated: YYYY-MM-DD
---

# Workflow Table — MODxx

The flat index of every item across all 14 steps for this module. Every
agent updates its own rows here as it produces items — this file is never
owned by a single agent; each agent is responsible only for the rows it
creates or changes. The referential-integrity hook validates every
`Traces from` / `Depends on` reference elsewhere in the pipeline against
the IDs listed here.

| ID | Title | Step | Traces from | Depends on (cross-module) | Status | Approver | Blocker | Updated |
|---|---|---|---|---|---|---|---|---|
| BR01 | | 01 | — | | | | | |
| FR01 | | 02 | BR01 | | | | | |
| UX01 | | 03 | FR01 | | | | | |
| UI01 | | 04 | FR01, UX01 | | | | | |
| TS01 | | 05 | FR01 | | | | | |
| IA01 | | 06 | FR01 | | | | | |
| TR01 | | 07 | FR01 | | | | | |
| SP01 | | 08 | TR01 | | | | | |
| IMP01 | | 09 | TR01, SP01 | | | | | |
| TA01 | | 10 | TS01 | | | | | |
| TE01 | | 11 | TA01 | | | | | |
| IMP-FIX01 | | 12 | TE01 | | | | | |
| MON01 | | 13 | SP01 | | | | | |
| (Deploy entries are logged in 14-deploy-docs.md's own Unreleased/versioned sections, not duplicated here) | | | | | | | | |

## Rollup
| Metric | Value |
|---|---|
| Total items | |
| Approved | |
| Open blockers | |
| Current step in progress | |
