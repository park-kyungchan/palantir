# Palantir FDE Learning - Full Context Quick Loader

**Purpose**: Compressed document for AI Agent to quickly load full project context at conversation start
**Last Updated**: 2025-12-31
**Version**: 2.0 (16 LearningDomains)

---

## 1. Core Philosophy (3 Sentences)

1. **Real-Time Dynamic Design**: When learner asks questions or provides a project, design learning path on-the-fly
2. **Dynamic Curriculum Adjustment**: Adjust based on discovered weaknesses, combining KB content + external resources
3. **Interactive Project Decomposition**: Questions allowed at file/code level, handled via AI conversation

---

## 2. Project Structure

```
/home/palantir/orion-orchestrator-v2/coding/
├── palantir_fde_learning/           # Python package
│   ├── domain/types.py              # LearningDomain(16), DifficultyTier, LearningConcept
│   ├── application/scoping.py       # ScopingEngine (ZPD recommendations)
│   └── adapters/kb_reader.py        # KB parsing
├── palantir-fde-learning/           # Learning content
│   ├── knowledge_bases/             # 11 KBs
│   └── SYSTEM_DIRECTIVE.md          # 7-component response protocol
├── HANDOFF_FULL_CONTEXT.md          # Full context document
├── DEEP_RESEARCH_PROMPT.md          # External agent prompt
└── CONTEXT_LOADER.md                # ← This file
```

---

## 3. LearningDomain (16 Actual Palantir Products)

| Category | Domains |
|----------|---------|
| **Core Platform** | FOUNDRY, AIP, ONTOLOGY |
| **AIP Features** | AIP_LOGIC, AIP_AGENT_STUDIO, AIP_EVALS |
| **Foundry Apps** | WORKSHOP, QUIVER, SLATE, CODE_REPOSITORIES, PIPELINE_BUILDER, DATA_CONNECTION |
| **Developer Tools** | OSDK, FUNCTIONS, ACTIONS |
| **UI/UX** | BLUEPRINT |

---

## 4. Knowledge Base Mapping (11 KBs)

| KB | File | LearningDomain Mapping |
|----|------|------------------------|
| 00 | palantir_core_architecture.md | FOUNDRY, ONTOLOGY |
| 01 | language_foundation.md | (general) |
| 02 | react_ecosystem.md | BLUEPRINT, WORKSHOP |
| 03 | styling_systems.md | BLUEPRINT |
| 04 | data_layer.md | OSDK, FUNCTIONS, ACTIONS, DATA_CONNECTION |
| 05 | testing_pyramid.md | (general) |
| 06 | build_tooling.md | CODE_REPOSITORIES, PIPELINE_BUILDER |
| 07 | version_control.md | (general) |
| 08 | advanced_capabilities.md | QUIVER, SLATE |
| 09 | orion_system_architecture.md | (internal) |
| 10 | visual_glossary.md | (reference) |

**Gap**: No dedicated KB for AIP, AIP_LOGIC, AIP_AGENT_STUDIO, AIP_EVALS → Deep Research needed

---

## 5. Dynamic Design Protocol

### 5.1 Project Decomposition Request
```
Learner: "Analyze this project" + path
     ↓
Agent: Directory structure analysis (list_dir)
     ↓
Agent: Identify key files and code-level analysis (view_file, view_code_item)
     ↓
Agent: LearningDomain mapping + KB linking
     ↓
Agent: Present learning points (7-component format)
```

### 5.2 Code Question
```
Learner: "What is this function?" + file/function name
     ↓
Agent: Code analysis (view_code_item)
     ↓
Agent: Reference relevant KB (read_file)
     ↓
Agent: 7-component response (Universal Concept, Technical, Cross-Stack, Palantir Context, Philosophy, Exercise, Next Steps)
```

### 5.3 Dynamic Adjustment
```
Learner: "I don't understand" or weakness discovered
     ↓
Agent: Determine adjustment scope (narrow/medium/wide)
     ↓
If wide: Combine KB + external resources (web_search)
     ↓
Agent: Generate supplementary learning path on-the-fly
```

---

## 6. 7-Component Response Structure (Required)

For every learning question:

1. **Universal Concept**: Language/framework-agnostic core principle
2. **Technical Explanation**: Executable code examples
3. **Cross-Stack Comparison**: TS/Java/Python comparison table
4. **Palantir Context**: Actual Blueprint/OSDK/Foundry usage
5. **Design Philosophy**: Creator quotes (Anders Hejlsberg, Dan Abramov, etc.)
6. **Practice Exercise**: Interview-level coding task
7. **Adaptive Next Steps**: Wait for learner response (no unsolicited suggestions)

---

## 7. Quick Context Check

At conversation start, Agent should verify:

- [ ] Is this conversation FDE learning related?
- [ ] Did learner request project decomposition?
- [ ] Is this question related to a specific LearningDomain?
- [ ] Does this question require 7-component response?

---

## 8. Frequently Used Commands

```bash
# List KBs
ls /home/palantir/orion-orchestrator-v2/coding/palantir-fde-learning/knowledge_bases/

# Python package structure
ls /home/palantir/orion-orchestrator-v2/coding/palantir_fde_learning/

# Check LearningDomain
head -120 /home/palantir/orion-orchestrator-v2/coding/palantir_fde_learning/domain/types.py
```

---

**End of Context Loader**
