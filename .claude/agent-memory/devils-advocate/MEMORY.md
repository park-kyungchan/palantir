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
