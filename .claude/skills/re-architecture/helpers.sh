#!/usr/bin/env bash
# =============================================================================
# /re-architecture Skill Helper Functions (V1.0.0)
# =============================================================================
# Purpose: YAML logging utilities for re-architecture skill with traceability
# Requires: yq (https://github.com/mikefarah/yq)
# Usage: source /home/palantir/.claude/skills/re-architecture/helpers.sh
# =============================================================================
#
# KEY FEATURES:
# - Machine-Readable YAML logging with traceability schema
# - Incremental document update (매 라운드마다 문서 업데이트)
# - Design intent tracking (설계 의도 추적)
# - Issue reference system (이슈 참조)
# - /research handoff support
#
# =============================================================================

set -euo pipefail

# ============================================================================
# DEPENDENCIES
# ============================================================================
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SHARED_DIR="${SCRIPT_DIR}/../shared"

if [[ -f "${SHARED_DIR}/slug-generator.sh" ]]; then
    source "${SHARED_DIR}/slug-generator.sh"
fi

if [[ -f "${SHARED_DIR}/workload-tracker.sh" ]]; then
    source "${SHARED_DIR}/workload-tracker.sh"
fi

if [[ -f "${SHARED_DIR}/workload-files.sh" ]]; then
    source "${SHARED_DIR}/workload-files.sh"
fi

# ============================================================================
# CONSTANTS
# ============================================================================
RE_ARCH_VERSION="1.0.0"
RE_ARCH_LOG_NAME="re-architecture-log.yaml"

# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

# Check if yq is available
_check_yq() {
    if ! command -v yq &> /dev/null; then
        echo "ERROR: yq not found. Install with: brew install yq" >&2
        return 1
    fi
}

# Get ISO8601 timestamp
_timestamp() {
    date -u +"%Y-%m-%dT%H:%M:%SZ"
}

# Generate unique ID
_generate_id() {
    local prefix="$1"
    echo "${prefix}-$(date +%s%N | sha256sum | head -c 8)"
}

# ============================================================================
# yaml_init_architecture_log
# Initialize new re-architecture YAML log with full traceability schema
#
# Args:
#   $1 - Log file path
#   $2 - Target path (분석 대상 경로)
#   $3 - User request (optional)
# ============================================================================
yaml_init_architecture_log() {
    local log_path="$1"
    local target_path="$2"
    local user_request="${3:-}"
    local slug
    slug=$(basename "$(dirname "$log_path")")

    _check_yq || return 1

    # Ensure directory exists
    mkdir -p "$(dirname "$log_path")"

    # Create initial YAML structure with traceability schema
    cat > "$log_path" << EOF
# /re-architecture Session Log
# Generated: $(_timestamp)
# Schema Version: ${RE_ARCH_VERSION}
# Purpose: Pipeline component analysis with full traceability

metadata:
  id: "${slug}"
  version: "${RE_ARCH_VERSION}"
  created_at: "$(_timestamp)"
  updated_at: "$(_timestamp)"
  status: "in_progress"
  target_path: "${target_path}"

# 세션 상태 추적
state:
  current_phase: "initialization"
  current_component: null
  round: 0
  total_components: 0
  analyzed_components: 0

# 사용자 의도 및 요구사항 (Traceability Core)
user_intent:
  original_request: |
$(echo "$user_request" | sed 's/^/    /')
  clarified_goals: []
  constraints: []
  priorities: []

# 컴포넌트 분해 결과
decomposition:
  pipeline_structure: null
  components: []

# 상호작용 라운드 기록 (Incremental)
rounds: []

# 컴포넌트별 피드백 결과
component_feedback: {}

# 핸드오프 정보 (/research 연계)
handoff:
  ready_for_research: false
  research_context:
    summary: null
    key_findings: []
    priority_components: []
    recommended_focus: []
  next_action_hint: "/research --clarify-slug ${slug}"

# 파이프라인 통합
pipeline:
  downstream_skills: []
  context_hash: null
  decision_trace: []
EOF

    echo "✅ Re-architecture log initialized: $log_path"
}

# ============================================================================
# yaml_update_state
# Update session state fields
#
# Args:
#   $1 - Log file path
#   $2 - Field name (current_phase, current_component, etc.)
#   $3 - New value
# ============================================================================
yaml_update_state() {
    local log_path="$1"
    local field="$2"
    local value="$3"

    _check_yq || return 1

    yq -i ".state.${field} = \"${value}\"" "$log_path"
    yq -i ".metadata.updated_at = \"$(_timestamp)\"" "$log_path"
}

