# Dashboard Build Script — Data Parsing Analysis

**Analysis Date:** 2026-02-15
**Analyst:** analyst
**Purpose:** Document file structure and bash parsing strategies for dashboard build script

---

## Executive Summary

This analysis documents the structure of all `.claude/` infrastructure files and proposes bash parsing strategies for extracting structured data into JSON format for the dashboard build script.

**Key Findings:**
- **6 agent files** with consistent YAML frontmatter structure
- **35 skill files** with standardized L1 frontmatter and L2 body sections
- **5 hook scripts** with predictable structure and JSON output
- **1 settings.json** with nested JSON configuration
- **CLAUDE.md** with markdown table-based protocol
- **MEMORY.md** with structured session history and state tables

**Parsing Complexity:**
- **Low:** settings.json (already JSON), hook scripts (simple bash structure)
- **Medium:** agent frontmatter (YAML), CLAUDE.md (markdown tables)
- **High:** skill frontmatter (multi-line YAML strings with embedded structure), MEMORY.md (mixed format tables and narrative)

---

## 1. Agent Files (.claude/agents/*.md)

### 1.1 File Inventory

```
.claude/agents/analyst.md
.claude/agents/researcher.md
.claude/agents/implementer.md
.claude/agents/infra-implementer.md
.claude/agents/delivery-agent.md
.claude/agents/pt-manager.md
```

Total: **6 files**

### 1.2 YAML Frontmatter Structure

All agent files follow this structure:

```yaml
---
name: string
description: |
  Multi-line string with structured format:
  - Line 1: [Profile-X·Tag] Summary sentence.
  - Line 2: (blank)
  - Line 3: WHEN: trigger condition
  - Line 4: TOOLS: comma-separated tool list
  - Line 5: CANNOT: comma-separated forbidden tools
  - Line 6: PROFILE: X (profile name). Description.
tools:
  - tool1
  - tool2
memory: project|none
maxTurns: integer
color: string
model: haiku (optional, only delivery-agent and pt-manager)
---
```

### 1.3 Field Types and Values

| Field | Type | Example Values | Notes |
|-------|------|----------------|-------|
| `name` | string | `analyst`, `researcher` | Matches filename |
| `description` | multi-line string | See structure above | Contains profile tag, WHEN/TOOLS/CANNOT/PROFILE blocks |
| `tools` | array of strings | `["Read", "Glob", "Grep"]` | Tool names from CC tool set |
| `memory` | enum | `project`, `none` | Memory configuration |
| `maxTurns` | integer | `20`, `25`, `30`, `35`, `50` | Turn limit for agent |
| `color` | string | `magenta`, `yellow`, `green`, `red`, `cyan`, `blue` | Tmux pane color |
| `model` | string (optional) | `haiku` | Only for delivery-agent, pt-manager |

### 1.4 Description String Format

Pattern: `[Profile-{LETTER}·{TAG}] {SUMMARY}.\n\n{WHEN}.\n{TOOLS}.\n{CANNOT}.\n{PROFILE}.`

**Profile Tags Observed:**
- `Profile-B·ReadAnalyzeWrite` (analyst)
- `Profile-C·ReadAnalyzeWriteWeb` (researcher)
- `Profile-D·CodeImpl` (implementer)
- `Profile-E·InfraImpl` (infra-implementer)
- `Profile-F·ForkDelivery` (delivery-agent)
- `Profile-G·ForkPT` (pt-manager)

### 1.5 Bash Parsing Strategy

**Challenge:** Extract fields from YAML frontmatter with multi-line strings.

**Approach:** Use `awk` to parse YAML frontmatter between `---` delimiters, `yq` or manual parsing for specific fields.

#### Strategy A: yq (YAML parser)

```bash
#!/usr/bin/env bash
# Extract agent data to JSON using yq

AGENTS_DIR=".claude/agents"
OUTPUT_FILE="agents.json"

echo "[" > "$OUTPUT_FILE"
first=true

for agent_file in "$AGENTS_DIR"/*.md; do
    [ -f "$agent_file" ] || continue

    # yq reads YAML frontmatter and converts to JSON
    # Extract frontmatter between --- delimiters
    agent_json=$(awk '/^---$/{p++; next} p==1' "$agent_file" | yq eval -o=json -)

    # Add comma separator except for first entry
    if [ "$first" = true ]; then
        first=false
    else
        echo "," >> "$OUTPUT_FILE"
    fi

    # Add source filename as metadata
    echo "$agent_json" | jq --arg file "$(basename "$agent_file")" '. + {source_file: $file}' >> "$OUTPUT_FILE"
done

echo "]" >> "$OUTPUT_FILE"
```

**Dependencies:** `yq`, `jq`, `awk`

#### Strategy B: Pure bash/awk (no yq)

```bash
#!/usr/bin/env bash
# Extract agent data to JSON using pure bash/awk

parse_agent() {
    local file="$1"
    local name color memory maxTurns model tools_json description

    # Extract frontmatter
    local frontmatter=$(awk '/^---$/{p++; next} p==1' "$file")

    # Parse single-line fields
    name=$(echo "$frontmatter" | awk -F': ' '/^name:/ {print $2}')
    color=$(echo "$frontmatter" | awk -F': ' '/^color:/ {print $2}')
    memory=$(echo "$frontmatter" | awk -F': ' '/^memory:/ {print $2}')
    maxTurns=$(echo "$frontmatter" | awk -F': ' '/^maxTurns:/ {print $2}')
    model=$(echo "$frontmatter" | awk -F': ' '/^model:/ {print $2}')

    # Parse description (multi-line after "description: |")
    description=$(echo "$frontmatter" | awk '/^description:/{flag=1; next} /^[a-z]+:/{flag=0} flag' | \
        sed 's/^  //' | \
        jq -Rs . | \
        tr -d '\n')

    # Parse tools array
    tools_json=$(echo "$frontmatter" | awk '/^tools:/{flag=1; next} /^[a-z]+:/{flag=0} flag' | \
        sed 's/^  - //' | \
        jq -R . | \
        jq -s .)

    # Build JSON object
    cat <<EOF
{
  "name": "$name",
  "description": $description,
  "tools": $tools_json,
  "memory": "$memory",
  "maxTurns": $maxTurns,
  "color": "$color"$([ -n "$model" ] && echo ",
  \"model\": \"$model\"" || echo ""),
  "source_file": "$(basename "$file")"
}
EOF
}

# Main loop
echo "["
first=true
for agent_file in .claude/agents/*.md; do
    [ -f "$agent_file" ] || continue

    if [ "$first" = true ]; then
        first=false
    else
        echo ","
    fi

    parse_agent "$agent_file"
done
echo "]"
```

