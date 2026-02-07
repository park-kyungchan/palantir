# Enhancing Claude Code CLI for Palantir Ontology Construction

Claude Code CLI provides a powerful extensible framework for building an automated Palantir Ontology scaffolding system. By combining **Skills** (modular capabilities), **Hooks** (validation gates), and **Subagent orchestration** (parallel workflows), you can create an interactive pipeline that transforms source code analysis into validated ObjectType definitions with Korean/English bilingual support.

## Claude Code CLI's native capabilities enable complex multi-step workflows

Claude Code CLI (v2.1.x) offers four key mechanisms for sophisticated automation:

**Skills System** provides modular, auto-discoverable capabilities. Each skill lives in a `SKILL.md` file with YAML frontmatter defining name, description, allowed tools, and model preferences. Skills use **progressive disclosure** at three levels: ~50 tokens for L1 metadata scanning, ~2,500 tokens for L2 full instructions when activated, and up to ~7,500 tokens for L3 reference files loaded on-demand. This architecture maps directly to Ontology scaffolding phases—L1 for candidate detection, L2 for property extraction, L3 for full validation schemas.

**Hook System** enables shift-left validation through event-based interception. The `PreToolUse` hook blocks operations before execution (exit code 2), while `PostToolUse` processes results afterward. Matchers support patterns like `"Edit|Write"` for multiple tools or `"mcp__ontology__*"` for custom MCP integrations. Critically, hooks can **modify inputs transparently**—receiving JSON via stdin and outputting modified JSON to stdout.

**Subagent Architecture** provides isolated context windows for parallel research. Built-in subagents include Explore (fast read-only with Haiku), General-Purpose (full tools with Sonnet), and Plan (research-focused). Custom subagents defined in `.claude/agents/` inherit configurable tool access, permission modes, and skill loading.

**Machine-Readable Output** supports `--output-format json` and `--output-format stream-json` for CI/CD integration, plus `--json-schema` for enforcing structured responses.

## Palantir's primary key design follows strict determinism principles

Palantir's official documentation establishes **non-negotiable requirements** for primary keys:

| Requirement | Rationale |
|-------------|-----------|
| **String type only** | Strings represent numbers, not vice versa; type migration is painful |
| **Deterministic generation** | If PK changes on rebuild, all edits are lost and links disappear |
| **Inherent uniqueness** | Constructed only from properties of the object instance itself |
| **No external dependencies** | Should not depend on other objects or runtime state |
| **Separate `id` column** | Always create dedicated PK column even if another unique column exists |

The recommended pattern uses readable composite keys with explicit delimiters:

```python
# GOOD: Deterministic composite key from stable columns
df = df.withColumn("primary_key", F.concat_ws(":", "customer_id", "order_date", "product_id"))

# OPTIONAL: Hash for uniform length (64 chars)
df = df.withColumn("primary_key", F.sha2(F.col("primary_key"), 256))
```

**Anti-patterns to avoid**: Row rank positions (change on insertion), runtime UUID generation (changes on rebuild), hashed IDs without readable composition (debugging nightmare), and inferring properties from ID structure (brittle assumption).

For **LinkTypes**, cardinality patterns require distinct implementation strategies:
- **One-to-Many**: Foreign key on "many" side pointing to "one" PK
- **Many-to-Many**: Requires dedicated join table dataset containing PK pairs
- **Object-Backed Links**: Uses third ObjectType to store relationship with additional metadata

## Machine-readable YAML structure for Claude Code CLI scaffolding

The schema follows JSON Schema draft 2020-12 for maximum tooling compatibility, implementing L1/L2/L3 progressive disclosure:

