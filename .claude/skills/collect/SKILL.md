---
name: collect
description: |
  Aggregate worker results, verify completion, detect blockers.

  **V4.0 Changes (EFL Integration):**
  - P1: Skill as Sub-Orchestrator (agent delegation)
  - P3: General-Purpose Synthesis (Phase 3-A L2 horizontal + Phase 3-B L3 vertical)
  - P5: Phase 3.5 Review Gate (holistic verification)
  - P6: Agent Internal Feedback Loop (max 3 iterations)

  **V3.0 Changes:**
  - Multi-source collection (files + git + session)
  - Fallback strategy when TaskList empty
  - Session-based workload tracking
user-invocable: true
disable-model-invocation: false
context: standard
model: opus
version: "4.0.0"
argument-hint: "[--all | --phase <phase-id> | --from-session | --from-git]"

# EFL Configuration (Enhanced Feedback Loop)
agent_delegation:
  enabled: true
  mode: "sub_orchestrator"
  description: "Collect delegates to specialized agents for structured data collection"
  agents:
    - type: "explore"
      role: "Phase 3-A L2 Horizontal - Cross-area consistency and gap detection"
      output_format: "L2 structured data (summaries, deliverables, metadata)"
    - type: "explore"
      role: "Phase 3-B L3 Vertical - Code reality check and reference accuracy"
      output_format: "L3 verification results (file checks, link validation)"
  return_format:
    l1: "Collection summary with confidence level"
    l2_path: ".agent/prompts/{workload}/collection_report.md"
    requires_l2_read: false

agent_internal_feedback_loop:
  enabled: true
  max_iterations: 3
  validation_criteria:
    completeness:
      - "All worker outputs collected"
      - "Deliverables identified and validated"
      - "Warnings and blockers documented"
    quality:
      - "Confidence level calculated accurately"
      - "Cross-references resolved"
      - "No missing file artifacts"
    internal_consistency:
      - "L1/L2/L3 hierarchy maintained"
      - "Metadata matches actual files"
      - "Progress tracking aligned with artifacts"

review_gate:
  enabled: true
  phase: "3.5"
  criteria:
    - "requirement_alignment: Collection covers all orchestrated tasks"
    - "design_flow_consistency: L2/L3 structure properly separated"
    - "gap_detection: Missing outputs identified"
    - "conclusion_clarity: Next action recommendations clear"
    - "integrity_verified: All artifacts pass SHA256 verification"
    - "chain_valid: Upstream manifest chain verified"
    - "no_staleness: No stale artifacts detected"
  auto_approve: false
  tamper_response:
    on_tampered: "BLOCK_SYNTHESIS"
    on_stale: "WARN_AND_CONTINUE"
    on_missing: "BLOCK_SYNTHESIS"
    integrity_threshold: 1.0

selective_feedback:
  enabled: true
  threshold: "MEDIUM"
  action_on_low: "log_only"
  action_on_medium_plus: "trigger_review_gate"

hooks:
  Setup:
    - shared/validation-feedback-loop.sh  # P4/P5/P6 integration
---

# /collect - Result Aggregation & Completion Verification

> **Version:** 4.1.0
> **Role:** Sub-Orchestrator for multi-source worker result aggregation (EFL Pattern)
> **Architecture:** Agent Delegation + L2/L3 Structured Collection + Review Gate + Semantic Integrity

---

## 1. Purpose

**Collection Sub-Orchestrator** (P1) that:
1. **Orchestration**: Delegates collection to specialized agents (not direct execution)
2. **Phase 3-A (L2 Horizontal)**: Cross-area consistency and gap detection (P3)
3. **Phase 3-B (L3 Vertical)**: Code reality check and reference accuracy validation (P3)
4. **Phase 3.5 Review Gate**: Holistic verification before synthesis (P5)
5. **Internal Feedback Loop**: Agent self-validation with max 3 iterations (P6)
6. **Multi-Source**: Files + Git + Session + Workload tracking (V3.0 feature)

### Enhanced Feedback Loop (EFL) Integration

| Pattern | Implementation |
|---------|----------------|
| **P1: Sub-Orchestrator** | Skill conducts agents, doesn't execute directly |
| **P3: General-Purpose** | Phase 3-A/3-B structure (L2 horizontal + L3 vertical) |
| **P5: Review Gate** | Phase 3.5 holistic verification before synthesis |
| **P6: Internal Loop** | Agent self-validation (max 3 iterations) |
| **P4: Selective Feedback** | Severity-based threshold (MEDIUM+) |

### Key Changes in V3.0

| Feature | V2.1 (Old) | V3.0 (New) |
|---------|------------|-----------|
| **Primary Source** | TaskList API | File artifacts (`.agent/outputs/`) |
| **Fallback** | None | Git + Session + Workload tracking |
| **Empty Task API** | Fail | Continue with file-based collection |
| **Workload Scope** | Global only | Multi-workload support |

---

## 2. Invocation

### User Syntax

```bash
# Auto-detect collection sources
/collect
/collect --all

# Specific phase
/collect --phase phase1

# Force collection from specific source
/collect --from-session    # Use session history
/collect --from-git        # Use git commits
/collect --from-files      # Only file artifacts
```

### Arguments

| Argument | Description |
|----------|-------------|
| `--all` | Collect all available outputs |
| `--phase <id>` | Collect specific phase only |
| `--from-session` | Use session history as source |
| `--from-git` | Use recent git commits |
| `--from-files` | Only file artifacts (default) |
| `--workload <slug>` | Specific workload (defaults to active) |

---

## 3. Execution Protocol (EFL Pattern)

### Overview: Sub-Orchestrator Flow

```
/collect (Main Skill - Orchestrator)
    │
    ├─▶ Phase 0: Setup & Workload Detection
    │
    ├─▶ Phase 1: Agent Delegation (P1)
    │   ├─▶ Agent 1 (Explore): Phase 3-A L2 Horizontal
    │   │   └─▶ Internal Loop (P6): Self-validate, max 3 iterations
    │   └─▶ Agent 2 (Explore): Phase 3-B L3 Vertical
    │       └─▶ Internal Loop (P6): Self-validate, max 3 iterations
    │
    ├─▶ Phase 2: Aggregate L2/L3 Results (P3)
    │
    ├─▶ Phase 3: Selective Feedback Check (P4)
    │   └─▶ If MEDIUM+ severity → Trigger iteration
    │
    ├─▶ Phase 3.5: Review Gate (P5)
    │   └─▶ Holistic verification (requirement_alignment, etc.)
    │
    └─▶ Phase 4: Generate L1 Collection Report
        └─▶ Return to /synthesis with L1 summary + L2 path
```

### 3.0 Phase 0: Determine Active Workload

```javascript
async function determineActiveWorkload(args) {
  // 1. Check for explicit --workload flag
  if (args.includes('--workload')) {
    const idx = args.indexOf('--workload')
    return args[idx + 1]
  }

  // 2. Read _active_workload.yaml
  const activeWorkloadPath = '.agent/prompts/_active_workload.yaml'

  try {
    const content = await Read({ file_path: activeWorkloadPath })
    const match = content.match(/activeWorkload:\s*"([^"]+)"/)
    if (match) {
      return match[1]
    }
  } catch (e) {
    // File doesn't exist, fall back to global
  }

  // 3. Fallback: use most recent workload directory
  const workloadDirs = await Bash({
    command: 'ls -t .agent/prompts/ | grep -E "^[a-z]" | head -1',
    description: 'Find most recent workload directory'
  })

  return workloadDirs.trim() || null
}
```

### 3.1 Phase 1: Agent Delegation (P1 - Sub-Orchestrator Pattern)

```javascript
// P1: Skill as Sub-Orchestrator - Delegates to agents instead of direct execution
async function delegateCollection(workloadSlug, options) {
  console.log("🎯 P1: Delegating collection to specialized agents...")

  // Source validation-feedback-loop.sh
  await Bash({
    command: 'source /home/palantir/.claude/skills/shared/validation-feedback-loop.sh',
    description: 'Load P4/P5/P6 feedback loop functions'
  })

  // Phase 3-A: L2 Horizontal Collection (Cross-area consistency)
  console.log("\n📊 Phase 3-A: L2 Horizontal Collection (Cross-area consistency)")
  const l2HorizontalResult = await delegateToAgent({
    agentType: 'explore',
    task: 'phase3a_l2_horizontal',
    prompt: generatePhase3APrompt(workloadSlug, options),
    validationCriteria: {
      required_sections: ['worker_outputs', 'deliverables', 'metadata'],
      completeness_checks: ['all_workers_covered', 'cross_references_resolved'],
      quality_thresholds: { confidence: 'medium' }
    }
  })

  // Phase 3-B: L3 Vertical Verification (Code reality check)
  console.log("\n🔍 Phase 3-B: L3 Vertical Verification (Code reality check)")
  const l3VerticalResult = await delegateToAgent({
    agentType: 'explore',
    task: 'phase3b_l3_vertical',
    prompt: generatePhase3BPrompt(workloadSlug, l2HorizontalResult),
    validationCriteria: {
      required_sections: ['file_existence', 'reference_accuracy', 'link_validation'],
      completeness_checks: ['all_files_verified', 'no_broken_references'],
      quality_thresholds: { verification_rate: 0.95 }
    }
  })

  return {
    l2Horizontal: l2HorizontalResult,
    l3Vertical: l3VerticalResult
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
    model: 'haiku'  // Use haiku for cost-effective agent execution
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

// Generate Phase 3-A prompt (L2 Horizontal - Cross-area consistency)
function generatePhase3APrompt(workloadSlug, options) {
  return `# Phase 3-A: L2 Horizontal Collection

