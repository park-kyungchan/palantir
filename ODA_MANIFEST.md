# ORION ODA SPECIFICATION V2.1 (MACHINE-READABLE)

> **PURPOSE**: This document is a complete technical specification of the "Orion ODA" system at `/home/palantir/`. It is designed for consumption by Autonomous Agents (Gemini, Claude, Web Agents) to perform Deep Research, Code Analysis, and Architecture Refactoring.
> **CONTEXT**: The system simulates Palantir AIP/Foundry architecture using Python/SQLAlchemy/Pydantic.
> **LAST_UPDATED**: 2025-12-13

---

## 1. SYSTEM TOPOLOGY

### 1.1 Core Components
- **Kernel**: `Gemini 3.0 Pro` (Orchestrator)
- **Executors**: `Claude Opus 4.5` (Architect), `GPT-5.2` (Mechanic)
- **Runtime**: Python 3.12 (Virtual Environment: `/home/palantir/.venv`)
- **Persistence**: SQLite (`objects.db`) via SQLAlchemy + Pydantic Serialization
- **Communication**: File-Based Handoffs (`.agent/handoffs/pending/`)

### 1.2 The "Self-Driving" Cycle (The Loop)
The system operates on a strictly defined Lifecycle Map (ODA Phase Map):
1.  **Phase 1: Planning (Gemini)**
    - **Input**: User Intent.
    - **Output**: `Plan` Object (DB) + `Handoff Artifact` (MD File).
    - **Mechanism**: `scripts/ontology/handoff.py` injects Phase 2 Signal.
2.  **Phase 2: Execution (Claude/Codex)**
    - **Signal**: `# ODA_PHASE: 2. Execution (Relay)` in Handoff file.
    - **Action**: Agent reads file, executes instructions (Terminal/File Edits).
3.  **Phase 3: Reporting (Claude/Codex)**
    - **Signal**: "RELAY PROTOCOL (MANDATORY)" section in Handoff template.
    - **Action**: Agent generates and runs `scripts/ontology/relays/result_job_{id}.py`.
    - **Output**: `JobResult` Object committed to DB.
4.  **Phase 4: Consolidation (Gemini)**
    - **Signal**: User invokes `/05_consolidate` or reports job done.
    - **Action**: Gemini reads `JobResult`, updates `Memory`, mutates `Plan`.

---

## 2. ONTOLOGY SCHEMA DEFINITIONS (The Data Layer)

### 2.1 Core Object (`scripts/ontology/core.py`)
```python
class OrionObject(BaseModel):
    id: str = Field(simulation_of="UUIDv7")
    version: int = Field(simulation_of="Optimistic Locking")
    created_at: datetime
    updated_at: datetime
```

### 2.2 Planning Objects (`scripts/ontology/plan.py`, `job.py`)
```python
class Plan(OrionObject):
    objective: str
    jobs: List[Job]
    ontology_impact: Optional[str]

class Job(OrionObject):
    action_name: str
    action_args: Dict
    role: Literal["Architect", "Mechanic"]
    input_context: List[str]
```

### 2.3 Result Objects (`scripts/ontology/schemas/result.py`)
```python
class JobResult(OrionObject):
    job_id: str
    status: Literal["SUCCESS", "FAILURE", "BLOCKED"]
    output_artifacts: List[Artifact]
    metrics: Dict[str, Any]

class Artifact(BaseModel):
    path: str
    checksum: str
```

### 2.4 Memory Objects (`scripts/ontology/schemas/memory.py`)
```python
class OrionInsight(OrionObject):
    content: InsightContent(summary, domain, tags)
    provenance: InsightProvenance

class OrionPattern(OrionObject):
    structure: PatternStructure(trigger, steps, anti_patterns)
```

---

## 3. LOGIC & INTERFACE (The Implementation)

### 3.1 Object Manager (`scripts/ontology/manager.py`)
- **Role**: Gatekeeper / Phonograph.
- **Pattern**: Singleton with `SessionLocal`.
- **Methods**: `save(obj)`, `get(id)`, `query(type)`.
- **AIP Alignment**: Currently mimics "Direct DB Access". Needs migration to "OSDK Client" pattern.

### 3.2 Handoff Interface (`scripts/ontology/handoff.py`)
- **Role**: Signal Injector.
- **Mechanism**: Template Injection.
- **Key Logic**:
  ```python
  # ODA Phase Signal Injection
  content = f"# ODA_PHASE: 2. Execution (Relay)\n{content}"
  ```

---

## 4. AIP ALIGNMENT GAP ANALYSIS (For Deep Research)

### 4.1 Concept Mapping
| Orion ODA Component | Palantir AIP Equivalent | Status |
| :--- | :--- | :--- |
| `ObjectManager` | **Ontology SDK (OSDK)** | ⚠️ Divergent (Migrate to `client.ontology.objects`) |
| `relays/result_*.py` | **AIP Logic Functions** | ⚠️ Divergent (Migrate to `@function` decorators) |
| `JobResult` | **Action Side-Effect** | ✅ Conceptual Match (But needs explicit `ActionType`) |
| `memory.py` | **Object Constraints/Links** | ⚠️ Partial (Need formal `LinkType`) |
| `GEMINI.md` | **Agent Logic Core** | ✅ Aligned (Instruction Tuning) |

### 4.2 Code Level Mismatch
- **Dependency**: Missing `foundry-platform-sdk` patterns.
- **Structure**: Current code handles persistence (`manager.save`). AIP handles persistence via Action submission (`action.apply`).
- **Authorization**: Current code has implicit sudo. AIP has Granular ACLs (not implemented).

---

## 5. CODEBASE MAP (Target for Analysis)
```
/home/palantir/orion-orchestrator-v2/
├── .agent/
│   ├── handoffs/
│   │   ├── templates/ (Protocol definitions)
│   │   └── pending/ (Active packets)
├── scripts/
│   ├── ontology/
│   │   ├── schemas/ (Pydantic Models)
│   │   ├── relays/ (Execution Logs)
│   │   ├── manager.py (DB Interface)
│   │   ├── core.py (Base Class)
│   │   ├── handoff.py (Signal Generator)
│   └── action_registry.py (Tool Definitions)
└── objects.db (SQLite Storage)
```

---

## 6. RESEARCH DIRECTIVE: API-LESS CONSTRAINT (CRITICAL)

> **INSTRUCTION FOR READING AGENT**: The User operates in a strict **"No API Key"** environment. All LLM interactions are performed via **Subscription-based Web Interfaces** (ChatGPT Plus, Claude Pro).

### 6.1 The Constraint
- **FORBIDDEN**: Using `openai`, `anthropic`, or `google.generativeai` Python libraries requiring API Keys.
- **REQUIRED**: Workflows must rely on **Manual Relay** (User Copy-Paste) or **Browser Automation**.
- **TOLERANCE**: Time latency is acceptable. Accuracy and Zero-Cost (beyond subscription) are the priorities.

### 6.2 Research Prompt
Please research and propose architectural solutions for:
1.  **"Headless" ODA Interface**: Can we use libraries like `selenium`, `playwright`, or `puppeteer` to automate the text injection into the Web Interface?
2.  **Local LLM Integration**: Can we offload simple ODA logic (e.g. JSON validation) to free local models (Ollama/Llama3) to reduce the Relay burden?
3.  **Reverse Engineering AIP Agents**: How does Palantir AIP handle "Offline" or "Air-gapped" deployments? Are there patterns (e.g., queuing actions) we can mimic?
4.  **Optimized Relay Protocol**: How can we minimize the User's friction (e.g., generating "One-Click Copy" artifacts) within this constraint?