```yaml
# ontology-objecttype.schema.yaml
$schema: "https://json-schema.org/draft/2020-12/schema"
$id: "https://example.com/ontology-objecttype.schema.json"
title: "Palantir ObjectType Scaffolding Schema"
type: object

required:
  - apiVersion
  - kind
  - metadata
  - spec

properties:
  # === L1: Always loaded (~50 tokens) ===
  apiVersion:
    type: string
    const: "ontology.palantir.com/v1"
  kind:
    type: string
    enum: ["ObjectType", "LinkType", "ActionType"]
  metadata:
    $ref: "#/$defs/metadata"

  # === L2: Loaded on activation (~2,500 tokens) ===
  spec:
    type: object
    required: ["primaryKey", "properties"]
    properties:
      displayName:
        type: string
        maxLength: 256
      pluralDisplayName:
        type: string
      apiName:
        type: string
        pattern: "^[A-Z][a-zA-Z0-9]*$"
        description: "PascalCase, alphanumeric, unique across all object types"
      
      primaryKey:
        $ref: "#/$defs/primaryKeySpec"
      
      titleKey:
        type: string
        description: "Property used as display name for objects"
      
      properties:
        type: array
        items:
          $ref: "#/$defs/propertyDefinition"
        minItems: 1
      
      links:
        type: array
        items:
          $ref: "#/$defs/linkDefinition"

  # === L3: Heavy validation resources ===
  validation:
    $ref: "#/$defs/validationRules"

$defs:
  metadata:
    type: object
    required: ["name"]
    properties:
      name:
        type: string
        pattern: "^[a-z][a-z0-9-]*$"
        maxLength: 64
      description:
        type: string
        maxLength: 1024
      labels:
        type: object
        additionalProperties:
          type: string
      annotations:
        type: object
        properties:
          "palantir.com/status":
            type: string
            enum: ["experimental", "active", "deprecated"]
          "palantir.com/owner":
            type: string
            format: email

  primaryKeySpec:
    type: object
    required: ["propertyId", "strategy"]
    properties:
      propertyId:
        type: string
      strategy:
        type: string
        enum: ["single_column", "composite", "composite_hashed"]
      components:
        type: array
        items:
          type: string
        description: "For composite keys: ordered list of property IDs"
      delimiter:
        type: string
        default: ":"
        description: "Separator for composite keys"

  propertyDefinition:
    type: object
    required: ["id", "dataType"]
    properties:
      id:
        type: string
        pattern: "^[a-z][a-zA-Z0-9_]*$"
      displayName:
        type: string
      displayName_ko:
        type: string
        description: "Korean display name for bilingual support"
      dataType:
        type: string
        enum: ["string", "integer", "long", "short", "float", "double", 
               "boolean", "date", "timestamp", "array", "struct", 
               "geopoint", "geoshape", "vector"]
      required:
        type: boolean
        default: false
      primaryKeyEligible:
        type: boolean
      titleKeyEligible:
        type: boolean
      valueConstraints:
        $ref: "#/$defs/valueConstraints"

  valueConstraints:
    type: object
    properties:
      enum:
        type: array
        items:
          type: string
      range:
        type: object
        properties:
          min: {}
          max: {}
      regex:
        type: string
      uniqueness:
        type: boolean

  linkDefinition:
    type: object
    required: ["name", "targetObjectType", "cardinality"]
    properties:
      name:
        type: string
      apiName:
        type: string
      targetObjectType:
        type: string
      cardinality:
        type: string
        enum: ["one_to_one", "one_to_many", "many_to_one", "many_to_many"]
      foreignKeyProperty:
        type: string
        description: "For FK-based links: property holding target PK"
      joinTable:
        type: object
        description: "For M:M links: backing join table configuration"
        properties:
          datasetRid:
            type: string
          sourceKeyColumn:
            type: string
          targetKeyColumn:
            type: string

  validationRules:
    type: object
    properties:
      gates:
        type: array
        items:
          type: object
          properties:
            name:
              type: string
            stage:
              type: string
              enum: ["clarify", "research", "define", "validate"]
            type:
              type: string
              enum: ["automated", "manual", "approval"]
            rules:
              type: array
              items:
                type: object
                properties:
                  expr:
                    type: string
                  message:
                    type: string
                  message_ko:
                    type: string
```

## Validation gates at each workflow stage enforce Ontology integrity

The progressive refinement loop implements four stages with distinct validation checkpoints:

```yaml
# ontology-workflow-gates.yaml
workflow:
  stages:
    - name: clarify
      disclosure_level: L1
      gates:
        - name: source_validity
          type: automated
          rules:
            - expr: "has(input.source_paths) && size(input.source_paths) > 0"
              message: "At least one source path required"
              message_ko: "최소 하나의 소스 경로가 필요합니다"
            - expr: "input.domain_context != ''"
              message: "Domain context must be provided"
              message_ko: "도메인 컨텍스트를 제공해야 합니다"

    - name: research
      disclosure_level: L2
      gates:
        - name: candidate_extraction
          type: automated
          rules:
            - expr: "size(candidates.entities) >= 1"
              message: "At least one entity candidate must be identified"
              message_ko: "최소 하나의 엔티티 후보가 식별되어야 합니다"
            - expr: "candidates.entities.all(e, has(e.primary_key_candidate))"
              message: "All entities must have primary key candidates"
              message_ko: "모든 엔티티에 기본 키 후보가 있어야 합니다"

    - name: define
      disclosure_level: L2
      gates:
        - name: pk_determinism
          type: automated
          rules:
            - expr: "spec.primaryKey.strategy != '' && spec.primaryKey.propertyId != ''"
              message: "Primary key strategy and property must be defined"
              message_ko: "기본 키 전략과 속성이 정의되어야 합니다"
            - expr: "!spec.properties.exists(p, p.id == spec.primaryKey.propertyId && p.dataType != 'string')"
              message: "Primary key must be string type"
              message_ko: "기본 키는 문자열 타입이어야 합니다"
            - expr: "spec.properties.filter(p, p.id == spec.primaryKey.propertyId)[0].required == true"
              message: "Primary key property must be required (non-null)"
              message_ko: "기본 키 속성은 필수(non-null)여야 합니다"

        - name: link_integrity
          type: automated
          rules:
            - expr: "spec.links.all(l, l.cardinality != 'many_to_many' || has(l.joinTable))"
              message: "Many-to-many links require join table configuration"
              message_ko: "다대다 링크에는 조인 테이블 구성이 필요합니다"
            - expr: "spec.links.all(l, l.cardinality == 'many_to_many' || has(l.foreignKeyProperty))"
              message: "Non-M:M links require foreign key property"
              message_ko: "다대다가 아닌 링크에는 외래 키 속성이 필요합니다"

    - name: validate
      disclosure_level: L3
      gates:
        - name: semantic_consistency
          type: manual
          approvers: ["ontology-stewards@company.com"]
          timeout: "24h"
          checklist:
            - "ObjectType maps to natural-language business concept"
            - "Primary key is deterministic and immutable"
            - "All meaningful relationships are modeled as LinkTypes"
            - "Properties use appropriate data types"

        - name: final_review
          type: approval
          rules:
            - expr: "metadata.annotations['palantir.com/owner'] != ''"
              message: "Point of contact must be configured"
              message_ko: "담당자가 구성되어야 합니다"
```

## Interactive Q&A implements real-time reasoning for design decisions

The decision support workflow uses Inquirer.js-style prompts integrated with Claude Code skills:

```yaml
# SKILL.md for ontology-objecttype skill
---
name: ontology-objecttype
description: |
  Interactive ObjectType scaffolding for Palantir Foundry.
  Use when: user wants to create new ObjectType, analyze code for entities,
  or needs guidance on Ontology design decisions.
  Supports Korean (ko) and English (en) languages.
allowed-tools: Read, Grep, Glob, Bash
model: sonnet
---

# Ontology ObjectType Scaffolding

## Decision Tree Workflow

When the user invokes this skill, follow this interactive decision flow:

### Phase 1: Context Clarification (L1)
```
Q1: What is your source for this ObjectType?
    [a] Existing source code (분석할 소스 코드)
    [b] Database schema (데이터베이스 스키마)
    [c] Business requirements document (비즈니스 요구사항)
    [d] Manual definition (수동 정의)

Q2: What is the business domain? (비즈니스 도메인)
    → Free text input with validation
