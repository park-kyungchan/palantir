# Enhanced Feedback Loop (EFL) Pattern Template

> **Version:** 1.0.0
> **Purpose:** Standardized EFL implementation guide for all skills
> **Source:** `.agent/prompts/enhanced-feedback-loop-pattern-20260127/plan-final.yaml`

---

## 1. Frontmatter Configuration

### 1.1 Required Fields

```yaml
---
name: {skill-name}
description: |
  {One-line summary}

  Core Capabilities:
  - {Capability 1}: {Description}
  - {Capability 2}: {Description}
  - {Capability 3}: {Description}

  Output Format:
  - L1: {Summary purpose}
  - L2: {Detail purpose}
  - L3: {Deep-dive purpose}

  Pipeline Position:
  - {Upstream/Downstream relationships}
user-invocable: true
disable-model-invocation: true  # REQUIRED for consistency
context: fork                    # REQUIRED for consistency
model: opus
version: "3.0.0"
argument-hint: "{argument hints}"
allowed-tools:
  - Read
  - Write    # REQUIRED for L1/L2/L3 system
  - Task
  - Glob
  - Grep
  - AskUserQuestion
  - {skill-specific tools}
hooks:
  Setup:
    - type: command              # REQUIRED format
      command: "{setup command}"
      timeout: 5000
  PreToolUse:
    - type: command
      command: "{validation hook}"
      timeout: 30000
      matcher: "Task"
  Stop:
    - type: command
      command: "{finalize hook}"
      timeout: 150000
---
```

### 1.2 P1: Agent Delegation Config

```yaml
# P1: Skill as Sub-Orchestrator
agent_delegation:
  enabled: true
  max_sub_agents: 4
  delegation_strategy: "auto"  # or "phase-based", "scope-based", "complexity-based"
  strategies:
    phase_based:
      description: "Delegate by implementation phase"
      use_when: "Multi-phase implementation"
    scope_based:
      description: "Delegate by analysis scope"
      use_when: "Large codebase analysis"
    complexity_based:
      description: "Delegate by task complexity"
      use_when: "Mixed complexity tasks"
  description: |
    This skill operates as a Sub-Orchestrator.
    It delegates work to Agents rather than executing directly.
```

### 1.3 P2: Parallel Agent Config

```yaml
# P2: Parallel Agent Deployment
parallel_agent_config:
  enabled: true
  complexity_detection: "auto"
  agent_count_by_complexity:
    simple: 1
    moderate: 2
    complex: 3
    very_complex: 4
  synchronization_strategy: "barrier"  # Wait for all agents
  aggregation_strategy: "merge"        # Merge all outputs
  description: |
    Deploy multiple agents in parallel for comprehensive analysis.
    Agent count scales with detected complexity.
```

---

## 2. Execution Flow (EFL Phases)

### 2.1 Phase Structure Overview

```
Phase 1: Parallel Agent Deployment (P2)
    │
    ▼
Phase 2: L1 Aggregation
    │
    ▼
Phase 3-A: L2 Horizontal Synthesis (P3)
    │
    ▼
Phase 3-B: L3 Vertical Verification (P3)
    │
    ▼
Phase 3.5: Main Agent Review Gate (P1)
    │
    ├── PASS → Phase 5
    └── ISSUES → Phase 4
          │
          ▼
Phase 4: Selective Feedback Loop (P4)
    │
    ▼
Phase 5: Repeat Until Approval (P5)
    │
    ▼
Output: L1/L2/L3
```

### 2.2 Phase 1: Parallel Agent Deployment

```javascript
async function phase1_parallel_deployment(input) {
  // Divide work into areas
  const areas = divideIntoAreas(input)

  // Deploy parallel agents with P6 self-validation
  const agents = areas.map(area => Task({
    subagent_type: "{appropriate-agent-type}",
    model: "opus",
    prompt: `
## Analysis Request
${area.name}: ${area.description}

## Internal Feedback Loop (P6 - REQUIRED)
1. Perform analysis
2. Self-validate results:
   - Validation Criteria: ${area.validationCriteria.join(", ")}
3. If issues found, retry (max 3 times)
4. Output in L1/L2/L3 format after validation passes

## Output Format
Return:
- L1: 500-token summary (for main context)
- L2: 2000-token detail (for synthesis)
- L3: File path for deep-dive

