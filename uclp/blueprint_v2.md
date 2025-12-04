# 🏗️ Blueprint: UCLP v2.0 (Palantir Ontology Edition)

## 1. Ontology Definition

We define 3 Core Object Types to replace the monolithic JSON.

### 1.1 Object: `Concept`
Represents a programming concept (e.g., "Variable Declaration").
- **primaryKey**: `concept_id` (string, e.g., `variable_declaration`)
- **properties**:
  - `name`: string
  - `category`: string (e.g., `basics`)
  - `prerequisites`: string[] (Link to other Concepts)
  - `related_concepts`: string[]

### 1.2 Object: `Language`
Represents a programming language supported by the protocol.
- **primaryKey**: `language_id` (string, e.g., `python`)
- **properties**:
  - `name`: string
  - `philosophy_summary`: string
  - `idiomatic_patterns`: object[] (List of patterns)

### 1.3 Object: `Implementation`
Represents how a Concept is implemented in a Language.
- **primaryKey**: `impl_id` (UUID)
- **links**:
  - `concept_id`: Link -> Concept
  - `language_id`: Link -> Language
- **properties**:
  - `syntax_template`: string
  - `design_rationale`: string
  - `code_snippet`: string
  - `sources`: object[]

## 2. Directory Structure (Refactoring Target)

```
/home/palantir/uclp/
├── ontology/                 # The "Database"
│   ├── schemas/              # JSON Schemas for Objects
│   │   ├── concept.schema.json
│   │   ├── language.schema.json
│   │   └── implementation.schema.json
│   └── data/                 # The "Records"
│       ├── concepts/         # One JSON per Concept
│       ├── languages/        # One JSON per Language
│       └── implementations/  # One JSON per Impl
├── src/                      # The "Logic"
│   ├── api/                  # Python/TS API to query Ontology
│   └── generator/            # Response Generator
└── legacy/                   # Old files (to be archived)
```

## 3. Migration Plan (Executor Tasks)

1.  **Scaffold:** Create the new directory structure.
2.  **Schema:** Define the 3 JSON Schemas.
3.  **Migrate:** Write a script (`scripts/migrate_uclp.py`) to parse `uclp-reference.json` and split it into thousands of atomic JSON files in `ontology/data/`.
4.  **Verify:** Ensure no data loss during splitting.
