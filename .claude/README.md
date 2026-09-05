# SDLC Autonomous Pipeline — Claude Code Plugin

The fully autonomous variant of `sdlc-traceable-pipeline`. Same 16 agents,
same file formats, same quality gates (ISO 29148, STRIDE, C4/ADRs, test
pyramid, Keep a Changelog) — the only thing that changes is **who
approves each step.** Every gate here is self-certified by a role-based
reviewer agent, driven end to end by one command, instead of waiting on a
named human at every step.

**Read the risk section below before using this on real work.** This
plugin exists to answer a specific question — does the pipeline actually
complete, start to finish, from one command — not to replace the
human-gated plugin as the default way to run real projects.

## What's different from `sdlc-traceable-pipeline`

| | Human-gated plugin | This plugin |
|---|---|---|
| Approval | Named human per step | Role-based reviewer agent per step |
| Execution | Pauses at every gate | Runs continuously via `/run-pipeline`, pauses only on a genuine `Blocked` item |
| Audit trail | `approved_by: <human name>` | `approved_by: reviewer-agent (autonomous mode)`, with explicit risk caveats on the 8 judgment gates |
| Agent count | 16 | 32 (16 producers + 16 paired reviewers) |
| New pieces | — | `commands/run-pipeline.md` (orchestrator), `hooks/scripts/signal-next-step.sh` |

Nothing about the artifact formats, the quality gates, or the traceability
chain changed. This is purely a change in who signs off.

## Why this isn't automatically the safer or better choice

A reviewer agent checking a producer agent's work is not the same
guarantee as a human checking it. LLM judges are documented to exhibit
**self-preference bias** — rating outputs more favorably when the judge
recognizes the same model family that produced them — and this effect is
measured to be strongest exactly when the judge can recognize its own
style. Since the producer and its paired reviewer here will typically run
on the same underlying model, they are not independent checks. This
matters most on exactly the kind of subtle, interpretive judgment call
where a human would catch something an agent wouldn't even flag as
uncertain.

## The 8 gates with elevated risk in this mode

Every reviewer agent for these 8 states its own risk explicitly in its
file, but the summary:

| Gate | What's actually at risk with no human |
|---|---|
| 0. Module | Wrong business-capability split — a strategic error, not a checklist failure |
| 0b. Architecture | Wrong tech stack/topology — surfaces as accumulating technical debt, not a failed check |
| 1. Business Requirements | Worth-check #1 self-certified — something gets built that nobody actually needed |
| 6. Impact Analysis | Worth-check #2 self-certified — risk accepted with no accountable human owner |
| 7. Tech Reqs / ER Model | The single highest blast-radius artifact in the pipeline — an error here invalidates everything built on top |
| 8. Security & Performance | Accepting a security risk with no named human risk-owner **can fail a SOC 2 / ISO 27001 audit outright**, independent of technical correctness |
| 13. Monitoring | Wrong response tiers are a live-production risk, not a documentation error |
| 14. Deploy Docs | **No human ever authorizes the actual production release** — this is very likely a segregation-of-duties violation under SOC 2 / SOX if this project has any formal change-management obligation |

The last two rows are not soft warnings — they describe a real, likely
compliance failure mode, not just elevated technical risk. If this
project is subject to any formal security or change-management review,
read those two reviewer agents' files (`08-security-performance-reviewer.md`,
`14-deploy-docs-reviewer.md`) before relying on an autonomous run's output
as production-ready.

## How to run it

```
/run-pipeline <your raw problem statement, in your own words>
```

The orchestrator command drives every agent in sequence, invoking each
producer then its paired reviewer, checking `status` in the resulting
file's frontmatter, and proceeding immediately on `Sealed` with no
confirmation prompts. It stops only when an item reaches genuine
`Blocked` — either a producing agent's `researcher` subagent exhausted its
2-attempt limit, or a reviewer agent's own decision rules triggered an
escalation (each reviewer states exactly when, in its own file).

When it stops, it reports exactly which module, step, and item is
blocked, and the recorded blocker text. Resolve it, then re-run
`/run-pipeline` — agents check for already-`Sealed` upstream files and
won't redo completed work.

## Recommended way to actually use this

1. **Trial run first**, as originally intended — run it on a small,
   low-stakes module and read every `approved_by: reviewer-agent` line
   afterward, especially on the 8 elevated-risk gates, before trusting
   the output.
2. **If it completes cleanly**, that tells you the mechanics work — the
   sequencing, the hooks, the handoffs — not that the 8 judgment calls
   inside it were made as well as a human would have made them. Those
   still deserve a read.
3. **If you want the rigor back without giving up the automation of the
   other 8 mechanical gates**, the two plugins are compatible in
   structure — you can swap individual reviewer agents in
   `agents/reviewers/` back to a "stop and wait for named human" version
   per gate, without touching anything else. The producer agents and file
   formats are identical between both plugins for exactly this reason.
4. **For real, audited, production work**, use `sdlc-traceable-pipeline`
   (the human-gated plugin) as the default, and treat this one as the
   fast-iteration/prototyping mode.

## Folder structure

Identical to `sdlc-traceable-pipeline`, plus:

```
/project-root
  /modules/...            (same as human-gated plugin)
  ARCHITECTURE.md
  IMPLEMENTATION-TEST-STANDARDS.md
  PROCESS-README.md
```

The plugin itself adds `commands/run-pipeline.md` and
`hooks/scripts/signal-next-step.sh` on top of everything the human-gated
plugin already has.