**Dependencies:** `awk`, `sed`, `jq`

**Recommendation:** Use Strategy A (yq) for robustness with complex YAML. Fallback to Strategy B for environments without yq.

---

## 2. Skill Files (.claude/skills/*/SKILL.md)

### 2.1 File Inventory

**Total:** 35 skill files across 8 domains + 4 homeostasis + 3 cross-cutting

**Sample paths:**
```
.claude/skills/pre-design-brainstorm/SKILL.md
.claude/skills/design-architecture/SKILL.md
.claude/skills/research-codebase/SKILL.md
.claude/skills/execution-code/SKILL.md
.claude/skills/verify-content/SKILL.md
.claude/skills/manage-infra/SKILL.md
.claude/skills/delivery-pipeline/SKILL.md
```

### 2.2 YAML Frontmatter Structure (L1)

```yaml
---
name: kebab-case-skill-name
description: |
  Multi-line string with orchestration map:
  - Line 1: [P{N}·Domain·Skill] Summary sentence.
  - Line 2: (blank)
  - Line 3: WHEN: trigger condition.
  - Line 4: DOMAIN: domain classification and position.
  - Line 5: INPUT_FROM: upstream dependencies.
  - Line 6: OUTPUT_TO: downstream consumers.
  - Line 7: (blank)
  - Line 8: METHODOLOGY: numbered execution steps.
  - Line 9+: Additional metadata (TIER_BEHAVIOR, OUTPUT_FORMAT, etc.)
user-invocable: true|false
disable-model-invocation: true|false
argument-hint: "[arg]" (optional, only if user-invocable: true)
---
```

### 2.3 Field Types and Values

| Field | Type | Example Values | Notes |
|-------|------|----------------|-------|
| `name` | string | `pre-design-brainstorm`, `execution-code` | Matches directory name |
| `description` | multi-line string | See structure above | Contains phase tag, orchestration map |
| `user-invocable` | boolean | `true`, `false` | Can user invoke directly? |
| `disable-model-invocation` | boolean | `true`, `false` | Lead-only execution flag |
| `argument-hint` | string (optional) | `"[topic]"`, `"[commit-message]"` | CLI argument hint for user-invocable skills |

### 2.4 Description String Format

**Phase Tag Pattern:** `[P{N}·{DOMAIN}·{SKILL}]` where N = 0-8

**Orchestration Map Keys:**
- `WHEN:` — trigger condition (when to invoke this skill)
- `DOMAIN:` — domain classification and skill position (1 of N, sequential/parallel)
- `INPUT_FROM:` — upstream skill dependencies
- `OUTPUT_TO:` — downstream skill consumers
- `METHODOLOGY:` — numbered execution steps (brief)
- `TIER_BEHAVIOR:` (optional) — TRIVIAL/STANDARD/COMPLEX behavior
- `OUTPUT_FORMAT:` — L1 YAML and L2 markdown templates
- `CONSTRAINT:` (optional) — execution constraints

**Example Tag Values:**
- `[P0·PreDesign·Brainstorm]`
- `[P2·Design·Architecture]`
- `[P7·Execution·Code]`
- `[P8·Verify·Content]`
- `[Homeostasis·Manager·Infra]`
- `[X-Cut·TaskMgmt·TaskAPI]`

### 2.5 L2 Body Structure

All skills have standardized markdown body sections after frontmatter:

```markdown
# {Skill Title}

## Execution Model
- **TRIVIAL**: ...
- **STANDARD**: ...
- **COMPLEX**: ...

## Methodology

### 1. {Step Title}
...

### 2. {Step Title}
...

### N. {Step Title}
...

## Quality Gate
- Criterion 1
- Criterion 2
...

## Output

### L1
```yaml
domain: {domain}
skill: {skill-name}
# ... fields
```

### L2
- Description of L2 output
...
```

**Additional Optional Sections:**
- `## Decision Points` (in some execution skills)
- `## Failure Handling`
- `## Anti-Patterns`
- `## Transitions` (Receives From / Sends To tables)
- `## Degradation Handling`
- `## Fork Execution` (for delivery-pipeline)

### 2.6 Bash Parsing Strategy

**Challenge:** Extract structured frontmatter with complex multi-line descriptions, plus parse L2 body sections.

#### Strategy A: Frontmatter Only (yq + jq)

```bash
#!/usr/bin/env bash
# Extract skill frontmatter to JSON

SKILLS_DIR=".claude/skills"
OUTPUT_FILE="skills.json"

echo "[" > "$OUTPUT_FILE"
first=true

for skill_dir in "$SKILLS_DIR"/*/; do
    skill_file="${skill_dir}SKILL.md"
    [ -f "$skill_file" ] || continue

    # Extract frontmatter
    skill_json=$(awk '/^---$/{p++; next} p==1' "$skill_file" | yq eval -o=json -)

    # Parse phase tag from description
    phase_tag=$(echo "$skill_json" | jq -r '.description' | head -1 | grep -oP '\[P?\d+·[^]]+\]|\[[^]]+·[^]]+·[^]]+\]')

    # Add comma separator
    if [ "$first" = true ]; then
        first=false
    else
        echo "," >> "$OUTPUT_FILE"
    fi

    # Add metadata
    echo "$skill_json" | jq --arg dir "$(basename "$(dirname "$skill_file")")" \
                             --arg tag "$phase_tag" \
                             '. + {skill_dir: $dir, phase_tag: $tag}' >> "$OUTPUT_FILE"
done

echo "]" >> "$OUTPUT_FILE"
```

