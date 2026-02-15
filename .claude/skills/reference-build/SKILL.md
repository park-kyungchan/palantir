---
name: reference-build
description: |
  [D0·Foundation·Reference] BuildDomainReference with OCR pattern library, backslash depth guide, structured R1-R5 rules. Tiered command tables (T1-3), per-domain separation.

  WHEN: First session, reference refresh, or new domain onboarding. No prerequisites.
  DOMAIN: foundation (1/1). Independent. Extensible registry (math/physics/chemistry/biology).
  INPUT_FROM: User request (domain scope), progress-track (weak areas).
  OUTPUT_TO: challenge-generate IC-01 command_pool (commands[], escape_rules[], ocr_confusions[], trap_catalog[]), latex-parse IC-02 command_allowlist (valid_commands[], operators[], environments[], domain_semantics[]), golden-correct (canonical syntax).

  METHODOLOGY: (1) Domain scope from registry, (2) Tiered command table, (3) OCR confusion patterns, (4) Backslash depth guide (0-2), (5) R1-R5 rules with severity/example/counter-example, (6) Trap catalog, (7) Persist reference-cache/{domain}.yaml.
  OUTPUT_FORMAT: L1 YAML inventory + contract compliance, L2 with IC-01/IC-02 sections.
user-invocable: true
disable-model-invocation: false
argument-hint: "[domain: math|physics|chemistry|biology]"
---

# Foundation -- Reference Build

## Execution Model
- **BASIC**: Single-domain reference (e.g., calculus only). Lead-direct generation. ~30 commands.
- **STANDARD**: Multi-domain reference (2-3 domains). Structured table generation. ~60-90 commands.
- **COMPREHENSIVE**: Full-scope reference (all domains in registry). Includes cross-domain patterns and OCR confusion matrix. ~120+ commands.

## Decision Points

### Domain Registry Architecture
Domains are externalized to `crowd_works/data/reference-cache/{domain}.yaml`. Skills read from the registry, never from hardcoded lists.

**Current registry:**

| Domain | File | Key Commands | Trap Density |
|--------|------|-------------|--------------|
| Functions/Limits | math.yaml | `\lim`, `\to`, `\infty`, `\epsilon` | Medium |
| Differentiation | math.yaml | `\frac{d}{dx}`, `\partial`, `\nabla` | High (nested fracs) |
| Integration | math.yaml | `\int`, `\iint`, `\oint`, `\,dx` | High (dx spacing, bounds) |
| Sequences/Series | math.yaml | `\sum`, `\prod`, `\cdots`, `\binom` | Medium |
| Probability/Stats | math.yaml | `\mathbb{P}`, `\sigma`, `\mu`, `\bar{x}` | Low |
| Geometry/Vectors | math.yaml | `\vec`, `\overrightarrow`, `\angle`, `\perp` | Medium |
| Matrices/Linear | math.yaml | `\begin{pmatrix}`, `\det`, `\text{tr}` | Very High (environments) |
| Mechanics | physics.yaml | `\vec{F}`, `\ddot{x}`, `\omega` | Medium |
| Chemical Eqns | chemistry.yaml | `\ce{}`, `\rightleftharpoons` | High (mhchem pkg) |
| Molecular Bio | biology.yaml | `\text{}` sequences, subscripts | Low |

### New Domain Onboarding Process
```
Step 1: Invoke /reference-build [new-domain]
  -> Generates crowd_works/data/reference-cache/{new-domain}.yaml
  -> Contains: commands[], escape_rules[], ocr_confusions[], domain_semantics[]

Step 2: Automatic downstream propagation (zero SKILL.md edits)
  - challenge-generate reads command_pool from reference-cache/{domain}.yaml
  - latex-parse reads command_allowlist from reference-cache/{domain}.yaml
  - golden-correct reads canonical syntax from reference-cache/{domain}.yaml

Step 3: Domain-specific validation rules (optional)
  - Add domain_semantics[] entries to the new domain YAML
  - Example: chemistry requires \ce{} syntax, physics requires \vec{} consistency

Step 4: Verification
  - Run 1 drill cycle with new domain at Level 1
  - Verify: challenge generation, validation, rendering, correction all work
  - Verify: progress-track correctly separates new domain metrics
```

