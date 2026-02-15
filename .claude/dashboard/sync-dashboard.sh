#!/usr/bin/env bash
# sync-dashboard.sh — Parse .claude/ infrastructure files and generate dashboard
# Produces JSON data from agents, skills, hooks, settings, CLAUDE.md, MEMORY.md
# Then injects into template.html to produce index.html
#
# Usage: ./sync-dashboard.sh [--json-only] [--help]
# Dependencies: bash 4+, jq 1.7+, python3 3.12+, awk, sed, grep

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
CLAUDE_DIR="$REPO_ROOT/.claude"
TEMPLATE_FILE="$SCRIPT_DIR/template.html"
OUTPUT_FILE="$SCRIPT_DIR/index.html"
JSON_ONLY=false
TMPDIR_DASH=$(mktemp -d)
trap 'rm -rf "$TMPDIR_DASH"' EXIT

# --- Help -------------------------------------------------------------------

show_help() {
    cat <<'HELP'
sync-dashboard.sh — Parse .claude/ infrastructure and generate dashboard

Usage:
    ./sync-dashboard.sh              Build index.html from template + data
    ./sync-dashboard.sh --json-only  Print extracted JSON to stdout (no HTML)
    ./sync-dashboard.sh --help       Show this help

Dependencies: bash 4+, jq 1.7+, python3 3.12+, awk, sed, grep
No external deps (no yq, no pip install).

Must be run from repo root or via absolute path.
HELP
    exit 0
}

# --- Argument parsing --------------------------------------------------------

for arg in "$@"; do
    case "$arg" in
        --json-only) JSON_ONLY=true ;;
        --help|-h)   show_help ;;
        *)           echo "ERROR: Unknown argument: $arg" >&2; exit 1 ;;
    esac
done

# --- Dependency check --------------------------------------------------------

