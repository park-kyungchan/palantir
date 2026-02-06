---
name: planning
description: |
  Generate YAML planning documents from research results for execution readiness.

  Core Capabilities:
  - Research Integration: Parse L1/L2/L3 research outputs for informed planning
  - Phase Decomposition: Break down implementation into dependency-aware phases
  - EFL Pattern Execution: Full P1-P6 implementation with Phase 3-A/3-B synthesis
  - Plan Agent Review: Quality assurance through iterative review loop (max 3 iterations)
  - Execution Blueprint: Output structured YAML for /orchestrate consumption

  Output Format:
  - L1: YAML summary for main orchestrator (500 tokens)
  - L2: Human-readable phase overview (2000 tokens)
  - L3: Complete planning document (plan.yaml)

  Pipeline Position:
  - Post-/research phase (or standalone execution)
  - Handoff to /orchestrate when Plan Agent approves
user-invocable: true
disable-model-invocation: false
context: fork
model: opus
version: "3.0.0"
argument-hint: "[--research-slug <slug>] [--auto-approve]"
allowed-tools:
  - Read
  - Write
  - Task
  - Glob
  - Grep
  - mcp__sequential-thinking__sequentialthinking
  - AskUserQuestion

# =============================================================================
# P1: Skill as Sub-Orchestrator
# =============================================================================
agent_delegation:
  enabled: true
  default_mode: true  # V1.1.0: Auto-delegation by default
  max_sub_agents: 4
  delegation_strategy: "auto"
  strategies:
    phase_based:
      description: "Delegate by implementation phase area"
      use_when: "Large multi-component planning"
    complexity_based:
      description: "Delegate by task complexity level"
      use_when: "Mixed complexity planning"
    scope_based:
      description: "Delegate by analysis scope (frontend/backend/infra)"
      use_when: "Cross-domain planning"
  slug_orchestration:
    enabled: true
  default_mode: true  # V1.1.0: Auto-delegation by default
    source: "clarify or research slug"
    action: "reuse upstream workload context"
  sub_agent_permissions:
    - Read
    - Write  # Required for L1/L2/L3 output
    - Glob
    - Grep
  output_paths:
    l1: ".agent/prompts/{slug}/planning/l1_summary.yaml"
    l2: ".agent/prompts/{slug}/planning/l2_index.md"
    l3: ".agent/prompts/{slug}/planning/l3_details/"
  return_format:
    l1: "Planning summary with phase count and approval status (≤500 tokens)"
    l2_path: ".agent/prompts/{slug}/planning/l2_index.md"
    l3_path: ".agent/prompts/{slug}/planning/l3_details/"
    requires_l2_read: false
    next_action_hint: "/orchestrate"
  description: |
    This skill operates as a Sub-Orchestrator (P1).
    It delegates planning work to Plan Agents rather than executing directly.
    L1 returns to main context; L2/L3 always saved to files.

# =============================================================================
# P2: Parallel Agent Configuration
# =============================================================================
parallel_agent_config:
  enabled: true
  complexity_detection: "auto"
  agent_count_by_complexity:
    simple: 1      # Basic planning (single phase)
    moderate: 2    # Standard planning (2-3 phases)
    complex: 3     # Complex planning (4-6 phases)
    very_complex: 4  # Comprehensive planning (7+ phases)
  synchronization_strategy: "barrier"  # Wait for all agents
  aggregation_strategy: "merge"        # Merge all planning outputs
  plan_areas:
    - tech_stack_analysis
    - architecture_option_analysis
    - risk_analysis
    - implementation_phase_design
    - dependency_order_design
    - test_strategy_design
  description: |
    Deploy multiple Plan Agents in parallel for comprehensive planning.
    Agent count scales with detected complexity (phase count).
    All agents run Phase 1 simultaneously, then results are aggregated.

# =============================================================================
# P6: Agent Internal Feedback Loop
# =============================================================================
agent_internal_feedback_loop:
  enabled: true
  max_iterations: 3
  validation_criteria:
    completeness:
      - "All research findings incorporated into plan"
      - "All phases have clear deliverables"
      - "Dependencies between phases documented"
    quality:
      - "Phase breakdown is logical and actionable"
      - "Risk analysis covers critical paths"
      - "Test strategy aligns with implementation phases"
    internal_consistency:
      - "L1/L2/L3 hierarchy maintained"
      - "Phase numbering sequential"
      - "No circular dependencies"
  refinement_triggers:
    - "Plan Agent requests revision"
    - "Missing dependency detected"
    - "Incomplete phase definition"
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


