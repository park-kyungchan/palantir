---
name: rsil-plan
description: |
  Requirements-Synthesis Integration Loop (RSIL).
  Verifies synthesis results against original requirements.
  Performs code-level gap analysis and creates remediation plans.

  **V3.0.0 Changes (EFL Integration):**
  - P1: Skill as Sub-Orchestrator (agent delegation for gap analysis)
  - P3: General-Purpose Synthesis (Phase 3-A L2 horizontal + Phase 3-B L3 vertical)
  - P5: Phase 3.5 Review Gate (holistic verification before remediation)
  - P6: Agent Internal Feedback Loop (max 3 iterations)

user-invocable: true
disable-model-invocation: false
context: fork
model: opus
version: "3.0.0"
argument-hint: "[--iteration <n>] [--auto-remediate] [--workload <slug>]"
allowed-tools:
  - Read
  - Grep
  - Glob
  - Task
  - TaskCreate
  - mcp__sequential-thinking__sequentialthinking
  - TaskUpdate
  - TaskList
  - AskUserQuestion
  - Write
hooks:
  Setup:
    - type: command
      command: "source /home/palantir/.claude/skills/shared/workload-files.sh"
      timeout: 5000

# =============================================================================
# P1: Skill as Sub-Orchestrator
# =============================================================================
agent_delegation:
  enabled: true
  default_mode: true  # V1.1.0: Auto-delegation by default
  max_sub_agents: 3
  delegation_strategy: "phase-based"
  strategies:
    gap_verification:
      description: "Delegate code-level gap verification to explore agents"
      use_when: "Multiple requirements need verification"
    evidence_collection:
      description: "Delegate evidence collection from codebase"
      use_when: "Deep code analysis needed"
  slug_orchestration:
    enabled: true
  default_mode: true  # V1.1.0: Auto-delegation by default
    source: "synthesis or active workload"
    action: "reuse upstream workload context"
  sub_agent_permissions:
    - Read
    - Grep
    - Glob
  output_paths:
    l1: ".agent/prompts/{slug}/rsil-plan/l1_summary.yaml"
    l2: ".agent/prompts/{slug}/rsil-plan/l2_index.md"
    l3: ".agent/prompts/{slug}/rsil-plan/l3_details/"
  return_format:
    l1: "Gap analysis summary with remediation decision (≤500 tokens)"
    l2_path: ".agent/prompts/{slug}/rsil-plan/l2_index.md"
    l3_path: ".agent/prompts/{slug}/rsil-plan/l3_details/"
    requires_l2_read: false
    next_action_hint: "/orchestrate (remediation tasks)"
  description: |
    This skill operates as a Sub-Orchestrator (P1).
    L1 returns to main context; L2/L3 always saved to files.

# =============================================================================
# P2: Parallel Agent Configuration
# =============================================================================
parallel_agent_config:
  enabled: true
  complexity_detection: "auto"
  agent_count_by_complexity:
    simple: 1      # 1-2 gaps
    moderate: 2    # 3-5 gaps
    complex: 3     # 6+ gaps
  synchronization_strategy: "barrier"
  aggregation_strategy: "merge"
  gap_areas:
    - requirement_verification
    - code_evidence_collection
    - test_coverage_check
  description: |
    Deploy multiple Explore Agents in parallel for gap verification.
    Agent count scales with gap count detected in synthesis.

# =============================================================================
# P6: Agent Internal Feedback Loop
# =============================================================================
agent_internal_feedback_loop:
  enabled: true
  max_iterations: 3
  validation_criteria:
    completeness:
      - "All requirements verified against codebase"
      - "Evidence collected for each finding"
      - "Gap classification accurate (COVERED/PARTIAL/MISSING)"
    quality:
      - "Code evidence includes file paths and snippets"
      - "Confidence levels assigned to each finding"
      - "Remediation recommendations specific"
    internal_consistency:
      - "L1/L2/L3 hierarchy maintained"
      - "Gap stats match detailed findings"
      - "Task descriptions actionable"

# =============================================================================
# P5: Review Gate (Phase 3.5)
# =============================================================================
review_gate:
  enabled: true
  phase: "3.5"
  criteria:
    - "requirement_alignment: All synthesis gaps re-verified"
    - "design_flow_consistency: Gap findings match code reality"
    - "gap_detection: Missing/partial requirements clearly identified"
    - "conclusion_clarity: Decision (AUTO_REMEDIATE/ESCALATE) unambiguous"
  auto_approve: false

# =============================================================================
# P4: Selective Feedback
# =============================================================================
selective_feedback:
  enabled: true
  threshold: "MEDIUM"
  action_on_low: "log_only"
  action_on_medium_plus: "trigger_review_gate"

hooks:
  Setup:
    - type: command
      command: "source /home/palantir/.claude/skills/shared/validation-feedback-loop.sh"
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


# /rsil-plan - Requirements-Synthesis Integration Loop (EFL V3.0.0)

> **Version:** 3.0.0 (EFL Pattern)
> **Role:** Gap Analysis + Remediation Planning with Full EFL Implementation
> **Pipeline Position:** After /synthesis ITERATE decision
> **Model:** Opus (for comprehensive code analysis)
> **EFL Template:** `.claude/skills/shared/efl-template.md`

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


## 1. Purpose

The RSIL (Requirements-Synthesis Integration Loop) skill handles iteration cycles when `/synthesis` returns ITERATE, using Enhanced Feedback Loop (EFL) pattern:

1. **Phase 1**: Deploy parallel Explore Agents for gap verification (P2)
2. **Phase 2**: Aggregate L1 summaries from all agents
3. **Phase 3-A**: L2 Horizontal Synthesis (cross-requirement consistency)
4. **Phase 3-B**: L3 Vertical Verification (code-level accuracy)
5. **Phase 3.5**: Main Agent Review Gate (holistic verification)
6. **Phase 4**: Selective Feedback Loop (if issues found)
7. **Phase 5**: User Decision Confirmation

### Pipeline Integration

```
/synthesis
    │
    └── ITERATE → /rsil-plan ◄── THIS SKILL (EFL V3.0.0)
                      │
                      ├── Phase 1: Parallel Explore Agents (P2)
                      ├── Phase 2: L1 Aggregation
                      ├── Phase 3-A: L2 Horizontal Synthesis (P3)
                      ├── Phase 3-B: L3 Vertical Verification (P3)
                      ├── Phase 3.5: Main Agent Review Gate (P1)
                      ├── Phase 4: Selective Feedback Loop (P4)
                      ├── Phase 5: User Decision Confirmation (P5)
                      │
                      ├── Gaps < 3 + Low Complexity → AUTO_REMEDIATE → /orchestrate
                      └── Otherwise → ESCALATE → /clarify
```

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