```

### Phase 2: Entity Discovery (L2)
```
IF source == "code":
    - Scan for @Entity, @AggregateRoot, class hierarchies
    - Extract candidate entities with properties
    - Present: "Found {n} entity candidates. Review? (Y/n)"

Q3: Primary Key Strategy (기본 키 전략):
    [a] Single existing column (단일 기존 컬럼)
    [b] Composite key (복합 키) → prompt for components
    [c] Generate new ID column (새 ID 컬럼 생성)
    
    VALIDATION: If user selects non-string type, warn:
    "⚠️ Primary keys must be string type. Convert to string? (Y/n)"
```

### Phase 3: Link Definition (L2)
```
Q4: Does this ObjectType have relationships? (관계 존재 여부)
    IF yes:
        Q4a: Target ObjectType? (대상 ObjectType)
        Q4b: Cardinality? (카디널리티)
            [a] One-to-One (1:1)
            [b] One-to-Many (1:N)
            [c] Many-to-One (N:1)
            [d] Many-to-Many (M:N) → auto-configure join table
```

### Phase 4: Validation & Output (L3)
- Run all validation gates
- Generate YAML scaffold
- Offer: "Generate PySpark pipeline code? (Y/n)"
```

## Reference: DataType Mapping Table

| Source Type | Palantir Type | PK Eligible | Notes |
|-------------|---------------|-------------|-------|
| string, varchar | string | ✅ | Recommended for PKs |
| int, integer | integer | ✅ | |
| bigint | long | ⚠️ | JS issues >1e15; use string |
| float, real | float | ❌ | |
| double | double | ❌ | |
| boolean | boolean | ⚠️ | Limits to 2 objects |
| date | date | ⚠️ | Format collision risk |
| datetime, timestamp | timestamp | ⚠️ | Storage vs display issues |
| json, jsonb | struct | ❌ | No nesting in OSv2 |
| array | array | ❌ | No null elements |
| point, geometry | geopoint/geoshape | ❌ | |
```

## Hook integration enables shift-left validation at every step

Configure hooks in `.claude/settings.json` to enforce Ontology integrity rules:

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Write|Edit",
        "hooks": [
          {
            "type": "command",
            "command": "python3 scripts/validate_ontology_yaml.py",
            "timeout": 30
          }
        ]
      }
    ],
    "PostToolUse": [
      {
        "matcher": "mcp__ontology__generate_*",
        "hooks": [
          {
            "type": "command",
            "command": "python3 scripts/post_generation_audit.py"
          }
        ]
      }
    ],
    "SubagentStop": [
      {
        "matcher": "*",
        "hooks": [
          {
            "type": "command",
            "command": "python3 scripts/aggregate_findings.py"
          }
        ]
      }
    ]
  }
}
```

The validation script enforces Palantir-specific rules:

```python
# scripts/validate_ontology_yaml.py
import sys
import json
import yaml
from jsonschema import validate, ValidationError

SCHEMA_PATH = ".claude/schemas/ontology-objecttype.schema.yaml"
PALANTIR_RULES = [
    ("Primary key must be string", 
     lambda s: s.get("spec", {}).get("properties", [{}])[0].get("dataType") == "string"
     if s.get("spec", {}).get("primaryKey", {}).get("propertyId") else True),
    ("API name must be PascalCase",
     lambda s: s.get("spec", {}).get("apiName", "A")[0].isupper()),
    ("M:M links require join table",
     lambda s: all(l.get("joinTable") for l in s.get("spec", {}).get("links", [])
                   if l.get("cardinality") == "many_to_many")),
]

def main():
    input_data = json.load(sys.stdin)
    file_path = input_data.get("tool_input", {}).get("file_path", "")
    
    if not file_path.endswith((".ontology.yaml", ".ontology.yml")):
        sys.exit(0)  # Not an ontology file, allow
    
    content = input_data.get("tool_input", {}).get("content", "")
    
    try:
        spec = yaml.safe_load(content)
        with open(SCHEMA_PATH) as f:
            schema = yaml.safe_load(f)
        validate(spec, schema)
        
        for rule_name, rule_fn in PALANTIR_RULES:
            if not rule_fn(spec):
                print(f"❌ Validation failed: {rule_name}", file=sys.stderr)
                sys.exit(2)  # Block the operation
        
        print("✅ Ontology validation passed")
        sys.exit(0)
        
    except ValidationError as e:
        print(f"❌ Schema validation failed: {e.message}", file=sys.stderr)
        sys.exit(2)

if __name__ == "__main__":
    main()
```