#### Strategy B: Frontmatter + Body Section Extraction

```bash
#!/usr/bin/env bash
# Extract skill frontmatter + body sections

parse_skill() {
    local file="$1"
    local skill_dir=$(basename "$(dirname "$file")")

    # Extract frontmatter
    local frontmatter=$(awk '/^---$/{p++; next} p==1' "$file")
    local frontmatter_json=$(echo "$frontmatter" | yq eval -o=json -)

    # Extract body (everything after second ---)
    local body=$(awk '/^---$/{p++; next} p==2' "$file")

    # Parse phase tag from description
    local phase_tag=$(echo "$frontmatter_json" | jq -r '.description' | head -1 | grep -oP '\[P?\d+·[^]]+\]|\[[^]]+·[^]]+·[^]]+\]')

    # Extract sections from body
    local has_exec_model=$(echo "$body" | grep -q '^## Execution Model' && echo "true" || echo "false")
    local has_methodology=$(echo "$body" | grep -q '^## Methodology' && echo "true" || echo "false")
    local has_quality_gate=$(echo "$body" | grep -q '^## Quality Gate' && echo "true" || echo "false")
    local has_output=$(echo "$body" | grep -q '^## Output' && echo "true" || echo "false")

    # Count methodology steps
    local method_step_count=$(echo "$body" | grep -c '^### [0-9]\+\.')

    # Build JSON
    echo "$frontmatter_json" | jq --arg dir "$skill_dir" \
                                   --arg tag "$phase_tag" \
                                   --argjson exec "$has_exec_model" \
                                   --argjson meth "$has_methodology" \
                                   --argjson gate "$has_quality_gate" \
                                   --argjson out "$has_output" \
                                   --argjson steps "$method_step_count" \
                                   '. + {
                                       skill_dir: $dir,
                                       phase_tag: $tag,
                                       body_sections: {
                                           execution_model: $exec,
                                           methodology: $meth,
                                           quality_gate: $gate,
                                           output: $out,
                                           methodology_steps: $steps
                                       }
                                   }'
}

# Main
echo "["
first=true
for skill_file in .claude/skills/*/SKILL.md; do
    [ -f "$skill_file" ] || continue

    if [ "$first" = true ]; then
        first=false
    else
        echo ","
    fi

    parse_skill "$skill_file"
done
echo "]"
```

**Dependencies:** `yq`, `jq`, `awk`, `grep`

### 2.7 Domain Extraction from Phase Tags

Phase tags encode domain information:

```bash
# Extract domain from phase tag
extract_domain() {
    local tag="$1"
    # [P7·Execution·Code] -> "execution"
    # [Homeostasis·Manager·Infra] -> "homeostasis"
    # [X-Cut·TaskMgmt·TaskAPI] -> "cross-cutting"

    echo "$tag" | sed -E 's/\[P?[0-9]+·([^·]+)·.*/\1/' | tr '[:upper:]' '[:lower:]'
}
```

**Domain List (from tags):**
- `predesign` (P0)
- `design` (P1)
- `research` (P2)
- `plan` (P3)
- `plan-verify` (P4)
- `orchestration` (P5)
- `execution` (P6)
- `verify` (P7)
- `homeostasis` (X-cut)
- `cross-cutting` (X-cut, P8)

---

## 3. Hook Scripts (.claude/hooks/*.sh)

### 3.1 File Inventory

```
.claude/hooks/on-subagent-start.sh
.claude/hooks/on-session-compact.sh
.claude/hooks/on-implementer-done.sh
.claude/hooks/on-file-change.sh
.claude/hooks/on-pre-compact.sh
```

Total: **5 files**

### 3.2 Hook Structure

All hooks follow this pattern:

```bash
#!/usr/bin/env bash
# Hook: {EventName} — {Purpose}
# {Optional metadata comments}

set -euo pipefail

INPUT=$(cat)

# ... processing logic ...

# JSON output (if applicable)
echo '{"hookSpecificOutput":{"hookEventName":"...","additionalContext":"..."}}'
exit 0
```

### 3.3 Hook Metadata

| Hook File | Event | Matcher | Timeout | Async | Purpose |
|-----------|-------|---------|---------|-------|---------|
| `on-subagent-start.sh` | SubagentStart | (empty) | 10s | false | PT context injection |
| `on-session-compact.sh` | SessionStart | `compact` | 15s | false | Auto-compact recovery |
| `on-implementer-done.sh` | SubagentStop | `implementer\|infra-implementer` | 30s | false | SRC Stage 2 impact injection |
| `on-file-change.sh` | PostToolUse | `Edit\|Write` | 5s | **true** | SRC Stage 1 file logger |
| `on-pre-compact.sh` | PreCompact | (empty) | 30s | false | State preservation |

### 3.4 Bash Parsing Strategy

**Challenge:** Extract hook metadata from comments and identify trigger events.

