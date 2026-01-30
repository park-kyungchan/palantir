---
name: synthesis
description: |
  Traceability matrix, quality validation, completion decision.

  **V3.0 Changes (EFL Integration):**
  - P1: Skill as Sub-Orchestrator (agent delegation)
  - P3: General-Purpose Synthesis (semantic matching replaces keyword matching)
  - P5: Phase 3.5 Review Gate (holistic verification)
  - P6: Agent Internal Feedback Loop with convergence detection

user-invocable: true
disable-model-invocation: false
context: fork
model: opus
version: "3.0.0"
argument-hint: "[--strict | --lenient | --dry-run]"
allowed-tools:
  - Read
  - Write
  - Grep
  - Glob
  - Task
  - mcp__sequential-thinking__sequentialthinking

# =============================================================================
# P1: Skill as Sub-Orchestrator
# =============================================================================
agent_delegation:
  enabled: true
  default_mode: true  # V1.1.0: Auto-delegation by default
  mode: "sub_orchestrator"
  description: "Synthesis delegates to specialized agents for semantic analysis"
  agents:
    - type: "explore"
      role: "Phase 3-A: Semantic requirement-deliverable matching"
      output_format: "L2 traceability matrix with confidence scores"
    - type: "explore"
      role: "Phase 3-B: Quality validation (consistency, completeness, coherence)"
      output_format: "L3 quality analysis with issue categorization"
  output_paths:
    l1: ".agent/prompts/{slug}/synthesis/l1_summary.yaml"
    l2: ".agent/prompts/{slug}/synthesis/l2_index.md"
    l3: ".agent/prompts/{slug}/synthesis/l3_details/"
  return_format:
    l1: "Synthesis decision (COMPLETE/ITERATE) with coverage (≤500 tokens)"
    l2_path: ".agent/prompts/{slug}/synthesis/l2_index.md"
    l3_path: ".agent/prompts/{slug}/synthesis/l3_details/"
    requires_l2_read: false
    next_action_hint: "/commit-push-pr or /rsil-plan"

# =============================================================================
# P2: Parallel Agent Configuration
# =============================================================================
parallel_agent_config:
  enabled: true
  complexity_detection: "auto"
  agent_count_by_complexity:
    simple: 1      # Few requirements (1-5)
    moderate: 2    # Medium requirements (6-15)
    complex: 3     # Many requirements (16+)
  synchronization_strategy: "barrier"
  aggregation_strategy: "merge"
  synthesis_areas:
    - requirement_traceability
    - quality_validation
    - gap_analysis

# =============================================================================
# P6: Agent Internal Feedback Loop
# =============================================================================
agent_internal_feedback_loop:
  enabled: true
  max_iterations: 3
  convergence_detection:
    enabled: true
    metrics:
      - "coverage_improvement_rate"
      - "critical_issue_reduction"
      - "gap_closure_velocity"
    threshold: "improvement < 5% over last iteration"
  validation_criteria:
    completeness:
      - "All requirements analyzed"
      - "All deliverables cross-referenced"
      - "Decision rationale clear"
    quality:
      - "Traceability matrix complete"
      - "Quality checks executed"
      - "Gaps identified with specificity"
    internal_consistency:
      - "Coverage calculation accurate"
      - "Decision aligns with threshold"
      - "No contradictions in validation results"

review_gate:
  enabled: true
  phase: "3.5"
  criteria:
    - "requirement_alignment: All requirements addressed in traceability matrix"
    - "design_flow_consistency: Quality validation results are coherent"
    - "gap_detection: Missing/partial requirements clearly identified"
    - "conclusion_clarity: Decision (COMPLETE/ITERATE) is unambiguous"
  auto_approve: false

selective_feedback:
  enabled: true
  threshold: "MEDIUM"
  action_on_low: "log_only"
  action_on_medium_plus: "trigger_review_gate"

iteration_tracking:
  enabled: true
  max_pipeline_iterations: 5
  convergence_detection: true
  history_path: ".agent/prompts/{workload}/synthesis/iteration_history.yaml"

hooks:
  Setup:
    - type: command
      command: "source /home/palantir/.claude/skills/shared/workload-files.sh"
      timeout: 5000
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


# /synthesis - Traceability & Quality Validation (EFL V4.0.0)

> **Version:** 4.0.0 (EFL Pattern)
> **Role:** Sub-Orchestrator for semantic traceability analysis & completion decision
> **Architecture:** Agent Delegation + Semantic Matching + Convergence Detection + Review Gate
> **EFL Features:** P1 Sub-Orchestrator, P3 Semantic Synthesis, P5 Review Gate, P6 Convergence Detection

---



## 1. Purpose

**Synthesis Sub-Orchestrator** (P1) that:
1. **Orchestration**: Delegates analysis to specialized agents (not direct execution)
2. **Phase 3-A (Semantic Matching)**: AI-powered requirement-deliverable matching (P3)
3. **Phase 3-B (Quality Validation)**: Consistency, completeness, coherence checks (P3)
4. **Phase 3.5 Review Gate**: Holistic verification of synthesis results (P5)
5. **Convergence Detection**: Tracks iteration progress and detects convergence (P6)
6. **Decision**: Makes COMPLETE or ITERATE decision with remediation plan

### Enhanced Feedback Loop (EFL) Integration

| Pattern | Implementation |
|---------|----------------|
| **P1: Sub-Orchestrator** | Skill conducts agents, doesn't analyze directly |
| **P3: Semantic Synthesis** | Replaces keyword matching with semantic analysis |
| **P5: Review Gate** | Phase 3.5 holistic verification before decision |
| **P6: Internal Loop + Convergence** | Agent self-validation + iteration tracking |
| **P4: Selective Feedback** | Severity-based threshold (MEDIUM+) |

### Key Changes in V3.0

| Feature | V2.2 (Old) | V3.0 (New) |
|---------|------------|-----------|
| **Matching Algorithm** | Keyword-based (heuristic) | Semantic AI-powered matching |
| **Agent Delegation** | Direct execution | Sub-Orchestrator pattern (P1) |
| **Iteration Tracking** | Manual count | Convergence detection (P6) |
| **Review Gate** | None | Phase 3.5 holistic verification (P5) |
| **Internal Loop** | Single-pass | Agent self-validation (max 3 iterations) |

---



## 2. Invocation

### User Syntax

```bash
# Standard synthesis (80% threshold)
/synthesis

# Strict mode (95% threshold)
/synthesis --strict

# Lenient mode (60% threshold)
/synthesis --lenient

# Dry run (analysis only, no decision)
/synthesis --dry-run
```

### Arguments

- `$0`: Mode flag (`--strict`, `--lenient`, `--dry-run`)

---



## 3. Execution Protocol (EFL Pattern)

### Overview: Sub-Orchestrator Flow

```
/synthesis (Main Skill - Orchestrator)
    │
    ├─▶ Phase 0: Setup & Context Loading
    │   ├─▶ Read requirements from /clarify
    │   ├─▶ Read collection report from /collect
    │   └─▶ Load iteration history (if exists)
    │
    ├─▶ Phase 1: Agent Delegation (P1)
    │   ├─▶ Agent 1 (Explore): Phase 3-A Semantic Matching
    │   │   ├─▶ AI-powered requirement-deliverable matching
    │   │   ├─▶ Internal Loop (P6): Self-validate, max 3 iterations
    │   │   └─▶ Output: L2 traceability matrix with confidence scores
    │   │
    │   └─▶ Agent 2 (Explore): Phase 3-B Quality Validation
    │       ├─▶ Consistency, completeness, coherence checks
    │       ├─▶ Internal Loop (P6): Self-validate, max 3 iterations
    │       └─▶ Output: L3 quality analysis with issue categorization
    │
    ├─▶ Phase 2: Convergence Detection (P6)
    │   ├─▶ Compare with previous iteration (if exists)
    │   ├─▶ Calculate improvement rate
    │   └─▶ Detect convergence or progress stall
    │
    ├─▶ Phase 3: Selective Feedback Check (P4)
    │   └─▶ If MEDIUM+ severity → Trigger iteration
    │
    ├─▶ Phase 3.5: Review Gate (P5)
    │   └─▶ Holistic verification (requirement_alignment, etc.)
    │
    └─▶ Phase 4: Make Decision & Generate Report
        ├─▶ COMPLETE → /commit-push-pr
        └─▶ ITERATE → /rsil-plan or escalate
```

### 3.0 Workload Slug 결정 (표준)

