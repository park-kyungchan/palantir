# Agent Teams — Architecture, Coordination & Task Sharing

> Verified: 2026-02-17 via claude-code-guide, cross-referenced with code.claude.com

---

## 1. Overview

Agent Teams enable multiple Claude Code instances to coordinate as a team. One session becomes the **team lead**, spawning **teammates** — each a full, independent Claude Code instance with its own context window.

### Enabling

```json
// settings.json env block:
"CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS": "1"
```

Or set `teammateMode` in settings.json: `"in-process"`, `"tmux"`, or `"auto"` (default — split panes if inside tmux, otherwise in-process). CLI flag: `claude --teammate-mode in-process`.

### Core Architecture

- Shared task list with dependency tracking
- Inbox-based messaging for inter-agent communication
- Teammates can self-claim work as they finish tasks

---

## 2. Team Lifecycle

```
1. spawnTeam("team-name")     → Creates team config at ~/.claude/teams/{team-name}/
2. spawn(teammate)            → Launches teammate in tmux pane with unique agent ID
3. createTask(tasks)          → Creates task JSON files at ~/.claude/tasks/{team-name}/
4. [Teammates work]           → Claim tasks, execute, communicate via inbox
5. sendMessage(target, text)  → Write to target's inbox JSON
6. requestShutdown(target)    → Gracefully terminate teammate
7. cleanup                    → Remove team config and task files
```

### TeammateTool Operations

| Operation | Who Can Call | Effect |
|-----------|-------------|--------|
| `spawnTeam` | Lead | Create team infrastructure |
| `spawn` | Lead | Launch a new teammate |
| `sendMessage` / `write` | Lead → anyone; Teammate → any teammate or lead | Write to recipient's inbox |
| `broadcast` | Lead or Teammate | Message all teammates (costly) |
| `requestShutdown` | Lead | Ask teammate to terminate |
| `approveShutdown` | Lead | Approve teammate shutdown request |
| `cleanup` | Lead | Remove team resources |
| `createTask` | Lead | Add tasks to shared task list |
| `updateTask` | Lead or assigned teammate | Change task status/details |
| `claimTask` | Teammate | Take ownership of a pending task |

### Mailbox System

The official docs refer to the messaging infrastructure as the **"Mailbox"** system. Each message in the inbox JSON follows this structure:

```json
{
  "from": "sender-name",
  "text": "full content",
  "summary": "5-10 word preview",
  "timestamp": "2026-02-05T18:56:10.615Z",
  "read": false
}
```

- `text`: Full message content delivered to recipient
- `summary`: Brief preview used for UI display (not the full message)
- `read`: Toggled to `true` once the recipient processes the message

### Display Modes

- **Split panes**: Each teammate gets own pane. Requires tmux or iTerm2 with `it2` CLI
- **In-process**: All teammates in main terminal. Shift+Up/Down to select. Any terminal
- **Auto** (default): Split panes if inside tmux, otherwise in-process

---

## 3. Coordination Channels

There are exactly two coordination mechanisms:

1. **Task files on disk** (`~/.claude/tasks/{team-name}/*.json`)
2. **Inbox messaging via SendMessage** (`~/.claude/teams/{team-name}/inboxes/*.json`)

**There is no shared memory.** No sockets, no pipes, no IPC. Every coordination action is file I/O.

### Channel 1: Task Files

Each task is an independent JSON file. State machine: `pending → in_progress → completed`.

**Claiming**: Teammate reads task directory, finds pending task, atomically updates JSON (status + owner). File locking prevents race conditions.

**Concurrency control**: `tempfile + os.replace` for atomic writes, `filelock` library for cross-platform locking.

**Dependency tracking**: Tasks support DAGs via `blocked_by` field. Completing a blocking task automatically unblocks downstream tasks.

**Location**: `~/.claude/tasks/{team-name}/{n}.json`

### Channel 2: Inbox / Mailbox (SendMessage)

The official docs call this the **"Mailbox"** system.

**Location**: `~/.claude/teams/{team-name}/inboxes/{agent-id}.json`

**Tool availability**: SendMessage is part of TeammateTool -- automatically available to ALL teammates. It is NOT subject to the agent's `tools` allowlist. This is infrastructure-level tooling.

**Team discovery**: Teammates can read `~/.claude/teams/{team-name}/config.json` to discover other team members. The config contains a `members` array with `name`, `agentId`, and `agentType` for each teammate.

**Communication constraints**:
- Lead can message anyone
- Teammates can message other teammates directly (not lead-only)
- `broadcast` sends to all teammates (costly — use sparingly)
- Each agent reads only its own inbox file
- Sending = appending entry to recipient's inbox JSON, protected by file locks

**"Automatic delivery"**: Claude Code checks inbox on each API turn — NOT OS-level push. "Automatic" means user doesn't need to poll manually.

### Sequence Diagram

