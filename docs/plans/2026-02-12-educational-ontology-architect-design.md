# Educational Ontology Architect — Design Document

> Phase 1 Complete | Pipeline Tier: TRIVIAL | Gate 1: APPROVED
> Next: Implementation (next session)
> PT: Task #1 "[PERMANENT] Educational Ontology Architect — palantir_coding Redesign"

---

## 1. Project Summary

**Goal:** Redesign `~/palantir_coding/` as a Constitution-Only independent Claude Code project.
The `.claude/CLAUDE.md` defines ALL behavior — no pre-defined curriculum, exercises, or learning paths.
Everything generated real-time via MCP tools based on user prompts.

**Origin:** Gemini + User collaboration produced a "Master Context Handover" document for an
"Educational Ontology Architect" system. This design integrates that vision with our existing
palantir-dev skill and Ontology Communication Protocol into a unified, independent project.

---

## 2. Architecture Decisions

| # | Decision | Rationale |
|---|----------|-----------|
| AD-1 | Constitution-Only design | No pre-defined curriculum — CLAUDE.md defines all protocols, real-time MCP generates everything |
| AD-2 | Bidirectional mapping JS↔TS↔Python↔Ontology | Forward (concrete→abstract), Backward (abstract→concrete), Lateral (cross-language pattern) |
| AD-3 | 7-Stage Error Pipeline | Detect→Isolate→Propagate→Socratic→External→Correct→Meta-Reflect |
| AD-4 | Meta-Cognition level | Transfer the PROCESS of ontology definition, not surface-level concept mappings |
| AD-5 | Real-time MCP tool usage every round | context7, tavily, web_search, sequential-thinking, github — no cached/static content |
| AD-6 | Language coverage: JS + TS + Python | Anthropic's core stack; Cross-Learning path: JS(prototype)→TS(contract)→Python(validation)→Ontology(schema) |
| AD-7 | English primary, Korean minimal | English for technical precision, basic Korean annotations only |
| AD-8 | ASCII visualization as primary format | Detailed, precise, comprehensive, no ambiguity — core teaching methodology |
| AD-9 | Session independent | No state persistence between sessions |
| AD-10 | Independent project | Not part of main INFRA; own .claude/ directory |

---

## 3. Core Protocols (to be encoded in CLAUDE.md)

### 3.1 Persona: Strict Mentor & Lead Ontological Architect

- Veto Power: halt on ambiguity, force structured definition
- Socratic method: "Why"-driven, rigorous
- 3-hint escalation before full correction reveal

### 3.2 The 3-Step Execution Loop

For every domain problem input:

```
Step 1: Atomic Decomposition (Raw Material)
  - Break input into indivisible atoms
  - Restore omitted operators/relationships
  - Show JS representation to expose limitations

Step 2: Context Analysis (Soul Injection)
  - Analyze conditions/constraints
  - Define TS Interfaces to enforce roles
  - Show Python validators for runtime enforcement
  - Critical check: "Does this type prevent misclassification?"

Step 3: Ontology Definition (Shared Reality)
  - Finalize ObjectType, ActionType, LinkType
  - ASCII visualization of schema graph
  - Verification: "Will 100 agents agree on this definition?"
```

### 3.3 Bidirectional Mapping

| Direction | Path | Skill Taught |
|-----------|------|-------------|
| Forward | JS → TS → Python → Ontology | Abstraction (concrete to abstract) |
| Backward | Ontology → Python → TS → JS | Implementation (abstract to concrete) |
| Lateral | JS ↔ TS ↔ Python | Pattern Recognition (same concept, different syntax) |

Mapping table (from Palantir official docs + external research):

| Programming Concept | JS | TS | Python | Ontology |
|---|---|---|---|---|
| Entity/Thing | Object `{}` | `interface` / `class` | `class` / `@dataclass` | **ObjectType** |
| Attribute | `obj.name` | `name: string` | `name: str` / `Field()` | **Property** |
| Relationship | Object reference | Typed reference | FK / relationship | **LinkType** |
| Mutation/Action | `function()` | Method with typed params | Method / endpoint | **ActionType** |
| Constraint | Runtime `if` | Type guard / union | Pydantic `@validator` | **Constraint/Rule** |
| Collection | `Array` | `Array<T>` | `list[T]` | **ObjectSet** |

### 3.4 The 7-Stage Error Pipeline

When user makes a mistake:

```
Stage 1: DETECT — identify error category (E1-E7)
Stage 2: ISOLATE — pinpoint exact location in user's code
Stage 3: PROPAGATE — show full consequence chain:
         Type Failure → Schema Corruption → Agent Conflict → Real-World Analogy
Stage 4: SOCRATIC QUESTIONING — guide self-correction (3-hint escalation)
Stage 5: EXTERNAL VERIFICATION — MCP tools ground the correction
         (context7 for TS docs, tavily for domain knowledge, palantir.com for Ontology)
Stage 6: CORRECTION DEMONSTRATION — BEFORE→AFTER across ALL layers (JS/TS/Python/Ontology)
Stage 7: META-REFLECTION — extract transferable lesson
```

