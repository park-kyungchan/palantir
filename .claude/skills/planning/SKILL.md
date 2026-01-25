---
name: planning
description: |
  Generate YAML planning documents from research results.
  Includes Plan Agent review loop for quality assurance.
  Outputs structured execution blueprints for /orchestrate.
user-invocable: true
disable-model-invocation: false
context: standard
model: opus
version: "1.0.0"
argument-hint: "[--research-slug <slug>] [--auto-approve]"
allowed-tools:
  - Read
  - Write
  - Task
  - Glob
  - Grep
  - AskUserQuestion
hooks:
  PreToolUse:
    - type: command
      command: "/home/palantir/.claude/hooks/planning-preflight.sh"
      timeout: 30000
      matcher: "Task"
  Stop:
    - type: command
      command: "/home/palantir/.claude/hooks/planning-finalize.sh"
      timeout: 150000
---

# /planning - YAML Planning Document Generator

> **Version:** 1.0.0
> **Role:** Planning Document Generation with Plan Agent Review
> **Pipeline Position:** After /research, Before /orchestrate

---

## 1. Purpose

Generate structured YAML planning documents from research outputs that:
1. Parse research findings from `.agent/research/{slug}.md`
2. Load requirements from `.agent/clarify/{slug}.yaml`
3. Structure implementation phases with dependencies
4. Validate through Plan Agent review loop
5. Output execution-ready blueprints for `/orchestrate`

### Pipeline Integration

```
/clarify → /research → [/planning] → /orchestrate → Workers → /synthesis
                          │
                          ├── Load research + clarify outputs
                          ├── Generate planning document YAML
                          ├── Plan Agent review loop
                          └── Output: .agent/plans/{slug}.yaml
```

---

## 2. Invocation

### User Syntax

```bash
# With research slug
/planning --research-slug enhanced_pipeline_skills_20260124

# Auto-approve (skip user confirmation for Plan Agent approval)
/planning --research-slug my-feature --auto-approve

# Interactive (prompts for slug if not provided)
/planning
```

### Arguments

| Argument | Required | Description |
|----------|----------|-------------|
| `--research-slug` | No | Research document slug to load |
| `--auto-approve` | No | Skip user confirmation after Plan Agent approval |

---

## 3. Input Processing

### 3.1 Source Files

```javascript
// Required input files
const researchPath = `.agent/research/${slug}.md`
const clarifyPath = `.agent/clarify/${slug}.yaml`

// Optional: previous planning iterations
const previousPlanPath = `.agent/plans/${slug}.yaml`
```

### 3.2 Research Loading

```javascript
async function loadResearch(slug) {
  // 1. Read research document
  const research = await Read({ file_path: `.agent/research/${slug}.md` })

  // 2. Extract key sections
  const sections = {
    codebaseAnalysis: extractSection(research, '## Codebase Analysis'),
    externalResearch: extractSection(research, '## External Research'),
    riskAssessment: extractSection(research, '## Risk Assessment'),
    recommendations: extractSection(research, '## Recommendations')
  }

  return sections
}
```

### 3.3 Clarify Loading

```javascript
async function loadClarify(slug) {
  // 1. Read clarify YAML
  const clarify = await Read({ file_path: `.agent/clarify/${slug}.yaml` })

  // 2. Parse requirements and extract workload_id (handle nested structures)
  // Priority: metadata.workload_id > workload_id > metadata.id > slug
  const workloadId = clarify.metadata?.workload_id
    || clarify.workload_id
    || clarify.metadata?.id
    || slug

  return {
    originalRequest: clarify.original_request,
    workloadId: workloadId,  // Properly extracted workload_id
    rounds: clarify.rounds,
    finalDecision: clarify.final_decision,
    requirements: extractRequirements(clarify.rounds)
  }
}
```

---

## 4. Planning Document Schema

### 4.1 Full Schema

