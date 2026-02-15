# RSI L5 Dashboard Audit Report

**Scope**: `/home/palantir/.claude/dashboard/` (3 files: sync-dashboard.sh, template.html, .gitignore)
**Date**: 2026-02-15
**Analyst**: analyst agent
**Coverage**: 100% (767 + 2441 + 3 = 3211 lines analyzed)

---

## Executive Summary

| Severity | Count |
|----------|-------|
| CRITICAL | 1 |
| HIGH | 7 |
| MEDIUM | 11 |
| LOW | 9 |
| ADVISORY | 6 |
| **Total** | **34** |

Overall quality is good for a first implementation. The bash script has robust error handling (parse_with_fallback, trap cleanup, set -euo pipefail). The HTML template has proper ARIA tab management and keyboard navigation. However, there are real bugs in data contract mismatches, YAML parsing edge cases, and JavaScript correctness issues.

---

## Findings

### CRITICAL

#### C-01: `enabledPlugins` parsed as object keys, template expects array
**File**: `/home/palantir/.claude/dashboard/sync-dashboard.sh:389`
**File**: `/home/palantir/.claude/dashboard/template.html:2371`

The settings parser extracts `enabledPlugins` as:
```bash
enabled_plugins: (.enabledPlugins | keys)
```
This produces `["superpowers-developing-for-claude-code@superpowers-marketplace", "superpowers@superpowers-marketplace"]` -- an array of string keys.

However, in `settings.json`, `.enabledPlugins` is an object with boolean values:
```json
"enabledPlugins": {
    "superpowers-developing-for-claude-code@superpowers-marketplace": true,
    "superpowers@superpowers-marketplace": true
}
```

The jq expression `.enabledPlugins | keys` works correctly today because both values are `true`. **But if a plugin is set to `false` (disabled), the key still appears in `keys`, making a disabled plugin look enabled in the dashboard.** The correct jq would be:
```jq
enabled_plugins: ([.enabledPlugins | to_entries[] | select(.value == true) | .key])
```

Additionally, if `enabledPlugins` is `null` or missing, `.enabledPlugins | keys` throws a jq error, causing the entire `parse_settings` function to fall through to `echo '{}'`, losing ALL settings data.

**Impact**: Silent data corruption -- disabled plugins displayed as enabled. Potential total settings section failure.

---

### HIGH

#### H-01: `parse_settings` crashes if `env`, `hooks`, `permissions.allow`, or `permissions.deny` is missing
**File**: `/home/palantir/.claude/dashboard/sync-dashboard.sh:381-391`

The jq expression assumes all nested paths exist:
```jq
env_var_count: (.env | keys | length),
hook_event_count: (.hooks | keys | length),
permission_allow_count: (.permissions.allow | length),
permission_deny_count: (.permissions.deny | length),
```

If any of `env`, `hooks`, `permissions`, `permissions.allow`, or `permissions.deny` is missing from settings.json, `keys` or `length` on `null` will produce a jq error. The fallback `|| echo '{}'` catches this, but it means the entire settings section renders with zero data (model, teammate_mode, etc. all lost).

**Fix**: Use null-coalescing: `(.env // {} | keys | length)`, `(.permissions.allow // [] | length)`, etc.

#### H-02: YAML description regex fails for non-pipe descriptions
**File**: `/home/palantir/.claude/dashboard/sync-dashboard.sh:169` (agents), `:233` (skills)

The regex for multi-line descriptions is:
```python
re.search(r'^description:\s*\|\n(.*?)(?=^[a-z])', fm, re.DOTALL | re.MULTILINE)
```

This pattern requires:
1. `description: |` with a pipe character (YAML block scalar)
2. The description to end at a line starting with a lowercase letter `[a-z]`

**Edge cases that fail**:
- A description that ends at a field starting with an uppercase letter (e.g., hypothetical `Tools:`) -- would consume too much
- A description that is the last field in frontmatter before `---` -- `(?=^[a-z])` never matches, so `desc_match` is `None`, and ALL description-derived fields (`phase_tag`, `phase`, `domain`, `description_preview`) are silently missing
- A single-line description like `description: "Short desc"` -- no match, same silent failure

