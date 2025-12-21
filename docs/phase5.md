# Orion Adaptive Tutoring Engine: Phase 5 Blueprint

The Codebase-as-Curriculum Architecture transforms live source code into personalized teaching material through three interlocking systems: a diagnostic protocol that gauges learner expertise through Socratic dialogue, a scoping algorithm that selects files matching the learner's Zone of Proximal Development, and a real-time curriculum generator that decomposes source files into interactive micro-lessons. This blueprint synthesizes cognitive load theory, knowledge tracing research, and modern LLM capabilities into a concrete implementation framework for Python/TypeScript codebases using Pydantic models and governance workflows.

---

## The mathematics of teaching complexity

Before an adaptive tutor can route learners to appropriate content, it must mathematically quantify how difficult each source file is to understand. Research reveals that **teaching complexity is multi-dimensional**—no single metric captures pedagogical difficulty. The Orion engine should compute a composite Teaching Complexity Score (TCS) combining five factors weighted for educational relevance.

**The composite formula:**

```
TCS = 0.30 × Cognitive_Complexity_normalized
    + 0.25 × Dependency_Depth_ratio
    + 0.20 × Novel_Concept_density
    + 0.15 × Domain_Pattern_weight
    + 0.10 × Halstead_Difficulty_normalized
```

**Cognitive Complexity** (SonarSource method) improves upon McCabe's cyclomatic complexity by penalizing nested structures—research confirms nested code imposes exponentially higher cognitive load. Each control flow break (if/for/while/try) adds +1, with an additional +1 penalty per nesting level. A function with three nested loops scores dramatically higher than three sequential loops, matching how humans actually perceive difficulty.

**Dependency Depth** measures how far down the import chain a file sits. Files with zero internal dependencies (foundational types like `ontology_types.py`) get depth 0 and should be taught first. Files importing multiple internal modules (like `proposal_repository.py`) get higher depth scores. This leverages topological sorting—a learner encountering `proposal_repository.py` must first understand its transitive dependencies.

**Novel Concept density** counts unique programming constructs per 100 lines: new classes, decorators, design patterns, framework-specific idioms. A file introducing Pydantic validators, async/await, and custom descriptors simultaneously overloads working memory. Miller's research established working memory handles **7±2 chunks**; files exceeding this threshold require scaffolding.

For the Orion ODA codebase specifically, **domain pattern weights** should assign higher complexity to:

| Pattern | Weight | Rationale |
|---------|--------|-----------|
| Repository pattern | 5 | Integration layer abstraction |
| Proposal workflows | 4 | Stateful governance logic |
| ActionType | 3 | Command pattern with validation |
| Pydantic BaseModel | 2 | Foundational but framework-specific |
| Enums | 1 | Straightforward type definitions |

Applying this formula to your codebase would classify `ontology_types.py` (enums, base types, few dependencies) as **Intermediate (TCS ~25)** while `proposal_repository.py` (repository pattern, async operations, multiple imports) lands at **Advanced (TCS ~55)**.

---

## The Diagnosis Protocol: Assessment without examinations

Traditional assessments fail in adaptive tutoring contexts—they're slow, anxiety-inducing, and reveal what learners memorized rather than what they understand. The Orion engine should implement **conversational assessment** that infers learner expertise from dialogue about actual code.

### The four-phase diagnostic exchange

**Phase 1: Open Exploration (1-2 exchanges)**

The agent presents a code snippet without framing it as a test:

```
Agent: "Let's look at this Proposal model together. What catches your eye 
about how version tracking is handled here?"
```

This low-pressure opener establishes baseline vocabulary, conceptual framing, and confidence signals. A learner mentioning "immutable state transitions" reveals different expertise than one saying "it has a version number." Parse responses for:

- Technical terminology density
- Conceptual abstraction level (describes *what* vs explains *why*)
- Confidence markers ("I think..." vs "This clearly...")

Initialize the ability estimate θ using the learner's background as prior—a mathematics education background suggests analytical capability (θ₀ ≈ 0.5) but potentially limited domain vocabulary.

**Phase 2: Targeted Probing (2-4 exchanges)**

Based on Phase 1, select questions from a difficulty-calibrated pool using **Item Response Theory**. Each question has pre-computed difficulty (b) and discrimination (a) parameters. The CAT algorithm selects questions maximizing information gain at the current θ estimate.

High-understanding path:
```
Agent: "Good observation about immutability. What failure modes would you 
anticipate if concurrent services attempted version updates simultaneously?"
```

Gap-detected path:
```
Agent: "I notice you mentioned the version field—can you trace what 
happens when updateProposal() is called? Walk me through the data flow."
```

The **Socratic questioning taxonomy** guides probe design:

- *Clarification*: "What do you mean when you say the proposal 'changes state'?"
- *Assumption probing*: "What would happen if we removed the validator decorator?"
- *Evidence seeking*: "How do you know this method will raise an exception?"
- *Implication exploring*: "If we modify `Proposal.version` here, what downstream effects occur?"

**Phase 3: Misconception Detection (1-2 exchanges)**

Probe for documented programming misconceptions. Research identifies common categories: reference-vs-value confusion, mutation timing errors, and scope misunderstandings. For FDE patterns specifically:

```
Agent: "Some developers set version numbers from client calls rather than 
server-side. What's your instinct on where version assignment should 
happen, and why?"
```

The response reveals whether the learner understands optimistic locking, conflict resolution, and distributed systems constraints—or harbors misconceptions about client authority.

**Phase 4: Calibration Synthesis (1 exchange)**

```
Agent: "Based on our discussion, you seem comfortable with Pydantic 
validation patterns but might benefit from more work on repository-level 
transaction boundaries. Does that match your own sense?"
```

This meta-cognitive check validates the assessment and builds trust. Learner self-reports correlate meaningfully with actual performance when framed as collaborative reflection rather than judgment.

### Knowledge state representation

Maintain a Bayesian knowledge model for each **Knowledge Component (KC)** in the curriculum:

```json
{
  "learner_id": "user_123",
  "knowledge_components": {
    "pydantic_validation": {
      "p_mastery": 0.78,
      "theta": 1.2,
      "last_assessed": "2025-12-21T14:30:00Z",
      "evidence_count": 4,
      "misconception_flags": []
    },
    "proposal_governance": {
      "p_mastery": 0.42,
      "theta": -0.3,
      "last_assessed": "2025-12-21T14:35:00Z",
      "evidence_count": 2,
      "misconception_flags": ["version_client_authority"]
    }
  }
}
```

Update probabilities using **Bayesian Knowledge Tracing**. When a learner demonstrates understanding, P(mastery) increases based on prior probability and slip rate. When they reveal gaps, P(mastery) decreases based on guess probability. The four BKT parameters should be initialized from population data then personalized:

- **P(L₀)**: Initial mastery probability (0.3 default, adjust for background)
- **P(T)**: Learning rate (0.2 default, higher for math-educated learners)
- **P(G)**: Guess probability (0.1 for open-ended code questions)
- **P(S)**: Slip probability (0.15 for complex domain questions)

---

## The Scoping Algorithm: Selecting the right files

Zone of Proximal Development theory states optimal learning occurs when material is **10-30% beyond current capability**—challenging enough to require effort, achievable enough to prevent frustration. The scoping algorithm must select files falling within this zone.

### ZPD-based file selection

```python
def calculate_zpd_suitability(
    file_tcs: float, 
    learner_level: float,
    prerequisite_mastery: float
) -> float:
    """
    Returns 0-1 score indicating file's fit for learner's ZPD.
    Higher scores = better learning candidates.
    """
    stretch = (file_tcs - learner_level) / max(learner_level, 1)
    
    # Zone classification
    if stretch < 0.05:
        # Too easy: Zone of Actual Development
        base_score = 0.25
    elif 0.10 <= stretch <= 0.30:
        # Optimal: Zone of Proximal Development
        base_score = 1.0
    elif 0.30 < stretch <= 0.50:
        # Challenging but reachable with scaffolding
        base_score = 0.65
    else:
        # Zone of Frustration
        base_score = 0.15
    
    # Prerequisite penalty: Can't learn X without mastering dependencies
    prereq_penalty = (1.0 - prerequisite_mastery) * 0.5
    
    return max(0, base_score - prereq_penalty)
```

### Dependency-aware sequencing

Before applying ZPD selection, the algorithm must respect **prerequisite constraints**. A learner cannot productively study `proposal_repository.py` without first mastering what `ontology_types.py` exports.

**Step 1: Build the import dependency graph**

Parse all Python files, extracting import statements via AST analysis. Create a directed graph where edges point from dependent files to their dependencies.

**Step 2: Topological sort for valid orderings**

```python
def get_learning_order(dependency_graph: dict) -> list:
    """Return files in valid learning sequence (prerequisites first)."""
    in_degree = defaultdict(int)
    for file, deps in dependency_graph.items():
        for dep in deps:
            in_degree[file] += 1
    
    # Start with foundation files (no dependencies)
    queue = deque([f for f in dependency_graph if in_degree[f] == 0])
    order = []
    
    while queue:
        node = queue.popleft()
        order.append(node)
        for dependent in get_dependents(node, dependency_graph):
            in_degree[dependent] -= 1
            if in_degree[dependent] == 0:
                queue.append(dependent)
    
    return order
```

**Step 3: Filter by ZPD within valid orderings**

From the topologically-sorted list, select files where:
1. All prerequisites have mastery P > 0.7
2. ZPD suitability score > 0.5
3. No more than 3 novel concepts beyond current knowledge

