---
name: clarify
description: |
  Discover and refine user requirements through iterative conversation.
  Capture and preserve Design Intent across the entire pipeline lifecycle.

  Core Capabilities:
  - Requirement Discovery: Uncover implicit needs through natural dialogue
  - Design Intent Tracking: Record WHY behind each decision (design_intent, decision_rationale)
  - Machine-Readable YAML Logging: Every interaction logged for traceability
  - Semantic Integrity: Eliminate ambiguity while preserving original meaning
  - EFL Pattern Execution: Full P1-P6 implementation with Phase 3-A/3-B synthesis

  Output Format:
  - L1: YAML summary for main orchestrator (500 tokens)
  - L2: Human-readable clarification overview (2000 tokens)
  - L3: Complete clarify.yaml document

  Pipeline Position:
  - Optional clarification phase (not mandatory entry point)
  - Users may skip to /research if requirements are already clear
  - Handoff to /research when clarification is complete
user-invocable: true
disable-model-invocation: false
context: fork
model: opus
version: "3.1.0"
argument-hint: "<request> | --resume <slug> | --list"
allowed-tools:
  - Read
  - Write
  - Grep
  - Glob
  - AskUserQuestion
  - mcp__sequential-thinking__sequentialthinking
  - Task
  - WebSearch
hooks:
  Setup:
    - type: command
      command: "source /home/palantir/.claude/skills/shared/parallel-agent.sh"
      timeout: 5000
      once: true
  Stop:
    - type: command
      command: "/home/palantir/.claude/hooks/clarify-validate.sh"
      timeout: 10000
    - type: command
      command: "/home/palantir/.claude/hooks/clarify-finalize.sh"
      timeout: 150000

# =============================================================================
# P1: Skill as Sub-Orchestrator
# =============================================================================
agent_delegation:
  enabled: true
  default_mode: true  # V1.1.0: Auto-delegation by default
  max_sub_agents: 3
  delegation_strategy: "auto"
  strategies:
    scope_based:
      description: "Delegate by requirement scope (functional, non-functional, constraints)"
      use_when: "Complex multi-faceted requirements"
    domain_based:
      description: "Delegate by domain area (frontend, backend, infra)"
      use_when: "Cross-domain clarification"
  slug_orchestration:
    enabled: true
    source: "user input or active workload"
    action: "create new workload context"
  sub_agent_permissions:
    - Read
    - Write  # Required for L1/L2/L3 output
    - Glob
    - Grep
    - WebSearch
  output_paths:
    l1: ".agent/prompts/{slug}/clarify/l1_summary.yaml"
    l2: ".agent/prompts/{slug}/clarify/l2_index.md"
    l3: ".agent/prompts/{slug}/clarify/l3_details/"
  return_format:
    l1: "Clarification summary with requirement count and confidence (≤500 tokens)"
    l2_path: ".agent/prompts/{slug}/clarify/l2_index.md"
    l3_path: ".agent/prompts/{slug}/clarify/l3_details/"
    requires_l2_read: false
    next_action_hint: "/research"
  description: |
    This skill operates as a Sub-Orchestrator (P1).
    It delegates clarification work to Clarify Agents rather than executing directly.
    L1 returns to main context; L2/L3 always saved to files.

# =============================================================================
# P2: Parallel Agent Configuration
# =============================================================================
parallel_agent_config:
  enabled: true
  complexity_detection: "auto"
  agent_count_by_complexity:
    simple: 1      # Basic clarification (single requirement)
    moderate: 2    # Standard clarification (2-3 requirements)
    complex: 3     # Complex clarification (4+ requirements)
  synchronization_strategy: "barrier"  # Wait for all agents
  aggregation_strategy: "merge"        # Merge all clarification outputs
  clarification_areas:
    - functional_requirements
    - non_functional_requirements
    - constraints_and_assumptions
  description: |
    Deploy multiple Clarify Agents in parallel for comprehensive requirement analysis.
    Agent count scales with detected complexity (requirement count).
    All agents run Phase 1 simultaneously, then results are aggregated.

# =============================================================================
# P3: General-Purpose Synthesis Configuration
# =============================================================================
synthesis_config:
  phase_3a_l2_horizontal:
    enabled: true
    description: "Cross-validate clarification areas for consistency"
    validation_criteria:
      - cross_area_consistency
      - requirement_completeness
      - design_intent_alignment
  phase_3b_l3_vertical:
    enabled: true
    description: "Verify requirements against codebase context"
    validation_criteria:
      - requirement_implementability
      - existing_pattern_alignment
      - scope_feasibility
  phase_3_5_review_gate:
    enabled: true
    description: "Main Agent holistic verification"
    criteria:
      - requirement_alignment
      - design_flow_consistency
      - gap_detection
      - conclusion_clarity