```bash
# Source centralized slug generator
source "${WORKSPACE_ROOT:-.}/.claude/skills/shared/slug-generator.sh"
source "${WORKSPACE_ROOT:-.}/.claude/skills/shared/workload-files.sh"

# Slug 결정 (우선순위)
# 1. --workload 인자 (명시적 지정)
# 2. 활성 workload (get_active_workload)
# 3. 최근 workload 디렉토리
# 4. 새 workload 생성 (기본 동작)

if [[ -n "$WORKLOAD_ARG" ]]; then
    SLUG="$WORKLOAD_ARG"
    echo "🔍 Using specified workload: $SLUG"

elif ACTIVE_WORKLOAD=$(get_active_workload) && [[ -n "$ACTIVE_WORKLOAD" ]]; then
    WORKLOAD_ID="$ACTIVE_WORKLOAD"
    SLUG=$(get_active_workload_slug)
    echo "🔍 Using active workload: $SLUG"

elif RECENT_SLUG=$(ls -t .agent/prompts/ 2>/dev/null | grep -E "^[a-z]" | head -1); [[ -n "$RECENT_SLUG" ]]; then
    SLUG="$RECENT_SLUG"
    echo "🔍 Using recent workload: $SLUG"

else
    # 기본 동작: 새 workload 생성
    TOPIC="synthesis-$(date +%H%M%S)"
    WORKLOAD_ID=$(generate_workload_id "$TOPIC")
    SLUG=$(generate_slug_from_workload "$WORKLOAD_ID")
    init_workload_directory "$WORKLOAD_ID"
    set_active_workload "$WORKLOAD_ID"
    echo "🔍 Created new workload: $SLUG"
fi

# 출력 경로 설정
WORKLOAD_DIR=".agent/prompts/${SLUG}"
OUTPUT_DIR="${WORKLOAD_DIR}/synthesis"
mkdir -p "${OUTPUT_DIR}"
```

### 3.1 Phase 0: Setup & Context Loading

```javascript
async function loadSynthesisContext(workloadSlug) {
  console.log("🔧 Phase 0: Loading synthesis context...")

  // Source validation-feedback-loop.sh
  await Bash({
    command: 'source /home/palantir/.claude/skills/shared/validation-feedback-loop.sh',
    description: 'Load P4/P5/P6 feedback loop functions'
  })

  // 1. Read requirements from /clarify
  console.log("📋 Reading requirements...")
  const requirementsResult = await readRequirements(workloadSlug)

  if (requirementsResult.requirements.length === 0) {
    throw new Error("No requirements found. Run /clarify first.")
  }

  console.log(`  Found ${requirementsResult.totalCount} requirements (P0: ${requirementsResult.p0Count}, P1: ${requirementsResult.p1Count})`)

  // 2. Read collection report from /collect
  console.log("📦 Reading collection report...")
  const collectionResult = await readCollectionReport(workloadSlug)

  if (!collectionResult.source) {
    throw new Error("Collection report not found. Run /collect first.")
  }

  console.log(`  Found ${collectionResult.deliverables.length} deliverables`)

  // 3. Load iteration history (P6 convergence detection)
  console.log("📊 Loading iteration history...")
  const iterationHistory = await loadIterationHistory(workloadSlug)

  if (iterationHistory.iterations.length > 0) {
    console.log(`  Previous iterations: ${iterationHistory.iterations.length}`)
    console.log(`  Last coverage: ${iterationHistory.lastIteration?.coverage || 'N/A'}`)
  }

  return {
    requirements: requirementsResult,
    collection: collectionResult,
    iterationHistory: iterationHistory,
    workloadSlug: workloadSlug
  }
}
```

### 3.1 Phase 1: Agent Delegation (P1 - Sub-Orchestrator Pattern)

```javascript
// P1: Skill as Sub-Orchestrator - Delegates to agents instead of direct analysis
async function delegateSynthesis(context, options) {
  console.log("🎯 P1: Delegating synthesis to specialized agents...")

  // Phase 3-A: Semantic Matching (Requirement-Deliverable Traceability)
  console.log("\n🧠 Phase 3-A: Semantic Matching (AI-powered traceability)")
  const semanticMatchingResult = await delegateToAgent({
    agentType: 'explore',
    task: 'phase3a_semantic_matching',
    prompt: generatePhase3APrompt(context),
    validationCriteria: {
      required_sections: ['traceability_matrix', 'coverage_stats', 'confidence_scores'],
      completeness_checks: ['all_requirements_analyzed', 'all_deliverables_cross_referenced'],
      quality_thresholds: { min_confidence: 0.6 }
    }
  })

  // Phase 3-B: Quality Validation (Consistency, Completeness, Coherence)
  console.log("\n🔍 Phase 3-B: Quality Validation (3C checks)")
  const qualityValidationResult = await delegateToAgent({
    agentType: 'explore',
    task: 'phase3b_quality_validation',
    prompt: generatePhase3BPrompt(context, semanticMatchingResult),
    validationCriteria: {
      required_sections: ['consistency_check', 'completeness_check', 'coherence_check'],
      completeness_checks: ['all_3c_checks_executed', 'critical_issues_identified'],
      quality_thresholds: { max_critical_issues: 0 }
    }
  })

  return {
    semanticMatching: semanticMatchingResult,
    qualityValidation: qualityValidationResult
  }
}

// Delegate to agent with P6 internal feedback loop
async function delegateToAgent(config) {
  const { agentType, task, prompt, validationCriteria } = config

  console.log(`  🤖 Spawning ${agentType} agent for ${task}...`)

  // P6: Generate agent prompt with internal loop instructions
  const agentPromptWithLoop = await Bash({
    command: `source /home/palantir/.claude/skills/shared/validation-feedback-loop.sh && \
              generate_agent_prompt_with_internal_loop "${agentType}" '${JSON.stringify(validationCriteria)}'`,
    description: 'Generate agent prompt with P6 internal loop'
  })

  // Combine task prompt with internal loop instructions
  const fullPrompt = `${agentPromptWithLoop}\n\n---\n\n${prompt}`

  // Launch agent via Task tool
  const agentResult = await Task({
    subagent_type: agentType,
    description: `${task} with internal loop`,
    prompt: fullPrompt,
    model: 'opus'  // Use opus for high-quality semantic analysis
  })

  // Extract internal loop metadata
  const loopMetadata = extractInternalLoopMetadata(agentResult)

  console.log(`  ✅ Agent completed: ${loopMetadata.iterations_used} iterations, status: ${loopMetadata.final_validation_status}`)

  return {
    task: task,
    result: agentResult,
    internalLoop: loopMetadata
  }
}

// Generate Phase 3-A prompt (Semantic Matching - AI-powered)
function generatePhase3APrompt(context) {
  const { requirements, collection } = context

  return `# Phase 3-A: Semantic Requirement-Deliverable Matching

**Objective:** Build traceability matrix using AI-powered semantic analysis (not keyword matching).

## Requirements to Analyze (${requirements.totalCount} total)

${requirements.requirements.map((r, i) => `
### ${i + 1}. ${r.id} (${r.priority})
**Description:** ${r.description}
**Category:** ${r.category}
`).join('\n')}

## Deliverables to Match (${collection.deliverables.length} total)

${collection.deliverables.map((d, i) => `
${i + 1}. **File:** \`${d.item}\`
   **Task:** ${d.taskSubject || 'N/A'}
   **Owner:** ${d.owner || 'N/A'}
`).join('\n')}

## Task Instructions

### 1. Semantic Analysis (NOT Keyword Matching)

For each requirement:
- Understand the **semantic intent** (what the requirement actually means)
- Analyze deliverable content for **conceptual match** (not just keyword overlap)
- Consider:
  - Does the deliverable address the core need of the requirement?
  - Are there functional/semantic relationships beyond lexical similarity?
  - Context clues: file paths, task descriptions, code patterns

