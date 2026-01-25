---
name: collect
description: |
  Aggregate worker results, verify completion, detect blockers.

  **V3.0 Changes:**
  - Multi-source collection (files + git + session)
  - Fallback strategy when TaskList empty
  - Session-based workload tracking
user-invocable: true
disable-model-invocation: false
context: standard
model: sonnet
version: "3.0.0"
argument-hint: "[--all | --phase <phase-id> | --from-session | --from-git]"
---

# /collect - Result Aggregation & Completion Verification

> **Version:** 3.0.0
> **Role:** Multi-source worker result aggregation
> **Architecture:** Hybrid (Files + Git + Session History)

---

## 1. Purpose

**Collection Agent** that:
1. **Primary**: Aggregates worker outputs from `.agent/outputs/` (file-based artifacts)
2. **Secondary**: Falls back to git history, session logs, workload tracking
3. **Verification**: Cross-references with workload `_progress.yaml`
4. **Report**: Generates collection report for `/synthesis`

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

## 3. Execution Protocol

### 3.1 Phase 0: Determine Active Workload

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

### 3.2 Phase 1: Multi-Source Collection

```javascript
async function collectFromMultipleSources(workloadSlug, options) {
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

### 3.4 Phase 2: Aggregate & Synthesize

```javascript
function aggregateCollectedData(sources) {
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

### 3.5 Phase 3: Generate Collection Report

```javascript
async function generateCollectionReport(aggregated, workloadSlug, options) {
  const timestamp = new Date().toISOString()

  const reportContent = `# Collection Report

> **Generated:** ${timestamp}
> **Workload:** ${workloadSlug || 'global'}
> **Confidence:** ${aggregated.confidence}
> **Sources:** ${aggregated.completedWork.map(w => w.type).join(', ')}

---

## Summary

${aggregated.warnings.length > 0 ? `
### ⚠️ Collection Warnings

${aggregated.warnings.map(w => `- ${w}`).join('\n')}

` : ''}

### Completed Work

${aggregated.completedWork.map(work => formatCompletedWork(work)).join('\n\n')}

---

## Deliverables

${aggregated.completedWork.flatMap(w => w.deliverables || []).length > 0
  ? aggregated.completedWork.flatMap(w => w.deliverables || []).map(d => `- ${d}`).join('\n')
  : '*No deliverables specified*'}

---

## Recommended Next Action

${getRecommendation(aggregated)}

---

## Collection Metadata

\`\`\`yaml
collectedAt: "${timestamp}"
workloadSlug: "${workloadSlug || 'global'}"
confidence: "${aggregated.confidence}"
sources: ${JSON.stringify(aggregated.completedWork.map(w => w.type))}
\`\`\`
`

  // Workload-scoped output path
  const reportDir = workloadSlug
    ? `.agent/prompts/${workloadSlug}`
    : `.agent/outputs`  // Fallback for global (deprecated)

  const reportPath = `${reportDir}/collection_report.md`

  // Ensure directory exists
  await Bash({ command: `mkdir -p ${reportDir}`, description: 'Create output directory' })
  await Write({ file_path: reportPath, content: reportContent })

  return reportPath
}
```

### 3.6 Helper Functions

```javascript
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

## 4. Main Execution Flow

```javascript
async function collect(args) {
  console.log("🔄 Starting multi-source collection...\n")

  // 1. Parse arguments
  const options = {
    mode: args.includes('--all') ? 'all' : 'default',
    phaseId: args.includes('--phase') ? args[args.indexOf('--phase') + 1] : null,
    fromSession: args.includes('--from-session'),
    fromGit: args.includes('--from-git'),
    fromFiles: args.includes('--from-files')
  }

  // 2. Determine active workload
  console.log("🔍 Determining active workload...")
  const workloadSlug = await determineActiveWorkload(args)
  console.log(`   Workload: ${workloadSlug || 'global'}\n`)

  // 3. Collect from multiple sources
  console.log("📊 Collecting from multiple sources...")
  const sources = await collectFromMultipleSources(workloadSlug, options)

  // 4. Aggregate data
  console.log("\n📦 Aggregating collected data...")
  const aggregated = aggregateCollectedData(sources)

  // 5. Generate report
  console.log("\n📝 Generating collection report...")
  const reportPath = await generateCollectionReport(aggregated, workloadSlug, options)

  // 6. Display summary
  console.log(`
=== Collection Complete ===

Report: ${reportPath}
Confidence: ${aggregated.confidence}
Completed Work: ${aggregated.completedWork.length} item(s)

${aggregated.warnings.length > 0 ? `Warnings: ${aggregated.warnings.length}` : ''}

${getRecommendation(aggregated)}

Next: ${aggregated.confidence === 'high' ? '/synthesis' : 'Review and verify outputs'}
`)

  return {
    status: 'success',
    reportPath: reportPath,
    confidence: aggregated.confidence,
    completedWork: aggregated.completedWork.length
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

- [ ] File artifacts collection (primary path)
- [ ] Workload progress collection
- [ ] Git history fallback
- [ ] Session history fallback
- [ ] Multi-workload support
- [ ] Empty TaskList handling (no failure)
- [ ] Report generation with mixed sources
- [ ] Confidence level calculation
- [ ] Recommendation logic

---

## Parameter Module Compatibility (V3.0.0)

| Module | Status | Notes |
|--------|--------|-------|
| `model-selection.md` | ✅ | `model: sonnet` |
| `context-mode.md` | ✅ | `context: standard` |
| `tool-config.md` | ✅ | Multi-source collection pattern |
| `hook-config.md` | N/A | No hooks |
| `permission-mode.md` | N/A | No elevated permissions |
| `task-params.md` | ✅ | File-based artifact tracking |

---

## Version History

| Version | Change |
|---------|--------|
| 1.0.0 | Initial implementation (TaskList-based) |
| 2.1.0 | V2.1.19 Spec compliance |
| 3.0.0 | **Multi-source collection**, File-first strategy, Fallback support |

---

**End of Skill Documentation**