# /planning - YAML Planning Document Generator (EFL V3.0.0)

> **Version:** 3.0.0 (EFL Pattern)
> **Role:** Planning Document Generation with Full EFL Implementation
> **Pipeline Position:** After /research, Before /orchestrate
> **EFL Template:** `.claude/skills/shared/efl-template.md`


---

## 1. Purpose

Generate structured YAML planning documents using Enhanced Feedback Loop (EFL) pattern:

1. **Phase 1**: Deploy parallel Plan Agents for different planning areas
2. **Phase 2**: Aggregate L1 summaries from all agents
3. **Phase 3-A**: L2 Horizontal Synthesis (cross-area consistency)
4. **Phase 3-B**: L3 Vertical Verification (code-level accuracy)
5. **Phase 3.5**: Main Agent Review Gate (holistic verification)
6. **Phase 4**: Selective Feedback Loop (if issues found)
7. **Phase 5**: User Final Approval Loop

### Pipeline Integration

```
/clarify → /research → [/planning] → /orchestrate → Workers → /synthesis
                          │
                          ├── Load research L1/L2/L3 outputs
                          ├── Phase 1: Parallel Plan Agents (P2)
                          ├── Phase 2: L1 Aggregation
                          ├── Phase 3-A: L2 Horizontal Synthesis (P3)
                          ├── Phase 3-B: L3 Vertical Verification (P3)
                          ├── Phase 3.5: Main Agent Review Gate (P1)
                          ├── Phase 4: Selective Feedback Loop (P4)
                          ├── Phase 5: User Approval (P5)
                          └── Output: .agent/prompts/{slug}/plan.yaml
```


---

## 2. Invocation

### Syntax

```bash
# Pipeline mode (with upstream research)
/planning --research-slug enhanced_pipeline_skills_20260124

# Auto-approve (skip user confirmation)
/planning --research-slug my-feature --auto-approve

# Interactive (uses active workload or prompts)
/planning

# Show help
/planning --help
```

### Arguments

| Argument | Required | Description |
|----------|----------|-------------|
| `--research-slug` | No | Research document slug to load (pipeline mode) |
| `--auto-approve` | No | Skip user confirmation after Plan Agent approval |
| `--help`, `-h` | No | Show usage information |

### Argument Parsing

```bash
# $ARGUMENTS parsing with error recovery
RESEARCH_SLUG=""
AUTO_APPROVE=false
SHOW_HELP=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --help|-h)
            SHOW_HELP=true
            shift
            ;;
        --research-slug)
            if [[ -z "$2" || "$2" == --* ]]; then
                echo "❌ Error: --research-slug requires a slug argument" >&2
                SHOW_HELP=true
                shift
            else
                RESEARCH_SLUG="$2"
                shift 2
            fi
            ;;
        --auto-approve)
            AUTO_APPROVE=true
            shift
            ;;
        --*)
            echo "❌ Error: Unknown option: $1" >&2
            SHOW_HELP=true
            shift
            ;;
        *)
            echo "❌ Error: Unexpected argument: $1" >&2
            SHOW_HELP=true
            shift
            ;;
    esac
done

if [[ "$SHOW_HELP" == "true" ]]; then
    cat << 'EOF'
Usage: /planning [OPTIONS]

Options:
  --research-slug <slug>  Link to upstream /research workload
  --auto-approve          Skip user confirmation after Plan Agent approval
  --help, -h              Show this help message

Examples:
  /planning --research-slug user-auth-20260129
  /planning --research-slug my-feature --auto-approve
  /planning  # Uses active workload or prompts for slug

Pipeline Position:
  /clarify → /research → /planning → /orchestrate
EOF
    exit 1
fi
```


---

## 3. Workload Slug Resolution