**Objective:** Collect structured data across all worker outputs and identify cross-area gaps.

**Workload:** ${workloadSlug}

**Tasks:**
1. Scan all worker output directories:
   - .agent/prompts/${workloadSlug}/outputs/terminal-*/
   - .agent/outputs/terminal-*/
   - .agent/outputs/${workloadSlug}/

2. For each output file, extract:
   - Worker ID
   - Task ID (if present)
   - Deliverables (files created, features implemented)
   - Completion status
   - Timestamps

3. Cross-area analysis:
   - Identify gaps: Missing outputs, incomplete tasks
   - Check consistency: Do deliverables match orchestration plan?
   - Detect blockers: Are there unresolved dependencies?

4. Calculate confidence level:
   - HIGH: All workers reported, all tasks complete, deliverables verified
   - MEDIUM: Most workers reported, minor gaps acceptable
   - LOW: Significant gaps, missing critical outputs

**Output Format (L2 Structured Data):**
\`\`\`yaml
l2_horizontal:
  workers:
    - worker_id: terminal-b
      outputs_found: 3
      tasks_completed: [1, 2, 3]
      deliverables: [...]
    - worker_id: terminal-c
      outputs_found: 2
      tasks_completed: [4, 5]
      deliverables: [...]

  gaps:
    - type: missing_output
      worker: terminal-d
      task: 6

  cross_references:
    - file: /path/to/file.py
      mentioned_by: [terminal-b, terminal-c]
      verified: true

  confidence: MEDIUM
  reason: "Worker terminal-d output missing"
\`\`\`

**Collection Options:**
${JSON.stringify(options, null, 2)}
`
}

// Generate Phase 3-B prompt (L3 Vertical - Semantic Integrity Verification)
// V4.1: SHA256 hash-based verification using semantic-integrity.sh
function generatePhase3BPrompt(workloadSlug, l2Result) {
  const workers = extractWorkersFromL2(l2Result)

  return `# Phase 3-B: L3 Semantic Integrity Verification

**Objective:** Verify artifact integrity using SHA256 hashes - ensure worker outputs match their manifests and upstream chain is valid.

**Context from Phase 3-A (L2):**
- Confidence: ${l2Result.internalLoop?.confidence || 'unknown'}
- Workers identified: ${workers.length}

**Verification Tasks:**

1. Collect worker manifests:
   For each worker terminal:
   \`\`\`bash
   # Find manifest files
   ls .agent/prompts/${workloadSlug}/outputs/terminal-*/task-*-manifest.yaml 2>/dev/null
   ls .agent/outputs/terminal-*/task-*-manifest.yaml 2>/dev/null
   \`\`\`

2. Verify each manifest using semantic-integrity.sh:
   \`\`\`bash
   source .claude/skills/shared/semantic-integrity.sh
   # For each manifest file:
   verify_artifact_integrity "<file_path>" "<expected_hash>"
   \`\`\`

3. Verify upstream chain:
   \`\`\`bash
   verify_upstream_chain "${workloadSlug}" "orchestrate"
   \`\`\`

4. Classify results:
   - **VERIFIED**: Hash matches, file exists, upstream valid
   - **TAMPERED**: Hash mismatch (content modified after completion)
   - **MISSING**: File referenced but not found
   - **STALE**: Upstream chain broken

5. Calculate integrity_rate:
   - integrity_rate = verified_count / total_count
   - Target: >= 95%

**Workers to Verify:**
${workers.map((w, i) => `${i + 1}. ${w.worker_id} (tasks: ${w.tasks_completed?.join(', ') || 'N/A'})`).join('\n')}

**Output Format (L3 Semantic Integrity Results):**
\`\`\`yaml
l3_semantic_integrity:
  artifacts:
    - worker_id: terminal-b
      task_id: "9"
      manifest_path: .agent/outputs/terminal-b/task-9-manifest.yaml
      status: VERIFIED
      expected_hash: "abc123..."
      actual_hash: "abc123..."
      outputs:
        - path: .agent/outputs/terminal-b/semantic-integrity.sh
          status: VERIFIED
          hash: "def456..."

    - worker_id: terminal-c
      task_id: "10"
      manifest_path: .agent/outputs/terminal-c/task-10-manifest.yaml
      status: TAMPERED
      expected_hash: "xyz789..."
      actual_hash: "different..."
      reason: "Content modified after manifest generation"

  chain_verification:
    workload: "${workloadSlug}"
    upstream_phase: "orchestrate"
    chain_status: VERIFIED
    context_hash: "upstream_hash..."

  integrity_summary:
    total_artifacts: 5
    verified: 4
    tampered: 1
    missing: 0
    stale: 0
    integrity_rate: 0.80

  failed_verifications:
    - worker_id: terminal-c
      task_id: "10"
      status: TAMPERED
      reason: "Hash mismatch detected"
\`\`\`
`
}

// Extract workers from L2 result for Phase 3-B
function extractWorkersFromL2(l2Result) {
  if (l2Result.result && typeof l2Result.result === 'string') {
    const parsed = parseAgentResult(l2Result.result, 'l2_horizontal')
    return parsed.workers || []
  }
  return []
}

// =============================================================================
// verifySemanticIntegrity - SHA256 Hash-Based Verification (V4.1)
// Uses semantic-integrity.sh shared module
// =============================================================================
async function verifySemanticIntegrity(workloadSlug, workers) {
  console.log("  🔐 Running semantic integrity verification...")

  const integrityResults = {
    artifacts: [],
    chainVerification: null,
    summary: {
      total: 0,
      verified: 0,
      tampered: 0,
      missing: 0,
      stale: 0,
      integrityRate: 0
    },
    failedVerifications: []
  }

  // 1. Find all worker manifests
  const manifestPaths = [
    `.agent/prompts/${workloadSlug}/outputs/terminal-*/task-*-manifest.yaml`,
    `.agent/outputs/terminal-*/task-*-manifest.yaml`
  ]

  let manifestFiles = []
  for (const pattern of manifestPaths) {
    try {
      const files = await Glob({ pattern: pattern })
      manifestFiles = manifestFiles.concat(files)
    } catch (e) {
      // Pattern didn't match, continue
    }
  }

  console.log(`     Found ${manifestFiles.length} manifest files`)

  // 2. Verify each manifest
  for (const manifestPath of manifestFiles) {
    try {
      const manifestContent = await Read({ file_path: manifestPath })

      // Extract metadata from manifest
      const workerIdMatch = manifestPath.match(/terminal-([bcd])/)
      const taskIdMatch = manifestPath.match(/task-(\d+)-manifest/)

      const workerId = workerIdMatch ? `terminal-${workerIdMatch[1]}` : 'unknown'
      const taskId = taskIdMatch ? taskIdMatch[1] : 'unknown'

      // Call semantic-integrity.sh to verify
      const verifyResult = await Bash({
        command: `source .claude/skills/shared/semantic-integrity.sh 2>/dev/null && \
                  verify_artifact_integrity "${manifestPath}" ""`,
        description: `Verify integrity of ${manifestPath}`
      })

      const resultJson = JSON.parse(verifyResult.trim())

      const artifact = {
        worker_id: workerId,
        task_id: taskId,
        manifest_path: manifestPath,
        status: resultJson.status || 'UNKNOWN',
        expected_hash: resultJson.expected_hash || null,
        actual_hash: resultJson.actual_hash || null,
        outputs: []
      }

      // Extract output files from manifest and verify each
      const outputsMatch = manifestContent.match(/outputs:\s*\n([\s\S]*?)(?:\n\n|integrity:|$)/)
      if (outputsMatch) {
        const outputLines = outputsMatch[1].match(/path:\s*"([^"]+)"/g) || []
        for (const line of outputLines) {
          const pathMatch = line.match(/path:\s*"([^"]+)"/)
          if (pathMatch) {
            const outputPath = pathMatch[1]
            const outputVerify = await Bash({
              command: `source .claude/skills/shared/semantic-integrity.sh 2>/dev/null && \
                        verify_artifact_integrity "${outputPath}" "" 2>/dev/null || echo '{"status":"MISSING"}'`,
              description: `Verify output ${outputPath}`
            })

            try {
              const outputResult = JSON.parse(outputVerify.trim())
              artifact.outputs.push({
                path: outputPath,
                status: outputResult.status || 'UNKNOWN',
                hash: outputResult.actual_hash || null
              })
            } catch (e) {
              artifact.outputs.push({
                path: outputPath,
                status: 'MISSING',
                hash: null
              })
            }
          }
        }
      }

      integrityResults.artifacts.push(artifact)
      integrityResults.summary.total++

      // Update counters
      switch (artifact.status) {
        case 'VERIFIED': integrityResults.summary.verified++; break
        case 'TAMPERED':
          integrityResults.summary.tampered++
          integrityResults.failedVerifications.push({
            worker_id: workerId,
            task_id: taskId,
            status: 'TAMPERED',
            reason: 'Hash mismatch detected'
          })
          break
        case 'MISSING':
          integrityResults.summary.missing++
          integrityResults.failedVerifications.push({
            worker_id: workerId,
            task_id: taskId,
            status: 'MISSING',
            reason: 'Manifest file not found or unreadable'
          })
          break
        case 'STALE':
          integrityResults.summary.stale++
          integrityResults.failedVerifications.push({
            worker_id: workerId,
            task_id: taskId,
            status: 'STALE',
            reason: 'Upstream chain broken'
          })
          break
      }

    } catch (e) {
      console.log(`     ⚠️  Failed to verify ${manifestPath}: ${e.message}`)
      integrityResults.summary.missing++
    }
  }

  // 3. Verify upstream chain
  try {
    const chainResult = await Bash({
      command: `source .claude/skills/shared/semantic-integrity.sh 2>/dev/null && \
                verify_upstream_chain "${workloadSlug}" "orchestrate"`,
      description: 'Verify upstream chain integrity'
    })

    const chainJson = JSON.parse(chainResult.trim())
    integrityResults.chainVerification = {
      workload: workloadSlug,
      upstream_phase: 'orchestrate',
      chain_status: chainJson.chain_valid ? 'VERIFIED' : 'BROKEN',
      context_hash: chainJson.context_hash || null,
      details: chainJson.phases || []
    }

    // If chain is broken, mark all as STALE
    if (!chainJson.chain_valid) {
      for (const artifact of integrityResults.artifacts) {
        if (artifact.status === 'VERIFIED') {
          artifact.status = 'STALE'
          integrityResults.summary.verified--
          integrityResults.summary.stale++
          integrityResults.failedVerifications.push({
            worker_id: artifact.worker_id,
            task_id: artifact.task_id,
            status: 'STALE',
            reason: 'Upstream chain integrity broken'
          })
        }
      }
    }
  } catch (e) {
    console.log(`     ⚠️  Chain verification failed: ${e.message}`)
    integrityResults.chainVerification = {
      workload: workloadSlug,
      upstream_phase: 'orchestrate',
      chain_status: 'UNKNOWN',
      context_hash: null,
      details: []
    }
  }

  // 4. Calculate integrity rate
  if (integrityResults.summary.total > 0) {
    integrityResults.summary.integrityRate =
      integrityResults.summary.verified / integrityResults.summary.total
  }

  console.log(`     ✅ Integrity check complete: ${integrityResults.summary.verified}/${integrityResults.summary.total} verified (${(integrityResults.summary.integrityRate * 100).toFixed(1)}%)`)

  return integrityResults
}