## Internal Loop Status (REQUIRED)
Include in output:
- internalIterations: {count}
- validationStatus: {passed|failed}
- resolvedIssues: [{issue descriptions}]
`
  }))

  // Wait for all agents (barrier synchronization)
  const results = await Promise.all(agents)

  return {
    l1s: results.map(r => r.l1),
    l2Paths: results.map(r => r.l2Path),
    l3Paths: results.map(r => r.l3Path),
    iterations: results.map(r => r.internalIterations)
  }
}
```

### 2.3 Phase 2: L1 Aggregation

```javascript
async function phase2_l1_aggregation(phase1Results) {
  // Validate each L1
  for (const l1 of phase1Results.l1s) {
    validateL1Format(l1)
  }

  // Merge all L1s
  const aggregatedL1 = {
    totalAgents: phase1Results.l1s.length,
    summaries: phase1Results.l1s.map((l1, i) => ({
      area: l1.area,
      status: l1.status,
      keyFindings: l1.keyFindings,
      l2Path: phase1Results.l2Paths[i]
    })),
    overallStatus: determineOverallStatus(phase1Results.l1s)
  }

  return aggregatedL1
}
```

### 2.4 Phase 3-A: L2 Horizontal Synthesis

```javascript
async function phase3a_l2_synthesis(aggregatedL1, l2Paths) {
  // Read all L2 files for horizontal integration
  const l2Contents = await Promise.all(
    l2Paths.map(path => Read({ file_path: path }))
  )

  // Delegate to general-purpose agent for synthesis
  const synthesis = await Task({
    subagent_type: "general-purpose",
    model: "opus",
    prompt: `
## L2 Horizontal Synthesis Request

### Input
Aggregated L1:
${JSON.stringify(aggregatedL1, null, 2)}

L2 Contents:
${l2Contents.map((c, i) => `### Area ${i+1}\n${c}`).join('\n\n')}

### Task
1. Cross-validate all L2 analyses for consistency
2. Identify contradictions between areas
3. Detect gaps at area connection points
4. Synthesize into unified L2

### Validation Criteria
- cross_area_consistency
- analysis_completeness
- information_accuracy

### Internal Feedback Loop (P6)
Self-validate synthesis, retry up to 3 times if issues found.

### Output
- phase3a_L1: 500-token synthesis summary
- phase3a_L2: 2000-token synthesis detail
- phase3a_L3Path: File path for deep-dive
- l2SynthesisData: Data for Phase 3-B
`
  })

  return synthesis
}
```

### 2.5 Phase 3-B: L3 Vertical Verification

```javascript
async function phase3b_l3_verification(phase3aResult, l3Paths) {
  // Read Phase 3-A output and all L3s
  const phase3aL3 = await Read({ file_path: phase3aResult.phase3a_L3Path })
  const l3Contents = await Promise.all(
    l3Paths.map(path => Read({ file_path: path }))
  )

  // Delegate to general-purpose agent for code-level verification
  const verification = await Task({
    subagent_type: "general-purpose",
    model: "opus",
    prompt: `
## L3 Code-Level Verification Request

### Input
Phase 3-A Synthesis:
${phase3aResult.phase3a_L2}

L3 Code-Level Evidence:
${l3Contents.map((c, i) => `### L3 ${i+1}\n${c}`).join('\n\n')}

### Task
1. Verify L2 claims match actual code
2. Check file:line references are accurate
3. Validate logic analysis correctness
4. Verify dependency analysis completeness

### Validation Criteria
- code_reference_accuracy
- logic_analysis_accuracy
- dependency_analysis_completeness
- issue_detection_accuracy

### Internal Feedback Loop (P6)
Self-validate verification, retry up to 3 times if issues found.

### Output
- synthesisL1: Final 500-token summary (for main context injection)
- synthesisL2: Final 2000-token detail (for main context injection)
- synthesisL3Path: File path (NOT injected, file only)
- unresolvedIssues: Issues needing Main Agent review
`
  })

  // Inject L1 and L2 to main context (NOT L3)
  injectToMainContext(verification.synthesisL1)
  injectToMainContext(verification.synthesisL2)

  return verification
}
```

### 2.6 Phase 3.5: Main Agent Review Gate