check_deps() {
    local missing=()
    for cmd in jq python3 awk sed grep git; do
        if ! command -v "$cmd" &>/dev/null; then
            missing+=("$cmd")
        fi
    done
    if [[ ${#missing[@]} -gt 0 ]]; then
        echo "ERROR: Missing required commands: ${missing[*]}" >&2
        exit 1
    fi
}
check_deps

# --- Utility: graceful parse with fallback -----------------------------------

parse_with_fallback() {
    local label="$1"
    local fallback="$2"
    shift 2
    local result
    if result=$("$@" 2>/dev/null); then
        # Validate JSON
        if echo "$result" | jq empty 2>/dev/null; then
            echo "$result"
        else
            echo "WARN: [$label] produced invalid JSON, using fallback" >&2
            echo "$fallback"
        fi
    else
        echo "WARN: [$label] parser failed, using fallback" >&2
        echo "$fallback"
    fi
}

# =============================================================================
# SECTION 1: METADATA
# =============================================================================

parse_metadata() {
    local generated_at
    generated_at=$(date -u +"%Y-%m-%dT%H:%M:%SZ")

    local infra_version="unknown"
    if [[ -f "$CLAUDE_DIR/CLAUDE.md" ]]; then
        infra_version=$(grep -oP 'v[\d.]+' "$CLAUDE_DIR/CLAUDE.md" | head -1) || true
    fi

    local git_branch="unknown"
    local git_commit="unknown"
    if git -C "$REPO_ROOT" rev-parse --is-inside-work-tree &>/dev/null; then
        git_branch=$(git -C "$REPO_ROOT" rev-parse --abbrev-ref HEAD 2>/dev/null) || true
        git_commit=$(git -C "$REPO_ROOT" rev-parse --short HEAD 2>/dev/null) || true
    fi

    jq -n \
        --arg ts "$generated_at" \
        --arg ver "$infra_version" \
        --arg branch "$git_branch" \
        --arg commit "$git_commit" \
        '{
            generated_at: $ts,
            infra_version: $ver,
            git_branch: $branch,
            git_commit: $commit
        }'
}

# =============================================================================
# SECTION 2: AGENTS (python3 helper script)
# =============================================================================

parse_agents() {
    local agents_dir="$CLAUDE_DIR/agents"

    cat > "$TMPDIR_DASH/parse_agents.py" << 'PYEOF'
import sys, json, re, os, glob

agents_dir = sys.argv[1]
results = []

for agent_path in sorted(glob.glob(os.path.join(agents_dir, '*.md'))):
    with open(agent_path, 'r') as f:
        content = f.read()

    match = re.search(r'^---\n(.*?)\n---', content, re.DOTALL)
    if not match:
        continue

    fm = match.group(1)
    agent = {}

    # Parse simple single-line fields
    for field in ['name', 'memory', 'color', 'model']:
        m = re.search(r'^' + field + r':\s*(.+)$', fm, re.MULTILINE)
        if m:
            agent[field] = m.group(1).strip()

    # Parse maxTurns as integer
    m = re.search(r'^maxTurns:\s*(\d+)', fm, re.MULTILINE)
    if m:
        agent['maxTurns'] = int(m.group(1))

    # Parse tools array
    tools = []
    in_tools = False
    for line in fm.split('\n'):
        if line.startswith('tools:'):
            in_tools = True
            continue
        if in_tools:
            if line.startswith('  - '):
                tools.append(line[4:].strip())
            elif line and not line.startswith(' '):
                in_tools = False
    agent['tools'] = tools

    # Parse description (multi-line after 'description: |')
    desc_match = re.search(r'^description:\s*\|\n(.*?)(?=^\S|^---)', fm, re.DOTALL | re.MULTILINE)
    if desc_match:
        desc_text = desc_match.group(1)
        desc_lines = [l[2:] if l.startswith('  ') else l for l in desc_text.split('\n')]
        desc = '\n'.join(desc_lines).strip()

        # Extract profile tag
        tag_match = re.search(r'\[Profile-\w+[^\]]*\]', desc)
        if tag_match:
            agent['profile_tag'] = tag_match.group(0)

    agent['source_file'] = os.path.basename(agent_path)
    results.append(agent)

print(json.dumps(results, indent=2))
PYEOF

    python3 "$TMPDIR_DASH/parse_agents.py" "$agents_dir"
}

# =============================================================================
# SECTION 3: SKILLS (python3 helper script)
# =============================================================================

parse_skills() {
    local skills_dir="$CLAUDE_DIR/skills"

    cat > "$TMPDIR_DASH/parse_skills.py" << 'PYEOF'
import sys, json, re, os, glob

skills_dir = sys.argv[1]
results = []

for skill_path in sorted(glob.glob(os.path.join(skills_dir, '*', 'SKILL.md'))):
    with open(skill_path, 'r') as f:
        content = f.read()

    match = re.search(r'^---\n(.*?)\n---', content, re.DOTALL)
    if not match:
        continue

    fm = match.group(1)
    body = content[match.end():]
    skill = {}

    # Parse name
    m = re.search(r'^name:\s*(.+)$', fm, re.MULTILINE)
    if m:
        skill['name'] = m.group(1).strip()

    # Parse booleans
    for field in ['user-invocable', 'disable-model-invocation']:
        m = re.search(r'^' + re.escape(field) + r':\s*(true|false)', fm, re.MULTILINE)
        if m:
            skill[field.replace('-', '_')] = m.group(1) == 'true'
        else:
            skill[field.replace('-', '_')] = False

    # Parse argument-hint (quoted value)
    m = re.search(r'^argument-hint:\s*["\'](.+?)["\']', fm, re.MULTILINE)
    if m:
        skill['argument_hint'] = m.group(1)

    # Parse description
    desc_match = re.search(r'^description:\s*\|\n(.*?)(?=^\S|^---)', fm, re.DOTALL | re.MULTILINE)
    if desc_match:
        desc_text = desc_match.group(1)
        desc_lines = [l[2:] if l.startswith('  ') else l for l in desc_text.split('\n')]
        desc = '\n'.join(desc_lines).strip()

        # Extract phase tag [P{N}*Domain*Skill] or [Homeostasis*...] or [X-Cut*...]
        tag_match = re.search(r'\[[^\]]+\]', desc)
        if tag_match:
            skill['phase_tag'] = tag_match.group(0)

        # Extract phase number
        phase_match = re.search(r'\[P(\d+)', desc)
        if phase_match:
            skill['phase'] = 'P' + phase_match.group(1)
        elif 'Homeostasis' in desc[:80]:
            skill['phase'] = 'X-cut'
        elif 'X-Cut' in desc[:80]:
            skill['phase'] = 'X-cut'

        # Extract domain from DOMAIN: line
        domain_match = re.search(r'DOMAIN:\s*(\S+)', desc)
        if domain_match:
            raw_domain = domain_match.group(1).rstrip('.').rstrip(',')
            # Normalize: "Homeostasis" -> "homeostasis"
            skill['domain'] = raw_domain.lower() if raw_domain[0].isupper() else raw_domain

        # Description preview (first 100 chars, first line only)
        first_line = desc.split('\n')[0]
        skill['description_preview'] = first_line[:100]

    # Parse body sections
    body_sections = {}
    body_sections['has_execution_model'] = bool(re.search(r'^## Execution Model', body, re.MULTILINE))
    body_sections['has_methodology'] = bool(re.search(r'^## Methodology', body, re.MULTILINE))
    body_sections['has_quality_gate'] = bool(re.search(r'^## Quality Gate', body, re.MULTILINE))
    body_sections['has_output'] = bool(re.search(r'^## Output', body, re.MULTILINE))
    body_sections['has_decision_points'] = bool(re.search(r'^## Decision Points', body, re.MULTILINE))
    body_sections['has_failure_handling'] = bool(re.search(r'^## (Failure|Error) Handling', body, re.MULTILINE))
    body_sections['has_anti_patterns'] = bool(re.search(r'^## Anti-Patterns', body, re.MULTILINE))
    body_sections['has_transitions'] = bool(re.search(r'^## Transitions', body, re.MULTILINE))

    # Count methodology steps (### N. Title)
    steps = re.findall(r'^### \d+\.', body, re.MULTILINE)
    body_sections['methodology_steps'] = len(steps)

    skill['body_sections'] = body_sections
    skill['char_count'] = len(content)
    skill['skill_dir'] = os.path.basename(os.path.dirname(skill_path))

    results.append(skill)

print(json.dumps(results, indent=2))
PYEOF

    python3 "$TMPDIR_DASH/parse_skills.py" "$skills_dir"
}

# =============================================================================
# SECTION 4: HOOKS (python3 helper script)
# =============================================================================

parse_hooks() {
    local settings_file="$CLAUDE_DIR/settings.json"
    local hooks_dir="$CLAUDE_DIR/hooks"

    if [[ ! -f "$settings_file" ]]; then
        echo "[]"
        return
    fi

    cat > "$TMPDIR_DASH/parse_hooks.py" << 'PYEOF'
import json, re, os, sys

settings_path = sys.argv[1]
hooks_dir = sys.argv[2]

with open(settings_path, 'r') as f:
    settings = json.load(f)

hooks_config = settings.get('hooks', {})
result = []

for event_name, matchers in hooks_config.items():
    for matcher_group in matchers:
        matcher = matcher_group.get('matcher', '')
        for hook in matcher_group.get('hooks', []):
            command = hook.get('command', '')
            timeout = hook.get('timeout', 0)
            is_async = hook.get('async', False)

            hook_file = os.path.basename(command) if command else ''

            # Read description from script header
            description = ''
            script_path = os.path.join(hooks_dir, hook_file) if hook_file else ''
            if script_path and os.path.isfile(script_path):
                try:
                    with open(script_path, 'r') as sf:
                        for line in sf:
                            line = line.strip()
                            if line.startswith('#!'):
                                continue
                            if line.startswith('# Hook:'):
                                # "# Hook: EventName — Description"
                                desc_match = re.search(r'Hook:\s*\S+\s*[\u2014—-]+\s*(.*)', line)
                                if desc_match:
                                    description = desc_match.group(1).strip()
                                else:
                                    description = line.lstrip('# ').strip()
                                break
                            elif line.startswith('# SRC'):
                                # "# SRC Stage N: Description"
                                desc_match = re.search(r'SRC Stage \d+:\s*(.*)', line)
                                if desc_match:
                                    description = desc_match.group(1).strip()
                                else:
                                    description = line.lstrip('# ').strip()
                                break
                            elif line.startswith('#') and not line.startswith('#!'):
                                description = line.lstrip('# ').strip()
                                break
                except Exception:
                    pass

            result.append({
                'hook_file': hook_file,
                'event': event_name,
                'matcher': matcher,
                'timeout': timeout,
                'async': is_async,
                'description': description
            })

print(json.dumps(result, indent=2))
PYEOF

    python3 "$TMPDIR_DASH/parse_hooks.py" "$settings_file" "$hooks_dir"
}

# =============================================================================
# SECTION 5: SETTINGS
# =============================================================================

parse_settings() {
    local settings_file="$CLAUDE_DIR/settings.json"

    if [[ ! -f "$settings_file" ]]; then
        echo '{}'
        return
    fi

    jq '{
        model: .model,
        teammate_mode: .teammateMode,
        always_thinking: .alwaysThinkingEnabled,
        env_var_count: (.env // {} | keys | length),
        hook_event_count: (.hooks // {} | keys | length),
        permission_allow_count: (.permissions.allow // [] | length),
        permission_deny_count: (.permissions.deny // [] | length),
        enabled_plugins: ([.enabledPlugins // {} | to_entries[] | select(.value == true) | .key]),
        env_vars: (.env // {} | keys),
        permission_allow: (.permissions.allow // []),
        permission_deny: (.permissions.deny // [])
    }' "$settings_file" 2>/dev/null || echo '{}'
}

# =============================================================================
# SECTION 6: CLAUDE.md
# =============================================================================

parse_claude_md() {
    local claude_md="$CLAUDE_DIR/CLAUDE.md"

    if [[ ! -f "$claude_md" ]]; then
        echo '{}'
        return
    fi

    local version
    version=$(grep -oP 'v[\d.]+' "$claude_md" | head -1) || version="unknown"

    local line_count
    line_count=$(wc -l < "$claude_md") || line_count=0

    local section_count
    section_count=$(grep -c '^## ' "$claude_md") || section_count=0

    # Parse tier table
    local tier_json
    tier_json=$(awk '
        /^\| Tier \|/ { capture=1; next }
        /^\|---/ && capture { next }
        capture && /^\|/ {
            n = split($0, a, "|")
            if (n >= 4) {
                gsub(/^[ \t]+|[ \t]+$/, "", a[2])
                gsub(/^[ \t]+|[ \t]+$/, "", a[3])
                gsub(/^[ \t]+|[ \t]+$/, "", a[4])
                if (a[2] != "" && a[2] != "------") {
                    gsub(/"/, "\\\"", a[2])
                    gsub(/"/, "\\\"", a[3])
                    gsub(/"/, "\\\"", a[4])
                    printf "{\"tier\":\"%s\",\"criteria\":\"%s\",\"phases\":\"%s\"}\n", a[2], a[3], a[4]
                }
            }
        }
        capture && !/^\|/ { capture=0 }
    ' "$claude_md" | jq -s '.' 2>/dev/null) || tier_json="[]"

    jq -n \
        --arg ver "$version" \
        --argjson lc "$line_count" \
        --argjson sc "$section_count" \
        --argjson tiers "$tier_json" \
        '{
            version: $ver,
            line_count: $lc,
            section_count: $sc,
            tier_table: $tiers
        }'
}

# =============================================================================
# SECTION 7: MEMORY.md (python3 helper script)
# =============================================================================

parse_memory_md() {
    local memory_md="$CLAUDE_DIR/projects/-home-palantir/memory/MEMORY.md"

    if [[ ! -f "$memory_md" ]]; then
        echo '{}'
        return
    fi

    cat > "$TMPDIR_DASH/parse_memory.py" << 'PYEOF'
import json, re, sys

memory_path = sys.argv[1]

with open(memory_path, 'r') as f:
    content = f.read()
lines = content.split('\n')

result = {}

# Extract INFRA State version and date
m = re.search(r'## Current INFRA State \((v[\d.]+),\s*(\d{4}-\d{2}-\d{2})\)', content)
if m:
    result['infra_version'] = m.group(1)
    result['infra_date'] = m.group(2)

# Parse INFRA State component table
components = []
in_component_table = False
for line in lines:
    if '| Component |' in line:
        in_component_table = True
        continue
    if in_component_table:
        if line.startswith('|---'):
            continue
        if line.startswith('|'):
            parts = [p.strip() for p in line.split('|')]
            if len(parts) >= 5 and parts[1]:
                components.append({
                    'component': parts[1],
                    'version': parts[2],
                    'size': parts[3],
                    'key_feature': parts[4]
                })
        else:
            in_component_table = False
result['components'] = components

# Parse skill domains table
skill_domains = []
in_skills_table = False
for line in lines:
    if '| Domain |' in line and '| Skills |' in line:
        in_skills_table = True
        continue
    if in_skills_table:
        if line.startswith('|---'):
            continue
        if line.startswith('|'):
            parts = [p.strip() for p in line.split('|')]
            if len(parts) >= 4 and parts[1]:
                skill_domains.append({
                    'domain': parts[1],
                    'skills': parts[2],
                    'phase': parts[3]
                })
        else:
            in_skills_table = False
result['skill_domains'] = skill_domains

# Parse known bugs table
known_bugs = []
in_bugs_table = False
for line in lines:
    if '| ID |' in line and '| Severity |' in line:
        in_bugs_table = True
        continue
    if in_bugs_table:
        if line.startswith('|---'):
            continue
        if line.startswith('|'):
            parts = [p.strip() for p in line.split('|')]
            if len(parts) >= 5 and parts[1]:
                known_bugs.append({
                    'id': parts[1],
                    'severity': parts[2],
                    'summary': parts[3],
                    'workaround': parts[4]
                })
        else:
            in_bugs_table = False
result['known_bugs'] = known_bugs

# Parse session history entries
session_history = []
in_sessions = False
for line in lines:
    if line.startswith('## Session History'):
        in_sessions = True
        continue
    if in_sessions and line.startswith('## ') and 'Session History' not in line:
        break
    if in_sessions and line.startswith('### '):
        entry = line[4:]
        title_match = re.match(r'^(.*?)\s*\((\d{4}-\d{2}-\d{2}),\s*branch:\s*([^)]+)\)', entry)
        if title_match:
            session_history.append({
                'title': title_match.group(1).strip(),
                'date': title_match.group(2),
                'branch': title_match.group(3)
            })

result['session_count'] = len(session_history)
result['session_history'] = session_history

print(json.dumps(result, indent=2))
PYEOF

    python3 "$TMPDIR_DASH/parse_memory.py" "$memory_md"
}

# =============================================================================
# SECTION 8: PIPELINE (python3 helper script)
# =============================================================================

parse_pipeline() {
    local memory_md="$CLAUDE_DIR/projects/-home-palantir/memory/MEMORY.md"

    cat > "$TMPDIR_DASH/parse_pipeline.py" << 'PYEOF'
import json, re, sys

memory_path = sys.argv[1]
phases = ['P0','P1','P2','P3','P4','P5','P6','P7','P8','X-cut']

domain_phase = {
    'pre-design': 'P0',
    'design': 'P1',
    'research': 'P2',
    'plan': 'P3',
    'plan-verify': 'P4',
    'orchestration': 'P5',
    'execution': 'P6',
    'verify': 'P7',
    'homeostasis': 'X-cut',
    'cross-cutting': 'P8'
}

domain_skills = {}

try:
    with open(memory_path, 'r') as f:
        content = f.read()
    lines = content.split('\n')
    in_table = False
    for line in lines:
        if '| Domain |' in line and '| Skills |' in line and '| Phase |' in line:
            in_table = True
            continue
        if in_table:
            if line.startswith('|---'):
                continue
            if line.startswith('|'):
                parts = [p.strip() for p in line.split('|')]
                if len(parts) >= 4 and parts[1]:
                    domain = parts[1]
                    skills_str = parts[2].replace('**', '')
                    skills_list = [s.strip() for s in skills_str.split(',')]
                    domain_skills[domain] = skills_list
            else:
                in_table = False
except Exception:
    pass

domains = {}
for domain, skills in domain_skills.items():
    phase = domain_phase.get(domain, 'unknown')
    domains[phase] = domains.get(phase, []) + skills

result = {
    'phases': phases,
    'domains': domains
}

print(json.dumps(result, indent=2))
PYEOF

    python3 "$TMPDIR_DASH/parse_pipeline.py" "$memory_md"
}

# =============================================================================
# MAIN: Assemble all data
# =============================================================================

main() {
    echo "Parsing .claude/ infrastructure..." >&2

    echo "  [1/8] metadata..." >&2
    local metadata_json
    metadata_json=$(parse_with_fallback "metadata" '{}' parse_metadata)

    echo "  [2/8] agents..." >&2
    local agents_json
    agents_json=$(parse_with_fallback "agents" '[]' parse_agents)

    echo "  [3/8] skills..." >&2
    local skills_json
    skills_json=$(parse_with_fallback "skills" '[]' parse_skills)

    echo "  [4/8] hooks..." >&2
    local hooks_json
    hooks_json=$(parse_with_fallback "hooks" '[]' parse_hooks)

    echo "  [5/8] settings..." >&2
    local settings_json
    settings_json=$(parse_with_fallback "settings" '{}' parse_settings)

    echo "  [6/8] CLAUDE.md..." >&2
    local claude_md_json
    claude_md_json=$(parse_with_fallback "claude_md" '{}' parse_claude_md)

    echo "  [7/8] MEMORY.md..." >&2
    local memory_md_json
    memory_md_json=$(parse_with_fallback "memory_md" '{}' parse_memory_md)

    echo "  [8/8] pipeline..." >&2
    local pipeline_json
    pipeline_json=$(parse_with_fallback "pipeline" '{"phases":[],"domains":{}}' parse_pipeline)

    # Assemble final JSON
    local full_json
    full_json=$(jq -n \
        --argjson metadata "$metadata_json" \
        --argjson agents "$agents_json" \
        --argjson skills "$skills_json" \
        --argjson hooks "$hooks_json" \
        --argjson settings "$settings_json" \
        --argjson claude_md "$claude_md_json" \
        --argjson memory_md "$memory_md_json" \
        --argjson pipeline "$pipeline_json" \
        '{
            metadata: $metadata,
            agents: $agents,
            skills: $skills,
            hooks: $hooks,
            settings: $settings,
            claude_md: $claude_md,
            memory_md: $memory_md,
            pipeline: $pipeline
        }')

    # --json-only: just print and exit
    if [[ "$JSON_ONLY" == true ]]; then
        echo "$full_json"
        print_summary "$full_json" >&2
        exit 0
    fi

    # Build HTML from template
    if [[ ! -f "$TEMPLATE_FILE" ]]; then
        echo "WARN: template.html not found at $TEMPLATE_FILE" >&2
        echo "WARN: Outputting JSON only (use --json-only or create template.html)" >&2
        echo "$full_json"
        print_summary "$full_json" >&2
        exit 0
    fi

    # Inject JSON data into template
    # The template contains: /*DASHBOARD_DATA_PLACEHOLDER*/null
    cat > "$TMPDIR_DASH/inject_template.py" << 'PYEOF'
import sys, json

template_path = sys.argv[1]
output_path = sys.argv[2]

json_data = sys.stdin.read()

# Validate JSON
obj = json.loads(json_data)
compact_json = json.dumps(obj)

with open(template_path, 'r') as f:
    template = f.read()

output = template.replace('/*DASHBOARD_DATA_PLACEHOLDER*/null', compact_json)

with open(output_path, 'w') as f:
    f.write(output)

print(f'Dashboard written to {output_path}', file=sys.stderr)
PYEOF

    echo "$full_json" | python3 "$TMPDIR_DASH/inject_template.py" "$TEMPLATE_FILE" "$OUTPUT_FILE"

    print_summary "$full_json" >&2
    local output_size
    output_size=$(wc -c < "$OUTPUT_FILE")
    echo "  Output: $OUTPUT_FILE ($(numfmt --to=iec "$output_size" 2>/dev/null || echo "${output_size}B"))" >&2
}

print_summary() {
    local json="$1"
    echo "" >&2
    echo "=== Dashboard Data Summary ===" >&2
    echo "  Agents:   $(echo "$json" | jq '.agents | length')" >&2
    echo "  Skills:   $(echo "$json" | jq '.skills | length')" >&2
    echo "  Hooks:    $(echo "$json" | jq '.hooks | length')" >&2
    echo "  Sessions: $(echo "$json" | jq '.memory_md.session_count // 0')" >&2
    echo "  Bugs:     $(echo "$json" | jq '.memory_md.known_bugs | length')" >&2
    echo "  Version:  $(echo "$json" | jq -r '.metadata.infra_version')" >&2
    echo "  Branch:   $(echo "$json" | jq -r '.metadata.git_branch')" >&2
    echo "  Commit:   $(echo "$json" | jq -r '.metadata.git_commit')" >&2
    echo "===============================" >&2
}

main