## Skills extension architecture for complete Ontology construction pipeline

Extend existing skills and add new ones organized in `.claude/skills/`:

```
.claude/
├── skills/
│   ├── ontology-core/
│   │   └── SKILL.md           # Base Ontology concepts, terminology
│   ├── ontology-objecttype/
│   │   ├── SKILL.md           # ObjectType scaffolding (enhanced)
│   │   ├── DECISION_TREE.md   # Interactive Q&A flow
│   │   └── DATATYPE_MAP.md    # Type conversion reference
│   ├── ontology-linktype/
│   │   ├── SKILL.md           # LinkType definition patterns
│   │   └── CARDINALITY.md     # Cardinality decision guide
│   ├── ontology-actiontype/
│   │   └── SKILL.md           # ActionType for workflows
│   ├── ontology-validate/
│   │   ├── SKILL.md           # Validation orchestration
│   │   └── RULES.md           # All validation rules
│   └── ontology-codegen/
│       ├── SKILL.md           # PySpark/TypeScript generation
│       └── templates/
│           ├── pyspark_sync.py.j2
│           └── osdk_client.ts.j2
├── agents/
│   └── ontology-architect.md  # Coordinating subagent
└── settings.json              # Hook configurations
```

**New skill: ontology-codegen** for pipeline generation:

```yaml
---
name: ontology-codegen
description: |
  Generate PySpark sync pipelines and OSDK TypeScript clients from ObjectType definitions.
  Use after: ontology-objecttype scaffolding is complete and validated.
allowed-tools: Read, Write, Bash
model: sonnet
---

# Ontology Code Generation

## Available Templates

### PySpark Sync Pipeline
Generates pipeline code for syncing backing datasets to Object Storage:
- Deterministic primary key computation
- Property type casting
- Incremental sync support

### OSDK TypeScript Client
Generates typed client code for accessing ObjectTypes:
- Full type definitions
- Link traversal methods
- Action submission helpers

## Usage
```
/ontology-codegen --type pyspark --input customer.ontology.yaml
/ontology-codegen --type osdk-ts --input customer.ontology.yaml --output ./src/ontology/
```

## Template Variables
- `{{ objecttype.apiName }}` - PascalCase API name
- `{{ objecttype.primaryKey.components }}` - PK column list
- `{{ objecttype.properties | selectattr("required") }}` - Required properties
```

## Bilingual support integrates throughout the workflow

All user-facing components support Korean (ko) and English (en):

```yaml
# locales/en.yaml
prompts:
  select_source: "What is your source for this ObjectType?"
  select_pk_strategy: "Primary Key Strategy:"
  confirm_generation: "Generate YAML scaffold?"
  
validation:
  pk_must_be_string: "Primary key must be string type"
  pk_must_be_required: "Primary key property must be required (non-null)"
  mm_requires_join: "Many-to-many links require join table configuration"
  
choices:
  source_code: "Existing source code"
  database_schema: "Database schema"
  business_doc: "Business requirements document"
  manual: "Manual definition"

# locales/ko.yaml
prompts:
  select_source: "이 ObjectType의 소스는 무엇인가요?"
  select_pk_strategy: "기본 키 전략:"
  confirm_generation: "YAML 스캐폴드를 생성할까요?"
  
validation:
  pk_must_be_string: "기본 키는 문자열 타입이어야 합니다"
  pk_must_be_required: "기본 키 속성은 필수(non-null)여야 합니다"
  mm_requires_join: "다대다 링크에는 조인 테이블 구성이 필요합니다"
  
choices:
  source_code: "기존 소스 코드"
  database_schema: "데이터베이스 스키마"
  business_doc: "비즈니스 요구사항 문서"
  manual: "수동 정의"
```

