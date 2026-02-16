# Community Tooling Ecosystem (Post-Opus 4.6)

> Section verified: 2026-02-16. Community tools may change rapidly.

---

## 1. agnix — Infrastructure Linter + LSP

- **Repository**: `github.com/avifenesh/agnix`
- **Install**: `npm install -g agnix` or `cargo install agnix-cli`
- **What it does**: 200 rules validating CLAUDE.md, SKILL.md, hooks, MCP configs, and agent files. Supports auto-fix, GitHub Action, and editor integration (VSCode, JetBrains, Neovim, Zed).

**Key capabilities**:
- Cross-file consistency validation
- Detects: skill name kebab-case violations, dangerous hook commands, missing frontmatter, unrestricted allowedTools
- `agnix --fix .` for auto-repair; `--dry-run --show-fixes` for preview
- Wireable into PostToolUse hook for automatic validation

**Limitation**: Validates structure/syntax but NOT cascade dependency analysis.

---

## 2. diet103/claude-code-infrastructure-showcase

- **Repository**: `github.com/diet103/claude-code-infrastructure-showcase`
- **What it does**: Patterns from 6 months of TypeScript microservices. Solves "skills don't auto-activate" problem.

**Key components**:
- `skill-rules.json`: Skill activation based on `pathPattern` (glob patterns)
- `UserPromptSubmit` hook: Suggests relevant skills before Claude processes
- `PostToolUse` hook: Tracks file changes for context

---

## 3. kieranklaassen Gist — Swarm Orchestration

- **Source**: `gist.github.com/kieranklaassen/4f2aba89594a4aea4ad64d753984b2ea`
- **What it does**: Complete Agent Teams TeammateTool documentation, task system, message protocols.

**Key details**: tmux backend, lifecycle, config.json structure, heartbeat timeout (5 min), compound-engineering patterns. Most practical WSL2 tmux reference.

---

## 4. ruvnet/claude-flow v3

- **Repository**: `github.com/ruvnet/claude-flow`
- **What it does**: 170+ MCP tools, 60+ agents for multi-agent orchestration.

**Relevant concepts**: Effort-Level Router, Security Swarm-on-Commit, Self-Audit Mode. Status: Experimental.

---

## 5. wshobson/agents

- **Repository**: `github.com/wshobson/agents`
- **What it does**: 112 agents, 146 skills, 16 orchestrators, 79 tools in 73 plugins.

**Architecture**: Minimal token usage through fine-grained plugin structure. Each plugin loads only its own components.

---

## 6. disler/claude-code-hooks-mastery

- **Repository**: `github.com/disler/claude-code-hooks-mastery`
- **What it does**: Complete hook lifecycle coverage with all hook events. Builder/Validator agent pattern.

**Key patterns**: TTS feedback, security enforcement, chat transcript extraction, Builder/Validator team orchestration.

---

## 7. disler/claude-code-hooks-multi-agent-observability

- **Repository**: `github.com/disler/claude-code-hooks-multi-agent-observability`
- **What it does**: Real-time monitoring dashboard for Agent Teams. Task lifecycle tracking, failure surfacing, throughput measurement.

---

## 8. Anthropic C Compiler Project — Reference Architecture

- **Source**: `anthropic.com/engineering/building-c-compiler`
- **What happened**: 16 parallel Opus 4.6 instances built a 100,000-line Rust C compiler. Cost: ~$20,000.

**Key lessons**:
- No orchestration agent — autonomous "next most obvious" selection
- Running doc of failed approaches for stuck agents
- Git history for task locking
- Test harness (verifier) quality matters more than prompts
- CI pipeline essential for regression prevention

---

## 9. obra/superpowers

- **Repository**: `github.com/obra/superpowers`
- **Install**: `/plugin marketplace add obra/superpowers-marketplace`
- **What it does**: Meta-skill collection including `writing-skills` and `using-superpowers`. Enforces "THE RULE": invoke if even 1% applicable.

---

## 10. daymade/claude-code-skills

- **Repository**: `github.com/daymade/claude-code-skills`
- **Key skills**:
  - `claude-md-progressive-disclosurer`: Optimizes CLAUDE.md bloat via progressive disclosure
  - `docs-cleaner`: Consolidates duplicate documentation
  - `skill-creator`: Automates new skill creation
  - CCPM: `ccpm search`, `ccpm install`, `ccpm list` for skill lifecycle
