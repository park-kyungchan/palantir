# Architect Agent Memory

## SKL-002 agent-teams-write-plan Design (2026-02-07)

### Key Patterns Learned
- **LDAP defense → design features**: Challenge responses (Q1-Q3) directly produced 4 compensating mechanisms (AD-3 through AD-5, AD-10) that became core design features
- **4-layer task-context**: GC-v{N} (full) + L2 (inline) + L3 (path reference) + exemplar (format reference) is the pattern for cross-session context continuity
- **Verification Level tags**: READ_VERIFIED > PATTERN_BASED > DESIGN_ONLY — signals confidence to downstream consumers when author cannot execute code
- **AC-0 pattern**: Universal "plan verification step" as first acceptance criterion compensates for any plan-vs-reality drift
- **V6 Code Plausibility**: 6th validation category beyond CH-001's original 5 — needed whenever architect produces code specs without Bash

### Template Design Principles
- CH-001 10-section format generalizes well with parametric fields
- §5 Change Specifications need 3 sub-formats: MODIFY (location+action), CREATE (scaffold+imports), DELETE (justification+impact)
- §6 Test Strategy is conditional — "N/A" with justification for infrastructure-only changes
- §7 V1-V5 from CH-001 + V6 Code Plausibility = standard 6-category validation

### Skill Design Principles
- Follow brainstorming-pipeline pattern: frontmatter, When to Use decision tree, Dynamic Context injection, phase-by-phase workflow, Cross-Cutting, Never list
- DIA delegation: skill specifies tier/intensity, CLAUDE.md [PERMANENT] owns protocol details
- Clean termination: no auto-chaining, user controls next step
- Dual-save: docs/plans/ (permanent) + .agent/teams/ (session L1/L2/L3)

### Risk Patterns
- Single precedent risk → parametric/generalizable template design
- Cross-session agent discontinuity → multi-layer context injection + DIA verification
- Tool limitation gaps → explicit signaling (tags) + downstream verification steps
- Post-gate rework → pipeline ordering as structural defense

## SKL-003 agent-teams-execution-plan Design (2026-02-07)

### Key Patterns Learned
- **LDAP defense → algorithm refinement**: Q1(INTERCONNECTION_MAP) directly refined "independent cluster" definition to require BOTH file non-overlap AND no blockedBy — connected components algorithm
- **3-Layer Defense pattern**: Automated(100%) → Self-report(100%) → Sampling(risk-proportional) is reusable for any trust-but-verify scenario where full verification is impractical
- **Quantitative ALTERNATIVE defense**: Token consumption analysis (Option A ~290K vs Option B ~122K = 58% savings) is the strongest defense form — concrete numbers beat qualitative arguments
- **Cross-boundary escalation reuse**: Existing [CONTEXT-UPDATE]→[ACK-UPDATE] protocol handles new scenarios without new message types — always check existing protocol before inventing new ones
- **Pre-Compact Obligation**: Per-task L1/L2/L3 checkpoint (not only at ~75%) is the correct context pressure strategy for multi-task implementers

### Execution Phase Skill Design Principles
- Adaptive spawn = graph algorithm (connected components), not simple task count heuristic
- Review delegation to Sub-Orchestrator reduces Lead context consumption dramatically
- Gate structure = per-unit + cross-unit 2-level (reusable for any multi-agent gate)
- Fix loop: fixed cap (3) with Lead escalation is simpler and safer than variable cap
- Conditional features (e.g., final whole-project review) should be Lead-judgment, not binary mandatory/optional

### Risk Patterns (new)
- Review manipulation → structural self-interest alignment (persistent agent + downstream rework) > spot-check frequency
- Lead context bottleneck → delegation to Sub-Orchestrator pattern (quantify token savings)
- Cross-boundary interference → immediate BLOCKED + escalation (never attempt cross-boundary fix)
- Dependent task allocation → same-implementer sequential (context continuity > parallelism for dependent tasks)

## CH-006 DIA v4.0 Architecture (2026-02-07)

