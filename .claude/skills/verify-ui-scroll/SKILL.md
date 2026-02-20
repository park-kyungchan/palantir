---
name: verify-ui-scroll
description: >
  [Verify·UI·Browser] Scroll through a page in increments, take screenshots at each
  position to verify scroll-triggered animations (RevealOnScroll, StaggerChildren,
  progress bar). Reports which sections appeared on scroll. Requires dev server.
  SRP: scroll behavior and entrance animations only.
model: sonnet
user-invocable: true
disable-model-invocation: true
---

# Verify UI Scroll Animations

Scrolls through a page and verifies scroll-triggered entrance animations fire.

## Input
- `base_url`: e.g. `http://localhost:3000`
- `route`: e.g. `/`
- `scroll_steps`: number of scroll increments (default: 5)

## Execution Model

- **TRIVIAL**: Lead-direct. Single page scroll verification.
- **STANDARD**: Spawn 1 browser-verifier (maxTurns: 15) for multi-section pages.
- **COMPLEX**: Spawn 2 browser-verifier agents for pages with 10+ animated sections.

## Phase-Aware Execution

P7 verify phase only. Operates after execution-code PASS.

## Methodology

### DPS for browser-verifier
- **OBJECTIVE**: Scroll through `{base_url}{route}` in increments and verify animations activate.
- **CONTEXT**: `base_url`, `route`, `scroll_increments` (default: 3), `expected_animation_classes[]`
- **CONSTRAINTS**: maxTurns: 15; take screenshot at each scroll position; do not interact with elements
- **CRITERIA**: Each scroll position shows visible animation state change; no JS errors detected
- **OUTPUT**: L1 YAML (status/scroll_positions_checked/animations_triggered/console_errors) + L2 narrative

### Execution Steps

1. **Navigate**: `navigate(url = base_url + route)`
2. **Wait**: `computer(action: wait, duration: 2)` for initial render
3. **Screenshot at top**: `computer(action: screenshot)` → frame 0
4. **Scroll loop** (repeat `scroll_steps` times):
   a. `computer(action: scroll, coordinate: [760, 400], scroll_direction: down, scroll_amount: 5)`
   b. `computer(action: wait, duration: 0.8)` for animation settle
   c. `computer(action: screenshot)` → capture frame
5. **Scroll progress bar check**: `javascript_tool("document.querySelector('.scroll-progress-bar')?.getBoundingClientRect()")`
6. **Read page after full scroll**: `read_page(filter: "all", depth: 3)`
- **Console check**: `read_console_messages(onlyErrors: true)` — catch animation JS errors

## Output
```yaml
status: PASS | FAIL | WARN
route: "{route}"
frames_captured: N
scroll_progress_bar_found: true | false
sections_visible_after_scroll: N
screenshot_ids: []
```
L2: Scroll positions tested, animation triggers count, screenshot IDs. PASS routes to verify-quality. FAIL routes to execution-code with scroll position and error details.

## Decision Points
- scroll_progress_bar not found → WARN
- Page does not scroll (height = viewport) → WARN (page may be short)
- Sections still opacity:0 after scrolling → FAIL

## Quality Gate
- PASS: sections_visible_after_scroll > frames_captured/2 (majority of sections revealed)
- WARN: progress bar not found, or page too short to scroll
- FAIL: all sections remain hidden after scrolling

## Anti-Patterns
- Do NOT scroll horizontally unless explicitly testing horizontal scroll
- Do NOT take more than 8 screenshots (memory limit)
- Capture screenshot_ids only, do not describe pixel content

## Transitions

### Receives From
| Source | Data Expected | Format |
|--------|---------------|--------|
| execution-code (PASS) | base_url + route + scroll config | DPS CONTEXT |
| (User invocation) | Same parameters | Direct |

### Sends To
| Target | Data Produced | Trigger |
|--------|---------------|---------|
| verify-quality | PASS signal + scroll_positions_checked | On PASS |
| execution-code | FAIL + screenshot_ids + animation_errors | On FAIL |

> D17 Note: Ch2: `tasks/{work_dir}/p7-verify-ui-scroll.md` · Ch3: micro-signal to Lead
