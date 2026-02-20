---
name: verify-navigation-routing
description: >
  [Verify·UI·Browser] Click each nav link in the application navbar, verify the
  correct route loads (URL matches, page renders). Tests all navigation links
  end-to-end. Requires dev server. SRP: navigation routing correctness only.
  Use at P7 after implementation to confirm all routes are accessible.
model: sonnet
user-invocable: true
disable-model-invocation: true
---

# Verify Navigation Routing

Tests that all navigation links route to the correct pages.

## Input
- `base_url`: e.g. `http://localhost:3000`
- `routes_to_test`: list of `{ href, expected_title_fragment }` objects

## Execution Model

- **TRIVIAL**: Lead-direct. 1-3 routes spot-check.
- **STANDARD**: Spawn 1 browser-verifier (maxTurns: 15) for full nav link suite (4-8 routes).
- **COMPLEX**: Spawn 2 browser-verifier agents for apps with 10+ routes or nested navigation.

## Phase-Aware Execution

P7 verify phase only. Operates after execution-code PASS.

## Methodology

### DPS for browser-verifier
- **OBJECTIVE**: Click each nav link in `{base_url}` and verify the correct route loads.
- **CONTEXT**: `base_url`, `routes_to_test: [{href, expected_title_fragment}]` — e.g. `[{ href: "/", expected: "Home" }, { href: "/about", expected: "About" }]`. Pass actual routes via DPS CONTEXT.
- **CONSTRAINTS**: maxTurns: 15; test each route independently; do not cache navigation state
- **CRITERIA**: Each href click changes URL to expected path; page renders with expected title fragment
- **OUTPUT**: L1 YAML (status/routes_tested/routes_passed/routes_failed[]) + L2 narrative

### Execution Steps

1. **Start at base_url**: `navigate(url = base_url)`
2. **Wait**: `computer(action: wait, duration: 2)`
3. **For each route**:
   a. `navigate(url = base_url + href)`
   b. `computer(action: wait, duration: 1.5)`
   c. `get_page_text` → check contains expected_title_fragment
   d. `javascript_tool("window.location.pathname")` → verify current URL
   e. `read_console_messages(onlyErrors: true)` → check for crashes
4. **Compile results**

## Output
```yaml
status: PASS | FAIL | WARN
routes_tested: N
routes_passed: N
routes_failed:
  - { href: "/example", error: "404 or blank page" }
console_errors_total: N
```

L2: Routes tested count, per-route PASS/FAIL with URL and title evidence. PASS routes to verify-quality. FAIL routes to execution-code with failed route list.

## Decision Points
- Route returns 404 → FAIL for that route
- Title fragment not found → WARN (may be data-dependent)
- Console crash on navigation → FAIL

## Quality Gate
- PASS: routes_passed = routes_tested, 0 console errors
- WARN: 1-2 title mismatches (data loading)
- FAIL: any 404, blank page, or JS crash

## Anti-Patterns
- Do NOT click nav buttons (use direct navigate for reliability)
- Do NOT test deep dynamic routes (e.g. /blueprints/999) — use known IDs or skip
- Maximum 10 routes per invocation

## Transitions

### Receives From
| Source | Data Expected | Format |
|--------|---------------|--------|
| execution-code (PASS) | base_url + routes_to_test list | DPS CONTEXT |
| (User invocation) | Same parameters | Direct |

### Sends To
| Target | Data Produced | Trigger |
|--------|---------------|---------|
| verify-quality | PASS signal + routes_tested count | On PASS |
| execution-code | FAIL + failed_routes[] + screenshots | On FAIL |

> D17 Note: Ch2: `tasks/{work_dir}/p7-verify-navigation-routing.md` · Ch3: micro-signal to Lead