```bash
#!/usr/bin/env bash
# Extract hook metadata to JSON

HOOKS_DIR=".claude/hooks"
OUTPUT_FILE="hooks.json"

parse_hook() {
    local file="$1"
    local filename=$(basename "$file")

    # Extract header comment purpose line
    local purpose=$(grep -m1 '^# Hook:' "$file" | sed 's/^# Hook: //')

    # Extract event and description from purpose
    local event=$(echo "$purpose" | awk -F' — ' '{print $1}')
    local description=$(echo "$purpose" | awk -F' — ' '{print $2}')

    # Check for jq dependency
    local needs_jq=$(grep -q 'command -v jq' "$file" && echo "true" || echo "false")

    # Check for session_id extraction (indicates input parsing)
    local parses_input=$(grep -q 'SESSION_ID' "$file" && echo "true" || echo "false")

    # Check for additionalContext output
    local outputs_context=$(grep -q 'additionalContext' "$file" && echo "true" || echo "false")

    # Build JSON
    jq -n --arg file "$filename" \
          --arg event "$event" \
          --arg desc "$description" \
          --argjson jq "$needs_jq" \
          --argjson input "$parses_input" \
          --argjson context "$outputs_context" \
          '{
              hook_file: $file,
              event: $event,
              description: $desc,
              needs_jq: $jq,
              parses_input: $input,
              outputs_context: $context
          }'
}

# Main
echo "["
first=true
for hook_file in "$HOOKS_DIR"/*.sh; do
    [ -f "$hook_file" ] || continue

    if [ "$first" = true ]; then
        first=false
    else
        echo ","
    fi

    parse_hook "$hook_file"
done
echo "]"
```

### 3.5 Hook Configuration from settings.json

Hook configuration lives in `settings.json` under `hooks` key. See section 4.3 for parsing strategy.

---

## 4. Settings (.claude/settings.json)

### 4.1 File Structure

**Path:** `.claude/settings.json`

**Structure:**
```json
{
  "env": {
    "CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS": "1",
    "CLAUDE_CODE_MAX_OUTPUT_TOKENS": "128000",
    ...
  },
  "permissions": {
    "allow": [ ... ],
    "deny": [ ... ],
    "defaultMode": "delegate"
  },
  "model": "claude-opus-4-6",
  "hooks": {
    "SubagentStart": [ ... ],
    "PreCompact": [ ... ],
    "SessionStart": [ ... ],
    "PostToolUse": [ ... ],
    "SubagentStop": [ ... ]
  },
  "enabledPlugins": { ... },
  "promptSuggestionEnabled": true,
  "skipDangerousModePermissionPrompt": true,
  "teammateMode": "tmux",
  "alwaysThinkingEnabled": true
}
```

### 4.2 Key Fields

| Field | Type | Purpose |
|-------|------|---------|
| `env` | object | Environment variables |
| `permissions` | object | Tool permission rules |
| `model` | string | Default model ID |
| `hooks` | object | Hook event configurations |
| `enabledPlugins` | object | Plugin enablement flags |
| `teammateMode` | string | Agent Teams mode (`tmux`) |
| `alwaysThinkingEnabled` | boolean | Thinking feature flag |

### 4.3 Bash Parsing Strategy

**Challenge:** None — already JSON.

```bash
#!/usr/bin/env bash
# Parse settings.json

SETTINGS_FILE=".claude/settings.json"

# Validate JSON
if ! jq empty "$SETTINGS_FILE" 2>/dev/null; then
    echo "ERROR: Invalid JSON in $SETTINGS_FILE" >&2
    exit 1
fi

# Extract specific fields
cat "$SETTINGS_FILE" | jq '{
    model: .model,
    teammate_mode: .teammateMode,
    always_thinking: .alwaysThinkingEnabled,
    env_vars: .env | keys,
    hook_events: .hooks | keys,
    enabled_plugins: .enabledPlugins | keys,
    permission_default: .permissions.defaultMode,
    allow_count: (.permissions.allow | length),
    deny_count: (.permissions.deny | length)
}'
```

### 4.4 Hook Configuration Extraction

```bash
# Extract hook configurations
jq '.hooks | to_entries | map({
    event: .key,
    matchers: [.value[] | .matcher],
    commands: [.value[] | .hooks[] | .command],
    timeouts: [.value[] | .hooks[] | .timeout],
    async_flags: [.value[] | .hooks[] | .async]
})' "$SETTINGS_FILE"
```

**Output:**
```json
[
  {
    "event": "SubagentStart",
    "matchers": [""],
    "commands": ["/home/palantir/.claude/hooks/on-subagent-start.sh"],
    "timeouts": [10],
    "async_flags": [null]
  },
  ...
]
```

---

## 5. CLAUDE.md

### 5.1 File Structure

**Path:** `.claude/CLAUDE.md`

**Structure:**
```markdown
# Agent Teams — Team Constitution v{VERSION}

> Tagline with version, key stats

> **INVIOLABLE — {Core Principle}**

## 0. Language Policy
...

## 1. Team Identity
...

## 2. Pipeline Tiers
| Tier | Criteria | Phases |
...

## 2.1 Execution Mode by Phase
...

## 3. Lead
...

## 4. PERMANENT Task (PT)
...
```

**Total Lines:** 54
**Sections:** 6 (§0-§4, plus §2.1)

### 5.2 Key Sections for Dashboard

#### Section 1: Team Identity

Contains:
- Agent count (`6 custom`)
- Skill count (`35 across 8 pipeline domains + 4 homeostasis + 3 cross-cutting`)
- Agent names (in parentheses)

#### Section 2: Pipeline Tiers

Markdown table:
```
| Tier | Criteria | Phases |
|------|----------|--------|
| TRIVIAL | ≤2 files, single module | P0→P6→P8 |
| STANDARD | 3 files, 1-2 modules | P0→P1→P2→P3→P6→P7→P8 |
| COMPLEX | ≥4 files, 2+ modules | P0→P8 (all phases) |
```

### 5.3 Bash Parsing Strategy