# =============================================================================
# P4: Selective Feedback Loop
# =============================================================================
selective_feedback:
  enabled: true
  severity_filter: "warning"
  feedback_targets:
    - gate: "CLARIFY"
      severity: ["error", "warning"]
      action: "block_on_error"
    - gate: "REQUIREMENT"
      severity: ["error"]
      action: "block"
  description: |
    Severity-based filtering for Gate 1 validation warnings.
    Errors block clarification. Warnings are logged but allow continuation.

# =============================================================================
# P5: Repeat Until Approval
# =============================================================================
repeat_until_approval:
  enabled: true
  max_rounds: 10
  approval_criteria:
    - "User explicitly approves clarified requirements"
    - "All ambiguities resolved"
    - "Design intent captured"
  description: |
    Continuous clarification loop until user satisfaction.
    User can approve, provide feedback, or cancel at any round.

# =============================================================================
# P6: Agent Internal Feedback Loop
# =============================================================================
agent_internal_feedback_loop:
  enabled: true
  max_iterations: 3
  validation_criteria:
    - "All requirements have clear acceptance criteria"
    - "Design intent is explicit and documented"
    - "No contradictory requirements"
    - "Scope is well-defined"
  refinement_triggers:
    - "Missing acceptance criteria detected"
    - "Vague or ambiguous language found"
    - "Contradictory requirements detected"
  description: |
    Local clarification refinement loop before presenting to user.
    Self-validates requirement clarity and iterates until quality threshold met.

# =============================================================================
# P5: Review Gate (EFL V3.0 Compliance)
# =============================================================================
review_gate:
  enabled: true
  phase: "pre_research"
  criteria:
    - "requirements_complete"
    - "ambiguity_resolved"
    - "scope_defined"
    - "design_intent_captured"
  auto_approve: false
  description: |
    Review gate before handoff to /research.
    Ensures clarified requirements are complete and unambiguous.
---

### Auto-Delegation Trigger (CRITICAL)

> **Reference:** `.claude/skills/shared/auto-delegation.md`
> **Behavior:** When `agent_delegation.enabled: true` AND `default_mode: true`, skill automatically operates as Sub-Orchestrator.

```javascript
// AUTO-DELEGATION CHECK - Execute at skill invocation
// If complex task detected, triggers: analyze → delegate → collect
const delegationDecision = checkAutoDelegation(SKILL_CONFIG, userRequest)
if (delegationDecision.shouldDelegate) {
  const complexity = analyzeTaskComplexity(taskDescription, SKILL_CONFIG)
  return executeDelegation(taskDescription, complexity, SKILL_CONFIG)
}
// Simple tasks execute directly without delegation overhead
```


# /clarify - Requirement Clarification with EFL (V3.0.0)

> **Version:** 3.0.0 (EFL Pattern)
> **Role:** Requirement Discovery and Clarification with Full EFL Implementation
> **Pipeline Position:** Entry point, Before /research
> **EFL Template:** `.claude/skills/shared/efl-template.md`


---

## 1. Purpose

Discover and refine user requirements using Enhanced Feedback Loop (EFL) pattern:

1. **Phase 1**: Deploy parallel Clarify Agents for different requirement areas
2. **Phase 2**: Aggregate L1 summaries from all agents
3. **Phase 3-A**: L2 Horizontal Synthesis (cross-area consistency)
4. **Phase 3-B**: L3 Vertical Verification (codebase context alignment)
5. **Phase 3.5**: Main Agent Review Gate (holistic verification)
6. **Phase 4**: Selective Feedback Loop (if issues found)
7. **Phase 5**: User Final Approval Loop

### Pipeline Integration

```
[/clarify] → /research → /planning → /orchestrate → Workers → /synthesis
     │
     ├── Phase 1: Parallel Clarify Agents (P2)
     ├── Phase 2: L1 Aggregation
     ├── Phase 3-A: L2 Horizontal Synthesis (P3)
     ├── Phase 3-B: L3 Vertical Verification (P3)
     ├── Phase 3.5: Main Agent Review Gate (P1)
     ├── Phase 4: Selective Feedback Loop (P4)
     ├── Phase 5: User Approval (P5)
     └── Output: .agent/prompts/{slug}/clarify.yaml
```


---

## 1.5 EFL Execution Flow

### 1.5.1 Phase 1: Parallel Clarify Agent Deployment (P2)

```javascript
async function phase1_parallel_clarify_agents(userRequest) {
  // Determine complexity and agent count
  const estimatedRequirements = estimateRequirementCount(userRequest)
  const agentCount = getAgentCountByComplexity(estimatedRequirements)

  console.log(`📊 Complexity: ${estimatedRequirements} requirements → ${agentCount} agents`)

  // Divide clarification into areas
  const clarifyAreas = [
    { id: "func", name: "Functional Requirements", focus: "what the system should do" },
    { id: "nfr", name: "Non-Functional Requirements", focus: "quality attributes" },
    { id: "constraints", name: "Constraints & Assumptions", focus: "limitations and context" }
  ].slice(0, agentCount)

  // Deploy parallel Clarify Agents with P6 self-validation
  const agents = clarifyAreas.map(area => Task({
    subagent_type: "general-purpose",
    model: "opus",
    prompt: `
