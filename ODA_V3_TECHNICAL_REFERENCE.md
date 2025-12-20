# Orion ODA v3.0 Comprehensive Technical Reference
> **Version**: 3.0.0 (Hybrid Semantic OS)
> **Generated Date**: 2025-12-20
> **Target Audience**: Senior Software Architect / Engineering Lead
> **Compliance**: Palantir AIP / Ontology-Driven Architecture (ODA)

---

## 1. Environment & Infrastructure
This system is designed to run in a **Headless Linux Environment** (e.g., Ubuntu via WSL) with a strict separation of concerns between the Agentic Runtime and the Developer Environment.

### 1.1 Host Specifications
- **Operating System**: Linux (Ubuntu 22.04+ recommended)
- **Shell**: Bash (primary interaction layer)
- **Timezone**: Asia/Seoul (KST) preferred for timestamps.

### 1.2 Runtime Environments
The architecture employs a **Polyglot Runtime** Strategy:

#### A. Python Runtime (Core Kernel)
- **Version**: Python 3.12+
- **Virtual Environment**: `/home/palantir/.venv` (Absolute Path Enforcement)
- **Key Dependencies**:
    - `pydantic >= 2.12` (Data Validation & Schema)
    - `httpx` (Async HTTP Client)
    - `sqlite3` (Built-in, required for WAL logic)
    - `pydantic_core` (High-performance validation)

#### B. Node.js Runtime (Tooling/MCP)
- **Version**: Node v24.12.0 (via NVM)
- **Purpose**: Hosts MCP Servers (`tavily`, `sequential-thinking`, `context7`)
- **Execution**: `npx` (No global pollution)

### 1.3 MCP Architecture (Model Context Protocol)
The system leverages MCP to inspect valid tools. Configuration is centrally managed at:
`~/.gemini/antigravity/mcp_config.json`

| Server | Runtime | Type | Purpose |
|:---|:---|:---|:---|
| **github-mcp-server** | Python | Infrastructure | Repo Management, PRs, Issues |
| **tavily** | Node (npx) | Research | Web Search & Deep Retrieval |
| **sequential-thinking** | Node (npx) | Cognition | Chain-of-Thought Enforcement |
| **context7** | Node (npx) | Knowledge | Library Documentation Access |

---

## 2. Ontology-Driven Architecture (ODA) Map
The system is strictly stratified into 5 "Living" Layers using the Palantir Living Object paradigm.

```mermaid
graph TD
    User((User)) -->|Prompt| Router[🧠 Hybrid Router]
    
    subgraph "Phase 2: Intelligence"
        Router -->|Simple| Local[🤖 Local LLM (Ollama)]
        Router -->|Complex| Relay[📨 Relay Queue (SQLite)]
    end
    
    subgraph "Phase 3: Semantic Kernel"
        Relay -->|Poll| Kernel[⚙️ Orion V3 Kernel]
        Kernel -->|Think| Local
        Kernel -->|Write| Ontology[📦 Ontology DB]
    end
    
    subgraph "Phase 4: Governance"
        Ontology -->|Draft| Proposal[📄 Proposal Object]
        Proposal -->|Review| Admin((👩‍💻 Admin))
        Admin -->|Approve| Action[⚡ Semantic Action]
    end
    
    subgraph "Phase 5: Effects"
        Action -->|Commit| Ontology
        Action -->|Trigger| SideEffect[🌐 Webhook/Notify]
    end
```

---

## 3. Codebase Deep Dive (Source Level)