Currently all 6 agents and 35 skills use `description: |` and have a subsequent lowercase field, so this works today. But adding a new agent/skill with different frontmatter ordering could silently lose the description.

#### H-03: `h()` helper handles `data` attributes incorrectly
**File**: `/home/palantir/.claude/dashboard/template.html:1702`

```javascript
else if (k.startsWith('data')) el.setAttribute(k.replace(/([A-Z])/g, '-$1').toLowerCase(), v);
```

This converts camelCase `data*` attributes to kebab-case via regex. However:
- `dataKo` becomes `data-ko` (correct)
- `dataEn` becomes `data-en` (correct)
- `dataSort` becomes `data-sort` (correct)

But the code also matches non-data attributes that happen to start with "data":
- A hypothetical attribute `database` would be mangled to `data-base`

More critically, the actual usage in the codebase passes `'data-ko'` and `'data-en'` as raw strings (already kebab-case). For these, the code path hits the `else if (k.startsWith('data'))` branch, and `k.replace(/([A-Z])/g, '-$1').toLowerCase()` transforms `data-ko` to `data-ko` (no change, coincidentally correct). But `data-ko-placeholder` would also match and would be handled in this path. This is fragile -- the function conflates `dataset` camelCase convention with raw `data-*` attribute strings.

#### H-04: Donut chart animation has race condition / visual glitch
**File**: `/home/palantir/.claude/dashboard/template.html:1926-1946`

```javascript
// Start with zero for animation
circle.style.strokeDashoffset = circumference + '';
// ...
setTimeout(() => {
    circle.style.strokeDashoffset = (-accumulated * circumference) + '';
}, 100 + idx * 80);
accumulated += pct;
```