## 2. Invocation

### User Syntax

```bash
# First iteration (auto-detected)
/rsil-plan

# Specific iteration number
/rsil-plan --iteration 2

# Auto-remediate mode (skip user confirmation)
/rsil-plan --auto-remediate

# Combined
/rsil-plan --iteration 3 --auto-remediate
```

### Arguments

| Argument | Required | Default | Description |
|----------|----------|---------|-------------|
| `--iteration` | No | Auto-detect | Iteration number (1, 2, 3...) |
| `--auto-remediate` | No | `false` | Skip confirmation for auto-remediation |

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


## 3. Workload Slug 결정 (표준)

### 3.0 Slug 결정 로직

```bash
# Source centralized slug generator
source "${WORKSPACE_ROOT:-.}/.claude/skills/shared/slug-generator.sh"
source "${WORKSPACE_ROOT:-.}/.claude/skills/shared/workload-files.sh"

# Slug 결정 (우선순위)
# 1. --workload 인자 (명시적 지정)
# 2. 활성 workload (get_active_workload)
# 3. synthesis 결과에서 추출 (glob 패턴)
# 4. 새 workload 생성 (기본 동작)

if [[ -n "$WORKLOAD_ARG" ]]; then
    SLUG="$WORKLOAD_ARG"
    echo "🔄 Using specified workload: $SLUG"

elif ACTIVE_WORKLOAD=$(get_active_workload) && [[ -n "$ACTIVE_WORKLOAD" ]]; then
    WORKLOAD_ID="$ACTIVE_WORKLOAD"
    SLUG=$(get_active_workload_slug)
    echo "🔄 Using active workload: $SLUG"

elif SYNTHESIS_PATH=$(ls -t .agent/prompts/*/synthesis/synthesis_report.md 2>/dev/null | head -1); [[ -n "$SYNTHESIS_PATH" ]]; then
    # synthesis 결과에서 slug 추출
    SLUG=$(echo "$SYNTHESIS_PATH" | sed 's|.agent/prompts/||' | sed 's|/synthesis/.*||')
    echo "🔄 Using workload from synthesis: $SLUG"

else
    # 기본 동작: 새 workload 생성
    TOPIC="rsil-$(date +%H%M%S)"
    WORKLOAD_ID=$(generate_workload_id "$TOPIC")
    SLUG=$(generate_slug_from_workload "$WORKLOAD_ID")
    init_workload_directory "$WORKLOAD_ID"
    set_active_workload "$WORKLOAD_ID"
    echo "🔄 Created new workload: $SLUG"
fi

# 출력 경로 설정
WORKLOAD_DIR=".agent/prompts/${SLUG}"
mkdir -p "${WORKLOAD_DIR}"
```

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


## 4. Multi-Source Loading

### 4.1 Source Files

```javascript
// Workload-scoped paths (V3.1.0)
const sources = {
  clarify: ".agent/prompts/{slug}/clarify.yaml",
  research: ".agent/prompts/{slug}/research.md",
  planning: ".agent/prompts/{slug}/plan.yaml",
  synthesis: ".agent/prompts/{slug}/synthesis/synthesis_report.md"
}
```

### 3.2 Load Requirements (from /clarify)

```javascript
async function loadClarifyRequirements() {
  // Find latest clarify log (Workload-scoped path)
  const clarifyLogs = await Glob({ pattern: ".agent/prompts/*/clarify.yaml" })

  if (clarifyLogs.length === 0) {
    return { error: "No clarify logs found" }
  }

  // Sort by modification time (newest first)
  const latestLog = clarifyLogs[0]
  const content = await Read({ file_path: latestLog })

  // Extract requirements from rounds
  const requirements = []
  for (const round of content.rounds || []) {
    if (round.user_response === "승인") {
      requirements.push({
        id: `REQ-${requirements.length + 1}`,
        description: round.improved_prompt,
        source: "clarify",
        priority: extractPriority(round.improved_prompt)
      })
    }
  }

  return {
    path: latestLog,
    requirements: requirements,
    finalPrompt: content.final_output?.approved_prompt
  }
}
```

### 3.3 Load Research Findings (from /research)

```javascript
async function loadResearchFindings() {
  // Workload-scoped path
  const researchDocs = await Glob({ pattern: ".agent/prompts/*/research.md" })

  if (researchDocs.length === 0) {
    return { findings: [], riskAssessment: null }
  }

  const latestDoc = researchDocs[0]
  const content = await Read({ file_path: latestDoc })

  // Extract patterns and recommendations
  const patterns = extractSection(content, "## Codebase Pattern Analysis")
  const risks = extractSection(content, "## Risk Assessment")
  const recommendations = extractSection(content, "## Recommendations")

  return {
    path: latestDoc,
    patterns: patterns,
    riskAssessment: risks,
    recommendations: recommendations
  }
}
```

### 3.4 Load Planning Document (from /planning)

```javascript
async function loadPlanningDocument() {
  // Workload-scoped path
  const planDocs = await Glob({ pattern: ".agent/prompts/*/plan.yaml" })

  if (planDocs.length === 0) {
    return { phases: [], dependencies: [] }
  }

  const latestPlan = planDocs[0]
  const content = await Read({ file_path: latestPlan })

  // Parse YAML structure
  return {
    path: latestPlan,
    phases: content.phases || [],
    dependencies: content.dependencies || {},
    completionCriteria: extractAllCompletionCriteria(content.phases)
  }
}
```

### 3.5 Load Synthesis Results (from /synthesis)

```javascript
async function loadSynthesisResults(workloadSlug) {
  // Workload-scoped path
  const synthesisPath = workloadSlug
    ? `.agent/prompts/${workloadSlug}/synthesis/synthesis_report.md`
    : ".agent/outputs/synthesis/synthesis_report.md"  // Fallback (deprecated)

  if (!await fileExists(synthesisPath)) {
    return { error: "Synthesis report not found" }
  }

  const content = await Read({ file_path: synthesisPath })

  // Extract traceability matrix
  const matrixSection = extractSection(content, "## Traceability Matrix")
  const matrix = parseTraceabilityMatrix(matrixSection)

  // Extract decision
  const decisionSection = extractSection(content, "## Decision")
  const decision = parseDecision(decisionSection)

  return {
    path: synthesisPath,
    matrix: matrix,
    decision: decision,
    coverage: decision.coverage,
    gaps: matrix.filter(m => m.status !== "covered")
  }
}
```

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


## 4. Code-Level Gap Verification

### 4.1 Verification Protocol

