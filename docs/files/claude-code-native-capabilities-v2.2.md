# Claude Code v2.2+ Native Capabilities Reference
## Machine-Readable Configuration for Codebase Analysis & Improvement Planning

---

## METADATA

```yaml
document_type: claude-code-native-capabilities
version: "2.2.0"
last_updated: "2025-01-24"
purpose: machine-readable-reference
target: claude-code-cli
use_case: codebase-improvement-planning
compatibility: "claude-code >= 2.1.16"
```

---

## 1. CORE ARCHITECTURE OVERVIEW

### 1.1 System Components Hierarchy

```yaml
claude_code_stack:
  layer_1_foundation:
    - name: "Claude Agent SDK"
      description: "Core execution engine powering Claude Code"
      capabilities:
        - tool_execution
        - context_management
        - permission_handling
        - session_persistence
    
  layer_2_tools:
    native_tools:
      - Read: "File reading with content extraction"
      - Edit: "In-place file modification"
      - Write: "New file creation"
      - Bash: "Shell command execution"
      - Grep: "Pattern search across files"
      - Glob: "File pattern matching"
      - WebFetch: "URL content retrieval"
      - Task: "Subagent spawning and orchestration"
      - Analyze: "Code analysis and understanding"
    
  layer_3_extensions:
    - MCP_servers: "Model Context Protocol integrations"
    - LSP_servers: "Language Server Protocol support"
    - Plugins: "Third-party extensions"
    - Skills: "Reusable workflow definitions"
    
  layer_4_orchestration:
    - Subagents: "Parallel task execution"
    - Hooks: "Event-driven automation"
    - Commands: "Custom slash commands"
    - Rules: "Behavioral guidelines"
```

### 1.2 Configuration Precedence (Highest to Lowest)

```yaml
configuration_hierarchy:
  1_enterprise_policies:
    location: "managed-settings.json"
    scope: "organization-wide"
    override_level: "highest"
    editable_by: "IT administrators only"
    
  2_cli_arguments:
    examples:
      - "--model opus"
      - "--dangerously-skip-permissions"
      - "--permission-mode plan"
    scope: "single session"
    override_level: "high"
    
  3_local_project_settings:
    location: ".claude/settings.local.json"
    scope: "project-specific, gitignored"
    override_level: "medium-high"
    use_case: "personal developer preferences"
    
  4_shared_project_settings:
    location: ".claude/settings.json"
    scope: "project-wide, version controlled"
    override_level: "medium"
    use_case: "team collaboration"
    
  5_user_settings:
    location: "~/.claude/settings.json"
    scope: "user-global"
    override_level: "low"
    
  6_default_settings:
    source: "claude-code-defaults"
    override_level: "lowest"
```

---

## 2. ENVIRONMENT VARIABLES REFERENCE

### 2.1 Authentication & API

```bash
# ============================================
# AUTHENTICATION
# ============================================
export ANTHROPIC_API_KEY="sk-ant-..."           # Direct API authentication
export ANTHROPIC_AUTH_TOKEN="..."               # Alternative auth token
export ANTHROPIC_BASE_URL="https://api.anthropic.com"  # API endpoint

# ============================================
# CLOUD PLATFORM INTEGRATION
# ============================================
# AWS Bedrock
export CLAUDE_CODE_USE_BEDROCK=1
export AWS_REGION="us-east-1"
export AWS_ACCESS_KEY_ID="..."
export AWS_SECRET_ACCESS_KEY="..."

# Google Vertex AI
export CLAUDE_CODE_USE_VERTEX=1
export GOOGLE_APPLICATION_CREDENTIALS="/path/to/credentials.json"
export VERTEX_PROJECT_ID="..."
export VERTEX_REGION="us-central1"
```

### 2.2 Model Selection & Performance

```bash
# ============================================
# MODEL CONFIGURATION
# ============================================
export ANTHROPIC_MODEL="claude-sonnet-4-5-20250929"

# Model aliases (resolved at runtime)
# - "sonnet" -> claude-sonnet-4-5-20250929
# - "opus"   -> claude-opus-4-5-20251101
# - "haiku"  -> claude-haiku-4-5-20251001

# Model for subagents (default: inherit from parent)
export ANTHROPIC_SUBAGENT_MODEL="claude-sonnet-4-5-20250929"

# ============================================
# TOKEN & CONTEXT MANAGEMENT
# ============================================
export MAX_THINKING_TOKENS=10000              # Extended thinking budget
export MAX_OUTPUT_TOKENS=16384                # Response length limit
export MAX_MCP_OUTPUT_TOKENS=25000            # MCP tool output limit
export SLASH_COMMAND_TOOL_CHAR_BUDGET=15000   # Slash command context limit

# ============================================
# PROMPT CACHING (cost optimization)
# ============================================
export DISABLE_PROMPT_CACHING_HAIKU=0         # 0=enabled, 1=disabled
export DISABLE_PROMPT_CACHING_OPUS=0
export DISABLE_PROMPT_CACHING_SONNET=0
```

### 2.3 Execution & Timeout Settings

