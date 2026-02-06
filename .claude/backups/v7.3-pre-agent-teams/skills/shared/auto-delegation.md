# Auto-Delegation Trigger Module

> **Version:** 1.0.0
> **Purpose:** Bridge gap between frontmatter `agent_delegation` settings and skill execution behavior
> **Mandatory for:** All skills with `agent_delegation.enabled: true`

---

## 1. Overview

This module provides standardized auto-delegation logic that skills include to automatically trigger sub-agent delegation based on frontmatter configuration.

### Problem Solved

Skills have `agent_delegation.enabled: true` in frontmatter, but no automatic mechanism to:
1. Check these settings at runtime
2. Analyze task complexity
3. Trigger delegation based on `default_mode` and `strategies`

### Solution

Include this module in skill body to enable auto-delegation behavior.

---

## 2. Auto-Delegation Decision Flow

```
Skill Invocation
    │
    ▼
┌───────────────────────────────────────┐
│  Check agent_delegation frontmatter   │
│  - enabled: true/false                │
│  - default_mode: true/false           │
└───────────────────────────────────────┘
    │
    ├─── enabled: false → Execute skill directly (no delegation)
    │
    └─── enabled: true
         │
         ├─── default_mode: true
         │    │
         │    ▼
         │    Auto-analyze task complexity
         │    │
         │    └─── Deploy sub-agents per strategies config
         │
         └─── default_mode: false (or not set)
              │
              └─── Check for explicit delegation request
                   │
                   ├─── User requested delegation → Delegate
                   └─── No request → Execute normally
```

---

## 3. Implementation Functions

### 3.1 checkAutoDelegation

```javascript
/**
 * Check if auto-delegation should be triggered based on frontmatter config
 * Call this at the START of skill execution
 *
 * @returns {Object} Delegation decision
 *   - shouldDelegate: boolean
 *   - mode: "auto" | "manual" | "disabled"
 *   - reason: string
 */
function checkAutoDelegation(skillConfig, userRequest) {
  // 1. Check if agent_delegation is enabled
  const delegation = skillConfig.agent_delegation

  if (!delegation || !delegation.enabled) {
    return {
      shouldDelegate: false,
      mode: "disabled",
      reason: "agent_delegation.enabled is false or not configured"
    }
  }

  // 2. Check default_mode setting
  if (delegation.default_mode === true) {
    // Always delegate when default_mode is true
    return {
      shouldDelegate: true,
      mode: "auto",
      reason: "agent_delegation.default_mode is true - auto-delegation active"
    }
  }

  // 3. Check for explicit user request
  const explicitDelegation = checkExplicitDelegationRequest(userRequest)

  if (explicitDelegation) {
    return {
      shouldDelegate: true,
      mode: "manual",
      reason: "User explicitly requested delegation"
    }
  }

  // 4. default_mode is false or not set, no explicit request
  return {
    shouldDelegate: false,
    mode: "manual",
    reason: "delegation.enabled but default_mode is false - requires explicit request"
  }
}

function checkExplicitDelegationRequest(userRequest) {
  if (!userRequest) return false

  // Check for delegation flags in user request
  const delegationPatterns = [
    /--delegate/i,
    /--sub-orchestrator/i,
    /--parallel/i,
    /with\s+agents?/i,
    /delegate\s+to/i
  ]

  return delegationPatterns.some(pattern => pattern.test(userRequest))
}
```

### 3.2 analyzeTaskComplexity

```javascript
/**
 * Analyze task complexity to determine agent count and strategy
 * Uses parallel_agent_config from frontmatter
 *
 * @returns {Object} Complexity analysis result
 */
function analyzeTaskComplexity(taskDescription, skillConfig) {
  const parallelConfig = skillConfig.parallel_agent_config

  if (!parallelConfig || !parallelConfig.enabled) {
    return {
      complexity: "simple",
      agentCount: 1,
      strategy: "single"
    }
  }

  // Complexity indicators
  const complexityIndicators = {
    simple: {
      maxLines: 50,
      maxFiles: 2,
      maxConcepts: 3,
      keywords: ["fix", "update", "minor", "simple"]
    },
    moderate: {
      maxLines: 200,
      maxFiles: 5,
      maxConcepts: 7,
      keywords: ["refactor", "enhance", "add", "implement"]
    },
    complex: {
      maxLines: 500,
      maxFiles: 10,
      maxConcepts: 15,
      keywords: ["redesign", "architecture", "integration", "migration"]
    },
    very_complex: {
      keywords: ["full rewrite", "system-wide", "cross-module", "breaking change"]
    }
  }

  // Detect complexity from task description
  let detectedComplexity = "simple"

  for (const [level, indicators] of Object.entries(complexityIndicators).reverse()) {
    if (indicators.keywords.some(kw =>
      taskDescription.toLowerCase().includes(kw.toLowerCase())
    )) {
      detectedComplexity = level
      break
    }
  }

  // Get agent count from config
  const agentCounts = parallelConfig.agent_count_by_complexity || {
    simple: 1,
    moderate: 2,
    complex: 3,
    very_complex: 4
  }

  const agentCount = agentCounts[detectedComplexity] || 1

  // Select strategy
  const strategies = skillConfig.agent_delegation?.strategies || {}
  const selectedStrategy = selectStrategy(detectedComplexity, strategies)

  return {
    complexity: detectedComplexity,
    agentCount: agentCount,
    strategy: selectedStrategy,
    autoDetected: parallelConfig.complexity_detection === "auto"
  }
}

function selectStrategy(complexity, strategies) {
  // Map complexity to strategy
  if (strategies.complexity_based && complexity !== "simple") {
    return "complexity_based"
  }
  if (strategies.phase_based) {
    return "phase_based"
  }
  if (strategies.scope_based) {
    return "scope_based"
  }
  return "default"
}
```