```javascript
async function verifyGapsWithCode(requirements, synthesis) {
  const verifiedGaps = []

  for (const req of requirements) {
    // Find synthesis status
    const synthEntry = synthesis.matrix.find(m =>
      m.requirement.includes(req.description.substring(0, 30))
    )

    // Generate Grep patterns from requirement
    const patterns = generateGrepPatterns(req)

    // Search codebase for evidence
    let evidence = {
      files: [],
      matchCount: 0,
      codeSnippets: []
    }

    for (const pattern of patterns) {
      const results = await Grep({
        pattern: pattern.regex,
        type: pattern.fileType,
        output_mode: "content",
        "-C": 2
      })

      if (results && results.length > 0) {
        evidence.files.push(...results.files)
        evidence.matchCount += results.matchCount
        evidence.codeSnippets.push(...extractSnippets(results))
      }
    }

    // Classify gap status
    let status = "MISSING"
    let coverage = 0

    if (evidence.matchCount >= 3) {
      status = "COVERED"
      coverage = 100
    } else if (evidence.matchCount >= 1) {
      status = "PARTIAL"
      coverage = 50
    }

    verifiedGaps.push({
      requirementId: req.id,
      requirement: req.description,
      priority: req.priority,
      synthStatus: synthEntry?.status || "unknown",
      codeStatus: status,
      coverage: coverage,
      evidence: evidence,
      discrepancy: synthEntry?.status !== status
    })
  }

  return verifiedGaps
}
```

### 4.2 Grep Pattern Generation

```javascript
function generateGrepPatterns(requirement) {
  const patterns = []
  const keywords = extractKeywords(requirement.description)

  // Function/class definition patterns
  patterns.push({
    regex: `(function|class|def|const|export).*${keywords[0]}`,
    fileType: "ts,js,py",
    description: "Function/class definition"
  })

  // Test file patterns
  patterns.push({
    regex: `(describe|test|it).*${keywords[0]}`,
    fileType: "ts,js",
    description: "Test coverage"
  })

  // Import/usage patterns
  patterns.push({
    regex: `(import|from|require).*${keywords[0]}`,
    fileType: "ts,js,py",
    description: "Import usage"
  })

  // Comment/documentation patterns
  patterns.push({
    regex: `(TODO|FIXME|@param|@returns).*${keywords[0]}`,
    fileType: "ts,js,py,md",
    description: "Documentation"
  })

  return patterns
}
```

### 4.3 Evidence Collection

```javascript
async function collectEvidence(requirement, grepResults) {
  return {
    matchingFiles: grepResults.map(r => r.file),
    lineNumbers: grepResults.map(r => r.lineNumber),
    snippets: grepResults.map(r => ({
      file: r.file,
      line: r.lineNumber,
      content: r.content,
      context: r.context
    })),
    confidenceLevel: calculateConfidence(grepResults)
  }
}

function calculateConfidence(results) {
  if (results.length >= 5) return "HIGH"
  if (results.length >= 2) return "MEDIUM"
  if (results.length >= 1) return "LOW"
  return "NONE"
}
```

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


## 5. Gap Classification

### 5.1 Status Definitions

| Status | Description | Code Evidence | Action |
|--------|-------------|---------------|--------|
| **COVERED** | Fully implemented | 3+ matches | No action |
| **PARTIAL** | Partially implemented | 1-2 matches | Complete implementation |
| **MISSING** | Not implemented | 0 matches | Full implementation |

### 5.2 Classification Logic

```javascript
function classifyGap(requirement, evidence, synthesis) {
  const codeMatches = evidence.matchCount
  const synthStatus = synthesis?.status || "unknown"

  // Code-level classification (primary)
  let status, complexity, action

  if (codeMatches >= 3) {
    status = "COVERED"
    complexity = "none"
    action = null
  } else if (codeMatches >= 1) {
    status = "PARTIAL"
    complexity = estimateComplexity(requirement, evidence)
    action = "complete_implementation"
  } else {
    status = "MISSING"
    complexity = estimateComplexity(requirement, evidence)
    action = "full_implementation"
  }

  // Check for discrepancy with synthesis
  const discrepancy = (synthStatus === "covered" && status !== "COVERED") ||
                      (synthStatus === "missing" && status === "COVERED")

  return {
    status,
    complexity,
    action,
    discrepancy,
    synthesisStatus: synthStatus,
    codeEvidence: evidence,
    notes: discrepancy ? "Code-level verification differs from synthesis" : null
  }
}
```

### 5.3 Complexity Estimation

```javascript
function estimateComplexity(requirement, evidence) {
  const keywords = extractKeywords(requirement.description)

  // High complexity indicators
  const highComplexityPatterns = [
    "integration", "security", "authentication", "database",
    "migration", "refactor", "architecture", "performance"
  ]

  // Low complexity indicators
  const lowComplexityPatterns = [
    "add", "update", "fix", "modify", "change",
    "simple", "basic", "straightforward"
  ]

  const descLower = requirement.description.toLowerCase()

  if (highComplexityPatterns.some(p => descLower.includes(p))) {
    return "high"
  }

  if (lowComplexityPatterns.some(p => descLower.includes(p)) &&
      evidence.matchCount >= 1) {
    return "low"
  }

  return "medium"
}
```

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


## 6. Remediation Task Generation

### 6.1 Task Creation Protocol

```javascript
async function createRemediationTasks(gaps, iteration) {
  const tasks = []

  for (const gap of gaps) {
    if (gap.status === "COVERED") continue

    // Create remediation task using Native Task API
    const task = await TaskCreate({
      subject: `[RSIL-${iteration}] ${gap.action === 'complete_implementation'
        ? 'Complete' : 'Implement'}: ${gap.requirement.substring(0, 50)}...`,
      description: generateTaskDescription(gap),
      activeForm: `Remediating: ${gap.requirementId}`
    })

    tasks.push({
      nativeTaskId: task.id,
      gap: gap,
      complexity: gap.complexity,
      priority: gap.priority
    })
  }

  // Set up dependencies between tasks if needed
  await setupTaskDependencies(tasks)

  return tasks
}
```

### 6.2 Task Description Generation

```javascript
function generateTaskDescription(gap) {
  return `
## Remediation Task

**Requirement ID:** ${gap.requirementId}
**Requirement:** ${gap.requirement}
**Status:** ${gap.status}
**Priority:** ${gap.priority}
**Complexity:** ${gap.complexity}

### Evidence Found
${gap.evidence.files.length > 0
  ? gap.evidence.files.map(f => `- ${f}`).join('\n')
  : '- No existing implementation found'}