```bash
# ============================================
# BASH EXECUTION
# ============================================
export BASH_DEFAULT_TIMEOUT_MS=300000         # 5 minutes default
export BASH_MAX_TIMEOUT_MS=600000             # 10 minutes maximum
export BASH_MAX_OUTPUT_LENGTH=100000          # Output truncation limit
export CLAUDE_BASH_MAINTAIN_PROJECT_WORKING_DIR=1  # Reset pwd after each command

# ============================================
# MCP SERVER TIMEOUTS
# ============================================
export MCP_STARTUP_TIMEOUT_MS=30000           # Server startup timeout
export MCP_TOOL_TIMEOUT_MS=60000              # Individual tool timeout

# ============================================
# ENVIRONMENT FILE SOURCING
# ============================================
export CLAUDE_ENV_FILE="$HOME/.claude/env.sh" # Sourced before each bash command
```

### 2.4 Session & Task Management

```bash
# ============================================
# SESSION MANAGEMENT
# ============================================
export CLAUDE_SESSION_ID="${CLAUDE_SESSION_ID}"  # Auto-set by Claude Code
export CLAUDE_CONFIG_DIR="$HOME/.claude"         # Configuration directory
export CLAUDE_CODE_TMPDIR="$HOME/.claude/tmp"    # Temporary files

# ============================================
# TASK LIST MANAGEMENT (Cross-session persistence)
# ============================================
export CLAUDE_CODE_TASK_LIST_ID="main-dev"    # Shared task list identifier
# Usage: Different task list IDs create separate persistent task contexts
# - "dev-main"      -> Main development tasks
# - "refactor-v2"   -> Refactoring project tasks
# - "bugfix-sprint" -> Bug fix tracking

# ============================================
# PLANS DIRECTORY
# ============================================
# Plans created with /plan are saved here
export CLAUDE_PLANS_DIRECTORY="./.claude/plans"
```

### 2.5 Feature Toggles

```bash
# ============================================
# FEATURE FLAGS
# ============================================
export CLAUDE_CODE_DISABLE_BACKGROUND_TASKS=0  # Background task execution
export CLAUDE_CODE_DISABLE_TERMINAL_TITLE=0    # Terminal title updates
export DISABLE_COST_WARNINGS=0                 # Cost warning popups
export DISABLE_TELEMETRY=0                     # Usage telemetry
export DISABLE_ERROR_REPORTING=0               # Error reporting
export DISABLE_AUTO_UPDATE=0                   # Automatic updates
export DISABLE_TOOL_SEARCH=0                   # Dynamic MCP tool loading

# ============================================
# BUILT-IN TOOLS
# ============================================
export USE_BUILTIN_RIPGREP=1                   # Use bundled ripgrep
export USE_NATIVE_FILE_WATCHER=1               # Native filesystem watching
```

### 2.6 Network & Proxy

```bash
# ============================================
# PROXY CONFIGURATION
# ============================================
export HTTP_PROXY="http://proxy.company.com:8080"
export HTTPS_PROXY="http://proxy.company.com:8080"
export NO_PROXY="localhost,127.0.0.1,.internal.company.com"

# ============================================
# mTLS (Enterprise)
# ============================================
export CLAUDE_CODE_CLIENT_CERT="/path/to/cert.pem"
export CLAUDE_CODE_CLIENT_KEY="/path/to/key.pem"
export CLAUDE_CODE_CLIENT_KEY_PASSPHRASE="..."
```

---

## 3. SETTINGS.JSON SCHEMA

### 3.1 Complete Settings Structure

```json
{
  "$schema": "claude-code-settings-v2.2",
  
  "model": "claude-sonnet-4-5-20250929",
  "cleanupPeriodDays": 30,
  "includeCoAuthoredBy": true,
  "plansDirectory": "./.claude/plans",
  "rulesDirectory": "./.claude/rules",
  
  "permissions": {
    "allow": [
      "Bash(npm run *)",
      "Bash(git diff*)",
      "Bash(git status*)",
      "Bash(git log*)",
      "Bash(pytest *)",
      "Bash(cargo test*)",
      "Read(~/.config/**)",
      "Read(./**)",
      "Edit(./**)",
      "MCP(filesystem:*)",
      "Task(*)"
    ],
    "ask": [
      "Bash(git push*)",
      "Bash(git commit*)",
      "Bash(npm publish*)",
      "Bash(docker*)",
      "WebFetch(*)"
    ],
    "deny": [
      "Read(./.env)",
      "Read(./.env.*)",
      "Read(./secrets/**)",
      "Read(**/.git/config)",
      "Bash(rm -rf /)",
      "Bash(curl*|sh)",
      "Bash(wget*|sh)"
    ],
    "defaultMode": "acceptEdits"
  },
  
  "disallowedTools": [],
  
  "env": {
    "CLAUDE_CODE_TASK_LIST_ID": "project-main",
    "MAX_THINKING_TOKENS": "10000",
    "BASH_DEFAULT_TIMEOUT_MS": "300000",
    "NODE_ENV": "development"
  },
  
  "hooks": {
    "SessionStart": [],
    "SessionStop": [],
    "PreToolUse": {},
    "PostToolUse": {},
    "Notification": []
  },
  
  "mcpServers": {},
  "enabledPlugins": {},
  "lspServers": {},
  
  "sandbox": {
    "enabled": false,
    "allowNetworking": true,
    "additionalMounts": []
  }
}
```