```bash
#!/usr/bin/env bash
# Parse CLAUDE.md

CLAUDE_MD=".claude/CLAUDE.md"

# Extract version from header
version=$(head -1 "$CLAUDE_MD" | grep -oP 'v[\d.]+')

# Extract tagline stats
tagline=$(head -5 "$CLAUDE_MD" | tail -1)
agent_count=$(echo "$tagline" | grep -oP '\d+ agents')
skill_count=$(echo "$tagline" | grep -oP '\d+ skills')

# Extract agent names from §1
agent_names=$(grep -A5 '## 1. Team Identity' "$CLAUDE_MD" | \
              grep 'Agents:' | \
              grep -oP '\([^)]+\)' | \
              tr -d '()' | \
              tr ', ' '\n')

# Extract pipeline tier table (lines between "| Tier |" header and next ##)
tier_table=$(awk '/\| Tier \|/,/^##/' "$CLAUDE_MD" | grep '|' | tail -n +2)

# Parse tier table to JSON
echo "$tier_table" | awk -F'|' '{
    gsub(/^[ \t]+|[ \t]+$/, "", $2);
    gsub(/^[ \t]+|[ \t]+$/, "", $3);
    gsub(/^[ \t]+|[ \t]+$/, "", $4);
    if (NF >= 4 && $2 != "------") {
        print "{\"tier\":\""$2"\",\"criteria\":\""$3"\",\"phases\":\""$4"\"}"
    }
}' | jq -s .
```

**Output:**
```json
[
  {"tier":"TRIVIAL","criteria":"≤2 files, single module","phases":"P0→P6→P8"},
  {"tier":"STANDARD","criteria":"3 files, 1-2 modules","phases":"P0→P1→P2→P3→P6→P7→P8"},
  {"tier":"COMPLEX","criteria":"≥4 files, 2+ modules","phases":"P0→P8 (all phases)"}
]
```

---

## 6. MEMORY.md

### 6.1 File Structure

**Path:** `.claude/projects/-home-palantir/memory/MEMORY.md`

**Structure:**
```markdown
# Claude Code Memory

## Permanent Rules
### {Rule Title} ({Date})
...

## Current INFRA State (v{VERSION}, {DATE})

| Component | Version | Size | Key Feature |
...

### Architecture (v{VERSION} Native Optimization)
...

### Skills ({COUNT} total: {BREAKDOWN})

| Domain | Skills | Phase |
...

### Pipeline Tiers

| Tier | Criteria | Phases |
...

### Known Bugs

| ID | Severity | Summary | Workaround |
...

## Next Topics
...

## Session History

### {Session Title} ({Date}, branch: {BRANCH})
...

## Topic Files Index
...
```

### 6.2 Key Sections for Dashboard

#### Current INFRA State Table

```
| Component | Version | Size | Key Feature |
|-----------|---------|------|-------------|
| CLAUDE.md | v10.8 | 54L | Protocol-only + ... |
| Agents | v10.8 | 6 files | 2 haiku+memory:none ... |
| Skills | v10.8 | 35 dirs | DPS 19 skills + ... |
| Settings | v10.8 | ~110L | teammateMode:tmux ... |
| Hooks | 5 total | ~285L | SRC log preserved ... |
```

#### Skills Domain Table

```
| Domain | Skills | Phase |
|--------|--------|-------|
| pre-design | brainstorm, validate, feasibility | P0 |
| design | architecture, interface, risk | P1 |
...
```

#### Known Bugs Table

```
| ID | Severity | Summary | Workaround |
|----|----------|---------|------------|
| BUG-001 | CRITICAL | ... | ... |
```

### 6.3 Bash Parsing Strategy

```bash
#!/usr/bin/env bash
# Parse MEMORY.md

MEMORY_MD=".claude/projects/-home-palantir/memory/MEMORY.md"

# Extract INFRA State version and date
infra_version=$(grep -m1 '## Current INFRA State' "$MEMORY_MD" | grep -oP 'v[\d.]+')
infra_date=$(grep -m1 '## Current INFRA State' "$MEMORY_MD" | grep -oP '\d{4}-\d{2}-\d{2}')

# Extract INFRA State table
infra_table=$(awk '/## Current INFRA State/,/^###/' "$MEMORY_MD" | \
              grep '|' | \
              awk '/Component.*Version.*Size/,/^$/' | \
              tail -n +2)

# Parse to JSON
echo "$infra_table" | awk -F'|' '{
    gsub(/^[ \t]+|[ \t]+$/, "", $2);
    gsub(/^[ \t]+|[ \t]+$/, "", $3);
    gsub(/^[ \t]+|[ \t]+$/, "", $4);
    gsub(/^[ \t]+|[ \t]+$/, "", $5);
    if (NF >= 5 && $2 != "------") {
        print "{\"component\":\""$2"\",\"version\":\""$3"\",\"size\":\""$4"\",\"key_feature\":\""$5"\"}"
    }
}' | jq -s .

# Extract skills domain table (similar approach)
skills_table=$(awk '/### Skills \(/,/^###/' "$MEMORY_MD" | \
               grep '|' | \
               awk '/Domain.*Skills.*Phase/,/^$/' | \
               tail -n +2)

# Parse to JSON
echo "$skills_table" | awk -F'|' '{
    gsub(/^[ \t]+|[ \t]+$/, "", $2);
    gsub(/^[ \t]+|[ \t]+$/, "", $3);
    gsub(/^[ \t]+|[ \t]+$/, "", $4);
    if (NF >= 4 && $2 != "------") {
        print "{\"domain\":\""$2"\",\"skills\":\""$3"\",\"phase\":\""$4"\"}"
    }
}' | jq -s .

# Extract session history entries (each ### under Session History)
session_count=$(awk '/## Session History/,/^## Topic Files Index/' "$MEMORY_MD" | \
                grep -c '^###')

# Extract latest session title and date
latest_session=$(awk '/## Session History/,/^## Topic Files Index/' "$MEMORY_MD" | \
                 grep -m1 '^###' | \
                 sed 's/^### //')
```

### 6.4 Session History Entry Format

Pattern: `### {TITLE} ({DATE}, branch: {BRANCH})`