# ============================================================================
# yaml_add_user_intent
# Add clarified goal, constraint, or priority
#
# Args:
#   $1 - Log file path
#   $2 - Intent type (clarified_goals, constraints, priorities)
#   $3 - Intent value
# ============================================================================
yaml_add_user_intent() {
    local log_path="$1"
    local intent_type="$2"
    local intent_value="$3"

    _check_yq || return 1

    yq -i ".user_intent.${intent_type} += [\"${intent_value}\"]" "$log_path"
    yq -i ".metadata.updated_at = \"$(_timestamp)\"" "$log_path"
}

# ============================================================================
# yaml_set_decomposition
# Set pipeline structure and components
#
# Args:
#   $1 - Log file path
#   $2 - Pipeline structure (diagram string)
# ============================================================================
yaml_set_decomposition() {
    local log_path="$1"
    local structure="$2"

    _check_yq || return 1

    yq -i ".decomposition.pipeline_structure = \"${structure}\"" "$log_path"
    yq -i ".state.current_phase = \"decomposition\"" "$log_path"
    yq -i ".metadata.updated_at = \"$(_timestamp)\"" "$log_path"
}

# ============================================================================
# yaml_add_component
# Add component to decomposition list
#
# Args:
#   $1 - Log file path
#   $2 - Component name
#   $3 - Component path
#   $4 - Component type (stage|module|service|utility)
#   $5 - Upstream dependencies (comma-separated, optional)
#   $6 - Downstream dependencies (comma-separated, optional)
# ============================================================================
yaml_add_component() {
    local log_path="$1"
    local name="$2"
    local path="$3"
    local type="${4:-module}"
    local upstream="${5:-}"
    local downstream="${6:-}"

    _check_yq || return 1

    local comp_id
    comp_id=$(_generate_id "comp")

    # Build component YAML
    local temp_comp
    temp_comp=$(mktemp)

    cat > "$temp_comp" << EOF
id: "${comp_id}"
name: "${name}"
path: "${path}"
type: "${type}"
dependencies:
  upstream: [$(echo "$upstream" | sed 's/,/", "/g' | sed 's/^/"/' | sed 's/$/"/' | sed 's/""/\[\]/')]
  downstream: [$(echo "$downstream" | sed 's/,/", "/g' | sed 's/^/"/' | sed 's/$/"/' | sed 's/""/\[\]/')]
status: "pending"
EOF

    # Append to components array
    yq -i ".decomposition.components += [$(cat "$temp_comp" | yq -o=json)]" "$log_path"

    # Update component count
    local count
    count=$(yq '.decomposition.components | length' "$log_path")
    yq -i ".state.total_components = ${count}" "$log_path"
    yq -i ".metadata.updated_at = \"$(_timestamp)\"" "$log_path"

    rm -f "$temp_comp"

    echo "$comp_id"
}

# ============================================================================
# yaml_append_round
# Append new round entry with full traceability
#
# Args:
#   $1  - Log file path
#   $2  - Round number
#   $3  - Phase (decomposition|analysis|feedback|handoff)
#   $4  - Component ID (null if not component-specific)
#   $5  - Input prompt
#   $6  - Input context
#   $7  - Design intent (CRITICAL for traceability)
#   $8  - Parent round (optional, for traceability chain)
# ============================================================================
yaml_append_round() {
    local log_path="$1"
    local round_num="$2"
    local phase="$3"
    local component_id="${4:-null}"
    local input_prompt="$5"
    local input_context="${6:-}"
    local design_intent="$7"
    local parent_round="${8:-null}"

    _check_yq || return 1

    # Escape quotes
    input_prompt="${input_prompt//\"/\\\"}"
    input_context="${input_context//\"/\\\"}"
    design_intent="${design_intent//\"/\\\"}"

    # Create round entry
    local temp_round
    temp_round=$(mktemp)

    cat > "$temp_round" << EOF
round: ${round_num}
timestamp: "$(_timestamp)"
phase: "${phase}"
component_id: ${component_id}
input:
  prompt: "${input_prompt}"
  context: "${input_context}"
analysis:
  findings: []
  recommendations: []
  issues: []
  code_evidence: []
output:
  feedback: null
  options_presented: []
  user_selection: null
traceability:
  design_intent: "${design_intent}"
  decision_rationale: null
  related_components: []
  parent_round: ${parent_round}
  issue_refs: []
EOF

    # Append to rounds array
    yq -i ".rounds += [$(cat "$temp_round" | yq -o=json)]" "$log_path"

    # Update state
    yq -i ".state.round = ${round_num}" "$log_path"
    yq -i ".state.current_phase = \"${phase}\"" "$log_path"
    if [[ "$component_id" != "null" ]]; then
        yq -i ".state.current_component = \"${component_id}\"" "$log_path"
    fi
    yq -i ".metadata.updated_at = \"$(_timestamp)\"" "$log_path"

    rm -f "$temp_round"

    echo "✅ Round ${round_num} appended (phase: ${phase})"
}