### 3.2 Permission Patterns Reference

```yaml
permission_patterns:
  # Read permissions
  read_patterns:
    - "Read(./**)"                    # All project files
    - "Read(~/.config/git/**)"        # Specific external config
    - "Read(!./.env)"                 # Exclude specific file
    - "Read(!./secrets/**)"           # Exclude directory
    
  # Edit permissions
  edit_patterns:
    - "Edit(./**)"                    # All project files
    - "Edit(./src/**/*.ts)"          # TypeScript files only
    - "Edit(!./node_modules/**)"      # Exclude node_modules
    
  # Bash permissions (CAUTION: fragile argument constraints)
  bash_patterns:
    - "Bash(npm run *)"               # npm scripts
    - "Bash(git diff*)"               # git operations
    - "Bash(pytest *)"                # Python tests
    - "Bash(cargo *)"                 # Rust toolchain
    # WARNING: Argument patterns can be bypassed with flags/shell tricks
    
  # MCP permissions
  mcp_patterns:
    - "MCP(*)"                        # All MCP servers
    - "MCP(github:*)"                 # Specific server
    - "MCP(filesystem:read_file)"     # Specific tool
    
  # Task permissions
  task_patterns:
    - "Task(*)"                       # Allow all subagents
    - "Task(code-reviewer)"           # Specific subagent
    
  # WebFetch permissions
  webfetch_patterns:
    - "WebFetch(*)"                   # All URLs
    - "WebFetch(https://docs.*)"      # Documentation sites only
```

---

## 4. HOOKS SYSTEM

### 4.1 Hook Event Types

```yaml
hook_events:
  SessionStart:
    trigger: "When Claude Code session begins"
    matcher: "startup"
    use_cases:
      - "Initialize environment"
      - "Load project context"
      - "Set up conda/virtualenv"
      - "Log session start"
    stdin_data: null
    
  SessionStop:
    trigger: "When Claude Code session ends"
    matcher: "shutdown"
    use_cases:
      - "Cleanup temporary files"
      - "Log session end"
      - "Generate session summary"
    stdin_data: null
    
  PreToolUse:
    trigger: "Before any tool executes"
    matchers:
      - "Edit"
      - "Write"
      - "Bash"
      - "Read"
      - "WebFetch"
      - "MCP"
      - "Task"
    use_cases:
      - "Security validation"
      - "Add context to operations"
      - "Block dangerous operations"
      - "Log tool usage"
    stdin_data:
      session_id: "string"
      tool_name: "string"
      tool_input: "object"
    response_schema:
      block: "boolean (PreToolUse only)"
      message: "string (shown to user)"
      feedback: "string (non-blocking info)"
      additionalContext: "string (injected into tool)"
      suppressOutput: "boolean"
      
  PostToolUse:
    trigger: "After tool completes"
    matchers: ["Edit", "Write", "Bash", "Read", "WebFetch", "MCP", "Task"]
    use_cases:
      - "Log changes"
      - "Run linters/formatters"
      - "Update documentation"
      - "Trigger notifications"
    stdin_data:
      session_id: "string"
      tool_name: "string"
      tool_input: "object"
      tool_output: "object"
      
  Notification:
    trigger: "When Claude wants to notify user"
    use_cases:
      - "Desktop notifications"
      - "Sound alerts"
      - "External logging"
```

### 4.2 Hook Configuration Examples

```json
{
  "hooks": {
    "SessionStart": [{
      "matcher": "startup",
      "hooks": [{
        "type": "command",
        "command": "echo '[${CLAUDE_SESSION_ID}] Session started at $(date)' >> .claude/session-log.txt"
      }, {
        "type": "command",
        "command": "echo 'conda activate myenv' >> \"$CLAUDE_ENV_FILE\""
      }]
    }],
    
    "PreToolUse": {
      "Edit": [{
        "type": "command",
        "command": "python .claude/hooks/validate-edit.py",
        "timeout": 5000
      }],
      "Bash": [{
        "type": "command",
        "command": "python .claude/hooks/block-dangerous.py"
      }],
      "Write": [{
        "type": "command",
        "command": "echo '{\"additionalContext\": \"Follow project naming conventions\"}'"
      }]
    },
    
    "PostToolUse": {
      "Edit": [{
        "type": "command",
        "command": "git diff --no-color > .claude/diffs/${CLAUDE_SESSION_ID}-$(date +%s).diff"
      }, {
        "type": "command",
        "command": "npm run lint:fix -- --quiet"
      }],
      "Write": [{
        "type": "command",
        "command": "prettier --write \"$file_path\" 2>/dev/null || true"
      }]
    },
    
    "SessionStop": [{
      "matcher": "shutdown",
      "hooks": [{
        "type": "command",
        "command": "echo '[${CLAUDE_SESSION_ID}] Session ended at $(date)' >> .claude/session-log.txt"
      }]
    }],
    
    "Notification": [{
      "type": "command",
      "command": "osascript -e 'display notification \"$message\" with title \"Claude Code\"'"
    }]
  }
}
```