### Required Actions
${gap.action === 'complete_implementation'
  ? `Complete the partial implementation:
- Review existing code at: ${gap.evidence.files.join(', ')}
- Fill in missing functionality
- Add tests if not present`
  : `Implement from scratch:
- Create necessary files
- Follow existing patterns
- Include tests and documentation`}

### Completion Criteria
- Code implements the full requirement
- Unit tests pass
- Integration with existing code verified

### Context
- Research: .agent/prompts/{slug}/research.md
- Planning: .agent/prompts/{slug}/plan.yaml
- Iteration: RSIL-${gap.iteration}
`
}
```

### 6.3 Dependency Setup

```javascript
async function setupTaskDependencies(tasks) {
  // Sort by complexity (simple first)
  const sorted = tasks.sort((a, b) =>
    complexityOrder(a.complexity) - complexityOrder(b.complexity)
  )

  // High complexity tasks depend on low complexity ones
  for (let i = 0; i < sorted.length; i++) {
    const task = sorted[i]

    if (task.complexity === "high") {
      // Find related low/medium complexity tasks
      const dependencies = sorted
        .filter(t => t.complexity !== "high" &&
                     isRelated(t.gap, task.gap))
        .map(t => t.nativeTaskId)

      if (dependencies.length > 0) {
        await TaskUpdate({
          taskId: task.nativeTaskId,
          addBlockedBy: dependencies
        })
      }
    }
  }
}

function complexityOrder(c) {
  return { low: 1, medium: 2, high: 3 }[c] || 2
}

function isRelated(gap1, gap2) {
  // Check if gaps share keywords or affected files
  const keywords1 = extractKeywords(gap1.requirement)
  const keywords2 = extractKeywords(gap2.requirement)

  return keywords1.some(k => keywords2.includes(k))
}
```

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


## 7. Decision Logic

### 7.1 Auto-Remediate vs Escalate

```javascript
function makeDecision(gaps, options) {
  const missingCount = gaps.filter(g => g.status === "MISSING").length
  const partialCount = gaps.filter(g => g.status === "PARTIAL").length
  const totalGaps = missingCount + partialCount

  const highComplexityCount = gaps.filter(g => g.complexity === "high").length

  // Decision criteria
  const criteria = {
    gapThreshold: 3,
    highComplexityThreshold: 1,
    autoRemediate: options.autoRemediate || false
  }

  let decision, reason, nextAction

  if (totalGaps === 0) {
    // No gaps - shouldn't happen if called from /synthesis ITERATE
    decision = "COMPLETE"
    reason = "No gaps detected"
    nextAction = "/commit-push-pr"
  }
  else if (totalGaps <= criteria.gapThreshold &&
           highComplexityCount < criteria.highComplexityThreshold) {
    // Auto-remediate eligible
    decision = "AUTO_REMEDIATE"
    reason = [
      `Gaps: ${totalGaps} (threshold: ${criteria.gapThreshold})`,
      `High complexity: ${highComplexityCount} (threshold: ${criteria.highComplexityThreshold})`,
      "Eligible for automatic remediation"
    ]
    nextAction = `/orchestrate --workload ${workloadSlug}`
  }
  else {
    // Escalate to user
    decision = "ESCALATE"
    reason = [
      `Gaps: ${totalGaps} exceeds threshold OR high complexity detected`,
      `Missing: ${missingCount}`,
      `Partial: ${partialCount}`,
      `High complexity: ${highComplexityCount}`,
      "Requires user guidance for requirements clarification"
    ]
    nextAction = `/clarify "Address RSIL gaps: ${gaps.slice(0, 3).map(g => g.requirementId).join(', ')}"`
  }

  return {
    decision,
    reason: Array.isArray(reason) ? reason : [reason],
    nextAction,
    gaps: gaps,
    stats: {
      total: totalGaps,
      missing: missingCount,
      partial: partialCount,
      highComplexity: highComplexityCount
    }
  }
}
```

### 7.2 User Confirmation

```javascript
async function confirmDecision(decision, options) {
  if (options.autoRemediate && decision.decision === "AUTO_REMEDIATE") {
    return { confirmed: true, action: decision.nextAction }
  }

  const response = await AskUserQuestion({
    questions: [{
      question: `RSIL Analysis: ${decision.stats.total} gaps found (${decision.stats.missing} missing, ${decision.stats.partial} partial). ${decision.decision === "AUTO_REMEDIATE" ? "Auto-remediate?" : "Escalate to /clarify?"}`,
      header: "RSIL Decision",
      options: [
        {
          label: decision.decision === "AUTO_REMEDIATE"
            ? "Auto-Remediate (Recommended)"
            : "Escalate to /clarify (Recommended)",
          description: decision.reason.join("; ")
        },
        {
          label: decision.decision === "AUTO_REMEDIATE"
            ? "Escalate Instead"
            : "Force Auto-Remediate",
          description: "Override the recommendation"
        },
        {
          label: "View Gap Details",
          description: "See full gap analysis before deciding"
        }
      ],
      multiSelect: false
    }]
  })

  if (response.includes("View")) {
    return { confirmed: false, action: "show_details" }
  }

  if (response.includes("Recommended")) {
    return { confirmed: true, action: decision.nextAction }
  }

  // User chose override
  if (decision.decision === "AUTO_REMEDIATE") {
    return { confirmed: true, action: `/clarify "Address RSIL gaps"` }
  } else {
    return { confirmed: true, action: "/orchestrate --plan-slug rsil-remediation" }
  }
}
```

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


## 8. Output Files

### 8.1 Gap Analysis Report

**Path:** `.agent/prompts/{workload-slug}/rsil/iteration_{n}.md`

```markdown
# RSIL Gap Analysis Report - Iteration {n}

> Generated: {timestamp}
> Previous Iteration: {n-1 or "Initial"}
> Coverage Before: {previous_coverage}%
> Coverage After: TBD

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


## Summary

| Metric | Value |
|--------|-------|
| Total Requirements | {count} |
| COVERED | {count} ({percent}%) |
| PARTIAL | {count} ({percent}%) |
| MISSING | {count} ({percent}%) |
| High Complexity Gaps | {count} |

## Decision

**{AUTO_REMEDIATE | ESCALATE}**

{reason}

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


## Gap Details

### MISSING

| ID | Requirement | Complexity | Evidence |
|----|-------------|------------|----------|
| REQ-001 | {description} | high | 0 matches |

### PARTIAL

| ID | Requirement | Complexity | Evidence | Files |
|----|-------------|------------|----------|-------|
| REQ-002 | {description} | medium | 2 matches | src/auth.ts |

### COVERED

| ID | Requirement | Evidence | Files |
|----|-------------|----------|-------|
| REQ-003 | {description} | 5 matches | src/user.ts, tests/user.test.ts |

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


## Remediation Tasks Created

| Task ID | Requirement | Complexity | Status |
|---------|-------------|------------|--------|
| #101 | REQ-001 | high | pending |
| #102 | REQ-002 | medium | pending |

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


## Next Action

\`\`\`bash
{next_action_command}
\`\`\`
```