```yaml
# =============================================================================
# Planning Document Schema
# =============================================================================

metadata:
  id: "string"              # Unique planning document ID (slug-based)
  workload_id: "string"     # Workload identifier (format: {topic}_{YYYYMMDD}_{HHMMSS})
  version: "string"         # Semantic version (1.0.0)
  created_at: "datetime"    # ISO 8601 timestamp
  updated_at: "datetime"    # Last modification timestamp
  status: "string"          # draft | reviewing | approved | superseded
  research_source: "string" # Path to research document
  clarify_source: "string"  # Path to clarify document

project:
  name: "string"            # Human-readable project name
  description: "string"     # Multi-line project description
  objectives:
    - "string"              # List of project objectives

# =============================================================================
# PHASES - Implementation Breakdown
# =============================================================================

phases:
  - id: "string"                    # Unique phase ID (e.g., phase1-setup)
    name: "string"                  # Human-readable phase name
    description: "string"           # Multi-line phase description
    priority: "string"              # P0 (critical) | P1 (high) | P2 (medium)
    owner: "string"                 # Suggested terminal owner
    dependencies: ["string"]        # List of phase IDs this depends on
    estimatedComplexity: "string"   # low | medium | high

    targetFiles:                    # Files this phase will modify
      - path: "string"              # Absolute or relative file path
        action: "string"            # create | modify | delete
        sections: ["string"]        # Specific sections to modify

    referenceFiles:                 # Files to read for context
      - path: "string"
        reason: "string"

    completionCriteria:             # Must all be met for phase completion
      - "string"

    verificationSteps:              # Automated verification commands
      - command: "string"
        expected: "string"

# =============================================================================
# DEPENDENCIES - Explicit Dependency Graph
# =============================================================================

dependencies:
  internal:                         # Dependencies between phases
    - from: "string"                # Phase ID that depends
      to: "string"                  # Phase ID being depended on
      reason: "string"              # Why this dependency exists

  external:                         # External system dependencies
    - name: "string"
      version: "string"
      reason: "string"

# =============================================================================
# PLAN AGENT REVIEW
# =============================================================================

planAgentReview:
  status: "string"                  # pending | approved | rejected | iterating
  reviewedAt: "datetime"            # When review was completed
  reviewedBy: "string"              # Agent/reviewer identifier
  iterationCount: "number"          # Number of review iterations
  comments:
    - round: "number"
      comment: "string"
      resolution: "string"

  approvalCriteria:                 # What Plan Agent verifies
    - "string"

# =============================================================================
# EXECUTION NOTES
# =============================================================================

executionNotes:
  parallelization: "string"         # Which phases can run in parallel
  estimatedDuration: "string"       # Total estimated time
  criticalPath: "string"            # Longest dependency chain
  riskMitigation: "string"          # Known risks and mitigations
```

### 4.2 Minimal Example

```yaml
metadata:
  id: "add-auth-feature"
  workload_id: "user-authentication_20260125_143022"
  version: "1.0.0"
  status: "draft"

project:
  name: "Add User Authentication"
  description: |
    Implement JWT-based authentication with refresh tokens.
  objectives:
    - "Secure API endpoints"
    - "Implement login/logout flow"

phases:
  - id: "phase1-jwt-setup"
    name: "JWT Library Setup"
    priority: "P0"
    dependencies: []
    targetFiles:
      - path: "src/auth/jwt.ts"
        action: "create"
    completionCriteria:
      - "JWT signing and verification functions implemented"

  - id: "phase2-middleware"
    name: "Auth Middleware"
    priority: "P0"
    dependencies: ["phase1-jwt-setup"]
    targetFiles:
      - path: "src/middleware/auth.ts"
        action: "create"
    completionCriteria:
      - "Middleware protects routes requiring authentication"

planAgentReview:
  status: "pending"
```

---

## 5. Plan Agent Review Process

### 5.1 Review Delegation

```javascript
async function requestPlanAgentReview(planningDoc) {
  const review = await Task({
    subagent_type: "Plan",
    prompt: `
## Plan Review Request

Review this planning document for implementation readiness:

\`\`\`yaml
${planningDoc}
\`\`\`

## Validation Checklist

1. **Dependency Graph**: Is it acyclic? No circular dependencies?
2. **Completion Criteria**: Does each phase have measurable criteria?
3. **Target Files**: Do paths exist or is creation justified?
4. **Risk Assessment**: Are risks identified and mitigations proposed?
5. **Parallelization**: Are parallel opportunities identified?

## Output Format

Return ONE of:
- "APPROVED" - Document is ready for /orchestrate
- "NEEDS_REVISION" with specific issues list:
  \`\`\`
  Issues:
  1. [Phase X]: Missing completion criteria
  2. [Dependencies]: Circular dependency between A and B
  3. [Risk]: No mitigation for external API failure
  \`\`\`
`,
    description: "Review planning document"
  })

  return {
    status: review.includes("APPROVED") ? "approved" : "needs_revision",
    comments: extractIssues(review)
  }
}
```

### 5.2 Review Loop

```javascript
async function reviewLoop(planningDoc, maxIterations = 3) {
  let iteration = 0
  let currentDoc = planningDoc

  while (iteration < maxIterations) {
    iteration++

    // Request Plan Agent review
    const review = await requestPlanAgentReview(currentDoc)

    // Update review status
    currentDoc = updateReviewSection(currentDoc, {
      status: review.status,
      iterationCount: iteration,
      comments: review.comments
    })

    if (review.status === "approved") {
      return { approved: true, document: currentDoc }
    }

    // Address issues
    currentDoc = await addressIssues(currentDoc, review.comments)
  }

  // Max iterations reached - escalate to user
  return {
    approved: false,
    document: currentDoc,
    escalation: "Max review iterations reached. Manual review required."
  }
}
```

### 5.3 Issue Resolution

```javascript
async function addressIssues(planningDoc, issues) {
  for (const issue of issues) {
    // Categorize issue
    if (issue.type === "missing_criteria") {
      planningDoc = addCompletionCriteria(planningDoc, issue.phaseId)
    } else if (issue.type === "circular_dependency") {
      planningDoc = resolveDependency(planningDoc, issue.phases)
    } else if (issue.type === "missing_risk") {
      planningDoc = addRiskMitigation(planningDoc, issue.description)
    }
  }

  return planningDoc
}
```

---

## 6. Execution Protocol

### 6.1 Main Flow

```javascript
async function executePlanning(args) {
  // 1. Parse arguments
  const { slug, autoApprove } = parseArgs(args)

  // 2. Determine slug if not provided
  const targetSlug = slug || await promptForSlug()

  // 3. Load source documents
  console.log("📚 Loading research and clarify documents...")
  const research = await loadResearch(targetSlug)
  const clarify = await loadClarify(targetSlug)

  // 3.5 Gate 3: Pre-flight Checks (Shift-Left Validation)
  console.log("🔍 Running Gate 3: Pre-flight checks...")
  const preflightResult = await runPreflightChecks(targetSlug, research, clarify)
  if (preflightResult.result === "failed") {
    console.log("❌ Gate 3 FAILED - Fix errors before proceeding:")
    preflightResult.errors.forEach(e => console.log(`   - ${e}`))
    return { status: "gate3_failed", errors: preflightResult.errors }
  }
  if (preflightResult.warnings.length > 0) {
    console.log("⚠️  Gate 3 warnings:")
    preflightResult.warnings.forEach(w => console.log(`   - ${w}`))
  }
  console.log("✅ Gate 3 PASSED")

  // 4. Generate initial planning document
  console.log("📝 Generating planning document...")
  const planningDoc = await generatePlanningDocument(research, clarify)

  // 5. Plan Agent review loop
  console.log("🔍 Starting Plan Agent review...")
  const reviewResult = await reviewLoop(planningDoc)

  // 6. User confirmation (unless auto-approve)
  if (!autoApprove && reviewResult.approved) {
    const confirmed = await AskUserQuestion({
      questions: [{
        question: "Plan Agent has approved the planning document. Proceed?",
        header: "Approval",
        options: [
          { label: "Yes, save and proceed", description: "Save planning document" },
          { label: "Review manually", description: "View full document first" }
        ],
        multiSelect: false
      }]
    })

    if (!confirmed.includes("Yes")) {
      return { action: "manual_review", document: reviewResult.document }
    }
  }

  // 7. Save planning document (Workload-scoped)
  const workloadDir = `.agent/prompts/${targetSlug}`
  await Bash({ command: `mkdir -p ${workloadDir}`, description: 'Ensure workload dir' })
  const outputPath = `${workloadDir}/plan.yaml`
  await Write({
    file_path: outputPath,
    content: reviewResult.document
  })

  // 8. Output summary
  return {
    status: reviewResult.approved ? "approved" : "escalated",
    path: outputPath,
    nextStep: "/orchestrate --plan-slug " + targetSlug
  }
}
```

### 6.2 Planning Document Generation

```javascript
async function generatePlanningDocument(research, clarify) {
  const timestamp = new Date().toISOString()
  const slug = generateSlug(clarify.originalRequest)

  // Extract phases from research recommendations
  const phases = extractPhases(research.recommendations)

  // Build dependency graph
  const dependencies = buildDependencyGraph(phases)

  // Generate YAML
  const document = `
# ${clarify.originalRequest}
# Generated: ${timestamp}
# Status: draft (awaiting Plan Agent review)

metadata:
  id: "${slug}"
  workload_id: "${clarify.workloadId}"
  version: "1.0.0"
  created_at: "${timestamp}"
  updated_at: "${timestamp}"
  status: "draft"
  research_source: ".agent/research/${slug}.md"
  clarify_source: ".agent/clarify/${slug}.yaml"

project:
  name: "${clarify.originalRequest.substring(0, 50)}"
  description: |
    ${clarify.finalDecision.description || clarify.originalRequest}
  objectives:
${clarify.requirements.map(r => `    - "${r}"`).join('\n')}

phases:
${phases.map(p => formatPhase(p)).join('\n')}

dependencies:
  internal:
${dependencies.map(d => `    - from: "${d.from}"
      to: "${d.to}"
      reason: "${d.reason}"`).join('\n')}
  external: []

planAgentReview:
  status: "pending"
  reviewedAt: null
  reviewedBy: null
  iterationCount: 0
  comments: []
  approvalCriteria:
    - "All phases have clear completion criteria"
    - "Dependencies form acyclic graph"
    - "Target files are specified for each phase"
    - "Risk mitigation strategies identified"

executionNotes:
  parallelization: |
    ${identifyParallelPhases(phases)}
  criticalPath: |
    ${calculateCriticalPath(phases, dependencies)}
`

  return document
}
```

---

## 7. Output Format (L1/L2/L3)

### L1 - Summary (Default)

```
✅ Planning Complete