// Fallback: Multi-Source Collection (V3.0 legacy - used when agent delegation fails)
async function collectFromMultipleSources(workloadSlug, options) {
  console.log("⚠️  Fallback: Using multi-source collection (agent delegation unavailable)")

  const sources = {
    files: null,
    tasks: null,
    git: null,
    session: null,
    workload: null
  }

  // Source 1: File artifacts (PRIMARY)
  console.log("📁 Checking file artifacts...")
  sources.files = await collectFromFiles(workloadSlug)

  // Source 2: Workload _progress.yaml
  console.log("📋 Checking workload progress...")
  sources.workload = await collectFromWorkloadProgress(workloadSlug)

  // Source 3: Native Task API (if available)
  console.log("✅ Checking Task API...")
  try {
    const taskList = await TaskList()
    sources.tasks = {
      available: true,
      tasks: taskList
    }
  } catch (e) {
    sources.tasks = { available: false, reason: "No tasks found" }
  }

  // Source 4: Git history (FALLBACK)
  if (options.fromGit || (sources.files.count === 0 && sources.tasks.available === false)) {
    console.log("🔍 Checking git history...")
    sources.git = await collectFromGit()
  }

  // Source 5: Session history (LAST RESORT)
  if (options.fromSession) {
    console.log("💬 Checking session history...")
    sources.session = await collectFromSession()
  }

  return sources
}
```

### 3.3 Source Collectors

#### 3.3.1 File Artifacts Collector

```javascript
async function collectFromFiles(workloadSlug) {
  // 1. Check workload-specific outputs
  let outputPaths = [
    `.agent/outputs/${workloadSlug}/`,
    `.agent/outputs/Worker/`,
    `.agent/outputs/terminal-*/`,
    `.agent/outputs/*/`
  ]

  let outputs = []

  for (const pattern of outputPaths) {
    try {
      const files = await Glob({ pattern: pattern + '*.md' })
      for (const file of files) {
        const content = await Read({ file_path: file })
        outputs.push({
          source: 'file',
          path: file,
          content: content,
          metadata: extractMetadata(content)
        })
      }
    } catch (e) {
      // Path doesn't exist, continue
    }
  }

  return {
    source: 'files',
    count: outputs.length,
    outputs: outputs
  }
}
```

#### 3.3.2 Workload Progress Collector

```javascript
async function collectFromWorkloadProgress(workloadSlug) {
  const progressPaths = [
    `.agent/prompts/${workloadSlug}/_progress.yaml`,
    `.agent/prompts/_progress.yaml`  // Global fallback
  ]

  for (const path of progressPaths) {
    try {
      const content = await Read({ file_path: path })

      // Parse YAML to extract completed tasks
      const completedTasks = extractCompletedTasksFromYaml(content)

      return {
        source: 'workload_progress',
        path: path,
        workloadSlug: workloadSlug,
        completedTasks: completedTasks,
        totalPhases: extractTotalPhases(content)
      }
    } catch (e) {
      // File doesn't exist, try next
    }
  }

  return {
    source: 'workload_progress',
    available: false
  }
}
```

#### 3.3.3 Git History Collector

```javascript
async function collectFromGit() {
  // Get recent commits (last 10)
  const gitLog = await Bash({
    command: `git log --oneline --no-decorate -10 --format="%h|%s|%an|%ad" --date=short`,
    description: 'Get recent git commits'
  })

  const commits = gitLog.split('\n').filter(Boolean).map(line => {
    const [hash, subject, author, date] = line.split('|')
    return { hash, subject, author, date }
  })

  // Get changed files in recent commits
  const changedFiles = await Bash({
    command: `git diff --name-only HEAD~10..HEAD`,
    description: 'Get changed files'
  })

  return {
    source: 'git',
    commits: commits,
    changedFiles: changedFiles.split('\n').filter(Boolean)
  }
}
```

#### 3.3.4 Session History Collector

```javascript
async function collectFromSession() {
  // Read current session file
  const sessionFiles = await Glob({ pattern: '.agent/tmp/sessions/session_*.json' })

  if (sessionFiles.length === 0) {
    return { source: 'session', available: false }
  }

  // Get most recent session
  const latestSession = sessionFiles[sessionFiles.length - 1]
  const sessionContent = await Read({ file_path: latestSession })
  const session = JSON.parse(sessionContent)

  return {
    source: 'session',
    path: latestSession,
    completedActions: extractCompletedActions(session)
  }
}
```

### 3.2 Phase 2: Aggregate L2/L3 Results (P3 - General-Purpose Synthesis)

```javascript
// P3: Aggregate Phase 3-A (L2 Horizontal) and Phase 3-B (L3 Vertical) results
// V4.1: Includes Semantic Integrity verification results
async function aggregateL2L3Results(delegationResult, workloadSlug) {
  console.log("\n📦 P3: Aggregating L2/L3 results...")

  const { l2Horizontal, l3Vertical } = delegationResult

  // Extract data from agent results
  const l2Data = parseAgentResult(l2Horizontal.result, 'l2_horizontal')
  const l3Data = parseAgentResult(l3Vertical.result, 'l3_semantic_integrity')

  // Run semantic integrity verification (V4.1)
  const workers = l2Data.workers || []
  const semanticIntegrity = await verifySemanticIntegrity(workloadSlug, workers)

  // Merge L2 and L3 into structured collection
  const aggregated = {
    // From L2 Horizontal (Cross-area consistency)
    workers: l2Data.workers || [],
    gaps: l2Data.gaps || [],
    crossReferences: l2Data.cross_references || [],
    l2Confidence: l2Data.confidence || 'unknown',

    // From L3 Vertical - Semantic Integrity (V4.1)
    semanticIntegrity: semanticIntegrity,
    fileChecks: l3Data.file_checks || [],
    referenceChecks: l3Data.reference_checks || [],
    verificationRate: semanticIntegrity.summary.integrityRate || 0,
    failedVerifications: semanticIntegrity.failedVerifications || [],

    // Combined metrics
    completedWork: [],
    deliverables: [],
    warnings: [],
    confidence: 'unknown'
  }

  // Combine confidence from L2 and L3 (using integrity rate instead of file checks)
  aggregated.confidence = calculateCombinedConfidence(
    aggregated.l2Confidence,
    aggregated.verificationRate
  )

  // Extract completed work from L2 workers
  for (const worker of aggregated.workers) {
    aggregated.completedWork.push({
      type: 'worker_output',
      worker: worker.worker_id,
      tasksCompleted: worker.tasks_completed,
      deliverables: worker.deliverables,
      outputsFound: worker.outputs_found
    })

    // Add deliverables
    aggregated.deliverables.push(...(worker.deliverables || []))
  }

  // Warnings from L2 gaps
  for (const gap of aggregated.gaps) {
    aggregated.warnings.push(`Gap detected: ${gap.type} - ${gap.worker} task ${gap.task}`)
  }

  // Warnings from L3 verification failures
  for (const failure of aggregated.failedVerifications) {
    aggregated.warnings.push(`Verification failed: ${failure.path} - ${failure.reason}`)
  }

  // P6: Track internal loop iterations
  aggregated.internalLoopMetadata = {
    l2HorizontalIterations: l2Horizontal.internalLoop.iterations_used,
    l3VerticalIterations: l3Vertical.internalLoop.iterations_used,
    totalIterations: l2Horizontal.internalLoop.iterations_used + l3Vertical.internalLoop.iterations_used
  }

  console.log(`  ✅ Aggregation complete: ${aggregated.completedWork.length} workers, confidence: ${aggregated.confidence}`)
  console.log(`  📊 P6: Total internal iterations: ${aggregated.internalLoopMetadata.totalIterations}`)

  return aggregated
}

