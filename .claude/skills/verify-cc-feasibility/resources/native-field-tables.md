# CC Native Field Reference Tables

> On-demand reference for verify-cc-feasibility. Contains complete native field lists for validation.

## Skill Native Fields (SKILL.md)

| Field | Type | Required | Default | Valid Values |
|-------|------|----------|---------|-------------|
| `name` | string | no | directory name | Lowercase, numbers, hyphens. Max 64 chars |
| `description` | string | recommended | none | Multi-line via YAML `\|`. Max 1024 chars |
| `argument-hint` | string | no | none | Free text, e.g., `[topic]`, `[file] [format]` |
| `user-invocable` | boolean | no | true | `true` or `false` only |
| `disable-model-invocation` | boolean | no | false | `true` or `false` only |
| `allowed-tools` | list | no | all | Array of CC tool registry names |
| `model` | enum | no | inherit | `sonnet`, `opus`, `haiku`, `inherit` |
| `context` | enum | no | none | `fork` (DANGER: replaces agent body with skill L2) |
| `agent` | string | no | general-purpose | Must match an existing agent name exactly |
| `hooks` | object | no | none | Skill-scoped hook configuration object |

## Agent Native Fields (.claude/agents/*.md)

| Field | Type | Required | Default | Valid Values |
|-------|------|----------|---------|-------------|
| `name` | string | yes | none | Agent identifier for subagent_type matching |
| `description` | string | yes | none | Free text. No enforced length limit |
| `tools` | list | no | all | Explicit allowlist of CC tool registry names |
| `disallowedTools` | list | no | none | Denylist of tool names. Ignored if `tools` is set |
| `model` | enum | no | inherit | `sonnet`, `opus`, `haiku` (aliases to latest) |
| `permissionMode` | enum | no | default | `default`, `acceptEdits`, `delegate`, `dontAsk`, `bypassPermissions`, `plan` |
| `maxTurns` | number | no | unlimited | Positive integer |
| `skills` | list | no | none | Array of skill names. Full L1+L2 injected at startup |
| `mcpServers` | list | no | none | MCP server access configuration |
| `hooks` | object | no | none | Agent-scoped hooks |
| `memory` | enum | no | none | `user`, `project`, `local` |
| `color` | string | no | none | UI color coding string |

## Known Non-Native Fields (Silently Ignored by CC)

- `input_schema` — was used in 12 skills before v10.2, removed
- `confirm` — was used in 3 skills before v10.2, removed
- `once` — was used in pt-manager before v10.5, removed
- `priority`, `weight` — no native priority mechanism exists
- `working_dir`, `timeout`, `env` — shell-like fields, not consumed by CC
- `routing`, `meta_cognition`, `ontology_lens` — custom metadata blocks, ignored
- `context-dependent`, `closed_loop` — custom protocol fields, ignored
- Any key not in the tables above is non-native and silently ignored

## Field Value Validation Rules

### Skill Field Values

| Field | Validation Rule | Common Errors |
|-------|-----------------|---------------|
| `name` | Lowercase, numbers, hyphens only. Max 64 chars. | Spaces, uppercase, underscores |
| `description` | Multi-line via `\|`. Max 1024 chars total. | Exceeding 1024 causes L1 truncation |
| `user-invocable` | `true` or `false` only. | `"yes"`, `"no"`, `1`, `0` |
| `disable-model-invocation` | `true` or `false` only. | `"true"` (string), `enabled` |
| `model` | One of: `sonnet`, `opus`, `haiku`, `inherit`. | `"fast"`, `"claude-3"`, version numbers |
| `context` | Only valid value: `fork`. | `"shared"`, `"isolated"` |
| `agent` | Must match an existing `.claude/agents/*.md` name. | Typo in agent name |

### Agent Field Values

| Field | Validation Rule | Common Errors |
|-------|-----------------|---------------|
| `model` | One of: `sonnet`, `opus`, `haiku`. | `inherit` (not valid for agents) |
| `permissionMode` | One of: `default`, `acceptEdits`, `delegate`, `dontAsk`, `bypassPermissions`, `plan`. | `plan` blocks MCP tools (BUG-001) |
| `maxTurns` | Positive integer. | String, negative, zero |
| `memory` | One of: `user`, `project`, `local`. | `"none"`, `true`, path string |