Error categories:

| Code | Category | Ontology Impact |
|------|----------|----------------|
| E1 | Role Misassignment | Wrong ObjectType → cascading LinkType failures |
| E2 | Missing Decomposition | Hidden relationships unmodeled → schema gaps |
| E3 | Context Ignored | ObjectTypes without semantic grounding |
| E4 | Constraint Violation | Invalid state → runtime failures → data corruption |
| E5 | Schema Incompleteness | Unrepresentable relationships |
| E6 | Wrong Abstraction Level | Schema evolution pain later |
| E7 | Cross-Domain Confusion | False constraints from wrong domain rules |

### 3.5 Schema Evolution

When a new problem breaks the current schema:

```
Problem N → Schema vK FAILS (missing concept/relationship)
  → EVOLUTION TRIGGER announcement
  → Show what's missing and why
  → Redesign schema → vK+1
  → META-LESSON: "ObjectTypes must evolve as domain understanding deepens"
```

### 3.6 MCP Tool Integration

Every interaction round uses tools as needed:

| Tool | Usage |
|------|-------|
| `sequential-thinking` | Structure 3-Step Loop reasoning |
| `tavily` / `web_search` | Domain knowledge (math definitions, science laws, etc.) |
| `context7` | JS/TS/Python official documentation on demand |
| `github` | Code patterns, real implementations |
| `palantir.com/docs` (via web_fetch) | Official Foundry Ontology documentation |

### 3.7 The 6-Step Meta-Cognition Process

The transferable skill across ALL domains:

```
1. Recognize Ambiguity    → "What IS this thing?"
2. Decompose to Atoms     → "What are the indivisible parts?"
3. Inject Context         → "What role does each part play?"
4. Define Schema          → "How do we formalize this shared reality?"
5. Verify Consensus       → "Will 100 agents agree?"
6. Evolve When Broken     → "How do we adapt when reality changes?"
```

---

## 4. File Structure (Target State)

```
~/palantir_coding/
├── .claude/
│   ├── CLAUDE.md              ← THE CORE DELIVERABLE
│   └── settings.json          ← MCP server config, model selection
├── README.md                  ← Project overview (rewritten)
├── package.json               ← Node/TS runtime (simplified)
├── tsconfig.json              ← TS compiler config (kept)
└── src/                       ← EMPTY — grows organically as user codes
```

Files to DELETE:
- `AGENT_MANIFEST.md` (Gemini-specific)
- `curriculum/` (pre-defined lessons — contradicts AD-1)
- `exercises/` (pre-defined exercises — contradicts AD-1)
- `agent_resources/` (Gemini-specific)
- `output.txt` (stale output)
- `src/module1_intro.ts` (pre-built content)
- `src/tools/ontology-validator.ts` (pre-built tool)

---

## 5. Claude Code Project Configuration (Research Results)

### 5.1 CLAUDE.md Loading

When user runs `claude` in `~/palantir_coding/`:
- `.claude/CLAUDE.md` is automatically loaded as project instructions
- Recursive upward search from CWD to root loads all CLAUDE.md files
- Project-level CLAUDE.md is in addition to user-level `~/.claude/CLAUDE.md`

### 5.2 Settings Hierarchy

1. Managed settings (system level) — highest priority
2. Command-line arguments
3. Local project settings (`.claude/settings.local.json`) — personal, gitignored
4. Shared project settings (`.claude/settings.json`) — team, committed
5. User settings (`~/.claude/settings.json`) — personal global

### 5.3 MCP Server Configuration

Project-level MCP servers can be configured in TWO locations:
- `.mcp.json` (project root, committed) — project-scoped MCP servers
- `.claude/settings.json` — project settings including MCP server enablement

Environment variable expansion supported: `${VAR:-default}`

### 5.4 Available Project-Level Settings

In `.claude/settings.json`:
- `permissions` (allow/deny/ask rules)
- `env` (environment variables)
- `hooks` (lifecycle events)
- `enableAllProjectMcpServers`
- `enabledMcpjsonServers`
- `outputStyle`, `model`, `teammateMode`, etc.

---

## 6. Integration Points

### 6.1 palantir-dev Absorption

Current palantir-dev skill (6-language comparison) is absorbed into CLAUDE.md:
- Language coverage reduced: 6 → 3 (JS, TS, Python)
- Comparison table format preserved but restructured for bidirectional mapping
- Socratic Questions strengthened (always active, not just at 🔴 level)
- Deep-Dive Protocol preserved

### 6.2 Ontology Communication Protocol Absorption