// Calculate combined confidence from L2 and L3
function calculateCombinedConfidence(l2Confidence, verificationRate) {
  const l2Score = { 'HIGH': 3, 'MEDIUM': 2, 'LOW': 1, 'unknown': 0 }[l2Confidence] || 0
  const l3Score = verificationRate >= 0.95 ? 3 : verificationRate >= 0.80 ? 2 : 1

  const combinedScore = Math.floor((l2Score + l3Score) / 2)

  if (combinedScore >= 3) return 'high'
  if (combinedScore >= 2) return 'medium'
  return 'low'
}

// Fallback aggregation (V3.0 legacy)
function aggregateCollectedData(sources) {
  console.log("⚠️  Fallback: Using legacy aggregation (V3.0)")

  const aggregated = {
    completedWork: [],
    deliverables: [],
    warnings: [],
    confidence: 'unknown'
  }

  // Priority 1: File artifacts (HIGHEST confidence)
  if (sources.files.count > 0) {
    aggregated.completedWork.push(...sources.files.outputs.map(o => ({
      type: 'file_artifact',
      title: o.metadata.title || extractTitle(o.path),
      path: o.path,
      summary: extractL1Summary(o.content),
      deliverables: extractDeliverables(o.content)
    })))
    aggregated.confidence = 'high'
  }

  // Priority 2: Workload progress
  if (sources.workload.available) {
    aggregated.completedWork.push({
      type: 'workload_tracking',
      completedTasks: sources.workload.completedTasks,
      totalPhases: sources.workload.totalPhases
    })
    if (aggregated.confidence === 'unknown') {
      aggregated.confidence = 'medium'
    }
  }

  // Priority 3: Git history
  if (sources.git) {
    aggregated.completedWork.push({
      type: 'git_commits',
      commits: sources.git.commits,
      changedFiles: sources.git.changedFiles
    })
    if (aggregated.confidence === 'unknown') {
      aggregated.confidence = 'low'
    }
  }

  // Warnings
  if (sources.files.count === 0) {
    aggregated.warnings.push("No file artifacts found in .agent/outputs/")
  }
  if (!sources.tasks.available) {
    aggregated.warnings.push("TaskList empty (tasks already completed)")
  }

  return aggregated
}
```

### 3.3 Phase 3: Selective Feedback Check (P4)

```javascript
// P4: Check if collection result requires feedback based on severity
async function checkSelectiveFeedback(aggregated) {
  console.log("\n🔍 P4: Checking selective feedback requirement...")

  // Prepare validation result JSON
  const validationResult = {
    gate: 'COLLECT',
    result: aggregated.confidence === 'high' ? 'passed' :
            aggregated.confidence === 'medium' ? 'passed_with_warnings' : 'failed',
    errors: aggregated.failedVerifications?.length || 0,
    warnings: aggregated.warnings.length
  }

  // Call check_selective_feedback from validation-feedback-loop.sh
  const feedbackCheck = await Bash({
    command: `source /home/palantir/.claude/skills/shared/validation-feedback-loop.sh && \
              check_selective_feedback "/home/palantir/.claude/skills/collect/SKILL.md" '${JSON.stringify(validationResult)}'`,
    description: 'P4: Check if feedback loop required'
  })

  const feedbackResult = JSON.parse(feedbackCheck)

  console.log(`  📊 Severity: ${feedbackResult.severity}, Needs feedback: ${feedbackResult.needs_feedback}`)

  if (feedbackResult.needs_feedback) {
    console.log(`  ⚠️  Feedback required: ${feedbackResult.reason}`)
    console.log(`  💡 Suggested action: Review gaps and re-run collection if needed`)
  }

  return feedbackResult
}
```

### 3.4 Phase 3.5: Review Gate (P5)

```javascript
// P5: Execute Phase 3.5 Review Gate - Holistic verification before synthesis
async function executeReviewGate(aggregated) {
  console.log("\n🚪 P5: Executing Phase 3.5 Review Gate...")

  // Prepare result JSON for review
  const reviewInput = {
    tasks: aggregated.completedWork,
    metadata: {
      complexity: aggregated.workers.length > 3 ? 'complex' : 'moderate',
      confidence: aggregated.confidence,
      verificationRate: aggregated.verificationRate
    },
    deliverables: aggregated.deliverables,
    warnings: aggregated.warnings,
    gaps: aggregated.gaps
  }

  // Call review_gate from validation-feedback-loop.sh
  const reviewResult = await Bash({
    command: `source /home/palantir/.claude/skills/shared/validation-feedback-loop.sh && \
              review_gate "collect" '${JSON.stringify(reviewInput)}' "false"`,
    description: 'P5: Execute review gate'
  })

  const review = JSON.parse(reviewResult)

  console.log(`  📋 Review result: ${review.approved ? '✅ APPROVED' : '❌ NEEDS REVIEW'}`)

  if (review.warnings.length > 0) {
    console.log(`  ⚠️  Warnings:`)
    review.warnings.forEach(w => console.log(`     - ${w}`))
  }

  if (review.errors.length > 0) {
    console.log(`  ❌ Errors:`)
    review.errors.forEach(e => console.log(`     - ${e}`))
  }

  // Review criteria (P5 spec):
  const criteriaChecks = {
    requirement_alignment: checkRequirementAlignment(aggregated),
    design_flow_consistency: checkL2L3Separation(aggregated),
    gap_detection: aggregated.gaps.length > 0 ? 'gaps_identified' : 'no_gaps',
    conclusion_clarity: aggregated.confidence !== 'unknown'
  }

  // V4.1: Semantic Integrity criteria
  const integrityChecks = checkSemanticIntegrity(aggregated)
  criteriaChecks.integrity_verified = integrityChecks.allVerified
  criteriaChecks.chain_valid = integrityChecks.chainValid
  criteriaChecks.no_staleness = integrityChecks.noStaleness

  console.log(`\n  📊 Review Criteria:`)
  console.log(`     - Requirement Alignment: ${criteriaChecks.requirement_alignment}`)
  console.log(`     - L2/L3 Separation: ${criteriaChecks.design_flow_consistency}`)
  console.log(`     - Gap Detection: ${criteriaChecks.gap_detection}`)
  console.log(`     - Conclusion Clarity: ${criteriaChecks.conclusion_clarity}`)
  console.log(`     - Integrity Verified: ${criteriaChecks.integrity_verified ? '✅' : '❌'}`)
  console.log(`     - Chain Valid: ${criteriaChecks.chain_valid ? '✅' : '❌'}`)
  console.log(`     - No Staleness: ${criteriaChecks.no_staleness ? '✅' : '❌'}`)

  // V4.1: Tamper response handling
  const tamperResponse = evaluateTamperResponse(integrityChecks)
  if (tamperResponse.action === 'BLOCK_SYNTHESIS') {
    console.log(`\n  🚫 BLOCKING SYNTHESIS: ${tamperResponse.reason}`)
    review.approved = false
    review.errors.push(tamperResponse.reason)
  } else if (tamperResponse.action === 'WARN_AND_CONTINUE') {
    console.log(`\n  ⚠️  WARNING: ${tamperResponse.reason}`)
    review.warnings.push(tamperResponse.reason)
  }

  return {
    approved: review.approved && integrityChecks.passesThreshold,
    criteriaChecks: criteriaChecks,
    integrityChecks: integrityChecks,
    tamperResponse: tamperResponse,
    review: review
  }
}

// Check if collection covers all orchestrated tasks
function checkRequirementAlignment(aggregated) {
  // Compare completed tasks with orchestration plan
  const totalTasksOrchestrated = aggregated.workers.reduce(
    (sum, w) => sum + (w.tasks_completed?.length || 0), 0
  )

  if (totalTasksOrchestrated === 0) {
    return 'no_tasks_orchestrated'
  }

  const gapCount = aggregated.gaps.length
  const alignmentRate = (totalTasksOrchestrated - gapCount) / totalTasksOrchestrated

  if (alignmentRate >= 0.95) return 'fully_aligned'
  if (alignmentRate >= 0.80) return 'mostly_aligned'
  return 'misaligned'
}

