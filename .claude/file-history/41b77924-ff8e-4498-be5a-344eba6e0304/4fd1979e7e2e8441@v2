# PAI → ODA Python Migration Plan

## Executive Summary

**Goal:** Migrate PAI (Personal AI Infrastructure) TypeScript components to ODA (Ontology-Driven Architecture) Python system.

**Strategy:** 4-Phase Parallel Migration with full Claude Code V2.1.x feature utilization

**Timeline:** Phases run in parallel with background subagents

---

## Architecture Overview

### Source (PAI - TypeScript/Bun)
```
/home/palantir/PAI/Packs/
├── pai-algorithm-skill/     → Universal Algorithm, ISC, Effort Levels
├── pai-agents-skill/        → 28-Trait Composition System
├── pai-hook-system/         → Event-Driven Hooks
└── pai-prompting-skill/     → Skill Routing
```

### Target (ODA - Python/Pydantic)
```
/home/palantir/park-kyungchan/palantir/lib/oda/
├── ontology/objects/        → ObjectType definitions
├── ontology/actions/        → ActionType implementations
├── ontology/protocols/      → 3-Stage Protocol
├── infrastructure/          → Event bus, metrics
└── pai/                     → NEW: Migrated PAI modules
    ├── algorithm/
    ├── traits/
    ├── hooks/
    └── skills/
```

---

## Phase 1: Algorithm Migration

### New Files
```
lib/oda/pai/algorithm/
├── __init__.py
├── effort_levels.py         # EffortLevel enum
├── isc_manager.py           # ISC table management
├── capability_registry.py   # Capability definitions
└── universal_algorithm.py   # Current→Ideal logic
```

### ObjectTypes
| Name | Description | Key Fields |
|------|-------------|------------|
| `EffortLevel` | Effort classification enum | TRIVIAL, QUICK, STANDARD, THOROUGH, DETERMINED |
| `ISCTable` | Ideal State Criteria table | request, effort, phase, iteration, rows[] |
| `ISCRow` | Individual ISC row | id, description, source, status, parallel, capability |
| `Capability` | Registered capability | name, effort_min, model, use_when |
| `CapabilityCategory` | Category grouping | models, thinking, debate, analysis, research, execution |

### ActionTypes
| Name | Hazardous | Description |
|------|-----------|-------------|
| `CreateISCAction` | No | Create new ISC table |
| `AddISCRowAction` | No | Add row to ISC |
| `UpdateISCStatusAction` | No | Update row status |
| `SetISCPhaseAction` | No | Transition phase |
| `SelectCapabilityAction` | No | Select capability for row |
| `VerifyISCAction` | No | Verify row completion |

### Key Mappings
```python
# PAI TypeScript → ODA Python
EffortLevel.TRIVIAL  → EffortLevel.TRIVIAL   # Direct enum mapping
ISCRow.parallel      → ISCRow.can_parallel   # Boolean for parallel execution
Capability.effort_min → Capability.min_effort # Minimum effort threshold
```

---

## Phase 2: Trait Composition Migration

### New Files
```
lib/oda/pai/traits/
├── __init__.py
├── dimensions.py            # Expertise, Personality, Approach enums
├── trait_definition.py      # TraitDefinition ObjectType
├── voice_mapping.py         # Voice resolution system
├── composition_factory.py   # AgentCompositionFactory
└── named_agents.py          # Persistent agent identities
```

### ObjectTypes
| Name | Description | Key Fields |
|------|-------------|------------|
| `ExpertiseType` | 10 expertise areas | security, legal, finance, medical, technical, research, creative, business, data, communications |
| `PersonalityDimension` | 10 personality types | skeptical, enthusiastic, cautious, bold, analytical, creative, empathetic, contrarian, pragmatic, meticulous |
| `ApproachStyle` | 8 approach styles | thorough, rapid, systematic, exploratory, comparative, synthesizing, adversarial, consultative |
| `TraitDefinition` | Trait metadata | trait_id, name, keywords[], prompt_fragment |
| `VoiceRegistry` | TTS voice definition | voice_name, voice_id, characteristics[], stability, similarity_boost |
| `TraitVoiceMapping` | Multi-trait → voice | traits[], voice_name, reason |
| `AgentPersona` | Composed agent | name, traits, assigned_voice, voice_id, full_prompt |
| `NamedAgentDefinition` | Persistent agent | agent_id, display_name, archetype, backstory, voice_id |

### ActionTypes
| Name | Hazardous | Description |
|------|-----------|-------------|
| `ComposeAgentAction` | No | Create agent from traits |
| `InferTraitsAction` | No | Infer traits from task text |
| `ResolveVoiceAction` | No | Resolve voice from traits |
| `RegisterNamedAgentAction` | No | Register persistent agent |

