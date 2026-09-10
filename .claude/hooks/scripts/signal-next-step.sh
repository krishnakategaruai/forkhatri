#!/bin/bash
# signal-next-step.sh
#
# PostToolUse hook. After any Write/Edit into a module's step file, checks
# whether that write set status: Sealed. If so, emits which agent (and
# which reviewer) runs next, deterministically, from a fixed sequence
# table — the same principle as check-referential-integrity.sh: a script
# derives the fact mechanically, rather than the orchestrator having to
# "remember" or re-derive the sequence from judgment each time.
#
# This does not invoke the next agent itself — hooks cannot call the Task
# tool. It surfaces the fact into the transcript so the orchestrator
# command's instructions (which explicitly say "act on this signal
# immediately, do not stop and ask") can act on it without re-deriving
# the sequence from scratch.

set -euo pipefail

TOOL_INPUT=$(cat)
FILE_PATH=$(echo "$TOOL_INPUT" | jq -r '.tool_input.file_path // empty')
CONTENT=$(echo "$TOOL_INPUT" | jq -r '.tool_input.content // .tool_input.new_str // empty')

if [[ "$FILE_PATH" != *"/modules/"* ]] && [[ "$FILE_PATH" != "/ARCHITECTURE.md" ]] && [[ "$FILE_PATH" != *"modules.md" ]]; then
  exit 0
fi

if ! echo "$CONTENT" | grep -q "status: Sealed"; then
  exit 0
fi

# Fixed sequence: step file basename -> (producer agent, next producer agent)
declare -A NEXT_AGENT=(
  ["modules.md"]="step0b-solution-architecture-agent"
  ["ARCHITECTURE.md"]="step1-business-requirements-agent (for every module)"
  ["01-business-requirements.md"]="step2-functional-requirements-agent"
  ["02-functional-requirements.md"]="step3-ux-agent"
  ["03-ux.md"]="step4-ui-agent"
  ["04-ui.md"]="step5-test-scenarios-agent"
  ["05-test-scenarios.md"]="step6-impact-analysis-agent"
  ["06-impact-analysis.md"]="step7-tech-reqs-er-model-agent"
  ["07-tech-reqs.md"]="step8-security-performance-agent (once 07a-er-model.md is also Sealed)"
  ["07a-er-model.md"]="step8-security-performance-agent (once 07-tech-reqs.md is also Sealed)"
  ["08-security-performance.md"]="step9-implementation-agent"
  ["09-implementation.md"]="step10-test-automation-agent"
  ["10-test-automation.md"]="step11-test-execution-agent"
  ["11-test-execution.md"]="step12-improvement-agent"
  ["12-improvement.md"]="step13-monitoring-agent"
  ["13-monitoring.md"]="step14-deploy-docs-agent"
)

BASENAME=$(basename "$FILE_PATH")
NEXT="${NEXT_AGENT[$BASENAME]:-}"

if [[ -n "$NEXT" ]]; then
  echo "SEALED: $FILE_PATH -> NEXT AGENT TO INVOKE: $NEXT" >&2
fi

exit 0