```bash
# Source centralized utilities
source "${WORKSPACE_ROOT:-.}/.claude/skills/shared/slug-generator.sh"
source "${WORKSPACE_ROOT:-.}/.claude/skills/shared/workload-files.sh"

# Resolution priority:
# 1. --research-slug argument (upstream linkage)
# 2. Active workload (get_active_workload)
# 3. Generate new workload (standalone mode)

if [[ -n "$RESEARCH_SLUG" ]]; then
    WORKLOAD_ID="$RESEARCH_SLUG"
    SLUG=$(generate_slug_from_workload "$WORKLOAD_ID")
    echo "📋 Using upstream research slug: $SLUG"

elif ACTIVE_WORKLOAD=$(get_active_workload) && [[ -n "$ACTIVE_WORKLOAD" ]]; then
    WORKLOAD_ID="$ACTIVE_WORKLOAD"
    SLUG=$(get_active_workload_slug)
    echo "📋 Using active workload: $SLUG"

else
    TOPIC="${QUERY:-planning-$(date +%H%M%S)}"
    WORKLOAD_ID=$(generate_workload_id "$TOPIC")
    SLUG=$(generate_slug_from_workload "$WORKLOAD_ID")
    init_workload_directory "$WORKLOAD_ID"
    set_active_workload "$WORKLOAD_ID"
    echo "📋 Created new workload: $SLUG"
fi

WORKLOAD_DIR=".agent/prompts/${SLUG}"
mkdir -p "${WORKLOAD_DIR}"
```


---

## 4. Input Processing (3-Tier Reference)

### 4.1 Load Research Outputs (L1/L2/L3)

```javascript
async function loadResearchOutputs(slug) {
  const basePath = `.agent/prompts/${slug}`

  // L1: Summary for quick context
  const l1 = await Read({ file_path: `${basePath}/research.md` })

  // L2: Implementation patterns for targetFiles
  const l2Path = `${basePath}/research/l2_detailed.md`
  const l2Exists = await fileExists(l2Path)
  const l2 = l2Exists ? await Read({ file_path: l2Path }) : null

  // L3: Risk matrix for dependency ordering
  const l3Path = `${basePath}/research/l3_synthesis.md`
  const l3Exists = await fileExists(l3Path)
  const l3 = l3Exists ? await Read({ file_path: l3Path }) : null

  return {
    l1: {
      content: l1,
      sections: {
        codebaseAnalysis: extractSection(l1, '## Codebase Analysis'),
        externalResearch: extractSection(l1, '## External Research'),
        riskAssessment: extractSection(l1, '## Risk Assessment'),
        recommendations: extractSection(l1, '## Recommendations')
      }
    },
    l2: l2 ? {
      content: l2,
      implementationPatterns: extractImplementationPatterns(l2),
      targetFiles: extractTargetFiles(l2)
    } : null,
    l3: l3 ? {
      content: l3,
      riskMatrix: extractRiskMatrix(l3),
      dependencyGraph: extractDependencyGraph(l3)
    } : null
  }
}
```

### 4.2 Load Clarify Output

```javascript
async function loadClarify(slug) {
  const clarify = await Read({ file_path: `.agent/prompts/${slug}/clarify.yaml` })

  const workloadId = clarify.metadata?.workload_id
    || clarify.workload_id
    || clarify.metadata?.id
    || slug

  return {
    originalRequest: clarify.original_request,
    workloadId: workloadId,
    rounds: clarify.rounds,
    finalDecision: clarify.final_decision,
    requirements: extractRequirements(clarify.rounds)
  }
}
```


---

## 5. EFL Execution Flow

### 5.1 Phase 1: Parallel Plan Agent Deployment (P2)

```javascript
async function phase1_parallel_plan_agents(research, clarify) {
  // Determine complexity and agent count
  const estimatedPhases = estimatePhaseCount(research, clarify)
  const agentCount = getAgentCountByComplexity(estimatedPhases)

  console.log(`📊 Complexity: ${estimatedPhases} phases → ${agentCount} agents`)

  // Divide planning into areas
  const planAreas = [
    { id: "arch", name: "Architecture & Tech Stack", focus: "technology decisions" },
    { id: "impl", name: "Implementation Phases", focus: "phase breakdown" },
    { id: "risk", name: "Risk & Dependencies", focus: "risk mitigation" },
    { id: "test", name: "Testing & Validation", focus: "verification strategy" }
  ].slice(0, agentCount)

  // Deploy parallel Plan Agents with P6 self-validation
  const agents = planAreas.map(area => Task({
    subagent_type: "Plan",
    model: "opus",
    prompt: `
