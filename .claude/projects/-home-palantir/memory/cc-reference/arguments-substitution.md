# CC Skill Arguments & Substitution Reference
<!-- Last verified: 2026-02-16 via claude-code-guide, all claims confirmed -->
<!-- Update policy: Re-verify after CC version updates -->

## $ARGUMENTS Substitution

### In Skill Body (Markdown Content Below ---)
- `$ARGUMENTS` replaced with entire user input string (in-place substitution)
- `$ARGUMENTS[0]`, `$ARGUMENTS[1]` positional access (0-indexed, space-delimited)
- `$0`, `$1`, `$2` shorthand for positional access
- Can appear multiple times in body (all occurrences replaced)
- Substitution happens AFTER skill L2 is loaded, BEFORE execution begins

### Auto-Append Behavior
- If `$ARGUMENTS` NOT found anywhere in body: `ARGUMENTS: <user_input>` appended at end
- If `$ARGUMENTS` IS found in body: replaced in-place, nothing appended
- No arguments provided by user: replaced with empty string (no error)

### NOT Supported In
- Frontmatter fields (name, description, argument-hint) -- these are static
- Only works in skill body (markdown content below the `---` closing delimiter)

### Examples

```markdown
---
name: my-skill
argument-hint: "[topic]"
description: Processes a topic.
---
# My Skill

Analyze the following topic: $ARGUMENTS

Focus on $ARGUMENTS[0] with depth level $ARGUMENTS[1].
```

User invocation: `/my-skill security high`
- `$ARGUMENTS` becomes `security high`
- `$ARGUMENTS[0]` / `$0` becomes `security`
- `$ARGUMENTS[1]` / `$1` becomes `high`

## Dynamic Context Injection

### Shell Command Execution at Load Time
- Syntax: `` !`shell-command` `` (backtick-wrapped command with `!` prefix)
- Executes at skill load time, output replaces the placeholder in-place
- Runs BEFORE `$ARGUMENTS` substitution
- Use for live codebase state injection

### Examples

```markdown
## Current State
!`git diff --stat`

## Recent Changes
!`git log --oneline -5`

## File Structure
!`find .claude/skills -name SKILL.md | head -20`
```

### Execution Order
1. Skill L2 body loaded into context
2. Dynamic context injection (`` !`commands` ``) executed and replaced
3. `$ARGUMENTS` substitution performed
4. Skill execution begins

### Constraints
- Commands run in project root directory
- Subject to same permission rules as Bash tool
- Output is raw text (no formatting applied)
- Long output may consume significant context budget
- Failed commands: error message replaces placeholder (does not block skill)

## Environment Variables

### Available in Skill Bodies and Hook Commands
- `$CLAUDE_SESSION_ID` -- current session unique identifier
- `$CLAUDE_PROJECT_DIR` -- project root directory path

### Available in Hook Commands Only (stdin JSON)
- `session_id` -- same as CLAUDE_SESSION_ID
- `event` -- hook event name
- `matcher` -- matched pattern value
- `tool_name` -- tool being used (PreToolUse/PostToolUse)
- `tool_input` -- tool call parameters (JSON object)
- `agent_type` -- agent type name (SubagentStart/SubagentStop)

## argument-hint Field

### Purpose
- Shown in `/` autocomplete menu next to skill name
- Indicates expected arguments to the user
- Display only -- does NOT affect argument parsing or validation

### Format
- Single hint: `argument-hint: "[topic]"`
- Multi-arg hint: `argument-hint: "[file] [format]"`
- Action options: `argument-hint: "add [tag] | remove [tag] | list"`
- Optional indicator: `argument-hint: "[query] [--verbose]"`

### Our Usage
- `pre-design-brainstorm`: `[topic]`
- `delivery-pipeline`: `[commit-message]`
- `task-management`: `[action] [args]`
- `self-improve`: `[focus-area]`
- `manage-codebase`: `[full|incremental]`
- `pipeline-resume`: `[resume-from-phase]`
- 28 skills have no argument-hint (invoked by Lead with full context, not user-typed args)

## Shell Command Preprocessing (verified 2026-02-15)

### Syntax
- Skills support `` !`command` `` syntax (backtick-wrapped command with `!` prefix)
- Also referred to as "Dynamic Context Injection" (see above)
- Commands execute BEFORE skill content reaches Claude
- Shell output replaces the placeholder inline

### Execution Details
- Runs at skill load time, after L2 body is loaded
- Executes before `$ARGUMENTS` substitution
- Commands run in project root directory
- Subject to same permission rules as Bash tool
- Failed commands: error message replaces placeholder (does not block skill)

### Common Patterns
```markdown
## PR Context
!`gh pr diff`

## Current Branch State
!`git log --oneline -10`

## Changed Files
!`git diff --name-only HEAD~1`
```

### Practical Notes
- Long output consumes context budget — use `head`, `tail`, or filtering
- Useful for injecting live codebase state into skill execution context
- Cannot use in frontmatter (only in skill body below `---`)

## Skill Invocation Methods

### User Direct (via / menu)
```
/skill-name arg1 arg2 arg3
```
- `$ARGUMENTS` = `arg1 arg2 arg3`
- `$0` = `arg1`, `$1` = `arg2`, `$2` = `arg3`

### Claude Auto-Invoke (via Skill tool)
- Claude calls Skill tool with `name` and `arguments` parameters
- `arguments` string becomes `$ARGUMENTS`
- Requires `disable-model-invocation: false` (or field absent)

### Lead Routing (our pattern)
- Lead invokes skill, passes structured context as arguments
- Arguments often multi-line (plan excerpts, requirement summaries)
- Positional access (`$0`, `$1`) less useful for structured content
- Pattern: use `$ARGUMENTS` for full block, not positional splits