### 4.3 Hook Response Schema (PreToolUse)

```javascript
// Return JSON to stdout for PreToolUse hooks
// Exit code 2 = block operation

// Block operation
{
  "block": true,
  "message": "Operation blocked: Cannot modify .env files"
}

// Add context without blocking
{
  "additionalContext": "Remember to follow TypeScript strict mode guidelines",
  "feedback": "TypeScript file detected, applying strict checks"
}

// Allow with suppressed output
{
  "suppressOutput": true
}

// Continue processing (hook decides not to intervene)
{
  "continue": true
}
```

---

## 5. SUBAGENTS & TASK ORCHESTRATION

### 5.1 Built-in Subagents

```yaml
builtin_subagents:
  Explore:
    purpose: "Codebase exploration and search"
    tools: ["Read", "Grep", "Glob"]
    characteristics:
      - "Read-only"
      - "Fast execution"
      - "Optimized for file discovery"
    thoroughness_levels:
      - "quick"
      - "medium"
      - "very thorough"
      
  Plan:
    purpose: "Task planning and decomposition"
    model: "opus (default)"
    characteristics:
      - "Extended thinking"
      - "Multi-step planning"
      - "Dependency analysis"
      
  General:
    purpose: "Flexible task execution"
    tools: "Inherits from parent"
    characteristics:
      - "Can perform any delegated task"
      - "Isolated context window"
```

### 5.2 Custom Subagent Definition

```markdown
---
name: code-reviewer
description: Reviews code for quality, security, and maintainability
model: sonnet
tools:
  - Read
  - Grep
  - Glob
permission-mode: bypassPermissions
hooks: []
skills: []
color: blue
---

# Code Reviewer Agent

You are a senior code reviewer focused on:

## Review Criteria
1. **Security**: Check for vulnerabilities, injection risks, exposed secrets
2. **Performance**: Identify N+1 queries, memory leaks, inefficient algorithms
3. **Maintainability**: Ensure code follows SOLID principles
4. **Testing**: Verify adequate test coverage

## Output Format
```json
{
  "summary": "Brief overview",
  "issues": [
    {
      "severity": "critical|high|medium|low",
      "file": "path/to/file.ts",
      "line": 42,
      "description": "Issue description",
      "suggestion": "How to fix"
    }
  ],
  "approved": true|false
}
```

## Constraints
- Never modify files
- Always provide actionable feedback
- Reference specific line numbers
```

### 5.3 Task Tool Orchestration Patterns

```yaml
orchestration_patterns:
  
  parallel_exploration:
    description: "Search codebase with multiple agents"
    prompt_template: |
      Explore the codebase using {n} parallel tasks.
      Each agent should explore different directories:
      - Agent 1: src/frontend/
      - Agent 2: src/backend/
      - Agent 3: src/shared/
      - Agent 4: tests/
    constraints:
      max_concurrent: 10
      token_overhead_per_task: 20000
      
  sequential_pipeline:
    description: "Assembly line processing"
    stages:
      - name: "planning"
        agent: "Plan"
        output: "implementation_spec"
      - name: "implementation"
        agent: "code-writer"
        input: "implementation_spec"
        output: "code_changes"
      - name: "review"
        agent: "code-reviewer"
        input: "code_changes"
        output: "review_feedback"
        
  fan_out_fan_in:
    description: "Parallel work with aggregation"
    phases:
      fan_out:
        agents: ["frontend-specialist", "backend-specialist", "test-writer"]
        parallel: true
      fan_in:
        agent: "integrator"
        aggregates_results: true
```

### 5.4 Subagent Limitations

```yaml
subagent_constraints:
  nesting: "Subagents cannot spawn other subagents"
  concurrency: "Maximum 10 concurrent tasks"
  queuing: "Additional tasks queued until slot available"
  batching: "Tasks execute in batches, not dynamically"
  context_isolation: "Each task has separate 200k context window"
  token_overhead: "~20k tokens per task initialization"
  communication: "No direct inter-agent communication"
  result_handling: "Only parent receives results"
```

---

## 6. SKILLS SYSTEM

### 6.1 Skill Definition Format

```markdown
---
name: tdd-workflow
description: Test-Driven Development workflow with red-green-refactor cycle
auto-load: true
user-invocable: true
tools:
  - Read
  - Edit
  - Write
  - Bash
---

# TDD Workflow Skill

Session: ${CLAUDE_SESSION_ID}
Task List: ${CLAUDE_CODE_TASK_LIST_ID}

## Workflow Steps

### 1. RED Phase - Write Failing Test
```bash
# Create test file
cat > tests/test_${feature}.py << 'TEST'
import pytest
from src.${module} import ${function}

def test_${feature}_basic():
    # Arrange
    input_data = ...
    
    # Act
    result = ${function}(input_data)
    
    # Assert
    assert result == expected_output
TEST