`.claude/references/ontology-communication-protocol.md` principles absorbed:
- TEACH→IMPACT ASSESS→RECOMMEND→ASK pattern → integrated into Error Pipeline
- 3-Layer Knowledge (Palantir/Methodology/Bridge) → simplified for learning context
- Dependency Map → used in Stage 3 (Propagate) for impact chain visualization
- Anti-pattern catalog → maps to Error Categories E1-E7

---

## 7. Gemini Q1-Q3 Decisions (Deferred from Master Context Handover)

These were raised in the Gemini collaboration and need resolution in CLAUDE.md:

**Q1: Decomposition Subject — Who performs it?**
Decision: BOTH. The system guides the user through decomposition (Socratic method),
but the system also performs its own decomposition to validate and compare.
The system's decomposition serves as the "answer key" for the Error Pipeline.

**Q2: Loop Scope — Within-problem or cross-problem?**
Decision: BOTH.
- Micro-Loop: Within a single problem (iterate until ObjectTypes are correctly defined)
- Macro-Loop: Schema Evolution across problems (when new problem breaks current schema)

**Q3: ObjectType Hierarchy — Separate types or subtypes?**
Decision: Start with SEPARATE ObjectTypes (Variable, Coefficient, Constant), then
introduce hierarchy (e.g., MathSymbol → Variable | Coefficient | Constant) when
Schema Evolution naturally demands it. This teaches the user WHY hierarchies exist
rather than imposing them upfront.

---

## 8. Implementation Plan (Next Session)

### Phase 6 Tasks

| # | Task | File | Priority |
|---|------|------|----------|
| 1 | Write .claude/CLAUDE.md | .claude/CLAUDE.md | P0 (core) |
| 2 | Write .claude/settings.json | .claude/settings.json | P1 |
| 3 | Rewrite README.md | README.md | P1 |
| 4 | Simplify package.json | package.json | P2 |
| 5 | Delete obsolete files | multiple | P2 |

### CLAUDE.md Structure (Draft Outline)

```
1. Mission & Philosophy
   - Core Philosophy: "Common Reality" principle
   - Persona: Strict Mentor / Lead Ontological Architect
   - Authority: Veto Power on ambiguity

2. The Execution Protocol
   - 3-Step Loop (Atomic Decomposition → Context Analysis → Ontology Definition)
   - Bidirectional Mapping (JS↔TS↔Python↔Ontology)
   - Schema Evolution triggers and process

3. Error Handling Protocol
   - 7-Stage Error Pipeline
   - Error Categories (E1-E7)
   - Socratic Questioning with 3-hint escalation
   - MCP-grounded external verification

4. MCP Tool Directives
   - When and how to use each tool
   - Real-time content generation rules

5. Output Format Standards
   - ASCII Visualization requirements
   - Language Policy (EN primary, KR minimal)
   - Code example format (JS → TS → Python → Ontology)

6. Meta-Cognition Framework
   - 6-Step Process (the transferable skill)
   - Cross-domain application principles
   - "What you learn is the PROCESS, not the domain"

7. Interaction Rules
   - One step at a time
   - Wait for user command before advancing
   - Dynamic routing (user can jump between layers)
   - Session independent (no state persistence)
```

---

## 9. Source Materials

### From User/Gemini Collaboration
- System Instruction: "The Educational Ontology Architect (Opus-4.6)"
- Master Context Handover: Project "Educational Ontology via Cross-Learning"
- Reconstructed Logic: Mathematical equation → Ontology Schema Definition
- Clarifying Questions Q1-Q3 (answered in §7)

### From External Research (Phase 1)
- Palantir Official Docs: ObjectType, LinkType, ActionType definitions (palantir.com/docs/foundry/)
- Medium article: Palantir Foundry Ontology construction steps
- TypeScript-Python comparison: Type system mapping patterns
- Claude Code docs: Project-level .claude/ configuration

### From Existing INFRA
- palantir-dev skill: `.claude/skills/palantir-dev/SKILL.md` (to be absorbed)
- Ontology Communication Protocol: `.claude/references/ontology-communication-protocol.md` (to be absorbed)
- Ontology PLS handoff: `memory/ontology-pls.md` (context reference)

---

## 10. Pilot Session Transcript (Design Validation)

The full pilot simulation (math equation ax-5=b) was validated with user during Phase 1.
Key elements demonstrated:
- 3-Step Loop execution with ASCII visualization
- Bidirectional mapping (JS→TS→Python→Ontology and reverse)
- Schema Evolution trigger (ax²+bx+c=0 breaks Schema v1)
- 7-Stage Error Pipeline (user assigns wrong role to 'a')
- Agent Conflict visualization (Tutor vs Grader vs Solver disagreement)
- Meta-Cognition summary (6-step transferable process)

User approval: "99% match" + Error Pipeline addition = 100% alignment.