## Clarification Area: ${area.name}

### User Request
${userRequest}

### Your Focus
Analyze and clarify: **${area.focus}**

### Internal Feedback Loop (P6 - REQUIRED)
1. Generate clarification output for your area
2. Self-validate:
   - Clarity: Are requirements unambiguous?
   - Completeness: Are all aspects covered?
   - Testability: Can each requirement be verified?
3. If validation fails, revise and retry (max 3 iterations)
4. Output only after validation passes

### Output Format
Return YAML:
\`\`\`yaml
areaId: "${area.id}"
areaName: "${area.name}"
status: "success"

l1Summary:
  requirementCount: {number}
  keyFindings: [...]
  ambiguitiesFound: [...]

requirements:
  - id: "REQ-{n}"
    description: "..."
    acceptanceCriteria: [...]
    priority: "HIGH|MEDIUM|LOW"
    designIntent: "..."

internalLoopStatus:
  iterations: {1-3}
  validationStatus: "passed"
  issuesResolved: [...]
\`\`\`
`,
    description: `Clarify Agent: ${area.name}`
  }))

  // Wait for all agents (barrier synchronization)
  const results = await Promise.all(agents)

  return {
    agentCount,
    clarifyAreas,
    results,
    l1s: results.map(r => r.l1Summary),
    requirements: results.flatMap(r => r.requirements || [])
  }
}
```

### 1.5.2 Phase 3-A: L2 Horizontal Synthesis (P3)

```javascript
async function phase3a_l2_horizontal_synthesis(aggregatedL1, requirements) {
  const synthesis = await Task({
    subagent_type: "general-purpose",
    model: "opus",
    prompt: `
## L2 Horizontal Synthesis for Clarification

### Input
Aggregated L1 from ${aggregatedL1.totalAgents} Clarify Agents:
${JSON.stringify(aggregatedL1, null, 2)}

Requirements (${requirements.length} total):
${requirements.map(r => `- ${r.id}: ${r.description}`).join('\n')}

### Task
1. **Cross-validate** all clarification areas for consistency
2. **Identify contradictions** between areas
3. **Detect gaps** in requirement coverage
4. **Synthesize** into unified requirement document

### Internal Feedback Loop (P6)
Self-validate synthesis, retry up to 3 times if issues found.

### Output Format
\`\`\`yaml
phase3a_L1:
  synthesisStatus: "success"
  consistencyScore: {0-100}
  contradictionsFound: {count}
  gapsDetected: {count}

phase3a_L2:
  unifiedRequirements: [...]
  crossAreaAnalysis:
    consistencyIssues: [...]
    resolvedContradictions: [...]
    gapsFilled: [...]

internalLoopStatus:
  iterations: {1-3}
  validationStatus: "passed"
\`\`\`
`,
    description: "L2 Horizontal Synthesis for Clarification"
  })

  return synthesis
}
```

### 1.5.3 Phase 3.5: Main Agent Review Gate (P1)

```javascript
async function phase3_5_main_agent_review(synthesisResult, userRequest) {
  const reviewCriteria = {
    requirement_alignment: "Does clarification match original request?",
    design_flow_consistency: "Is requirement flow logical?",
    gap_detection: "Are important requirements missing?",
    conclusion_clarity: "Is clarification actionable for /research?"
  }

  const reviewIssues = []

  for (const [criterion, question] of Object.entries(reviewCriteria)) {
    const passed = evaluateCriterion(synthesisResult, criterion)
    if (!passed.result) {
      reviewIssues.push({
        type: criterion,
        description: passed.reason,
        severity: passed.severity
      })
    }
  }

  if (reviewIssues.length === 0) {
    console.log("✅ Phase 3.5: Main Agent review PASSED")
    return { reviewPassed: true, skipToPhase5: true }
  }

  return { reviewPassed: false, reviewIssues, proceedToPhase4: true }
}
```


---


---

## 1. Execution Protocol

### 1.1 Argument Parsing (V2.5.0)

> **Claude Code V2.1.19+ Compliant**: Uses `$ARGUMENTS` placeholder with flag parsing

```bash
# $ARGUMENTS parsing with enhanced error handling
# Supports: <request> | --resume <slug> | --list