The `accumulated` variable is captured by closure, but it is mutated AFTER the setTimeout is set. This means when the timeout fires, `accumulated` has already been incremented to its final value. However, because `accumulated` is read at the time the setTimeout callback executes (not when it's defined), the closure captures the *variable* not the *value*.

Wait -- actually, the callback computes `(-accumulated * circumference)` using the value of `accumulated` at the time the setTimeout fires. But `accumulated += pct` runs synchronously BEFORE any setTimeout fires. So by the time the first setTimeout fires, `accumulated` equals the sum of ALL percentages (1.0).

**Result**: Every donut ring animates to the same final offset (`-1.0 * circumference`), making all rings overlap at the same position. The donut chart is visually broken.

**Fix**: Capture the current value:
```javascript
const currentAccumulated = accumulated;
setTimeout(() => {
    circle.style.strokeDashoffset = (-currentAccumulated * circumference) + '';
}, 100 + idx * 80);
```

#### H-05: `setAttribute` on `stroke-dasharray` and `stroke-dashoffset` is immediately overwritten
**File**: `/home/palantir/.claude/dashboard/template.html:1935-1939`

```javascript
circle.setAttribute('stroke-dasharray', (pct * circumference) + ' ' + circumference);
circle.setAttribute('stroke-dashoffset', -accumulated * circumference + '');
// ...
// Start with zero for animation
circle.style.strokeDashoffset = circumference + '';
```

Line 1939 uses `circle.style.strokeDashoffset` which overrides the `stroke-dashoffset` attribute (inline style takes precedence over attribute). But on line 1936, the `stroke-dashoffset` is set via `setAttribute`. These two are fighting.

The intended behavior appears to be: setAttribute sets the "target", style sets the "start" for CSS transition. But CSS transitions on SVG attributes work via the *attribute* not the *property*. The `transition: stroke-dashoffset 1s` declared in CSS (`.donut-ring`) targets the SVG presentation attribute, but `el.style.strokeDashoffset` sets a CSS property, which may or may not trigger a CSS transition depending on browser SVG CSSOM support.

**Impact**: Animation may not work in all browsers. Firefox historically does not support CSS transitions on SVG stroke-dashoffset via the `style` property.

#### H-06: `phase-bg-x-cut` CSS class never defined
**File**: `/home/palantir/.claude/dashboard/template.html:2076, 2429`

```javascript
const phaseCls = 'phase-bg-' + phase.toLowerCase();  // "phase-bg-x-cut"
```

When `phase` is `"X-cut"`, this generates `phase-bg-x-cut`. But the CSS only defines:
```css
.phase-bg-x { background: var(--text-dim); }
```

There is no `.phase-bg-x-cut` class. So skills with `phase: "X-cut"` (homeostasis, cross-cutting) get no background color on their phase tag -- just a white/transparent badge on a dark background.

This also affects the domain matrix table at line 2429:
```javascript
'phase-tag phase-bg-' + ((d.phase || 'x').toLowerCase())
```
Where `d.phase` is `"X-cut"` from the MEMORY.md parser.

**Fix**: Either normalize the phase value to `"X"` before class generation, or add `.phase-bg-x-cut` to CSS.

#### H-07: Settings accordion `max-height: 500px` silently truncates tall content
**File**: `/home/palantir/.claude/dashboard/template.html:1113`

```css
&.open .accordion-panel {
    max-height: 500px;
}
```

If the permissions list or environment variables list exceeds 500px in rendered height, the content is silently clipped with `overflow: hidden`. With 10 permission allow rules and 7 deny rules, each rendering at ~24px, the permissions section is only ~408px. But if the user adds more rules, content will be invisibly clipped with no scrollbar.

**Fix**: Use a JavaScript-based accordion that measures actual content height, or set `max-height` to a very large value (e.g., `2000px`), or use `overflow-y: auto` on the panel.

---

### MEDIUM

#### M-01: `parse_memory.py` table parsing stops at first non-pipe line, misses multi-part tables
**File**: `/home/palantir/.claude/dashboard/sync-dashboard.sh:480-498, 502-521, 523-544`

Each table parser uses the pattern:
```python
if line.startswith('|'):
    # parse
else:
    in_table = False  # stops parsing
```

If there is a blank line within a markdown table (rare but valid), the parser prematurely terminates. More importantly, if the MEMORY.md file ever has two tables with the same header format (e.g., two `| Domain |` tables in different sections), the first one encountered wins and the second is ignored.

Currently this is not a problem because each table header is unique in MEMORY.md, but it is a fragile assumption.

#### M-02: Skill char utilization bar uses wrong denominator
**File**: `/home/palantir/.claude/dashboard/template.html:2078`

```javascript
const charPct = Math.round((s.char_count || 0) / 1024 * 100);
```

This calculates the percentage as `char_count / 1024 * 100`, treating 1024 chars as 100%. But `char_count` is the total SKILL.md file size (L1 frontmatter + L2 body), not the L1 description length. Typical skill files are 1000-3000 chars, so this bar always shows 100-300% and gets capped at `Math.min(charPct, 100)`, making every skill show a full green bar.

The L1 budget limit is 1024 chars for the description field only, not the entire file. The total file size is not a meaningful metric against 1024.

**Impact**: The utilization bar is meaningless -- it shows 100% for every skill.

#### M-03: No env_vars or permission_allow/permission_deny arrays in settings JSON output
**File**: `/home/palantir/.claude/dashboard/sync-dashboard.sh:381-391`
**File**: `/home/palantir/.claude/dashboard/template.html:2343-2367`

The template checks for `s.env_vars` (array), `s.permission_allow` (array), and `s.permission_deny` (array), but the bash script only outputs counts:
```jq
env_var_count: (.env | keys | length),
permission_allow_count: (.permissions.allow | length),
permission_deny_count: (.permissions.deny | length)
```

This means the template always falls through to the fallback paths:
- env_vars: shows "N variables" chip instead of individual variable names
- permissions: shows "N allow / M deny" text instead of the actual rule list

The accordion sections for environment variables and permissions are essentially dead UI -- they expand to show a single summary chip instead of detailed content.

**Fix**: Add the actual arrays to the jq output:
```jq
env_vars: (.env // {} | keys),
permission_allow: (.permissions.allow // []),
permission_deny: (.permissions.deny // [])
```

#### M-04: `h()` helper does not handle boolean attributes
**File**: `/home/palantir/.claude/dashboard/template.html:1698-1712`

The `h()` function treats all attribute values as strings via `el.setAttribute(k, v)`. For boolean HTML attributes like `disabled`, `hidden`, `required`, this works (setAttribute with any truthy value sets the attribute). But passing `false` will set `setAttribute('disabled', false)` which coerces to `"false"` string -- the attribute is still present and the element is still disabled.

Currently no code passes boolean attributes through `h()`, so this is latent.

#### M-05: Language toggle does not update dynamically-created bilingual elements
**File**: `/home/palantir/.claude/dashboard/template.html:1743-1761`

The `setLang()` function queries `$$('[data-ko]')` to update text. But many elements are created dynamically in the render functions using the `h()` helper with `'data-ko'` and `'data-en'` attributes. These dynamic elements ARE found by `$$('[data-ko]')` since they are in the DOM by the time the user clicks the language toggle.

However, some bilingual elements are created with direct `textContent` without `data-ko`/`data-en` attributes:
- Donut chart center label (line 1965): `centerLabel.textContent = currentLang === 'ko' ? ...` -- hardcoded at render time, never updated on toggle
- Stat card labels (line 1870): created with `data-ko`/`data-en` but initial text set inline -- these DO update correctly via setLang
- Agent memory labels (line 2029): created with `data-ko`/`data-en` -- these update correctly

**Impact**: The donut center label ("skills" vs "스킬") does not change when toggling language.

#### M-06: `os.path.basename(command)` fails for commands with arguments
**File**: `/home/palantir/.claude/dashboard/sync-dashboard.sh:320`

```python
hook_file = os.path.basename(command) if command else ''
```

If a hook command contains arguments (e.g., `/path/to/script.sh --flag`), `basename` returns `"script.sh --flag"`. Subsequently, `os.path.join(hooks_dir, hook_file)` produces a path like `/home/palantir/.claude/hooks/script.sh --flag` which is not a valid file path.

Currently all hooks in settings.json use bare paths without arguments, so this is latent.

#### M-07: Sort on `char_count` column uses wrong dataset key
**File**: `/home/palantir/.claude/dashboard/template.html:2177-2184`

The sort function reads `th.dataset.sort` which is `"char_count"` (from `data-sort="char_count"` on the `<th>`). Then:
```javascript
let va = a.dataset[key] || '';  // a.dataset.char_count
```

But the rows are created with `'data-chars'` (line 2089):
```javascript
'data-chars': String(s.char_count || 0)
```

So `a.dataset['char_count']` is `undefined`, not `a.dataset.chars`. The code then falls into the special case check:
```javascript
if (key === 'char_count' || key === 'chars') {
    va = parseInt(a.dataset.chars) || 0;
```

This does work because the condition `key === 'char_count'` matches. But `a.dataset[key]` (line 2177) returns `undefined`, and `'' || ''` = `''` is assigned to `va`, then immediately overwritten by `parseInt(a.dataset.chars)`. So the initial assignment is dead code but harmless.

However, if someone changes the `data-sort` attribute without updating this conditional, sorting breaks silently. The code is fragile but functionally correct.

#### M-08: `grep -oP` (Perl regex) not available on all systems
**File**: `/home/palantir/.claude/dashboard/sync-dashboard.sh:96, 406`

```bash
infra_version=$(grep -oP 'v[\d.]+' "$CLAUDE_DIR/CLAUDE.md" | head -1)
```

The `-P` flag (Perl-compatible regex) is not available on macOS `grep` (BSD grep) or minimal Linux installations. The dependency check (line 53) verifies `grep` exists but not that it supports `-P`.

Since the target platform is WSL2 Linux (confirmed by env), this works today. But the script header claims no external deps, yet implicitly requires GNU grep.

#### M-09: `body::before` ambient animation causes continuous GPU compositing
**File**: `/home/palantir/.claude/dashboard/template.html:148-165`

```css
body::before {
    width: 200%; height: 200%;
    animation: ambientDrift 30s ease-in-out infinite alternate;
}
```

This creates a pseudo-element that is 200% of viewport in both dimensions and runs a continuous 30s transform animation forever. On low-end machines or when the tab is in the background, this wastes GPU resources. Modern browsers mitigate background tab animations, but the element itself (huge pseudo-element with radial gradients) requires a large compositing layer.

#### M-10: Pipeline `X-cut` skills not shown in pipeline flow
**File**: `/home/palantir/.claude/dashboard/template.html:1880-1892`
**File**: `/home/palantir/.claude/dashboard/sync-dashboard.sh:586-597`

The pipeline parser maps `homeostasis` to `X-cut`:
```python
domain_phase = {
    'homeostasis': 'X-cut',
    'cross-cutting': 'P8'
}
```

But the phases list is `['P0','P1','P2','P3','P4','P5','P6','P7','P8']` -- it does not include `X-cut`. So homeostasis skills (manage-infra, manage-skills, manage-codebase, self-improve) are in `domains['X-cut']` but never rendered in the pipeline flow because `X-cut` is not in the phases array.

**Impact**: 4 out of 35 skills (11%) are invisible in the pipeline visualization.

#### M-11: `h()` helper setAttribute bypass for `className` and `innerHTML`
**File**: `/home/palantir/.claude/dashboard/template.html:1703-1704`

```javascript
else if (k === 'className') el.className = v;
else if (k === 'innerHTML') el.innerHTML = v;
```

Setting `innerHTML` via the `h()` helper bypasses the element creation pattern and is potentially an XSS vector. While the data comes from a locally-generated JSON file (not user input), using `innerHTML` with data from the bash script means any malicious content in MEMORY.md or CLAUDE.md could be injected as HTML.

Currently `innerHTML` is used in one place (line 2041-2049) for SVG inner content, and the data is not user-controlled text. But the pattern is risky.

---

### LOW

#### L-01: `print_summary` calls `jq` 8 times on the same JSON string
**File**: `/home/palantir/.claude/dashboard/sync-dashboard.sh:752-764`

```bash
echo "  Agents:   $(echo "$json" | jq '.agents | length')" >&2
echo "  Skills:   $(echo "$json" | jq '.skills | length')" >&2
# ... 6 more jq invocations
```

Each invocation spawns a new jq process and re-parses the full JSON. This could be collapsed into a single jq call:
```bash
echo "$json" | jq -r '[...] | @text' >&2
```

**Impact**: Performance only -- 8 process spawns instead of 1. Takes ~200ms extra on typical hardware.

#### L-02: SVG `text` element uses CSS `var()` which is not supported in all SVG contexts
**File**: `/home/palantir/.claude/dashboard/template.html:1964`

```javascript
centerLabel.setAttribute('font-family', 'var(--font-sans)');
```

CSS custom properties in SVG presentation attributes are supported in modern browsers but may not work in older browsers or when the SVG is extracted from the DOM context.

#### L-03: Event flow diagram viewBox recalculation ignores hook distribution
**File**: `/home/palantir/.claude/dashboard/template.html:2257-2258`

```javascript
const totalWidth = Math.max(events.length * (eventWidth + 40), 800);
flowSvg.setAttribute('viewBox', '0 0 ' + totalWidth + ' 220');
```

If multiple hooks share an event, the hook boxes at the bottom may overflow horizontally beyond the calculated `totalWidth` because each hook adds `hookWidth + 10` = 150px, but the event calculation only accounts for `eventWidth + 40` = 160px per event.

With the current data (5 events, 5 hooks -- 1:1 mapping), this is fine. But if 3 hooks shared one event, the bottom row would extend 450px while the event slot is only 160px wide.

#### L-04: `numfmt` not available on macOS
**File**: `/home/palantir/.claude/dashboard/sync-dashboard.sh:749`

```bash
output_size=$(numfmt --to=iec "$output_size" 2>/dev/null || echo "${output_size}B")
```

Has a proper fallback (`echo "${output_size}B"`), so this is non-breaking. But the output format differs between platforms.

#### L-05: Donut SVG `totalSkills` denominator guards against zero but shows "1" in center
**File**: `/home/palantir/.claude/dashboard/template.html:1915`

```javascript
const totalSkills = (D.skills || []).length || 1;
```

If there are zero skills, `totalSkills` becomes `1` to avoid division by zero. But the center text displays `1` instead of `0`, which is incorrect.

#### L-06: `escHtml` creates a DOM element per call for escaping
**File**: `/home/palantir/.claude/dashboard/template.html:1714-1718`

```javascript
function escHtml(s) {
    const d = document.createElement('div');
    d.textContent = s || '';
    return d.innerHTML;
}
```

This creates a temporary DOM element each time. For high-frequency calls this is wasteful, but `escHtml` is only called once (header timestamp), so the impact is negligible.

#### L-07: YAML tools array parsing does not handle inline syntax
**File**: `/home/palantir/.claude/dashboard/sync-dashboard.sh:156-166`

```python
if line.startswith('tools:'):
    in_tools = True
    continue
if in_tools:
    if line.startswith('  - '):
        tools.append(line[4:].strip())
```

YAML also supports inline arrays: `tools: [Read, Write, Edit]`. The parser only handles block style (`- item`). All current agent files use block style, so this is latent.

#### L-08: Agent card `maxTurns` radial progress uses hardcoded max of 50
**File**: `/home/palantir/.claude/dashboard/template.html:2009`

```javascript
const pct = Math.min(maxT / 50, 1);
```

Agents have maxTurns of 20-25. With a hardcoded max of 50, the radial progress only fills 40-50%, making every agent look "underutilized". The max should be derived from the actual maximum across all agents.

#### L-09: Search filter matches domain in name query
**File**: `/home/palantir/.claude/dashboard/template.html:2150`

```javascript
const matchName = !query || name.includes(query) || domain.includes(query);
```

Searching for "design" matches both skill names containing "design" AND skills in the "design" domain. This is arguably a feature (broader search), but the search input label says "Search skills" not "Search skills and domains". Could confuse users who see unexpected results.

---

### ADVISORY

#### A-01: `.gitignore` only ignores `index.html` -- generated Python temp files are already cleaned by trap
The trap at line 18 (`trap 'rm -rf "$TMPDIR_DASH"' EXIT`) properly cleans up all temp files. The `.gitignore` correctly only lists `index.html` as the generated output. No issue here.

#### A-02: Template uses CSS nesting (`& .child {}`) which requires modern browsers
CSS nesting is used extensively throughout the stylesheet. This is supported in Chrome 120+, Firefox 117+, Safari 17.2+. Older browsers will silently ignore nested rules, breaking the entire layout. If broad browser support is needed, a build step or PostCSS would be required. For a local developer dashboard, this is acceptable.

#### A-03: No `<meta name="color-scheme" content="dark">` declaration
The dashboard is dark-theme only, but doesn't declare `color-scheme: dark`. This means form controls (inputs, selects) may render with light-theme defaults in some browsers, creating contrast issues. Line 787-790 manually styles them, which mitigates this.

#### A-04: `tabindex="-1"` on inactive tabs is correct ARIA practice
The implementation follows WAI-ARIA Authoring Practices for tabs. Arrow key navigation, Home/End, and focus management are all correct. No issues found.

#### A-05: Event listeners on tab buttons and accordions are never cleaned up
Since this is a single-page dashboard that never re-renders (no SPA routing, no dynamic tab creation), event listeners persist for the lifetime of the page. No memory leak concern in practice.

#### A-06: `parse_pipeline.py` duplicates table parsing logic from `parse_memory.py`
Both scripts parse the skill domains table from MEMORY.md using nearly identical code. If the table format changes, both must be updated. Consider extracting shared parsing logic.

---

## Data Contract Analysis

### Fields produced by `sync-dashboard.sh` vs consumed by `template.html`

| JSON Path | Produced | Consumed | Mismatch |
|-----------|----------|----------|----------|
| `metadata.generated_at` | Yes | Yes | -- |
| `metadata.infra_version` | Yes | Yes | -- |
| `metadata.git_branch` | Yes | Yes | -- |
| `metadata.git_commit` | Yes | Yes | -- |
| `agents[].name` | Yes | Yes | -- |
| `agents[].color` | Yes | Yes | -- |
| `agents[].maxTurns` | Yes | Yes | -- |
| `agents[].model` | Yes | Yes | -- |
| `agents[].tools` | Yes | Yes | -- |
| `agents[].memory` | Yes | Yes | -- |
| `agents[].profile_tag` | Yes | Yes | -- |
| `agents[].source_file` | Yes | No | Unused |
| `skills[].name` | Yes | Yes | -- |
| `skills[].phase` | Yes | Yes | -- |
| `skills[].domain` | Yes | Yes | -- |
| `skills[].user_invocable` | Yes | Yes | -- |
| `skills[].disable_model_invocation` | Yes | No | Unused |
| `skills[].argument_hint` | Yes | No | Unused |
| `skills[].phase_tag` | Yes | No | Unused |
| `skills[].description_preview` | Yes | No | Unused |
| `skills[].body_sections.*` | Yes | Yes | -- |
| `skills[].char_count` | Yes | Yes | Wrong denominator (M-02) |
| `skills[].skill_dir` | Yes | No | Unused |
| `settings.model` | Yes | Yes | -- |
| `settings.teammate_mode` | Yes | Yes | -- |
| `settings.always_thinking` | Yes | Yes | -- |
| `settings.env_var_count` | Yes | Yes | -- |
| `settings.env_vars` | No | Yes (checked) | Missing (M-03) |
| `settings.permission_allow` | No | Yes (checked) | Missing (M-03) |
| `settings.permission_deny` | No | Yes (checked) | Missing (M-03) |
| `settings.enabled_plugins` | Yes (array) | Yes (array) | Incorrect filter (C-01) |
| `settings.hook_event_count` | Yes | Yes | -- |
| `settings.permission_allow_count` | Yes | Yes | -- |
| `settings.permission_deny_count` | Yes | Yes | -- |
| `claude_md.version` | Yes | Yes | -- |
| `claude_md.line_count` | Yes | No | Unused |
| `claude_md.section_count` | Yes | No | Unused |
| `claude_md.tier_table` | Yes | Yes | -- |
| `memory_md.infra_version` | Yes | No | Unused |
| `memory_md.infra_date` | Yes | No | Unused |
| `memory_md.components` | Yes | Yes | -- |
| `memory_md.skill_domains` | Yes | Yes | -- |
| `memory_md.known_bugs` | Yes | Yes | -- |
| `memory_md.session_history` | Yes | Yes | -- |
| `memory_md.session_count` | Yes | No | Unused |
| `pipeline.phases` | Yes | Yes | -- |
| `pipeline.domains` | Yes | Yes | Missing X-cut (M-10) |

**Summary**: 6 fields produced but unused (harmless), 3 fields consumed but not produced (M-03), 2 semantic mismatches (C-01, M-10).

---

## Null/Undefined Safety Analysis

The template uses defensive patterns throughout:
- `(D.agents || [])` -- safe
- `(D.metadata && D.metadata.infra_version) || 'N/A'` -- safe
- `(s.domain || 'unknown')` -- safe
- `agent.color || 'blue'` -- safe

**Gaps**:
- `$('#header-version').textContent = md.infra_version || ''` -- safe (null coalesced)
- `hook.matcher || '\u2014'` -- safe
- `s.body_sections || {}` -- safe

No null reference crashes found in the template. The defensive coding is consistent.

---

## Performance Analysis

**O(n^2) loops**: None found. All skill/agent iteration is O(n). Sorting is O(n log n).

**DOM reflows**: Each `appendChild` call triggers a potential reflow. The render functions append elements one-by-one in a loop. For 35 skills, this means 35 reflows in `renderSkills()`. A DocumentFragment would batch these, but 35 elements is small enough to be imperceptible.

**Memory**: No leaks detected. All IIFEs scope their variables. No circular references. No detached DOM nodes.

**Large inline styles**: None. All styling via CSS classes.

---

## Top 5 Fixes by Impact

| Priority | ID | Summary | Effort |
|----------|----|---------|--------|
| 1 | H-04 | Donut chart closure bug -- all rings animate to same position | 1 line |
| 2 | C-01 | enabledPlugins filter ignores disabled plugins, null crash risk | 1 line |
| 3 | H-06 | `phase-bg-x-cut` CSS class missing -- homeostasis skills unstyled | 1 line |
| 4 | M-03 | Settings env_vars/permissions arrays not produced -- dead UI | 3 lines |
| 5 | H-01 | parse_settings jq null crash on missing keys | 4 lines |

---

*End of audit report.*