**Examples:**
- `### v10.8 CLAUDE.md Review + Phase Renumbering (2026-02-15, branch: test)`
- `### RSI L4 — Context Engineering + Prompt Engineering (2026-02-15, branch: test)`

**Extraction:**
```bash
parse_session_entry() {
    local line="$1"
    # Remove leading "### "
    line="${line#\#\#\# }"

    # Extract title (everything before first parenthesis)
    local title=$(echo "$line" | sed 's/ (.*//')

    # Extract date (YYYY-MM-DD)
    local date=$(echo "$line" | grep -oP '\d{4}-\d{2}-\d{2}')

    # Extract branch
    local branch=$(echo "$line" | grep -oP 'branch: \K[^)]+')

    jq -n --arg t "$title" --arg d "$date" --arg b "$branch" \
          '{title: $t, date: $d, branch: $b}'
}
```

---

## 7. Unified Dashboard Data Schema

### 7.1 Proposed JSON Output Structure

```json
{
  "metadata": {
    "extracted_at": "2026-02-15T10:30:00Z",
    "infra_version": "v10.8",
    "claude_md_version": "v10.8",
    "memory_md_version": "v10.8"
  },
  "agents": [
    {
      "name": "analyst",
      "profile": "B",
      "description": "...",
      "tools": ["Read", "Glob", "Grep", "Write", "sequential-thinking"],
      "memory": "project",
      "maxTurns": 25,
      "color": "magenta",
      "source_file": "analyst.md"
    }
  ],
  "skills": [
    {
      "name": "pre-design-brainstorm",
      "phase_tag": "[P0·PreDesign·Brainstorm]",
      "domain": "pre-design",
      "phase": "P0",
      "description": "...",
      "user_invocable": true,
      "disable_model_invocation": true,
      "argument_hint": "[topic]",
      "body_sections": {
        "execution_model": true,
        "methodology": true,
        "methodology_steps": 5,
        "quality_gate": true,
        "output": true
      },
      "skill_dir": "pre-design-brainstorm"
    }
  ],
  "hooks": [
    {
      "hook_file": "on-subagent-start.sh",
      "event": "SubagentStart",
      "description": "Logging + PT context injection",
      "needs_jq": true,
      "parses_input": true,
      "outputs_context": true,
      "config": {
        "matcher": "",
        "timeout": 10,
        "async": false
      }
    }
  ],
  "settings": {
    "model": "claude-opus-4-6",
    "teammate_mode": "tmux",
    "always_thinking": true,
    "env_vars": ["CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS", ...],
    "hook_events": ["SubagentStart", "PreCompact", ...],
    "enabled_plugins": ["superpowers-developing-for-claude-code@superpowers-marketplace", ...]
  },
  "claude_md": {
    "version": "v10.8",
    "sections": 6,
    "agent_count": 6,
    "skill_count": 35,
    "agent_names": ["analyst", "researcher", ...],
    "pipeline_tiers": [
      {"tier": "TRIVIAL", "criteria": "≤2 files, single module", "phases": "P0→P6→P8"}
    ]
  },
  "memory_md": {
    "infra_version": "v10.8",
    "infra_date": "2026-02-15",
    "components": [
      {"component": "CLAUDE.md", "version": "v10.8", "size": "54L", "key_feature": "..."}
    ],
    "skills_domains": [
      {"domain": "pre-design", "skills": "brainstorm, validate, feasibility", "phase": "P0"}
    ],
    "known_bugs": [
      {"id": "BUG-001", "severity": "CRITICAL", "summary": "...", "workaround": "..."}
    ],
    "session_count": 10,
    "latest_session": {
      "title": "v10.8 CLAUDE.md Review + Phase Renumbering",
      "date": "2026-02-15",
      "branch": "test"
    }
  }
}
```

### 7.2 Master Build Script

```bash
#!/usr/bin/env bash
# dashboard-build.sh — Master data extraction script

set -euo pipefail

CLAUDE_DIR=".claude"
OUTPUT_FILE="dashboard-data.json"

# Check dependencies
for cmd in jq yq awk sed grep; do
    if ! command -v "$cmd" &>/dev/null; then
        echo "ERROR: Required command '$cmd' not found" >&2
        exit 1
    fi
done

# Extract metadata
TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
INFRA_VERSION=$(grep -m1 '## Current INFRA State' "$CLAUDE_DIR/../projects/-home-palantir/memory/MEMORY.md" | grep -oP 'v[\d.]+')

# Build JSON structure
jq -n \
  --arg ts "$TIMESTAMP" \
  --arg ver "$INFRA_VERSION" \
  '{
    metadata: {
      extracted_at: $ts,
      infra_version: $ver
    },
    agents: [],
    skills: [],
    hooks: [],
    settings: {},
    claude_md: {},
    memory_md: {}
  }' > "$OUTPUT_FILE.tmp"

# Extract agents
AGENTS_JSON=$(./extract-agents.sh)
jq --argjson agents "$AGENTS_JSON" '.agents = $agents' "$OUTPUT_FILE.tmp" > "$OUTPUT_FILE.tmp2"
mv "$OUTPUT_FILE.tmp2" "$OUTPUT_FILE.tmp"

# Extract skills
SKILLS_JSON=$(./extract-skills.sh)
jq --argjson skills "$SKILLS_JSON" '.skills = $skills' "$OUTPUT_FILE.tmp" > "$OUTPUT_FILE.tmp2"
mv "$OUTPUT_FILE.tmp2" "$OUTPUT_FILE.tmp"

# Extract hooks
HOOKS_JSON=$(./extract-hooks.sh)
jq --argjson hooks "$HOOKS_JSON" '.hooks = $hooks' "$OUTPUT_FILE.tmp" > "$OUTPUT_FILE.tmp2"
mv "$OUTPUT_FILE.tmp2" "$OUTPUT_FILE.tmp"

# Extract settings
SETTINGS_JSON=$(jq '{
  model: .model,
  teammate_mode: .teammateMode,
  always_thinking: .alwaysThinkingEnabled,
  env_vars: (.env | keys),
  hook_events: (.hooks | keys),
  enabled_plugins: (.enabledPlugins | keys)
}' "$CLAUDE_DIR/settings.json")
jq --argjson settings "$SETTINGS_JSON" '.settings = $settings' "$OUTPUT_FILE.tmp" > "$OUTPUT_FILE.tmp2"
mv "$OUTPUT_FILE.tmp2" "$OUTPUT_FILE.tmp"

# Extract CLAUDE.md
CLAUDE_JSON=$(./extract-claude-md.sh)
jq --argjson claude "$CLAUDE_JSON" '.claude_md = $claude' "$OUTPUT_FILE.tmp" > "$OUTPUT_FILE.tmp2"
mv "$OUTPUT_FILE.tmp2" "$OUTPUT_FILE.tmp"

# Extract MEMORY.md
MEMORY_JSON=$(./extract-memory-md.sh)
jq --argjson memory "$MEMORY_JSON" '.memory_md = $memory' "$OUTPUT_FILE.tmp" > "$OUTPUT_FILE"

# Cleanup
rm -f "$OUTPUT_FILE.tmp" "$OUTPUT_FILE.tmp2"

echo "Dashboard data extracted to $OUTPUT_FILE"
jq '.metadata' "$OUTPUT_FILE"
```

