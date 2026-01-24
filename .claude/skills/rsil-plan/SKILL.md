---
name: rsil-plan
description: |
  Requirements-Synthesis Integration Loop (RSIL).
  Verifies synthesis results against original requirements.
  Performs code-level gap analysis and creates remediation plans.
user-invocable: true
disable-model-invocation: false
context: standard
model: opus
version: "1.0.0"
argument-hint: "[--iteration <n>] [--auto-remediate]"
allowed-tools:
  - Read
  - Grep
  - Glob
  - Task
  - TaskCreate
  - TaskUpdate
  - TaskList
  - AskUserQuestion
---

# /rsil-plan - Requirements-Synthesis Integration Loop

> **Version:** 1.0.0
> **Role:** Gap Analysis + Remediation Planning for 2nd+ Loop Iterations
> **Pipeline Position:** After /synthesis ITERATE decision
> **Model:** Opus (for comprehensive code analysis)

---

## 1. Purpose

The RSIL (Requirements-Synthesis Integration Loop) skill handles iteration cycles when `/synthesis` returns ITERATE:

1. **Multi-Source Loading** - Load outputs from clarify, research, planning, synthesis
2. **Code-Level Gap Verification** - Use Grep to find implementation evidence
3. **Gap Classification** - Mark each requirement as COVERED | PARTIAL | MISSING
4. **Remediation Task Generation** - Create Native Tasks for each gap
5. **Decision Logic** - Auto-remediate or escalate based on gap count/complexity

### When to Use

```
/synthesis
    │
    └── ITERATE → /rsil-plan ◄── THIS SKILL
                      │
                      ├── Gaps < 3 + Low Complexity → Auto-Remediate → /orchestrate
                      └── Otherwise → Escalate → /clarify
```

---

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

## 3. Multi-Source Loading

### 3.1 Source Files

```javascript
const sources = {
  clarify: ".agent/clarify/{slug}.yaml",
  research: ".agent/research/{slug}.md",
  planning: ".agent/plans/{slug}.yaml",
  synthesis: ".agent/outputs/synthesis/synthesis_report.md"
}
```

### 3.2 Load Requirements (from /clarify)

```javascript
async function loadClarifyRequirements() {
  // Find latest clarify log
  const clarifyLogs = await Glob({ pattern: ".agent/clarify/*.yaml" })

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
  const researchDocs = await Glob({ pattern: ".agent/research/*.md" })

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
  const planDocs = await Glob({ pattern: ".agent/plans/*.yaml" })

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
async function loadSynthesisResults() {
  const synthesisPath = ".agent/outputs/synthesis/synthesis_report.md"

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
- Research: .agent/research/
- Planning: .agent/plans/
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
    nextAction = "/orchestrate --plan-slug rsil-remediation"
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

## 8. Output Files

### 8.1 Gap Analysis Report

**Path:** `.agent/rsil/iteration_{n}.md`

```markdown
# RSIL Gap Analysis Report - Iteration {n}

> Generated: {timestamp}
> Previous Iteration: {n-1 or "Initial"}
> Coverage Before: {previous_coverage}%
> Coverage After: TBD

---

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

## Remediation Tasks Created

| Task ID | Requirement | Complexity | Status |
|---------|-------------|------------|--------|
| #101 | REQ-001 | high | pending |
| #102 | REQ-002 | medium | pending |

---

## Next Action

\`\`\`bash
{next_action_command}
\`\`\`
```

### 8.2 Remediation Plan

**Path:** `.agent/rsil/iteration_{n}_remediation.yaml`

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

## 9. Execution Protocol

### 9.1 Main Flow