// Check if L2/L3 structure is properly separated
function checkL2L3Separation(aggregated) {
  const hasL2Data = aggregated.workers && aggregated.workers.length > 0
  const hasL3Data = aggregated.fileChecks && aggregated.fileChecks.length > 0

  if (hasL2Data && hasL3Data) return 'properly_separated'
  if (hasL2Data || hasL3Data) return 'partial_separation'
  return 'no_separation'
}

// V4.1: Check Semantic Integrity from aggregated results
function checkSemanticIntegrity(aggregated) {
  const integrity = aggregated.semanticIntegrity || {}
  const summary = integrity.summary || { total: 0, verified: 0, tampered: 0, missing: 0, stale: 0 }
  const chainVerification = integrity.chainVerification || { valid: true }

  const allVerified = summary.verified === summary.total && summary.total > 0
  const chainValid = chainVerification.valid === true
  const noStaleness = summary.stale === 0
  const integrityRate = summary.integrityRate || (summary.total > 0 ? summary.verified / summary.total : 1.0)

  // Threshold from frontmatter (default 1.0)
  const threshold = 1.0
  const passesThreshold = integrityRate >= threshold

  return {
    allVerified,
    chainValid,
    noStaleness,
    integrityRate,
    passesThreshold,
    summary,
    hasTampered: summary.tampered > 0,
    hasMissing: summary.missing > 0,
    hasStale: summary.stale > 0
  }
}

// V4.1: Evaluate tamper response based on integrity check results
function evaluateTamperResponse(integrityChecks) {
  // Priority: TAMPERED > MISSING > STALE
  if (integrityChecks.hasTampered) {
    return {
      action: 'BLOCK_SYNTHESIS',
      reason: `Tampered artifacts detected (${integrityChecks.summary.tampered} files) - SHA256 hash mismatch`,
      severity: 'CRITICAL'
    }
  }

  if (integrityChecks.hasMissing) {
    return {
      action: 'BLOCK_SYNTHESIS',
      reason: `Missing artifacts detected (${integrityChecks.summary.missing} files) - Output files not found`,
      severity: 'HIGH'
    }
  }

  if (integrityChecks.hasStale) {
    return {
      action: 'WARN_AND_CONTINUE',
      reason: `Stale artifacts detected (${integrityChecks.summary.stale} files) - Files modified after manifest generation`,
      severity: 'MEDIUM'
    }
  }

  if (!integrityChecks.chainValid) {
    return {
      action: 'BLOCK_SYNTHESIS',
      reason: 'Upstream chain validation failed - Manifest chain broken',
      severity: 'CRITICAL'
    }
  }

  return {
    action: 'PASS',
    reason: 'All integrity checks passed',
    severity: 'INFO'
  }
}
```

### 3.5 Phase 4: Generate Collection Report (L1/L2 Output)

```javascript
// Generate L1 (summary) and L2 (detailed report) collection outputs
async function generateCollectionReport(aggregated, reviewGateResult, workloadSlug, options) {
  console.log("\n📝 Generating L1/L2 collection report...")

  const timestamp = new Date().toISOString()

  // L2: Detailed Collection Report (stored in file)
  const l2ReportContent = generateL2Report(aggregated, reviewGateResult, workloadSlug, timestamp, options)

  // L1: Summary for /synthesis (returned to caller)
  const l1Summary = generateL1Summary(aggregated, reviewGateResult, workloadSlug, timestamp)

  // Workload-scoped output path
  const reportDir = workloadSlug
    ? `.agent/prompts/${workloadSlug}`
    : `.agent/outputs`  // Fallback for global (deprecated)

  const l2ReportPath = `${reportDir}/collection_report.md`

  // Save L2 report to file
  await Bash({ command: `mkdir -p ${reportDir}`, description: 'Create output directory' })
  await Write({ file_path: l2ReportPath, content: l2ReportContent })

  console.log(`  ✅ L2 report saved: ${l2ReportPath}`)
  console.log(`  📊 L1 summary generated (${l1Summary.length} chars)`)

  return {
    l1Summary: l1Summary,
    l2ReportPath: l2ReportPath,
    confidence: aggregated.confidence,
    reviewApproved: reviewGateResult.approved
  }
}

// Generate L2 Detailed Report (full context for synthesis)
function generateL2Report(aggregated, reviewGateResult, workloadSlug, timestamp, options) {
  return `# Collection Report (L2 - Detailed)

> **Generated:** ${timestamp}
> **Workload:** ${workloadSlug || 'global'}
> **Version:** 4.0.0 (EFL Pattern)
> **Confidence:** ${aggregated.confidence}
> **Review Gate:** ${reviewGateResult.approved ? '✅ APPROVED' : '⚠️ NEEDS REVIEW'}

---

## Executive Summary (L1)

**Collection completed with ${aggregated.confidence} confidence.**

- Workers: ${aggregated.workers.length}
- Completed Tasks: ${aggregated.completedWork.length}
- Deliverables: ${aggregated.deliverables.length}
- Gaps Detected: ${aggregated.gaps.length}
- Verification Rate: ${(aggregated.verificationRate * 100).toFixed(1)}%

${reviewGateResult.approved ? '✅ Ready for /synthesis' : '⚠️ Review required before synthesis'}

---

## Phase 3-A: L2 Horizontal Collection (Cross-Area Consistency)

### Workers Overview

${aggregated.workers.map(worker => `
#### ${worker.worker_id}

- **Outputs Found:** ${worker.outputs_found}
- **Tasks Completed:** ${worker.tasks_completed?.join(', ') || 'N/A'}
- **Deliverables:**
${(worker.deliverables || []).map(d => `  - ${d}`).join('\n') || '  - None specified'}
`).join('\n')}

### Gaps Detected

${aggregated.gaps.length > 0 ? aggregated.gaps.map(gap => `
- **Type:** ${gap.type}
- **Worker:** ${gap.worker}
- **Task:** ${gap.task}
- **Impact:** ${gap.impact || 'Unknown'}
`).join('\n') : '*No gaps detected*'}

### Cross-References

${aggregated.crossReferences.length > 0 ? aggregated.crossReferences.map(ref => `
- **File:** \`${ref.file}\`
- **Mentioned by:** ${ref.mentioned_by.join(', ')}
- **Verified:** ${ref.verified ? '✅' : '❌'}
`).join('\n') : '*No cross-references found*'}

---

## Phase 3-B: L3 Semantic Integrity Verification (V4.1)

> SHA256 hash-based verification using \`semantic-integrity.sh\`

### Artifact Integrity

${aggregated.semanticIntegrity?.artifacts?.length > 0 ? `
| Worker | Task | Manifest | Status | Hash Match |
|--------|------|----------|--------|------------|
${aggregated.semanticIntegrity.artifacts.map(artifact =>
  `| ${artifact.worker_id} | #${artifact.task_id} | \`${artifact.manifest_path.split('/').pop()}\` | ${getStatusEmoji(artifact.status)} ${artifact.status} | ${artifact.expected_hash === artifact.actual_hash ? '✅' : '❌'} |`
).join('\n')}
` : '*No manifests found for verification*'}

### Upstream Chain Verification

${aggregated.semanticIntegrity?.chainVerification ? `
- **Workload:** ${aggregated.semanticIntegrity.chainVerification.workload}
- **Upstream Phase:** ${aggregated.semanticIntegrity.chainVerification.upstream_phase}
- **Chain Status:** ${getStatusEmoji(aggregated.semanticIntegrity.chainVerification.chain_status)} ${aggregated.semanticIntegrity.chainVerification.chain_status}
- **Context Hash:** \`${aggregated.semanticIntegrity.chainVerification.context_hash || 'N/A'}\`
` : '*Chain verification not performed*'}

### Integrity Summary

- **Total Artifacts:** ${aggregated.semanticIntegrity?.summary?.total || 0}
- **Verified:** ${aggregated.semanticIntegrity?.summary?.verified || 0} ${getStatusEmoji('VERIFIED')}
- **Tampered:** ${aggregated.semanticIntegrity?.summary?.tampered || 0} ${aggregated.semanticIntegrity?.summary?.tampered > 0 ? '⚠️' : ''}
- **Missing:** ${aggregated.semanticIntegrity?.summary?.missing || 0}
- **Stale:** ${aggregated.semanticIntegrity?.summary?.stale || 0}
- **Integrity Rate:** ${((aggregated.semanticIntegrity?.summary?.integrityRate || 0) * 100).toFixed(1)}%

${aggregated.semanticIntegrity?.failedVerifications?.length > 0 ? `
### Failed Integrity Checks

${aggregated.semanticIntegrity.failedVerifications.map(failure => `
- **Worker:** ${failure.worker_id} | **Task:** #${failure.task_id}
- **Status:** ${getStatusEmoji(failure.status)} ${failure.status}
- **Reason:** ${failure.reason}
`).join('\n')}
` : '### ✅ All Integrity Checks Passed'}

---

## Phase 3.5: Review Gate Results (V4.1)

**Status:** ${reviewGateResult.approved ? '✅ APPROVED' : '❌ NEEDS REVIEW'}

### Review Criteria