**Example:**
- Requirement: "User authentication system"
- Deliverable: \`auth/jwt-handler.py\` (HIGH confidence - semantic match)
- Deliverable: \`utils/password-hash.py\` (MEDIUM confidence - supporting match)
- Deliverable: \`ui/login-form.tsx\` (MEDIUM confidence - UI component)

### 2. Confidence Scoring

For each match, assign confidence score:
- **0.9-1.0**: Strong semantic match (directly addresses requirement)
- **0.7-0.89**: Good match (addresses requirement with minor gaps)
- **0.5-0.69**: Moderate match (partially addresses requirement)
- **0.3-0.49**: Weak match (tangentially related)
- **0.0-0.29**: No match (unrelated)

### 3. Coverage Calculation

- **Covered (100%)**: At least one deliverable with confidence >= 0.7
- **Partial (50%)**: At least one deliverable with confidence >= 0.4 and < 0.7
- **Missing (0%)**: No deliverables with confidence >= 0.4

## Output Format (L2 Traceability Matrix)

\`\`\`yaml
l2_semantic_matching:
  traceability_matrix:
    - requirement_id: "REQ-001"
      requirement: "User authentication system"
      priority: "P0"
      status: "covered"  # covered | partial | missing
      coverage: 100
      matches:
        - deliverable: "auth/jwt-handler.py"
          confidence: 0.95
          rationale: "Directly implements JWT authentication logic"
        - deliverable: "utils/password-hash.py"
          confidence: 0.75
          rationale: "Provides password hashing for auth system"
      notes: "Strong coverage with multiple supporting files"

    # ... (one entry per requirement)

  coverage_stats:
    total_requirements: ${requirements.totalCount}
    covered: 0  # Count of covered requirements
    partial: 0  # Count of partial requirements
    missing: 0  # Count of missing requirements
    overall_coverage: 0.0  # Percentage (0-100)

  confidence_scores:
    average_confidence: 0.0  # Average confidence across all matches
    high_confidence_matches: 0  # Count of matches with confidence >= 0.7
    low_confidence_matches: 0  # Count of matches with confidence < 0.5
\`\`\`

## Important Notes

- **Do NOT use simple keyword matching** - This is semantic analysis
- Analyze file content if needed (use Read tool for key files)
- Consider architectural patterns (e.g., MVC, layers)
- Cross-reference task descriptions with requirement intent
- Be conservative with confidence scores (better to underestimate than overestimate)
`
}

// Generate Phase 3-B prompt (Quality Validation - 3C Checks)
function generatePhase3BPrompt(context, semanticMatchingResult) {
  const traceabilityMatrix = parseAgentResult(semanticMatchingResult.result, 'l2_semantic_matching')

  return `# Phase 3-B: Quality Validation (Consistency, Completeness, Coherence)

**Objective:** Validate synthesis quality using 3C checks.

## Context from Phase 3-A (Semantic Matching)

**Traceability Matrix:**
- Total Requirements: ${traceabilityMatrix.coverage_stats?.total_requirements || context.requirements.totalCount}
- Covered: ${traceabilityMatrix.coverage_stats?.covered || 0}
- Partial: ${traceabilityMatrix.coverage_stats?.partial || 0}
- Missing: ${traceabilityMatrix.coverage_stats?.missing || 0}
- Overall Coverage: ${traceabilityMatrix.coverage_stats?.overall_coverage || 0}%

## Quality Validation Tasks

### 1. Consistency Check

**Goal:** Detect conflicting or duplicate implementations.

**Checks:**
- Duplicate deliverables (same file modified by multiple tasks)
- Conflicting patterns (e.g., two different auth implementations)
- Inconsistent naming conventions
- Architectural mismatches

**For each issue found:**
\`\`\`yaml
- type: "duplicate" | "conflict" | "inconsistency"
  description: "Clear description of the issue"
  severity: "CRITICAL" | "HIGH" | "MEDIUM" | "LOW"
  affected_items: ["file1.py", "file2.py"]
  recommendation: "How to resolve"
\`\`\`

### 2. Completeness Check

**Goal:** Ensure all critical requirements are addressed.

**Checks:**
- All P0 requirements must be covered (not partial/missing)
- No missing test files (look for .test., .spec., test_ patterns)
- Documentation exists (README, API docs, etc.)
- Error handling present
- Security requirements addressed

**For each issue found:**
\`\`\`yaml
- type: "p0_missing" | "no_tests" | "no_docs" | "missing_requirement"
  description: "What is missing"
  severity: "CRITICAL" | "HIGH" | "MEDIUM" | "LOW"
  requirement_id: "REQ-001"  # If applicable
  recommendation: "What needs to be added"
\`\`\`

### 3. Coherence Check

**Goal:** Verify components work together cohesively.

**Checks:**
- Orphan deliverables (deliverables not mapping to any requirement)
- Integration gaps (components that don't connect)
- Missing dependencies (required imports/modules not found)
- Logical flow issues

**For each issue found:**
\`\`\`yaml
- type: "orphan" | "integration_gap" | "missing_dependency"
  description: "What breaks coherence"
  severity: "CRITICAL" | "HIGH" | "MEDIUM" | "LOW"
  affected_items: ["item1", "item2"]
  recommendation: "How to improve coherence"
\`\`\`

## Deliverables to Validate

${context.collection.deliverables.map((d, i) => `${i + 1}. \`${d.item}\` (Task: ${d.taskSubject || 'N/A'})`).join('\n')}

## Output Format (L3 Quality Analysis)

\`\`\`yaml
l3_quality_validation:
  consistency_check:
    passed: true | false
    issues: [...]  # List of issues found

  completeness_check:
    passed: true | false
    issues: [...]  # List of issues found
    p0_missing_count: 0  # Count of P0 requirements not covered

  coherence_check:
    passed: true | false
    issues: [...]  # List of issues found
    orphan_count: 0  # Count of orphan deliverables

  overall_validation:
    passed: true | false  # True if no CRITICAL issues
    critical_issue_count: 0
    high_issue_count: 0
    medium_issue_count: 0
    low_issue_count: 0
    total_issue_count: 0
\`\`\`

## Important Notes

- Use Read tool to inspect actual file content when needed
- Be thorough - check all aspects of 3C
- Severity levels guide:
  - CRITICAL: Blocks release (P0 missing, major conflicts)
  - HIGH: Should fix before release (security, missing tests)
  - MEDIUM: Fix in next iteration (minor inconsistencies)
  - LOW: Nice to have (documentation improvements)
`
}

// Legacy: Read Requirements (V2.2 - kept for fallback)
function readRequirements(workloadSlug) {
  // ... (existing implementation preserved for fallback)
  // Find latest clarify log in workload or global paths
  const clarifyPaths = [
    workloadSlug ? `.agent/prompts/${workloadSlug}/clarify.yaml` : null,
    '.agent/plans/clarify_*.md'
  ].filter(Boolean)

  let clarifyLogs = []
  for (const pattern of clarifyPaths) {
    clarifyLogs.push(...Glob(pattern))
  }

  if (clarifyLogs.length === 0) {
    console.log("⚠️  No /clarify logs found")
    return { requirements: [], source: null, totalCount: 0, p0Count: 0, p1Count: 0 }
  }

  // Sort by date (newest first)
  clarifyLogs.sort((a, b) => {
    let dateA = extractDateFromFilename(a)
    let dateB = extractDateFromFilename(b)
    return dateB - dateA
  })

  latestLog = clarifyLogs[0]
  console.log(`📋 Reading requirements from: ${latestLog}`)

  // Parse requirements
  content = Read(latestLog)
  requirements = parseRequirements(content)

  return {
    requirements: requirements,
    source: latestLog,
    totalCount: requirements.length,
    p0Count: requirements.filter(r => r.priority === "P0").length,
    p1Count: requirements.filter(r => r.priority === "P1").length
  }
}
```

### 3.2 Phase 2: Convergence Detection (P6)

```javascript
// P6: Track iteration progress and detect convergence
async function detectConvergence(currentIteration, iterationHistory, options) {
  console.log("\n📈 P6: Convergence Detection...")

  if (iterationHistory.iterations.length === 0) {
    console.log("  First iteration - no convergence data")
    return {
      converged: false,
      reason: "first_iteration",
      improvementRate: null,
      recommendation: "continue"
    }
  }

  const lastIteration = iterationHistory.lastIteration
  const currentCoverage = currentIteration.coverage
  const lastCoverage = lastIteration.coverage

  // Calculate improvement rate
  const improvementRate = currentCoverage - lastCoverage
  const improvementPercent = ((improvementRate / (100 - lastCoverage)) * 100).toFixed(1)

  console.log(`  Last coverage: ${lastCoverage}%`)
  console.log(`  Current coverage: ${currentCoverage}%`)
  console.log(`  Improvement: ${improvementRate > 0 ? '+' : ''}${improvementRate}% (${improvementPercent}% of gap)`)

  // Convergence detection criteria
  let converged = false
  let reason = ""
  let recommendation = "continue"

  // Criterion 1: Improvement rate < 5% (stalled progress)
  if (Math.abs(improvementRate) < 5) {
    converged = true
    reason = "improvement_rate_below_threshold"
    recommendation = improvementRate >= 0 ? "escalate_to_manual" : "investigate_regression"
    console.log(`  ⚠️  Convergence detected: Improvement < 5%`)
  }

  // Criterion 2: Critical issues not decreasing
  const currentCritical = currentIteration.criticalIssueCount
  const lastCritical = lastIteration.criticalIssueCount
  const criticalReduction = lastCritical - currentCritical

  console.log(`  Critical issues: ${lastCritical} → ${currentCritical} (${criticalReduction >= 0 ? '-' : '+'}${Math.abs(criticalReduction)})`)

  if (criticalReduction <= 0 && currentCritical > 0) {
    converged = true
    reason = "critical_issues_not_reducing"
    recommendation = "escalate_to_manual"
    console.log(`  ⚠️  Convergence detected: Critical issues not reducing`)
  }

  // Criterion 3: Max iterations reached
  if (iterationHistory.iterations.length >= options.maxIterations) {
    converged = true
    reason = "max_iterations_reached"
    recommendation = "escalate_to_manual"
    console.log(`  ⚠️  Max iterations (${options.maxIterations}) reached`)
  }

  // Criterion 4: Coverage plateau (3 consecutive iterations with <2% improvement)
  if (iterationHistory.iterations.length >= 3) {
    const last3Improvements = iterationHistory.iterations.slice(-3).map((it, i, arr) =>
      i > 0 ? it.coverage - arr[i - 1].coverage : 0
    ).filter(imp => imp !== 0)

    if (last3Improvements.every(imp => imp < 2)) {
      converged = true
      reason = "coverage_plateau"
      recommendation = "escalate_to_manual"
      console.log(`  ⚠️  Coverage plateau detected (< 2% improvement over 3 iterations)`)
    }
  }

  return {
    converged: converged,
    reason: reason,
    improvementRate: improvementRate,
    improvementPercent: improvementPercent,
    criticalReduction: criticalReduction,
    recommendation: recommendation,
    iterationCount: iterationHistory.iterations.length + 1
  }
}

