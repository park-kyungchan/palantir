#!/bin/bash
# PermissionRequest Hook
# Routes hazardous operations to ODA Proposal workflow
#
# Environment variables used:
#   PERMISSION_TYPE - Type of permission being requested
#   PERMISSION_REASON - Reason for the permission request
#   PERMISSION_SCOPE - Scope of the operation
#
# Exit codes:
#   0 - Permission granted (WARN mode)
#   1 - Permission denied (future BLOCK mode)

set -euo pipefail

PERMISSION_TYPE="${PERMISSION_TYPE:-unknown}"
PERMISSION_REASON="${PERMISSION_REASON:-}"
PERMISSION_SCOPE="${PERMISSION_SCOPE:-}"
TIMESTAMP=$(date -Iseconds)

# Ensure log directory exists
mkdir -p .agent/logs

# Define hazardous permission types that require Proposal
HAZARDOUS_TYPES=("destructive" "security" "schema_change" "database_migration")

# Check if this permission type requires ODA Proposal
REQUIRES_PROPOSAL=false
for hazard in "${HAZARDOUS_TYPES[@]}"; do
  if [[ "$PERMISSION_TYPE" == "$hazard" ]]; then
    REQUIRES_PROPOSAL=true
    break
  fi
done

# Log permission request
if [[ "$REQUIRES_PROPOSAL" == "true" ]]; then
  echo "$TIMESTAMP | PERMISSION_REQUEST | $PERMISSION_TYPE | PROPOSAL_REQUIRED | reason:$PERMISSION_REASON | scope:$PERMISSION_SCOPE" >> .agent/logs/oda_audit.log
  echo "[ODA-PROPOSAL] Hazardous operation detected: $PERMISSION_TYPE"
  echo "[ODA-PROPOSAL] Consider using 'mcp__oda-ontology__create_proposal' for approval workflow"
else
  echo "$TIMESTAMP | PERMISSION_REQUEST | $PERMISSION_TYPE | ALLOWED | reason:$PERMISSION_REASON" >> .agent/logs/oda_audit.log
fi

# For now, just log and allow (WARN mode)
# Future: Integrate with ODA MCP create_proposal for BLOCK mode
exit 0