# Run test (should fail)
pytest tests/test_${feature}.py -v
```

### 2. GREEN Phase - Minimal Implementation
Implement the minimum code to make tests pass.

### 3. REFACTOR Phase - Improve Code Quality
- Remove duplication
- Improve naming
- Optimize performance
- Ensure 80%+ coverage

### 4. Verification
```bash
pytest --cov=src --cov-report=term-missing
```
```

### 6.2 Skill Discovery & Activation

```yaml
skill_locations:
  user_level: "~/.claude/skills/"
  project_level: ".claude/skills/"
  plugin_level: "{plugin_root}/skills/"
  
skill_activation:
  automatic: "When description matches task context"
  manual: "/skills command or direct reference"
  
skill_frontmatter:
  required:
    - name
    - description
  optional:
    - auto-load: "boolean (default: false)"
    - user-invocable: "boolean (default: true)"
    - tools: "array of allowed tools"
    - model: "override model for skill"
```

---

## 7. MCP (MODEL CONTEXT PROTOCOL)

### 7.1 MCP Configuration

```json
{
  "mcpServers": {
    "github": {
      "command": "npx",
      "args": ["-y", "@anthropic/mcp-server-github"],
      "env": {
        "GITHUB_TOKEN": "${GITHUB_TOKEN}"
      }
    },
    "filesystem": {
      "command": "npx",
      "args": ["-y", "@anthropic/mcp-server-filesystem", "/path/to/allowed/dir"]
    },
    "puppeteer": {
      "command": "npx",
      "args": ["-y", "@anthropic/mcp-server-puppeteer"]
    },
    "postgres": {
      "command": "npx",
      "args": ["-y", "@anthropic/mcp-server-postgres"],
      "env": {
        "DATABASE_URL": "${DATABASE_URL}"
      }
    },
    "linear": {
      "type": "sse",
      "url": "https://mcp.linear.app/sse",
      "headers": {
        "Authorization": "Bearer ${LINEAR_API_KEY}"
      }
    }
  }
}
```

### 7.2 MCP CLI Commands

```bash
# Add MCP server (stdio transport)
claude mcp add <name> <command> [args...]
claude mcp add github npx -y @anthropic/mcp-server-github

# Add MCP server (SSE transport)
claude mcp add --transport sse linear https://mcp.linear.app/sse

# Add MCP server (HTTP transport)
claude mcp add --transport http myapi https://api.example.com/mcp

# Add with environment variables
claude mcp add --env API_KEY=xxx -- myserver npx -y @my/mcp-server

# List configured servers
claude mcp list

# Remove server
claude mcp remove <name>

# Debug MCP issues
claude --mcp-debug
```

### 7.3 Project-Scoped MCP (.mcp.json)

```json
{
  "mcpServers": {
    "jira": {
      "command": "npx",
      "args": ["-y", "@anthropic/mcp-server-jira"],
      "env": {
        "JIRA_URL": "https://company.atlassian.net",
        "JIRA_EMAIL": "${JIRA_EMAIL}",
        "JIRA_API_TOKEN": "${JIRA_API_TOKEN}"
      }
    },
    "sentry": {
      "command": "npx",
      "args": ["-y", "@anthropic/mcp-server-sentry"],
      "env": {
        "SENTRY_AUTH_TOKEN": "${SENTRY_AUTH_TOKEN}",
        "SENTRY_ORG": "my-org"
      }
    }
  }
}
```

---

## 8. CUSTOM SLASH COMMANDS

### 8.1 Command Definition Format

```markdown
---
name: implement-feature
description: Implement a new feature with TDD approach
argument-hint: [feature-name] [priority]
allowed-tools:
  - Read
  - Edit
  - Write
  - Bash(npm run test*)
  - Bash(git add*)
  - Bash(git commit*)
---

# Feature Implementation: $1

Priority: $2

## Context
- Current git status: !`git status --short`
- Current branch: !`git branch --show-current`
- Recent commits: !`git log --oneline -5`

## Implementation Steps

1. **Analyze Requirements**
   - Review related code in src/
   - Check existing tests in tests/
   - Identify dependencies

2. **Write Tests First (TDD)**
   - Create test file: tests/test_$1.py
   - Define test cases covering edge cases
   - Run tests to confirm they fail

3. **Implement Feature**
   - Create minimal implementation
   - Ensure all tests pass
   - Add error handling

4. **Refactor & Document**
   - Improve code quality
   - Add docstrings
   - Update README if needed

5. **Commit Changes**
   ```bash
   git add -A
   git commit -m "feat($1): implement $1 feature"
   ```

## Constraints
- Follow project coding standards
- Maintain 80%+ test coverage
- No breaking changes to existing APIs
```

### 8.2 Command Locations

```yaml
command_locations:
  user_level: "~/.claude/commands/"
  project_level: ".claude/commands/"
  plugin_level: "{plugin_root}/commands/"
  
command_features:
  arguments: "$1, $2, ... or $ARGUMENTS"
  bash_interpolation: "!`command` syntax"
  file_reference: "@file.md for inclusion"
  tool_restrictions: "allowed-tools frontmatter"
```

---

## 9. RULES SYSTEM

### 9.1 Rules Directory Structure

