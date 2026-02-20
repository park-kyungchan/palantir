---
name: verify-ui-interactive
description: >
  [Verify·UI·Browser] Find all buttons, links, and interactive elements on a page.
  Click each, verify state changes (text, class, URL). Reports element count tested
  and any failures. Requires dev server. Use at P7 to verify interactive components.
  SRP: interactive element testing only. Pair with verify-page-load for render check.
model: sonnet
user-invocable: true
disable-model-invocation: true
---

# Verify UI Interactive Elements

Tests all interactive elements on a page: buttons, links, toggles.

## Input
- `base_url`: e.g. `http://localhost:3000`
- `route`: e.g. `/blueprints/1`
- `skip_navigation`: true | false (skip nav links to avoid page changes)

## Execution Model

- **TRIVIAL**: Lead-direct. Single URL spot-check, no spawn needed.
- **STANDARD**: Spawn 1 browser-verifier (maxTurns: 15) for multi-step verification.
- **COMPLEX**: Spawn 2 browser-verifier agents for pages with 20+ interactive elements.

## Phase-Aware Execution

P7 verify phase only. Operates after execution-code PASS.

## Methodology

### DPS for browser-verifier
- **OBJECTIVE**: Find all interactive elements on `{base_url}{route}` and verify each produces expected state changes on click.
- **CONTEXT**: `base_url`, `route`, optional `element_filter` description
- **CONSTRAINTS**: maxTurns: 15; do not trigger browser dialogs/alerts; report element count + state changes only
- **CRITERIA**: All interactive elements found; each click produces observable state change; no JS errors
- **OUTPUT**: L1 YAML (status/element_count/tested_count/failed_elements[]) + L2 narrative

### Execution Steps

1. **Navigate**: `navigate(url = base_url + route)`
2. **Wait**: `computer(action: wait, duration: 2)`
3. **Find interactive**: `find("button or clickable element")`
4. **For each element** (max 10, skip nav if `skip_navigation: true`):
   a. `computer(action: screenshot)` before click
   b. `computer(action: left_click, ref)` on element
   c. `computer(action: wait, duration: 0.5)`
   d. `computer(action: screenshot)` after click
   e. Check if page changed unexpectedly (DOM diff via read_page)
5. **Console errors**: `read_console_messages(onlyErrors: true)`

## Output
```yaml
status: PASS | FAIL | WARN
route: "{route}"
elements_found: N
elements_tested: N
elements_failed: []
console_errors: N
```
L2: Element count tested, state change results per element. PASS routes to verify-quality. FAIL routes to execution-code with failed element list.

## Decision Points
- Element click causes JS error → FAIL for that element
- Toggle button does not change state → WARN
- Page navigates away unexpectedly → record as navigation_triggered

## Quality Gate
- PASS: elements_tested ≥ 1, elements_failed = 0
- WARN: some elements non-interactive but no errors
- FAIL: JS errors on click, or elements_found = 0

## Anti-Patterns
- Do NOT test more than 10 elements per invocation (token budget)
- Do NOT click destructive buttons (delete, submit with real data)
- Do NOT follow external links

## Transitions

### Receives From
| Source | Data Expected | Format |
|--------|---------------|--------|
| execution-code (PASS) | base_url + route to test | DPS CONTEXT |
| (User invocation) | Same parameters | Direct |

### Sends To
| Target | Data Produced | Trigger |
|--------|---------------|---------|
| verify-quality | PASS signal + tested_count | On PASS |
| execution-code | FAIL + failed_elements[] + screenshots | On FAIL |

> D17 Note: Ch2: `tasks/{work_dir}/p7-verify-ui-interactive.md` · Ch3: micro-signal to Lead