### Key Patterns Learned
- **Tool availability analysis before design:** Always check which agents have which tools before designing shared resource access patterns. Only implementer/integrator have Edit → discovered during design that 4/6 agents need Lead relay for TEAM-MEMORY.md.
- **Speed Bump positioning:** Hook enforcement = syntax check (file existence, size) not semantic check. Complements LLM-based enforcement (Layer 1-3). Explicitly position as Layer 4 in documentation.
- **Exhaustive fallback tree:** For any protocol with optimized path (delta), define ALL conditions that trigger safety fallback (full injection). 5 independent conditions is better than one catch-all.
- **LDAP defense → architecture insights:** Q1 (FAILURE_MODE) led to section-header-in-old_string rule. Q3 (ALTERNATIVE_DEMAND) validated 3-component approach via concrete comparison table.

### Infrastructure Design Principles
- **Bottom-up migration:** Scripts → Config → Protocol docs → Constitution → Agent instructions. References must exist before referencing files.
- **Backward compatibility default:** All new features check for team context first (team_name empty → exit 0). Solo mode unaffected.
- **File change mapping granularity:** Specify exact §/section + action (ADD/MODIFY/REPLACE) per target file. Enables implementation task decomposition.
- **Hook design:** Always define behavior for ALL exit codes, especially exit 2 blocking vs non-blocking per event type.

### Risk Patterns (new)
- Edit race on shared file → section isolation + header inclusion + non-destructive failure (score 2)
- LLM-generated delta inaccuracy → ACK feedback loop + explicit request fallback (score 6)
- File size bloat → Lead curation discipline + threshold trigger (score 6)
- Lead relay bottleneck → acceptable when primary use case (Phase 6 parallelism) has direct access

## NLP Conversion Architecture (2026-02-08)

### Key Patterns Learned
- **Deduplication before rewriting:** Identifying 6 concepts repeated 3-4x each saved ~22 lines before any NLP conversion. Always deduplicate first — it's a mechanical win before the creative work begins.
- **Semantic preservation checklist:** Enumerate every behavioral requirement (28 for CLAUDE.md, 13 for common-protocol) and verify each survives the conversion. This catches silent drops that natural rewriting can introduce.
- **Authoritative location principle:** Each concept has exactly one canonical location. The file closest to where the behavior is acted upon wins: Lead behavior → CLAUDE.md, shared teammate → common-protocol, role-specific → agent .md.
- **Full rewritten text > guidance notes:** When providing design for implementers, complete rewritten text eliminates interpretation variance. "Write it like this" > "Make it more natural."
- **Phase numbering is anti-pattern for LLMs:** "Phase 1 / Phase 1.5 / Phase 2 / Phase 3" creates false rigidity. Natural section headers ("Before Starting Work", "How to Work") match LLM processing better.

### NLP Conversion Principles
- Protocol markers add cognitive overhead without proven benefit for Opus 4.6
- Role prompting (3-5x performance boost) over rule-based framing
- "Enable success" > "prevent failure" — trust + spot-check scales better than over-enforcement
- Counting questions doesn't guarantee depth — one insightful question > three surface-level ones
- DIA permissiveness trade-off is acceptable when model has low sycophancy (Opus 4.6)

### Design Metrics
- 847 → 525 lines (38% reduction) across 8 files
- 27 protocol markers → 0
- 4 DIAVP tiers → role-appropriate questions
- 5 LDAP levels → 2 levels (Standard/Deep)
- [PERMANENT] 40 lines → §10 Integrity Principles 18 lines

## NLP + PERMANENT Task Integration (L3 v2) (2026-02-08)