## Planning Area: ${area.name}

### Context
Original Request: ${clarify.originalRequest}

Research Summary (L1):
${research.l1.content.substring(0, 2000)}

${research.l2 ? `Implementation Patterns (L2):
${research.l2.implementationPatterns.substring(0, 1500)}` : ''}

${research.l3 ? `Risk Matrix (L3):
${research.l3.riskMatrix.substring(0, 1000)}` : ''}

### Your Focus
Analyze and plan for: **${area.focus}**

### Internal Feedback Loop (P6 - REQUIRED)
1. Generate planning output for your area
2. Self-validate:
   - Implementability: Can each item actually be implemented?
   - Dependency correctness: Are dependencies properly identified?
   - Completeness: Are all aspects of your area covered?
   - Risk identification: Are risks for your area documented?
3. If validation fails, revise and retry (max 3 iterations)
4. Output only after validation passes

### Output Format
Return YAML:
\`\`\`yaml
areaId: "${area.id}"
areaName: "${area.name}"
status: "success"

l1Summary:
  keyDecisions: [...]
  phaseCount: {number}
  criticalRisks: [...]

phases:  # Phases relevant to your area
  - id: "phase-{n}"
    name: "{phase name}"
    priority: "P0|P1|P2"
    targetFiles: [...]
    dependencies: [...]
    completionCriteria: [...]

internalLoopStatus:
  iterations: {1-3}
  validationStatus: "passed"
  issuesResolved: [...]
\`\`\`
`,
    description: `Plan Agent: ${area.name}`
  }))

  // Wait for all agents (barrier synchronization)
  const results = await Promise.all(agents)

  return {
    agentCount,
    planAreas,
    results,
    l1s: results.map(r => r.l1Summary),
    phases: results.flatMap(r => r.phases || []),
    iterations: results.map(r => r.internalLoopStatus?.iterations || 1)
  }
}
```

### 5.2 Phase 2: L1 Aggregation

```javascript
async function phase2_l1_aggregation(phase1Results) {
  // Validate each L1
  for (const l1 of phase1Results.l1s) {
    if (!l1 || !l1.keyDecisions) {
      throw new Error("Invalid L1 format from Plan Agent")
    }
  }

  // Merge all L1s
  const aggregatedL1 = {
    totalAgents: phase1Results.agentCount,
    areas: phase1Results.planAreas.map((area, i) => ({
      id: area.id,
      name: area.name,
      keyDecisions: phase1Results.l1s[i].keyDecisions,
      phaseCount: phase1Results.l1s[i].phaseCount,
      criticalRisks: phase1Results.l1s[i].criticalRisks
    })),
    totalPhases: phase1Results.phases.length,
    overallStatus: determineOverallStatus(phase1Results.l1s)
  }

  // Merge and deduplicate phases
  const mergedPhases = mergePhases(phase1Results.phases)

  return { aggregatedL1, mergedPhases }
}
```

### 5.3 Phase 3-A: L2 Horizontal Synthesis (P3)

```javascript
async function phase3a_l2_horizontal_synthesis(aggregatedL1, mergedPhases) {
  // Delegate to general-purpose agent for horizontal integration
  const synthesis = await Task({
    subagent_type: "general-purpose",
    model: "opus",
    prompt: `
## L2 Horizontal Synthesis for Planning

### Input
Aggregated L1 from ${aggregatedL1.totalAgents} Plan Agents:
${JSON.stringify(aggregatedL1, null, 2)}

Merged Phases (${mergedPhases.length} total):
${mergedPhases.map(p => `- ${p.id}: ${p.name} (${p.priority})`).join('\n')}

### Task
1. **Cross-validate** all planning areas for consistency:
   - Do architecture decisions align with implementation phases?
   - Are dependencies correctly ordered across areas?
   - Are risk mitigations properly integrated?

2. **Identify contradictions** between areas:
   - Technology choice conflicts
   - Dependency cycle detection
   - Resource allocation conflicts

3. **Detect gaps** at area connection points:
   - Missing integration phases
   - Uncovered transition points
   - Missing verification steps

4. **Synthesize** into unified planning document structure

### Validation Criteria
- cross_area_consistency
- dependency_acyclicity
- risk_coverage_completeness

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
  unifiedPhaseStructure:
    phases: [...]  # Reordered and validated
  crossAreaAnalysis:
    consistencyIssues: [...]
    resolvedContradictions: [...]
    gapsFilled: [...]

phase3a_L3Path: ".agent/prompts/{slug}/planning_phase3a_l3.md"

internalLoopStatus:
  iterations: {1-3}
  validationStatus: "passed"
\`\`\`
`,
    description: "L2 Horizontal Synthesis for Planning"
  })

  // Write L3 detail to file
  await Write({
    file_path: synthesis.phase3a_L3Path,
    content: generatePhase3aL3Detail(synthesis)
  })

  return synthesis
}
```

### 5.4 Phase 3-B: L3 Vertical Verification (P3)

```javascript
async function phase3b_l3_vertical_verification(phase3aResult, research) {
  // Read Phase 3-A L3 for deep verification
  const phase3aL3 = await Read({ file_path: phase3aResult.phase3a_L3Path })

  // Delegate to general-purpose agent for code-level verification
  const verification = await Task({
    subagent_type: "general-purpose",
    model: "opus",
    prompt: `
## L3 Code-Level Verification for Planning

### Input
Phase 3-A Synthesis L2:
${JSON.stringify(phase3aResult.phase3a_L2, null, 2)}

Phase 3-A L3 Detail:
${phase3aL3}

Research L3 (Risk Matrix):
${research.l3?.content || "Not available"}

### Task
1. **Verify targetFiles exist** or creation is justified:
   - Check if file paths in phases are valid
   - Verify parent directories exist
   - Flag non-existent paths for creation

2. **Validate dependency logic**:
   - Check if dependencies reference valid phase IDs
   - Verify dependency order is logical
   - Detect any circular dependencies

3. **Cross-reference with research**:
   - Do target files match research recommendations?
   - Are identified risks addressed in phases?
   - Are completion criteria measurable?

### Validation Criteria
- targetFile_validity
- dependency_logic_accuracy
- research_alignment
- criteria_measurability

### Internal Feedback Loop (P6)
Self-validate verification, retry up to 3 times if issues found.

### Output Format
\`\`\`yaml
synthesisL1:
  verificationStatus: "success"
  targetFileValidity: {percentage}
  dependencyCorrectness: {percentage}
  researchAlignment: {percentage}

synthesisL2:
  verifiedPhases:
    - id: "..."
      targetFilesValid: true/false
      dependenciesValid: true/false
      criteriaValid: true/false
  verificationNotes: [...]

synthesisL3Path: ".agent/prompts/{slug}/plan.yaml"

unresolvedIssues: [...]  # Issues needing Main Agent review

internalLoopStatus:
  iterations: {1-3}
  validationStatus: "passed"
\`\`\`
`,
    description: "L3 Vertical Verification for Planning"
  })

  return verification
}
```

### 5.5 Phase 3.5: Main Agent Review Gate (P1)

```javascript
async function phase3_5_main_agent_review(synthesisResult, clarify) {
  // Main Agent reviews from holistic perspective
  const reviewCriteria = {
    requirement_alignment: {
      question: "Does planning match original request?",
      checks: ["requirement_interpretation", "scope_appropriate"]
    },
    design_flow_consistency: {
      question: "Is research→plan logical flow natural?",
      checks: ["step_connections", "architecture_perspective"]
    },
    gap_detection: {
      question: "Are important implementation areas missing?",
      checks: ["edge_cases", "risk_factors"]
    },
    conclusion_clarity: {
      question: "Is planning actionable for /orchestrate?",
      checks: ["no_ambiguity", "sufficient_detail"]
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

  // Need L3 deep review for MEDIUM+ severity issues
  const needsL3Review = reviewIssues.some(i => i.needsL3Review)

  if (needsL3Review) {
    const l3DeepReview = await Task({
      subagent_type: "general-purpose",
      model: "opus",
      prompt: `
## L3 Deep Review for Planning Issues

### Issues Found by Main Agent
${reviewIssues.map(i => `- [${i.severity}] ${i.type}: ${i.description}`).join('\n')}

### Task
1. Read planning L3 file at ${synthesisResult.synthesisL3Path}
2. Detailed code-level analysis per issue
3. Identify root cause
4. Suggest resolution approach

### Output
\`\`\`yaml
l3Analysis:
  - issueType: "..."
    rootCause: "..."
    affectedPhases: [...]
    suggestedAction: "..."
    targetFiles: [...]
\`\`\`
`,
      description: "L3 Deep Review for Planning Issues"
    })

    return {
      reviewPassed: false,
      reviewIssues,
      l3DeepReview,
      proceedToPhase4: true
    }
  }

  return { reviewPassed: false, reviewIssues, proceedToPhase4: true }
}
```

### 5.6 Phase 4: Selective Feedback Loop (P4)

```javascript
async function phase4_selective_feedback(reviewResult, synthesisResult) {
  // Main Agent classifies issues
  const classification = {
    directFix: [],      // LOW severity - fix directly
    agentDelegation: [] // MEDIUM+ - delegate
  }

  for (const issue of reviewResult.reviewIssues) {
    if (issue.severity === "LOW") {
      classification.directFix.push(issue)
    } else {
      classification.agentDelegation.push({
        ...issue,
        l3Analysis: reviewResult.l3DeepReview?.l3Analysis?.find(
          a => a.issueType === issue.type
        )
      })
    }
  }

  // Step 1: Main Agent direct fix for LOW severity
  let updatedSynthesis = { ...synthesisResult }
  for (const issue of classification.directFix) {
    console.log(`🔧 Direct fix: ${issue.type}`)
    updatedSynthesis = applyDirectFix(updatedSynthesis, issue)
  }

  // Step 2: Delegate MEDIUM+ issues
  if (classification.agentDelegation.length > 0) {
    const feedbackResults = await Promise.all(
      classification.agentDelegation.map(issue => Task({
        subagent_type: "Plan",
        model: "opus",
        prompt: `
## Issue Resolution for Planning

### Problem (WHAT)
- Type: ${issue.type}
- Severity: ${issue.severity}
- Description: ${issue.description}

### Root Cause (WHY)
${issue.l3Analysis?.rootCause || "Analyze and determine"}

### Resolution Approach (HOW)
Suggested: ${issue.l3Analysis?.suggestedAction || "Determine best approach"}
Affected Phases: ${issue.l3Analysis?.affectedPhases?.join(', ') || "Identify"}

### Expected Output
Return corrected planning sections in YAML format.

### Self-Validation (P6)
- Original issue resolved
- No new issues introduced
- Consistency maintained
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

### 5.7 Phase 5: User Final Approval (P5)

```javascript
async function phase5_user_approval(finalSynthesis, autoApprove) {
  if (autoApprove) {
    console.log("✅ Auto-approve enabled, skipping user confirmation")
    return { approved: true, synthesis: finalSynthesis }
  }

  let userApproved = false
  let currentSynthesis = finalSynthesis

  while (!userApproved) {
    const response = await AskUserQuestion({
      questions: [{
        question: "Plan Agent has completed. Do you approve this planning document?",
        header: "Final Approval",
        options: [
          { label: "Approve", description: "Proceed to /orchestrate" },
          { label: "Review L3", description: "View full planning document first" },
          { label: "Request Changes", description: "Provide feedback for revision" }
        ],
        multiSelect: false
      }]
    })

    if (response.includes("Approve")) {
      userApproved = true
    } else if (response.includes("Review L3")) {
      // Display L3 content
      const l3Content = await Read({ file_path: currentSynthesis.synthesisL3Path })
      console.log(l3Content)
    } else {
      // Get user feedback and rerun Phase 4
      const feedback = await getUserFeedback()
      currentSynthesis = await rerunWithFeedback(currentSynthesis, feedback)
    }
  }

  return { approved: true, synthesis: currentSynthesis }
}
```


---

## 6. Main Execution Protocol

```javascript
async function executePlanning(args) {
  console.log("🚀 /planning V3.0.0 (EFL Pattern)")

  // 1. Parse arguments
  const { slug, autoApprove } = parseArgs(args)
  const targetSlug = slug || await getOrPromptSlug()

  // 2. Post-Compact Recovery Check
  if (isPostCompactSession()) {
    console.log("⚠️ Post-Compact detected, restoring context...")
    await restoreSkillContext(targetSlug, "planning")
  }

  // 3. Load inputs
  console.log("📚 Loading research and clarify outputs...")
  const research = await loadResearchOutputs(targetSlug)
  const clarify = await loadClarify(targetSlug)

  // 4. Gate 3: Pre-flight Checks
  console.log("🔍 Gate 3: Pre-flight checks...")
  const preflight = await runPreflightChecks(targetSlug, research, clarify)
  if (preflight.result === "failed") {
    return { status: "gate3_failed", errors: preflight.errors }
  }

  // 5. EFL Phase 1: Parallel Plan Agent Deployment
  console.log("📊 Phase 1: Deploying parallel Plan Agents...")
  const phase1 = await phase1_parallel_plan_agents(research, clarify)

  // 6. EFL Phase 2: L1 Aggregation
  console.log("📋 Phase 2: Aggregating L1 summaries...")
  const phase2 = await phase2_l1_aggregation(phase1)

  // 7. EFL Phase 3-A: L2 Horizontal Synthesis
  console.log("🔄 Phase 3-A: L2 Horizontal Synthesis...")
  const phase3a = await phase3a_l2_horizontal_synthesis(phase2.aggregatedL1, phase2.mergedPhases)

  // 8. EFL Phase 3-B: L3 Vertical Verification
  console.log("🔍 Phase 3-B: L3 Vertical Verification...")
  const phase3b = await phase3b_l3_vertical_verification(phase3a, research)

  // 9. EFL Phase 3.5: Main Agent Review Gate
  console.log("🚦 Phase 3.5: Main Agent Review Gate...")
  const review = await phase3_5_main_agent_review(phase3b, clarify)

  let finalSynthesis = phase3b
  let feedbackLoops = 0

  // 10. EFL Phase 4: Selective Feedback Loop (if needed)
  if (!review.reviewPassed) {
    console.log("🔄 Phase 4: Selective Feedback Loop...")
    const phase4 = await phase4_selective_feedback(review, phase3b)
    finalSynthesis = phase4.updatedSynthesis
    feedbackLoops = 1
  }

  // 11. EFL Phase 5: User Final Approval
  console.log("✋ Phase 5: User Approval...")
  const approval = await phase5_user_approval(finalSynthesis, autoApprove)

  // 12. Generate and save final output
  const outputPath = `.agent/prompts/${targetSlug}/plan.yaml`
  await Write({
    file_path: outputPath,
    content: generateFinalPlanYAML(approval.synthesis, {
      eflMetrics: {
        totalAgents: phase1.agentCount,
        parallelPhases: phase1.planAreas.length,
        feedbackLoops,
        internalIterations: phase1.iterations.reduce((a, b) => a + b, 0)
      }
    })
  })

  // 13. Return L1 summary
  return {
    taskId: `planning-${Date.now()}`,
    agentType: "planning",
    status: "success",
    summary: `Planning complete: ${phase2.mergedPhases.length} phases, EFL verified`,

    priority: "HIGH",
    l2Path: `.agent/prompts/${targetSlug}/planning_l2.md`,
    l3Path: outputPath,
    requiresL2Read: false,

    phases: {
      total: phase2.mergedPhases.length,
      parallel_capable: identifyParallelPhases(phase2.mergedPhases).length,
      critical_path_length: calculateCriticalPath(phase2.mergedPhases).length
    },

    eflMetrics: {
      totalAgents: phase1.agentCount,
      parallelPhases: phase1.planAreas.length,
      feedbackLoops,
      internalIterations: phase1.iterations.reduce((a, b) => a + b, 0),
      phase3aStatus: phase3a.phase3a_L1.synthesisStatus,
      phase3bStatus: phase3b.synthesisL1.verificationStatus,
      mainAgentReviewPassed: review.reviewPassed
    },

    nextActionHint: `/orchestrate --plan-slug ${targetSlug}`
  }
}
```


---

## 7. Output Format (L1/L2/L3)

### 7.1 L1 - Summary (YAML)

```yaml
taskId: planning-{timestamp}
agentType: planning
status: success
summary: "Planning complete: {phase_count} phases, EFL verified"

priority: HIGH
l2Path: .agent/prompts/{slug}/planning_l2.md
l3Path: .agent/prompts/{slug}/plan.yaml
requiresL2Read: false

phases:
  total: {count}
  parallel_capable: {count}
  critical_path_length: {count}

eflMetrics:
  totalAgents: {count}
  parallelPhases: {count}
  feedbackLoops: {count}
  internalIterations: {total}
  phase3aStatus: "success"
  phase3bStatus: "success"
  mainAgentReviewPassed: true

nextActionHint: "/orchestrate --plan-slug {slug}"
```

### 7.2 L2 - Phase Overview (Markdown)

```markdown
# Planning Complete: {project_name}

**Document:** .agent/prompts/{slug}/plan.yaml
**Status:** EFL Verified
**Phases:** {count} phases
**Complexity:** {low|medium|high}

## EFL Execution Report

| Phase | Status | Details |
|-------|--------|---------|
| Phase 1 | ✅ | {agent_count} agents deployed |
| Phase 2 | ✅ | {l1_count} L1s aggregated |
| Phase 3-A | ✅ | Horizontal synthesis complete |
| Phase 3-B | ✅ | Vertical verification complete |
| Phase 3.5 | ✅ | Main Agent review passed |
| Phase 4 | {✅|⏭️} | {feedback_count} loops / Skipped |
| Phase 5 | ✅ | User approved |

## Phase Breakdown

| ID | Phase Name | Priority | Dependencies |
|----|------------|----------|--------------|
{phase_rows}

## Next Step

\`\`\`bash
/orchestrate --plan-slug {slug}
\`\`\`
```

### 7.3 L3 - Full Planning Document

Output at `.agent/prompts/{slug}/plan.yaml` - complete YAML planning document.


---

## 8. Error Handling

### 8.1 All-or-Nothing Policy

Any EFL phase failure blocks entire skill:

```javascript
if (phaseResult.status === "failed") {
  return {
    status: "efl_phase_failed",
    failedPhase: phaseResult.phase,
    error: phaseResult.error,
    recovery: "Fix errors and retry /planning"
  }
}
```

### 8.2 Post-Compact Recovery

Reference: `.claude/skills/shared/post-compact-recovery.md`

Required reads after compact:
- `.agent/prompts/{slug}/clarify.yaml`
- `.agent/prompts/{slug}/research.md`
- `.agent/prompts/{slug}/research/l2_detailed.md`
- `.agent/prompts/{slug}/research/l3_synthesis.md`


---

## 9. Standalone Execution

```bash
# Standalone (new workload)
/planning "Implement user authentication"

# Pipeline linkage
/planning --research-slug user-auth-20260129
```


---

## 10. Handoff Contract

```yaml
handoff:
  skill: "planning"
  workload_slug: "{slug}"
  status: "completed"
  efl_verified: true
  next_action:
    skill: "/orchestrate"
    arguments: "--plan-slug {slug}"
    required: true
```


---

## 11. Version History

| Version | Date | Changes |
|---------|------|---------|
| 3.0.0 | 2026-01-29 | **Full EFL Implementation** |
| | | P1-P6 complete |
| | | Phase 3-A: L2 Horizontal Synthesis |
| | | Phase 3-B: L3 Vertical Verification |
| | | Phase 3.5: Main Agent Review Gate |
| | | Phase 4: Selective Feedback Loop |
| | | Phase 5: User Approval Loop |
| | | Agent prompts include P6 self-validation |
| | | eflMetrics in L1 output |
| 2.2.0 | 2026-01-29 | Consistency principles, argument parsing |
| 2.1.0 | 2026-01-28 | Standalone + Handoff Contract |
| 2.0.0 | 2026-01-28 | P1/P2 config, L1 YAML format |
| 1.0.0 | 2026-01-24 | Initial implementation |


---

**End of Skill Documentation**