### Tier Classification
- **Tier 1 (Daily)**: Commands appearing in >70% of problems. Must be memorized.
- **Tier 2 (Frequent)**: Commands appearing in 30-70%. Should recognize and write correctly.
- **Tier 3 (Rare)**: Commands appearing in <30%. Should recognize; lookup acceptable.

### When to Rebuild vs Incremental Update
```
IF first session OR no existing reference-cache/{domain}.yaml:
  -> Full build (all tiers, all requested domains)
ELIF progress-track reports new weak areas:
  -> Incremental: add weak-area commands to existing reference
ELIF user requests new domain not in registry:
  -> New domain onboarding (full build for that domain only)
ELIF user requests specific existing domain:
  -> Targeted: rebuild single-domain reference
```

## Methodology

### 1. Identify Domain Scope from Extensible Registry
Parse user request or progress-track output for domain keywords. Check existing files in `crowd_works/data/reference-cache/` to determine rebuild vs incremental. Default to full math scope if unspecified and first session.

### 2. Build Tiered Command Table
For each command in scope, create structured entries per IC-01 schema:

```yaml
- command: "\\frac{a}{b}"
  tier: 1
  domain: "calculus"
  meaning: "fraction a/b"
  jsonl_escaped: "\\\\frac{a}{b}"
  common_errors:
    - pattern: "\\frac{a}b"
      issue: "Missing second braces group"
      fix: "\\frac{a}{b}"
    - pattern: "\\frac a b"
      issue: "No braces at all"
      fix: "\\frac{a}{b}"
  render_note: "Renders as vertical fraction"
```

### 3. Compile OCR Confusion Patterns Per Domain
Build domain-specific OCR error pattern library. Each entry maps what OCR commonly misreads:

| Source (OCR Output) | Target (Correct) | LaTeX Correct | Frequency | Domain Context |
|---------------------|-------------------|---------------|-----------|----------------|
| `9` | theta | `\theta` | high | Greek letters in calculus |
| `A` | Delta | `\Delta` | high | Change/difference notation |
| `u` | mu | `\mu` | medium | Statistics, physics constants |
| `E` | Sigma | `\Sigma` | medium | Summation notation |
| broken/garbled | integral | `\int` | high | Integral sign OCR failure |
| `0` | phi | `\phi` | medium | Angle/phase notation |
| `l` (lowercase L) | 1 (one) | `1` | high | Numeric expressions |
| `rn` | m | `m` | medium | Variable names |

Per IC-01 schema, each entry requires: `source_char`, `target_char`, `latex_correct`, `frequency` (enum: high/medium/low), optional `domain_context`.

### 4. Generate Backslash Escape Depth Guide
The core confusion in LaTeX-in-JSONL is backslash explosion across encoding layers:

| Depth | Context | `\frac` becomes | `\\` (newline) becomes | Rule |
|-------|---------|-----------------|------------------------|------|
| 0 | Raw LaTeX (source) | `\frac` | `\\` | As-written |
| 1 | JSON string value | `\\frac` | `\\\\` | Each `\` doubled |
| 2 | JSONL line (escaped) | `\\\\frac` | `\\\\\\\\` | Doubled again |

Key insight: At each depth, every single backslash from the previous depth becomes two backslashes. Depth 2 is what appears in `.jsonl` files on disk.

### 5. Build Structured R1-R5 Escape Rule Objects
Each rule is a structured object with severity, example, and counter-example:

```yaml
escape_rules:
  - rule_id: "R1"
    name: "Backslash Double-Escape"
    severity: "FATAL"
    latex_original: "\\frac"
    jsonl_escaped: "\\\\frac"
    trap_description: "Single \\ breaks JSON parser -- sees escape sequence"
    example: '{"text": "\\\\frac{1}{2}"}'       # correct
    counter_example: '{"text": "\\frac{1}{2}"}'  # FATAL: JSON parse error
  - rule_id: "R2"
    name: "Quote Escape"
    severity: "FATAL"
    latex_original: '"text"'
    jsonl_escaped: '\\"text\\"'
    trap_description: "Unescaped quotes terminate JSON string prematurely"
    example: '{"text": "say \\"hello\\""}'
    counter_example: '{"text": "say "hello""}'    # FATAL: invalid JSON
  - rule_id: "R3"
    name: "Newline Handling"
    severity: "FATAL"
    latex_original: "literal newline"
    jsonl_escaped: "\\n"
    trap_description: "JSONL is single-line -- literal newlines break format"
    example: '{"text": "line1\\nline2"}'
    counter_example: '{"text": "line1\nline2"}'   # FATAL: split JSONL record
  - rule_id: "R4"
    name: "Align Row Break"
    severity: "FATAL"
    latex_original: "\\\\"
    jsonl_escaped: "\\\\\\\\"
    trap_description: "Double-backslash in LaTeX needs quadruple in JSONL"
    example: '{"text": "a \\\\\\\\ b"}'
    counter_example: '{"text": "a \\\\ b"}'       # Ambiguous: partial escape
  - rule_id: "R5"
    name: "Brace Escape Layer"
    severity: "WARN"
    latex_original: "\\{"
    jsonl_escaped: "\\\\{"
    trap_description: "LaTeX brace escape needs double-escape in JSONL"
    example: '{"text": "\\\\{x\\\\}"}'
    counter_example: '{"text": "\\{x\\}"}'        # WARN: may parse but wrong