```
.claude/rules/
├── security.md          # Security guidelines
├── coding-style.md      # Code style rules
├── testing.md           # Testing requirements
├── git-workflow.md      # Git conventions
└── architecture.md      # Architecture decisions
```

### 9.2 Rule File Format

```markdown
# Security Rules

## MUST DO
- Never hardcode secrets, API keys, or credentials
- Always validate and sanitize user input
- Use parameterized queries for database operations
- Implement proper authentication checks

## MUST NOT
- Never commit .env files
- Never log sensitive data
- Never use eval() or exec() with user input
- Never disable SSL verification

## FILE RESTRICTIONS
- .env* files: READ DENIED
- secrets/: READ DENIED
- credentials.json: READ DENIED

## WHEN REVIEWING CODE
1. Check for exposed secrets
2. Verify input validation
3. Confirm proper error handling
4. Ensure secure dependencies
```

---

## 10. PLUGINS SYSTEM

### 10.1 Plugin Structure

```
my-plugin/
├── .claude-plugin/
│   └── plugin.json          # Plugin manifest (ONLY file in this dir)
├── commands/                # Custom commands
│   └── my-command.md
├── agents/                  # Subagent definitions
│   └── my-agent.md
├── skills/                  # Skills
│   └── my-skill/
│       └── SKILL.md
├── hooks/                   # Hook configurations
│   └── hooks.json
├── .mcp.json               # MCP server definitions
├── .lsp.json               # LSP configurations
├── scripts/                # Utility scripts
│   └── helper.sh
└── CHANGELOG.md
```

### 10.2 Plugin Manifest (plugin.json)

```json
{
  "name": "my-enterprise-plugin",
  "version": "1.2.0",
  "description": "Enterprise development workflow automation",
  "author": {
    "name": "DevOps Team",
    "email": "devops@company.com"
  },
  "license": "MIT",
  "keywords": ["enterprise", "workflow", "automation"],
  
  "commands": ["./custom/commands/"],
  "agents": "./agents/",
  "skills": "./skills/",
  "hooks": "./hooks/hooks.json",
  "mcpServers": "./.mcp.json",
  "lspServers": "./.lsp.json",
  "outputStyles": "./styles/"
}
```

### 10.3 Plugin CLI Commands

```bash
# Install from marketplace
claude plugin install <name>@<marketplace>
claude plugin install formatter@claude-plugins-official

# Install with scope
claude plugin install <name>@<marketplace> --scope project  # Shared with team
claude plugin install <name>@<marketplace> --scope local    # Gitignored
claude plugin install <name>@<marketplace> --scope user     # Default

# Manage plugins
claude plugin list
claude plugin enable <name>
claude plugin disable <name>
claude plugin remove <name>
claude plugin update <name>
```

---

## 11. LSP (LANGUAGE SERVER PROTOCOL)

### 11.1 LSP Configuration

```json
{
  "lspServers": {
    "typescript": {
      "command": "typescript-language-server",
      "args": ["--stdio"],
      "extensionToLanguage": {
        ".ts": "typescript",
        ".tsx": "typescriptreact",
        ".js": "javascript",
        ".jsx": "javascriptreact"
      },
      "initializationOptions": {
        "preferences": {
          "quotePreference": "single",
          "importModuleSpecifierPreference": "relative"
        }
      }
    },
    "python": {
      "command": "pyright-langserver",
      "args": ["--stdio"],
      "extensionToLanguage": {
        ".py": "python"
      }
    },
    "rust": {
      "command": "rust-analyzer",
      "args": [],
      "extensionToLanguage": {
        ".rs": "rust"
      }
    }
  }
}
```

### 11.2 LSP via Plugins

```json
{
  "enabledPlugins": {
    "typescript-lsp@claude-plugins-official": true,
    "pyright-lsp@claude-plugins-official": true,
    "rust-analyzer-lsp@claude-plugins-official": true
  }
}
```

---

## 12. CHECKPOINTING & RECOVERY

### 12.1 Checkpoint System

```yaml
checkpointing:
  automatic: true
  trigger: "Before each file edit"
  storage: ".claude/checkpoints/"
  
  commands:
    view_checkpoints: "Esc + Esc"
    rewind: "/rewind"
    restore_options:
      - "code only"
      - "conversation only"
      - "both"
      
  limitations:
    - "Only tracks Claude's edits"
    - "Does not track user edits"
    - "Does not track bash command effects"
    - "Recommend using with version control"
```

### 12.2 Session Resume

```bash
# Resume last session
claude --resume

# Continue last conversation
claude --continue

# Resume specific session
claude --resume-session <session-id>
```

---

## 13. CLI FLAGS REFERENCE

### 13.1 Common Flags