# ============================================================================
# yaml_add_finding
# Add finding to current round
#
# Args:
#   $1 - Log file path
#   $2 - Round number
#   $3 - Finding type (pattern|issue|opportunity)
#   $4 - Severity (info|warning|critical)
#   $5 - Description
#   $6 - File path (evidence, optional)
#   $7 - Line number (evidence, optional)
#   $8 - Code snippet (evidence, optional)
# ============================================================================
yaml_add_finding() {
    local log_path="$1"
    local round_num="$2"
    local finding_type="$3"
    local severity="$4"
    local description="$5"
    local file_path="${6:-}"
    local line_num="${7:-}"
    local snippet="${8:-}"

    _check_yq || return 1

    local finding_id
    finding_id=$(_generate_id "find")
    local idx=$((round_num - 1))

    # Escape quotes
    description="${description//\"/\\\"}"
    snippet="${snippet//\"/\\\"}"

    # Build finding object
    local finding_json
    finding_json=$(cat << EOF
{
  "id": "${finding_id}",
  "type": "${finding_type}",
  "severity": "${severity}",
  "description": "${description}",
  "evidence": {
    "file": "${file_path}",
    "line": "${line_num}",
    "snippet": "${snippet}"
  }
}
EOF
)

    yq -i ".rounds[${idx}].analysis.findings += [${finding_json}]" "$log_path"
    yq -i ".metadata.updated_at = \"$(_timestamp)\"" "$log_path"

    echo "$finding_id"
}

# ============================================================================
# yaml_add_recommendation
# Add recommendation to current round
#
# Args:
#   $1 - Log file path
#   $2 - Round number
#   $3 - Priority (high|medium|low)
#   $4 - Description
#   $5 - Rationale (판단근거)
#   $6 - Effort estimate (small|medium|large)
# ============================================================================
yaml_add_recommendation() {
    local log_path="$1"
    local round_num="$2"
    local priority="$3"
    local description="$4"
    local rationale="$5"
    local effort="${6:-medium}"

    _check_yq || return 1

    local rec_id
    rec_id=$(_generate_id "rec")
    local idx=$((round_num - 1))

    # Escape quotes
    description="${description//\"/\\\"}"
    rationale="${rationale//\"/\\\"}"

    local rec_json
    rec_json=$(cat << EOF
{
  "id": "${rec_id}",
  "priority": "${priority}",
  "description": "${description}",
  "rationale": "${rationale}",
  "effort_estimate": "${effort}"
}
EOF
)

    yq -i ".rounds[${idx}].analysis.recommendations += [${rec_json}]" "$log_path"
    yq -i ".metadata.updated_at = \"$(_timestamp)\"" "$log_path"

    echo "$rec_id"
}

# ============================================================================
# yaml_add_issue
# Add issue to current round
#
# Args:
#   $1 - Log file path
#   $2 - Round number
#   $3 - Issue type (bug|debt|risk|improvement)
#   $4 - Severity (critical|high|medium|low)
#   $5 - Description
#   $6 - Suggested action
#   $7 - Blocking (true|false)
# ============================================================================
yaml_add_issue() {
    local log_path="$1"
    local round_num="$2"
    local issue_type="$3"
    local severity="$4"
    local description="$5"
    local suggested_action="$6"
    local blocking="${7:-false}"

    _check_yq || return 1

    local issue_id
    issue_id=$(_generate_id "issue")
    local idx=$((round_num - 1))

    # Escape quotes
    description="${description//\"/\\\"}"
    suggested_action="${suggested_action//\"/\\\"}"

    local issue_json
    issue_json=$(cat << EOF
{
  "id": "${issue_id}",
  "type": "${issue_type}",
  "severity": "${severity}",
  "description": "${description}",
  "suggested_action": "${suggested_action}",
  "blocking": ${blocking}
}
EOF
)

    yq -i ".rounds[${idx}].analysis.issues += [${issue_json}]" "$log_path"

    # Add to traceability issue_refs
    yq -i ".rounds[${idx}].traceability.issue_refs += [\"${issue_id}\"]" "$log_path"
    yq -i ".metadata.updated_at = \"$(_timestamp)\"" "$log_path"

    echo "$issue_id"
}