### Key Patterns Learned
- **Upgrade design = preserve + extend, not rewrite:** When upgrading an existing L3, identify exactly what changes and what stays. Appendix B (change delta) documents every text change — implementers see the diff, not just the final state.
- **Push→Pull context delivery:** Embedding full context in directives (push) → including Task ID and letting teammates self-serve via TaskGet (pull). Reduces directive size, ensures latest version, enables self-recovery. Core pattern for any shared-state system.
- **Grounding questions in data:** LDAP challenges without reference data = guesswork. Impact Map provides authoritative module dependencies and ripple paths. Both questioner and defender operate on same data — this is the most significant DIA quality improvement.
- **Progressive enrichment:** Impact Map starts empty and grows through phases. Design must handle empty state gracefully (Lead judgment in early phases). Don't block on "map not ready."
- **Self-recovery reduces bottlenecks:** TaskGet is already in every agent's tool list. Letting teammates self-recover (TaskList→TaskGet→reconfirm) removes Lead from critical recovery path without sacrificing DIA integrity.
- **Line budget for capability:** +18 lines (525→543) for PT integration is acceptable. Quantify the trade-off: self-serve context + Impact Map + self-recovery + cross-session persistence > 2 lines/file average cost.

### Architecture Revision Principles
- New decisions (AD-7~AD-9) layer on top of preserved decisions (AD-1~AD-6) — never contradict
- Semantic preservation checklist must be re-run after each upgrade — verify original 28+13 survive + document new behaviors
- Implementation task breakdown must align with upstream design's recommended split (10-task from PT design), not just original L3's split
- Excluded files (task-api-guideline.md in separate terminal) must be explicitly marked in task list
- Change delta appendix is high-value for implementers — shows exactly what moved, not just final state

## SKL-006 Delivery Pipeline Architecture (2026-02-08)

### Key Patterns Learned
- **Terminal phase design differs fundamentally:** No teammates, no TeamCreate/TeamDelete, no understanding verification, no "Next" phase. The skill pattern must be adapted, not copied.
- **User confirmation scaling:** External-facing operations (git, MEMORY persistence) need more confirmation points than internal operations. SKL-006 has 4 vs 0 for internal phases.
- **Dual-input discovery:** Supporting both PT and GC as input sources maintains backward compatibility during migration. "Preferred + fallback" is the right pattern for gradual transitions.
- **RSIL scoping discipline:** "Enables SKL-006 OR quick win OR correctness fix" as inclusion criteria prevents scope creep. 5 in / 8+ deferred from 13+ total candidates.
- **DRY extraction timing:** Extracting shared patterns across 6 files while creating a 7th is high-risk. Better to match the pattern now and extract later in a dedicated sprint.

### Risk Patterns (new)
- External-facing operations (git) need explicit user confirmation — blast radius extends beyond session
- Read-Merge-Write on critical files (MEMORY.md) needs preview step — corruption has cross-session impact
- Session cleanup must classify preserve/delete explicitly — implicit rules lead to accidental deletion

## SKL-006 Detailed Design / Phase 4 (2026-02-08)

### Key Patterns Learned
- **Zero-overlap parallel split:** When workstreams have zero file overlap, 2 implementers is strictly better than 1 — no coordination overhead, pure parallelism. The test: can you draw a complete file list per implementer with no intersection?
- **Hook removal = 3-step migration:** (1) Remove from settings.json, (2) Delete .sh files, (3) Add NL replacement in agent .md. Steps 1+2 can be one task, step 3 depends on it to avoid duplicate enforcement.
- **Triple NL reinforcement:** When replacing mechanical enforcement (hook exit 2) with NL, ensure the instruction appears in 3 independent locations (CLAUDE.md §10 + agent-common-protocol.md + agent .md Constraints). Any one location might be skipped; three makes it reliable.
- **Feasibility re-evaluation heuristic:** For "re-evaluate" items, apply the same scoping criteria as RSIL: "Enables the primary deliverable OR quick win OR correctness fix." Everything else defers.
- **Read-every-file discipline:** Reading all 8 hook .sh files, all 6 agent .md files, and all existing MEMORY.md files before writing specs catches assumptions. Example: discovered only 2 (not 5) MEMORY.md templates needed because 4 already existed.

### Implementation Plan Design Principles
- §5 Change Specifications must cover DELETE operations (not just MODIFY and CREATE) — CH-001 exemplar didn't have deletions
- VL (Verification Level) tags: VL-1 (trivial/self-evident), VL-2 (moderate/needs-review), VL-3 (complex/needs-testing) — signals effort to downstream validators
- §6 Interface Contracts should document the enforcement migration explicitly (before: hook exit 2, after: NL instruction) — this is the highest-risk interface change
- §9 Commit Strategy: for mixed new+modified+deleted files, use `git add` for new/modified and `git rm` for deleted — don't rely on `git add -A`