```bash
# Session control
claude --resume                      # Resume last session
claude --continue                    # Continue last conversation
claude --resume-session <id>         # Resume specific session

# Model selection
claude --model opus                  # Use Opus model
claude --model sonnet                # Use Sonnet model
claude --model <full-model-string>   # Use specific model version

# Permission modes
claude --permission-mode plan        # Plan-only mode (no modifications)
claude --permission-mode edit        # Standard edit mode
claude --dangerously-skip-permissions # Bypass all permission checks

# Context management
claude --add-dir /path/to/dir        # Add directory to context
claude --system-prompt "..."         # Override system prompt

# Output control
claude -p "prompt"                   # Print mode (non-interactive)
claude -p "prompt" --output-format json      # JSON output
claude -p "prompt" --output-format stream-json  # Streaming JSON

# Debugging
claude --debug                       # Enable debug logging
claude --mcp-debug                   # MCP-specific debugging
claude --verbose                     # Verbose output
```

### 13.2 Headless Mode (CI/CD)

```bash
# Basic headless execution
claude -p "Fix all TypeScript errors" --output-format json

# With permission bypass (for trusted automation)
claude -p "Run tests and fix failures" --dangerously-skip-permissions

# Pipeline integration
claude -p "Analyze code quality" --output-format json | jq '.result'

# GitHub Actions example
- name: Claude Code Analysis
  run: |
    claude -p "Review changes in this PR and suggest improvements" \
      --output-format json \
      > analysis.json
```

---

## 14. CODEBASE IMPROVEMENT PLANNING

### 14.1 Analysis Command Template

```markdown
---
name: analyze-codebase
description: Comprehensive codebase analysis for improvement planning
allowed-tools:
  - Read
  - Grep
  - Glob
  - Bash(wc*)
  - Bash(find*)
  - Bash(git log*)
  - Task
---

# Codebase Analysis Report

Session: ${CLAUDE_SESSION_ID}
Date: !`date -Iseconds`

## 1. Project Structure Analysis

### Directory Statistics
!`find . -type f -name "*.ts" -o -name "*.tsx" -o -name "*.js" -o -name "*.jsx" | wc -l` TypeScript/JavaScript files
!`find . -type f -name "*.py" | wc -l` Python files
!`find . -type f -name "*.go" | wc -l` Go files
!`find . -type f -name "*.rs" | wc -l` Rust files

### Code Metrics
!`cloc . --json 2>/dev/null || echo "cloc not installed"`

## 2. Quality Assessment

Launch parallel analysis agents for:
- Code duplication detection
- Security vulnerability scan
- Dependency audit
- Test coverage analysis
- Performance hotspot identification

## 3. Technical Debt Identification

Categories to assess:
- [ ] Outdated dependencies
- [ ] Missing tests
- [ ] Code duplication
- [ ] Inconsistent patterns
- [ ] Documentation gaps
- [ ] Performance issues
- [ ] Security vulnerabilities

## 4. Improvement Recommendations

Priority levels:
- P0: Critical (security, breaking issues)
- P1: High (major tech debt)
- P2: Medium (code quality)
- P3: Low (nice-to-have)

## 5. Implementation Roadmap

Generate phased improvement plan with:
- Estimated effort
- Dependencies
- Risk assessment
- Success metrics
```

### 14.2 Improvement Execution Workflow

```yaml
improvement_workflow:
  phase_1_discovery:
    duration: "1-2 sessions"
    activities:
      - "Run codebase analysis"
      - "Identify critical issues"
      - "Map dependencies"
      - "Document current state"
    output: "analysis_report.md"
    
  phase_2_planning:
    duration: "1 session"
    activities:
      - "Prioritize improvements"
      - "Define success criteria"
      - "Create task breakdown"
      - "Estimate effort"
    output: "improvement_plan.md"
    
  phase_3_execution:
    approach: "iterative"
    batch_size: "1-3 related changes"
    workflow:
      - "Create feature branch"
      - "Implement changes"
      - "Run tests"
      - "Code review (subagent)"
      - "Commit with conventional format"
    checkpointing: "before each batch"
    
  phase_4_validation:
    activities:
      - "Run full test suite"
      - "Performance benchmarks"
      - "Security scan"
      - "Documentation update"
    output: "validation_report.md"
```

---

## 15. SHELL ALIASES & HELPERS

```bash
# ============================================
# CLAUDE CODE ALIASES
# ============================================

# Basic shortcuts
alias cc='claude'
alias ccr='claude --resume'
alias ccc='claude --continue'
alias ccp='claude --permission-mode plan'

# Task-specific sessions
alias cc-dev='CLAUDE_CODE_TASK_LIST_ID=dev-main claude'
alias cc-refactor='CLAUDE_CODE_TASK_LIST_ID=refactor claude'
alias cc-test='CLAUDE_CODE_TASK_LIST_ID=testing claude'
alias cc-docs='CLAUDE_CODE_TASK_LIST_ID=documentation claude'
alias cc-review='CLAUDE_CODE_TASK_LIST_ID=code-review claude'

# Model-specific
alias cc-opus='claude --model opus'
alias cc-sonnet='claude --model sonnet'
alias cc-haiku='claude --model haiku'

# Dangerous but useful
alias cc-yolo='claude --dangerously-skip-permissions'

# Debugging
alias cc-debug='claude --debug --mcp-debug --verbose'

# Headless/CI
alias cc-ci='claude -p --output-format json'

# ============================================
# HELPER FUNCTIONS
# ============================================

# Quick codebase analysis
cc-analyze() {
    claude -p "Analyze the codebase structure and provide a summary" \
           --output-format json | jq '.'
}

# Fix linting errors automatically
cc-lint-fix() {
    claude -p "Find and fix all linting errors in the codebase" \
           --dangerously-skip-permissions
}

# Generate PR description
cc-pr-desc() {
    claude -p "Generate a PR description for the changes in this branch compared to main" \
           --output-format json | jq -r '.result'
}

# Session with context
cc-with-context() {
    local context_file="${1:-CLAUDE.md}"
    claude --system-prompt "$(cat $context_file)"
}
```