---

## 8. Implementation Recommendations

### 8.1 Dependencies

**Required:**
- `bash` (v4.0+)
- `jq` (v1.6+)
- `yq` (v4.0+, for YAML parsing)
- `awk` (GNU awk recommended)
- `sed` (GNU sed recommended)
- `grep` (GNU grep with `-P` Perl regex support)

**Installation:**
```bash
# Ubuntu/Debian
sudo apt-get install jq gawk sed grep

# Install yq (Go version, not Python yq)
sudo wget -qO /usr/local/bin/yq https://github.com/mikefarah/yq/releases/latest/download/yq_linux_amd64
sudo chmod +x /usr/local/bin/yq
```

### 8.2 Parsing Complexity Ranking

| Data Source | Complexity | Reason | Recommended Approach |
|-------------|------------|--------|---------------------|
| settings.json | **Low** | Already JSON | Direct `jq` |
| Hook scripts | **Low** | Predictable structure | `grep` + `awk` |
| Agent frontmatter | **Medium** | YAML with multi-line strings | `yq` + `jq` |
| CLAUDE.md tables | **Medium** | Markdown tables | `awk` table parser |
| Skill frontmatter | **High** | Complex YAML, embedded structure | `yq` + regex extraction |
| Skill L2 body | **High** | Free-form markdown with sections | Section-based `awk` parser |
| MEMORY.md | **High** | Mixed tables + narrative | Multiple `awk` parsers per section |

### 8.3 Error Handling Strategy

```bash
# Graceful degradation pattern
parse_with_fallback() {
    local parser="$1"
    local fallback_value="$2"

    local result
    if result=$($parser 2>/dev/null); then
        echo "$result"
    else
        echo "$fallback_value"
        echo "WARN: Parser failed, using fallback" >&2
    fi
}

# Example usage
AGENTS_JSON=$(parse_with_fallback "./extract-agents.sh" "[]")
```

### 8.4 Performance Optimization

For 35+ skills:
- **Parallel processing:** Use `xargs -P` for skill extraction
- **Caching:** Store intermediate JSON fragments, rebuild only changed files
- **Incremental builds:** Track file mtimes, skip unchanged files

```bash
# Parallel skill extraction
find .claude/skills/*/SKILL.md -type f | \
  xargs -P 4 -I {} bash -c 'parse_skill "{}"' | \
  jq -s .
```

### 8.5 Validation

```bash
# Validate extracted JSON schema
validate_dashboard_data() {
    local file="$1"

    # Check required top-level keys
    for key in metadata agents skills hooks settings claude_md memory_md; do
        if ! jq -e ".$key" "$file" >/dev/null 2>&1; then
            echo "ERROR: Missing required key: $key" >&2
            return 1
        fi
    done

    # Check array lengths match expected counts
    local agent_count=$(jq '.agents | length' "$file")
    local skill_count=$(jq '.skills | length' "$file")
    local hook_count=$(jq '.hooks | length' "$file")

    echo "Validation: $agent_count agents, $skill_count skills, $hook_count hooks"

    # Expected: 6 agents, 35 skills, 5 hooks
    [[ "$agent_count" -eq 6 ]] || echo "WARN: Expected 6 agents, found $agent_count"
    [[ "$skill_count" -eq 35 ]] || echo "WARN: Expected 35 skills, found $skill_count"
    [[ "$hook_count" -eq 5 ]] || echo "WARN: Expected 5 hooks, found $hook_count"
}
```

---

## 9. Summary

### 9.1 Data Extraction Complexity Matrix

| File Type | Count | Fields to Extract | Parser Toolchain | Estimated LOC |
|-----------|-------|-------------------|------------------|---------------|
| Agents | 6 | 7 fields + tools array | yq + jq + awk | ~50 |
| Skills | 35 | 6 frontmatter + 5 body sections | yq + jq + awk + grep | ~120 |
| Hooks | 5 | 6 metadata fields | grep + awk + jq | ~40 |
| settings.json | 1 | 8 top-level fields | jq | ~20 |
| CLAUDE.md | 1 | 5 sections + 1 table | awk + grep + jq | ~60 |
| MEMORY.md | 1 | 3 tables + session history | awk + grep + jq | ~80 |
| **Total** | **49** | **~45 fields** | **bash + jq + yq + awk** | **~370 LOC** |

### 9.2 Key Insights