// Load iteration history for convergence detection
async function loadIterationHistory(workloadSlug) {
  const historyPath = workloadSlug
    ? `.agent/prompts/${workloadSlug}/synthesis/iteration_history.yaml`
    : `.agent/outputs/synthesis/iteration_history.yaml`

  if (!fileExists(historyPath)) {
    return {
      iterations: [],
      lastIteration: null
    }
  }

  const content = Read(historyPath)
  const iterations = parseIterationHistory(content)

  return {
    iterations: iterations,
    lastIteration: iterations.length > 0 ? iterations[iterations.length - 1] : null
  }
}

// Save current iteration to history
async function saveIterationHistory(workloadSlug, currentIteration) {
  const historyPath = workloadSlug
    ? `.agent/prompts/${workloadSlug}/synthesis/iteration_history.yaml`
    : `.agent/outputs/synthesis/iteration_history.yaml`

  const historyDir = historyPath.substring(0, historyPath.lastIndexOf('/'))
  await Bash({ command: `mkdir -p ${historyDir}`, description: 'Create history directory' })

  // Load existing history
  let iterations = []
  if (fileExists(historyPath)) {
    const content = Read(historyPath)
    iterations = parseIterationHistory(content)
  }

  // Append current iteration
  iterations.push(currentIteration)

  // Generate YAML content
  const historyContent = `# Synthesis Iteration History
# Workload: ${workloadSlug || 'global'}

iterations:
${iterations.map((it, i) => `
  - iteration: ${i + 1}
    timestamp: "${it.timestamp}"
    coverage: ${it.coverage}
    decision: "${it.decision}"
    critical_issue_count: ${it.criticalIssueCount}
    threshold: ${it.threshold}
    improvement_from_last: ${i > 0 ? (it.coverage - iterations[i - 1].coverage).toFixed(1) : 0}
`).join('')}

metadata:
  total_iterations: ${iterations.length}
  converged: ${currentIteration.converged || false}
  last_updated: "${currentIteration.timestamp}"
`

  Write({ file_path: historyPath, content: historyContent })
  console.log(`  💾 Iteration history saved: ${historyPath}`)
}
```

### 3.3 Phase 2 (Legacy): Read Collection Report

```javascript
function readCollectionReport(workloadSlug) {
  // Workload-scoped path (primary) with global fallback
  const primaryPath = workloadSlug
    ? `.agent/prompts/${workloadSlug}/collection_report.md`
    : null
  const fallbackPath = ".agent/outputs/collection_report.md"

  let reportPath = primaryPath && fileExists(primaryPath) ? primaryPath : fallbackPath

  if (!fileExists(reportPath)) {
    console.log("⚠️  Collection report not found. Run /collect first.")
    return { deliverables: [], taskSummaries: [], source: null }
  }

  console.log(`📦 Reading collection report: ${reportPath}`)

  content = Read(reportPath)

  // 1. Parse task summaries
  taskSummaries = parseTaskSummaries(content)

  // 2. Extract all deliverables
  deliverables = []
  for (task of taskSummaries) {
    for (d of task.deliverables) {
      deliverables.push({
        item: d,
        taskId: task.taskId,
        taskSubject: task.subject,
        owner: task.owner
      })
    }
  }

  // 3. Parse completion stats
  stats = parseCompletionStats(content)

  return {
    deliverables: deliverables,
    taskSummaries: taskSummaries,
    source: reportPath,
    stats: stats
  }
}
```

### 3.3 Phase 3: Build Traceability Matrix

```javascript
function buildTraceabilityMatrix(requirements, deliverables) {
  matrix = []

  for (req of requirements) {
    // Find matching deliverables
    matches = findMatchingDeliverables(req, deliverables)

    let status = "missing"
    let coverage = 0

    if (matches.full.length > 0) {
      status = "covered"
      coverage = 100
    } else if (matches.partial.length > 0) {
      status = "partial"
      coverage = 50
    }

    matrix.push({
      requirementId: req.id,
      requirement: req.description,
      priority: req.priority,
      status: status,
      deliverables: matches.full.concat(matches.partial),
      coverage: coverage,
      notes: generateNotes(status, matches)
    })
  }

  // Calculate overall coverage
  totalCoverage = matrix.reduce((sum, m) => sum + m.coverage, 0) / matrix.length
  coveredCount = matrix.filter(m => m.status === "covered").length
  partialCount = matrix.filter(m => m.status === "partial").length
  missingCount = matrix.filter(m => m.status === "missing").length

  return {
    matrix: matrix,
    stats: {
      totalRequirements: requirements.length,
      covered: coveredCount,
      partial: partialCount,
      missing: missingCount,
      overallCoverage: totalCoverage.toFixed(1) + "%"
    }
  }
}
```

### 3.4 Phase 4: Validate Quality

```javascript
function validateQuality(matrix, deliverables) {
  checks = {
    consistency: { passed: true, issues: [] },
    completeness: { passed: true, issues: [] },
    coherence: { passed: true, issues: [] }
  }

  // === Consistency Check ===
  // Look for conflicting implementations

  // Check for duplicate deliverables (same file, different tasks)
  deliverableFiles = {}
  for (d of deliverables) {
    if (deliverableFiles[d.item]) {
      checks.consistency.issues.push({
        type: "duplicate",
        description: `File "${d.item}" modified by multiple tasks`,
        severity: "warning"
      })
    }
    deliverableFiles[d.item] = d.taskId
  }

  // Check for conflicting patterns (heuristic)
  if (checks.consistency.issues.filter(i => i.severity === "critical").length > 0) {
    checks.consistency.passed = false
  }

  // === Completeness Check ===
  // All P0 requirements should be covered

  p0Missing = matrix.matrix.filter(m =>
    m.priority === "P0" && m.status === "missing"
  )

  if (p0Missing.length > 0) {
    checks.completeness.passed = false
    for (m of p0Missing) {
      checks.completeness.issues.push({
        type: "p0_missing",
        description: `P0 requirement not addressed: ${m.requirement}`,
        requirementId: m.requirementId,
        severity: "critical"
      })
    }
  }

  // Check for missing tests (heuristic - look for test files)
  hasTests = deliverables.some(d =>
    d.item.includes("test") || d.item.includes(".spec.") || d.item.includes(".test.")
  )

  if (!hasTests) {
    checks.completeness.issues.push({
      type: "no_tests",
      description: "No test files found in deliverables",
      severity: "warning"
    })
  }

  // === Coherence Check ===
  // Components should work together

  // Check for orphan deliverables (deliverables that don't map to any requirement)
  orphans = findOrphanDeliverables(deliverables, matrix.matrix)
  if (orphans.length > 0) {
    for (o of orphans) {
      checks.coherence.issues.push({
        type: "orphan",
        description: `Deliverable "${o.item}" doesn't map to any requirement`,
        severity: "info"
      })
    }
  }

  // Calculate overall validation result
  criticalIssues = [
    ...checks.consistency.issues,
    ...checks.completeness.issues,
    ...checks.coherence.issues
  ].filter(i => i.severity === "critical")

  return {
    consistency: checks.consistency,
    completeness: checks.completeness,
    coherence: checks.coherence,
    overallPassed: criticalIssues.length === 0,
    criticalIssueCount: criticalIssues.length,
    warningCount: [
      ...checks.consistency.issues,
      ...checks.completeness.issues,
      ...checks.coherence.issues
    ].filter(i => i.severity === "warning").length
  }
}
```

### 3.5 Phase 5: Make Decision

```javascript
function makeDecision(matrixResult, validationResult, options) {
  coverage = parseFloat(matrixResult.stats.overallCoverage)

  // Determine threshold based on mode
  let threshold = 80  // default
  if (options.mode === "strict") {
    threshold = 95
  } else if (options.mode === "lenient") {
    threshold = 60
  }

  // Decision logic
  let decision, rationale, nextAction, gaps

  if (coverage >= threshold && validationResult.criticalIssueCount === 0 && validationResult.overallPassed) {
    decision = "COMPLETE"
    rationale = [
      `Coverage: ${matrixResult.stats.overallCoverage} (above ${threshold}% threshold)`,
      `Critical Issues: 0`,
      `Quality Validation: PASSED`
    ]
    nextAction = "/commit-push-pr"
    gaps = []
  }
  else if (coverage >= (threshold - 20) && validationResult.criticalIssueCount === 0) {
    decision = "COMPLETE_WITH_WARNINGS"
    rationale = [
      `Coverage: ${matrixResult.stats.overallCoverage} (slightly below ${threshold}% threshold)`,
      `Critical Issues: 0`,
      `Quality Validation: PASSED with warnings`,
      `Warnings: ${validationResult.warningCount}`
    ]
    nextAction = "/commit-push-pr --with-warnings"
    gaps = matrixResult.matrix.filter(m => m.status !== "covered")
  }
  else {
    decision = "ITERATE"

    // Gather gaps
    gaps = matrixResult.matrix.filter(m => m.status === "missing" || m.status === "partial")

    rationale = [
      `Coverage: ${matrixResult.stats.overallCoverage} (below ${threshold}% threshold)`,
      `Critical Issues: ${validationResult.criticalIssueCount}`,
      `Quality Validation: ${validationResult.overallPassed ? 'PASSED' : 'FAILED'}`,
      `Missing Requirements: ${matrixResult.stats.missing}`,
      `Partial Requirements: ${matrixResult.stats.partial}`
    ]

    // Generate RSIL prompt for automated gap analysis
    // Track iteration count for progressive refinement
    let iteration_count = (options.iteration || 0) + 1
    nextAction = `/rsil-plan --iteration ${iteration_count}`
  }

  return {
    decision: decision,
    threshold: threshold,
    coverage: coverage,
    rationale: rationale,
    nextAction: nextAction,
    gaps: gaps
  }
}
```

### 3.6 Phase 6: Generate Synthesis Report

```javascript
function generateSynthesisReport(requirementsResult, collectionResult, matrixResult, validationResult, decisionResult, options) {
  let now = new Date().toISOString()

  let reportContent = `# Synthesis Report

> Generated: ${now}
> Mode: ${options.mode || "standard"}
> Threshold: ${decisionResult.threshold}%

---



## Summary

| Metric | Value |
|--------|-------|
| Requirements Source | ${requirementsResult.source || 'N/A'} |
| Collection Source | ${collectionResult.source || 'N/A'} |
| Total Requirements | ${requirementsResult.totalCount} |
| P0 Requirements | ${requirementsResult.p0Count} |
| P1 Requirements | ${requirementsResult.p1Count} |
| Total Deliverables | ${collectionResult.deliverables.length} |
| **Coverage** | **${matrixResult.stats.overallCoverage}** |

---



## Traceability Matrix

| Requirement | Priority | Status | Deliverable(s) | Notes |
|-------------|----------|--------|----------------|-------|
${matrixResult.matrix.map(m => {
  let statusIcon = m.status === "covered" ? "✅" : m.status === "partial" ? "⚠️" : "❌"
  let deliverablesList = m.deliverables.length > 0
    ? m.deliverables.map(d => d.item).join(", ")
    : "-"
  return `| ${m.requirementId}: ${m.requirement.substring(0, 40)}... | ${m.priority} | ${statusIcon} ${m.status} | ${deliverablesList} | ${m.notes || '-'} |`
}).join('\n')}

**Coverage Summary:**
- ✅ Covered: ${matrixResult.stats.covered}
- ⚠️ Partial: ${matrixResult.stats.partial}
- ❌ Missing: ${matrixResult.stats.missing}

---



## Quality Validation

### Consistency Check ${validationResult.consistency.passed ? '✅' : '❌'}

${validationResult.consistency.issues.length > 0 ?
  validationResult.consistency.issues.map(i => `- [${i.severity}] ${i.description}`).join('\n')
  : '- No issues detected'}

### Completeness Check ${validationResult.completeness.passed ? '✅' : '❌'}

${validationResult.completeness.issues.length > 0 ?
  validationResult.completeness.issues.map(i => `- [${i.severity}] ${i.description}`).join('\n')
  : '- All requirements addressed'}

### Coherence Check ${validationResult.coherence.passed ? '✅' : '❌'}

${validationResult.coherence.issues.length > 0 ?
  validationResult.coherence.issues.map(i => `- [${i.severity}] ${i.description}`).join('\n')
  : '- Components integrate properly'}

**Overall Validation:** ${validationResult.overallPassed ? '✅ PASSED' : '❌ FAILED'}
- Critical Issues: ${validationResult.criticalIssueCount}
- Warnings: ${validationResult.warningCount}

---



## Decision

${getDecisionBlock(decisionResult)}

---



## Synthesis Metadata

\`\`\`yaml
synthesizedAt: "${now}"
mode: "${options.mode || 'standard'}"
threshold: ${decisionResult.threshold}
coverage: ${decisionResult.coverage}
decision: "${decisionResult.decision}"
criticalIssues: ${validationResult.criticalIssueCount}
\`\`\`
`

  // Workload-scoped output directory
  outputDir = workloadSlug
    ? `.agent/prompts/${workloadSlug}/synthesis`
    : ".agent/outputs/synthesis"  // Fallback (deprecated)
  Bash(`mkdir -p ${outputDir}`)

  // Write report
  reportPath = `${outputDir}/synthesis_report.md`
  Write({
    file_path: reportPath,
    content: reportContent
  })

  console.log(`✅ Synthesis report generated: ${reportPath}`)

  return {
    path: reportPath,
    decision: decisionResult.decision
  }
}
```

### 3.7 Helper: getDecisionBlock

```javascript
function getDecisionBlock(decisionResult) {
  if (decisionResult.decision === "COMPLETE") {
    return `**Status: COMPLETE** ✅

**Rationale:**
${decisionResult.rationale.map(r => `- ${r}`).join('\n')}

**Next Action:**
\`\`\`bash
${decisionResult.nextAction}
\`\`\``
  }

  if (decisionResult.decision === "COMPLETE_WITH_WARNINGS") {
    return `**Status: COMPLETE WITH WARNINGS** ⚠️

**Rationale:**
${decisionResult.rationale.map(r => `- ${r}`).join('\n')}

**Gaps (non-critical):**
${decisionResult.gaps.map(g => `- ${g.requirementId}: ${g.requirement}`).join('\n')}

**Next Action:**
\`\`\`bash
${decisionResult.nextAction}
\`\`\`

Consider addressing warnings in a follow-up iteration.`
  }

  // ITERATE
  let iteration_count = decisionResult.iteration || 1
  return `**Status: ITERATE** 🔄

**Rationale:**
${decisionResult.rationale.map(r => `- ${r}`).join('\n')}

**Gaps to Address:**
${decisionResult.gaps.map((g, i) => `${i + 1}. ${g.requirementId}: ${g.requirement}`).join('\n')}

**Next Action:**
\`\`\`bash
/rsil-plan --iteration ${iteration_count}
\`\`\`

RSIL will perform code-level gap analysis and create remediation plan.
For manual iteration, use: /clarify "Address gaps: ..."`
}
```

### 3.8 Helper Functions

```javascript
function parseRequirements(content) {
  requirements = []
  lines = content.split('\n')

  let reqId = 1
  for (line of lines) {
    // Look for requirement patterns
    // Pattern 1: "- REQ-001: Description"
    // Pattern 2: "- [P0] Description"
    // Pattern 3: "## Requirement: Description"

    if (line.match(/^\s*[-*]\s*(REQ-\d+|R\d+):/i)) {
      match = line.match(/^\s*[-*]\s*(REQ-\d+|R\d+):\s*(.+)/i)
      if (match) {
        requirements.push({
          id: match[1].toUpperCase(),
          description: match[2].trim(),
          priority: extractPriority(line) || "P1",
          category: extractCategory(match[2])
        })
      }
    }
    else if (line.match(/^\s*[-*]\s*\[(P\d)\]/i)) {
      match = line.match(/^\s*[-*]\s*\[(P\d)\]\s*(.+)/i)
      if (match) {
        requirements.push({
          id: `REQ-${String(reqId++).padStart(3, '0')}`,
          description: match[2].trim(),
          priority: match[1].toUpperCase(),
          category: extractCategory(match[2])
        })
      }
    }
    else if (line.match(/^##\s*(Requirement|요구사항):\s*/i)) {
      match = line.match(/^##\s*(Requirement|요구사항):\s*(.+)/i)
      if (match) {
        requirements.push({
          id: `REQ-${String(reqId++).padStart(3, '0')}`,
          description: match[2].trim(),
          priority: "P1",
          category: extractCategory(match[2])
        })
      }
    }
  }

  return requirements
}

function findMatchingDeliverables(requirement, deliverables) {
  full = []
  partial = []

  // Keyword matching (simple heuristic)
  keywords = requirement.description.toLowerCase().split(/\s+/).filter(w => w.length > 3)

  for (d of deliverables) {
    matchScore = 0
    itemLower = d.item.toLowerCase()
    taskLower = (d.taskSubject || "").toLowerCase()

    for (kw of keywords) {
      if (itemLower.includes(kw) || taskLower.includes(kw)) {
        matchScore++
      }
    }

    // Threshold for matching
    matchPercentage = (matchScore / keywords.length) * 100

    if (matchPercentage >= 50) {
      full.push(d)
    } else if (matchPercentage >= 25) {
      partial.push(d)
    }
  }

  return { full, partial }
}

function findOrphanDeliverables(deliverables, matrix) {
  orphans = []

  for (d of deliverables) {
    isOrphan = true

    for (m of matrix) {
      if (m.deliverables.some(md => md.item === d.item)) {
        isOrphan = false
        break
      }
    }

    if (isOrphan) {
      orphans.push(d)
    }
  }

  return orphans
}

function extractPriority(text) {
  match = text.match(/\b(P0|P1|P2|P3)\b/i)
  return match ? match[1].toUpperCase() : null
}

function extractCategory(text) {
  categories = ["feature", "security", "performance", "ux", "infrastructure", "testing"]
  textLower = text.toLowerCase()

  for (cat of categories) {
    if (textLower.includes(cat)) return cat
  }
  return "feature"
}
```

---



## 4. Main Execution Flow (EFL Pattern)

```javascript
async function synthesis(args) {
  console.log("🔍 Starting synthesis with EFL Pattern (v3.0.0)...\n")

  // Parse arguments
  let options = {
    mode: args.includes('--strict') ? 'strict' : args.includes('--lenient') ? 'lenient' : 'standard',
    dryRun: args.includes('--dry-run'),
    maxIterations: 5,
    workloadSlug: extractWorkloadSlug(args)
  }

  console.log(`Mode: ${options.mode} | Dry Run: ${options.dryRun} | Max Iterations: ${options.maxIterations}`)

  try {
    // Phase 0: Setup & Context Loading
    console.log("\n🔧 Phase 0: Loading synthesis context...")
    const context = await loadSynthesisContext(options.workloadSlug)

    // Phase 1: Agent Delegation (P1)
    let aggregated
    let usingAgentDelegation = true

    try {
      console.log("\n🎯 Phase 1: Agent Delegation (P1 - Sub-Orchestrator)")
      const delegationResult = await delegateSynthesis(context, options)

      // Aggregate Phase 3-A (Semantic Matching) + Phase 3-B (Quality Validation)
      console.log("\n📦 Aggregating L2/L3 results...")
      aggregated = await aggregateSemanticAndQuality(delegationResult)

    } catch (delegationError) {
      console.log(`⚠️  Agent delegation failed: ${delegationError.message}`)
      console.log(`   Falling back to keyword matching (V2.2)...\n`)

      usingAgentDelegation = false

      // Fallback to V2.2 keyword matching
      const matrixResult = buildTraceabilityMatrix(
        context.requirements.requirements,
        context.collection.deliverables
      )
      const validationResult = validateQuality(matrixResult, context.collection.deliverables)

      aggregated = {
        matrix: matrixResult,
        validation: validationResult,
        internalLoopMetadata: { totalIterations: 0 }
      }
    }

    // Phase 2: Convergence Detection (P6)
    let convergenceResult
    if (usingAgentDelegation && context.iterationHistory.iterations.length > 0) {
      const currentIteration = {
        timestamp: new Date().toISOString(),
        coverage: parseFloat(aggregated.matrix.stats.overallCoverage),
        criticalIssueCount: aggregated.validation.criticalIssueCount,
        threshold: getThreshold(options.mode),
        decision: null  // Will be set after decision phase
      }

      convergenceResult = await detectConvergence(currentIteration, context.iterationHistory, options)
    } else {
      convergenceResult = {
        converged: false,
        reason: "first_iteration_or_fallback",
        recommendation: "continue"
      }
    }

    // Phase 3: Selective Feedback Check (P4)
    if (usingAgentDelegation) {
      const feedbackCheck = await checkSelectiveFeedback(aggregated)

      if (feedbackCheck.needs_feedback) {
        console.log(`\n⚠️  P4: Feedback required (${feedbackCheck.severity})`)
      }
    }

    // Phase 3.5: Review Gate (P5)
    let reviewGateResult
    if (options.skipReviewGate) {
      reviewGateResult = {
        approved: true,
        criteriaChecks: { skipped: true },
        review: { warnings: [], errors: [] }
      }
    } else {
      reviewGateResult = await executeReviewGate(aggregated, convergenceResult)
    }

    // Phase 4: Make Decision
    console.log("\n⚖️  Phase 4: Making decision...")
    const decisionResult = makeDecisionWithConvergence(
      aggregated.matrix,
      aggregated.validation,
      convergenceResult,
      options
    )

    // Save iteration history (P6)
    if (usingAgentDelegation && !options.dryRun) {
      const currentIteration = {
        timestamp: new Date().toISOString(),
        coverage: parseFloat(aggregated.matrix.stats.overallCoverage),
        criticalIssueCount: aggregated.validation.criticalIssueCount,
        threshold: decisionResult.threshold,
        decision: decisionResult.decision,
        converged: convergenceResult.converged
      }

      await saveIterationHistory(options.workloadSlug, currentIteration)
    }

    // Phase 5: Generate L1/L2 Report
    let reportResult
    if (!options.dryRun) {
      console.log("\n📝 Phase 5: Generating L1/L2 synthesis report...")
      reportResult = await generateSynthesisReportV3(
        context,
        aggregated,
        reviewGateResult,
        decisionResult,
        convergenceResult,
        options
      )
    }

    // Display summary
    displaySynthesisSummary(aggregated, decisionResult, convergenceResult, reviewGateResult, reportResult, options, usingAgentDelegation)

    // Return L1 summary
    return {
      status: 'success',
      l1Summary: reportResult?.l1Summary,
      l2ReportPath: reportResult?.l2ReportPath,
      decision: decisionResult.decision,
      coverage: aggregated.matrix.stats.overallCoverage,
      reviewApproved: reviewGateResult.approved,
      converged: convergenceResult.converged,
      eflMetadata: {
        version: '3.0.0',
        agentDelegation: usingAgentDelegation,
        internalIterations: aggregated.internalLoopMetadata?.totalIterations || 0,
        reviewGate: reviewGateResult.approved,
        convergenceDetection: convergenceResult.converged
      }
    }

  } catch (error) {
    console.error(`\n❌ Synthesis failed: ${error.message}`)
    console.error(`   Stack: ${error.stack}`)

    return {
      status: 'error',
      error: error.message,
      stack: error.stack
    }
  }
}

function displaySynthesisSummary(aggregated, decisionResult, convergenceResult, reviewGateResult, reportResult, options, usingAgentDelegation) {
  let decisionIcon = decisionResult.decision === "COMPLETE" ? "✅" :
                     decisionResult.decision === "COMPLETE_WITH_WARNINGS" ? "⚠️" : "🔄"

  console.log(`
╔════════════════════════════════════════════════════════════════╗
║                   Synthesis Complete (v3.0.0)                  ║
╚════════════════════════════════════════════════════════════════╝

📊 Traceability Matrix:
   Coverage: ${aggregated.matrix.stats.overallCoverage}
   Threshold: ${decisionResult.threshold}%
   Covered: ${aggregated.matrix.stats.covered}
   Partial: ${aggregated.matrix.stats.partial}
   Missing: ${aggregated.matrix.stats.missing}

🔍 Quality Validation:
   Consistency: ${aggregated.validation.consistency.passed ? '✅' : '❌'}
   Completeness: ${aggregated.validation.completeness.passed ? '✅' : '❌'}
   Coherence: ${aggregated.validation.coherence.passed ? '✅' : '❌'}
   Critical Issues: ${aggregated.validation.criticalIssueCount}

🚪 Review Gate (P5):
   Status: ${reviewGateResult.approved ? '✅ APPROVED' : '❌ NEEDS REVIEW'}
   Warnings: ${reviewGateResult.review.warnings.length}
   Errors: ${reviewGateResult.review.errors.length}

📈 Convergence (P6):
   ${convergenceResult.converged ? `⚠️  CONVERGED (${convergenceResult.reason})` : `✅ Progressing (${convergenceResult.reason})`}
   ${convergenceResult.improvementRate !== null ? `Improvement: ${convergenceResult.improvementRate > 0 ? '+' : ''}${convergenceResult.improvementRate}% (${convergenceResult.improvementPercent}% of gap)` : ''}
   Iteration: ${convergenceResult.iterationCount || 1}
   Recommendation: ${convergenceResult.recommendation}

📁 Output:
   ${reportResult ? `L1 Summary: ${reportResult.l1Summary.length} chars` : '(Dry run)'}
   ${reportResult ? `L2 Report: ${reportResult.l2ReportPath}` : ''}

🔄 EFL Metadata:
   Pattern: ${usingAgentDelegation ? 'Agent Delegation (P1)' : 'Fallback (V2.2)'}
   Internal Iterations: ${aggregated.internalLoopMetadata?.totalIterations || 0}

═══════════════════════════════════════════════════════════════

${decisionIcon} Decision: ${decisionResult.decision}

${decisionResult.rationale.map(r => `  ${r}`).join('\n')}

Next Action:
  ${decisionResult.nextAction}

${convergenceResult.converged && convergenceResult.recommendation === 'escalate_to_manual' ? `
⚠️  Convergence Alert:
   Automated iteration has stalled. Consider:
   1. Manual gap analysis
   2. Requirements refinement
   3. Architecture review
` : ''}
`)
}

function getThreshold(mode) {
  return mode === 'strict' ? 95 : mode === 'lenient' ? 60 : 80
}
```

---



## 5. Error Handling

| Error | Detection | Recovery |
|-------|-----------|----------|
| **No clarify logs** | Glob returns empty | Prompt user to run /clarify first |
| **No collection report** | File not found | Prompt user to run /collect first |
| **Empty requirements** | Parse returns 0 | Show "No parseable requirements" |
| **Parse error** | Malformed content | Skip problematic sections, warn user |
| **Report write failure** | Permission error | Output to stdout instead |

---



## 6. Example Usage

### Example 1: Complete Success

```bash
/synthesis
```

**Output:**
```
🔍 Starting synthesis...
Mode: standard | Dry Run: false

📋 Reading requirements...
  Found 5 requirements (P0: 2, P1: 3)

📦 Reading collection report...
  Found 8 deliverables

📊 Building traceability matrix...

Matrix Summary:
  ✅ Covered: 4
  ⚠️  Partial: 1
  ❌ Missing: 0
  📈 Coverage: 90.0%

🔬 Validating quality...

Quality Check:
  Consistency: ✅
  Completeness: ✅
  Coherence: ✅
  Critical Issues: 0

⚖️  Making decision...

📝 Generating synthesis report...
✅ Synthesis report generated: .agent/outputs/synthesis/synthesis_report.md

=== Synthesis Complete ===

Decision: ✅ COMPLETE
Coverage: 90.0%
Threshold: 80%

  - Coverage: 90.0% (above 80% threshold)
  - Critical Issues: 0
  - Quality Validation: PASSED

Next Action:
  /commit-push-pr

Report: .agent/outputs/synthesis/synthesis_report.md
```

### Example 2: Iterate Required

```bash
/synthesis
```

**Output:**
```
🔍 Starting synthesis...
Mode: standard | Dry Run: false

📋 Reading requirements...
  Found 5 requirements (P0: 2, P1: 3)

📦 Reading collection report...
  Found 3 deliverables

📊 Building traceability matrix...

Matrix Summary:
  ✅ Covered: 2
  ⚠️  Partial: 1
  ❌ Missing: 2
  📈 Coverage: 50.0%

🔬 Validating quality...

Quality Check:
  Consistency: ✅
  Completeness: ❌
  Coherence: ✅
  Critical Issues: 1

⚖️  Making decision...

📝 Generating synthesis report...
✅ Synthesis report generated: .agent/outputs/synthesis/synthesis_report.md

=== Synthesis Complete ===

Decision: 🔄 ITERATE
Coverage: 50.0%
Threshold: 80%

  - Coverage: 50.0% (below 80% threshold)
  - Critical Issues: 1
  - Quality Validation: FAILED
  - Missing Requirements: 2
  - Partial Requirements: 1

Next Action:
  /clarify "Address gaps: Error handling, Input validation"

Report: .agent/outputs/synthesis/synthesis_report.md
```

### Example 3: Strict Mode

```bash
/synthesis --strict
```

**Output:**
```
🔍 Starting synthesis...
Mode: strict | Dry Run: false

...

=== Synthesis Complete ===

Decision: 🔄 ITERATE
Coverage: 90.0%
Threshold: 95%  # Strict mode requires 95%

  - Coverage: 90.0% (below 95% threshold)
  ...
```

---



## 7. Integration Points

### 7.1 Pipeline Position

```
/clarify → /research → /planning → /orchestrate → /assign → Workers → /collect → /synthesis
                                                                                       ↑
                                                                                 [THIS SKILL]
                                                                                       │
                                              ┌────────────────────────────────────────┴────────────────────────────────────────┐
                                              │                                                                                 │
                                          COMPLETE                                                                          ITERATE
                                              │                                                                                 │
                                              ▼                                                                                 ▼
                                    /commit-push-pr                                                                     /rsil-plan (2nd+ Loop)
                                                                                                                               │
                                                                                                               ┌───────────────┴───────────────┐
                                                                                                               │                               │
                                                                                                        Auto-Remediate                     Escalate
                                                                                                               │                               │
                                                                                                               ▼                               ▼
                                                                                                         /orchestrate                      /clarify
```

### 7.2 Input Dependencies

| Source | File | Purpose |
|--------|------|---------|
| /clarify | `.agent/plans/clarify_*.md` | Original requirements |
| /collect | `.agent/outputs/collection_report.md` | Aggregated deliverables |

### 7.3 Output

| Destination | File | Purpose |
|-------------|------|---------|
| /commit-push-pr | `.agent/outputs/synthesis/synthesis_report.md` | Completion evidence |
| /rsil-plan | Gaps list + synthesis report | Code-level gap analysis (2nd+ loops) |
| /clarify | Gaps list | Manual iteration (escalation only) |

---



## 8. Testing Checklist

### EFL Pattern Tests (V3.0)

**P1: Sub-Orchestrator (Agent Delegation)**
- [ ] Agent delegation to Phase 3-A (Semantic Matching)
- [ ] Agent delegation to Phase 3-B (Quality Validation)
- [ ] Agent prompt generation with internal loop instructions
- [ ] Fallback to V2.2 keyword matching when delegation fails

**P3: Semantic Synthesis**
- [ ] Semantic matching replaces keyword matching
- [ ] Confidence scores calculated accurately
- [ ] AI-powered requirement-deliverable matching
- [ ] L2/L3 structure properly separated

**P4: Selective Feedback**
- [ ] Severity-based feedback check (MEDIUM+ threshold)
- [ ] LOW severity → log only
- [ ] MEDIUM+ severity → trigger review/feedback

**P5: Phase 3.5 Review Gate**
- [ ] Review gate executes before decision
- [ ] Review criteria checked (requirement_alignment, etc.)
- [ ] Approved result allows progression
- [ ] Failed review blocks with clear errors

**P6: Internal Loop + Convergence Detection**
- [ ] Agent prompts include internal loop instructions
- [ ] Internal loop metadata extracted from agent results
- [ ] Max 3 iterations enforced per agent
- [ ] Convergence detection (improvement rate < 5%)
- [ ] Coverage plateau detection (3 iterations < 2% improvement)
- [ ] Critical issue stagnation detection
- [ ] Max pipeline iterations enforced
- [ ] Iteration history saved to YAML

### V2.2 Legacy Tests (Fallback)
- [ ] No clarify logs found scenario
- [ ] No collection report scenario
- [ ] All requirements covered (COMPLETE)
- [ ] Partial coverage (COMPLETE_WITH_WARNINGS)
- [ ] Low coverage (ITERATE)
- [ ] Critical issues detected
- [ ] --strict mode threshold (95%)
- [ ] --lenient mode threshold (60%)
- [ ] --dry-run mode
- [ ] Traceability matrix accuracy
- [ ] Quality validation (consistency)
- [ ] Quality validation (completeness)
- [ ] Quality validation (coherence)
- [ ] Report generation
- [ ] Decision rationale clarity

### Integration Tests
- [ ] End-to-end: /collect L1 → /synthesis → decision
- [ ] Workload-scoped output paths
- [ ] Iteration history tracking across multiple runs
- [ ] Convergence alert triggers manual escalation
- [ ] Review gate warnings display correctly

---



## 9. Performance Targets

| Operation | Target | Actual |
|-----------|--------|--------|
| Read requirements | <500ms | TBD |
| Read collection | <500ms | TBD |
| Build matrix | <1s | TBD |
| Quality validation | <2s | TBD |
| Report generation | <500ms | TBD |
| Total /synthesis | <5s | TBD |

---



## 10. Future Enhancements

1. **AI-powered matching:** Use embeddings for requirement-deliverable matching
2. **Diff analysis:** Compare current vs previous synthesis runs
3. **Auto-fix suggestions:** Generate specific code fixes for gaps
4. **Confidence scores:** Add confidence percentage to each matrix entry
5. **Historical tracking:** Track coverage trend over iterations

---



## Parameter Module Compatibility (V2.1.0)

> `/build/parameters/` 모듈과의 호환성 체크리스트

| Module | Status | Notes |
|--------|--------|-------|
| `model-selection.md` | ✅ | `model: sonnet` 설정 |
| `context-mode.md` | ✅ | `context: standard` 사용 |
| `tool-config.md` | ✅ | V2.1.0: Task + Read + Grep tools |
| `hook-config.md` | N/A | Skill 내 Hook 없음 |
| `permission-mode.md` | N/A | Skill에는 해당 없음 |
| `task-params.md` | ✅ | Task quality matrix + traceability |

## Parameter Module Compatibility (V3.0.0)

| Module | Status | Notes |
|--------|--------|-------|
| `model-selection.md` | ✅ | `model: opus` (skill + agents for high-quality analysis) |
| `context-mode.md` | ✅ | `context: standard` |
| `tool-config.md` | ✅ | V3.0: Agent delegation + Task tool integration |
| `hook-config.md` | ✅ | V3.0: Setup hook (validation-feedback-loop.sh) |
| `permission-mode.md` | N/A | No elevated permissions |
| `task-params.md` | ✅ | Traceability matrix + convergence tracking |

---



### Version History

| Version | Change |
|---------|--------|
| 1.0.0 | Traceability matrix generation |
| 2.1.0 | V2.1.19 Spec 호환, task-params 통합 |
| 2.2.0 | /rsil-plan integration for ITERATE path |
| 3.0.0 | **EFL Integration**: P1 (Sub-Orchestrator), P3 (Semantic matching), P5 (Review Gate), P6 (Convergence detection) |

### V3.0.0 Detailed Changes

**Enhanced Feedback Loop (EFL) Patterns:**
- **P1: Skill as Sub-Orchestrator** - Delegates to specialized agents instead of direct analysis
- **P3: Semantic Synthesis** - AI-powered semantic matching replaces keyword-based heuristics
- **P5: Phase 3.5 Review Gate** - Holistic verification before final decision
- **P6: Agent Internal Feedback Loop + Convergence Detection** - Agent self-validation + iteration tracking with stall detection
- **P4: Selective Feedback** - Severity-based threshold (MEDIUM+)

**New Sections:**
- `agent_delegation` frontmatter config
- `agent_internal_feedback_loop` config with convergence detection
- `review_gate` config with Phase 3.5 criteria
- `selective_feedback` config with severity thresholds
- `iteration_tracking` config for convergence detection
- Setup hook: `shared/validation-feedback-loop.sh`

**Modified Execution Flow:**
1. Phase 0: Setup & Context Loading (NEW) - Loads requirements, collection, iteration history
2. Phase 1: Agent delegation (NEW) - Replaces direct traceability matrix building
   - Phase 3-A: Semantic requirement-deliverable matching (AI-powered)
   - Phase 3-B: Quality validation (consistency, completeness, coherence)
3. Phase 2: Convergence detection (NEW) - Tracks iteration progress, detects stalls
4. Phase 3: Selective feedback check (NEW) - P4 integration
5. Phase 3.5: Review gate (NEW) - P5 verification
6. Phase 4: Make decision with convergence awareness (ENHANCED)
7. Phase 5: Generate L1/L2 report + save iteration history (ENHANCED)

**Convergence Detection Features:**
- Improvement rate tracking (alerts if < 5% improvement)
- Critical issue reduction monitoring
- Coverage plateau detection (3 consecutive iterations < 2% improvement)
- Max iterations enforcement (default: 5)
- Iteration history persistence (`.agent/prompts/{workload}/synthesis/iteration_history.yaml`)
- Automatic escalation recommendation when converged

**Backward Compatibility:**
- V2.2 keyword matching preserved as fallback
- All existing command-line arguments supported
- Legacy helper functions retained
- Graceful degradation when agent delegation unavailable

| 3.1.0 | **Standalone Execution + Handoff Contract** - 독립 실행 모드, 표준화된 handoff 출력 |

---



## 11. Standalone Execution (V3.1.0)

### 11.1 독립 실행 모드

`/synthesis`는 upstream `/collect` 없이 독립적으로 실행 가능:

```bash
# 독립 실행 (active workload 또는 새 workload)
/synthesis
/synthesis --strict
# Output: .agent/prompts/{slug}/synthesis/synthesis_report.md

# 명시적 workload 지정
/synthesis --workload user-auth-20260128-143022
```

### 11.2 Workload Context Resolution

```bash
# Source standalone module
source /home/palantir/.claude/skills/shared/skill-standalone.sh

# Initialize skill context
CONTEXT=$(init_skill_context "synthesis" "$ARGUMENTS" "")

# Resolution priority:
# 1. --workload argument → explicit workload
# 2. Active workload → .agent/prompts/_active_workload.yaml
# 3. Recent workload directory → most recently modified
# 4. Generate new workload → standalone mode
```

---



## 12. Handoff Contract (V3.1.0)

### 12.1 Handoff 매핑

| Decision | Next Skill | Arguments |
|----------|------------|-----------|
| `COMPLETE` | `/commit-push-pr` | `--workload {slug}` |
| `COMPLETE_WITH_WARNINGS` | `/commit-push-pr` | `--workload {slug} --with-warnings` |
| `ITERATE` | `/rsil-plan` | `--workload {slug} --iteration N` |

### 12.2 Handoff YAML 출력

스킬 완료 시 synthesis_report.md 끝에 다음 handoff 섹션을 추가:

```yaml
---


# Handoff Metadata (auto-generated)
handoff:
  skill: "synthesis"
  workload_slug: "user-auth-20260128-143022"
  status: "completed"  # or "iterate"
  timestamp: "2026-01-28T16:30:00Z"
  next_action:
    skill: "/commit-push-pr"  # or "/rsil-plan"
    arguments: "--workload user-auth-20260128-143022"
    required: true
    reason: "Synthesis complete, coverage 95%"
```

### 12.3 Decision-Based Routing

```bash
# COMPLETE 결정 시
/commit-push-pr --workload user-auth-20260128-143022

# ITERATE 결정 시
/rsil-plan --workload user-auth-20260128-143022 --iteration 2
```

---



**End of Skill Documentation**