### 8.2 Remediation Plan

**Path:** `.agent/prompts/{workload-slug}/rsil/iteration_{n}_remediation.yaml`

```yaml
metadata:
  iteration: {n}
  created_at: "{timestamp}"
  decision: "{AUTO_REMEDIATE | ESCALATE}"
  previous_coverage: "{percent}%"

gaps:
  - id: "REQ-001"
    requirement: "{description}"
    status: "MISSING"
    complexity: "high"
    priority: "P0"
    action: "full_implementation"
    nativeTaskId: "101"

  - id: "REQ-002"
    requirement: "{description}"
    status: "PARTIAL"
    complexity: "medium"
    priority: "P1"
    action: "complete_implementation"
    nativeTaskId: "102"
    existingFiles:
      - "src/auth.ts"

tasks:
  - id: "101"
    subject: "[RSIL-{n}] Implement: {requirement}"
    blockedBy: []
    complexity: "high"

  - id: "102"
    subject: "[RSIL-{n}] Complete: {requirement}"
    blockedBy: []
    complexity: "medium"

execution:
  parallelizable: ["102"]
  sequential: ["101"]
  estimatedDuration: "{hours}h"

nextAction:
  command: "{next_action_command}"
  type: "{orchestrate | clarify}"
```

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


## 9. EFL Execution Protocol (V3.0.0)

### 9.1 Phase 1: Parallel Explore Agent Deployment (P2)

```javascript
async function phase1_parallel_gap_verification(synthesis, clarify) {
  // Determine complexity and agent count
  const gapCount = synthesis.gaps.length
  const agentCount = getAgentCountByComplexity(gapCount)

  console.log(`📊 Gap count: ${gapCount} → ${agentCount} agents`)

  // Divide gaps into areas for parallel verification
  const gapAreas = [
    { id: "req", name: "Requirement Verification", focus: "requirement_coverage" },
    { id: "code", name: "Code Evidence Collection", focus: "implementation_evidence" },
    { id: "test", name: "Test Coverage Check", focus: "test_verification" }
  ].slice(0, agentCount)

  // Deploy parallel Explore Agents with P6 self-validation
  const agents = gapAreas.map(area => Task({
    subagent_type: "Explore",
    model: "opus",
    prompt: `
## Gap Verification Area: ${area.name}

### Context
Original Requirements: ${clarify.originalRequest}

Synthesis Gaps (${synthesis.gaps.length} total):
${synthesis.gaps.map(g => `- ${g.requirementId}: ${g.description}`).join('\n')}

### Your Focus
Verify gaps for: **${area.focus}**

### Internal Feedback Loop (P6 - REQUIRED)
1. Search codebase for evidence using Grep patterns
2. Self-validate:
   - Evidence accuracy: Do matches actually implement the requirement?
   - Completeness: Have all relevant files been checked?
   - Classification correctness: Is COVERED/PARTIAL/MISSING accurate?
3. If validation fails, revise and retry (max 3 iterations)
4. Output only after validation passes