| Criterion | Status |
|-----------|--------|
| Requirement Alignment | ${reviewGateResult.criteriaChecks.requirement_alignment} |
| Design Flow Consistency | ${reviewGateResult.criteriaChecks.design_flow_consistency} |
| Gap Detection | ${reviewGateResult.criteriaChecks.gap_detection} |
| Conclusion Clarity | ${reviewGateResult.criteriaChecks.conclusion_clarity} |
| **Integrity Verified** | ${reviewGateResult.criteriaChecks.integrity_verified ? '✅ Passed' : '❌ Failed'} |
| **Chain Valid** | ${reviewGateResult.criteriaChecks.chain_valid ? '✅ Valid' : '❌ Broken'} |
| **No Staleness** | ${reviewGateResult.criteriaChecks.no_staleness ? '✅ Fresh' : '⚠️ Stale'} |

### Tamper Response

- **Action:** ${reviewGateResult.tamperResponse?.action || 'PASS'}
- **Severity:** ${reviewGateResult.tamperResponse?.severity || 'INFO'}
${reviewGateResult.tamperResponse?.reason !== 'All integrity checks passed' ? `- **Reason:** ${reviewGateResult.tamperResponse?.reason}` : ''}

${reviewGateResult.review.warnings.length > 0 ? `
### Warnings

${reviewGateResult.review.warnings.map(w => `- ${w}`).join('\n')}
` : ''}

${reviewGateResult.review.errors.length > 0 ? `
### Errors

${reviewGateResult.review.errors.map(e => `- ${e}`).join('\n')}
` : ''}

---

## Deliverables Summary

${aggregated.deliverables.length > 0
  ? aggregated.deliverables.map((d, i) => `${i + 1}. ${d}`).join('\n')
  : '*No deliverables specified*'}

---

## Warnings & Issues

${aggregated.warnings.length > 0 ? aggregated.warnings.map(w => `- ⚠️ ${w}`).join('\n') : '*No warnings*'}

---

## Recommended Next Action

${getRecommendation(aggregated, reviewGateResult)}

---

## Enhanced Feedback Loop (EFL) Metadata

\`\`\`yaml
efl_metadata:
  version: "4.0.0"
  patterns_applied:
    - P1: Sub-Orchestrator (agent delegation)
    - P3: General-Purpose Synthesis (L2/L3 structure)
    - P5: Phase 3.5 Review Gate
    - P6: Agent Internal Feedback Loop

  agent_delegation:
    phase_3a_l2_horizontal:
      iterations: ${aggregated.internalLoopMetadata?.l2HorizontalIterations || 0}
      status: completed
    phase_3b_l3_vertical:
      iterations: ${aggregated.internalLoopMetadata?.l3VerticalIterations || 0}
      status: completed

  review_gate:
    approved: ${reviewGateResult.approved}
    criteria_met: ${Object.values(reviewGateResult.criteriaChecks).filter(c => c.includes('aligned') || c.includes('separated') || c.includes('identified') || c === true).length}/${Object.keys(reviewGateResult.criteriaChecks).length}

  collection_metadata:
    collected_at: "${timestamp}"
    workload_slug: "${workloadSlug || 'global'}"
    confidence: "${aggregated.confidence}"
    verification_rate: ${aggregated.verificationRate}
    collection_mode: "agent_delegation"
\`\`\`
`
}

// Generate L1 Summary (for /synthesis context - keep concise)
function generateL1Summary(aggregated, reviewGateResult, workloadSlug, timestamp) {
  return `# Collection Summary (L1)

**Workload:** ${workloadSlug || 'global'}
**Confidence:** ${aggregated.confidence}
**Review:** ${reviewGateResult.approved ? '✅ APPROVED' : '⚠️ NEEDS REVIEW'}

## Key Metrics
- Workers: ${aggregated.workers.length}
- Tasks Completed: ${aggregated.completedWork.length}
- Deliverables: ${aggregated.deliverables.length}
- Gaps: ${aggregated.gaps.length}
- Verification Rate: ${(aggregated.verificationRate * 100).toFixed(1)}%

## Status
${reviewGateResult.approved
  ? '✅ Collection complete. Ready for /synthesis.'
  : `⚠️ Review required: ${reviewGateResult.review.warnings.length} warning(s), ${reviewGateResult.review.errors.length} error(s)`}

## L2 Details
See: \`.agent/prompts/${workloadSlug}/collection_report.md\`

*Generated by /collect v4.1.0 (EFL Pattern + Semantic Integrity) at ${timestamp}*
`
}

// Get recommendation based on aggregated data and review gate result
function getRecommendation(aggregated, reviewGateResult) {
  if (reviewGateResult.approved && aggregated.confidence === 'high') {
    return `### ✅ Proceed to /synthesis

Collection is complete with high confidence and approved by review gate.

**Next Command:**
\`\`\`bash
/synthesis
\`\`\`
`
  } else if (reviewGateResult.approved && aggregated.confidence === 'medium') {
    return `### ⚠️ Review Recommended

Collection passed review gate but with medium confidence.

**Suggested Actions:**
1. Review gaps and warnings above
2. Verify critical deliverables manually
3. Proceed to /synthesis if acceptable: \`/synthesis --force\`
`
  } else {
    return `### ❌ Address Issues Before Synthesis

Collection failed review gate or has low confidence.

**Required Actions:**
1. Address review gate errors (see above)
2. Re-run collection: \`/collect --from-files\`
3. Or investigate gaps: Check worker outputs in \`.agent/outputs/\`

**Diagnostic Commands:**
\`\`\`bash
# Check worker outputs
ls -la .agent/outputs/terminal-*/

# Check workload progress
cat .agent/prompts/${aggregated.workloadSlug || 'global'}/_progress.yaml

# Re-run with git fallback
/collect --from-git
\`\`\`
`
  }
}
```

### 3.6 Helper Functions

```javascript
// Get status emoji for semantic integrity status (V4.1)
function getStatusEmoji(status) {
  switch (status) {
    case 'VERIFIED': return '✅'
    case 'TAMPERED': return '🔴'
    case 'MISSING': return '❓'
    case 'STALE': return '⚠️'
    case 'BROKEN': return '🔴'
    case 'UNKNOWN': return '❔'
    default: return '❔'
  }
}

// Parse agent result (extract YAML/JSON from agent output)
function parseAgentResult(agentOutput, expectedSection) {
  try {
    // Try to extract YAML block
    const yamlMatch = agentOutput.match(/```yaml\n([\s\S]*?)\n```/)
    if (yamlMatch) {
      // Simple YAML parsing (or use a library)
      return parseSimpleYaml(yamlMatch[1])
    }

    // Try to extract JSON block
    const jsonMatch = agentOutput.match(/```json\n([\s\S]*?)\n```/)
    if (jsonMatch) {
      return JSON.parse(jsonMatch[1])
    }

    // Fallback: look for section header
    const sectionRegex = new RegExp(`${expectedSection}:\\s*\\n([\\s\\S]*?)(?:\\n\\n|$)`, 'i')
    const sectionMatch = agentOutput.match(sectionRegex)
    if (sectionMatch) {
      return parseSimpleYaml(sectionMatch[1])
    }

    throw new Error(`Could not parse ${expectedSection} from agent output`)
  } catch (error) {
    console.error(`Parse error: ${error.message}`)
    return {}
  }
}