```javascript
async function executeRSIL(args) {
  console.log("🔄 Starting RSIL Gap Analysis...")

  // 1. Parse arguments
  const options = parseArgs(args)
  const iteration = options.iteration || await detectIteration()

  console.log(`Iteration: ${iteration}`)

  // 2. Load all sources
  console.log("\n📚 Loading source documents...")
  const clarify = await loadClarifyRequirements()
  const research = await loadResearchFindings()
  const planning = await loadPlanningDocument()
  const synthesis = await loadSynthesisResults()

  if (!synthesis.decision || synthesis.decision.decision !== "ITERATE") {
    console.log("⚠️ No ITERATE decision found. /rsil-plan is for 2nd+ loops.")
    return { status: "skipped", reason: "No ITERATE decision" }
  }

  // 3. Code-level gap verification
  console.log("\n🔍 Verifying gaps with code analysis...")
  const verifiedGaps = await verifyGapsWithCode(
    clarify.requirements,
    synthesis
  )

  // 4. Classify gaps
  console.log("\n📊 Classifying gaps...")
  const classifiedGaps = verifiedGaps.map(g => classifyGap(
    g,
    g.evidence,
    synthesis.matrix.find(m => m.requirementId === g.requirementId)
  ))

  // 5. Make decision
  console.log("\n⚖️ Making decision...")
  const decision = makeDecision(classifiedGaps, options)

  // 6. User confirmation
  const confirmation = await confirmDecision(decision, options)

  if (confirmation.action === "show_details") {
    // Show full report and re-prompt
    await showDetailedReport(classifiedGaps)
    return await executeRSIL(args) // Recursive call
  }

  // 7. Create remediation tasks
  console.log("\n📝 Creating remediation tasks...")
  const tasks = await createRemediationTasks(
    classifiedGaps.filter(g => g.status !== "COVERED"),
    iteration
  )

  // 8. Generate output files
  console.log("\n💾 Generating output files...")
  const reportPath = await generateGapReport(
    classifiedGaps,
    decision,
    tasks,
    iteration
  )
  const planPath = await generateRemediationPlan(
    classifiedGaps,
    decision,
    tasks,
    iteration
  )

  // 9. Final output
  console.log(`
=== RSIL Analysis Complete ===

📊 Gap Summary:
   - COVERED: ${decision.stats.total - decision.stats.missing - decision.stats.partial}
   - PARTIAL: ${decision.stats.partial}
   - MISSING: ${decision.stats.missing}

⚖️ Decision: ${decision.decision}
   ${decision.reason.join('\n   ')}

📝 Reports:
   - Gap Analysis: ${reportPath}
   - Remediation Plan: ${planPath}

🎯 Next Action:
   ${confirmation.action}
`)

  return {
    status: "success",
    decision: decision.decision,
    gapCount: decision.stats.total,
    tasksCreated: tasks.length,
    reportPath: reportPath,
    planPath: planPath,
    nextAction: confirmation.action
  }
}
```

---

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
| /clarify | `.agent/clarify/*.yaml` | Original requirements |
| /research | `.agent/research/*.md` | Codebase patterns, risks |
| /planning | `.agent/plans/*.yaml` | Phases, completion criteria |
| /synthesis | `.agent/outputs/synthesis/` | Gap matrix, decision |

### 10.3 Output Destinations

| Destination | File | Data Provided |
|-------------|------|---------------|
| Native Tasks | TaskCreate API | Remediation tasks |
| /orchestrate | `.agent/rsil/` | Remediation plan YAML |
| /clarify | Gap descriptions | Requirements to clarify |

---

## 11. Error Handling

| Error | Detection | Recovery |
|-------|-----------|----------|
| No synthesis report | File not found | Prompt user to run /synthesis |
| Not ITERATE decision | Decision != ITERATE | Exit with skip message |
| Grep timeout | Large codebase | Use sampling, reduce scope |
| TaskCreate failure | API error | Retry once, then manual task |
| No requirements found | Empty clarify | Exit with error message |

---

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

| Version | Change |
|---------|--------|
| 1.0.0 | Initial RSIL implementation |

---

**End of Skill Documentation**