---

## 16. CLAUDE.md BEST PRACTICES

### 16.1 Recommended Structure

```markdown
# Project: [Name]

## Overview
[Brief project description - 2-3 sentences]

## Tech Stack
- Language: TypeScript 5.x
- Framework: Next.js 14
- Database: PostgreSQL 15
- ORM: Prisma
- Testing: Jest + React Testing Library

## Directory Structure
```
src/
├── app/           # Next.js app router
├── components/    # React components
├── lib/           # Utility functions
├── hooks/         # Custom React hooks
├── types/         # TypeScript types
└── services/      # API clients
```

## Build & Run Commands
```bash
npm run dev        # Start dev server
npm run build      # Production build
npm run test       # Run tests
npm run lint       # Lint code
npm run typecheck  # TypeScript check
```

## Code Standards
- Use functional components with hooks
- Prefer named exports
- Maximum file length: 300 lines
- Test coverage minimum: 80%

## Git Workflow
- Branch naming: `feature/`, `fix/`, `refactor/`
- Commit format: `type(scope): description`
- Always create PR for main branch

## Architecture Decisions
[Key architectural decisions and rationale]

## Current Priorities
1. [Priority 1]
2. [Priority 2]
3. [Priority 3]

## Known Issues / Tech Debt
- [ ] [Issue 1]
- [ ] [Issue 2]

## Context for Claude
- Session management: Use CLAUDE_CODE_TASK_LIST_ID
- Before /clear: Use /checkpoint
- Prefer small, focused commits
```

### 16.2 Anti-Patterns to Avoid

```yaml
claude_md_antipatterns:
  - "Including binary file paths (images, PDFs)"
  - "Embedding large code blocks"
  - "Including @file references to non-essential files"
  - "Storing secrets or credentials"
  - "Overly verbose descriptions"
  - "Outdated information"
  - "Conflicting instructions"
```

---

## 17. VERIFICATION CHECKLIST

```yaml
verification_checklist:
  configuration:
    - "[ ] .claude/settings.json exists with proper structure"
    - "[ ] Environment variables exported in shell RC"
    - "[ ] Permissions configured appropriately"
    - "[ ] Hooks defined and tested"
    
  skills_and_commands:
    - "[ ] .claude/skills/ directory exists"
    - "[ ] .claude/commands/ directory exists"
    - "[ ] Skills visible in /skills command"
    - "[ ] Commands visible in / menu"
    
  mcp_integration:
    - "[ ] MCP servers configured in .mcp.json"
    - "[ ] Server connections verified"
    - "[ ] Tool permissions set correctly"
    
  subagents:
    - "[ ] Custom agents defined in .claude/agents/"
    - "[ ] Agent permissions appropriate"
    - "[ ] Parallel execution tested"
    
  session_management:
    - "[ ] CLAUDE_CODE_TASK_LIST_ID strategy defined"
    - "[ ] Session logging working"
    - "[ ] Checkpoint system functional"
    - "[ ] Resume capability verified"
    
  project_memory:
    - "[ ] CLAUDE.md up to date"
    - "[ ] Rules defined in .claude/rules/"
    - "[ ] No sensitive data in memory files"
```

---

## 18. QUICK START COMMANDS

```bash
# Initialize Claude Code configuration
mkdir -p .claude/{skills,commands,agents,rules,plans,checkpoints}

# Create minimal settings.json
cat > .claude/settings.json << 'EOF'
{
  "model": "claude-sonnet-4-5-20250929",
  "plansDirectory": "./.claude/plans",
  "permissions": {
    "allow": ["Bash(npm run *)", "Bash(git diff*)", "Read(./**)"],
    "defaultMode": "acceptEdits"
  },
  "hooks": {
    "SessionStart": [{
      "matcher": "startup",
      "hooks": [{"type": "command", "command": "echo 'Session started' >> .claude/session.log"}]
    }]
  }
}
EOF

# Add to .gitignore
echo ".claude/settings.local.json" >> .gitignore
echo ".claude/checkpoints/" >> .gitignore
echo ".claude/session.log" >> .gitignore

# Start Claude Code
claude

# Inside Claude Code
> /skills          # View available skills
> /agents          # View available agents
> /config          # Open configuration UI
```

---

**END OF MACHINE-READABLE REFERENCE**

```yaml
document_footer:
  generated_by: "Claude (claude.ai)"
  purpose: "Claude Code CLI configuration reference"
  usage: "Place in project root for Claude Code to read"
  updates: "Regenerate when Claude Code version changes"
```