Language detection follows priority: CLI flag (`--lang=ko`) → environment variable (`CLI_LANG`) → OS locale → default (en).

## Decision tree guides Ontology component selection

```
┌─────────────────────────────────────────────────────────────────┐
│                  ONTOLOGY COMPONENT DECISION TREE                │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  START: What are you modeling?                                   │
│  ┌────────────────┬─────────────────┬──────────────────┐        │
│  ▼                ▼                 ▼                  ▼        │
│ Entity         Event            Relationship      Operation     │
│ (noun)       (verb+time)        (connection)      (action)      │
│  │                │                 │                  │        │
│  ▼                ▼                 ▼                  ▼        │
│ ObjectType   ObjectType          LinkType         ActionType    │
│              (event-sourced)                                    │
│                                                                  │
├─────────────────────────────────────────────────────────────────┤
│  PRIMARY KEY DECISION                                            │
│                                                                  │
│  Does a natural unique identifier exist?                         │
│  ┌────────────┬────────────────┐                                │
│  ▼ YES        ▼ NO             │                                │
│ Is it       Multiple columns    │                                │
│ string?     identify uniquely?  │                                │
│  │  │       ┌────┬─────┐        │                                │
│  │  ▼NO     ▼YES ▼NO           │                                │
│  │ CONVERT  Composite  Generate │                                │
│  │ to       Key        UUID*    │                                │
│  ▼ STRING   (a:b:c)    (⚠️)    │                                │
│ Use as PK                       │                                │
│                                                                  │
│ *UUID only if truly random entity; prefer deterministic          │
│                                                                  │
├─────────────────────────────────────────────────────────────────┤
│  LINK CARDINALITY DECISION                                       │
│                                                                  │
│  How many of A relate to how many of B?                          │
│  ┌──────────────┬──────────────┬──────────────┐                 │
│  ▼              ▼              ▼              │                 │
│ Exactly 1:1   1:Many/Many:1   Many:Many      │                 │
│  │              │              │              │                 │
│  ▼              ▼              ▼              │                 │
│ FK on         FK on          JOIN TABLE       │                 │
│ either        "many"         required         │                 │
│ side          side                            │                 │
│                                                                  │
│  Need metadata on relationship?                                  │
│  ┌────────┬────────────┐                                        │
│  ▼ YES    ▼ NO         │                                        │
│ Object-   Standard     │                                        │
│ Backed    LinkType     │                                        │
│ Link                   │                                        │
└─────────────────────────────────────────────────────────────────┘
```

## Conclusion: Architecture for production Ontology scaffolding

This enhanced Claude Code CLI infrastructure delivers a complete Ontology construction pipeline through five integrated layers:

1. **Skills Layer**: Modular, progressive-disclosure skills for each Ontology component (ObjectType, LinkType, ActionType) with L1/L2/L3 content organization matching Claude's token-efficient loading patterns.

2. **Interactive Decision Layer**: Real-time Q&A workflows using structured decision trees that guide users through complex design choices while enforcing Palantir's determinism and immutability principles.

3. **Validation Layer**: PreToolUse hooks implementing shift-left validation with Palantir-specific rules (string PKs, composite key delimiters, M:M join table requirements) that block invalid definitions before they're written.

4. **Code Generation Layer**: Template-based generation of PySpark sync pipelines and OSDK TypeScript clients directly from validated YAML scaffolds.

5. **Localization Layer**: Full Korean/English bilingual support across all prompts, validation messages, and generated documentation.

The key insight is that **Claude Code's progressive disclosure architecture maps naturally to Ontology scaffolding phases**—lightweight metadata scanning for candidate detection, full skill activation for property extraction, and on-demand reference loading for complete validation. Combined with hook-based enforcement of Palantir's strict integrity rules, this creates a guardrailed yet flexible system for enterprise Ontology construction.