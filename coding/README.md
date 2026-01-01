# Palantir FDE Learning System

> Personalized interview preparation system for Palantir Frontend Development Engineer (FDE) roles.

[![CI](https://github.com/YOUR_USERNAME/palantir-fde-learning/actions/workflows/ci.yml/badge.svg)](https://github.com/YOUR_USERNAME/palantir-fde-learning/actions/workflows/ci.yml)
![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue)
![Coverage](https://img.shields.io/badge/coverage-59%25-yellow)

---

## Features

- **Bayesian Knowledge Tracing (BKT)** - Accurate mastery estimation based on learner responses
- **Zone of Proximal Development (ZPD)** - Personalized concept recommendations
- **Knowledge Base Parser** - Structured markdown KB with 7-section format
- **CLI Tools** - Profile management, recommendations, and KB exploration
- **Clean Architecture** - Domain-driven design with clear layer separation
- **ODA Integration** - Connects with Orion Orchestrator via ActionTypes

---

## Quick Start

### Installation

```bash
# Clone and install
cd palantir-fde-learning
pip install -e ".[dev]"

# Verify installation
fde-learn --help
```

### Basic Usage

```bash
# Create a learner profile
fde-learn profile init my-profile

# Get personalized recommendations
fde-learn recommend --profile my-profile --count 5

# List knowledge bases
fde-learn kb list

# View a specific KB
fde-learn kb show osdk_typescript
```

### Python API

```python
from palantir_fde_learning.domain import LearnerProfile, get_bkt_model, BKTState

# Create profile
profile = LearnerProfile(learner_id="candidate_001")

# Track mastery with BKT
bkt = get_bkt_model("interview")  # Strict params for FDE prep
state = BKTState()

# Record attempts
state = bkt.update(state, correct=True)
state = bkt.update(state, correct=True)
state = bkt.update(state, correct=False)
state = bkt.update(state, correct=True)

print(f"Mastery: {state.mastery:.1%}")  # ~68.7%
print(f"Mastered: {state.is_mastered}")  # False
```

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        CLI Layer                            │
│                  (fde-learn commands)                       │
├─────────────────────────────────────────────────────────────┤
│                    Application Layer                        │
│              ScopingEngine, ZPDRecommendation               │
├─────────────────────────────────────────────────────────────┤
│                      Domain Layer                           │
│      LearnerProfile, KnowledgeComponentState, BKTModel      │
├─────────────────────────────────────────────────────────────┤
│                     Adapters Layer                          │
│         SQLiteLearnerRepository, KBReader                   │
└─────────────────────────────────────────────────────────────┘
```

### Clean Architecture Layers

| Layer | Purpose | Dependencies |
|-------|---------|--------------|
| **Domain** | Core entities, BKT | None (pure Python) |
| **Application** | Use cases, ZPD | Domain |
| **Adapters** | Persistence, KB parsing | Application, Domain |
| **CLI** | User interface | All layers |

---

## Knowledge Base Format

KBs use a standardized 7-section markdown format:

```markdown
# Topic Title

[metadata]
domain = osdk
difficulty = intermediate
estimated_time = 45

## Prerequisites
- Basic TypeScript knowledge

## Core Concepts
...

## Examples
...

## Common Pitfalls
...

## Best Practices
...

## References
...
```

---

## BKT Parameter Presets

| Preset | P(L0) | P(T) | P(S) | P(G) | Use Case |
|--------|-------|------|------|------|----------|
| `default` | 0.00 | 0.10 | 0.10 | 0.25 | Balanced |
| `easy` | 0.10 | 0.30 | 0.05 | 0.20 | Easy concepts |
| `difficult` | 0.00 | 0.05 | 0.15 | 0.10 | Hard concepts |
| `interview` | 0.00 | 0.08 | 0.12 | 0.10 | FDE preparation |

---

## Development

### Setup

```bash
# Install with dev dependencies
pip install -e ".[dev]"

# Run tests
pytest tests/ -v --cov=palantir_fde_learning

# Run linter
ruff check palantir_fde_learning/

# Run type checker
mypy palantir_fde_learning/
```

### Examples

```bash
# Run example scripts
python examples/basic_profile.py
python examples/bkt_mastery.py
python examples/zpd_recommendations.py
```

---

## Project Structure

```
palantir-fde-learning/
├── palantir_fde_learning/
│   ├── domain/          # Core entities & BKT
│   ├── application/     # Use cases & ZPD
│   ├── adapters/        # Persistence & KB
│   └── cli/             # Click commands
├── knowledge_bases/     # 19 Palantir domain KBs
├── tests/               # 78 unit tests
├── examples/            # Usage examples
└── .github/             # CI/CD workflows
```

---

## Integration with Orion ODA

The system integrates with the Orion Orchestrator via ActionTypes:

```python
# scripts/ontology/fde_learning/actions.py
@register_action
class RecordAttemptAction(ActionType[LearnerObject]):
    api_name = "fde.record_attempt"
    # ... BKT-based mastery update
```

Available ActionTypes:
- `fde.record_attempt` - Record learning attempt
- `fde.get_recommendation` - Get ZPD recommendations
- `fde.sync_learner_state` - Sync with Orion (hazardous)

---

## License

MIT License - See [LICENSE](LICENSE) for details.
