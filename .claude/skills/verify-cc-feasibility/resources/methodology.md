# Verify CC Feasibility — Detailed Methodology

> On-demand reference for verify-cc-feasibility. Contains step-by-step validation procedure.

## Step 1: Read Target Frontmatter

For each agent and skill file in scope:
- Extract all YAML frontmatter field names (everything between the `---` delimiters)
- Build field inventory per file: `{file_path: [field_name, field_name, ...]}`
- Separate files into two categories: skill files (SKILL.md) and agent files (.claude/agents/*.md)
- Record the raw field values alongside field names for Step 3 validation

Scope determination:
- If `$ARGUMENTS` contains specific file paths: check only those files
- If `$ARGUMENTS` is "full" or empty: scan all `.claude/skills/*/SKILL.md` and `.claude/agents/*.md`
- If invoked after verify-quality: use the file list from the previous verify stage output

## Step 2: Check Against Native Fields

Read `resources/native-field-tables.md` for complete native field lists.

Flag any field NOT in the skill or agent tables as non-native. Ensure you are checking against the correct table for the file type (skill fields for SKILL.md, agent fields for agent .md files).

For STANDARD/COMPLEX tiers, construct DPS for analyst. Read `~/.claude/resources/dps-construction-guide.md` for DPS structure.

### DPS Specifics for CC Feasibility
- **Context INCLUDE**: Extracted frontmatter fields+values per file. Native field tables from resources/. Known non-native list. cc-reference cache path. File paths in analyst's scope.
- **Context EXCLUDE**: L2 body content. Historical field removal rationale. Other subagents' tasks. Non-.claude/ files.
- **Task**: "Compare each extracted field against native field lists. Flag non-native fields. Validate value types. Read cc-reference cache at `memory/cc-reference/native-fields.md` for latest reference. Report per-file status."
- **Constraints**: Read-only. No file modifications. Use cc-reference cache as primary source (NOT claude-code-guide). maxTurns: 25.
- **Delivery**: file-based signal: `"{STATUS}|files:{total_files}|non_native:{count}|ref:tasks/{work_dir}/p7-cc-feasibility.md"`

## Step 3: Validate Field Values

For each native field found in Step 2, validate value matches expected type. Read `resources/native-field-tables.md` § Field Value Validation Rules.

## Step 4: Validate Questionable Fields

When a field is not clearly native or non-native:

1. **Primary check**: Read `memory/cc-reference/native-fields.md`
2. **Cross-reference check**: If field exists in OTHER table (agent field in skill), flag as "wrong file type"
3. **Supplementary check**: If cache stale (>30 days), analyst sends verdict via file-based signal. Lead escalates to claude-code-guide only for ambiguous fields.
4. **Record verdict**: NATIVE, NON_NATIVE, WRONG_FILE_TYPE, or UNKNOWN

If claude-code-guide spawned by Lead:
- If confirms native: PASS + flag cache for update via execution-infra
- If confirms non-native: FAIL
- If unavailable: Conservative FAIL with WARN. Do NOT mark as PASS.

## Step 5: Generate Compliance Report

Per-file status:
- **PASS**: All native, all valid types, no warnings
- **FAIL**: Non-native found, type mismatches, or unverifiable fields. List each with file/field/action.
- **SKIP**: Skip conditions met. Include rationale.

Separate findings:
- Non-native fields (BLOCKING — must remove before delivery)
- Value type mismatches (BLOCKING — must correct)
- Warnings (NON-BLOCKING — cache staleness, unverifiable fields)

Aggregate verdict: PASS only if zero blocking findings.

## Failure Protocols

**Non-Native Field Detected**: FAIL with file/field/evidence → execution-infra removal. Silently ignored fields create false configuration sense.

**Field Value Type Mismatch**: FAIL with current/expected → execution-infra correction. Boolean fields especially prone to string/boolean confusion.

**CC Reference Cache Stale/Missing**: Spawn claude-code-guide for fresh validation → route cache update to execution-infra.

**claude-code-guide Unavailable**: Fall back to cc-reference cache. If both unavailable, FAIL with "unable to validate" → Lead manual assessment. Include unverifiable fields in L1 `warnings[]`.

**Deprecated Field**: FAIL with deprecation details + migration path → execution-infra replacement.