📄 Document: .agent/plans/enhanced-pipeline-skills.yaml
📊 Status: approved (Plan Agent reviewed)
🔄 Phases: 6 phases identified
⏱️ Estimated: ~2 hours (parallel execution)

Next: /orchestrate --plan-slug enhanced-pipeline-skills
```

### L2 - Phase Overview

```
✅ Planning Complete

📄 Document: .agent/plans/enhanced-pipeline-skills.yaml

Phases:
  1. phase1-research-skill (P0) - Terminal-B
     └─ Create /research skill with codebase analysis
  2. phase2-planning-skill (P0) - Terminal-C
     └─ Create /planning skill with Plan Agent review
  3. phase3a-research-hook (P1) - Terminal-B [depends: phase1]
     └─ Create research-finalize.sh hook
  4. phase3b-planning-hook (P1) - Terminal-C [depends: phase2]
     └─ Create planning-finalize.sh hook
  5. phase4-rsil-plan (P0) - Terminal-B [depends: phase1, phase2]
     └─ Create /rsil-plan skill
  6. phase5-testing (P0) - Both [depends: all above]
     └─ E2E pipeline testing

Plan Agent Review: ✅ Approved (2 iterations)

Next: /orchestrate --plan-slug enhanced-pipeline-skills
```

### L3 - Full Detail

Outputs the complete YAML planning document.

---

## 8. Integration Points

### 8.1 Upstream: /research

```bash
# /research outputs to .agent/research/{slug}.md
# /planning reads this file for context
```

### 8.2 Downstream: /orchestrate

```bash
# /planning outputs to .agent/plans/{slug}.yaml
# /orchestrate reads this to create Native Tasks
/orchestrate --plan-slug enhanced-pipeline-skills
```

### 8.3 Pipeline Diagram

```
/clarify ─────────────────────────────────────────────────────────────┐
    │                                                                 │
    ▼                                                                 │
/research ───────────────────────────────────────────────────────┐    │
    │                                                            │    │
    ▼                                                            │    │
/planning ◀──────────────────────────────────────────────────────┘    │
    │                                                                 │
    ├── Load .agent/research/{slug}.md                                │
    ├── Load .agent/clarify/{slug}.yaml ◀─────────────────────────────┘
    ├── Generate planning document
    ├── Plan Agent review loop
    │       │
    │       ├── APPROVED → Save .agent/plans/{slug}.yaml
    │       │                   │
    │       └── REJECTED → Iterate (max 3) or Escalate
    │
    ▼
/orchestrate
    │
    ├── Read .agent/plans/{slug}.yaml
    ├── TaskCreate for each phase
    ├── TaskUpdate(addBlockedBy) for dependencies
    └── Generate worker prompts
