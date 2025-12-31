# Palantir FDE Learning Project - Full Context Handoff Document

**Created**: 2025-12-31
**Purpose**: Full-Context-Injected document for external agent Deep Research
**Target**: Palantir Deployment Strategist / FDE learning system enhancement

---

## 1. Project Overview

### 1.1 Location
```
/home/palantir/orion-orchestrator-v2/coding/
├── palantir_fde_learning/     # Python package (core code)
└── palantir-fde-learning/     # Learning content (KB documents)
```

### 1.2 Purpose
- **Palantir FDE position preparation coding learning system**
- **Agile and Real-Time Dynamic Design** philosophy based
- Supports **interactive project decomposition learning** via AI conversation

### 1.3 Core Philosophy
| Principle | Description |
|-----------|-------------|
| Real-Time Dynamic Design | When learner asks or provides project, design learning path on-the-fly |
| Dynamic Curriculum Adjustment | Adjust based on discovered weaknesses (scope: KB internal + external resources) |
| No Codification Needed | AI conversation capability is sufficient, no additional infrastructure needed |

---

## 2. Python Package Structure (palantir_fde_learning/)

### 2.1 Clean Architecture Structure
```
palantir_fde_learning/
├── __init__.py              # 29 lines - package entry point
├── domain/
│   └── types.py             # 399 lines - core domain types
├── application/
│   └── scoping.py           # 410 lines - ZPD recommendation engine
└── adapters/
    └── kb_reader.py         # 489 lines - KB file reader
```

---

## 3. Core Code Details

### 3.1 LearningDomain (domain/types.py:58-108)
**16 domains based on actual Palantir products (2024-2025)**

```python
class LearningDomain(str, Enum):
    # CORE PLATFORM
    FOUNDRY = "foundry"              # Palantir Foundry platform
    AIP = "aip"                      # AI Platform (LLM integration)
    ONTOLOGY = "ontology"            # Ontology (core data modeling)

    # AIP FEATURES
    AIP_LOGIC = "aip_logic"          # No-code AI function builder
    AIP_AGENT_STUDIO = "aip_agent_studio"  # AI agents
    AIP_EVALS = "aip_evals"          # AI evaluation system

    # FOUNDRY APPLICATIONS
    WORKSHOP = "workshop"            # No-code app builder
    QUIVER = "quiver"               # Ontology-based analytics
    SLATE = "slate"                 # Custom app builder
    CODE_REPOSITORIES = "code_repositories"  # Web IDE
    PIPELINE_BUILDER = "pipeline_builder"    # Data pipelines
    DATA_CONNECTION = "data_connection"      # External data sync

    # DEVELOPER TOOLS
    OSDK = "osdk"                    # Ontology SDK 2.0
    FUNCTIONS = "functions"          # TypeScript/Python Functions
    ACTIONS = "actions"              # Ontology Actions

    # UI/UX
    BLUEPRINT = "blueprint"          # React design system
```

### 3.2 DifficultyTier (domain/types.py:22-55)
**Bloom's Taxonomy based difficulty**
- BEGINNER: Knowledge & Comprehension
- INTERMEDIATE: Application & Analysis
- ADVANCED: Synthesis & Evaluation

### 3.3 LearningConcept (domain/types.py:111-207)
**Learning concept entity**
```python
class LearningConcept(BaseModel):
    concept_id: str  # Format: "osdk.beginner.installation"
    domain: LearningDomain
    difficulty_tier: DifficultyTier
    prerequisites: list[str]  # DAG structure
    title: str
    description: Optional[str]
    estimated_minutes: int  # 5-480 minutes
    tags: list[str]
```

### 3.4 KnowledgeComponentState (domain/types.py:210-330)
**BKT-based mastery tracking**
- mastery_level: 0.0 ~ 1.0 (70%+ = mastered)
- record_attempt(): Record learning attempt and update mastery

### 3.5 LearnerProfile (domain/types.py:333-398)
**Learner profile**
- knowledge_states: Dict[concept_id, KnowledgeComponentState]
- overall_mastery(): Total mastery average
- get_stale_concepts(): Concepts needing review

### 3.6 ScopingEngine (application/scoping.py)
**ZPD-based learning recommendation engine**
```python
class ScopingEngine:
    OPTIMAL_STRETCH_MIN = 0.10  # Minimum stretch
    OPTIMAL_STRETCH_MAX = 0.30  # Maximum stretch
    MASTERY_THRESHOLD = 0.70    # Mastery threshold

    def recommend_next_concept() -> list[ZPDRecommendation]
    def get_learning_path(target_concept_id) -> list[LearningConcept]
    def get_domain_progress(domain) -> dict
```

