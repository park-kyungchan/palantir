# Orion ODA (Ontology-Driven Architecture)

> **Version:** 4.0.0
> **License:** MIT
> **Namespace:** `lib.oda`

## Overview

ODA (Ontology-Driven Architecture) is a Python framework for building schema-first, action-oriented systems with full audit trails. It provides a Palantir Foundry-inspired architecture for managing complex data workflows.

## Package Structure

```
lib/oda/
├── __init__.py              # Package entry point
├── ontology/                # Core ontology types and actions
├── semantic/                # Embedding and vector store layer
├── transaction/             # ACID transaction management
├── pai/                     # Personal AI infrastructure
├── claude/                  # Claude Code integration
├── agent/                   # Agent orchestration
├── memory/                  # Memory management
├── data/                    # Data sources and pipelines
├── tools/                   # External tool integrations
├── cognitive/               # Adaptive tutoring engine
├── lib/                     # Pure Python algorithms
├── maintenance/             # Database maintenance scripts
├── layer/                   # Subagent orchestration
├── observe/                 # Observability and events
├── aip_logic/               # Logic function framework
├── osdk/                    # OSDK-style query and actions
├── infrastructure/          # Runtime infrastructure
├── planning/                # Task decomposition
├── voice/                   # Voice synthesis
├── llm/                     # LLM adapters
├── api/                     # API layer
├── mcp/                     # MCP protocol
├── runtime/                 # Runtime components
├── relay/                   # Cross-module relay
├── simulation/              # Simulation and testing
└── consolidation/           # Memory consolidation
```

## Core Modules

### ontology
Core ontology types, actions, storage, and governance.

```python
from lib.oda.ontology import Plan, Job, Action, Trace, Event

# Create a plan
plan = Plan(name="Feature Implementation", description="...")
```

**Key Classes:**
- `Plan` - High-level execution plan
- `Job` - Unit of work within a plan
- `Action` - Atomic operation with side effects
- `Trace` - Execution trace with status
- `Event` - Event logging

**Submodules:**
- `actions/` - Registered ActionTypes
- `storage/` - SQLite/async database layer
- `validators/` - Input validation
- `governance/` - Access control and proposals
- `evidence/` - Evidence collection
- `protocols/` - Execution protocols

### semantic
Vector embedding and semantic search infrastructure.

```python
from lib.oda.semantic import (
    EmbeddingConfig,
    VectorStore,
    VectorIndexManager,
)
from lib.oda.semantic.providers import LocalEmbeddingProvider
from lib.oda.semantic.stores import SQLiteVSSStore

# Configure embeddings
config = EmbeddingConfig(model="all-MiniLM-L6-v2", dimension=384)
provider = LocalEmbeddingProvider(config)

# Vector storage
store = SQLiteVSSStore(db_path="vectors.db", dimension=384)
```

**Key Classes:**
- `EmbeddingProvider` - Abstract embedding interface
- `VectorStore` - Abstract vector storage
- `VectorIndexManager` - Index management
- `EmbeddingCache` - Caching layer

### transaction
ACID-compliant transaction management with branching.

```python
from lib.oda.transaction import (
    TransactionManager,
    BranchManager,
    transactional,
    IsolationLevel,
)

@transactional(isolation=IsolationLevel.SERIALIZABLE)
async def update_objects(ctx):
    # Atomic operations here
    pass
```

**Key Classes:**
- `TransactionManager` - Transaction orchestration
- `BranchManager` - Git-like branching
- `MergeStrategy` - Three-way merge
- `ConflictResolver` - Conflict handling
- `Checkpoint` - Immutable snapshots
- `DiffEngine` - Checkpoint comparison

### pai
Personal AI Infrastructure for agent composition.

```python
from lib.oda.pai.algorithm import EffortLevel, ISCTable
from lib.oda.pai.traits import ExpertiseType, AgentCompositionFactory
from lib.oda.pai.hooks import HookEventType, SecurityValidator
from lib.oda.pai.skills import SkillRouter, SkillDefinition
```

**Submodules:**
- `algorithm/` - Universal Algorithm, ISC, EffortLevels
- `traits/` - 28-dimension agent composition
- `hooks/` - Event-driven hooks
- `skills/` - Skill routing and workflows
- `tools/` - Tool definitions
- `blocks/` - Agent building blocks
- `evaluation/` - Agent evaluation

### claude
Claude Code integration handlers.

```python
from lib.oda.claude.handlers import (
    audit_stage_a_handler,
    planning_stage_b_handler,
    governance_check_handler,
)
```

### agent
Agent orchestration framework.

```python
from lib.oda.agent import AgentExecutor, ExecutionProtocol, TaskResult

executor = AgentExecutor()
result = await executor.execute(protocol)
```

### data
Data source abstraction and pipelines.

```python
from lib.oda.data import DataSource, CSVDataSource, DataPipeline

source = CSVDataSource("data.csv")
pipeline = DataPipeline([source])
```

### tools
External tool integrations (SPS, YouTube).

```python
from lib.oda.tools import PromptManager, Transcriber, YouTubeWorkflow
```

### cognitive
Adaptive tutoring with ZPD scoping.

```python
from lib.oda.cognitive import (
    ComplexityScore,
    LearnerState,
    KnowledgeComponent,
    ScopedLesson,
)
```

### lib
Pure Python algorithm implementations.

```python
from lib.oda.lib import FPTree, pagerank, extract_summary
```

### memory
Memory management with semantic integration.

```python
from lib.oda.memory import MemoryManager, SemanticMemory, recall
```

### maintenance
Database maintenance utilities.

```python
from lib.oda.maintenance import rebuild_database
# WARNING: Destructive operation
await rebuild_database()
```

## Usage Patterns

### 1. Basic Import

```python
from lib.oda import __version__
from lib.oda.ontology import Plan, Action
```

### 2. Action Registration

```python
from lib.oda.ontology.actions import ActionRegistry

@ActionRegistry.register
class MyCustomAction:
    api_name = "my_action"
    hazardous = False

    async def execute(self, params):
        # Implementation
        pass
```

### 3. Protocol Execution

```python
from lib.oda.ontology.protocols import ThreeStageProtocol

protocol = ThreeStageProtocol(
    stage_a="SCAN",
    stage_b="TRACE",
    stage_c="VERIFY",
)
result = await protocol.execute(context)
```

### 4. Evidence Collection

```python
from lib.oda.ontology.evidence import auto_evidence, EvidenceCollector

@auto_evidence
async def my_function():
    # Evidence automatically collected
    pass
```

## Dependencies

Core:
- Python 3.12+
- pydantic >= 2.0
- sqlalchemy[asyncio] >= 2.0
- aiosqlite

Optional:
- sentence-transformers (local embeddings)
- chromadb (vector storage)
- openai (OpenAI embeddings)

## Configuration

Environment variables:
- `ORION_DB_PATH` - Database file path
- `ORION_LOG_LEVEL` - Logging level (DEBUG, INFO, etc.)
- `ORION_DB_INIT_MODE` - Database init mode (async, sync)

## Architecture Principles

1. **Schema-First**: ObjectTypes are canonical; mutations follow schema
2. **Action-Only**: State changes ONLY through registered Actions
3. **Audit-First**: All operations logged with evidence
4. **Zero-Trust**: Verify files/imports before ANY mutation

## Version History

- **4.0.0** - ODA architecture with Foundry patterns
- **3.0.0** - Semantic layer integration
- **2.0.0** - Transaction framework
- **1.0.0** - Initial PAI migration
