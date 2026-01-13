# ODA Full Import Refactoring - Migration File List

> **Generated:** 2026-01-10
> **Scope:** Complete `from scripts.` import migration to relative imports
> **Total Files Affected:** 120+ files

---

## Table of Contents

1. [Import Change Target Files](#1-import-change-target-files)
2. [Hardcoded Path Files](#2-hardcoded-path-files)
3. [sys.path Manipulation Files](#3-syspath-manipulation-files)
4. [Test File Impact Analysis](#4-test-file-impact-analysis)
5. [Circular Dependency Resolution Plan](#5-circular-dependency-resolution-plan)

---

## 1. Import Change Target Files

### 1.1 scripts/observe/ (2 files)

| File | Line | Current Import |
|------|------|----------------|
| `/home/palantir/park-kyungchan/palantir/scripts/observe/repository.py` | 17 | `from scripts.observe.models import HookEvent` |
| `/home/palantir/park-kyungchan/palantir/scripts/observe/repository.py` | 48 | `from scripts.ontology.storage.database import DatabaseManager` |
| `/home/palantir/park-kyungchan/palantir/scripts/observe/repository.py` | 51 | `from scripts.ontology.storage import get_database` |
| `/home/palantir/park-kyungchan/palantir/scripts/observe/server.py` | 22 | `from scripts.observe.repository import EventsRepository` |
| `/home/palantir/park-kyungchan/palantir/scripts/observe/server.py` | 23 | `from scripts.observe.models import HookEvent` |

### 1.2 scripts/mcp/ (1 file)

| File | Line | Current Import |
|------|------|----------------|
| `/home/palantir/park-kyungchan/palantir/scripts/mcp/ontology_server.py` | 29 | `from scripts.ontology.actions import action_registry, ActionContext` |
| `/home/palantir/park-kyungchan/palantir/scripts/mcp/ontology_server.py` | 30 | `from scripts.ontology.objects.proposal import (...)` |
| `/home/palantir/park-kyungchan/palantir/scripts/mcp/ontology_server.py` | 35 | `from scripts.ontology.storage.database import initialize_database` |
| `/home/palantir/park-kyungchan/palantir/scripts/mcp/ontology_server.py` | 36 | `from scripts.ontology.storage.proposal_repository import (...)` |

### 1.3 scripts/governance.py (1 file)

| File | Line | Current Import |
|------|------|----------------|
| `/home/palantir/park-kyungchan/palantir/scripts/governance.py` | 14 | `from scripts.ontology.storage import ProposalRepository, initialize_database` |
| `/home/palantir/park-kyungchan/palantir/scripts/governance.py` | 15 | `from scripts.ontology.objects.proposal import ProposalStatus` |

### 1.4 scripts/cognitive/ (4 files)

| File | Line | Current Import |
|------|------|----------------|
| `/home/palantir/park-kyungchan/palantir/scripts/cognitive/learner.py` | 4 | `from scripts.cognitive.types import LearnerState, KnowledgeComponent` |
| `/home/palantir/park-kyungchan/palantir/scripts/cognitive/learner.py` | 5 | `from scripts.ontology.objects.learning import Learner` |
| `/home/palantir/park-kyungchan/palantir/scripts/cognitive/learner.py` | 6 | `from scripts.ontology.storage.learner_repository import LearnerRepository` |
| `/home/palantir/park-kyungchan/palantir/scripts/cognitive/learner.py` | 7 | `from scripts.ontology.actions.learning_actions import SaveLearnerStateAction` |
| `/home/palantir/park-kyungchan/palantir/scripts/cognitive/learner.py` | 8 | `from scripts.simulation.core import ActionRunner, ActionContext` |
| `/home/palantir/park-kyungchan/palantir/scripts/cognitive/learner.py` | 9 | `from scripts.ontology.storage.database import get_database` |
| `/home/palantir/park-kyungchan/palantir/scripts/cognitive/engine.py` | 5 | `from scripts.cognitive.types import LearnerState, ScopedLesson` |
| `/home/palantir/park-kyungchan/palantir/scripts/cognitive/engine.py` | 6 | `from scripts.cognitive.learner import LearnerManager` |
| `/home/palantir/park-kyungchan/palantir/scripts/cognitive/engine.py` | 7 | `from scripts.ontology.learning.scoping import ScopingEngine` |
| `/home/palantir/park-kyungchan/palantir/scripts/cognitive/engine.py` | 8 | `from scripts.ontology.learning.engine import TutoringEngine` |
| `/home/palantir/park-kyungchan/palantir/scripts/cognitive/engine.py` | 9 | `from scripts.cognitive.generator import LessonGenerator, LessonInput, LessonContent` |
| `/home/palantir/park-kyungchan/palantir/scripts/cognitive/engine.py` | 10 | `from scripts.aip_logic.engine import LogicEngine` |
| `/home/palantir/park-kyungchan/palantir/scripts/cognitive/engine.py` | 11 | `from scripts.llm.instructor_client import InstructorClient` |
| `/home/palantir/park-kyungchan/palantir/scripts/cognitive/engine.py` | 64 | `from scripts.ontology.learning.metrics import analyze_file` |
| `/home/palantir/park-kyungchan/palantir/scripts/cognitive/generator.py` | 4 | `from scripts.aip_logic.engine import LLMBasedLogicFunction` |
| `/home/palantir/park-kyungchan/palantir/scripts/cognitive/generator.py` | 5 | `from scripts.aip_logic.function import LogicContext` |
| `/home/palantir/park-kyungchan/palantir/scripts/cognitive/generator.py` | 6 | `from scripts.cognitive.types import ComplexityScore, LearnerState` |
| `/home/palantir/park-kyungchan/palantir/scripts/cognitive/generator.py` | 7 | `from scripts.llm.instructor_client import InstructorClient` |

### 1.5 scripts/aip_logic/ (4 files)

| File | Line | Current Import |
|------|------|----------------|
| `/home/palantir/park-kyungchan/palantir/scripts/aip_logic/registry.py` | 5 | `from scripts.aip_logic.function import LogicFunction, Input, Output` |
| `/home/palantir/park-kyungchan/palantir/scripts/aip_logic/engine.py` | 6 | `from scripts.llm.instructor_client import InstructorClient` |
| `/home/palantir/park-kyungchan/palantir/scripts/aip_logic/engine.py` | 7 | `from scripts.aip_logic.function import LogicFunction, LogicContext, Input, Output` |
| `/home/palantir/park-kyungchan/palantir/scripts/aip_logic/function.py` | 5 | `from scripts.llm.instructor_client import InstructorClient` |
| `/home/palantir/park-kyungchan/palantir/scripts/aip_logic/function.py` | 6 | `from scripts.llm.config import get_default_model` |

### 1.6 scripts/maintenance/ (1 file)

| File | Line | Current Import |
|------|------|----------------|
| `/home/palantir/park-kyungchan/palantir/scripts/maintenance/rebuild_db.py` | 11 | `from scripts.ontology.storage.database import initialize_database` |
| `/home/palantir/park-kyungchan/palantir/scripts/maintenance/rebuild_db.py` | 12 | `from scripts.ontology.storage.models import Base` |

### 1.7 scripts/layer/ (2 files)

| File | Line | Current Import |
|------|------|----------------|
| `/home/palantir/park-kyungchan/palantir/scripts/layer/commands.py` | 13 | `from scripts.layer.subagent_manager import SubAgentManager` |
| `/home/palantir/park-kyungchan/palantir/scripts/layer/subagent_manager.py` | 23 | `from scripts.layer.parallel_notifier import ParallelNotifier, get_notifier` |

### 1.8 scripts/claude/ (9 files)

| File | Line | Current Import |
|------|------|----------------|
| `/home/palantir/park-kyungchan/palantir/scripts/claude/handlers/planning_handlers.py` | 12 | `from scripts.claude.evidence_tracker import EvidenceTracker` |
| `/home/palantir/park-kyungchan/palantir/scripts/claude/handlers/__init__.py` | 2-4 | `from scripts.claude.handlers.audit_handlers import *` etc. |
| `/home/palantir/park-kyungchan/palantir/scripts/claude/handlers/audit_handlers.py` | 14 | `from scripts.claude.evidence_tracker import EvidenceTracker` |
| `/home/palantir/park-kyungchan/palantir/scripts/claude/handlers/governance_handlers.py` | 12 | `from scripts.claude.evidence_tracker import EvidenceTracker` |
| `/home/palantir/park-kyungchan/palantir/scripts/claude/protocol_runner.py` | 19-20 | `from scripts.claude.evidence_tracker import EvidenceTracker, AntiHallucinationError` etc. |
| `/home/palantir/park-kyungchan/palantir/scripts/claude/protocol_runner.py` | 205 | `from scripts.claude.protocol_adapter import (...)` |
| `/home/palantir/park-kyungchan/palantir/scripts/claude/todo_sync.py` | 19-21 | `from scripts.ontology.objects.task_types import Task, TaskStatus, TaskPriority` etc. |
| `/home/palantir/park-kyungchan/palantir/scripts/claude/protocol_adapter.py` | 17-29 | Multiple ontology/claude imports |
| `/home/palantir/park-kyungchan/palantir/scripts/claude/protocol_adapter.py` | 482-494 | Protocol imports |
| `/home/palantir/park-kyungchan/palantir/scripts/claude/__init__.py` | 15-17 | `from scripts.claude.todo_sync import TodoTaskSync, TodoStatus` etc. |
| `/home/palantir/park-kyungchan/palantir/scripts/claude/sandbox_runner.py` | 9 | `from scripts.claude.sandbox_runner import SandboxRunner` |

### 1.9 scripts/memory/ (2 files)

| File | Line | Current Import |
|------|------|----------------|
| `/home/palantir/park-kyungchan/palantir/scripts/memory/manager.py` | 10-13 | Multiple ontology/simulation imports |
| `/home/palantir/park-kyungchan/palantir/scripts/memory/recall.py` | 11 | `from scripts.memory.manager import MemoryManager` |

### 1.10 scripts/consolidate.py (1 file)

| File | Line | Current Import |
|------|------|----------------|
| `/home/palantir/park-kyungchan/palantir/scripts/consolidate.py` | 13-16 | Multiple imports |

### 1.11 scripts/relay/ (1 file)

| File | Line | Current Import |
|------|------|----------------|
| `/home/palantir/park-kyungchan/palantir/scripts/relay/queue.py` | 6-8 | `from scripts.ontology.storage.database import DatabaseManager` etc. |
| `/home/palantir/park-kyungchan/palantir/scripts/relay/queue.py` | 33 | `from scripts.ontology.storage.relay_repository import RelayTask as RelayTaskDomain` |

### 1.12 scripts/api/ (4 files)

| File | Line | Current Import |
|------|------|----------------|
| `/home/palantir/park-kyungchan/palantir/scripts/api/dependencies.py` | 10-11 | Database and repository imports |
| `/home/palantir/park-kyungchan/palantir/scripts/api/main.py` | 19-20 | `from scripts.ontology.storage.database import initialize_database` etc. |
| `/home/palantir/park-kyungchan/palantir/scripts/api/routes.py` | 12-26 | Multiple imports |
| `/home/palantir/park-kyungchan/palantir/scripts/api/routes.py` | 94-95 | Runtime/ontology imports |

### 1.13 scripts/tools/ (5 files)

| File | Line | Current Import |
|------|------|----------------|
| `/home/palantir/park-kyungchan/palantir/scripts/tools/cli.py` | 44-248 | Multiple dynamic imports |
| `/home/palantir/park-kyungchan/palantir/scripts/tools/sps/runner.py` | 13 | `from scripts.tools.sps.prompts import Prompt, PromptManager` |
| `/home/palantir/park-kyungchan/palantir/scripts/tools/sps/runner.py` | 42 | `from scripts.llm.instructor_client import InstructorClient` |
| `/home/palantir/park-kyungchan/palantir/scripts/tools/__main__.py` | 12 | `from scripts.tools.cli import main` |
| `/home/palantir/park-kyungchan/palantir/scripts/tools/yt/state_machine.py` | 89-90 | `from scripts.tools.yt.transcriber import Transcriber` etc. |
| `/home/palantir/park-kyungchan/palantir/scripts/tools/yt/generator.py` | 42 | `from scripts.llm.instructor_client import InstructorClient` |

### 1.14 scripts/agent/ (3 files)

| File | Line | Current Import |
|------|------|----------------|
| `/home/palantir/park-kyungchan/palantir/scripts/agent/executor.py` | 25-34 | Multiple ontology imports |
| `/home/palantir/park-kyungchan/palantir/scripts/agent/__init__.py` | 14-15 | `from scripts.agent.executor import AgentExecutor` etc. |
| `/home/palantir/park-kyungchan/palantir/scripts/agent/protocols.py` | 22 | `from scripts.ontology.ontology_types import utc_now` |
| `/home/palantir/park-kyungchan/palantir/scripts/agent/protocols.py` | 329 | `from scripts.agent.executor import TaskResult` |

### 1.15 scripts/lib/ (1 file)

| File | Line | Current Import |
|------|------|----------------|
| `/home/palantir/park-kyungchan/palantir/scripts/lib/textrank.py` | 86 | `from scripts.ontology.learning.algorithms.preprocessing import tokenize` |

### 1.16 scripts/data/ (1 file)

| File | Line | Current Import |
|------|------|----------------|
| `/home/palantir/park-kyungchan/palantir/scripts/data/database.py` | 4 | `from scripts.ontology.storage.database import Database` |

### 1.17 scripts/simulation/ (2 files)

| File | Line | Current Import |
|------|------|----------------|
| `/home/palantir/park-kyungchan/palantir/scripts/simulation/core.py` | 11-15 | Multiple infrastructure/ontology imports |
| `/home/palantir/park-kyungchan/palantir/scripts/simulation/complex_mission.py` | 10-11 | Runtime/relay imports |

### 1.18 scripts/consolidation/ (1 file)

| File | Line | Current Import |
|------|------|----------------|
| `/home/palantir/park-kyungchan/palantir/scripts/consolidation/miner.py` | 11-17 | Multiple ontology imports |

### 1.19 scripts/llm/ (3 files)

| File | Line | Current Import |
|------|------|----------------|
| `/home/palantir/park-kyungchan/palantir/scripts/llm/providers.py` | 22 | `from scripts.llm.config import LLMBackendConfig, LLMProviderType, load_llm_config` |
| `/home/palantir/park-kyungchan/palantir/scripts/llm/instructor_client.py` | 26-28 | Plan and config imports |
| `/home/palantir/park-kyungchan/palantir/scripts/llm/instructor_client.py` | 141-142 | Action/simulation imports |

### 1.20 scripts/runtime/ (3 files)

| File | Line | Current Import |
|------|------|----------------|
| `/home/palantir/park-kyungchan/palantir/scripts/runtime/kernel.py` | 16-24 | Multiple imports |
| `/home/palantir/park-kyungchan/palantir/scripts/runtime/marshaler.py` | 17 | `from scripts.ontology.actions import (...)` |
| `/home/palantir/park-kyungchan/palantir/scripts/runtime/planning_hook.py` | 26 | Hardcoded path (see section 2) |

### 1.21 scripts/voice/ (2 files)

| File | Line | Current Import |
|------|------|----------------|
| `/home/palantir/park-kyungchan/palantir/scripts/voice/ada.py` | 18-20 | STT/TTS/Scratchpad imports |
| `/home/palantir/park-kyungchan/palantir/scripts/voice/ada.py` | 67-79 | Multiple dynamic imports |
| `/home/palantir/park-kyungchan/palantir/scripts/voice/ada.py` | 244 | `from scripts.ontology.actions import ActionContext` |
| `/home/palantir/park-kyungchan/palantir/scripts/voice/__main__.py` | 14 | `from scripts.voice.ada import AlwaysOnAssistant` |

### 1.22 scripts/osdk/ (5 files)

| File | Line | Current Import |
|------|------|----------------|
| `/home/palantir/park-kyungchan/palantir/scripts/osdk/actions.py` | 4-5 | Ontology imports |
| `/home/palantir/park-kyungchan/palantir/scripts/osdk/connector.py` | 6 | `from scripts.ontology.ontology_types import OntologyObject` |
| `/home/palantir/park-kyungchan/palantir/scripts/osdk/sqlite_connector.py` | 8-23 | Multiple imports |
| `/home/palantir/park-kyungchan/palantir/scripts/osdk/generator.py` | 51-57 | Generated import strings |
| `/home/palantir/park-kyungchan/palantir/scripts/osdk/query.py` | 6 | `from scripts.ontology.ontology_types import OntologyObject` |
| `/home/palantir/park-kyungchan/palantir/scripts/osdk/query.py` | 61 | `from scripts.osdk.sqlite_connector import SQLiteConnector` |

### 1.23 scripts/infrastructure/ (2 files)

| File | Line | Current Import |
|------|------|----------------|
| `/home/palantir/park-kyungchan/palantir/scripts/infrastructure/metrics.py` | 32 | `from scripts.ontology.storage.proposal_repository import ProposalRepository` |
| `/home/palantir/park-kyungchan/palantir/scripts/infrastructure/metrics.py` | 208 | `from scripts.infrastructure.event_bus import EventBus` |
| `/home/palantir/park-kyungchan/palantir/scripts/infrastructure/__init__.py` | 7-8 | EventBus and metrics imports |

### 1.24 scripts/ontology/ (40+ files - Core Module)

| File | Line | Current Import |
|------|------|----------------|
| `/home/palantir/park-kyungchan/palantir/scripts/ontology/registry.py` | 24 | `from scripts.ontology.ontology_types import Link, OntologyObject, PropertyType` |
| `/home/palantir/park-kyungchan/palantir/scripts/ontology/registry.py` | 209-212 | Object module imports |
| `/home/palantir/park-kyungchan/palantir/scripts/ontology/actions/__init__.py` | 42 | `from scripts.ontology.ontology_types import OntologyObject, utc_now` |
| `/home/palantir/park-kyungchan/palantir/scripts/ontology/actions/__init__.py` | 638 | `from scripts.ontology.storage.exceptions import ConcurrencyError` |
| `/home/palantir/park-kyungchan/palantir/scripts/ontology/actions/__init__.py` | 820 | `from scripts.ontology.governance import (...)` |
| `/home/palantir/park-kyungchan/palantir/scripts/ontology/actions/__init__.py` | 941 | `from scripts.ontology.protocols.decorators import ProtocolRegistry` |
| `/home/palantir/park-kyungchan/palantir/scripts/ontology/actions/__init__.py` | 995 | `from scripts.ontology.actions import validate_registry` |
| `/home/palantir/park-kyungchan/palantir/scripts/ontology/actions/learning_actions.py` | 2-5 | Multiple imports |
| `/home/palantir/park-kyungchan/palantir/scripts/ontology/actions/logic_actions.py` | 5-9 | Multiple imports |
| `/home/palantir/park-kyungchan/palantir/scripts/ontology/actions/memory_actions.py` | 3-7 | Multiple imports |
| `/home/palantir/park-kyungchan/palantir/scripts/ontology/actions/llm_actions.py` | 6-8 | Multiple imports |
| `/home/palantir/park-kyungchan/palantir/scripts/ontology/actions/llm_actions.py` | 32-125 | Multiple dynamic imports |
| `/home/palantir/park-kyungchan/palantir/scripts/ontology/actions/workflow_actions.py` | 11-20 | Multiple imports |
| `/home/palantir/park-kyungchan/palantir/scripts/ontology/actions/side_effects.py` | 151 | `from scripts.infrastructure.event_bus import EventBus` |
| `/home/palantir/park-kyungchan/palantir/scripts/ontology/actions/learning_kb_actions.py` | 9-33 | Multiple imports |
| `/home/palantir/park-kyungchan/palantir/scripts/ontology/objects/core_definitions.py` | 12-13 | Registry and types imports |
| `/home/palantir/park-kyungchan/palantir/scripts/ontology/objects/proposal.py` | 24-25 | Types and registry imports |
| `/home/palantir/park-kyungchan/palantir/scripts/ontology/objects/learning.py` | 4-5 | Types and registry imports |
| `/home/palantir/park-kyungchan/palantir/scripts/ontology/objects/task_types.py` | 9-10 | Types and registry imports |
| `/home/palantir/park-kyungchan/palantir/scripts/ontology/objects/audit_log.py` | 26-27 | Types and registry imports |
| `/home/palantir/park-kyungchan/palantir/scripts/ontology/objects/task_actions.py` | 26-27 | Multiple imports |
| `/home/palantir/park-kyungchan/palantir/scripts/ontology/storage/database.py` | 36-37 | Models and ORM imports |
| `/home/palantir/park-kyungchan/palantir/scripts/ontology/storage/base_repository.py` | 46-58 | Multiple imports |
| `/home/palantir/park-kyungchan/palantir/scripts/ontology/storage/proposal_repository.py` | 12-17 | Multiple imports |
| `/home/palantir/park-kyungchan/palantir/scripts/ontology/storage/proposal_repository.py` | 168-186 | Dynamic imports |
| `/home/palantir/park-kyungchan/palantir/scripts/ontology/storage/repositories.py` | 24-37 | Multiple imports |
| `/home/palantir/park-kyungchan/palantir/scripts/ontology/storage/relay_repository.py` | 4-5 | Base and models imports |
| `/home/palantir/park-kyungchan/palantir/scripts/ontology/storage/learner_repository.py` | 10-13 | Multiple imports |
| `/home/palantir/park-kyungchan/palantir/scripts/ontology/storage/task_repository.py` | 9-12 | Multiple imports |
| `/home/palantir/park-kyungchan/palantir/scripts/ontology/schemas/governance.py` | 5 | `from scripts.ontology.ontology_types import OrionObject` |
| `/home/palantir/park-kyungchan/palantir/scripts/ontology/schemas/memory.py` | 5 | `from scripts.ontology.ontology_types import OrionObject` |
| `/home/palantir/park-kyungchan/palantir/scripts/ontology/schemas/result.py` | 3 | `from scripts.ontology.ontology_types import OrionObject` |
| `/home/palantir/park-kyungchan/palantir/scripts/ontology/protocols/base.py` | - | (imports needed) |
| `/home/palantir/park-kyungchan/palantir/scripts/ontology/protocols/planning_protocol.py` | 17 | `from scripts.ontology.protocols.base import (...)` |
| `/home/palantir/park-kyungchan/palantir/scripts/ontology/protocols/audit_protocol.py` | 17 | `from scripts.ontology.protocols.base import (...)` |
| `/home/palantir/park-kyungchan/palantir/scripts/ontology/protocols/execution_protocol.py` | 17 | `from scripts.ontology.protocols.base import (...)` |
| `/home/palantir/park-kyungchan/palantir/scripts/ontology/protocols/decorators.py` | 25-146 | Multiple imports |
| `/home/palantir/park-kyungchan/palantir/scripts/ontology/governance/holistic_validator.py` | 16 | `from scripts.ontology.governance.violations import (...)` |
| `/home/palantir/park-kyungchan/palantir/scripts/ontology/governance/quality_gate.py` | 9-24 | Multiple imports |
| `/home/palantir/park-kyungchan/palantir/scripts/ontology/governance/loader.py` | 221-284 | Dynamic imports |
| `/home/palantir/park-kyungchan/palantir/scripts/ontology/validators/__init__.py` | 7 | `from scripts.ontology.validators.schema_validator import (...)` |
| `/home/palantir/park-kyungchan/palantir/scripts/ontology/validators/schema_validator.py` | 18 | `from scripts.ontology.validators import get_validator` |
| `/home/palantir/park-kyungchan/palantir/scripts/ontology/learning/engine.py` | - | (verify imports) |
| `/home/palantir/park-kyungchan/palantir/scripts/ontology/learning/prompt_scope.py` | 22 | `from scripts.ontology.learning.engine import TutoringEngine` |
| `/home/palantir/park-kyungchan/palantir/scripts/ontology/learning/persistence.py` | 11-14 | Multiple imports |
| `/home/palantir/park-kyungchan/palantir/scripts/ontology/learning/verify_*.py` | - | Multiple verification scripts |
| `/home/palantir/park-kyungchan/palantir/scripts/ontology/ontology_types.py` | 327-328 | Circular type hints |
| `/home/palantir/park-kyungchan/palantir/scripts/ontology/handoff.py` | 5 | `from scripts.ontology.plan import Plan` |
| `/home/palantir/park-kyungchan/palantir/scripts/ontology/init_beginner.py` | 2-5 | Multiple imports |
| `/home/palantir/park-kyungchan/palantir/scripts/ontology/run_tutor.py` | 30-31 | Cognitive/ontology imports |
| `/home/palantir/park-kyungchan/palantir/scripts/ontology/run_tutor.py` | 210-399 | Multiple dynamic imports |
| `/home/palantir/park-kyungchan/palantir/scripts/ontology/jobs/cleanup.py` | 17-19 | Multiple imports |
| `/home/palantir/park-kyungchan/palantir/scripts/ontology/plans/orchestrator.py` | 23-235 | Multiple imports |
| `/home/palantir/park-kyungchan/palantir/scripts/ontology/fde_learning/__init__.py` | 17 | `from scripts.ontology.fde_learning.actions import (...)` |
| `/home/palantir/park-kyungchan/palantir/scripts/ontology/fde_learning/actions.py` | 38-49 | Multiple imports |
| `/home/palantir/park-kyungchan/palantir/scripts/ontology/kb/__init__.py` | 11-12 | Index and match imports |
| `/home/palantir/park-kyungchan/palantir/scripts/ontology/evidence/__init__.py` | 7 | `from scripts.ontology.evidence.collector import (...)` |
| `/home/palantir/park-kyungchan/palantir/scripts/ontology/evidence/collector.py` | 19 | `from scripts.ontology.evidence import track_evidence, get_current_evidence` |
| `/home/palantir/park-kyungchan/palantir/scripts/ontology/relays/result_job_job-test-01.py` | 16-17 | Multiple imports |

---

## 2. Hardcoded Path Files

### 2.1 Complete List (16 Files with Source Code Changes)

#### File 1: `/home/palantir/park-kyungchan/palantir/scripts/workflow_runner.py`

```python
# Line 11 - Current
WORKFLOWS_DIR = Path("/home/palantir/park-kyungchan/palantir/.agent/workflows")

# Line 11 - After
WORKFLOWS_DIR = Path(__file__).parent.parent / ".agent/workflows"
```

#### File 2: `/home/palantir/park-kyungchan/palantir/scripts/llm/config.py`

```python
# Line 61 - Current
    return "/home/palantir"

# Line 61 - After
    return str(Path(__file__).parent.parent.parent)
```

#### File 3: `/home/palantir/park-kyungchan/palantir/scripts/maintenance/rebuild_db.py`

```python
# Line 23 - Current
        db_path = os.environ.get("ORION_DB_PATH", "/home/palantir/park-kyungchan/palantir/data/ontology.db")

# Line 23 - After
        db_path = os.environ.get("ORION_DB_PATH", str(Path(__file__).parent.parent.parent / "data/ontology.db"))
```

#### File 4: `/home/palantir/park-kyungchan/palantir/scripts/mcp_preflight.py`

```python
# Line 38 - Current
        return "/home/palantir"

# Line 38 - After
        return str(Path(__file__).parent.parent)
```

#### File 5: `/home/palantir/park-kyungchan/palantir/scripts/mcp_manager.py`

```python
# Line 47 - Current
        return "/home/palantir"

# Line 47 - After
        return str(Path(__file__).parent.parent)
```

#### File 6: `/home/palantir/park-kyungchan/palantir/scripts/lifecycle_manager.py`

```python
# Line 13 - Current
AGENTS_ROOT = "/home/palantir/.agent"

# Line 13 - After
AGENTS_ROOT = str(Path(__file__).parent.parent / ".agent")
```

#### File 7: `/home/palantir/park-kyungchan/palantir/scripts/ontology/validators/schema_validator.py`

```python
# Line 223 - Current
            "/home/palantir/park-kyungchan/palantir"

# Line 223 - After
            str(Path(__file__).parent.parent.parent.parent)
```

#### File 8: `/home/palantir/park-kyungchan/palantir/scripts/claude/sandbox_runner.py`

```python
# Line 71 - Current
    workspace_root: Path = field(default_factory=lambda: Path("/home/palantir/park-kyungchan/palantir"))

# Line 71 - After
    workspace_root: Path = field(default_factory=lambda: Path(__file__).parent.parent.parent)
```

#### File 9: `/home/palantir/park-kyungchan/palantir/scripts/ontology/handoff.py`

```python
# Line 8-10 - Current
TEMPLATE_DIR = "/home/palantir/park-kyungchan/palantir/.agent/handoffs/templates"
PENDING_DIR = "/home/palantir/park-kyungchan/palantir/.agent/handoffs/pending"
PLANS_DIR = "/home/palantir/.agent/plans"

# Line 8-10 - After
_PROJECT_ROOT = Path(__file__).parent.parent.parent
TEMPLATE_DIR = str(_PROJECT_ROOT / ".agent/handoffs/templates")
PENDING_DIR = str(_PROJECT_ROOT / ".agent/handoffs/pending")
PLANS_DIR = str(_PROJECT_ROOT.parent.parent / ".agent/plans")
```

#### File 10: `/home/palantir/park-kyungchan/palantir/scripts/ontology/memory_sync.py`

```python
# Line 11-13 - Current
WORKSPACE_ROOT = Path(os.environ.get("ORION_WORKSPACE_ROOT", "/home/palantir"))
...
ORION_MEMORY = Path("/home/palantir/park-kyungchan/palantir/.agent/memory/system_facts.md")

# Line 11-13 - After
_PROJECT_ROOT = Path(__file__).parent.parent.parent
WORKSPACE_ROOT = Path(os.environ.get("ORION_WORKSPACE_ROOT", str(_PROJECT_ROOT.parent.parent)))
ORION_MEMORY = _PROJECT_ROOT / ".agent/memory/system_facts.md"
```

#### File 11: `/home/palantir/park-kyungchan/palantir/scripts/runtime/planning_hook.py`

```python
# Line 26 - Current
PROJECT_LEVEL_AGENT = Path("/home/palantir/park-kyungchan/palantir/.agent")

# Line 26 - After
PROJECT_LEVEL_AGENT = Path(__file__).parent.parent.parent / ".agent"
```

#### File 12: `/home/palantir/park-kyungchan/palantir/scripts/claude/session_health.py`

```python
# Line 160-181 - Current
            workspace_root or os.getenv("ORION_WORKSPACE_ROOT", "/home/palantir")
        ...
        self.agent_tmp = self.workspace_root / "park-kyungchan/palantir/.agent/tmp"

# Line 160-181 - After
_PROJECT_ROOT = Path(__file__).parent.parent.parent
...
            workspace_root or os.getenv("ORION_WORKSPACE_ROOT", str(_PROJECT_ROOT.parent.parent))
        ...
        self.agent_tmp = Path(_PROJECT_ROOT) / ".agent/tmp"
```

#### File 13: `/home/palantir/park-kyungchan/palantir/scripts/claude/session_teleport.py`

```python
# Line 150-262 - Current
            workspace_root or os.getenv("ORION_WORKSPACE_ROOT", "/home/palantir")
        ...
            session_dir or self.workspace_root / "park-kyungchan/palantir/.agent/tmp/sessions"
        ...
        git_context = GitContext.from_repo(str(self.workspace_root / "park-kyungchan/palantir"))
        ...
            / f"park-kyungchan/palantir/.agent/tmp/evidence_{self.current_session_id}.jsonl"

# Line 150-262 - After
_PROJECT_ROOT = Path(__file__).parent.parent.parent
...
            workspace_root or os.getenv("ORION_WORKSPACE_ROOT", str(_PROJECT_ROOT.parent.parent))
        ...
            session_dir or _PROJECT_ROOT / ".agent/tmp/sessions"
        ...
        git_context = GitContext.from_repo(str(_PROJECT_ROOT))
        ...
            / f".agent/tmp/evidence_{self.current_session_id}.jsonl"
```

#### File 14: `/home/palantir/park-kyungchan/palantir/scripts/ontology/storage/database.py`

```python
# Line 220 - Current
        default_path = "/home/palantir/park-kyungchan/palantir/data/ontology.db"

# Line 220 - After
        default_path = str(Path(__file__).parent.parent.parent.parent / "data/ontology.db")
```

#### File 15: `/home/palantir/park-kyungchan/palantir/scripts/ontology/relays/result_job_job-test-01.py`

```python
# Line 21 - Current
    checked_path = "/home/palantir"

# Line 21 - After
    checked_path = str(Path(__file__).parent.parent.parent.parent.parent)
```

#### File 16: `/home/palantir/park-kyungchan/palantir/scripts/build_ontology.sh`

```bash
# Line 15 - Current
/home/palantir/.venv/bin/datamodel-codegen \

# Line 28 - Current
    /home/palantir/.venv/bin/datamodel-codegen \

# After - Use relative or environment variable
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
"${VIRTUAL_ENV:-$HOME/.venv}/bin/datamodel-codegen" \
```

---

## 3. sys.path Manipulation Files

### 3.1 Complete List (17 Locations in 14 Files)

#### Location 1: `/home/palantir/park-kyungchan/palantir/tests/e2e/test_monolith.py`

```python
# Line 13 - Current
sys.path.append("/home/palantir/park-kyungchan/palantir")

# Line 13 - After (REMOVE - use conftest.py fixture or pyproject.toml)
# Removed - imports should work via proper package configuration
```

#### Location 2: `/home/palantir/park-kyungchan/palantir/tests/e2e/test_v3_production.py`

```python
# Line 9 - Current
sys.path.append("/home/palantir/park-kyungchan/palantir")

# Line 9 - After (REMOVE)
# Removed - imports should work via proper package configuration
```

#### Location 3: `/home/palantir/park-kyungchan/palantir/tests/e2e/test_v3_full_stack.py`

```python
# Line 7 - Current
sys.path.append("/home/palantir/park-kyungchan/palantir")

# Line 7 - After (REMOVE)
# Removed - imports should work via proper package configuration
```

#### Location 4: `/home/palantir/park-kyungchan/palantir/scripts/maintenance/rebuild_db.py`

```python
# Line 9 - Current
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))

# Line 9 - After (KEEP - relative path computation is acceptable)
# Keep as is - uses relative path, not hardcoded
```

#### Location 5: `/home/palantir/park-kyungchan/palantir/scripts/consolidate.py`

```python
# Line 11 - Current
sys.path.append(WORKSPACE_ROOT)

# Line 11 - After (REFACTOR)
_PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(_PROJECT_ROOT))
```

#### Location 6: `/home/palantir/park-kyungchan/palantir/scripts/orion`

```python
# Line 1 - Current
import sys; import os; sys.path.append(os.getcwd()); from scripts.runtime.kernel import OrionRuntime; import asyncio; asyncio.run(OrionRuntime().start())

# Line 1 - After (REFACTOR to proper entrypoint)
#!/usr/bin/env python3
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
from scripts.runtime.kernel import OrionRuntime
import asyncio
asyncio.run(OrionRuntime().start())
```

#### Location 7: `/home/palantir/park-kyungchan/palantir/scripts/memory/recall.py`

```python
# Line 9 - Current
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))

# Line 9 - After (KEEP - relative path)
# Keep as is - uses relative path
```

#### Location 8: `/home/palantir/park-kyungchan/palantir/scripts/runtime/kernel.py`

```python
# Line 14 - Current
    sys.path.insert(0, _PROJECT_ROOT)

# Line 14 - After (KEEP - _PROJECT_ROOT should be computed relatively)
# Verify _PROJECT_ROOT is computed relatively
```

#### Location 9: `/home/palantir/park-kyungchan/palantir/scripts/ontology/run_tutor.py`

```python
# Line 27 - Current
    sys.path.insert(0, str(_PROJECT_ROOT))

# Line 27 - After (KEEP - verify _PROJECT_ROOT computation)
# Keep if _PROJECT_ROOT = Path(__file__).parent.parent.parent
```

#### Location 10: `/home/palantir/park-kyungchan/palantir/scripts/simulation/complex_mission.py`

```python
# Line 8 - Current
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

# Line 8 - After (KEEP - relative path)
# Keep as is - uses relative path
```

#### Location 11: `/home/palantir/park-kyungchan/palantir/scripts/ontology/relays/result_job_job-test-01.py`

```python
# Line 14 - Current
sys.path.append("/home/palantir/park-kyungchan/palantir")

# Line 14 - After (REFACTOR)
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))
```

#### Location 12: `/home/palantir/park-kyungchan/palantir/scripts/ontology/actions/learning_kb_actions.py`

```python
# Line 282 - Current
            sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / "coding"))

# Line 282 - After (KEEP - relative path)
# Keep as is - uses relative path
```

#### Location 13: `/home/palantir/park-kyungchan/palantir/scripts/ontology/fde_learning/actions.py`

```python
# Line 36 - Current
    sys.path.insert(0, _CODING_PATH)

# Line 36 - After (KEEP - verify _CODING_PATH computation)
# Keep if _CODING_PATH is computed relatively
```

#### Location 14: `/home/palantir/park-kyungchan/palantir/scripts/ontology/learning/verify_persistence_quick.py`

```python
# Line 6 - Current
sys.path.append(str(Path("/home/palantir/park-kyungchan/palantir")))

# Line 6 - After (REFACTOR)
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))
```

#### Location 15: `/home/palantir/park-kyungchan/palantir/scripts/ontology/learning/verify_scoping_quick.py`

```python
# Line 5 - Current
sys.path.append(str(Path("/home/palantir/park-kyungchan/palantir")))

# Line 5 - After (REFACTOR)
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))
```

#### Location 16: `/home/palantir/park-kyungchan/palantir/scripts/ontology/learning/verify_metrics_quick.py`

```python
# Line 7 - Current
sys.path.append(str(Path("/home/palantir/park-kyungchan/palantir")))

# Line 7 - After (REFACTOR)
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))
```

#### Location 17: `/home/palantir/park-kyungchan/palantir/scripts/ontology/learning/verify_full_engine.py`

```python
# Line 5 - Current
sys.path.append(str(Path("/home/palantir/park-kyungchan/palantir")))

# Line 5 - After (REFACTOR)
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))
```

---

## 4. Test File Impact Analysis

### 4.1 E2E Tests (11 Files)

| File | Import Lines | Affected Modules |
|------|--------------|------------------|
| `/home/palantir/park-kyungchan/palantir/tests/e2e/test_monolith.py` | 13, 15 | sys.path, scripts.api |
| `/home/palantir/park-kyungchan/palantir/tests/e2e/test_v3_production.py` | 9, 11-15, 55, 125 | sys.path, ontology, llm, relay, runtime |
| `/home/palantir/park-kyungchan/palantir/tests/e2e/test_v3_full_stack.py` | 7, 9-12, 72, 105 | sys.path, ontology, llm, relay |
| `/home/palantir/park-kyungchan/palantir/tests/e2e/test_proposal_repository.py` | 27, 33-34 | ontology.objects, ontology.storage |
| `/home/palantir/park-kyungchan/palantir/tests/e2e/test_e2e_golden_path.py` | 8-29, 82, 117, 200 | ontology, osdk, data, aip_logic, runtime |
| `/home/palantir/park-kyungchan/palantir/tests/e2e/test_full_integration.py` | 41-62, 148 | ontology |
| `/home/palantir/park-kyungchan/palantir/tests/e2e/test_occ_integration.py` | 26-34 | ontology |
| `/home/palantir/park-kyungchan/palantir/tests/e2e/test_oda_v3_scenarios.py` | 28-59 | ontology, llm |

### 4.2 Unit Tests (12 Files)

| File | Import Lines | Affected Modules |
|------|--------------|------------------|
| `/home/palantir/park-kyungchan/palantir/tests/unit/actions/test_llm_actions.py` | 12-13 | ontology.actions |
| `/home/palantir/park-kyungchan/palantir/tests/unit/actions/test_memory_actions.py` | 12-13 | ontology.actions |
| `/home/palantir/park-kyungchan/palantir/tests/unit/actions/test_learning_actions.py` | 12-13 | ontology.actions |
| `/home/palantir/park-kyungchan/palantir/tests/unit/actions/test_logic_actions.py` | 12-13 | ontology.actions |
| `/home/palantir/park-kyungchan/palantir/tests/unit/ontology/test_proposal_fsm.py` | 18 | ontology.objects |
| `/home/palantir/park-kyungchan/palantir/tests/unit/agent/test_executor.py` | 13-18, 158, 165 | agent, ontology.actions |
| `/home/palantir/park-kyungchan/palantir/tests/unit/storage/test_database_config.py` | 23 | ontology.storage |
| `/home/palantir/park-kyungchan/palantir/tests/unit/kb/test_kb_index_and_match.py` | 9-10 | ontology.kb |
| `/home/palantir/park-kyungchan/palantir/tests/unit/learning/test_multilang_tutoring_engine.py` | 11-12 | ontology.learning, ontology.run_tutor |
| `/home/palantir/park-kyungchan/palantir/tests/unit/learning/test_prompt_scope.py` | 12-14 | ontology.learning, ontology.run_tutor |
| `/home/palantir/park-kyungchan/palantir/tests/unit/learning/test_workflow_artifacts.py` | 5-7 | ontology.learning |
| `/home/palantir/park-kyungchan/palantir/tests/unit/learning/test_learning_brief.py` | 3 | ontology.learning |

### 4.3 Other Tests (4 Files)

| File | Import Lines | Affected Modules |
|------|--------------|------------------|
| `/home/palantir/park-kyungchan/palantir/tests/aip_logic/test_logic_function.py` | 5-6 | aip_logic |
| `/home/palantir/park-kyungchan/palantir/tests/data/test_pipeline.py` | 5 | data |
| `/home/palantir/park-kyungchan/palantir/tests/osdk/test_generator.py` | 3 | osdk |
| `/home/palantir/park-kyungchan/palantir/tests/osdk/test_query_integration.py` | 3-5 | osdk, ontology |
| `/home/palantir/park-kyungchan/palantir/tests/conftest.py` | 15-16, 127 | ontology.actions, ontology.storage |

### 4.4 Recommended Test Configuration

```python
# /home/palantir/park-kyungchan/palantir/tests/conftest.py - Add at top
import sys
from pathlib import Path

# Ensure project root is in path for all tests
PROJECT_ROOT = Path(__file__).parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
```

---

## 5. Circular Dependency Resolution Plan

### 5.1 ontology <-> cognitive

**Current Dependency Chain:**
```
ontology.run_tutor.py (line 30)
    -> from scripts.cognitive.engine import AdaptiveTutoringEngine

cognitive.learner.py (lines 5-9)
    -> from scripts.ontology.objects.learning import Learner
    -> from scripts.ontology.storage.learner_repository import LearnerRepository
    -> from scripts.ontology.actions.learning_actions import SaveLearnerStateAction
    -> from scripts.ontology.storage.database import get_database

cognitive.engine.py (lines 7-8, 64)
    -> from scripts.ontology.learning.scoping import ScopingEngine
    -> from scripts.ontology.learning.engine import TutoringEngine
    -> from scripts.ontology.learning.metrics import analyze_file
```

**Resolution Strategy:**
1. **Extract Interface Layer:**
   ```
   scripts/interfaces/learning_interfaces.py
       - AbstractTutoringEngine
       - AbstractLearnerManager
       - LearnerState (dataclass, no dependencies)
   ```

2. **Dependency Inversion:**
   ```python
   # ontology.run_tutor.py
   from scripts.interfaces.learning_interfaces import AbstractTutoringEngine

   def get_engine() -> AbstractTutoringEngine:
       from scripts.cognitive.engine import AdaptiveTutoringEngine
       return AdaptiveTutoringEngine()
   ```

3. **Lazy Import Pattern:**
   ```python
   # cognitive.learner.py
   def _get_learner_class():
       from scripts.ontology.objects.learning import Learner
       return Learner
   ```

### 5.2 ontology <-> aip_logic

**Current Dependency Chain:**
```
ontology.actions.logic_actions.py (lines 7-8)
    -> from scripts.aip_logic.engine import LogicEngine
    -> from scripts.aip_logic.registry import get_logic_function

aip_logic has NO reverse dependency on ontology (CLEAN)
```

**Resolution Strategy:**
- **No circular dependency exists** - aip_logic is a clean dependency
- Keep current structure, just convert to relative imports

### 5.3 ontology <-> infrastructure

**Current Dependency Chain:**
```
ontology.actions.side_effects.py (line 151)
    -> from scripts.infrastructure.event_bus import EventBus

ontology.storage.base_repository.py (line 46)
    -> from scripts.infrastructure.event_bus import EventBus

infrastructure.metrics.py (line 32)
    -> from scripts.ontology.storage.proposal_repository import ProposalRepository
```

**Resolution Strategy:**
1. **Extract Event Protocol:**
   ```python
   # scripts/interfaces/event_protocol.py
   from typing import Protocol

   class EventPublisher(Protocol):
       async def publish(self, event: "DomainEvent") -> None: ...
   ```

2. **Dependency Injection:**
   ```python
   # ontology.storage.base_repository.py
   from scripts.interfaces.event_protocol import EventPublisher

   class GenericRepository:
       def __init__(self, event_bus: EventPublisher | None = None):
           self._event_bus = event_bus
   ```

3. **Factory Pattern for Metrics:**
   ```python
   # infrastructure.metrics.py - lazy load
   def _get_proposal_repo():
       from scripts.ontology.storage.proposal_repository import ProposalRepository
       return ProposalRepository
   ```

### 5.4 Recommended Resolution Order

1. **Phase 1: Create Interface Layer**
   - `/home/palantir/park-kyungchan/palantir/scripts/interfaces/__init__.py`
   - `/home/palantir/park-kyungchan/palantir/scripts/interfaces/learning_interfaces.py`
   - `/home/palantir/park-kyungchan/palantir/scripts/interfaces/event_protocol.py`

2. **Phase 2: Update ontology First**
   - Convert all `from scripts.ontology.` imports within ontology to relative imports
   - Apply lazy import pattern for external dependencies

3. **Phase 3: Update Dependent Modules**
   - cognitive -> relative imports + interface usage
   - infrastructure -> relative imports + lazy loading
   - aip_logic -> relative imports (no circular issues)

4. **Phase 4: Update All Remaining Modules**
   - api, agent, claude, runtime, etc.

5. **Phase 5: Test Files**
   - Update conftest.py with proper path configuration
   - Remove all hardcoded sys.path manipulations from test files

---

## Summary Statistics

| Category | Count |
|----------|-------|
| Total files with `from scripts.` imports | 120+ |
| Hardcoded path files | 16 |
| sys.path manipulation locations | 17 |
| Test files affected | 27 |
| Circular dependency pairs | 2 (ontology-cognitive, ontology-infrastructure) |

---

## Migration Execution Checklist

- [ ] Create interface layer (`scripts/interfaces/`)
- [ ] Update ontology module (core - 40+ files)
- [ ] Update cognitive module (4 files)
- [ ] Update infrastructure module (2 files)
- [ ] Update aip_logic module (4 files)
- [ ] Update remaining modules (50+ files)
- [ ] Fix hardcoded paths (16 files)
- [ ] Fix sys.path manipulations (17 locations)
- [ ] Update test configuration
- [ ] Run full test suite
- [ ] Verify all imports work from clean environment