parse_arguments() {
    local args="$ARGUMENTS"

    # Mode 1: List available sessions
    if [[ "$args" == "--list" ]]; then
        LIST_MODE=true
        list_available_sessions
        return 0
    fi

    # Mode 2: Resume existing session
    if [[ "$args" == --resume* ]]; then
        RESUME_MODE=true
        SLUG="${args#--resume }"
        SLUG="${SLUG## }"  # Trim leading spaces

        # Validation: Check slug provided
        if [[ -z "$SLUG" ]]; then
            echo "❌ Missing slug: /clarify --resume <slug>"
            echo ""
            echo "Available sessions:"
            list_available_sessions
            return 1
        fi

        # Workload-scoped path (V2.2.0)
        LOG_PATH=".agent/prompts/${SLUG}/clarify.yaml"

        # Validation: Check file exists
        if [[ ! -f "$LOG_PATH" ]]; then
            echo "❌ Session not found: $SLUG"
            echo ""
            echo "Available sessions:"
            list_available_sessions
            return 1
        fi

        return 0
    fi

    # Mode 3: New session
    RESUME_MODE=false
    USER_INPUT="$args"
    return 0
}

list_available_sessions() {
    # List all clarify sessions with status
    local sessions=$(ls .agent/prompts/*/clarify.yaml 2>/dev/null)

    if [[ -z "$sessions" ]]; then
        echo "   (no sessions found)"
        return
    fi

    for session in $sessions; do
        local slug=$(echo "$session" | sed 's|.*/prompts/\([^/]*\)/.*|\1|')
        local status=$(grep "status:" "$session" 2>/dev/null | head -1 | awk '{print $2}' | tr -d '"')
        echo "   - $slug [$status]"
    done
}
```

**Supported Arguments:**

| Argument | Description | Example |
|----------|-------------|---------|
| `<request>` | New clarification session | `/clarify "Implement OAuth2"` |
| `--resume <slug>` | Resume existing session | `/clarify --resume oauth2-20260129` |
| `--list` | List available sessions | `/clarify --list` |

### 1.2 Initialize (New Session) - V2.5.0

> **Centralized Workload Management**: Uses shared modules from `.claude/skills/shared/`

```bash
# Source shared modules (slug-generator v1.1.0, workload-files v1.1.0)
source /home/palantir/.claude/skills/shared/slug-generator.sh
source /home/palantir/.claude/skills/shared/workload-files.sh
source /home/palantir/.claude/skills/clarify/helpers.sh

# Generate unique workload ID and slug
# Format: {topic}_{YYYYMMDD}_{HHMMSS} → {topic}-{YYYYMMDD}-{HHMMSS}
# CRITICAL-003 FIX: HHMMSS included to prevent same-day collisions
WORKLOAD_ID=$(generate_workload_id "$USER_INPUT")
SLUG=$(generate_slug_from_workload "$WORKLOAD_ID")

# Workload-scoped paths (V7.1)
WORKLOAD_DIR=".agent/prompts/${SLUG}"
LOG_PATH="${WORKLOAD_DIR}/clarify.yaml"

# Initialize workload directory with standard structure
init_workload_directory "$WORKLOAD_ID" "clarify" "$USER_INPUT"

# Standard workload files created:
# - _context.yaml    : Workload context (upstream, global_context, reference_files)
# - _progress.yaml   : Progress tracking (status, workers, metrics)
# - pending/         : Worker task prompts (pending)
# - completed/       : Worker task prompts (completed)
# - outputs/         : Worker-specific outputs (terminal-b/, terminal-c/, terminal-d/)

# Initialize clarify-specific YAML log
yaml_init_log "$LOG_PATH" "$USER_INPUT" "$WORKLOAD_ID"

# Set as active workload
set_active_workload "$WORKLOAD_ID"
```

**Workload Directory Structure:**

```
.agent/prompts/{slug}/
├── _context.yaml       # Workload context
├── _progress.yaml      # Progress tracking
├── clarify.yaml        # This skill's output
├── pending/            # Worker prompts (pending)
├── completed/          # Worker prompts (completed)
└── outputs/            # Worker outputs
    ├── terminal-b/
    ├── terminal-c/
    └── terminal-d/
```

**Slug Generation Example:**

| Input | Workload ID | Slug |
|-------|-------------|------|
| "Implement OAuth2 flow" | `implement-oauth2-flow_20260129_154500` | `implement-oauth2-flow-20260129-154500` |

### 1.3 Resume (Existing Session)

```bash
if [[ "$RESUME_MODE" == "true" ]]; then
    # Load existing session
    if [[ ! -f "$LOG_PATH" ]]; then
        echo "❌ Session not found: $SLUG"
        exit 1
    fi

    # Extract last state
    ROUND_NUM=$(yaml_get_field "$LOG_PATH" ".metadata.rounds")
    CURRENT_INPUT=$(yaml_get_field "$LOG_PATH" ".rounds[-1].improved_prompt")
fi
```


---

## 2. YAML Log Schema

### 2.1 Full Schema

```yaml
# .agent/prompts/{slug}/clarify.yaml (Workload-scoped V2.2.0)
metadata:
  id: "{slug}"
  version: "2.0.0"
  created_at: "2026-01-24T18:13:32Z"
  updated_at: "2026-01-24T18:15:00Z"
  status: "in_progress"  # in_progress | completed | cancelled
  rounds: 0
  final_approved: false

original_request: |
  {원본 사용자 요청}

rounds:
  - round: 1
    timestamp: "2026-01-24T18:13:35Z"
    input: "{current round input from user}"
    agent_analysis: |
      {Opus's understanding of the request - what user wants and why}
    clarified_prompt: |
      {refined/clarified version of the request}
    user_response: "approved"  # approved | revision_requested | cancelled
    user_feedback: null
    # V2.5.0: Design Intent Tracking
    design_intent: |
      {WHY user made this request - inferred from conversation context}
    decision_rationale: |
      {reasoning behind decisions made in this round}

final_output:
  approved_prompt: |
    {final approved prompt ready for downstream skills}
  design_intent_summary: |
    {consolidated design intent from all rounds}
  key_decisions:
    - round: 1
      decision: "{what was decided}"
      rationale: "{why}"

# Pipeline Integration Fields
pipeline:
  downstream_skills: []    # 이후 호출된 스킬 추적
  task_references: []      # 연결된 Task ID
  context_hash: null       # SHA256 무결성 해시
  decision_trace:          # 주요 결정 기록
    - round: 1
      decision: "CoT 적용"
      reason: "분석 작업"
```

### 2.2 Schema Sections

| Section | Purpose | When Updated |
|---------|---------|--------------|
| `metadata` | 세션 메타데이터 | 매 라운드 |
| `original_request` | 원본 요청 보존 | 초기화 시 |
| `rounds` | 라운드별 상호작용 | 매 라운드 |
| `final_output` | 최종 승인 결과 | 승인 시 |
| `pipeline` | 스킬 파이프라인 통합 | Stop hook |


---

## 3. Main Loop - Conversation-Centric Clarification (V2.5.0)

> **Core Goals:**
> 1. Transform ambiguous requirements into clear, actionable specifications
> 2. Capture user's design intent through natural dialogue

```python
APPROVED = False
ROUND_NUM = 1
conversation_history = []

while not APPROVED:
    # Step 1: Analyze current input
    # Opus uses semantic understanding to identify:
    # - What user wants (explicit requirements)
    # - Why they want it (implicit design intent)
    # - What's unclear or ambiguous
    analysis = analyze_requirement(current_input, conversation_history)

    # Step 2: Generate clarified version
    # If ambiguities detected, ask clarifying questions
    # If clear, produce refined specification
    if analysis["has_ambiguities"]:
        clarified = generate_clarifying_questions(analysis)
    else:
        clarified = generate_refined_specification(analysis)

    # Step 3: Extract design intent from conversation context
    design_intent = extract_design_intent(current_input, conversation_history)
    decision_rationale = generate_decision_rationale(analysis, clarified)

    # Step 4: Record to YAML log (before user response)
    yaml_append_round(
        log_path=LOG_PATH,
        round_num=ROUND_NUM,
        input=current_input,
        agent_analysis=analysis["summary"],
        clarified_prompt=clarified,
        response="pending",
        design_intent=design_intent,
        decision_rationale=decision_rationale
    )

    # Step 5: Present to user
    present_round_result(
        round_num=ROUND_NUM,
        original_input=current_input,
        analysis=analysis,
        clarified=clarified
    )

    # Step 6: Get user response
    response = AskUserQuestion(
        questions=[{
            "question": "How would you like to proceed?",
            "header": f"Round {ROUND_NUM}",
            "options": [
                {"label": "Approve (Recommended)", "description": "Proceed with this clarified requirement"},
                {"label": "Provide feedback", "description": "Add details or corrections"}
            ],
            "multiSelect": False
        }],
        metadata={"source": f"clarify-round-{ROUND_NUM}"}
    )

    # Step 7: Handle response
    if response == "Approve":
        APPROVED = True
        yaml_finalize(LOG_PATH, clarified, design_intent)
        yaml_update_round(LOG_PATH, ROUND_NUM, "user_response", "approved")

        # Add to conversation history for downstream reference
        conversation_history.append({
            "round": ROUND_NUM,
            "input": current_input,
            "clarified": clarified,
            "design_intent": design_intent
        })

    elif response == "Provide feedback":
        feedback = get_user_feedback()
        conversation_history.append({
            "round": ROUND_NUM,
            "input": current_input,
            "clarified": clarified,
            "feedback": feedback
        })
        current_input = feedback  # User feedback becomes next input
        yaml_update_round(LOG_PATH, ROUND_NUM, "user_response", "revision_requested")
        yaml_update_round(LOG_PATH, ROUND_NUM, "user_feedback", feedback)
        ROUND_NUM += 1

    else:
        yaml_cancel(LOG_PATH, "User cancelled")
        break
```

**Key Functions:**

| Function | Purpose |
|----------|---------|
| `analyze_requirement()` | Identify explicit/implicit requirements, detect ambiguities |
| `generate_clarifying_questions()` | Ask targeted questions to resolve ambiguities |
| `generate_refined_specification()` | Produce clear, actionable requirement spec |
| `extract_design_intent()` | Capture WHY behind the request |
| `generate_decision_rationale()` | Document reasoning for this round's decisions |


---

## 4. Core Functions (V2.5.0)

### 4.1 Design Intent Extraction

```python
def extract_design_intent(current_input, conversation_history):
    """
    Extract user's design intent from conversation context.

    Using Opus's semantic understanding:
    - Infer WHY user made this request
    - Identify intent patterns from previous round feedback
    - Make implicit requirements explicit

    Returns:
        str: Extracted design intent (1-3 sentences)
    """
    # Opus analyzes conversation context to infer intent
    # Uses semantic understanding, not keyword matching
    pass  # Delegated to Opus reasoning


def generate_decision_rationale(analysis, clarified_prompt):
    """
    Generate rationale for decisions made in this round.

    Records:
    - Why certain clarifications were made
    - What judgments were applied
    - Context for downstream skills to reference

    Returns:
        str: Decision rationale (2-4 sentences)
    """
    # Opus explains its decision process
    pass  # Delegated to Opus reasoning
```

### 4.2 Requirement Analysis

```python
def analyze_requirement(current_input, conversation_history):
    """
    Analyze user's requirement to identify clarity and ambiguities.

    Returns:
        dict: {
            "summary": str,           # Agent's understanding
            "has_ambiguities": bool,  # Whether clarification needed
            "ambiguities": list,      # Specific unclear points
            "explicit_reqs": list,    # Clear requirements
            "implicit_reqs": list     # Inferred requirements
        }
    """
    pass  # Delegated to Opus reasoning


def generate_clarifying_questions(analysis):
    """
    Generate targeted questions to resolve ambiguities.

    Returns:
        str: Clarifying questions for user
    """
    pass  # Delegated to Opus reasoning


def generate_refined_specification(analysis):
    """
    Produce clear, actionable requirement specification.

    Returns:
        str: Refined specification ready for downstream skills
    """
    pass  # Delegated to Opus reasoning
```


---

## 5. User Interaction Format (V2.5.0)

> **Core Principle:** Each round presents detailed analysis, recommendations,
> and captures user feedback. All interactions are recorded to YAML for traceability.

### 5.1 Round Presentation Format

```markdown
## Round {n}: {component_or_topic_name}

### Current State
{detailed_explanation_of_current_component_or_requirement}

### Analysis
{agent_understanding_of_what_user_wants_and_why}

### Recommendations
| Item | Current | Recommended Change | Rationale |
|------|---------|-------------------|-----------|
| {item_1} | {current_state} | {proposed_change} | {why} |
| {item_2} | {current_state} | {proposed_change} | {why} |

### Questions for Feedback
1. {specific_question_1}
2. {specific_question_2}
3. Any additional requirements or corrections?

### Design Intent Captured
{inferred_design_intent_from_this_round}
```

### 5.2 Interaction Recording Protocol

**Every round MUST record to YAML:**

```yaml
rounds:
  - round: {n}
    timestamp: "{ISO8601}"
    component:
      name: "{component_name}"
      index: {n}
      total: {total}
    input: |
      {user_input_verbatim}
    agent_analysis: |
      {detailed_analysis_presented_to_user}
    recommendations:
      - item: "{what}"
        current: "{before}"
        proposed: "{after}"
        rationale: "{why}"
    questions:
      - id: "q1"
        question: "{question_text}"
        answer: "{user_answer}"
        action: "{resulting_action}"
    user_feedback: |
      {any_additional_user_feedback}
    applied_changes:
      - item: "{change_description}"
        description: "{details}"
    design_intent: |
      {captured_design_intent}
    decision_rationale: |
      {why_these_decisions_were_made}
```

### 5.3 AskUserQuestion Configuration

```yaml
questions:
  - question: "How would you like to proceed with these recommendations?"
    header: "Round {n}"
    options:
      - label: "Approve all (Recommended)"
        description: "Apply all recommended changes"
      - label: "Approve with modifications"
        description: "Provide specific feedback on recommendations"
      - label: "Skip this component"
        description: "Move to next component without changes"
    multiSelect: false
metadata:
  source: "clarify-round-{n}"
```

### 5.4 Feedback Integration Flow

```
┌─────────────────────────────────────────────────────────┐
│ Round Start                                             │
├─────────────────────────────────────────────────────────┤
│ 1. Present detailed component/requirement explanation   │
│ 2. Show current state analysis                          │
│ 3. Provide recommendations with rationale               │
│ 4. Ask specific questions                               │
├─────────────────────────────────────────────────────────┤
│ User Feedback                                           │
├─────────────────────────────────────────────────────────┤
│ 5. Capture all user responses                           │
│ 6. Apply approved changes                               │
│ 7. Record everything to YAML                            │
│ 8. Update design_intent and decision_rationale          │
├─────────────────────────────────────────────────────────┤
│ Next Round or Completion                                │
└─────────────────────────────────────────────────────────┘
```


---

## 6. Exit Conditions

### 6.1 Normal Exit (Success)

- User selects "Approve" on final round
- YAML status: `completed`
- Stop hooks trigger:
  1. `clarify-validate.sh` - Gate 1: Requirement Feasibility Validation
  2. `clarify-finalize.sh` - Finalization and pipeline integration

### 6.2 Abnormal Exit

| Condition | YAML Status | Recovery |
|-----------|-------------|----------|
| User cancels | `cancelled` | `/clarify --resume {slug}` |
| Error | `error` | Check logs, retry |
| Session timeout | `timeout` | Resume possible |

### 6.3 Completion Criteria

```yaml
# Session is complete when:
completion_criteria:
  - all_components_reviewed: true    # If component-based analysis
  - user_approved: true              # User explicitly approved
  - design_intent_captured: true     # Design intent recorded
  - yaml_log_complete: true          # All rounds logged
```


---

## 7. Post-Approval Routing

> **Note:** /clarify is an optional phase. Users may proceed to /research directly
> if requirements are already clear.

```python
if approved:
    # Suggest next skill based on clarified requirements
    next_skill = "/research"  # Default handoff target

    AskUserQuestion(
        questions=[{
            "question": "Clarification complete. Proceed to research phase?",
            "header": "Next Step",
            "options": [
                {"label": "Yes, run /research (Recommended)",
                 "description": "Deep analysis of requirements and codebase"},
                {"label": "No, save and exit",
                 "description": "Use clarified requirements later"}
            ],
            "multiSelect": False
        }],
        metadata={"source": "clarify-routing"}
    )
```

**Handoff Command:**
```bash
# Generated handoff for next skill
/research --clarify-slug {workload_slug}
```


---

## 8. Integration Points

### 8.1 Skill Pipeline

```
/clarify (optional entry point)
    │
    ▼ [YAML log created]
/research
    │
    ▼ [downstream_skills tracked]
/planning
    │
    ▼ [task_references linked]
/orchestrate → /worker → /collect → /synthesis
```

### 8.2 Log Reuse

```bash
# List previous sessions (Workload-scoped)
ls .agent/prompts/*/clarify.yaml

# Or use the --list argument
/clarify --list

# Resume specific session
/clarify --resume {slug}

# Search logs by content
grep -l "design_intent" .agent/prompts/*/clarify.yaml
```

### 8.3 Task Delegation Pattern (V2.1.16+)

> **Reference:** `/build/parameters/task-params.md`

```python
# Background research delegation (optional)
Task(
    subagent_type="Explore",
    prompt="Analyze codebase structure for requirement context",
    run_in_background=True,
    max_turns=10
)
```

### 8.4 Model Configuration

| Option | Behavior |
|--------|----------|
| `opus` (current) | High quality reasoning for requirement clarification |
| `inherit` | Use parent context model (when specified via CLI) |
| `haiku` | Fast response for simple requests |


---

## 9. Error Handling

| Error | Detection | Recovery |
|-------|-----------|----------|
| YAML write failure | File I/O error | Memory fallback + warning |
| Invalid slug | Resume with non-existent slug | Show available sessions |
| User timeout | No response | Auto-save, resume later |
| Hook failure | Stop hook error | Manual finalization |


---

## 10. Shift-Left Validation (Gate 1)

### 10.1 Purpose

Gate 1 validates requirement feasibility **before** proceeding to `/research`:
- Detects potentially missing files early
- Identifies vague requirements needing clarification
- Catches destructive operations before execution

### 10.2 Hook Integration

```yaml
hooks:
  Stop:
    - clarify-validate.sh  # Gate 1: Requirement Feasibility
    - clarify-finalize.sh  # Pipeline integration
```

### 10.3 Validation Results

| Result | Behavior | User Action |
|--------|----------|-------------|
| `passed` | ✅ Continue to next phase | None required |
| `passed_with_warnings` | ⚠️ Display warnings, allow proceed | Review warnings |
| `failed` | ❌ Block progression, request clarification | Address errors, re-run `/clarify` |


---

## 11. Testing Checklist

**Core Functionality:**
- [ ] `/clarify "test request"` basic execution
- [ ] `/clarify --resume {slug}` resume test
- [ ] `/clarify --list` session listing test
- [ ] YAML log schema validation
- [ ] AskUserQuestion metadata.source verification
- [ ] Stop hook trigger confirmation
- [ ] Gate 1 validation execution
- [ ] Warning/Error display verification
- [ ] Multi-round progression test
- [ ] Pipeline downstream_skills tracking test

**V2.5.0 Design Intent Tracking:**
- [ ] design_intent field populated each round
- [ ] decision_rationale field populated each round
- [ ] conversation_history accumulation across rounds
- [ ] Clarifying questions generated for ambiguous inputs
- [ ] Refined specification generated for clear inputs
- [ ] All user interactions recorded to YAML


---

## 12. Parameter Module Compatibility (V2.1.0)

> `/build/parameters/` 모듈과의 호환성 체크리스트

| Module | Status | Notes |
|--------|--------|-------|
| `model-selection.md` | ✅ | `sonnet` 설정, `inherit` 지원 문서화 |
| `context-mode.md` | ✅ | `fork` 사용, Task 위임 패턴 명시 |
| `tool-config.md` | ✅ | V2.1.0: `TodoWrite` 제거, Task API 사용 |
| `hook-config.md` | ✅ | Stop hook, 150000ms timeout |
| `permission-mode.md` | N/A | Skill에는 해당 없음 (Agent 전용) |
| `task-params.md` | ✅ | 8.3절 Task Delegation Pattern 참조 |

### Version History

| Version | Change |
|---------|--------|
| 2.0.0 | YAML logging, Stop hooks, PE technique library |
| 2.1.0 | Remove TodoWrite, Task API standardization, parameter module compatibility |
| 2.2.0 | Workload-scoped output paths (V7.1 compatible) |
| 2.3.0 | P4 Selective Feedback integration (deprecated in 2.5.0) |
| 2.4.0 | Standalone execution, handoff contract |
| 2.5.0 | **Conversation-Centric Redesign** - Remove PE techniques, add design intent tracking, YAML interaction logging, English documentation, optional entry point positioning |
| 3.0.0 | **Full EFL Implementation** |
| | P1-P6 complete |
| | Phase 3-A: L2 Horizontal Synthesis |
| | Phase 3-B: L3 Vertical Verification |
| | Phase 3.5: Main Agent Review Gate |
| | Phase 4: Selective Feedback Loop |
| | Phase 5: User Approval Loop |
| | Agent prompts include P6 self-validation |
| | eflMetrics in L1 output |
| | Write added to allowed-tools for L1/L2/L3 |


---

## 13. Standalone Execution (V2.4.0)

### 12.1 독립 실행 모드

`/clarify`는 파이프라인 진입점으로서 항상 독립적으로 실행됩니다:

```bash
# 독립 실행 (새 workload 자동 생성)
/clarify "OAuth2 구현 패턴 분석"

# Output: .agent/prompts/{auto-generated-slug}/clarify.yaml
```

### 12.2 Workload Context 초기화

```bash
# Source standalone module
source /home/palantir/.claude/skills/shared/skill-standalone.sh

# Initialize skill context
CONTEXT=$(init_skill_context "clarify" "$ARGUMENTS" "$USER_INPUT")

# Extract values
WORKLOAD_ID=$(echo "$CONTEXT" | jq -r '.workload_id')
SLUG=$(echo "$CONTEXT" | jq -r '.slug')
WORKLOAD_DIR=$(echo "$CONTEXT" | jq -r '.workload_dir')

# Always creates new workload for /clarify (entry point)
```


---

## 14. Handoff Contract (V2.4.0)

### 13.1 Handoff 매핑

| Status | Next Skill | Arguments |
|--------|------------|-----------|
| `completed` | `/research` | `--clarify-slug {slug}` |
| `partial` | `/research` (optional) | `--clarify-slug {slug}` |
| `error` | `null` | - |

### 13.2 Handoff YAML 출력

스킬 완료 시 clarify-finalize.sh hook이 다음 handoff 섹션을 출력에 추가:

```yaml

---

# Handoff Metadata (auto-generated)
handoff:
  skill: "clarify"
  workload_slug: "oauth2-implementation-20260128-143022"
  status: "completed"
  timestamp: "2026-01-28T14:35:00Z"
  next_action:
    skill: "/research"
    arguments: "--clarify-slug oauth2-implementation-20260128-143022"
    required: true
    reason: "Requirements clarified, ready for research"
```

### 13.3 다음 스킬 연계

```bash
# /clarify 완료 후 출력되는 handoff를 참조하여:
/research --clarify-slug oauth2-implementation-20260128-143022

# /research가 동일한 workload 내에서 실행됨
```

