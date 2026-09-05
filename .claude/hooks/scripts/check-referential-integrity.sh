#!/bin/bash
# check-referential-integrity.sh
#
# The one deterministic guardrail in this pipeline. Runs before any agent
# writes to a step .md file. Confirms every ID referenced in a "Traces from"
# or "Depends on" field actually exists somewhere in the module's
# workflow-table.md before the write is allowed to proceed.
#
# This exists because an agent validating its own cross-references is asking
# the thing that might hallucinate an ID to also confirm the ID is real.
# A deterministic grep closes that gap cheaply. Nothing else in this pipeline
# is enforced by a hook — every other control is human judgment at a named
# approval gate.

set -euo pipefail

TOOL_INPUT=$(cat)
FILE_PATH=$(echo "$TOOL_INPUT" | jq -r '.tool_input.file_path // empty')
CONTENT=$(echo "$TOOL_INPUT" | jq -r '.tool_input.content // .tool_input.new_str // empty')

# Only check writes into a module's step files, not unrelated files
if [[ "$FILE_PATH" != *"/modules/"* ]]; then
  exit 0
fi

MODULE_DIR=$(echo "$FILE_PATH" | sed -E 's#(.*/modules/[^/]+)/.*#\1#')
WORKFLOW_TABLE="$MODULE_DIR/workflow-table.md"

if [[ ! -f "$WORKFLOW_TABLE" ]]; then
  # Workflow table doesn't exist yet (e.g. this IS the first write that
  # creates it) — nothing to validate against yet, allow it.
  exit 0
fi

# Pull every ID this write references via "Traces from:" or "Depends on:"
REFERENCED_IDS=$(echo "$CONTENT" | grep -oE '\*\*(Traces from|Depends on)[^*]*\*\*[^\n]*' \
  | grep -oE '[A-Z]+[0-9]+(-[A-Z]+[0-9]+)*' | sort -u || true)

if [[ -z "$REFERENCED_IDS" ]]; then
  exit 0
fi

MISSING=""
for id in $REFERENCED_IDS; do
  if ! grep -q "$id" "$WORKFLOW_TABLE"; then
    MISSING="$MISSING $id"
  fi
done

if [[ -n "$MISSING" ]]; then
  echo "BLOCKED: the following referenced ID(s) do not exist in $WORKFLOW_TABLE:$MISSING" >&2
  echo "Confirm the correct ID in workflow-table.md before writing this reference." >&2
  exit 2
fi

exit 0
