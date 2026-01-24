# ODA E2E Test & Enhancement Master Prompt
## For GPT-5.2-Codex (xhigh Reasoning Mode)

> **Version:** 1.0.0 | **Created:** 2026-01-18
> **Target Model:** gpt-5.2-codex with xhigh reasoning effort
> **Estimated Duration:** 8-12 hours autonomous execution
> **Goal:** Palantir AIP/Foundry 수준 이상의 ODA 고도화

---

## 🎯 Mission Statement

You are a **Senior Software Architect** executing comprehensive E2E tests and architectural enhancements for the ODA (Ontology-Driven Architecture) system. Your goal is to elevate ODA to match or exceed **Palantir AIP/Foundry** production architecture standards.

**Core Directive:** Work autonomously for extended periods. Once given direction, proactively gather context, plan, implement, test, and refine without waiting for additional prompts at each step.

---

## 📋 Table of Contents

1. [Project Context](#1-project-context)
2. [Palantir AIP/Foundry Reference Architecture](#2-palantir-aipfoundry-reference-architecture)
3. [Current ODA Architecture](#3-current-oda-architecture)
4. [Phase 1: Individual Workflow E2E Tests](#4-phase-1-individual-workflow-e2e-tests)
5. [Phase 2: Cross-Workflow Integration Tests](#5-phase-2-cross-workflow-integration-tests)
6. [Phase 3: Full System E2E Tests](#6-phase-3-full-system-e2e-tests)
7. [Phase 4: Architecture Enhancement](#7-phase-4-architecture-enhancement)
8. [Phase 5: Palantir Parity Validation](#8-phase-5-palantir-parity-validation)
9. [Execution Protocol](#9-execution-protocol)
10. [Output Requirements](#10-output-requirements)

---

## 1. Project Context

### 1.1 Workspace Structure

```
/home/palantir/park-kyungchan/palantir/
├── lib/oda/                    # Core ODA Library
│   ├── ontology/              # Ontology Core (25 modules)
│   │   ├── actions/           # Action Types
│   │   ├── bridge/            # Integration Bridge
│   │   ├── decorators/        # Python Decorators
│   │   ├── evidence/          # Evidence Collection
│   │   ├── governance/        # Governance Rules
│   │   ├── hooks/             # Event Hooks
│   │   ├── objects/           # Object Types
│   │   ├── protocols/         # 3-Stage Protocol
│   │   ├── schemas/           # Schema Definitions
│   │   ├── storage/           # Storage Layer
│   │   ├── tracking/          # Progress Tracking
│   │   ├── types/             # Type Definitions
│   │   ├── validators/        # Validation Logic
│   │   └── versioning/        # Version Control
│   ├── pai/                   # Personal AI Infrastructure
│   │   ├── algorithm/         # Effort Levels, ISC
│   │   ├── hooks/             # Event Hooks
│   │   ├── skills/            # Skill Routing
│   │   ├── tools/             # Tool Registry
│   │   └── traits/            # 28-Trait System
│   ├── planning/              # Planning System
│   │   ├── context_budget_manager.py
│   │   ├── output_layer_manager.py
│   │   ├── l2_synthesizer.py
│   │   ├── prompt_templates.py
│   │   └── task_decomposer.py
│   ├── claude/                # Claude Integration
│   ├── llm/                   # LLM Adapters
│   ├── mcp/                   # MCP Server
│   ├── semantic/              # Semantic Memory
│   └── ...
├── .agent/                    # Agent State
├── .claude/                   # Claude Code Config
├── tests/oda/                 # Existing Tests
└── Ontology-Definition/       # Ontology Definition Library
```

### 1.2 ODA Core Principles

```yaml
SCHEMA-FIRST:   ObjectTypes are canonical; mutations follow schema
ACTION-ONLY:    State changes ONLY through registered Actions
AUDIT-FIRST:    All operations logged with evidence
ZERO-TRUST:     Verify files/imports before ANY mutation
3-STAGE:        SCAN → TRACE → VERIFY protocol
```

### 1.3 Current Test Status

- **Test Count:** ~400 tests
- **Passing:** ~379 (95%)
- **Coverage:** ~66%
- **Target:** 95% pass rate, 85% coverage

---

## 2. Palantir AIP/Foundry Reference Architecture

### 2.1 Core Components (Production Standard)

| Component | Palantir Implementation | ODA Equivalent | Gap |
|-----------|------------------------|----------------|-----|
| **Object Types** | Schema-defined entities with properties, backed by datasets | `lib/oda/ontology/objects/` | ✅ Exists |
| **Link Types** | Relationship definitions between Object Types | `ontology/types/` | ⚠️ Partial |
| **Action Types** | CRUD + custom operations with validation | `ontology/actions/` | ⚠️ Partial |
| **Interfaces** | Polymorphic type abstraction | Missing | ❌ Gap |
| **OMS (Metadata Service)** | Central schema registry | `ontology/schemas/` | ⚠️ Partial |
| **OSS (Object Set Service)** | Query/search/aggregate service | Missing | ❌ Gap |
| **Object Data Funnel** | Write orchestration & indexing | `ontology/storage/` | ⚠️ Partial |
| **OSDK** | Type-safe SDK generation | `Ontology-Definition/` | ✅ Exists |

### 2.2 Palantir Ontology Microservices Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                      PALANTIR FOUNDRY ARCHITECTURE                  │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌──────────────┐   ┌──────────────┐   ┌──────────────┐           │
│  │   Clients    │   │   Clients    │   │   Clients    │           │
│  │ (OSDK/API)   │   │ (Workshop)   │   │ (AIP Logic)  │           │
│  └──────┬───────┘   └──────┬───────┘   └──────┬───────┘           │
│         │                  │                  │                    │
│         └──────────────────┼──────────────────┘                    │
│                            ▼                                       │
│  ┌─────────────────────────────────────────────────────────────┐  │
│  │                    API Gateway Layer                         │  │
│  │         (Authentication, Rate Limiting, Routing)             │  │
│  └─────────────────────────────────────────────────────────────┘  │
│                            │                                       │
│         ┌──────────────────┼──────────────────┐                   │
│         ▼                  ▼                  ▼                   │
│  ┌──────────────┐   ┌──────────────┐   ┌──────────────┐          │
│  │     OMS      │   │     OSS      │   │   Funnel     │          │
│  │  (Metadata)  │   │  (Query)     │   │  (Write)     │          │
│  └──────┬───────┘   └──────┬───────┘   └──────┬───────┘          │
│         │                  │                  │                   │
│         └──────────────────┼──────────────────┘                   │
│                            ▼                                       │
│  ┌─────────────────────────────────────────────────────────────┐  │
│  │              Object Storage V2 (Canonical Store)             │  │
│  └─────────────────────────────────────────────────────────────┘  │
│                            │                                       │
│  ┌─────────────────────────────────────────────────────────────┐  │
│  │                    Datasets / Datasources                    │  │
│  └─────────────────────────────────────────────────────────────┘  │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### 2.3 Critical Palantir Features for ODA Parity

| Feature | Description | Priority |
|---------|-------------|----------|
| **Interface Types** | Polymorphic abstraction for Object Types | P0 |
| **Object Set Service** | Unified query/filter/aggregate API | P0 |
| **Link Type Registry** | Formal relationship definitions | P1 |
| **Action Side Effects** | Declarative side effect system | P1 |
| **Derived Properties** | Computed properties from Functions | P2 |
| **Dynamic Security** | Row-level security on Objects | P2 |

---

## 3. Current ODA Architecture

### 3.1 Module Inventory (Ordered by Dependency)

#### Tier 1: Core Foundation (No dependencies)

| Module | Path | Purpose | Tests Exist |
|--------|------|---------|-------------|
| `types` | `ontology/types/` | Base type definitions | ⚠️ Partial |
| `schemas` | `ontology/schemas/` | Schema validation | ⚠️ Partial |
| `decorators` | `ontology/decorators/` | Python decorators | ❌ Missing |

#### Tier 2: Data Layer (Depends on Tier 1)

| Module | Path | Purpose | Tests Exist |
|--------|------|---------|-------------|
| `objects` | `ontology/objects/` | ObjectType definitions | ✅ Yes |
| `storage` | `ontology/storage/` | Persistence layer | ⚠️ Partial |
| `validators` | `ontology/validators/` | Validation logic | ⚠️ Partial |

#### Tier 3: Operations Layer (Depends on Tier 2)

| Module | Path | Purpose | Tests Exist |
|--------|------|---------|-------------|
| `actions` | `ontology/actions/` | ActionType system | ⚠️ Partial |
| `hooks` | `ontology/hooks/` | Event hooks | ⚠️ Partial |
| `evidence` | `ontology/evidence/` | Evidence collection | ⚠️ Partial |
| `governance` | `ontology/governance/` | Governance rules | ⚠️ Partial |

#### Tier 4: Orchestration Layer (Depends on Tier 3)

| Module | Path | Purpose | Tests Exist |
|--------|------|---------|-------------|
| `protocols` | `ontology/protocols/` | 3-Stage Protocol | ⚠️ Partial |
| `bridge` | `ontology/bridge/` | Integration bridge | ❌ Missing |
| `tracking` | `ontology/tracking/` | Progress tracking | ⚠️ Partial |

#### Tier 5: Planning System

| Module | Path | Purpose | Tests Exist |
|--------|------|---------|-------------|
| `task_decomposer` | `planning/` | Task splitting | ⚠️ Partial |
| `context_budget_manager` | `planning/` | Context management | ⚠️ Partial |
| `output_layer_manager` | `planning/` | L1/L2/L3 outputs | ⚠️ Partial |
| `l2_synthesizer` | `planning/` | Multi-source synthesis | ⚠️ Partial |

#### Tier 6: PAI (Personal AI Infrastructure)

| Module | Path | Purpose | Tests Exist |
|--------|------|---------|-------------|
| `algorithm` | `pai/algorithm/` | EffortLevel, ISC | ⚠️ Partial |
| `skills` | `pai/skills/` | Skill routing | ⚠️ Partial |
| `traits` | `pai/traits/` | 28-trait system | ⚠️ Partial |
| `hooks` | `pai/hooks/` | PAI event hooks | ⚠️ Partial |

#### Tier 7: Integration Layer

| Module | Path | Purpose | Tests Exist |
|--------|------|---------|-------------|
| `claude` | `claude/` | Claude integration | ⚠️ Partial |
| `llm` | `llm/` | LLM adapters | ⚠️ Partial |
| `mcp` | `mcp/` | MCP server | ⚠️ Partial |
| `semantic` | `semantic/` | Semantic memory | ⚠️ Partial |

---

## 4. Phase 1: Individual Workflow E2E Tests

### 4.1 Execution Order (Dependency-Based)

Execute in this exact order. **DO NOT proceed to next workflow until current passes 100%.**

```
Phase 1.1: Tier 1 - Core Foundation
  → 1.1.1: ontology/types E2E
  → 1.1.2: ontology/schemas E2E
  → 1.1.3: ontology/decorators E2E

Phase 1.2: Tier 2 - Data Layer
  → 1.2.1: ontology/objects E2E
  → 1.2.2: ontology/storage E2E
  → 1.2.3: ontology/validators E2E

Phase 1.3: Tier 3 - Operations Layer
  → 1.3.1: ontology/actions E2E
  → 1.3.2: ontology/hooks E2E
  → 1.3.3: ontology/evidence E2E
  → 1.3.4: ontology/governance E2E

Phase 1.4: Tier 4 - Orchestration Layer
  → 1.4.1: ontology/protocols E2E
  → 1.4.2: ontology/bridge E2E
  → 1.4.3: ontology/tracking E2E

Phase 1.5: Tier 5 - Planning System
  → 1.5.1: planning/task_decomposer E2E
  → 1.5.2: planning/context_budget_manager E2E
  → 1.5.3: planning/output_layer_manager E2E
  → 1.5.4: planning/l2_synthesizer E2E

Phase 1.6: Tier 6 - PAI
  → 1.6.1: pai/algorithm E2E
  → 1.6.2: pai/skills E2E
  → 1.6.3: pai/traits E2E
  → 1.6.4: pai/hooks E2E

Phase 1.7: Tier 7 - Integration
  → 1.7.1: claude/handlers E2E
  → 1.7.2: llm/adapters E2E
  → 1.7.3: mcp E2E
  → 1.7.4: semantic E2E
```

### 4.2 Per-Workflow E2E Test Template

For EACH workflow, create test file: `tests/oda/e2e/test_{module_name}_e2e.py`

```python
"""
E2E Tests for {Module Name}

Workflow: {Workflow Description}
Tier: {Tier Number}
Dependencies: {List of dependent modules}
"""
import pytest
from pathlib import Path

# Mark all tests in this module as E2E
pytestmark = [pytest.mark.e2e, pytest.mark.{tier_name}]


class Test{ModuleName}E2E:
    """End-to-end tests for {module_name} workflow."""

    # ========== Setup & Teardown ==========

    @pytest.fixture(autouse=True)
    def setup_workflow(self, tmp_path):
        """Setup isolated test environment."""
        # 1. Create temporary workspace
        # 2. Initialize required dependencies
        # 3. Setup mock data if needed
        yield
        # Cleanup

    # ========== Happy Path Tests ==========

    def test_happy_path_basic_flow(self):
        """Test: Basic workflow execution succeeds."""
        # Given: Valid inputs
        # When: Execute workflow
        # Then: Expected outputs
        pass

    def test_happy_path_with_options(self):
        """Test: Workflow with optional parameters."""
        pass

    # ========== Error Handling Tests ==========

    def test_error_invalid_input(self):
        """Test: Invalid input raises appropriate error."""
        pass

    def test_error_missing_dependency(self):
        """Test: Missing dependency is handled gracefully."""
        pass

    def test_error_recovery(self):
        """Test: System recovers from transient errors."""
        pass

    # ========== Edge Cases ==========

    def test_edge_empty_input(self):
        """Test: Empty input handling."""
        pass

    def test_edge_maximum_input(self):
        """Test: Maximum size input handling."""
        pass

    def test_edge_concurrent_access(self):
        """Test: Concurrent access handling."""
        pass

    # ========== Integration Points ==========

    def test_integration_with_{dependency}(self):
        """Test: Integration with {dependency} module."""
        pass

    # ========== Performance ==========

    @pytest.mark.performance
    def test_performance_baseline(self):
        """Test: Performance meets baseline requirements."""
        pass
```

### 4.3 Test Categories Per Module

| Category | Description | Count Target |
|----------|-------------|--------------|
| Happy Path | Normal operation flows | 3-5 tests |
| Error Handling | Error conditions | 3-5 tests |
| Edge Cases | Boundary conditions | 2-3 tests |
| Integration | Cross-module interactions | 2-3 tests |
| Performance | Performance baselines | 1-2 tests |
| **Total per module** | | **12-18 tests** |

---

## 5. Phase 2: Cross-Workflow Integration Tests

### 5.1 Integration Test Matrix

After ALL Phase 1 tests pass, create integration tests for these critical paths:

#### 5.1.1 Data Flow Integration

| Test | Modules | Description |
|------|---------|-------------|
| `test_schema_to_object_flow` | schemas → objects | Schema defines ObjectType |
| `test_object_to_storage_flow` | objects → storage | Object persisted correctly |
| `test_validator_integration` | validators → objects | Validation enforced |

#### 5.1.2 Operation Flow Integration

| Test | Modules | Description |
|------|---------|-------------|
| `test_action_execution_flow` | actions → hooks → storage | Action triggers hooks, updates storage |
| `test_governance_enforcement` | governance → actions | Governance blocks invalid actions |
| `test_evidence_collection` | evidence → actions | Actions generate evidence |

#### 5.1.3 Protocol Flow Integration

| Test | Modules | Description |
|------|---------|-------------|
| `test_3_stage_protocol_flow` | protocols → all | SCAN → TRACE → VERIFY complete |
| `test_bridge_integration` | bridge → external | External system integration |

#### 5.1.4 Planning System Integration

| Test | Modules | Description |
|------|---------|-------------|
| `test_decomposer_to_budget` | task_decomposer → context_budget | Decomposition respects budget |
| `test_output_layer_flow` | output_layer → l2_synthesizer | L1→L2→L3 flow |

#### 5.1.5 PAI Integration

| Test | Modules | Description |
|------|---------|-------------|
| `test_skill_routing_flow` | skills → algorithm | Skill uses effort levels |
| `test_trait_composition` | traits → skills | Traits modify skill behavior |

### 5.2 Integration Test File

Create: `tests/oda/e2e/test_workflow_integration_e2e.py`

```python
"""
Cross-Workflow Integration E2E Tests

Tests integration points between ODA modules.
Run ONLY after all individual workflow tests pass.
"""
import pytest

pytestmark = [pytest.mark.e2e, pytest.mark.integration]


class TestDataFlowIntegration:
    """Tests for data layer integration."""

    def test_schema_to_object_to_storage_flow(self):
        """Test: Schema → Object → Storage complete flow."""
        # 1. Define schema
        # 2. Create ObjectType from schema
        # 3. Persist to storage
        # 4. Retrieve and validate
        pass


class TestOperationFlowIntegration:
    """Tests for operation layer integration."""

    def test_action_execution_with_hooks_and_evidence(self):
        """Test: Action → Hooks → Evidence → Storage flow."""
        # 1. Register action
        # 2. Execute action
        # 3. Verify hooks triggered
        # 4. Verify evidence collected
        # 5. Verify storage updated
        pass


class TestProtocolFlowIntegration:
    """Tests for 3-Stage Protocol integration."""

    def test_complete_3_stage_protocol(self):
        """Test: SCAN → TRACE → VERIFY with all modules."""
        # Stage A: SCAN
        # - Gather files_viewed
        # - Assess complexity

        # Stage B: TRACE
        # - Verify imports
        # - Match signatures

        # Stage C: VERIFY
        # - Run tests
        # - Check lint
        pass


class TestPlanningIntegration:
    """Tests for planning system integration."""

    def test_decomposition_with_context_budget(self):
        """Test: TaskDecomposer respects ContextBudgetManager."""
        pass

    def test_progressive_disclosure_flow(self):
        """Test: L1 → L2 → L3 output layer flow."""
        pass


class TestPAIIntegration:
    """Tests for PAI system integration."""

    def test_skill_routing_with_effort_levels(self):
        """Test: Skill routing uses EffortLevel from algorithm."""
        pass
```

---

## 6. Phase 3: Full System E2E Tests

### 6.1 System-Level Test Scenarios

Create: `tests/oda/e2e/test_oda_full_system_e2e.py`

```python
"""
ODA Full System E2E Tests

Tests complete ODA system flows from end to end.
Validates Palantir AIP/Foundry parity.
"""
import pytest

pytestmark = [pytest.mark.e2e, pytest.mark.system]


class TestODAFullSystemE2E:
    """Complete ODA system end-to-end tests."""

    # ========== Core ODA Flows ==========

    def test_schema_first_mutation_flow(self):
        """
        Test: Schema validation → Action execution → Audit log

        Palantir Parity: Matches Foundry's schema-first mutation pattern
        where all changes go through validated Action Types.
        """
        pass

    def test_action_only_state_change(self):
        """
        Test: State changes ONLY through registered Actions

        Palantir Parity: Matches Foundry's Action-only mutation model
        where direct data manipulation is prohibited.
        """
        pass

    def test_audit_first_execution(self):
        """
        Test: All operations logged with evidence

        Palantir Parity: Matches Foundry's comprehensive audit trail.
        """
        pass

    def test_3_stage_protocol_complete(self):
        """
        Test: SCAN → TRACE → VERIFY complete flow

        ODA-specific: Validates 3-Stage Protocol execution.
        """
        pass

    # ========== Palantir Feature Parity ==========

    def test_object_type_crud_flow(self):
        """
        Test: ObjectType Create/Read/Update/Delete

        Palantir Parity: Matches Foundry's Object Type operations.
        """
        pass

    def test_link_type_relationship_flow(self):
        """
        Test: LinkType defines and traverses relationships

        Palantir Parity: Matches Foundry's Link Type relationships.
        """
        pass

    def test_action_type_with_side_effects(self):
        """
        Test: ActionType execution with side effects

        Palantir Parity: Matches Foundry's Action side effects.
        """
        pass

    # ========== Progressive Disclosure ==========

    def test_progressive_disclosure_l1_l2_l3(self):
        """
        Test: L1 → L2 → L3 output layer flow

        ODA-specific: Validates Progressive Disclosure system.
        """
        pass

    def test_auto_compact_recovery(self):
        """
        Test: Context compaction → State recovery

        ODA-specific: Validates Auto-Compact recovery.
        """
        pass

    # ========== Resilience ==========

    def test_graceful_degradation(self):
        """Test: System degrades gracefully under failures."""
        pass

    def test_concurrent_operations(self):
        """Test: Concurrent operations handled correctly."""
        pass

    def test_transaction_rollback(self):
        """Test: Failed transactions rollback cleanly."""
        pass
```

### 6.2 Palantir Parity Validation Matrix

| Palantir Feature | ODA Implementation | Test Case | Status |
|------------------|-------------------|-----------|--------|
| Object Types | `ontology/objects/` | `test_object_type_crud_flow` | TBD |
| Link Types | `ontology/types/` | `test_link_type_relationship_flow` | TBD |
| Action Types | `ontology/actions/` | `test_action_type_with_side_effects` | TBD |
| OMS (Metadata) | `ontology/schemas/` | `test_schema_first_mutation_flow` | TBD |
| OSS (Query) | Gap - needs implementation | Blocked | ❌ |
| Funnel (Write) | `ontology/storage/` | `test_action_only_state_change` | TBD |
| Audit Trail | `ontology/evidence/` | `test_audit_first_execution` | TBD |

---

## 7. Phase 4: Architecture Enhancement

### 7.1 Gap Analysis & Implementation

Based on Palantir parity analysis, implement missing features:

#### 7.1.1 P0: Interface Types (Polymorphism)

**Gap:** ODA lacks Interface Types for polymorphic Object Type abstraction.

**Palantir Reference:** "An interface is an Ontology type that describes the shape of an object type and its capabilities. Interfaces provide object type polymorphism."

**Implementation:**

```python
# lib/oda/ontology/interfaces/__init__.py

from pydantic import BaseModel
from typing import List, Dict, Any, Type


class InterfaceType(BaseModel):
    """
    Interface Type for Object Type polymorphism.

    Palantir Parity: Matches Foundry's Interface concept.
    """
    api_name: str
    display_name: str
    description: str
    properties: List["PropertyDefinition"]
    extends: List[str] = []  # Parent interfaces

    def is_implemented_by(self, object_type: "ObjectType") -> bool:
        """Check if ObjectType implements this interface."""
        pass


class InterfaceRegistry:
    """Registry for Interface Types."""

    def register(self, interface: InterfaceType) -> None:
        pass

    def get(self, api_name: str) -> InterfaceType:
        pass

    def get_implementors(self, interface_name: str) -> List["ObjectType"]:
        """Get all ObjectTypes implementing an interface."""
        pass
```

#### 7.1.2 P0: Object Set Service (Query Layer)

**Gap:** ODA lacks unified query/filter/aggregate service for Objects.

**Palantir Reference:** "OSS allows other Foundry services and applications to query objects data from the Ontology, enabling searching, filtering, aggregating, and loading of objects."

**Implementation:**

```python
# lib/oda/ontology/oss/__init__.py

from typing import List, Dict, Any, Optional
from pydantic import BaseModel


class ObjectSetQuery(BaseModel):
    """Query definition for Object Set Service."""
    object_type: str
    filters: List[Dict[str, Any]] = []
    sort: Optional[Dict[str, str]] = None
    limit: Optional[int] = None
    offset: int = 0


class ObjectSetService:
    """
    Object Set Service for unified Ontology queries.

    Palantir Parity: Matches Foundry's OSS component.
    """

    def query(self, query: ObjectSetQuery) -> "ObjectSet":
        """Execute query and return ObjectSet."""
        pass

    def filter(self, object_type: str, **filters) -> "ObjectSet":
        """Filter objects by criteria."""
        pass

    def aggregate(self, object_type: str, aggregation: Dict) -> Dict:
        """Aggregate objects (count, sum, avg, etc.)."""
        pass

    def search(self, query: str, object_types: List[str] = None) -> "ObjectSet":
        """Full-text search across objects."""
        pass


class ObjectSet:
    """Lazy-evaluated set of objects."""

    def __iter__(self):
        pass

    def count(self) -> int:
        pass

    def to_list(self) -> List:
        pass
```

#### 7.1.3 P1: Link Type Registry

**Gap:** ODA has partial LinkType support but lacks formal registry.

**Implementation:**

```python
# lib/oda/ontology/links/__init__.py

from pydantic import BaseModel
from typing import Optional
from enum import Enum


class LinkCardinality(str, Enum):
    ONE_TO_ONE = "ONE_TO_ONE"
    ONE_TO_MANY = "ONE_TO_MANY"
    MANY_TO_ONE = "MANY_TO_ONE"
    MANY_TO_MANY = "MANY_TO_MANY"


class LinkType(BaseModel):
    """
    Link Type defining relationships between Object Types.

    Palantir Parity: Matches Foundry's Link Type concept.
    """
    api_name: str
    display_name: str
    description: str
    source_object_type: str
    target_object_type: str
    cardinality: LinkCardinality
    inverse_api_name: Optional[str] = None


class LinkTypeRegistry:
    """Registry for Link Types."""

    def register(self, link_type: LinkType) -> None:
        pass

    def get_links_for(self, object_type: str) -> List[LinkType]:
        """Get all links where object_type is source or target."""
        pass
```

#### 7.1.4 P1: Action Side Effects

**Gap:** ODA Actions lack declarative side effect system.

**Implementation:**

```python
# lib/oda/ontology/actions/side_effects.py

from pydantic import BaseModel
from typing import List, Callable, Any
from enum import Enum


class SideEffectType(str, Enum):
    NOTIFICATION = "NOTIFICATION"
    WEBHOOK = "WEBHOOK"
    AUDIT_LOG = "AUDIT_LOG"
    CASCADE_UPDATE = "CASCADE_UPDATE"
    TRIGGER_ACTION = "TRIGGER_ACTION"


class SideEffect(BaseModel):
    """Declarative side effect for Actions."""
    type: SideEffectType
    config: dict
    condition: Optional[str] = None  # Expression for conditional execution


class ActionWithSideEffects:
    """Action Type with side effects support."""

    side_effects: List[SideEffect] = []

    def execute(self, **params) -> Any:
        result = self._execute_action(**params)
        self._execute_side_effects(result)
        return result

    def _execute_side_effects(self, action_result: Any) -> None:
        for effect in self.side_effects:
            if self._should_execute(effect):
                self._execute_effect(effect, action_result)
```

### 7.2 Enhancement Priority Matrix

| Enhancement | Priority | Effort | Impact | Dependencies |
|-------------|----------|--------|--------|--------------|
| Interface Types | P0 | Medium | High | ontology/types |
| Object Set Service | P0 | High | High | ontology/storage |
| Link Type Registry | P1 | Medium | Medium | ontology/types |
| Action Side Effects | P1 | Medium | High | ontology/actions |
| Derived Properties | P2 | Medium | Medium | Interface Types |
| Dynamic Security | P2 | High | High | OSS |

---

## 8. Phase 5: Palantir Parity Validation

### 8.1 Parity Checklist

After all enhancements, validate against Palantir features:

```markdown
## Palantir AIP/Foundry Parity Checklist

### Core Ontology
- [ ] Object Types with typed properties
- [ ] Link Types with cardinality
- [ ] Interface Types for polymorphism
- [ ] Action Types with validation
- [ ] Action Side Effects

### Services
- [ ] OMS-equivalent metadata service
- [ ] OSS-equivalent query service
- [ ] Funnel-equivalent write orchestration
- [ ] Audit trail for all operations

### SDK
- [ ] Type-safe ObjectType definitions
- [ ] Generated client code (OSDK-equivalent)
- [ ] Query builder API

### Security
- [ ] Schema-first validation
- [ ] Action-only mutations
- [ ] Audit logging
- [ ] Row-level security (stretch goal)

### AI/Agent Integration
- [ ] Ontology-backed Actions for agents
- [ ] Bounded context retrieval
- [ ] Safe tool execution
```

### 8.2 Final Validation Tests

Create: `tests/oda/e2e/test_palantir_parity_e2e.py`

```python
"""
Palantir AIP/Foundry Parity Validation Tests

Validates ODA matches or exceeds Palantir production standards.
"""
import pytest

pytestmark = [pytest.mark.e2e, pytest.mark.parity]


class TestPalantirParity:
    """Palantir feature parity validation."""

    # Core Ontology
    def test_parity_object_types(self):
        """Validate: Object Types match Foundry capabilities."""
        pass

    def test_parity_link_types(self):
        """Validate: Link Types match Foundry capabilities."""
        pass

    def test_parity_interface_types(self):
        """Validate: Interface Types match Foundry capabilities."""
        pass

    def test_parity_action_types(self):
        """Validate: Action Types match Foundry capabilities."""
        pass

    # Services
    def test_parity_metadata_service(self):
        """Validate: Metadata service matches OMS."""
        pass

    def test_parity_query_service(self):
        """Validate: Query service matches OSS."""
        pass

    # SDK
    def test_parity_type_safety(self):
        """Validate: Type safety matches OSDK."""
        pass

    # Beyond Palantir
    def test_beyond_palantir_3_stage_protocol(self):
        """Validate: 3-Stage Protocol (ODA innovation)."""
        pass

    def test_beyond_palantir_progressive_disclosure(self):
        """Validate: Progressive Disclosure (ODA innovation)."""
        pass

    def test_beyond_palantir_auto_compact_recovery(self):
        """Validate: Auto-Compact Recovery (ODA innovation)."""
        pass
```

---

## 9. Execution Protocol

### 9.1 Autonomous Execution Rules

```yaml
# MANDATORY RULES FOR AUTONOMOUS EXECUTION

1. ACTION_BIAS:
   - Default to implementing with reasonable assumptions
   - Do NOT ask clarifying questions unless truly blocked
   - Make decisions and proceed

2. BATCH_EDITS:
   - Read sufficient context before modifying files
   - Plan all needed modifications upfront
   - Avoid repeated micro-edits

3. EXPLICIT_TODO:
   - Create TODO list at start of each phase
   - Update after each major step
   - Reconcile all intentions before concluding

4. VERIFY_BEFORE_PROCEED:
   - Run tests after each module
   - Fix failures before moving to next
   - 100% pass rate required before phase transition

5. CONTEXT_MANAGEMENT:
   - Use /compact when context grows large
   - Batch file reads using parallel calls
   - Limit tool outputs to 10k tokens

6. PROGRESS_LOGGING:
   - Log to .agent/logs/e2e_progress.log
   - Update .agent/reports/e2e_status.md after each phase
   - Include timestamps and metrics
```

### 9.2 Phase Transition Gates

| Gate | Criteria | Action if Failed |
|------|----------|------------------|
| Phase 1 → 2 | All individual E2E tests pass | Fix failing tests |
| Phase 2 → 3 | All integration tests pass | Debug integration issues |
| Phase 3 → 4 | System tests pass, gaps identified | Document remaining gaps |
| Phase 4 → 5 | Enhancements implemented | Complete implementation |
| Phase 5 Complete | Parity validation passes | Final report |

### 9.3 Error Recovery Protocol

```yaml
ON_TEST_FAILURE:
  1. Read test output carefully
  2. Identify root cause (not symptom)
  3. Fix source code, not test
  4. Re-run specific test
  5. If still failing after 3 attempts, log and continue

ON_IMPLEMENTATION_BLOCK:
  1. Document the blocker in .agent/logs/blockers.log
  2. Create placeholder with TODO comment
  3. Continue with other work
  4. Return to blocker after phase complete

ON_CONTEXT_LIMIT:
  1. Run /compact
  2. Read phase summary from .agent/reports/
  3. Resume from last checkpoint
```

---

## 10. Output Requirements

### 10.1 Test Files Created

```
tests/oda/e2e/
├── test_types_e2e.py
├── test_schemas_e2e.py
├── test_decorators_e2e.py
├── test_objects_e2e.py
├── test_storage_e2e.py
├── test_validators_e2e.py
├── test_actions_e2e.py
├── test_hooks_e2e.py
├── test_evidence_e2e.py
├── test_governance_e2e.py
├── test_protocols_e2e.py
├── test_bridge_e2e.py
├── test_tracking_e2e.py
├── test_task_decomposer_e2e.py
├── test_context_budget_manager_e2e.py
├── test_output_layer_manager_e2e.py
├── test_l2_synthesizer_e2e.py
├── test_pai_algorithm_e2e.py
├── test_pai_skills_e2e.py
├── test_pai_traits_e2e.py
├── test_pai_hooks_e2e.py
├── test_claude_handlers_e2e.py
├── test_llm_adapters_e2e.py
├── test_mcp_e2e.py
├── test_semantic_e2e.py
├── test_workflow_integration_e2e.py
├── test_oda_full_system_e2e.py
└── test_palantir_parity_e2e.py
```

### 10.2 Enhancement Files Created

```
lib/oda/ontology/
├── interfaces/
│   ├── __init__.py
│   ├── interface_type.py
│   └── interface_registry.py
├── oss/
│   ├── __init__.py
│   ├── query.py
│   ├── object_set.py
│   └── service.py
├── links/
│   ├── __init__.py
│   ├── link_type.py
│   └── link_registry.py
└── actions/
    └── side_effects.py
```

### 10.3 Reports Generated

```
.agent/reports/
├── e2e_status.md           # Phase-by-phase status
├── e2e_final_report.md     # Complete final report
├── palantir_parity.md      # Parity validation results
├── gap_analysis.md         # Identified gaps
└── enhancement_summary.md  # Enhancement implementation summary

.agent/logs/
├── e2e_progress.log        # Detailed progress log
├── test_results.log        # Test execution results
└── blockers.log            # Documented blockers
```

### 10.4 Final Report Template

```markdown
# ODA E2E Test & Enhancement Final Report

## Executive Summary
- **Execution Duration:** X hours
- **Total Tests Created:** N
- **Pass Rate:** X%
- **Coverage:** X%
- **Palantir Parity Score:** X/10

## Phase Results

### Phase 1: Individual Workflow E2E
| Module | Tests | Pass | Fail | Coverage |
|--------|-------|------|------|----------|
| ... | ... | ... | ... | ... |

### Phase 2: Integration Tests
...

### Phase 3: System Tests
...

### Phase 4: Enhancements
| Enhancement | Status | Files Created |
|-------------|--------|---------------|
| ... | ... | ... |

### Phase 5: Parity Validation
| Feature | Palantir | ODA | Parity |
|---------|----------|-----|--------|
| ... | ... | ... | ✅/❌ |

## Recommendations
1. ...
2. ...

## Next Steps
1. ...
2. ...
```

---

## 🚀 BEGIN EXECUTION

Start with **Phase 1.1.1: ontology/types E2E**

```bash
# Verify test directory exists
mkdir -p tests/oda/e2e

# Create first test file
# tests/oda/e2e/test_types_e2e.py

# Run to verify setup
pytest tests/oda/e2e/test_types_e2e.py -v
```

**Remember:**
- Work autonomously
- Verify before proceeding
- Log progress regularly
- Achieve Palantir parity or better

---

## References

- [Palantir Ontology Architecture](https://www.palantir.com/docs/foundry/object-backend/overview)
- [Palantir Action Types](https://www.palantir.com/docs/foundry/action-types/overview)
- [Palantir OSDK Overview](https://www.palantir.com/docs/foundry/ontology-sdk/overview)
- [Palantir AIP Features](https://www.palantir.com/docs/foundry/aip/aip-features)
- [GPT-5.2-Codex Prompting Guide](https://cookbook.openai.com/examples/gpt-5/gpt-5-1-codex-max_prompting_guide)