# ============================================================================
# yaml_update_round_output
# Update output fields for a round
#
# Args:
#   $1 - Log file path
#   $2 - Round number
#   $3 - Feedback text
#   $4 - User selection
#   $5 - Decision rationale
# ============================================================================
yaml_update_round_output() {
    local log_path="$1"
    local round_num="$2"
    local feedback="$3"
    local user_selection="$4"
    local decision_rationale="${5:-}"

    _check_yq || return 1

    local idx=$((round_num - 1))

    # Escape quotes
    feedback="${feedback//\"/\\\"}"
    user_selection="${user_selection//\"/\\\"}"
    decision_rationale="${decision_rationale//\"/\\\"}"

    yq -i ".rounds[${idx}].output.feedback = \"${feedback}\"" "$log_path"
    yq -i ".rounds[${idx}].output.user_selection = \"${user_selection}\"" "$log_path"

    if [[ -n "$decision_rationale" ]]; then
        yq -i ".rounds[${idx}].traceability.decision_rationale = \"${decision_rationale}\"" "$log_path"
    fi

    yq -i ".metadata.updated_at = \"$(_timestamp)\"" "$log_path"
}

# ============================================================================
# yaml_add_option
# Add presented option to round
#
# Args:
#   $1 - Log file path
#   $2 - Round number
#   $3 - Option label
#   $4 - Rationale (판단근거)
# ============================================================================
yaml_add_option() {
    local log_path="$1"
    local round_num="$2"
    local label="$3"
    local rationale="$4"

    _check_yq || return 1

    local idx=$((round_num - 1))

    # Escape quotes
    label="${label//\"/\\\"}"
    rationale="${rationale//\"/\\\"}"

    local option_json
    option_json=$(cat << EOF
{
  "label": "${label}",
  "rationale": "${rationale}"
}
EOF
)

    yq -i ".rounds[${idx}].output.options_presented += [${option_json}]" "$log_path"
    yq -i ".metadata.updated_at = \"$(_timestamp)\"" "$log_path"
}

# ============================================================================
# yaml_save_component_feedback
# Save aggregated feedback for a component
#
# Args:
#   $1 - Log file path
#   $2 - Component ID
#   $3 - Summary text
# ============================================================================
yaml_save_component_feedback() {
    local log_path="$1"
    local comp_id="$2"
    local summary="$3"

    _check_yq || return 1

    # Escape quotes
    summary="${summary//\"/\\\"}"

    # Initialize component feedback entry
    yq -i ".component_feedback.\"${comp_id}\" = {
        \"analyzed_at\": \"$(_timestamp)\",
        \"summary\": \"${summary}\",
        \"findings\": [],
        \"recommendations\": [],
        \"issues\": []
    }" "$log_path"

    # Update component status
    yq -i "(.decomposition.components[] | select(.id == \"${comp_id}\")).status = \"completed\"" "$log_path"

    # Increment analyzed count
    local analyzed
    analyzed=$(yq '.state.analyzed_components' "$log_path")
    yq -i ".state.analyzed_components = $((analyzed + 1))" "$log_path"
    yq -i ".metadata.updated_at = \"$(_timestamp)\"" "$log_path"

    echo "✅ Component feedback saved: ${comp_id}"
}