```

### 6. Create Trap Catalog
Organized by category and severity per IC-01 schema:
- **ESCAPE** (FATAL/FAIL): Backslash, quote, newline escape failures
- **GROUPING** (FAIL/WARN): Missing braces, wrong nesting depth
- **OPERATOR** (WARN): Italic operator names (`sin` instead of `\sin`)
- **SIZING** (WARN): Missing `\left`/`\right` for delimiters
- **TEXT** (WARN/INFO): Missing `\text{}` for Korean/English words in math mode
- **ENVIRONMENT** (FAIL): Unclosed environments, wrong environment names
- **SEMANTIC** (WARN/INFO): Domain-specific convention violations

Each trap entry: `trap_id`, `category`, `severity`, `description`, `wrong_example`, `correct_example`, `difficulty_contribution` (1-5).

Minimum counts per IC-01 validation: >=3 FATAL, >=5 FAIL, >=3 WARN.

### 7. Persist and Notify Downstream
Write output to `crowd_works/data/reference-cache/{domain}.yaml`. Structure:
```yaml
domain: "calculus"
version: "1.0"
generated_at: "2026-02-15T10:30:00+09:00"
commands: [...]        # IC-01 command entries
escape_rules: [...]    # R1-R5 structured rules
ocr_confusions: [...]  # Domain OCR patterns
trap_catalog: [...]    # Categorized traps
domain_semantics: [...]  # IC-02 semantic rules
```

Downstream skills auto-discover new domains by scanning reference-cache/ directory. No manual notification or SKILL.md edits required (AD-4 architecture decision).

## Failure Handling

### Domain Not Found in Registry
- **Cause**: User specifies a domain with no existing reference-cache file
- **Action**: Treat as new domain onboarding. Build reference from scratch.
- **Route**: Self (full build mode for new domain)

### OCR Pattern Stale
- **Cause**: OCR confusion patterns outdated (new scanner, different error distribution)
- **Action**: Regenerate ocr_confusions[] for affected domains. Compare old vs new patterns.
- **Route**: Self (incremental update, OCR section only)

### Contract Version Mismatch
- **Cause**: Downstream skill expects different schema version than what reference-build produces
- **Action**: Check IC-01/IC-02 version field. Log warning with expected vs actual version.
- **Route**: Report to Lead for interface reconciliation. Do not silently downgrade.

### Reference Too Large
- **Cause**: Full-scope reference exceeds practical size for single file
- **Action**: Split into per-domain reference files (one YAML per domain)
- **Route**: Output multiple files to reference-cache/

## Anti-Patterns

### DO NOT: Hardcode Domain Lists
Domain scope comes from the reference-cache/ directory contents and user input. Never maintain a static list of domains in skill logic. New domains are added by creating new YAML files.

### DO NOT: Remove Existing Commands When Adding Domain
Incremental updates are additive. When adding a new domain or updating an existing one, never delete commands from other domains. Each domain file is independent.

### DO NOT: Skip OCR Pattern Validation
Every domain reference MUST include ocr_confusions[]. Even if a domain has few OCR issues, document at minimum the universal confusions (l/1, 0/O, rn/m).

### DO NOT: Include Commands Not Used in Target Domain
Each domain has its own command scope. Math 수리논술 does not need `\ce{}` (chemistry). Chemistry does not need `\int`. Respect domain boundaries.

### DO NOT: Show Only Correct Forms
The trap catalog IS the reference's primary value. Every command entry MUST include common error patterns with wrong_example and correct_example.

### DO NOT: Separate LaTeX and JSONL References
Always show both forms together. The trainee must internalize the mapping between raw LaTeX and JSONL-escaped forms.

## Transitions

### Receives From
| Source | Data | Key Fields | Format |
|--------|------|------------|--------|
| User request | Domain scope | domain keyword or "all" | Natural language |
| progress-track | Weak areas | error_categories[], frequencies, by_domain | YAML |

### Sends To (IC-01: command_pool --> challenge-generate)
| Field | Type | Purpose |
|-------|------|---------|
| `domains[].commands[]` | array[object] | Tiered command entries with errors |
| `domains[].escape_rules[]` | array[object] | R1-R5 structured rules |
| `domains[].ocr_confusions[]` | array[object] | OCR misrecognition patterns |
| `domains[].trap_catalog[]` | array[object] | Categorized traps with severity |
| `tier_distribution` | object | Counts per tier |

### Sends To (IC-02: command_allowlist --> latex-parse)
| Field | Type | Purpose |
|-------|------|---------|
| `domains[].valid_commands[]` | array[object] | Known-valid commands with arg counts |
| `domains[].operators[]` | array[string] | Valid operator commands |
| `domains[].environments[]` | array[string] | Valid environment names |
| `domains[].domain_semantics[]` | array[object] | Domain-specific validation rules |
| `mode` | enum | "drill" or "production" pipeline context |

### Sends To (golden-correct)
| Field | Type | Purpose |
|-------|------|---------|
| Canonical command forms | YAML | Correct syntax for each command |
| Escape rules | YAML | R1-R5 for correction validation |

## Quality Gate
- Every command has: LaTeX form + JSONL-escaped form + >=1 error pattern
- Escape rule table covers all 5 core rules (R1-R5) with severity/example/counter-example
- Trap catalog has >=3 FATAL, >=5 FAIL, >=3 WARN entries (per IC-01 validation)
- All JSONL examples validated: string is parseable by `JSON.parse()`
- OCR confusion patterns present for every domain (>=3 entries per domain)
- Domain registry integrity: each output file exists in reference-cache/ with valid YAML
- IC-01 schema compliance: command_pool contains all required fields per contract
- IC-02 schema compliance: command_allowlist contains all required fields per contract
- Backslash depth guide included (depth 0/1/2 with examples)

## Output

### L1
```yaml
domain: foundation
skill: reference-build
status: complete
scope: [calculus, linear_algebra]  # domains covered
command_count: 0
tier_distribution:
  tier1: 0
  tier2: 0
  tier3: 0
trap_count: 0
ocr_pattern_count: 0
contract_compliance:
  ic01_command_pool: true
  ic02_command_allowlist: true
persistence: "crowd_works/data/reference-cache/{domain}.yaml"
```

### L2
- Tiered command reference table (YAML + markdown) per IC-01 command_pool schema
- OCR confusion pattern library per domain
- Backslash escape depth guide (depth 0/1/2)
- R1-R5 structured escape rules with severity/example/counter-example
- Trap catalog by severity and category (FATAL/FAIL/WARN/INFO)
- IC-02 command_allowlist output (valid_commands, operators, environments, domain_semantics)
- Domain-specific gotchas and cross-domain notes
- Persisted reference-cache file paths