```javascript
async function phase3_5_main_agent_review(synthesisResult, originalRequest) {
  // Main Agent reviews from holistic perspective
  const reviewCriteria = {
    requirement_alignment: "Does result match original request?",
    design_flow_consistency: "Is analysis→plan flow logical?",
    gap_detection: "Are important areas missing?",
    conclusion_clarity: "Is conclusion clear and actionable?"
  }

  const reviewIssues = []

  // Check each criterion
  for (const [criterion, question] of Object.entries(reviewCriteria)) {
    const issue = evaluateCriterion(synthesisResult, criterion, question)
    if (issue) reviewIssues.push(issue)
  }

  if (reviewIssues.length === 0) {
    // PASS - Skip Phase 4, proceed to Phase 5
    return { reviewPassed: true, skipToPhase5: true }
  }

  // ISSUES - Need L3 deep review
  const l3DeepReview = await Task({
    subagent_type: "general-purpose",
    model: "opus",
    prompt: `
## L3 Deep Review Request

### Issues Found
${reviewIssues.map(i => `- ${i.type}: ${i.description}`).join('\n')}

### Task
1. Read synthesis L3 file
2. Code-level detailed verification per issue
3. Root cause analysis
4. Resolution approach derivation

### Output
- l3Analysis: Detailed analysis per issue
- suggestedActions: Resolution suggestions
`
  })

  return {
    reviewPassed: false,
    reviewIssues,
    l3DeepReview,
    proceedToPhase4: true
  }
}
```

### 2.7 Phase 4: Selective Feedback Loop (P4)

```javascript
async function phase4_selective_feedback(reviewResult) {
  // Main Agent classifies issues
  const classification = {
    directFix: [],      // LOW severity - Main Agent fixes directly
    agentDelegation: [] // MEDIUM+ - Delegate to agents
  }

  for (const issue of reviewResult.reviewIssues) {
    if (issue.severity === "LOW" || isSimpleFix(issue)) {
      classification.directFix.push(issue)
    } else {
      classification.agentDelegation.push(issue)
    }
  }

  // Step 1: Main Agent direct fix for LOW severity
  for (const issue of classification.directFix) {
    applyDirectFix(issue)
  }

  // Step 2: Generate clear prompts for delegation
  const delegationPrompts = classification.agentDelegation.map(issue => ({
    problem_what: {
      area: issue.area,
      severity: issue.severity,
      description: issue.description,
      location: issue.location
    },
    root_cause_why: {
      l3_analysis: reviewResult.l3DeepReview.l3Analysis[issue.id],
      root_cause: issue.rootCause
    },
    resolution_how: {
      suggested_action: reviewResult.l3DeepReview.suggestedActions[issue.id],
      specific_instructions: generateInstructions(issue),
      target_files: issue.targetFiles
    }
  }))

  // Step 3: Execute agents with clear prompts
  const feedbackResults = await Promise.all(
    delegationPrompts.map(prompt => Task({
      subagent_type: "general-purpose",
      model: "opus",
      prompt: `
## Issue Resolution Request

### Problem (WHAT)
- Area: ${prompt.problem_what.area}
- Severity: ${prompt.problem_what.severity}
- Description: ${prompt.problem_what.description}
- Location: ${prompt.problem_what.location}

### Root Cause (WHY)
- L3 Analysis: ${prompt.root_cause_why.l3_analysis}
- Root Cause: ${prompt.root_cause_why.root_cause}

### Resolution Approach (HOW)
- Suggested Action: ${prompt.resolution_how.suggested_action}
- Specific Instructions: ${prompt.resolution_how.specific_instructions}
- Target Files: ${prompt.resolution_how.target_files.join(', ')}

### Expected Output
Problem resolved with L1/L2/L3 format output.
Document resolution process.

### Self-Validation (P6)
- Original problem resolved
- No new problems introduced
- Consistency with overall analysis maintained
`
    }))
  )

  // Step 4: Main Agent reviews and synthesizes
  const updatedSynthesis = mergeAndValidate(feedbackResults)

  // Reinject updated L1/L2 to main context
  injectToMainContext(updatedSynthesis.l1)
  injectToMainContext(updatedSynthesis.l2)

  return {
    directFixCount: classification.directFix.length,
    delegatedCount: classification.agentDelegation.length,
    issuesResolved: true,
    updatedSynthesis
  }
}
```

### 2.8 Phase 5: User Final Approval (P5)

