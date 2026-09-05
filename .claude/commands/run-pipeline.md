---
description: >
  Runs the full autonomous SDLC pipeline end to end from a single command:
  Module Agent through Deploy Docs, for every module, with every gate
  self-certified by its paired reviewer agent. Stops only on a genuine
  Blocked item that neither the producing agent's researcher self-loop nor
  its reviewer agent can resolve. Pass the raw problem statement as the
  argument.
argument-hint: "<raw problem statement, in your own words>"
---

# Run the autonomous pipeline

You are the orchestrator for this run. Your job is to drive every agent
in this fixed sequence to completion, without stopping to ask for
confirmation between steps, invoking each agent via the Task tool and
reading the resulting file's frontmatter `status` field to decide what
happens next. The only thing that stops you is a genuine `Blocked` item —
see "When to actually stop" below.

## Fixed sequence (do not deviate, do not skip a step)

**Once, for the whole project:**
1. `module-agent` with the argument as its problem statement input
2. `module-reviewer` on the resulting `modules.md`
3. `solution-architecture-agent`
4. `architecture-reviewer` on the resulting `ARCHITECTURE.md`

**Then, once per module produced in step 1-2, run this 14-step inner loop.**
Modules do not need to run in lockstep with each other — if running
multiple modules in the same session, you may interleave them, but each
module's own steps must stay strictly sequential relative to each other:

5. `business-requirements-agent` → 6. `business-requirements-reviewer`
7. `functional-requirements-agent` → 8. `functional-requirements-reviewer`
9. `ux-agent` → 10. `ux-reviewer`
11. `ui-agent` → 12. `ui-reviewer`
13. `test-scenarios-agent` → 14. `test-scenarios-reviewer`
15. `impact-analysis-agent` → 16. `impact-analysis-reviewer`
17. `tech-reqs-er-model-agent` → 18. `tech-reqs-er-model-reviewer`
19. `security-performance-agent` → 20. `security-performance-reviewer`
21. `implementation-agent` → 22. `implementation-reviewer`
23. `test-automation-agent` → 24. `test-automation-reviewer`
25. `test-execution-agent` → 26. `test-execution-reviewer`
27. `improvement-agent` → 28. `improvement-reviewer`
29. `monitoring-agent` → 30. `monitoring-reviewer`
31. `deploy-docs-agent` → 32. `deploy-docs-reviewer`

## How to drive it

- After invoking a producer agent, invoke its paired reviewer immediately
  — do not proceed to the next producer until the reviewer has run.
- Check the reviewer's outcome by reading the file's frontmatter
  `status` field. `Sealed` → proceed to the next step in the sequence
  immediately, no confirmation needed. `Blocked` → stop (see below).
- The `signal-next-step.sh` hook will surface a `SEALED: ... -> NEXT
  AGENT TO INVOKE: ...` line into your transcript after each sealing
  write — treat this as confirmation of what you already know from the
  sequence above, not as new information to interpret.
- Update `/PROCESS-README.md`'s log table after every seal, same as a
  human-gated run would — this plugin does not skip the audit trail, it
  only changes who signs it.

## When to actually stop

Stop and report to the person who ran this command — do not keep
retrying — only when:

- A producing agent's `researcher` subagent hits its 2-attempt limit
  without resolving a `Needs Research` item, and the item becomes
  genuinely `Blocked`, or
- A reviewer agent marks something `Blocked` per its own decision rules
  (every reviewer agent's file states exactly when this happens)

When you stop, report: which module, which step, which specific item,
and the exact blocker text the agent or reviewer recorded — so the person
can resolve it and re-invoke this command to continue from where it
stopped (agents check for already-`Sealed` upstream files and won't
redo completed work).

## Before you start

Confirm these exist, or create them from `templates/` before invoking
`module-agent`:
- `/PROCESS-README.md` (from `templates/PROCESS-README-TEMPLATE.md`)
- `/IMPLEMENTATION-TEST-STANDARDS.md` (from
  `templates/IMPLEMENTATION-TEST-STANDARDS-TEMPLATE.md` — if this doesn't
  exist yet, flag it as a `Blocked` pre-req rather than guessing at
  conventions; Steps 21-24 depend on it directly)