# ============================================================================
# yaml_update_handoff
# Prepare handoff context for /research
#
# Args:
#   $1 - Log file path
#   $2 - Summary text
#   $3 - Key findings (comma-separated)
#   $4 - Priority components (comma-separated)
#   $5 - Recommended focus areas (comma-separated)
# ============================================================================
yaml_update_handoff() {
    local log_path="$1"
    local summary="$2"
    local key_findings="$3"
    local priority_comps="$4"
    local focus_areas="$5"

    _check_yq || return 1

    # Escape quotes
    summary="${summary//\"/\\\"}"

    yq -i ".handoff.ready_for_research = true" "$log_path"
    yq -i ".handoff.research_context.summary = \"${summary}\"" "$log_path"

    # Convert comma-separated to arrays
    IFS=',' read -ra FINDINGS <<< "$key_findings"
    for f in "${FINDINGS[@]}"; do
        f=$(echo "$f" | xargs)  # trim whitespace
        [[ -n "$f" ]] && yq -i ".handoff.research_context.key_findings += [\"${f}\"]" "$log_path"
    done

    IFS=',' read -ra COMPS <<< "$priority_comps"
    for c in "${COMPS[@]}"; do
        c=$(echo "$c" | xargs)
        [[ -n "$c" ]] && yq -i ".handoff.research_context.priority_components += [\"${c}\"]" "$log_path"
    done

    IFS=',' read -ra FOCUS <<< "$focus_areas"
    for f in "${FOCUS[@]}"; do
        f=$(echo "$f" | xargs)
        [[ -n "$f" ]] && yq -i ".handoff.research_context.recommended_focus += [\"${f}\"]" "$log_path"
    done

    yq -i ".state.current_phase = \"handoff\"" "$log_path"
    yq -i ".metadata.updated_at = \"$(_timestamp)\"" "$log_path"

    echo "✅ Handoff context prepared"
}

# ============================================================================
# yaml_finalize_architecture
# Mark session as completed
#
# Args:
#   $1 - Log file path
# ============================================================================
yaml_finalize_architecture() {
    local log_path="$1"

    _check_yq || return 1

    yq -i '.metadata.status = "completed"' "$log_path"
    yq -i ".metadata.updated_at = \"$(_timestamp)\"" "$log_path"

    # Compute context hash for integrity
    local hash
    hash=$(yq '.user_intent, .rounds, .component_feedback' "$log_path" | sha256sum | cut -d' ' -f1)
    yq -i ".pipeline.context_hash = \"${hash}\"" "$log_path"

    echo "✅ Re-architecture session finalized"
}

# ============================================================================
# yaml_get_field
# Read specific field from YAML log
#
# Args:
#   $1 - Log file path
#   $2 - Field path (e.g., ".state.round", ".rounds[-1].analysis")
#
# Output:
#   Field value
# ============================================================================
yaml_get_field() {
    local log_path="$1"
    local field_path="$2"

    _check_yq || return 1

    yq "${field_path}" "$log_path"
}

# ============================================================================
# yaml_add_decision_trace
# Add decision to pipeline trace
#
# Args:
#   $1 - Log file path
#   $2 - Round number
#   $3 - Decision description
#   $4 - Reason
# ============================================================================
yaml_add_decision_trace() {
    local log_path="$1"
    local round_num="$2"
    local decision="$3"
    local reason="$4"

    _check_yq || return 1

    # Escape quotes
    decision="${decision//\"/\\\"}"
    reason="${reason//\"/\\\"}"

    local trace_json
    trace_json=$(cat << EOF
{
  "round": ${round_num},
  "decision": "${decision}",
  "reason": "${reason}",
  "timestamp": "$(_timestamp)"
}
EOF
)

    yq -i ".pipeline.decision_trace += [${trace_json}]" "$log_path"
    yq -i ".metadata.updated_at = \"$(_timestamp)\"" "$log_path"
}

# ============================================================================
# EXPORTS
# ============================================================================
# ============================================================================
# TASK DELEGATION FUNCTIONS
# ============================================================================
# Task 도구를 통한 서브에이전트 위임 함수들
# claude-code-guide 에이전트가 없을 경우 general-purpose로 대체
# ============================================================================

# ============================================================================
# delegate_component_analysis
# 컴포넌트 심층 분석을 서브에이전트에 위임
#
# Args:
#   $1 - Component path
#   $2 - Component name
#   $3 - Analysis focus (structure|dependencies|patterns|issues)
#
# Output:
#   Analysis result (JSON format)
#
# Note: Claude Code 내에서 Task 도구로 호출해야 함 (bash에서 직접 호출 불가)
# ============================================================================
delegate_component_analysis() {
    local comp_path="$1"
    local comp_name="$2"
    local focus="${3:-structure}"

    # 이 함수는 실제로는 Claude Code의 Task 도구를 통해 호출됨
    # bash에서는 프롬프트 템플릿만 생성
    cat << EOF
{
  "subagent_type": "explore",
  "model": "opus",
  "prompt": "Analyze component '${comp_name}' at path '${comp_path}'. Focus on: ${focus}. Return findings in structured format with: 1) Architecture overview, 2) Key patterns used, 3) Dependencies (upstream/downstream), 4) Potential issues or tech debt, 5) Recommendations for improvement.",
  "description": "Analyze ${comp_name} component"
}
EOF
}