```javascript
async function phase5_user_approval(finalSynthesis) {
  let userApproved = false

  while (!userApproved) {
    const response = await AskUserQuestion({
      questions: [{
        question: "Do you approve the above result?",
        header: "Final Approval",
        options: [
          { label: "Approve", description: "Confirm result" },
          { label: "Needs Modification", description: "Rerun with feedback" }
        ],
        multiSelect: false
      }]
    })

    if (response.includes("Approve")) {
      userApproved = true
    } else {
      // Get user feedback and restart from appropriate phase
      const feedback = await getUserFeedback()
      finalSynthesis = await rerunFromPhase(feedback.targetPhase, feedback)
    }
  }

  return generateFinalOutput(finalSynthesis)
}
```

---

## 3. Output Format (L1/L2/L3)

### 3.1 L1 - Summary (YAML)

```yaml
taskId: {skill}-{timestamp}
agentType: {skill}
status: success
summary: "{Brief summary of result}"

priority: HIGH
l2Path: .agent/prompts/{slug}/{skill}_l2.md
l3Path: .agent/prompts/{slug}/{skill}_l3.md
requiresL2Read: false

keyMetrics:
  {metric1}: {value}
  {metric2}: {value}

eflMetrics:
  totalAgents: {count}
  parallelPhases: {count}
  feedbackLoops: {count}
  internalIterations: {total across all agents}

nextActionHint: "/{next-skill} --slug {slug}"
```

### 3.2 L2 - Detail (Markdown)

```markdown
# {Skill} Result: {project_name}

**Workload:** {slug}
**Status:** {status}
**EFL Phases Completed:** {phases}

## Summary
{Executive summary}

## Detailed Analysis
{Section by section detail}

## EFL Execution Report
- **Phase 1**: {agent_count} agents deployed
- **Phase 2**: {l1_count} L1s aggregated
- **Phase 3-A**: L2 horizontal synthesis completed
- **Phase 3-B**: L3 code-level verification completed
- **Phase 3.5**: Main Agent review {passed|triggered Phase 4}
- **Phase 4**: {feedback_count} feedback loops (if applicable)
- **Phase 5**: User approved

## Next Step
\`\`\`bash
/{next-skill} --slug {slug}
\`\`\`
```

### 3.3 L3 - Deep-Dive (File)

Full detailed output stored at `.agent/prompts/{slug}/{skill}_l3.md`.
Not injected to main context (context size management).

---

## 4. Error Handling

### 4.1 All-or-Nothing Policy

```javascript
// Any phase failure blocks entire skill
if (phaseResult.status === "failed") {
  return {
    status: "failed",
    phase: phaseResult.phase,
    error: phaseResult.error,
    recovery: "Fix errors and retry skill"
  }
}
```

### 4.2 Post-Compact Recovery

Reference: `.claude/skills/shared/post-compact-recovery.md`

```javascript
if (isPostCompactSession()) {
  // MANDATORY: Restore full context from files
  const slug = await getActiveWorkload()
  const context = await restoreSkillContext(slug, SKILL_NAME)

  if (!context.isValid) {
    return { error: "Post-Compact Recovery Failed", missing: context.missing }
  }

  // Now proceed with full context
}
```

---

## 5. Checklist

### 5.1 Frontmatter Checklist

- [ ] `disable-model-invocation: true`
- [ ] `context: fork`
- [ ] `Write` in `allowed-tools`
- [ ] hooks use `type: command` format
- [ ] `agent_delegation` section (P1)
- [ ] `parallel_agent_config` section (P2)

### 5.2 Phase Structure Checklist

- [ ] Phase 1: Parallel Agent Deployment with P6 self-validation
- [ ] Phase 2: L1 Aggregation
- [ ] Phase 3-A: L2 Horizontal Synthesis
- [ ] Phase 3-B: L3 Vertical Verification
- [ ] Phase 3.5: Main Agent Review Gate
- [ ] Phase 4: Selective Feedback Loop
- [ ] Phase 5: User Final Approval

### 5.3 Agent Prompt Checklist

- [ ] P6 Internal Feedback Loop instructions included
- [ ] Validation criteria specified
- [ ] Max 3 iterations noted
- [ ] L1/L2/L3 output format required
- [ ] internalIterations status report required

### 5.4 Output Checklist

- [ ] L1 YAML format with eflMetrics
- [ ] L2 Markdown with EFL Execution Report
- [ ] L3 file path (not injected)
- [ ] nextActionHint for pipeline continuity

---

## 6. Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | 2026-01-29 | Initial EFL template for skill upgrade project |

---

*This template is the authoritative source for EFL pattern implementation across all skills.*
