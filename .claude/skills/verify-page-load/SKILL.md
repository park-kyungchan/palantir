---
name: verify-page-load
description: >
  [Verify·UI·Browser] Navigate to a URL via claude-in-chrome MCP, take screenshot,
  read accessibility tree. Returns PASS/FAIL with element count, screenshot ID, and
  page title. Requires dev server running at base_url. Use at P7 for visual page
  render verification. Lead-direct or via browser-verifier agent.
domain: verify
model: sonnet
user-invocable: true
disable-model-invocation: true
---

# Verify Page Load

Navigates to a URL in Chrome and verifies the page renders correctly.

## Input (via $ARGUMENTS or DPS CONTEXT)
- `base_url`: e.g. `http://localhost:3000`
- `route`: e.g. `/`, `/blueprints/1`, `/taxonomy`
- `expected_title_fragment`: substring expected in page title or h1

## Execution Model

- **TRIVIAL**: Lead-direct. Single URL spot-check, no spawn needed.
- **STANDARD**: Spawn 1 browser-verifier (maxTurns: 15) for multi-step verification.
- **COMPLEX**: Not applicable for single-page load verification.

## Phase-Aware Execution

P7 verify phase only. Operates after execution-code PASS.

## Methodology

### DPS for browser-verifier
- **OBJECTIVE**: Navigate to `{base_url}{route}` and verify the page renders with expected elements.
- **CONTEXT**: `base_url`, `route`, `expected_title_fragment`
- **CONSTRAINTS**: maxTurns: 15; do not modify the page; report screenshot_id only (no pixel content)
- **CRITERIA**: element_count ≥ 10, no navigation errors, expected_title_fragment found
- **OUTPUT**: L1 YAML (status/url/screenshot_id/element_count/console_errors) + L2 narrative

### Execution Steps

1. **Tab setup**: `tabs_context_mcp` → get/create MCP tab ID
2. **Navigate**: `navigate` with `url = base_url + route`
3. **Wait**: `computer(action: wait, duration: 2)` for JS hydration
4. **Screenshot**: `computer(action: screenshot)` → capture imageId
5. **Read page**: `read_page(filter: "all", depth: 4)` → get element tree
6. **Console check**: `read_console_messages(pattern: "error|Error", onlyErrors: true)`
7. **Verify**: element_count > 10 AND expected_title_fragment found in page text

## Output
```yaml
status: PASS | FAIL | WARN
url: "{full_url}"
screenshot_id: "{imageId}"
element_count: N
title_found: true | false
console_errors: N
errors: []
```
L2: Screenshot ID, element count, console error count. PASS routes to verify-quality. FAIL routes to execution-code with screenshot and error details.

## Decision Points
- element_count < 5 → FAIL (blank page)
- console_errors > 0 → WARN (not FAIL unless critical)
- Navigation throws error → FAIL immediately

## Quality Gate
- PASS: element_count ≥ 10, no navigation errors, expected_title_fragment found
- WARN: title not found but page loaded
- FAIL: page blank, navigation error, or JS crash in console

## Anti-Patterns
- Do NOT read full accessibility tree (depth > 4 causes token bloat)
- Do NOT keep the tab open after verification completes
- Do NOT report screenshot pixel content — only report screenshot_id

## Transitions

### Receives From
| Source | Data Expected | Format |
|--------|---------------|--------|
| execution-code (PASS) | base_url + route + expected_title_fragment | DPS CONTEXT |
| (User invocation) | Same parameters | Direct |

### Sends To
| Target | Data Produced | Trigger |
|--------|---------------|---------|
| verify-quality | PASS signal + screenshot_id | On PASS |
| execution-code | FAIL + screenshot_id + errors | On FAIL |

> D17 Note: Ch1: `metadata.phase_signals.p7_verify-page-load` · Ch2: `tasks/{team}/p7-verify-page-load.md` · Ch3: micro-signal to Lead · Ch4: P2P to verify-quality on PASS