### Output Format
Return YAML:
\`\`\`yaml
areaId: "${area.id}"
areaName: "${area.name}"
status: "success"

l1Summary:
  gapsVerified: {count}
  evidenceFound: {count}
  confidenceLevel: "HIGH|MEDIUM|LOW"

verifiedGaps:
  - requirementId: "REQ-xxx"
    status: "COVERED|PARTIAL|MISSING"
    evidence:
      files: [...]
      matchCount: {n}
      snippets: [...]
    confidence: "HIGH|MEDIUM|LOW"

internalLoopStatus:
  iterations: {1-3}
  validationStatus: "passed"
  issuesResolved: [...]
\`\`\`
`,
    description: `Gap Verification: ${area.name}`
  }))

  // Wait for all agents (barrier synchronization)
  const results = await Promise.all(agents)

  return {
    agentCount,
    gapAreas,
    results,
    l1s: results.map(r => r.l1Summary),
    verifiedGaps: results.flatMap(r => r.verifiedGaps || []),
    iterations: results.map(r => r.internalLoopStatus?.iterations || 1)
  }
}
```

### 9.2 Phase 2: L1 Aggregation

```javascript
async function phase2_l1_aggregation(phase1Results) {
  // Validate each L1
  for (const l1 of phase1Results.l1s) {
    if (!l1 || !l1.gapsVerified) {
      throw new Error("Invalid L1 format from Explore Agent")
    }
  }

  // Merge all L1s
  const aggregatedL1 = {
    totalAgents: phase1Results.agentCount,
    areas: phase1Results.gapAreas.map((area, i) => ({
      id: area.id,
      name: area.name,
      gapsVerified: phase1Results.l1s[i].gapsVerified,
      evidenceFound: phase1Results.l1s[i].evidenceFound,
      confidenceLevel: phase1Results.l1s[i].confidenceLevel
    })),
    totalGapsVerified: phase1Results.verifiedGaps.length,
    overallConfidence: calculateOverallConfidence(phase1Results.l1s)
  }

  // Merge and deduplicate verified gaps
  const mergedGaps = mergeVerifiedGaps(phase1Results.verifiedGaps)

  return { aggregatedL1, mergedGaps }
}
```

### 9.3 Phase 3-A: L2 Horizontal Synthesis (P3)

```javascript
async function phase3a_l2_horizontal_synthesis(aggregatedL1, mergedGaps) {
  // Delegate to general-purpose agent for horizontal integration
  const synthesis = await Task({
    subagent_type: "general-purpose",
    model: "opus",
    prompt: `
## L2 Horizontal Synthesis for Gap Analysis

### Input
Aggregated L1 from ${aggregatedL1.totalAgents} Explore Agents:
${JSON.stringify(aggregatedL1, null, 2)}

Merged Gaps (${mergedGaps.length} total):
${mergedGaps.map(g => `- ${g.requirementId}: ${g.status} (${g.confidence})`).join('\n')}

### Task
1. **Cross-validate** gap classifications:
   - Do different agents agree on gap status?
   - Is evidence consistent across verification areas?
   - Are confidence levels justified?

2. **Identify contradictions**:
   - Same requirement classified differently
   - Conflicting evidence from different areas
   - Inconsistent confidence ratings

3. **Detect synthesis gaps**:
   - Requirements not verified by any agent
   - Areas with low confidence needing re-verification
   - Missing cross-references between code areas

4. **Synthesize** into unified gap report

### Validation Criteria
- cross_area_consistency
- evidence_agreement
- classification_accuracy

### Internal Feedback Loop (P6)
Self-validate synthesis, retry up to 3 times if issues found.

### Output Format
\`\`\`yaml
phase3a_L1:
  synthesisStatus: "success"
  consistencyScore: {0-100}
  contradictionsFound: {count}
  gapsUnified: {count}

phase3a_L2:
  unifiedGapReport:
    gaps: [...]  # Reconciled and validated
  crossAreaAnalysis:
    consistencyIssues: [...]
    resolvedContradictions: [...]
    confidenceAdjustments: [...]

phase3a_L3Path: ".agent/prompts/{slug}/rsil/iteration_{n}_phase3a_l3.md"

internalLoopStatus:
  iterations: {1-3}
  validationStatus: "passed"
\`\`\`
`,
    description: "L2 Horizontal Synthesis for Gap Analysis"
  })

  return synthesis
}
```

### 9.4 Phase 3-B: L3 Vertical Verification (P3)

```javascript
async function phase3b_l3_vertical_verification(phase3aResult, clarify) {
  // Read Phase 3-A L3 for deep verification
  const phase3aL3 = await Read({ file_path: phase3aResult.phase3a_L3Path })

  // Delegate to general-purpose agent for code-level verification
  const verification = await Task({
    subagent_type: "general-purpose",
    model: "opus",
    prompt: `
## L3 Code-Level Verification for Gap Analysis

### Input
Phase 3-A Synthesis L2:
${JSON.stringify(phase3aResult.phase3a_L2, null, 2)}

Phase 3-A L3 Detail:
${phase3aL3}

Original Requirements:
${clarify.requirements.map(r => `- ${r.id}: ${r.description}`).join('\n')}

### Task
1. **Verify evidence paths exist**:
   - Check if file paths in evidence are valid
   - Verify line numbers are accurate
   - Confirm code snippets match current codebase

2. **Validate gap classifications**:
   - Re-check COVERED items actually implement requirement
   - Re-check MISSING items have no implementation
   - Verify PARTIAL items have incomplete implementation

3. **Cross-reference with requirements**:
   - Does evidence actually satisfy requirement intent?
   - Are there subtle requirement misinterpretations?
   - Are completion criteria measurable?

### Validation Criteria
- evidence_path_validity
- classification_accuracy
- requirement_alignment

### Internal Feedback Loop (P6)
Self-validate verification, retry up to 3 times if issues found.

### Output Format
\`\`\`yaml
synthesisL1:
  verificationStatus: "success"
  evidenceValidity: {percentage}
  classificationAccuracy: {percentage}
  requirementAlignment: {percentage}

synthesisL2:
  verifiedGaps:
    - requirementId: "..."
      originalStatus: "..."
      verifiedStatus: "..."
      evidenceValid: true/false
      alignmentValid: true/false
  verificationNotes: [...]

synthesisL3Path: ".agent/prompts/{slug}/rsil/iteration_{n}.md"

unresolvedIssues: [...]  # Issues needing Main Agent review

internalLoopStatus:
  iterations: {1-3}
  validationStatus: "passed"
\`\`\`
`,
    description: "L3 Vertical Verification for Gap Analysis"
  })

  return verification
}
```

### 9.5 Phase 3.5: Main Agent Review Gate (P1)

```javascript
async function phase3_5_main_agent_review(synthesisResult, clarify, options) {
  // Main Agent reviews from holistic perspective
  const reviewCriteria = {
    requirement_alignment: {
      question: "Do gap findings match original requirements?",
      checks: ["requirement_interpretation", "scope_appropriate"]
    },
    design_flow_consistency: {
      question: "Is synthesis→gap analysis flow logical?",
      checks: ["evidence_chain", "classification_rationale"]
    },
    gap_detection: {
      question: "Are all gaps correctly identified?",
      checks: ["no_false_positives", "no_false_negatives"]
    },
    conclusion_clarity: {
      question: "Is decision (AUTO_REMEDIATE/ESCALATE) justified?",
      checks: ["threshold_application", "complexity_assessment"]
    }
  }

  const reviewIssues = []

  // Main Agent evaluates each criterion
  for (const [criterion, config] of Object.entries(reviewCriteria)) {
    const passed = evaluateCriterion(synthesisResult, criterion, config)
    if (!passed.result) {
      reviewIssues.push({
        type: criterion,
        description: passed.reason,
        severity: passed.severity,
        needsL3Review: passed.severity !== "LOW"
      })
    }
  }

  if (reviewIssues.length === 0) {
    console.log("✅ Phase 3.5: Main Agent review PASSED")
    return { reviewPassed: true, skipToPhase5: true }
  }

  console.log(`⚠️ Phase 3.5: ${reviewIssues.length} issues found`)
  return { reviewPassed: false, reviewIssues, proceedToPhase4: true }
}
```

### 9.6 Phase 4: Selective Feedback Loop (P4)

```javascript
async function phase4_selective_feedback(reviewResult, synthesisResult) {
  // Main Agent classifies issues by severity
  const classification = {
    directFix: [],      // LOW severity - fix directly
    agentDelegation: [] // MEDIUM+ - delegate
  }

  for (const issue of reviewResult.reviewIssues) {
    if (issue.severity === "LOW") {
      classification.directFix.push(issue)
    } else {
      classification.agentDelegation.push(issue)
    }
  }

  // Step 1: Main Agent direct fix for LOW severity
  let updatedSynthesis = { ...synthesisResult }
  for (const issue of classification.directFix) {
    console.log(`🔧 Direct fix: ${issue.type}`)
    updatedSynthesis = applyDirectFix(updatedSynthesis, issue)
  }

  // Step 2: Delegate MEDIUM+ issues to Explore agents
  if (classification.agentDelegation.length > 0) {
    const feedbackResults = await Promise.all(
      classification.agentDelegation.map(issue => Task({
        subagent_type: "Explore",
        model: "opus",
        prompt: `
## Issue Resolution for Gap Analysis

### Problem (WHAT)
- Type: ${issue.type}
- Severity: ${issue.severity}
- Description: ${issue.description}

### Task
1. Re-verify the specific gap or evidence
2. Correct the classification if needed
3. Provide additional evidence if missing

### Expected Output
Return corrected gap data in YAML format.

### Self-Validation (P6)
- Original issue resolved
- No new issues introduced
- Evidence accurate
`,
        description: `Resolve: ${issue.type}`
      }))
    )

    // Merge feedback results
    updatedSynthesis = mergeFeedbackResults(updatedSynthesis, feedbackResults)
  }

  return {
    directFixCount: classification.directFix.length,
    delegatedCount: classification.agentDelegation.length,
    issuesResolved: true,
    updatedSynthesis
  }
}
```

### 9.7 Phase 5: User Decision Confirmation (P5)

```javascript
async function phase5_user_confirmation(finalSynthesis, decision, options) {
  if (options.autoRemediate && decision.decision === "AUTO_REMEDIATE") {
    console.log("✅ Auto-remediate enabled, proceeding automatically")
    return { confirmed: true, action: decision.nextAction }
  }

  const response = await AskUserQuestion({
    questions: [{
      question: `RSIL Analysis Complete: ${decision.stats.total} gaps (${decision.stats.missing} missing, ${decision.stats.partial} partial). Decision: ${decision.decision}. Proceed?`,
      header: "RSIL Decision",
      options: [
        {
          label: decision.decision === "AUTO_REMEDIATE"
            ? "Auto-Remediate (Recommended)"
            : "Escalate to /clarify (Recommended)",
          description: decision.reason.join("; ")
        },
        {
          label: decision.decision === "AUTO_REMEDIATE"
            ? "Escalate Instead"
            : "Force Auto-Remediate",
          description: "Override the recommendation"
        },
        {
          label: "View L3 Details",
          description: "Review full gap analysis before deciding"
        }
      ],
      multiSelect: false
    }]
  })

  if (response.includes("View L3")) {
    const l3Content = await Read({ file_path: finalSynthesis.synthesisL3Path })
    console.log(l3Content)
    return await phase5_user_confirmation(finalSynthesis, decision, options)
  }

  if (response.includes("Recommended")) {
    return { confirmed: true, action: decision.nextAction }
  }

  // User chose override
  return {
    confirmed: true,
    action: decision.decision === "AUTO_REMEDIATE"
      ? `/clarify "Address RSIL gaps"`
      : `/orchestrate --workload ${options.workloadSlug}`
  }
}
```

### 9.8 Main Execution Protocol

```javascript
async function executeRSIL(args) {
  console.log("🚀 /rsil-plan V3.0.0 (EFL Pattern)")

  // 1. Parse arguments
  const options = parseArgs(args)
  const iteration = options.iteration || await detectIteration()
  const targetSlug = options.workload || await getActiveWorkloadSlug()

  // 2. Post-Compact Recovery Check
  if (isPostCompactSession()) {
    console.log("⚠️ Post-Compact detected, restoring context...")
    await restoreSkillContext(targetSlug, "rsil-plan")
  }

  // 3. Load all sources
  console.log("📚 Loading source documents...")
  const clarify = await loadClarifyRequirements(targetSlug)
  const synthesis = await loadSynthesisResults(targetSlug)

  if (!synthesis.decision || synthesis.decision.decision !== "ITERATE") {
    console.log("⚠️ No ITERATE decision found. /rsil-plan is for 2nd+ loops.")
    return { status: "skipped", reason: "No ITERATE decision" }
  }

  // 4. EFL Phase 1: Parallel Explore Agent Deployment
  console.log("📊 Phase 1: Deploying parallel Explore Agents...")
  const phase1 = await phase1_parallel_gap_verification(synthesis, clarify)

  // 5. EFL Phase 2: L1 Aggregation
  console.log("📋 Phase 2: Aggregating L1 summaries...")
  const phase2 = await phase2_l1_aggregation(phase1)

  // 6. EFL Phase 3-A: L2 Horizontal Synthesis
  console.log("🔄 Phase 3-A: L2 Horizontal Synthesis...")
  const phase3a = await phase3a_l2_horizontal_synthesis(phase2.aggregatedL1, phase2.mergedGaps)

  // 7. EFL Phase 3-B: L3 Vertical Verification
  console.log("🔍 Phase 3-B: L3 Vertical Verification...")
  const phase3b = await phase3b_l3_vertical_verification(phase3a, clarify)

  // 8. EFL Phase 3.5: Main Agent Review Gate
  console.log("🚦 Phase 3.5: Main Agent Review Gate...")
  const review = await phase3_5_main_agent_review(phase3b, clarify, options)

  let finalSynthesis = phase3b
  let feedbackLoops = 0

  // 9. EFL Phase 4: Selective Feedback Loop (if needed)
  if (!review.reviewPassed) {
    console.log("🔄 Phase 4: Selective Feedback Loop...")
    const phase4 = await phase4_selective_feedback(review, phase3b)
    finalSynthesis = phase4.updatedSynthesis
    feedbackLoops = 1
  }

  // 10. Make decision
  const classifiedGaps = finalSynthesis.synthesisL2.verifiedGaps
  const decision = makeDecision(classifiedGaps, options)

  // 11. Create remediation tasks
  console.log("📝 Creating remediation tasks...")
  const tasks = await createRemediationTasks(
    classifiedGaps.filter(g => g.verifiedStatus !== "COVERED"),
    iteration
  )

  // 12. EFL Phase 5: User Decision Confirmation
  console.log("✋ Phase 5: User Decision Confirmation...")
  const confirmation = await phase5_user_confirmation(finalSynthesis, decision, options)

  // 13. Generate output files
  const reportPath = `.agent/prompts/${targetSlug}/rsil/iteration_${iteration}.md`
  const planPath = `.agent/prompts/${targetSlug}/rsil/iteration_${iteration}_remediation.yaml`

  await Write({
    file_path: reportPath,
    content: generateGapReport(classifiedGaps, decision, tasks, iteration, {
      eflMetrics: {
        totalAgents: phase1.agentCount,
        parallelPhases: phase1.gapAreas.length,
        feedbackLoops,
        internalIterations: phase1.iterations.reduce((a, b) => a + b, 0)
      }
    })
  })

  // 14. Return L1 summary
  return {
    taskId: `rsil-${iteration}-${Date.now()}`,
    agentType: "rsil-plan",
    status: "success",
    summary: `RSIL complete: ${decision.stats.total} gaps, ${tasks.length} tasks, EFL verified`,

    priority: "HIGH",
    l2Path: reportPath,
    l3Path: planPath,
    requiresL2Read: false,

    decision: decision.decision,
    gapStats: decision.stats,
    tasksCreated: tasks.length,

    eflMetrics: {
      totalAgents: phase1.agentCount,
      parallelPhases: phase1.gapAreas.length,
      feedbackLoops,
      internalIterations: phase1.iterations.reduce((a, b) => a + b, 0),
      phase3aStatus: phase3a.phase3a_L1.synthesisStatus,
      phase3bStatus: phase3b.synthesisL1.verificationStatus,
      mainAgentReviewPassed: review.reviewPassed
    },

    nextActionHint: confirmation.action
  }
}
```

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


## 10. Integration Points

### 10.1 Pipeline Position

```
/clarify → /research → /planning → /orchestrate → Workers → /collect
                                                                │
                                                                ▼
                                                          /synthesis
                                                                │
                      ┌─────────────────────────────────────────┤
                      │                                         │
                 COMPLETE                                   ITERATE
                      │                                         │
                      ▼                                         ▼
              /commit-push-pr                            /rsil-plan ◄── THIS
                                                                │
                              ┌─────────────────────────────────┤
                              │                                 │
                      AUTO_REMEDIATE                        ESCALATE
                              │                                 │
                              ▼                                 ▼
                      /orchestrate                          /clarify
                     (remediation)                     (requirements update)