// Simple YAML parser (for basic structures)
function parseSimpleYaml(yamlText) {
  const lines = yamlText.split('\n')
  const result = {}
  let currentKey = null
  let currentArray = null

  for (const line of lines) {
    if (line.trim().startsWith('#') || line.trim() === '') continue

    // Key-value pair
    if (line.match(/^\s*[\w_]+:/)) {
      const [key, ...valueParts] = line.split(':')
      const value = valueParts.join(':').trim()

      currentKey = key.trim()

      if (value === '[]') {
        result[currentKey] = []
        currentArray = result[currentKey]
      } else if (value) {
        result[currentKey] = value.replace(/['"]/g, '')
        currentArray = null
      } else {
        result[currentKey] = {}
        currentArray = null
      }
    }
    // Array item
    else if (line.match(/^\s*-\s+/)) {
      const value = line.replace(/^\s*-\s+/, '').trim()
      if (currentArray) {
        currentArray.push(value.replace(/['"]/g, ''))
      }
    }
  }

  return result
}

// Extract internal loop metadata from agent result
function extractInternalLoopMetadata(agentOutput) {
  try {
    // Look for internal_feedback_loop section
    const loopMatch = agentOutput.match(/internal_feedback_loop:\s*\n([\s\S]*?)(?:\n\n|```|$)/)
    if (loopMatch) {
      const loopData = parseSimpleYaml(loopMatch[1])
      return {
        iterations_used: parseInt(loopData.iterations_used) || 1,
        final_validation_status: loopData.final_validation_status || 'unknown',
        issues_resolved: loopData.issues_resolved || [],
        remaining_issues: loopData.remaining_issues || []
      }
    }

    // Fallback: assume 1 iteration
    return {
      iterations_used: 1,
      final_validation_status: 'completed',
      issues_resolved: [],
      remaining_issues: []
    }
  } catch (error) {
    return {
      iterations_used: 1,
      final_validation_status: 'unknown',
      issues_resolved: [],
      remaining_issues: []
    }
  }
}

// Extract deliverables from L2 result
function extractDeliverablesFromL2(l2Result) {
  const deliverables = []

  if (l2Result.result && typeof l2Result.result === 'string') {
    const parsed = parseAgentResult(l2Result.result, 'l2_horizontal')

    if (parsed.workers) {
      for (const worker of parsed.workers) {
        if (worker.deliverables) {
          deliverables.push(...worker.deliverables.map(d => ({
            path: d,
            worker: worker.worker_id
          })))
        }
      }
    }
  }

  return deliverables
}

// Extract cross-references from L2 result
function extractCrossReferencesFromL2(l2Result) {
  if (l2Result.result && typeof l2Result.result === 'string') {
    const parsed = parseAgentResult(l2Result.result, 'l2_horizontal')
    return parsed.cross_references || []
  }
  return []
}

// Legacy helper (V3.0)
function extractMetadata(content) {
  const lines = content.split('\n')
  const metadata = {}

  for (const line of lines) {
    if (line.startsWith('**Task ID:**')) {
      metadata.taskId = line.split(':')[1].trim()
    } else if (line.startsWith('**Phase:**')) {
      metadata.phase = line.split(':')[1].trim()
    } else if (line.startsWith('**Owner:**')) {
      metadata.owner = line.split(':')[1].trim()
    } else if (line.startsWith('**Completed:**')) {
      metadata.completedAt = line.split(':')[1].trim()
    }
  }

  return metadata
}

function extractL1Summary(content) {
  const lines = content.split('\n')
  let summaryLines = []
  let inSummary = false

  for (const line of lines) {
    if (line.startsWith('# ')) {
      inSummary = true
      continue
    }
    if (inSummary) {
      if (line.startsWith('#') || line.startsWith('---')) break
      if (line.trim()) summaryLines.push(line.trim())
    }
  }

  return summaryLines.join(' ').substring(0, 500)
}

function extractDeliverables(content) {
  const lines = content.split('\n')
  const deliverables = []
  let inDeliverables = false

  for (const line of lines) {
    if (line.toLowerCase().includes('deliverable') ||
        line.toLowerCase().includes('output:') ||
        line.toLowerCase().includes('created:')) {
      inDeliverables = true
      continue
    }
    if (inDeliverables) {
      if (line.startsWith('#') || line.startsWith('---')) break
      if (line.trim().startsWith('- ') || line.trim().startsWith('* ')) {
        deliverables.push(line.trim().replace(/^[-*]\s*/, ''))
      }
    }
  }

  return deliverables
}

function formatCompletedWork(work) {
  switch (work.type) {
    case 'file_artifact':
      return `#### ${work.title}

**File:** \`${work.path}\`
${work.summary}

**Deliverables:**
${work.deliverables.map(d => `- ${d}`).join('\n')}`

    case 'workload_tracking':
      return `#### Workload Progress Tracking

- **Completed Tasks:** ${work.completedTasks.length}
- **Total Phases:** ${work.totalPhases}`

    case 'git_commits':
      return `#### Git Commit History

**Recent Commits:**
${work.commits.map(c => `- \`${c.hash}\` ${c.subject} (${c.date})`).join('\n')}

**Changed Files:**
${work.changedFiles.slice(0, 10).map(f => `- ${f}`).join('\n')}`

    default:
      return `#### ${work.type}\n\n(Details not available)`
  }
}

function getRecommendation(aggregated) {
  if (aggregated.confidence === 'high') {
    return `- [x] \`/synthesis\` - High confidence collection, proceed to validation`
  } else if (aggregated.confidence === 'medium') {
    return `- [ ] **Review** - Medium confidence, verify outputs before synthesis
- [ ] Check \`.agent/outputs/\` for missing artifacts
- [ ] Run \`/synthesis --force\` if confident`
  } else {
    return `- [ ] **Low Confidence** - Limited data collected
- [ ] Verify workers completed their tasks
- [ ] Check for missing output files
- [ ] Consider re-running collection with \`--from-git\` or \`--from-session\``
  }
}
```

---

## 4. Main Execution Flow (EFL Pattern)

```javascript
async function collect(args) {
  console.log("🔄 Starting collection with EFL Pattern (v4.1.0)...\n")

  // Parse arguments
  const options = {
    mode: args.includes('--all') ? 'all' : 'default',
    phaseId: args.includes('--phase') ? args[args.indexOf('--phase') + 1] : null,
    fromSession: args.includes('--from-session'),
    fromGit: args.includes('--from-git'),
    fromFiles: args.includes('--from-files'),
    forceAgentDelegation: args.includes('--agent-delegation'),
    skipReviewGate: args.includes('--skip-review')
  }

  try {
    // Phase 0: Determine active workload
    console.log("🔍 Phase 0: Determining active workload...")
    const workloadSlug = await determineActiveWorkload(args)
    console.log(`   Workload: ${workloadSlug || 'global'}\n`)

    // Phase 1: Agent Delegation (P1)
    let aggregated
    let usingAgentDelegation = true

    try {
      console.log("🎯 Phase 1: Agent Delegation (P1 - Sub-Orchestrator)")
      const delegationResult = await delegateCollection(workloadSlug, options)

      // Phase 2: Aggregate L2/L3 Results (P3)
      console.log("\n📦 Phase 2: Aggregating L2/L3 results (P3)")
      aggregated = await aggregateL2L3Results(delegationResult)

    } catch (delegationError) {
      console.log(`⚠️  Agent delegation failed: ${delegationError.message}`)
      console.log(`   Falling back to multi-source collection (V3.0)...\n`)

      usingAgentDelegation = false

      // Fallback to V3.0 multi-source collection
      const sources = await collectFromMultipleSources(workloadSlug, options)
      aggregated = aggregateCollectedData(sources)
    }

    // Phase 3: Selective Feedback Check (P4)
    if (usingAgentDelegation) {
      const feedbackCheck = await checkSelectiveFeedback(aggregated)

      if (feedbackCheck.needs_feedback) {
        console.log(`\n⚠️  P4: Feedback required (${feedbackCheck.severity})`)
        console.log(`   Consider re-running collection or manual review`)
      }
    }

    // Phase 3.5: Review Gate (P5)
    let reviewGateResult
    if (options.skipReviewGate) {
      console.log("\n⏭️  P5: Review Gate skipped (--skip-review)")
      reviewGateResult = {
        approved: true,
        criteriaChecks: { skipped: true },
        review: { warnings: [], errors: [] }
      }
    } else {
      reviewGateResult = await executeReviewGate(aggregated)
    }

    // Phase 4: Generate L1/L2 Collection Report
    console.log("\n📝 Phase 4: Generating L1/L2 report...")
    const reportResult = await generateCollectionReport(
      aggregated,
      reviewGateResult,
      workloadSlug,
      options
    )

    // Display summary
    console.log(`
╔════════════════════════════════════════════════════════════════╗
║                   Collection Complete (v4.1.0)                 ║
╚════════════════════════════════════════════════════════════════╝

📊 Results:
   Confidence: ${aggregated.confidence.toUpperCase()}
   Workers: ${aggregated.workers?.length || 0}
   Completed Tasks: ${aggregated.completedWork.length}
   Deliverables: ${aggregated.deliverables.length}
   Gaps: ${aggregated.gaps?.length || 0}

🔍 Verification:
   Rate: ${(aggregated.verificationRate * 100).toFixed(1)}%
   Failed: ${aggregated.failedVerifications?.length || 0}

🚪 Review Gate (P5):
   Status: ${reviewGateResult.approved ? '✅ APPROVED' : '❌ NEEDS REVIEW'}
   Warnings: ${reviewGateResult.review.warnings.length}
   Errors: ${reviewGateResult.review.errors.length}

📁 Output:
   L1 Summary: ${reportResult.l1Summary.length} chars
   L2 Report: ${reportResult.l2ReportPath}

🔄 EFL Metadata:
   Pattern: ${usingAgentDelegation ? 'Agent Delegation (P1)' : 'Fallback (V3.0)'}
   Internal Iterations: ${aggregated.internalLoopMetadata?.totalIterations || 0}

${aggregated.warnings.length > 0 ? `
⚠️  Warnings (${aggregated.warnings.length}):
${aggregated.warnings.slice(0, 3).map(w => `   - ${w}`).join('\n')}
${aggregated.warnings.length > 3 ? `   ... and ${aggregated.warnings.length - 3} more (see L2 report)` : ''}
` : ''}

═══════════════════════════════════════════════════════════════

${getNextActionMessage(aggregated, reviewGateResult)}
`)

    // Return L1 summary for /synthesis
    return {
      status: 'success',
      l1Summary: reportResult.l1Summary,
      l2ReportPath: reportResult.l2ReportPath,
      confidence: aggregated.confidence,
      reviewApproved: reviewGateResult.approved,
      completedWork: aggregated.completedWork.length,
      warnings: aggregated.warnings.length,
      eflMetadata: {
        version: '4.0.0',
        agentDelegation: usingAgentDelegation,
        internalIterations: aggregated.internalLoopMetadata?.totalIterations || 0,
        reviewGate: reviewGateResult.approved
      }
    }

  } catch (error) {
    console.error(`\n❌ Collection failed: ${error.message}`)
    console.error(`   Stack: ${error.stack}`)

    return {
      status: 'error',
      error: error.message,
      stack: error.stack
    }
  }
}

function getNextActionMessage(aggregated, reviewGateResult) {
  if (reviewGateResult.approved && aggregated.confidence === 'high') {
    return `✅ Next Step: /synthesis
   Collection passed all checks. Proceed to synthesis.`
  } else if (reviewGateResult.approved) {
    return `⚠️  Next Step: Review then /synthesis --force
   Collection passed review but with ${aggregated.confidence} confidence.
   Review warnings above before proceeding.`
  } else {
    return `❌ Action Required: Address Issues
   1. Review errors in L2 report: ${aggregated.workloadSlug}/collection_report.md
   2. Fix gaps and missing outputs
   3. Re-run collection: /collect

   Diagnostic: /collect --from-git (use git history fallback)`
  }
}
```

---

## 5. Error Handling

| Error | Detection | Recovery |
|-------|-----------|----------|
| **No workload found** | Empty _active_workload.yaml | Use most recent workload dir |
| **No file artifacts** | Glob returns empty | Fall back to git/session |
| **TaskList empty** | API returns no tasks | Expected (tasks completed), continue |
| **Git not available** | Command fails | Skip git source |
| **Session not found** | No session files | Skip session source |
| **All sources empty** | All collectors fail | Warn user, generate minimal report |

---

## 6. Example Usage

### Example 1: Standard Collection (File Artifacts Available)

```bash
/collect
```

**Output:**
```
🔄 Starting multi-source collection...

🔍 Determining active workload...
   Workload: hierarchical-orchestration-20260125

📊 Collecting from multiple sources...
📁 Checking file artifacts...
   Found 5 output files
📋 Checking workload progress...
   Loaded progress tracking
✅ Checking Task API...
   No tasks (already completed)

📦 Aggregating collected data...
   Confidence: high

📝 Generating collection report...
✅ Collection report generated: .agent/outputs/collection_report.md

=== Collection Complete ===

Report: .agent/outputs/collection_report.md
Confidence: high
Completed Work: 5 item(s)

- [x] `/synthesis` - High confidence collection, proceed to validation

Next: /synthesis
```

### Example 2: Fallback to Git History

```bash
/collect --from-git
```

**Output:**
```
🔄 Starting multi-source collection...

🔍 Determining active workload...
   Workload: global

📊 Collecting from multiple sources...
📁 Checking file artifacts...
   No files found
🔍 Checking git history...
   Found 8 recent commits

📦 Aggregating collected data...
   Confidence: low

📝 Generating collection report...

=== Collection Complete ===

Report: .agent/outputs/collection_report.md
Confidence: low
Completed Work: 1 item(s)

Warnings: 1

- [ ] **Low Confidence** - Limited data collected

Next: Review and verify outputs
```

---

## 7. Testing Checklist

### EFL Pattern Tests (V4.0)

**P1: Sub-Orchestrator (Agent Delegation)**
- [ ] Agent delegation to Phase 3-A (L2 Horizontal)
- [ ] Agent delegation to Phase 3-B (L3 Vertical)
- [ ] Agent prompt generation with internal loop instructions
- [ ] Fallback to V3.0 multi-source when delegation fails

**P3: General-Purpose Synthesis (L2/L3 Structure)**
- [ ] Phase 3-A extracts cross-area consistency data
- [ ] Phase 3-B performs code reality checks
- [ ] L2 (horizontal) and L3 (vertical) properly separated
- [ ] L1 summary concise (<500 tokens)
- [ ] L2 report contains full details

**P4: Selective Feedback**
- [ ] Severity-based feedback check (MEDIUM+ threshold)
- [ ] LOW severity → log only
- [ ] MEDIUM+ severity → trigger review/feedback

**P5: Phase 3.5 Review Gate**
- [ ] Review gate executes before final report
- [ ] Review criteria checked (requirement_alignment, etc.)
- [ ] Approved result allows synthesis
- [ ] Failed review blocks synthesis with clear errors

**P6: Agent Internal Feedback Loop**
- [ ] Agent prompts include internal loop instructions
- [ ] Internal loop metadata extracted from agent results
- [ ] Max 3 iterations enforced per agent
- [ ] Iteration count tracked in EFL metadata

### V3.0 Legacy Tests (Fallback)
- [ ] File artifacts collection (primary path)
- [ ] Workload progress collection
- [ ] Git history fallback
- [ ] Session history fallback
- [ ] Multi-workload support
- [ ] Empty TaskList handling (no failure)
- [ ] Report generation with mixed sources
- [ ] Confidence level calculation

### Integration Tests
- [ ] End-to-end: /collect → L1/L2 output → /synthesis input
- [ ] Workload-scoped output paths
- [ ] Review gate warnings display correctly
- [ ] Fallback mode when agent delegation unavailable

---

## Parameter Module Compatibility (V4.0.0)

| Module | Status | Notes |
|--------|--------|-------|
| `model-selection.md` | ✅ | `model: sonnet` (skill), `haiku` (agents) |
| `context-mode.md` | ✅ | `context: standard` |
| `tool-config.md` | ✅ | V4.0: Agent delegation + Task tool integration |
| `hook-config.md` | ✅ | V4.0: Setup hook (validation-feedback-loop.sh) |
| `permission-mode.md` | N/A | No elevated permissions |
| `task-params.md` | ✅ | File-based artifact tracking + L2/L3 structure |

---

## Version History

| Version | Change |
|---------|--------|
| 1.0.0 | Initial implementation (TaskList-based) |
| 2.1.0 | V2.1.19 Spec compliance |
| 3.0.0 | **Multi-source collection**, File-first strategy, Fallback support |
| 4.0.0 | **EFL Integration**: P1 (Sub-Orchestrator), P3 (L2/L3 structure), P5 (Review Gate), P6 (Internal Loop) |
| 4.1.0 | **Semantic Integrity**: SHA256 hash-based verification, upstream chain validation, artifact status classification |

### V4.0.0 Detailed Changes

**Enhanced Feedback Loop (EFL) Patterns:**
- **P1: Skill as Sub-Orchestrator** - Delegates to specialized agents instead of direct execution
- **P3: General-Purpose Synthesis** - Phase 3-A (L2 horizontal) + Phase 3-B (L3 vertical) structure
- **P5: Phase 3.5 Review Gate** - Holistic verification before synthesis
- **P6: Agent Internal Feedback Loop** - Agent self-validation with max 3 iterations
- **P4: Selective Feedback** - Severity-based threshold (MEDIUM+)

**New Sections:**
- `agent_delegation` frontmatter config
- `agent_internal_feedback_loop` config with validation criteria
- `review_gate` config with Phase 3.5 criteria
- `selective_feedback` config with severity thresholds
- Setup hook: `shared/validation-feedback-loop.sh`

**Modified Execution Flow:**
1. Phase 0: Workload detection (unchanged)
2. Phase 1: Agent delegation (NEW) - Replaces direct multi-source collection
3. Phase 2: Aggregate L2/L3 results (NEW) - Structured synthesis
4. Phase 3: Selective feedback check (NEW) - P4 integration
5. Phase 3.5: Review gate (NEW) - P5 verification
6. Phase 4: Generate L1/L2 report (ENHANCED) - Separated output layers

**Backward Compatibility:**
- V3.0 multi-source collection preserved as fallback
- All existing command-line arguments supported
- Legacy helper functions retained
- Graceful degradation when agent delegation unavailable

### V4.1.0 Detailed Changes

**Semantic Integrity Verification:**
- **Phase 3-B Replacement** - SHA256 hash-based verification replaces file-existence check
- **`verifySemanticIntegrity()`** - New function integrates with `semantic-integrity.sh` shared module
- **Artifact Status Classification** - VERIFIED, TAMPERED, MISSING, STALE states
- **Upstream Chain Validation** - Verifies manifest chain integrity across pipeline phases

**New Functions:**
- `verifySemanticIntegrity(workloadSlug, workers)` - Main integrity verification orchestrator
- `getStatusEmoji(status)` - Status-to-emoji mapping helper

**L2 Report Enhancements:**
- Phase 3-B section updated with Semantic Integrity format
- Artifact integrity table with Worker, Task, Manifest, Status, Hash Match columns
- Upstream chain verification results
- Integrity summary metrics (total, verified, tampered, missing, stale, integrity_rate)

**Integration Points:**
- Calls `semantic-integrity.sh` via Bash for hash operations
- Reads worker completion manifests from `.agent/outputs/{terminal}/`
- Uses `verify_artifact_integrity()` and `verify_upstream_chain()` functions

**Review Gate Enhancement (P5):**
- **New Criteria** - `integrity_verified`, `chain_valid`, `no_staleness` added to review_gate.criteria
- **Tamper Response** - Configurable actions: BLOCK_SYNTHESIS, WARN_AND_CONTINUE
  - `on_tampered: BLOCK_SYNTHESIS` - Block when hash mismatch detected
  - `on_stale: WARN_AND_CONTINUE` - Warn but allow when files modified after manifest
  - `on_missing: BLOCK_SYNTHESIS` - Block when output files not found
- **Integrity Threshold** - `integrity_threshold: 1.0` (100% verification required)
- **New Functions**:
  - `checkSemanticIntegrity(aggregated)` - Extract integrity status from aggregated results
  - `evaluateTamperResponse(integrityChecks)` - Determine appropriate action based on severity
- **L2 Report** - Review Gate section updated with integrity criteria table and tamper response details

---

**End of Skill Documentation**
