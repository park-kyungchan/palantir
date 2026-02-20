# Grep Context Engineering

## 3-Step Pattern (MANDATORY)
1. `files_with_matches` first — discover which files match (cheapest)
2. `content` + `head_limit` — read actual lines only when needed (MUST have head_limit, enforced by hook)
3. `count` — check result scale before reading content

## Parameter Rules
- ALWAYS provide `path` — scoped search only (enforced by hook)
- ALWAYS provide `head_limit` when using `output_mode: "content"` (enforced by hook)
- Use `glob` or `type` to filter file types — reduces noise
- Prefer `files_with_matches` (default) over `content` for discovery

## Anti-Patterns
- Grep without path → BLOCKED (full workspace scan)
- content mode without head_limit → BLOCKED (unlimited results)
- Using Grep when you know the exact file → use Read instead
- Multiple broad Greps when one specific Grep + Read suffices