### Voice Resolution Algorithm
```python
# Priority order:
1. Check explicit combination mappings (full match wins)
2. Check fallbacks (single trait wins)
3. Default voice
```

---

## Phase 3: Hook System Integration

### New Files
```
lib/oda/pai/hooks/
├── __init__.py
├── event_types.py           # HookEventType enum
├── hook_definition.py       # HookDefinition ObjectType
├── hook_registry.py         # Dynamic hook registration
├── observability.py         # Dashboard integration
└── security_validator.py    # Security checks
```

### ObjectTypes
| Name | Description | Key Fields |
|------|-------------|------------|
| `HookEventType` | Hook event enum | PreToolUse, PostToolUse, Stop, SubagentStop, UserPromptSubmit, SessionStart, SessionEnd |
| `HookDefinition` | Hook configuration | event, matcher, command, description, priority |
| `HookExecution` | Execution record | hook_id, event_type, input, output, duration_ms, success |
| `ObservabilityEvent` | Observability payload | event_type, source_app, timestamp, metadata |

### ActionTypes
| Name | Hazardous | Description |
|------|-----------|-------------|
| `RegisterHookAction` | No | Register new hook |
| `ExecuteHookAction` | No | Execute hook command |
| `LogObservabilityAction` | No | Send to observability |
| `ValidateSecurityAction` | No | Run security checks |

### Integration with ODA EventBus
```python
# Map PAI hooks to ODA DomainEvent
HookEventType.PreToolUse   → "Tool.pre_execute"
HookEventType.PostToolUse  → "Tool.post_execute"
HookEventType.Stop         → "Agent.stopped"
HookEventType.SubagentStop → "Subagent.stopped"
```

---

## Phase 4: Skill Routing Migration

### New Files
```
lib/oda/pai/skills/
├── __init__.py
├── skill_definition.py      # SkillDefinition ObjectType
├── trigger_detector.py      # Keyword-based routing
├── workflow.py              # Workflow execution
└── router.py                # Skill router
```

### ObjectTypes
| Name | Description | Key Fields |
|------|-------------|------------|
| `SkillDefinition` | Skill metadata | name, description, triggers[], tools[], model |
| `SkillTrigger` | Trigger condition | keywords[], patterns[], context_match |
| `Workflow` | Multi-step workflow | name, steps[], validation |
| `WorkflowStep` | Single step | order, action_type, params, success_criteria |
| `SkillExecution` | Execution record | skill_name, input, output, duration_ms |

### ActionTypes
| Name | Hazardous | Description |
|------|-----------|-------------|
| `DetectSkillTriggerAction` | No | Detect matching skill |
| `RouteToSkillAction` | No | Route to skill handler |
| `ExecuteWorkflowAction` | No | Execute workflow steps |
| `RegisterSkillAction` | Yes | Register new skill (schema change) |

---

## Parallel Execution Strategy

### Phases Can Run in Parallel
All 4 phases can execute simultaneously because:
- Phase 1 (Algorithm): No dependencies on other phases
- Phase 2 (Traits): No dependencies on other phases
- Phase 3 (Hooks): No dependencies on other phases
- Phase 4 (Skills): No dependencies on other phases

### Shared Dependencies
```yaml
shared:
  - lib/oda/ontology/ontology_types.py   # OntologyObject base
  - lib/oda/ontology/registry.py         # @register_object_type
  - lib/oda/ontology/actions/__init__.py # ActionType base
  - lib/oda/infrastructure/event_bus.py  # DomainEvent
```

### Subagent Deployment Pattern
```python
# Use run_in_background=true for parallel phases
Task(subagent_type="general-purpose",
     prompt="Implement Phase 1: Algorithm Migration",
     run_in_background=True)
Task(subagent_type="general-purpose",
     prompt="Implement Phase 2: Traits Migration",
     run_in_background=True)
Task(subagent_type="general-purpose",
     prompt="Implement Phase 3: Hooks Migration",
     run_in_background=True)
Task(subagent_type="general-purpose",
     prompt="Implement Phase 4: Skills Migration",
     run_in_background=True)
```

---

## Critical Files to Modify

### New Directory Structure
```bash
mkdir -p lib/oda/pai/{algorithm,traits,hooks,skills}
touch lib/oda/pai/__init__.py
```