```

### 10.2 Input Dependencies

| Source | File | Data Used |
|--------|------|-----------|
| /clarify | `.agent/prompts/{slug}/clarify.yaml` | Original requirements |
| /research | `.agent/prompts/{slug}/research.md` | Codebase patterns, risks |
| /planning | `.agent/prompts/{slug}/plan.yaml` | Phases, completion criteria |
| /synthesis | `.agent/prompts/{slug}/synthesis/` | Gap matrix, decision |

### 10.3 Output Destinations

| Destination | File | Data Provided |
|-------------|------|---------------|
| Native Tasks | TaskCreate API | Remediation tasks |
| /orchestrate | `.agent/prompts/{slug}/rsil/` | Remediation plan YAML |
| /clarify | Gap descriptions | Requirements to clarify |

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


## 11. Error Handling

| Error | Detection | Recovery |
|-------|-----------|----------|
| No synthesis report | File not found | Prompt user to run /synthesis |
| Not ITERATE decision | Decision != ITERATE | Exit with skip message |
| Grep timeout | Large codebase | Use sampling, reduce scope |
| TaskCreate failure | API error | Retry once, then manual task |
| No requirements found | Empty clarify | Exit with error message |

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


## 12. Configuration

### Decision Thresholds

```javascript
const DEFAULT_CONFIG = {
  gapThreshold: 3,           // Max gaps for auto-remediate
  highComplexityThreshold: 1, // Max high-complexity gaps
  maxIterations: 5,          // Max RSIL iterations before force-escalate
  grepTimeout: 30000,        // Grep command timeout (ms)
  evidenceThreshold: {
    covered: 3,              // Matches for COVERED status
    partial: 1               // Matches for PARTIAL status
  }
}
```

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


## 13. Testing Checklist

- [ ] Load clarify requirements correctly
- [ ] Load synthesis report and parse gaps
- [ ] Grep patterns find expected code
- [ ] COVERED/PARTIAL/MISSING classification works
- [ ] TaskCreate generates valid remediation tasks
- [ ] Dependencies set up correctly
- [ ] AUTO_REMEDIATE decision at <=3 gaps
- [ ] ESCALATE decision at >3 gaps
- [ ] High complexity triggers ESCALATE
- [ ] Output files generated correctly
- [ ] User confirmation flow works
- [ ] --auto-remediate skips confirmation

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


## Parameter Module Compatibility (V2.1.0)

| Module | Status | Notes |
|--------|--------|-------|
| `model-selection.md` | ✅ | `model: opus` for code analysis |
| `context-mode.md` | ✅ | `context: standard` for task access |
| `tool-config.md` | ✅ | TaskCreate, TaskUpdate, Grep, Glob |
| `hook-config.md` | N/A | No Stop hook (decision-based exit) |
| `permission-mode.md` | N/A | Standard permissions |
| `task-params.md` | ✅ | Native Task integration |

### Version History

| Version | Date | Change |
|---------|------|--------|
| 3.0.0 | 2026-01-29 | **Full EFL Implementation** |
| | | P1-P6 complete |
| | | Phase 3-A: L2 Horizontal Synthesis |
| | | Phase 3-B: L3 Vertical Verification |
| | | Phase 3.5: Main Agent Review Gate |
| | | Phase 4: Selective Feedback Loop |
| | | Phase 5: User Decision Confirmation |
| | | Agent prompts include P6 self-validation |
| | | eflMetrics in L1 output |
| 1.2.0 | 2026-01-28 | Standalone Execution + Handoff Contract |
| 1.1.0 | 2026-01-27 | Workload-scoped output paths (V7.1 compatibility) |
| 1.0.0 | 2026-01-26 | Initial RSIL implementation |

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


## 14. Standalone Execution (V1.2.0)

### 14.1 독립 실행 모드

`/rsil-plan`은 독립적으로 gap 분석 수행 가능:

```bash
# 독립 실행 (synthesis 결과에서 workload 자동 감지)
/rsil-plan
/rsil-plan --iteration 2