This produces a **personalized reading list** respecting both pedagogical constraints and prerequisite dependencies.

### Practical file classification

For the Orion ODA codebase, the algorithm would produce classifications like:

| File | TCS | Dependencies | Learning Tier |
|------|-----|--------------|---------------|
| `ontology_types.py` | 22 | None | Foundation |
| `base_model.py` | 28 | ontology_types | Foundation |
| `action_type.py` | 35 | base_model, ontology_types | Intermediate |
| `proposal.py` | 48 | action_type, base_model | Intermediate+ |
| `proposal_repository.py` | 62 | proposal, async_utils | Advanced |
| `governance_workflow.py` | 71 | proposal_repository, action_type | Expert |

A new learner starts at Foundation tier. As diagnostic exchanges confirm mastery (P > 0.8), the agent unlocks Intermediate files, always ensuring prerequisites are met.

---

## The Live Interaction Model: Files become lessons

The most innovative aspect of the Orion engine is transforming arbitrary source files into interactive tutorials in real-time. This requires a structured prompt architecture that decomposes code into pedagogically-sound micro-lessons.

### File-to-lesson prompt structure

When a learner is ready for a new file, the agent generates a lesson using this template:

```markdown
## System Context
You are the Orion Adaptive Tutor—a hyper-personalized senior mentor 
helping a developer with a Mathematics Education background understand 
the Orion ODA codebase. The learner has demonstrated mastery of 
{mastered_concepts} and is ready to learn {target_concepts}.

## Source Material
```python
{source_code}
```

## Lesson Generation Instructions
Create an interactive micro-lesson following this structure:

### 1. Learning Anchor (30 seconds)
Connect this code to something the learner already knows. For a 
math-educated learner, use analogies to mathematical structures 
(types as sets, validators as domain constraints, workflows as 
state machines).

### 2. Worked Example Walkthrough (3-5 minutes)
Walk through the code line-by-line, but organized by conceptual 
chunks rather than line numbers. Highlight:
- The problem this code solves
- Key design decisions and their rationale  
- How it integrates with previously-learned components

### 3. Conceptual Checkpoints (2 minutes)
Pause at critical junctures with Socratic questions:
- "Before I explain the validator, what would YOU expect it to check?"
- "Given what you know about Pydantic, why might we use Field() here?"

### 4. Practice Scaffold (5 minutes)
Present a faded worked example—partial code requiring learner completion:
- First attempt: Fill in one missing line
- Second attempt: Implement a small variation
- Third attempt: Extend with a new constraint

### 5. Integration Check
Ask: "How would you modify this if {realistic scenario}?" to verify 
transfer learning and identify remaining gaps.
```

### Interactive decomposition for `scripts/ontology/`

Applying the prompt structure to a typical ontology directory produces a curriculum like:

**Micro-Course: The Ontology System**

```
Lesson 1: Types as Contracts (ontology_types.py)
├── Duration: 10 minutes
├── Anchor: "Think of these Enums like the axioms in a mathematical 
│   system—they define what's possible before any theorems (operations)"
├── Worked Example: Trace how OntologyCategory constrains downstream code
├── Checkpoint: "Why is 'UNKNOWN' included? What happens without it?"
├── Practice: Add a new category and predict validation behavior
└── Prerequisites: Python classes, type hints

Lesson 2: The Base Model Pattern (base_model.py)
├── Duration: 12 minutes
├── Anchor: "A BaseModel is like a vector space—it defines the structure 
│   that all instances must inhabit"
├── Worked Example: Field definitions, validators, Config class
├── Checkpoint: "What would break if we removed frozen=True?"
├── Practice: Create a model with cross-field validation
└── Prerequisites: Lesson 1

Lesson 3: Actions as Encapsulated Transformations (action_type.py)
├── Duration: 15 minutes
├── Anchor: "An ActionType is a morphism—a structure-preserving map 
│   between states"
├── Worked Example: Action execution flow, pre/post conditions
├── Checkpoint: "How does this differ from a plain function call?"
├── Practice: Implement an action with rollback capability
└── Prerequisites: Lessons 1-2

Lesson 4: Proposal Governance (proposal.py)
├── Duration: 18 minutes
├── Anchor: "The Proposal is a state machine—like a finite automaton 
│   where transitions are guarded by predicates"
├── Worked Example: State transitions, version tracking, approval flows
├── Checkpoint: "Why does version increment happen server-side?"
├── Practice: Add a new proposal state with appropriate guards
└── Prerequisites: Lessons 1-3
```

### Git-diff to lesson generation

When learners work with evolving codebases, git diffs become powerful teaching material. The agent can generate "change lessons" explaining what evolved and why:

```markdown
## Diff-to-Lesson Prompt

Given this commit:
```diff
{diff_content}
```

Commit message: "{commit_message}"

Generate a 5-minute micro-lesson explaining:
1. **What changed**: Identify added/modified/removed elements
2. **Why it changed**: Infer motivation from commit message and code context
3. **Impact analysis**: What other files might need updates?
4. **Learning moment**: What general principle does this change illustrate?
5. **Transfer question**: "If you needed to make a similar change to 
   {related_file}, what would you modify?"
```

This leverages version control history as curriculum—each meaningful commit becomes a potential lesson about software evolution, refactoring patterns, or feature implementation.

---

## Implementation architecture

The complete Orion Adaptive Tutoring Engine integrates these components:

```
┌─────────────────────────────────────────────────────────────────────┐
│                     ORION ADAPTIVE TUTORING ENGINE                  │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────────────┐  │
│  │   AST        │    │  Dependency  │    │  Teaching            │  │
│  │   Parser     │───▶│  Graph       │───▶│  Complexity          │  │
│  │              │    │  Builder     │    │  Calculator          │  │
│  └──────────────┘    └──────────────┘    └──────────┬───────────┘  │
│                                                      │              │
│                                                      ▼              │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │                    LEARNER MODEL                              │  │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐       │  │
│  │  │ BKT         │  │ IRT θ        │  │ Misconception │       │  │
│  │  │ P(mastery)  │  │ Estimates    │  │ Flags         │       │  │
│  │  └──────────────┘  └──────────────┘  └──────────────┘       │  │
│  └──────────────────────────────────────────────────────────────┘  │
│                              │                                      │
│                              ▼                                      │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │                    ZPD SCOPING ENGINE                         │  │
│  │  • Topological sort for prerequisite ordering                │  │
│  │  • ZPD suitability scoring                                   │  │
│  │  • Personalized file queue generation                        │  │
│  └──────────────────────────────────────────────────────────────┘  │
│                              │                                      │
│                              ▼                                      │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │                 CURRICULUM GENERATOR                          │  │
│  │  ┌────────────────┐  ┌────────────────┐  ┌────────────────┐  │  │
│  │  │ File-to-Lesson │  │ Diff-to-Lesson │  │ Worked Example │  │  │
│  │  │ Prompts        │  │ Prompts        │  │ Generator      │  │  │
│  │  └────────────────┘  └────────────────┘  └────────────────┘  │  │
│  └──────────────────────────────────────────────────────────────┘  │
│                              │                                      │
│                              ▼                                      │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │               DIALOGUE MANAGER                                │  │
│  │  • Socratic questioning engine                               │  │
│  │  • Response evaluation pipeline                              │  │
│  │  • Adaptive hint generation                                  │  │
│  │  • Misconception detection                                   │  │
│  └──────────────────────────────────────────────────────────────┘  │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### Core data flows

1. **Initialization**: Parse codebase → Build dependency graph → Calculate TCS for all files → Generate curriculum skeleton

2. **Diagnosis Loop**: Present code snippet → Ask Socratic question → Evaluate response → Update BKT probabilities → Select next probe OR determine readiness

3. **Learning Loop**: Select ZPD-appropriate file → Generate lesson from template → Present worked example → Scaffold practice → Assess understanding → Update learner model

4. **Adaptation Triggers**: 
   - P(mastery) > 0.85 → Unlock next complexity tier
   - Misconception detected → Insert remediation lesson
   - Confidence drop detected → Reduce question difficulty
   - Three successful completions → Fade scaffolding level

---

## Conclusion: The living syllabus

The Orion Adaptive Tutoring Engine reimagines code education by treating source files as primary teaching material rather than abstract examples. The **Teacher Algorithm** quantifies pedagogical difficulty through composite metrics grounded in cognitive load theory. The **Diagnostic Protocol** replaces examinations with Socratic dialogue that reveals understanding through conversation about real code. The **Live Interaction Model** transforms any file or commit into structured micro-lessons adapted to the learner's mathematical background.

Three key innovations distinguish this architecture from static tutorials:

**Dependency-aware sequencing** ensures learners never encounter files requiring concepts they haven't mastered. Unlike linear curricula, the topological ordering respects the actual structure of the codebase.

**Zone of Proximal Development targeting** selects files at optimal challenge levels—challenging enough to promote growth, achievable enough to maintain engagement. The 10-30% stretch principle from educational psychology becomes a mathematical constraint in file selection.

**Real-time curriculum generation** means the syllabus emerges from the codebase itself. When developers add new features, the tutoring engine can immediately generate lessons explaining the changes. The curriculum is never out of date because it's derived from the source of truth.

For a learner with a mathematics education background approaching the Orion ODA codebase, this architecture provides what traditional documentation cannot: a personalized path through complex material, with mathematical analogies (types as sets, validators as constraints, workflows as state machines) that leverage existing expertise while building new capabilities in Palantir FDE patterns.