### Files to Create (28 total)
```
Phase 1 (5 files):
- lib/oda/pai/algorithm/__init__.py
- lib/oda/pai/algorithm/effort_levels.py
- lib/oda/pai/algorithm/isc_manager.py
- lib/oda/pai/algorithm/capability_registry.py
- lib/oda/pai/algorithm/universal_algorithm.py

Phase 2 (6 files):
- lib/oda/pai/traits/__init__.py
- lib/oda/pai/traits/dimensions.py
- lib/oda/pai/traits/trait_definition.py
- lib/oda/pai/traits/voice_mapping.py
- lib/oda/pai/traits/composition_factory.py
- lib/oda/pai/traits/named_agents.py

Phase 3 (6 files):
- lib/oda/pai/hooks/__init__.py
- lib/oda/pai/hooks/event_types.py
- lib/oda/pai/hooks/hook_definition.py
- lib/oda/pai/hooks/hook_registry.py
- lib/oda/pai/hooks/observability.py
- lib/oda/pai/hooks/security_validator.py

Phase 4 (5 files):
- lib/oda/pai/skills/__init__.py
- lib/oda/pai/skills/skill_definition.py
- lib/oda/pai/skills/trigger_detector.py
- lib/oda/pai/skills/workflow.py
- lib/oda/pai/skills/router.py

Tests (6 files):
- tests/unit/pai/test_algorithm.py
- tests/unit/pai/test_traits.py
- tests/unit/pai/test_hooks.py
- tests/unit/pai/test_skills.py
- tests/e2e/test_pai_integration.py
- tests/e2e/test_pai_workflow.py
```

---

## Verification Strategy

### Unit Tests
```bash
# Run after each phase completion
pytest tests/unit/pai/test_algorithm.py -v
pytest tests/unit/pai/test_traits.py -v
pytest tests/unit/pai/test_hooks.py -v
pytest tests/unit/pai/test_skills.py -v
```

### Integration Tests
```bash
# Run after all phases complete
pytest tests/e2e/test_pai_integration.py -v
```

### Quality Gates
1. **Schema Validation**: All ObjectTypes pass registry validation
2. **Action Validation**: All ActionTypes pass quality gate
3. **Type Checking**: `mypy lib/oda/pai/` passes
4. **Linting**: `ruff check lib/oda/pai/` passes
5. **Evidence Collection**: All tests include files_viewed evidence

### Manual Verification
```python
# Test trait composition
from lib.oda.pai.traits import AgentCompositionFactory
factory = AgentCompositionFactory()
agent = factory.compose_from_traits(
    expertise=ExpertiseType.SECURITY,
    personality=PersonalityDimension.SKEPTICAL,
    approach=ApproachStyle.ADVERSARIAL,
    task_description="Security audit"
)
print(agent.assigned_voice)  # Should be "Intense"

# Test ISC management
from lib.oda.pai.algorithm import ISCManager
isc = ISCManager.create("Implement feature X", EffortLevel.STANDARD)
isc.add_row("Design API", source="EXPLICIT")
isc.set_phase("PLAN")
```

---

## Risks and Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| TypeScript→Python semantic loss | Medium | Document all type mappings explicitly |
| Voice API incompatibility | Low | Abstract voice layer, mock for tests |
| Circular imports | Medium | Use TYPE_CHECKING for forward refs |
| EventBus integration conflicts | Medium | Use separate event namespace (pai.*) |
| Effort level granularity mismatch | Low | Map PAI levels to ODA equivalents |

---

## Implementation Order (Within Each Phase)

### Recommended Order
1. **Enums and Constants** first (no dependencies)
2. **ObjectTypes** second (depend on enums)
3. **ActionTypes** third (depend on ObjectTypes)
4. **Integration logic** last (depend on Actions)

### Phase 1 Order
```
1. effort_levels.py     # EffortLevel enum
2. capability_registry.py # Capability, CapabilityCategory
3. isc_manager.py       # ISCTable, ISCRow, ISC actions
4. universal_algorithm.py # Integration logic
```

---

## Success Criteria

- [ ] All 28 files created and passing linting
- [ ] 100% ObjectType schema validation passing
- [ ] All ActionTypes passing quality gate
- [ ] Unit tests for each phase (>80% coverage)
- [ ] Integration test demonstrating full workflow
- [ ] Documentation updated in CLAUDE.md
- [ ] No circular import errors
- [ ] EventBus integration verified

---

## Next Steps

1. **Approve this plan** - Confirm scope and approach
2. **Create directory structure** - `mkdir -p lib/oda/pai/{algorithm,traits,hooks,skills}`
3. **Deploy 4 parallel subagents** - One per phase
4. **Monitor progress** - Use TodoWrite for tracking
5. **Run verification** - After all phases complete
6. **Update CLAUDE.md** - Document new PAI integration

---

*Generated by Orion ODA Orchestrator using Claude Code V2.1.3*
*Date: 2026-01-10*