# 명시적 workload 지정
/rsil-plan --workload user-auth-20260128-143022
```

### 14.2 Workload Context Resolution

```bash
# Source standalone module
source /home/palantir/.claude/skills/shared/skill-standalone.sh

# Initialize skill context
CONTEXT=$(init_skill_context "rsil-plan" "$ARGUMENTS" "")

# Resolution priority:
# 1. --workload argument → explicit workload
# 2. Active workload → .agent/prompts/_active_workload.yaml
# 3. Recent synthesis report → extract workload from path
# 4. Generate new workload → standalone mode
```

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


## 15. Handoff Contract (V1.2.0)

### 15.1 Handoff 매핑

| Decision | Next Skill | Arguments |
|----------|------------|-----------|
| `AUTO_REMEDIATE` | `/orchestrate` | `--workload {slug}` |
| `ESCALATE` | `/clarify` | (gaps description) |
| `COMPLETE` | `/commit-push-pr` | `--workload {slug}` |

### 15.2 Handoff YAML 출력

스킬 완료 시 iteration_{n}.md 끝에 다음 handoff 섹션을 추가:

```yaml
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

# Handoff Metadata (auto-generated)
handoff:
  skill: "rsil-plan"
  workload_slug: "user-auth-20260128-143022"
  status: "completed"
  timestamp: "2026-01-28T17:00:00Z"
  next_action:
    skill: "/orchestrate"  # or "/clarify"
    arguments: "--workload user-auth-20260128-143022"
    required: true
    reason: "Gap analysis complete, 2 remediation tasks created"
```

### 15.3 Decision-Based Routing

```bash
# AUTO_REMEDIATE 결정 시
/orchestrate --workload user-auth-20260128-143022

# ESCALATE 결정 시
/clarify "Address RSIL gaps: REQ-001, REQ-003"
```

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


**End of Skill Documentation**