### 3.3 executeDelegation

```javascript
/**
 * Execute delegation to sub-agents
 * Implements L1/L2/L3 output pattern
 *
 * @returns {Object} Delegation result with L1 summary
 */
async function executeDelegation(taskDescription, complexityResult, skillConfig) {
  const { agentCount, strategy, complexity } = complexityResult

  console.log(`
=== Auto-Delegation Triggered ===
Strategy: ${strategy}
Complexity: ${complexity}
Deploying: ${agentCount} sub-agent(s)
`)

  // 1. Divide task into subtasks based on strategy
  const subtasks = divideTask(taskDescription, agentCount, strategy, skillConfig)

  // 2. Deploy sub-agents in parallel (P2)
  const agentResults = await deploySubAgents(subtasks, skillConfig)

  // 3. Aggregate results into L1/L2/L3
  const aggregatedResult = aggregateResults(agentResults, skillConfig)

  // 4. Save L2/L3 to files (NEVER return to main context)
  await saveL2L3ToFiles(aggregatedResult, skillConfig)

  // 5. Return L1 summary ONLY
  return {
    l1Summary: aggregatedResult.l1,
    l2Path: aggregatedResult.l2Path,
    l3Path: aggregatedResult.l3Path,
    delegationMetrics: {
      agentCount: agentCount,
      strategy: strategy,
      complexity: complexity,
      subtaskCount: subtasks.length,
      completedCount: agentResults.filter(r => r.status === "success").length
    }
  }
}

function divideTask(taskDescription, agentCount, strategy, skillConfig) {
  const subtaskAreas = skillConfig.parallel_agent_config?.subtask_areas ||
    ["implementation", "testing", "documentation"]

  // Divide based on strategy
  if (strategy === "phase_based") {
    return subtaskAreas.slice(0, agentCount).map((area, i) => ({
      id: `subtask-${i + 1}`,
      area: area,
      description: `${area} phase of: ${taskDescription}`
    }))
  }

  if (strategy === "scope_based") {
    // Analyze scope and divide by component
    return analyzeScope(taskDescription, agentCount)
  }

  // Default: complexity-based division
  return [{
    id: "subtask-1",
    area: "main",
    description: taskDescription
  }]
}

async function deploySubAgents(subtasks, skillConfig) {
  const permissions = skillConfig.agent_delegation?.sub_agent_permissions || [
    "Read", "Write", "Grep", "Glob", "Edit"
  ]

  const results = await Promise.all(subtasks.map(subtask =>
    Task({
      subagent_type: "general-purpose",
      model: skillConfig.model || "opus",
      allowed_tools: permissions,
      prompt: `
## Sub-Agent Task: ${subtask.area}

${subtask.description}

## Internal Feedback Loop (P6 - REQUIRED)
1. Execute the task
2. Self-validate using criteria:
   - Completeness: All aspects addressed
   - Quality: Output meets standards
   - Consistency: No contradictions
3. If issues found, retry (max 3 times)
4. Report final status