```

---

## 9. Gate 3: Pre-flight Checks Integration

### 9.1 Pre-flight Check Function

```javascript
async function runPreflightChecks(slug, research, clarify) {
  // Source: .claude/skills/shared/validation-gates.sh -> pre_flight_checks()

  const warnings = []
  const errors = []

  // 1. Validate target files from research recommendations
  if (research.recommendations) {
    const targetFiles = extractTargetFiles(research.recommendations)

    for (const file of targetFiles) {
      const fullPath = `${WORKSPACE_ROOT}/${file}`
      const parentDir = path.dirname(fullPath)

      if (!fs.existsSync(fullPath) && !fs.existsSync(parentDir)) {
        warnings.push(`Target file parent directory missing: ${file}`)
      }
    }
  }

  // 2. Check for circular dependencies in proposed phases
  const phases = extractPhases(research.recommendations)
  const cycles = detectCircularDependencies(phases)

  if (cycles.length > 0) {
    errors.push(`Circular dependencies detected: ${cycles.join(' -> ')}`)
  }

  // 3. Validate requirement feasibility
  if (clarify.requirements) {
    for (const req of clarify.requirements) {
      if (req.length < 10) {
        warnings.push(`Requirement may be too vague: "${req}"`)
      }
    }
  }

  // Determine result
  let result = "passed"
  if (errors.length > 0) result = "failed"
  else if (warnings.length > 0) result = "passed_with_warnings"

  return { gate: "PLANNING", result, warnings, errors }
}
```

### 9.2 Circular Dependency Detection

```javascript
function detectCircularDependencies(phases) {
  const graph = new Map()
  const visited = new Set()
  const recursionStack = new Set()
  const cycles = []

  // Build adjacency list
  for (const phase of phases) {
    graph.set(phase.id, phase.dependencies || [])
  }

  function dfs(node, path) {
    visited.add(node)
    recursionStack.add(node)

    for (const neighbor of (graph.get(node) || [])) {
      if (!visited.has(neighbor)) {
        dfs(neighbor, [...path, neighbor])
      } else if (recursionStack.has(neighbor)) {
        cycles.push([...path, neighbor])
      }
    }

    recursionStack.delete(node)
  }

  for (const [node] of graph) {
    if (!visited.has(node)) {
      dfs(node, [node])
    }
  }

  return cycles
}
```

---

## 10. Error Handling

| Error | Detection | Recovery |
|-------|-----------|----------|
| Research not found | File doesn't exist | Prompt user to run /research first |
| Clarify not found | File doesn't exist | Prompt user to run /clarify first |
| Invalid YAML | Parse error | Log error, show line number |
| Plan Agent timeout | Task timeout | Retry once, then escalate |
| Circular dependency | Graph analysis | Show cycle, ask user to break |
| **Gate 3 failed** | Pre-flight check errors | Fix errors before proceeding |

---

## 10. Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `PLANNING_MAX_ITERATIONS` | `3` | Max Plan Agent review iterations |
| `PLANNING_AUTO_APPROVE` | `false` | Skip user confirmation |

### Settings

```json
{
  "planning": {
    "defaultSlugPattern": "{date}_{topic}",
    "maxPhases": 10,
    "requireRiskAssessment": true
  }
}
```

---

## 11. Testing Checklist

- [ ] Load research document from `.agent/research/`
- [ ] Load clarify document from `.agent/clarify/`
- [ ] Generate valid YAML planning document
- [ ] Plan Agent review identifies missing criteria
- [ ] Review loop iterates until approved
- [ ] Circular dependency detection works
- [ ] Output saved to `.agent/plans/`
- [ ] L1/L2/L3 output formats work
- [ ] Stop hook finalizes correctly

---

## Parameter Module Compatibility (V2.1.0)

| Module | Status | Notes |
|--------|--------|-------|
| `model-selection.md` | ✅ | `model: opus` for complex planning |
| `context-mode.md` | ✅ | `context: standard` |
| `tool-config.md` | ✅ | Task delegation to Plan Agent |
| `hook-config.md` | ✅ | Stop hook for finalization |
| `permission-mode.md` | N/A | No elevated permissions needed |
| `task-params.md` | ✅ | Generates TaskCreate-ready phases |

---

**End of Skill Documentation**