### 3.7 KBReader (adapters/kb_reader.py)
**KB markdown parsing**
- 7-component section extraction
- YAML frontmatter parsing
- LearningConcept auto-generation

---

## 4. Knowledge Base Content (palantir-fde-learning/knowledge_bases/)

### 4.1 KB List (11 files)
| KB | Filename | Size | Topic |
|----|----------|------|-------|
| 00 | palantir_core_architecture.md | 4KB | Palantir architecture (gold standard) |
| 01 | language_foundation.md | 30KB | JS/TS fundamentals |
| 02 | react_ecosystem.md | 31KB | React, Blueprint, Redoodle |
| 03 | styling_systems.md | 37KB | CSS, Sass, Theming |
| 04 | data_layer.md | 37KB | OSDK, GraphQL, React Query |
| 05 | testing_pyramid.md | 33KB | Jest, RTL, Playwright |
| 06 | build_tooling.md | 34KB | Webpack, Vite, Gradle |
| 07 | version_control.md | 33KB | Git, Monorepo |
| 08 | advanced_capabilities.md | 30KB | Visualization, Performance |
| 09 | orion_system_architecture.md | 7KB | ODA V3 (Orion architecture) |
| 10 | visual_glossary.md | 6KB | Visual glossary |

### 4.2 KB Structure (7-Component)
Each KB includes the following sections:
1. Universal Concept / Overview
2. Technical Explanation / Deep Dive
3. Cross-Stack Comparison
4. Palantir Context
5. Design Philosophy
6. **Practice Exercise** (required)
7. **Adaptive Next Steps** (required)

---

## 5. Current State Assessment

### 5.1 LearningDomain Mapping Status

| Domain | KB Coverage | Status |
|--------|-------------|--------|
| FOUNDRY | KB 00 | ✅ Basic description exists |
| AIP | - | ❌ **No KB** |
| ONTOLOGY | KB 04 partial | ⚠️ Partial |
| AIP_LOGIC | - | ❌ **No KB** |
| AIP_AGENT_STUDIO | - | ❌ **No KB** |
| AIP_EVALS | - | ❌ **No KB** |
| WORKSHOP | KB 00 partial | ⚠️ Partial |
| QUIVER | - | ❌ **No KB** |
| SLATE | - | ❌ **No KB** |
| CODE_REPOSITORIES | - | ❌ **No KB** |
| PIPELINE_BUILDER | - | ❌ **No KB** |
| DATA_CONNECTION | KB 04 partial | ⚠️ Partial |
| OSDK | KB 04 | ✅ Detailed description exists |
| FUNCTIONS | KB 04 partial | ⚠️ Partial |
| ACTIONS | KB 04 partial | ⚠️ Partial |
| BLUEPRINT | KB 02, 03 | ✅ Detailed description exists |

### 5.2 Gap Analysis
**Missing core Palantir product KBs**:
1. **AIP dedicated KB** (AIP, AIP Logic, Agent Studio, Evals)
2. **Foundry Apps KB** (Workshop detail, Quiver, Slate, Code Repos, Pipeline Builder)
3. **Data Connection KB** (External data sync detail)

---

## 6. Deep Research Request

### 6.1 Objective
For each LearningDomain:
1. **Accurate feature description** based on Palantir official docs
2. **FDE interview relevance** assessment
3. **KB creation or enhancement** requirement determination

### 6.2 Research Priority
| Priority | Domain | Reason |
|----------|--------|--------|
| P1 | AIP, AIP_LOGIC | 2024-2025 core features |
| P1 | AIP_AGENT_STUDIO | AI agent trend |
| P2 | OSDK | FDE developer essential |
| P2 | ONTOLOGY | Palantir differentiation core |
| P3 | Other Foundry Apps | Supporting tools |

### 6.3 Expected Output
For each domain:
```markdown
## [Domain Name]
### Official Definition (Palantir Docs based)
### FDE Interview Relevance (High/Medium/Low)
### Current KB Status (Missing/Partial/Sufficient)
### Recommended Action (Create new KB/Enhance/Maintain)
### Key Learning Points (3-5 items)
```

---

## 7. Reference Resources

### 7.1 Palantir Official Docs
- https://www.palantir.com/docs/foundry/
- https://www.palantir.com/docs/foundry/aip/overview/
- https://www.palantir.com/docs/foundry/ontology-sdk/

### 7.2 2024-2025 Release Notes
- AIP Logic Evaluations (2024)
- OSDK 2.0 (November 2024)
- AIP Agent Studio OSDK deployment (December 2024)

---

**End of Document**
