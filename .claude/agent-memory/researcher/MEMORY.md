# Researcher Agent Memory

## Stable Patterns

### context7 Library ID Resolution (2026-02-19)
- Motion/Framer Motion: use `/websites/motion_dev` (1429 snippets, High rep) NOT `/grx7/framer-motion`
- GSAP: use `/llmstxt/gsap_llms_txt` (1656 snippets, High rep) — most comprehensive
- Lenis: use `/darkroomengineering/lenis` (45 snippets, High rep)
- Locomotive Scroll: use `/websites/scroll_locomotive_ca` (145 snippets) or `/locomotivemtl/locomotive-scroll` (277 snippets)
- BSMNT Scrollytelling: `/basementstudio/scrollytelling` (41 snippets)

### Scroll-Driven Animation Stack (2026-02-19, verified)
Canonical 2025 stack for scrollytelling in React/Next.js:
1. **Lenis** (`lenis/react`) — smooth scroll normalization. `syncTouch: false` default = native touch on mobile
2. **GSAP ScrollTrigger** — pin/scrub for fixed-background overlay pattern. `normalizeScroll(true)` for mobile
3. **GSAP SplitText** — word/char level text splitting for highlight effects. v3.13+ has `autoSplit`, `onSplit()`
4. **Motion `useScroll` + `useTransform`** — React-native scroll linking. v12 uses native ScrollTimeline
5. **CSS `animation-timeline: view()`** — zero-JS progressive enhancement (Chrome 115+, Safari 17.2+ partial)
6. **IntersectionObserver** — universal step-activation fallback

### CSS Scroll-Driven API Notes (2026-02-19)
- `@scroll-timeline` at-rule is DEPRECATED — use `animation-timeline` inline property
- `animation-range: entry 0% entry 60%` — controls when within element's viewport entry animation runs
- `view-timeline-name` + `animation-timeline: --name` = cross-element timeline coordination (Chrome only)
- Safari 17.2+: basic `view()` works, `animation-range` has gaps. Always test on iOS.

### GitHub MCP Auth (2026-02-19)
- GitHub MCP (`mcp__github-mcp-server__*`) returns "Authentication Failed: Bad credentials" — BLOCKED
- Do not retry GitHub search/code tools. Use context7 + resolve-library-id instead for code examples.

### CC Context7 Library IDs for Claude Code (2026-02-20)
- Best source (most snippets): `/websites/code_claude` (1674 snippets, High rep) — official code.claude.com docs
- Secondary: `/anthropics/claude-code` (778 snippets, High rep) — GitHub repo source, good for plugin/hook examples
- Community patterns: `/affaan-m/everything-claude-code` (1845 snippets, High rep) — ECC hackathon winner

### MCPSearch / ToolSearch — CC Behavior (2026-02-20, verified)
- MCPSearch (ToolSearch) is a SYSTEM-LEVEL auto-mechanism, NOT an addable `tools:` item.
- Auto-activates for Sonnet 4+ / Opus 4+ when MCP definitions exceed 10% of context window.
- Haiku does NOT support MCPSearch/ToolSearch — hard CC-native restriction.
- ENABLE_TOOL_SEARCH env var: `auto` (default), `auto:N`, `true`, `false`
- DPS "Call ToolSearch before any MCP tool" = behavioral instruction, not frontmatter config.
- For agents with explicit `tools:` allowlist: MCPSearch may not auto-inject — use general-purpose for MCP-heavy tasks.
- Source: code.claude.com/docs/en/mcp (context7 /websites/code_claude)

### Hook Exit Code 2 — Message Display (2026-02-20, verified)
- Exit code 2 + stderr = standard block mechanism for PreToolUse hooks.
- Stderr content fed back to CLAUDE as context feedback (not directly shown to user).
- Multi-line stderr: YES supported (each print line is part of feedback).
- No documented character limit for stderr hook output.
- Code examples in stderr: YES (plain text; markdown may not render in Claude context).
- Exit 0 + additionalContext JSON = advisory warning (non-blocking alternative).
- Source: ref_hooks.md §5 + context7 /anthropics/claude-code hook examples

### CLAUDE.md Optimization — CC-Native Mechanisms (2026-02-20, verified)
1. `@import` in CLAUDE.md — NOT on-demand. Imports resolved at session start. Structural only, no token savings.
2. `rules/` with `paths` frontmatter — TRUE on-demand (file-pattern triggered). Only native CC frontmatter field for rules.
   - Example: `paths: ["**/*.ts", "**/*.tsx"]` — loads only when working with those files
   - UNVERIFIED: User-level rules (`~/.claude/rules/`) may ignore `paths` — empirical test needed
3. Subdirectory CLAUDE.md — TRUE on-demand (loads when Claude accesses that directory).
4. Skills L2 body — TRUE on-demand (loads only when skill is invoked).
- Official limit: ~500 lines for CLAUDE.md. Bloated CLAUDE.md causes instruction-following degradation.
- Details: `/home/palantir/tmp/claude-md-research.md`