## Output Format (REQUIRED)
Return structured result:
- l1: Summary (max 500 tokens)
- l2: Detailed analysis (max 2000 tokens)
- l3Content: Full details for file storage
- status: success | partial | failed
- internalIterations: Number of self-validation loops
`
    })
  ))

  return results
}

function aggregateResults(agentResults, skillConfig) {
  // Merge all L1s into single summary
  const l1Summary = agentResults.map(r => r.l1).join("\n\n")

  // Combine L2s with section headers
  const l2Content = agentResults.map((r, i) =>
    `## Area ${i + 1}: ${r.area || "Analysis"}\n\n${r.l2}`
  ).join("\n\n---\n\n")

  // Combine L3s
  const l3Content = agentResults.map((r, i) =>
    `# Detailed Analysis: Area ${i + 1}\n\n${r.l3Content || r.l2}`
  ).join("\n\n===\n\n")

  const outputPaths = skillConfig.agent_delegation?.output_paths || {
    l1: ".agent/prompts/{slug}/l1_summary.yaml",
    l2: ".agent/prompts/{slug}/l2_index.md",
    l3: ".agent/prompts/{slug}/l3_details/"
  }

  return {
    l1: l1Summary,
    l2Content: l2Content,
    l3Content: l3Content,
    l2Path: outputPaths.l2,
    l3Path: outputPaths.l3
  }
}

async function saveL2L3ToFiles(aggregatedResult, skillConfig) {
  // Get active workload slug
  const slug = await getActiveWorkloadSlug()
  const skillName = skillConfig.name

  const l2Path = aggregatedResult.l2Path.replace("{slug}", slug)
  const l3Path = aggregatedResult.l3Path.replace("{slug}", slug)

  // Ensure directories exist
  await Bash(`mkdir -p "$(dirname ${l2Path})"`)
  await Bash(`mkdir -p "${l3Path}"`)

  // Write L2
  await Write({
    file_path: l2Path,
    content: aggregatedResult.l2Content
  })

  // Write L3
  await Write({
    file_path: `${l3Path}/full_analysis.md`,
    content: aggregatedResult.l3Content
  })

  console.log(`
L2/L3 saved to files:
  L2: ${l2Path}
  L3: ${l3Path}/full_analysis.md
`)
}
```

---

## 4. Integration Pattern

### 4.1 Include in Skill Body

Add this section at the START of skill execution logic:

```markdown
## Auto-Delegation Check

At skill invocation, execute auto-delegation check:

\`\`\`javascript
// Include auto-delegation module
// Reference: .claude/skills/shared/auto-delegation.md

const delegationDecision = checkAutoDelegation(SKILL_CONFIG, userRequest)

if (delegationDecision.shouldDelegate) {
  console.log(`Auto-delegation: ${delegationDecision.reason}`)

  // Analyze complexity
  const complexity = analyzeTaskComplexity(taskDescription, SKILL_CONFIG)

  // Execute delegation
  const result = await executeDelegation(taskDescription, complexity, SKILL_CONFIG)

  // Return L1 only (L2/L3 saved to files)
  return {
    status: "success",
    delegated: true,
    l1Summary: result.l1Summary,
    l2Path: result.l2Path,
    l3Path: result.l3Path,
    metrics: result.delegationMetrics
  }
}

// Otherwise, execute skill normally (no delegation)
\`\`\`
```

### 4.2 Required Frontmatter for Auto-Delegation

```yaml
agent_delegation:
  enabled: true
  default_mode: true  # Set to true for auto-delegation by default
  max_sub_agents: 3
  delegation_strategy: "complexity-based"  # or "phase-based", "scope-based"
  strategies:
    phase_based:
      description: "Delegate by implementation phase"
      use_when: "Multi-phase task"
    complexity_based:
      description: "Delegate by task complexity"
      use_when: "Complex task analysis"
  sub_agent_permissions:
    - Read
    - Write
    - Grep
    - Glob
    - Edit
  output_paths:
    l1: ".agent/prompts/{slug}/{skill-name}/l1_summary.yaml"
    l2: ".agent/prompts/{slug}/{skill-name}/l2_index.md"
    l3: ".agent/prompts/{slug}/{skill-name}/l3_details/"
  return_format:
    l1: "Summary only (max 500 tokens)"
    l2_path: "Path to L2 file"
    l3_path: "Path to L3 directory"
    requires_l2_read: false
```

---

## 5. Behavior Summary

| `enabled` | `default_mode` | User Request | Behavior |
|-----------|----------------|--------------|----------|
| `false` | N/A | N/A | Execute skill directly (no delegation) |
| `true` | `true` | N/A | Auto-delegate (complexity analysis + sub-agents) |
| `true` | `true` | `--no-delegate` | Execute directly (user override) |
| `true` | `false` | No flags | Execute directly |
| `true` | `false` | `--delegate` | Delegate (explicit request) |
| `true` | not set | No flags | Execute directly (safe default) |

---

## 6. Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | 2026-01-29 | Initial auto-delegation module |

---

*This module bridges frontmatter configuration with runtime execution behavior.*
