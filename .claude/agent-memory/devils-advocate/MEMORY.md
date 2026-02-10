# Devil's Advocate Agent Memory

## Key Lessons

### 1. Always independently count lines (2026-02-08)
Design documents often claim line counts based on "content lines" (excluding blanks) but
actual file line counts include blank lines. Always verify by counting the raw text within
code fences. Architecture-design-v2 claimed 136 lines for CLAUDE.md but actual markdown
was ~167 lines including formatting blanks.

### 2. Preservation checklists can be incomplete (2026-02-08)
When a design claims "N/N behaviors preserved," the checklist itself may omit behaviors.
Cross-reference EVERY line of the current file against the new file — don't trust the
design's own checklist. Found 4 lost behaviors in a "28/28 preserved" claim.

### 3. Search for specific v5.1 terms that should appear in v6.0 (2026-02-08)
Effective approach: Grep for specific terms from the current version in the proposed version.
"Max 3 iterations," "APPROVE / ITERATE / ABORT," "6000 lines," "Spawn Matrix," "Delegate Mode" —
all missing. This is faster and more reliable than reading line by line.

### 4. Dependency graphs vs execution round tables (2026-02-08)
Implementation task breakdowns often have a dependency graph AND a round table that contradict.
Always check both: does the graph's edge direction match the round parallelism claims?
Found T4 ∥ T11 in round table but T4 → T11 in dependency graph.

### 5. Upstream design requirements as a separate verification pass (2026-02-08)
When a design says it "absolutely" reflects an upstream requirement document, create a
section-by-section cross-reference table. Found Operational Constraints from
permanent-tasks-design §1 (max 2 concurrent, no token conservation) missing entirely
from the CLAUDE.md v6.0 rewrite.

### 6. Semantic mapping for section merges (2026-02-09)
When a plan merges N items into M items (N>M), create an explicit mapping table:
old item → new item. Count actual items, not "lines" (headers/blanks inflate counts).
Found architecture claimed "21→11" but actual was 20→11 (off by 1 due to counting headers).
The mapping itself was complete — all 20 original semantics preserved in 11 new items.

### 7. Seed data derivability (2026-02-09)
When a plan claims data is "derived from" a source, verify the derivation is mechanical.
RSIL agent memory seed claimed per-lens statistics derived from tracker, but tracker had
no per-lens tags. Statistics were actually manual estimates. Not a blocking issue when
the data is self-correcting, but should be labeled as estimated.

### 8. Chicken-and-egg in NL enforcement (2026-02-09)
NL-based triggers have a fundamental detection gap: if the trigger fails to fire, the
detection mechanism (which lives inside the triggered skill) also fails. Look for
cross-system staleness detection — in RSIL, /rsil-review's dynamic context provides
cross-skill visibility into /rsil-global staleness.

### 9. Empirical SDK verification is the strongest evidence (2026-02-09)
When a plan assumes SDK API surface (method exists, type signature, error types), don't
rely on documentation alone. Install the SDK locally and test:
- `inspect.signature()` for method signatures
- `asyncio.iscoroutinefunction()` to distinguish sync/async
- `type(e).__mro__` for exception hierarchies
- Live API calls with valid/invalid inputs for error behavior
In COW v2.0 validation: verified google-genai 1.62.0 sync API, PIL Image support in
contents Union type, models.get() method, and ClientError exception hierarchy — all
via direct Python introspection. This resolved 6/7 assumptions definitively.

### 10. Code specs with inline class definitions create dual-definition risk (2026-02-09)
When a plan's code spec defines a class in Module A but a note says "actually define in
Module B and import", the code spec itself becomes misleading. An implementer following
the code literally creates a duplicate. Always check: does the code spec match the
architectural decision about canonical location? In COW v2.0: ModelUnavailableError
defined in both §5.2 (gemini_loop.py) and §5.4 (config/models.py) with a note resolving
to config/models.py as canonical — but the §5.2 code was never updated.

### 11. String-scanning exception messages is fragile pattern (2026-02-09)
Plans that detect error types via `if "404" in str(e).lower()` are fragile. Modern SDKs
(google-genai, httpx, etc.) have typed exception hierarchies. Always check:
- What specific exception type is raised? (ClientError, APIError, etc.)
- Does it have structured error codes? (.code, .status, etc.)
- Would string-scanning false-positive on content text containing the signal word?
Recommend: catch by type first, string-scan as fallback only.

### 12. Verify environment variables actually exist before trusting plan assumptions (2026-02-10)
When a plan assumes an environment variable is available (e.g., `$CLAUDE_SESSION_ID`),
verify against official documentation AND check for open feature requests. Found that
`CLAUDE_SESSION_ID` is NOT exposed as an env var — only available in JSON stdin. This
made an entire SubagentStart session registry block dead code. Always check:
- Official docs "Environment Variables" section
- GitHub issues for feature requests about that variable
- The existing hook scripts for precedent usage

### 13. Section headers vary across files even in "identical" templates (2026-02-10)
When a plan says "insert into {section name} in all N files," verify that ALL N files
actually have that section with that exact name. Found 1 of 7 skills had no
"Cross-Cutting Requirements" section at all, and another used a shortened header.
Grep for the section header across all target files BEFORE trusting the plan's claim.

### 14. Check real-world API field names against multiple source authority levels (2026-02-10)
Documentation ecosystem can have inconsistencies. The official Claude Code hooks docs
used `tool_response` while a third-party TypeScript SDK wrapper used `tool_result`.
Always establish a priority order: (1) official docs example JSON > (2) official docs
prose > (3) SDK TypeScript interfaces > (4) community docs. The plan should include
first-run verification (AC-0) for any assumed API field names.