# ============================================================================
# delegate_external_research
# 외부 문서/리소스 조사를 서브에이전트에 위임
#
# Args:
#   $1 - Research topic
#   $2 - Context (optional)
#
# Output:
#   Task delegation prompt (JSON format)
#
# Note: claude-code-guide 에이전트 대체로 general-purpose 사용
# ============================================================================
delegate_external_research() {
    local topic="$1"
    local context="${2:-}"

    cat << EOF
{
  "subagent_type": "general-purpose",
  "model": "sonnet",
  "prompt": "Research external documentation and best practices for: '${topic}'. ${context:+Context: ${context}. }Use WebSearch and WebFetch to gather information. Return: 1) Key concepts and patterns, 2) Best practices, 3) Common pitfalls, 4) Relevant documentation links, 5) Code examples if available.",
  "description": "Research ${topic}",
  "allowed_tools": ["WebSearch", "WebFetch", "Read"]
}
EOF
}

# ============================================================================
# delegate_codebase_exploration
# 코드베이스 탐색을 Explore 에이전트에 위임
#
# Args:
#   $1 - Search query or pattern
#   $2 - Scope path (optional)
#   $3 - Thoroughness (quick|medium|very thorough)
#
# Output:
#   Task delegation prompt (JSON format)
# ============================================================================
delegate_codebase_exploration() {
    local query="$1"
    local scope="${2:-.}"
    local thoroughness="${3:-medium}"

    cat << EOF
{
  "subagent_type": "explore",
  "model": "opus",
  "prompt": "Explore the codebase for: '${query}'. Scope: ${scope}. Thoroughness: ${thoroughness}. Find relevant files, patterns, and relationships. Return L1 summary with key findings.",
  "description": "Explore codebase for ${query}"
}
EOF
}

# ============================================================================
# delegate_architecture_planning
# 아키텍처 계획을 Plan 에이전트에 위임
#
# Args:
#   $1 - Planning topic
#   $2 - Constraints (optional)
#   $3 - Output path for L2/L3
#
# Output:
#   Task delegation prompt (JSON format)
# ============================================================================
delegate_architecture_planning() {
    local topic="$1"
    local constraints="${2:-}"
    local output_path="${3:-.agent/outputs/Plan/}"

    cat << EOF
{
  "subagent_type": "plan",
  "model": "opus",
  "prompt": "Create architecture plan for: '${topic}'. ${constraints:+Constraints: ${constraints}. }Output L1/L2/L3 progressive disclosure format. Save detailed plan to ${output_path}.",
  "description": "Plan architecture for ${topic}"
}
EOF
}

# ============================================================================
# generate_task_prompt
# SKILL.md에서 사용할 Task 도구 호출 프롬프트 생성
#
# Args:
#   $1 - Delegation type (component|external|explore|plan)
#   $2+ - Type-specific arguments
#
# Output:
#   Complete Task tool invocation template
# ============================================================================
generate_task_prompt() {
    local delegation_type="$1"
    shift

    case "$delegation_type" in
        component)
            delegate_component_analysis "$@"
            ;;
        external)
            delegate_external_research "$@"
            ;;
        explore)
            delegate_codebase_exploration "$@"
            ;;
        plan)
            delegate_architecture_planning "$@"
            ;;
        *)
            echo "ERROR: Unknown delegation type: $delegation_type" >&2
            return 1
            ;;
    esac
}

# ============================================================================
# EXPORTS
# ============================================================================
export -f yaml_init_architecture_log
export -f yaml_update_state
export -f yaml_add_user_intent
export -f yaml_set_decomposition
export -f yaml_add_component
export -f yaml_append_round
export -f yaml_add_finding
export -f yaml_add_recommendation
export -f yaml_add_issue
export -f yaml_update_round_output
export -f yaml_add_option
export -f yaml_save_component_feedback
export -f yaml_update_handoff
export -f yaml_finalize_architecture
export -f yaml_get_field
export -f yaml_add_decision_trace

# Task delegation exports
export -f delegate_component_analysis
export -f delegate_external_research
export -f delegate_codebase_exploration
export -f delegate_architecture_planning
export -f generate_task_prompt