```
Lead                    Worker-1                  Worker-2
  │                        │                         │
  ├─ spawnTeam("feat")     │                         │
  ├─ createTask(#1,#2,#3)  │                         │
  ├─ spawn(worker-1)───────┤                         │
  ├─ spawn(worker-2)───────┼─────────────────────────┤
  │                   claim #1 (file lock)       claim #2 (file lock)
  │                   tasks/1.json→in_progress   tasks/2.json→in_progress
  │                   [executes task...]         [executes task...]
  │                   tasks/1.json→completed          │
  │                   ← idle notification             │
  │                   [reads tasks/ dir]              │
  │                   claim #3                        │
  │                        │                    tasks/2.json→completed
```

Every arrow is a file I/O operation.

---

## 4. What Is Isolated vs Shared

| Isolated Per Teammate | Shared Across Team |
|----------------------|-------------------|
| Context window (conversation history) | Project filesystem (codebase) |
| Lead's conversation history | CLAUDE.md, MCP servers, skills |
| Reasoning process, intermediate state | Task JSON files on disk |
| Token usage | Inbox JSON files on disk |
| Memory of what others are doing | Git repository |

### The "No Shared Memory" Implication

When Teammate A develops an insight, that insight exists ONLY in A's context. For B to know:
1. A must `sendMessage` to B (or to lead who relays), OR
2. A must write to disk and B must read it, OR
3. Lead must receive A's result and forward to B

**No automatic propagation of insights between teammates.**

---

## 5. Task Sharing Mechanisms

### Mechanism A: Agent Teams Native Task List

- **Location**: `~/.claude/tasks/{team-name}/`
- **Creation**: Automatic when `spawnTeam` is called
- **Real-time**: File-lock based, near real-time (not strict)
- **Dependency**: Native `blocked_by` field

No manual task_id needed. `spawnTeam` creates infrastructure automatically.

**Task sizing guideline**: Having 5-6 tasks per teammate keeps everyone productive and lets the lead reassign work if someone gets stuck.

**Self-claim after completion**: After finishing a task, a teammate reads the task directory, finds the next unblocked pending task, and claims it autonomously. No lead intervention required for task flow.

### Mechanism B: `CLAUDE_CODE_TASK_LIST_ID` (Independent Sessions)

Enables task sharing between independent sessions NOT part of a team:

```bash
# Terminal A                                    # Terminal B
CLAUDE_CODE_TASK_LIST_ID="my-project" claude     CLAUDE_CODE_TASK_LIST_ID="my-project" claude
```

### Known Limitation: Task Status Lag

A teammate may complete a task but fail to update JSON, blocking downstream tasks.

**Mitigation**: `TaskCompleted` hook with verification logic. Exit code 2 rejects completion, stderr fed back to teammate.

### Heartbeat and Timeout

5-minute timeout. If teammate crashes mid-task, timeout releases tasks back to pool.

### Plan Approval Workflow

Official pattern for requiring teammates to plan before implementing:

1. Spawn teammate with plan approval requirement (mode: `plan`)
2. Teammate works in read-only plan mode until lead approves
3. On plan completion, teammate sends `plan_approval_request` to lead
4. Lead reviews and approves or rejects with feedback
5. If rejected, teammate revises and resubmits
6. Once approved, teammate exits plan mode and implements

Lead makes approval decisions autonomously. Influence via prompt (e.g., "only approve plans that include test coverage").

---

## 6. Cost Model

Each teammate is a separate Claude instance. Solo: ~200K tokens. Team of 3: ~800K. Team of 5: ~1.2M+. Agent Teams use ~7x tokens when teammates run in plan mode.

### Delegate Mode (Shift+Tab)

Delegate mode restricts the lead to coordination-only tools: spawning, messaging, shutting down teammates, and managing tasks. The lead CANNOT write code, run tests, or do implementation work. This is the CC native way to enforce "Lead NEVER edits files directly." Activated via Shift+Tab after team creation.

---

## 7. Known Limitations

- **No session resumption**: `/resume` and `/rewind` do not restore teammates
- **One team per session**: Lead can only manage one team at a time
- **No nested teams**: Teammates cannot spawn their own teams
- **Lead is fixed**: No leadership transfer mechanism
- **Split panes require tmux or iTerm2**: In-process mode works everywhere
- **Token cost**: ~7x in plan mode. Use Sonnet for teammates
- **Delegate mode bug ([#25037](https://github.com/anthropics/claude-code/issues/25037))**: When lead enables delegate mode, teammates inherit restricted tool access -- they lose Read, Write, Edit, Bash, Glob, Grep. Workaround: Do NOT use delegate permissionMode. Enforce "Lead NEVER edits" via CLAUDE.md convention instead.
- **Inbox delivery bug ([#23415](https://github.com/anthropics/claude-code/issues/23415), tmux)**: On macOS tmux backend, teammates may fail to establish messaging layer. Messages sit unread indefinitely. Workaround: Export `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1` in shell init (`.zshrc`) instead of only in `settings.json`.