## RSIL System Architecture (2026-02-09)

### Key Patterns Learned
- **Breadth vs depth = separate skills:** When a system needs both lightweight scanning (auto-invoked, budget-constrained) and deep analysis (user-invoked, thorough), merging into one skill creates branching complexity without benefit. Two independent skills sharing a stable foundation is superior.
- **Adaptive data source per work type:** When the same analysis framework applies to different work types (pipeline/skill/direct edit), keep the escalation logic constant but swap data sources at Tier 0 classification. Git diff substitutes for gate records in non-pipeline work.
- **Probing Q → design refinement:** Q1 (Three-Tier degradation) produced the per-work-type tables that became G-0/G-1 core architecture. Q2 (BREAK escalation) resolved the D-3 vs findings-only tension. Q3 (tracker consistency) validated the namespacing strategy. All 3 questions improved the design.
- **Constraint tension resolution:** When two design inputs appear contradictory (D-3 "immediate application" vs constraint "findings-only output"), resolve by reinterpreting the earlier decision in light of the later constraint. "Immediate" ≠ "automatic" — it means "propose immediately upon discovery."
- **Embedded copy > shared reference for stable content:** When shared content is small (~85L), stable (changes only on Lens additions), and critical (skills must be self-contained), embedded identical copies eliminate external dependency. The maintenance cost of updating 2 files simultaneously is lower than the fragility risk of a shared reference.

### Multi-Skill System Design Principles
- When to Use tree for auto-invoked skills must include explicit SKIP criteria (not just invoke criteria)
- Findings-only output is the safe default for auto-invoked skills — user is present, approval is fast
- ID namespacing (prefix per skill) eliminates collision in shared data stores without locks
- Section isolation in shared files (each writer owns a section) enables sequential multi-writer safety
- Shared agent memory between complementary skills accelerates cumulative learning — patterns are universal

### Risk Patterns (new)
- Tier 0 misclassification → multiple independent signals + comprehensive fallback (Type A)
- NL discipline non-compliance → CLAUDE.md instruction + staleness tracking in agent memory (no hook needed)
- Noise from auto-invoked reviews → tier escalation gates + AD-15 filter + acceptance rate self-correction

## RSIL System Detailed Design / Phase 4 (2026-02-09)

### Key Patterns Learned
- **Interface consistency by construction:** When two parallel implementers share an interface (agent memory schema), defining BOTH sides in the SAME §5 document using identical terminology from a single architecture source guarantees consistency without runtime coordination. The plan IS the coordination mechanism.
- **Verbatim text > file reference for shared content:** Providing Foundation text verbatim in §5 (not "copy from rsil-review lines X-Y") eliminates dependency on the other implementer's file state. One-time cost at plan writing; permanent safety at implementation.
- **VL-3 scoping discipline:** In a ~26-spec plan, only 1 spec (A7: G-1 Tiered Reading) was VL-3. Shell commands are VL-1 (verbatim from architecture). Classification logic is VL-2 (decision tree provided). Tight VL-3 scoping reduces implementation risk and V6 verification burden.
- **L3 internal discrepancy detection:** L3 §3.3 said head -30, L3 §7 said head -50. Architecture discrepancies are normal in 1000+ line designs — the plan author must identify the authoritative section and resolve. Document the resolution (PD-2) for traceability.
- **V6 items as first-3-runs monitoring:** V6 Code Plausibility items can't be resolved by the architect. Rather than leaving them as abstract risks, recommending "first 3 runs manual monitoring" gives testers a concrete verification plan.

### Implementation Plan Design Principles (new)
- For multi-implementer plans: define shared interfaces once in §5 and reference from both sides
- §6 Integration Points should be specific enough to be executable as grep + diff commands
- §10 Phase 5 targets should challenge ASSUMPTIONS (with evidence + risk-if-wrong), not just design choices
- Agent memory seed data should be DERIVABLE from existing data stores — no manual reconstruction