1. **YAML Frontmatter:** yq is essential for robust parsing. Fallback to awk/sed is possible but fragile.
2. **Multi-line Descriptions:** Agent and skill descriptions encode structured data in free-form text. Regex extraction needed.
3. **Phase Tags:** Skill phase tags (`[P{N}·Domain·Skill]`) are the primary routing metadata. Extract early.
4. **Markdown Tables:** CLAUDE.md and MEMORY.md use markdown tables. Standard awk field splitting works.
5. **Hook Configuration:** Split between hook scripts (bash comments) and settings.json (event config). Merge during extraction.
6. **Session History:** MEMORY.md session entries follow predictable pattern. Regex-based extraction sufficient.

### 9.3 Recommended Implementation Order

1. **Phase 1 — Low-Hanging Fruit:**
   - settings.json (direct jq)
   - Hook scripts (grep + awk)
   - CLAUDE.md version and agent list

2. **Phase 2 — Core Data:**
   - Agent frontmatter (yq + jq)
   - Skill frontmatter (yq + jq + regex)
   - MEMORY.md INFRA State table

3. **Phase 3 — Advanced Parsing:**
   - Skill L2 body sections
   - MEMORY.md skills domain table
   - Session history extraction

4. **Phase 4 — Integration:**
   - Master build script
   - JSON schema validation
   - Error handling and fallbacks

### 9.4 Deliverables

**Scripts to Create:**
1. `extract-agents.sh` — Agent frontmatter to JSON (50 LOC)
2. `extract-skills.sh` — Skill frontmatter + body to JSON (120 LOC)
3. `extract-hooks.sh` — Hook metadata to JSON (40 LOC)
4. `extract-claude-md.sh` — CLAUDE.md sections to JSON (60 LOC)
5. `extract-memory-md.sh` — MEMORY.md tables to JSON (80 LOC)
6. `dashboard-build.sh` — Master orchestration script (50 LOC)
7. `validate-dashboard-data.sh` — JSON schema validation (30 LOC)

**Total Estimated Size:** 430 LOC across 7 scripts

---

## Appendix A: File Path Reference

```
.claude/
├── agents/
│   ├── analyst.md
│   ├── researcher.md
│   ├── implementer.md
│   ├── infra-implementer.md
│   ├── delivery-agent.md
│   └── pt-manager.md
├── skills/
│   ├── pre-design-brainstorm/SKILL.md
│   ├── pre-design-validate/SKILL.md
│   ├── pre-design-feasibility/SKILL.md
│   ├── design-architecture/SKILL.md
│   ├── design-interface/SKILL.md
│   ├── design-risk/SKILL.md
│   ├── research-codebase/SKILL.md
│   ├── research-external/SKILL.md
│   ├── research-audit/SKILL.md
│   ├── plan-decomposition/SKILL.md
│   ├── plan-interface/SKILL.md
│   ├── plan-strategy/SKILL.md
│   ├── plan-verify-correctness/SKILL.md
│   ├── plan-verify-completeness/SKILL.md
│   ├── plan-verify-robustness/SKILL.md
│   ├── orchestration-decompose/SKILL.md
│   ├── orchestration-assign/SKILL.md
│   ├── orchestration-verify/SKILL.md
│   ├── execution-code/SKILL.md
│   ├── execution-infra/SKILL.md
│   ├── execution-impact/SKILL.md
│   ├── execution-cascade/SKILL.md
│   ├── execution-review/SKILL.md
│   ├── verify-structure/SKILL.md
│   ├── verify-content/SKILL.md
│   ├── verify-consistency/SKILL.md
│   ├── verify-quality/SKILL.md
│   ├── verify-cc-feasibility/SKILL.md
│   ├── delivery-pipeline/SKILL.md
│   ├── pipeline-resume/SKILL.md
│   ├── task-management/SKILL.md
│   ├── manage-infra/SKILL.md
│   ├── manage-skills/SKILL.md
│   ├── manage-codebase/SKILL.md
│   └── self-improve/SKILL.md
├── hooks/
│   ├── on-subagent-start.sh
│   ├── on-session-compact.sh
│   ├── on-implementer-done.sh
│   ├── on-file-change.sh
│   └── on-pre-compact.sh
├── settings.json
├── CLAUDE.md
└── projects/
    └── -home-palantir/
        └── memory/
            └── MEMORY.md
```

**Total Files:** 49
**Total Size (estimated):** ~150KB

---

## Appendix B: Sample Extraction Commands

### B.1 Quick Agent Count

```bash
ls -1 .claude/agents/*.md | wc -l
# Output: 6
```

### B.2 Quick Skill Count

```bash
find .claude/skills -name "SKILL.md" | wc -l
# Output: 35
```

### B.3 Extract All Phase Tags

```bash
find .claude/skills -name "SKILL.md" -exec awk '/^---$/{p++; next} p==1 && /^description:/{flag=1; next} flag && /^[a-z]+:/{flag=0} flag' {} \; | \
  grep -oP '\[P?\d+·[^]]+\]|\[[^]]+·[^]]+·[^]]+\]' | \
  sort -u
```

**Output:**
```
[Homeostasis·Manager·Infra]
[P0·PreDesign·Brainstorm]
[P0·PreDesign·Feasibility]
[P0·PreDesign·Validate]
[P1·Design·Architecture]
...
```

### B.4 Extract Agent Tool Lists

```bash
for agent in .claude/agents/*.md; do
  echo "=== $(basename "$agent" .md) ==="
  awk '/^tools:/,/^[a-z]+:/' "$agent" | grep '  - ' | sed 's/^  - //'
done
```

### B.5 Extract Hook Event Matchers from settings.json

```bash
jq -r '.hooks | to_entries[] | "\(.key): \(.value[].matcher)"' .claude/settings.json
```

**Output:**
```
SubagentStart:
PreCompact:
SessionStart: compact
PostToolUse: Edit|Write
SubagentStop: implementer|infra-implementer
```

---

**End of Analysis**