### 3.1 Directory Structure (Optimized)
```bash
/home/palantir/orion-orchestrator-v2/
├── scripts/
│   ├── runtime/           # ⚙️ The Active Kernel
│   │   └── kernel.py      #    Main Event Loop (Asyncio)
│   ├── ontology/          # 🧠 The Brain (Data & Logic)
│   │   ├── client.py      #    CQRS Interface (ObjectService / ActionService)
│   │   ├── actions.py     #    ActionType Definitions & Validation
│   │   ├── side_effects.py#    External Triggers (Webhooks)
│   │   ├── ontology_types.py # Core Pydantic Types
│   │   └── objects/       #    Domain Entities
│   │       ├── core_definitions.py # Task, Agent
│   │       └── proposal.py         # Governance Objects
│   ├── llm/               # 🤖 Intelligence
│   │   ├── ollama_client.py # Async Client & HybridRouter
│   │   └── router.py      #    (Legacy/Proxy)
│   ├── relay/             # 📨 Nervous System
│   │   └── queue.py       #    Persistent SQLite Queue (WAL Mode)
│   └── archive/           # 🏛️ History (V2 Legacy Code e.g. loops)
└── tests/                 # 🧪 Verification
    └── e2e/               #    Production Integration Tests
```

### 3.2 Key Component Implementations

#### A. The V3 Kernel (`scripts/runtime/kernel.py`)
**Role**: The "Cognitive Processor". It doesn't just run code; it reads, thinks, and proposes.
```python
async def _process_task_cognitive(self, task_payload):
    # 1. Plan Generation (Intelligence)
    plan = await self.llm.generate(task_payload['prompt'])
    
    # 2. Ontology Object Creation (Data)
    for step in plan:
        if step['action'] == 'hazardous':
             # 3. Governance Injection (Safety)
             Proposal.create(action_type=step['action'], status='pending')
        else:
             Task.create(title=step['title'])
```

#### B. Relay Queue (`scripts/relay/queue.py`)
**Role**: The "Reliability Layer". Ensures no intent is lost during restart/crash.
- **WAL Mode**: `PRAGMA journal_mode=WAL;` (High Concurrency)
- **Atomic Dequeue**: `UPDATE ... SET status='processing' ... LIMIT 1`

#### C. Semantic Actions (`scripts/ontology/actions.py`)
**Role**: The "Transaction Boundary".
- **SubmissionCriteria**: Pre-flight checks (e.g., `priority=='high'`).
- **Transactional Commit**: Edits are applied only if validation passes.
- **Side Effects**: Executed *after* commit (e.g., Slack Notification).

---

## 4. Operational Workflows

### 4.1 "Boot Sequence" (How to Run)
The entry point has been updated to point to the V3 Kernel.
```bash
# Activate Environment
source /home/palantir/.venv/bin/activate

# Run the Kernel
python scripts/orion
# Output: [Orion V3] Semantic OS Kernel Booting...
```

### 4.2 "Stress Simulation" (How to Verify)
Simulates a User requesting a massive architectural deployment.
```bash
python scripts/simulation/complex_mission.py
```
**Outcome**:
1.  Enqueues "Deploy Checkout Microservice".
2.  Kernel Dequeues & Thinks.
3.  LLM generates Plan (FastAPI, Postgres, Stripe, K8s).
4.  Kernel creates 3 `Task` objects.
5.  Kernel creates 1 `Proposal` object (for "Deploy to K8s" - Hazardous).

### 4.3 "E2E Production Test" (CI/CD)
```bash
python tests/e2e/test_v3_production.py
```
**Coverage**:
1.  Foundation Layer (OSDK Pattern)
2.  Intelligence Layer (Router + Mock LLM)
3.  Relay Layer (Queue Persistence)
4.  Semantic Action Layer (Validation + Side Effects)
5.  Proposal Workflow (Draft -> Approve -> Execute)
6.  Kernel Boot Integrity

---

## 5. Governance & Migration Protocol

### 5.1 Protocol Update (2025-12-20)
`GEMINI.md` has been patched to strictly enforce:
-   **No Ad-Hoc Scripts**: All logic must reside in `scripts/ontology/`.
-   **No Direct Edits**: Filesystem changes must go through `ActionType`.
-   **Proposal Mandate**: High-stakes changes require `Proposal` objects.

### 5.2 Legacy Cleanup
-   **Decommissioned**: `loop.py`, `engine.py`, `intent_router.py` (Old V2).
-   **Archived**: Moved to `scripts/archive/` for audit logs.
-   **Consolidated**: Logic merged into `kernel.py` and `actions.py`.

---

**End of Technical Reference**
*Certified by Antigravity (Gemini 3.0 Pro) - Palantir FDE Agent*
