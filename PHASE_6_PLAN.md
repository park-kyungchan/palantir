# Phase 6: The Consolidation Engine (Implementation Plan)

## 1. Objective
Implement the "Orion Insight Engine" to transform raw Episodic Logs (Traces) into Semantic Knowledge (Insights/Patterns) using **Zero-Dependency** algorithms.

## 2. Architecture: The Insight Pipeline
The pipeline operates in 4 stages, executed ideally during "Sleep Cycles" (Maintenance Windows).

```mermaid
graph TD
    A[Raw Traces (.json)] -->|Flatten & Canonicalize| B(Transactions)
    B -->|FP-Growth (Pure Python)| C(Frequent Patterns)
    C -->|Cluster Sampling| D{TextRank}
    D -->|Semantic Summary| E[New Insight Object]
    E -->|MemoryManager| F[Long-Term Memory]
```

## 3. Implementation Steps

### Step 3.1: The Mathematical Core (`scripts/lib/`)
Implement the algorithms defined in the Deep Research.
*   `scripts/lib/preprocessing.py`:
    *   `flatten_json(nested_dict)`: Recursive generator.
    *   `generate_signature(obj)`: SHA-256 canonicalization.
    *   `tokenize(text)`: Regex-based tokenizer.
*   `scripts/lib/fpgrowth.py`:
    *   `class FPNode`: Using `__slots__` for optimization.
    *   `class FPTree`: Tree construction and Mining logic.
*   `scripts/lib/textrank.py`:
    *   `cosine_similarity(vec1, vec2)`: Sparse vector math.
    *   `pagerank(graph)`: Power method solver.

### Step 3.2: The Consolidation Script (`scripts/consolidate.py`)
orchestrates the pipeline:
1.  **Ingest**: Load all `.json` files from `.agent/traces/`.
2.  **Transform**: Convert traces to flattened transactions.
3.  **Mine**: Find patterns with `support > 0.1` (10%).
4.  **Synthesize**: Create `Insight` objects for high-confidence patterns.
5.  **Store**: Save via `MemoryManager`.

### Step 3.3: Integration
*   Register only the high-level `consolidate_memory` action in `scripts/actions.py` (which wraps `subprocess.run(["python", "scripts/consolidate.py"])` or calls a main function).

## 4. Execution Command
```bash
python3 scripts/consolidate.py --lookback 24h
```

## 5. Verification
1.  Inject 5 artificial "Failure" traces with similar structure.
2.  Run `consolidate.py`.
3.  Verify a new `Pattern` object ("Frequent Failure X") is created in Memory.
