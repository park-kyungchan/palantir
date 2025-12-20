# Antigravity IDE (Gemini 3.0 Pro) Optimization Guide

> **Date**: 2025-12-20
> **Target**: Orion ODA V3.0 Development
> **Agent**: Antigravity IDE with Gemini 3.0 Pro

---

## Overview

This guide optimizes your Orion ODA development workflow for Antigravity IDE,
leveraging Gemini 3.0 Pro's advanced capabilities:

1. **Structured Output Generation** - Type-safe JSON/Pydantic schemas
2. **Long Context Window** - Full codebase awareness (1M+ tokens)
3. **Native Async Execution** - Parallel task processing
4. **Grounded Code Synthesis** - Context-aware code generation
5. **MCP Integration** - Tool orchestration via Model Context Protocol

---

## 1. MCP Server Configuration

Update your `~/.gemini/antigravity/mcp_config.json` to include ODA-aware tools:

```json
{
  "mcpServers": {
    "github-mcp-server": {
      "command": "python",
      "args": ["-m", "github_mcp_server"],
      "env": {
        "GITHUB_TOKEN": "${GITHUB_TOKEN}"
      },
      "description": "GitHub integration for PRs, Issues, and Repo management"
    },
    "tavily": {
      "command": "npx",
      "args": ["-y", "@anthropic/tavily-mcp-server"],
      "env": {
        "TAVILY_API_KEY": "${TAVILY_API_KEY}"
      },
      "description": "Web search and deep research retrieval"
    },
    "sequential-thinking": {
      "command": "npx",
      "args": ["-y", "@anthropic/sequential-thinking-mcp-server"],
      "description": "Chain-of-thought enforcement for complex reasoning"
    },
    "context7": {
      "command": "npx",
      "args": ["-y", "@anthropic/context7-mcp-server"],
      "description": "Library documentation and API reference access"
    },
    "oda-ontology": {
      "command": "python",
      "args": ["-m", "scripts.mcp.ontology_server"],
      "cwd": "/home/palantir/orion-orchestrator-v2",
      "description": "ODA Ontology inspection and action execution"
    }
  }
}
```

---

## 2. GEMINI.md System Prompt Updates

Add the following sections to `/home/palantir/.gemini/GEMINI.md`:

```markdown
## 0.2 <registry_lock> (ACTION LAYER)

- **[ACTION SUPREMACY]**: All Ontology mutations MUST use ActionType classes.
- **[HAZARD CONTROL]**: Hazardous actions MUST set `requires_proposal = True`.
- **[SIDE EFFECTS]**: Side effects execute ONLY after successful commit.

## 0.3 <gemini_3_pro_directives>

### Code Generation Rules
1. **Always use type hints** - Leverage Pydantic v2 for runtime validation
2. **Async by default** - Use `async/await` for all I/O operations
3. **Structured outputs** - Return Pydantic models, not raw dicts
4. **Error boundaries** - Wrap external calls in try/except with typed errors

### Context Utilization
1. **Full codebase awareness** - Reference existing patterns in `scripts/ontology/`
2. **Import verification** - Check if modules exist before importing
3. **Dependency tracking** - Update requirements.txt when adding packages

### MCP Tool Usage
1. **sequential-thinking** - Use for multi-step reasoning (>3 steps)
2. **context7** - Query before implementing external library integrations
3. **github-mcp-server** - Create PRs for significant changes
4. **oda-ontology** - Inspect registered ActionTypes before creating new ones

## 0.4 <development_workflow>

### Before Writing Code
1. Query existing patterns: `oda-ontology.list_actions()`
2. Check library APIs: `context7.query("pydantic v2 field validation")`
3. Plan reasoning: `sequential-thinking.solve(problem_statement)`

### During Code Generation
1. Follow ODA layer boundaries (Objects → Actions → Side Effects)
2. Use `@register_action` decorator for all ActionTypes
3. Include submission_criteria for all user-facing actions
4. Add docstrings with Args, Returns, Raises sections

### After Code Generation
1. Run type checker: `python -m mypy scripts/`
2. Execute tests: `pytest tests/e2e/ -v`
3. Create PR if tests pass: `github-mcp-server.create_pr(...)`
```

---

## 3. Custom MCP Server for ODA

Create `scripts/mcp/ontology_server.py`:

```python
"""
ODA Ontology MCP Server
=======================

Exposes Ontology inspection and action execution via MCP protocol.
Enables Gemini 3.0 Pro to:
- List registered ActionTypes
- Inspect submission criteria
- Execute actions (with proposal workflow for hazardous ones)
- Query Ontology objects

Start with: python -m scripts.mcp.ontology_server
"""

from __future__ import annotations

import asyncio
import json
import logging
from typing import Any, Dict, List, Optional

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

from scripts.ontology.actions import action_registry, ActionContext
from scripts.ontology.objects.proposal import Proposal, ProposalStatus

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize MCP Server
server = Server("oda-ontology")


@server.list_tools()
async def list_tools() -> List[Tool]:
    """List available ODA tools."""
    return [
        Tool(
            name="list_actions",
            description="List all registered ActionTypes with their metadata",
            inputSchema={
                "type": "object",
                "properties": {
                    "include_hazardous_only": {
                        "type": "boolean",
                        "description": "Filter to only hazardous actions",
                        "default": False
                    }
                }
            }
        ),
        Tool(
            name="inspect_action",
            description="Get detailed information about a specific ActionType",
            inputSchema={
                "type": "object",
                "properties": {
                    "api_name": {
                        "type": "string",
                        "description": "The API name of the action to inspect"
                    }
                },
                "required": ["api_name"]
            }
        ),
        Tool(
            name="execute_action",
            description="Execute an ActionType with given parameters",
            inputSchema={
                "type": "object",
                "properties": {
                    "api_name": {
                        "type": "string",
                        "description": "The API name of the action"
                    },
                    "params": {
                        "type": "object",
                        "description": "Action parameters"
                    },
                    "actor_id": {
                        "type": "string",
                        "description": "ID of the actor executing the action",
                        "default": "gemini-agent"
                    }
                },
                "required": ["api_name", "params"]
            }
        ),
        Tool(
            name="create_proposal",
            description="Create a Proposal for a hazardous action",
            inputSchema={
                "type": "object",
                "properties": {
                    "action_type": {
                        "type": "string",
                        "description": "The action type API name"
                    },
                    "payload": {
                        "type": "object",
                        "description": "Action parameters"
                    },
                    "priority": {
                        "type": "string",
                        "enum": ["low", "medium", "high", "critical"],
                        "default": "medium"
                    }
                },
                "required": ["action_type", "payload"]
            }
        ),
        Tool(
            name="list_pending_proposals",
            description="List all proposals pending review",
            inputSchema={
                "type": "object",
                "properties": {}
            }
        )
    ]


@server.call_tool()
async def call_tool(name: str, arguments: Dict[str, Any]) -> List[TextContent]:
    """Handle tool calls."""
    
    if name == "list_actions":
        include_hazardous_only = arguments.get("include_hazardous_only", False)
        
        if include_hazardous_only:
            actions = action_registry.get_hazardous_actions()
        else:
            actions = action_registry.list_actions()
        
        result = []
        for api_name in sorted(actions):
            action_cls = action_registry.get(api_name)
            result.append({
                "api_name": api_name,
                "object_type": action_cls.object_type.__name__,
                "requires_proposal": getattr(action_cls, "requires_proposal", False),
            })
        
        return [TextContent(type="text", text=json.dumps(result, indent=2))]
    
    elif name == "inspect_action":
        api_name = arguments["api_name"]
        action_cls = action_registry.get(api_name)
        
        if not action_cls:
            return [TextContent(type="text", text=f"Action not found: {api_name}")]
        
        criteria = []
        for c in getattr(action_cls, "submission_criteria", []):
            criteria.append(c.name if hasattr(c, "name") else str(c))
        
        side_effects = []
        for s in getattr(action_cls, "side_effects", []):
            side_effects.append(s.name if hasattr(s, "name") else str(s))
        
        result = {
            "api_name": api_name,
            "object_type": action_cls.object_type.__name__,
            "requires_proposal": getattr(action_cls, "requires_proposal", False),
            "submission_criteria": criteria,
            "side_effects": side_effects,
            "docstring": action_cls.__doc__,
        }
        
        return [TextContent(type="text", text=json.dumps(result, indent=2))]
    
    elif name == "execute_action":
        api_name = arguments["api_name"]
        params = arguments["params"]
        actor_id = arguments.get("actor_id", "gemini-agent")
        
        action_cls = action_registry.get(api_name)
        if not action_cls:
            return [TextContent(type="text", text=f"Action not found: {api_name}")]
        
        # Check if proposal required
        if getattr(action_cls, "requires_proposal", False):
            return [TextContent(
                type="text",
                text=json.dumps({
                    "error": "PROPOSAL_REQUIRED",
                    "message": f"Action '{api_name}' requires proposal approval. Use create_proposal instead.",
                })
            )]
        
        # Execute action
        action = action_cls()
        context = ActionContext(actor_id=actor_id)
        result = await action.execute(params, context)
        
        return [TextContent(type="text", text=json.dumps(result.to_dict(), indent=2))]
    
    elif name == "create_proposal":
        from scripts.ontology.objects.proposal import ProposalPriority
        
        proposal = Proposal(
            action_type=arguments["action_type"],
            payload=arguments["payload"],
            priority=ProposalPriority(arguments.get("priority", "medium")),
            created_by="gemini-agent",
        )
        proposal.submit()
        
        result = {
            "proposal_id": proposal.id,
            "action_type": proposal.action_type,
            "status": proposal.status.value,
            "message": "Proposal created and submitted for review",
        }
        
        return [TextContent(type="text", text=json.dumps(result, indent=2))]
    
    elif name == "list_pending_proposals":
        # In production, this would query a database
        # For now, return a placeholder
        return [TextContent(
            type="text",
            text=json.dumps({
                "message": "Query proposal storage for pending proposals",
                "filter": {"status": "pending"}
            }, indent=2)
        )]
    
    return [TextContent(type="text", text=f"Unknown tool: {name}")]


async def main():
    """Run the MCP server."""
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            server.create_initialization_options()
        )


if __name__ == "__main__":
    asyncio.run(main())
```

---

## 4. Gemini 3.0 Pro Prompt Templates

### Template 1: ActionType Generation

```
You are developing for Orion ODA V3.0. Generate a new ActionType following these rules:

1. Use the @register_action decorator
2. Define ClassVar attributes: api_name, object_type, requires_proposal
3. Add submission_criteria using RequiredField, AllowedValues, MaxLength, CustomValidator
4. Include side_effects (at minimum LogSideEffect)
5. Implement apply_edits() returning (object_or_none, List[EditOperation])

Context from existing actions:
{inspect_action("create_task")}

Generate ActionType for: {user_request}
```

### Template 2: Test Scenario Generation

```
Generate pytest test cases for the following ODA component:

Component: {component_name}
File: {file_path}

Requirements:
1. Use pytest.mark.asyncio for async tests
2. Create fixtures for ActionContext (system, user, admin)
3. Test both success and failure paths
4. Verify submission_criteria validation
5. Check side_effect execution timing

Reference implementation:
{view_file(file_path)}
```

### Template 3: Proposal Workflow Execution

```
Execute the following hazardous action through the proposal workflow:

Action: {action_type}
Parameters: {params}
Priority: {priority}

Steps:
1. Call oda-ontology.inspect_action to verify requirements
2. Call oda-ontology.create_proposal with the parameters
3. Report the proposal_id and next steps for approval

Current pending proposals:
{list_pending_proposals()}
```

---

## 5. Development Workflow Automation

### Pre-commit Hook Integration

Create `.gemini/hooks/pre-commit.py`:

```python
#!/usr/bin/env python
"""
Pre-commit hook for ODA development.
Validates ActionType registrations and submission criteria.
"""

import subprocess
import sys

def check_action_registration():
    """Verify all ActionTypes are properly registered."""
    result = subprocess.run(
        ["python", "-c", """
from scripts.ontology.actions import action_registry
from scripts.ontology.objects import task_actions

actions = action_registry.list_actions()
if len(actions) < 5:
    print(f"WARNING: Only {len(actions)} actions registered")
    exit(1)
print(f"✅ {len(actions)} actions registered")
        """],
        capture_output=True,
        text=True
    )
    
    if result.returncode != 0:
        print(result.stderr)
        return False
    print(result.stdout)
    return True


def check_tests():
    """Run quick validation tests."""
    result = subprocess.run(
        ["pytest", "tests/e2e/", "-v", "--tb=short", "-q"],
        capture_output=True,
        text=True
    )
    
    if result.returncode != 0:
        print("❌ Tests failed:")
        print(result.stdout)
        print(result.stderr)
        return False
    print("✅ All tests passed")
    return True


if __name__ == "__main__":
    success = True
    success = check_action_registration() and success
    success = check_tests() and success
    
    sys.exit(0 if success else 1)
```

---

## 6. Performance Optimization Tips

### Leverage Gemini 3.0 Pro's Capabilities

1. **Long Context Awareness**
   - Include full file contents when asking for modifications
   - Reference multiple related files in a single prompt
   - Use `sequential-thinking` for complex multi-file refactoring

2. **Structured Output**
   - Request Pydantic model definitions instead of raw JSON
   - Ask for TypedDict when interoperating with external APIs
   - Use `@dataclass` for simple data structures

3. **Parallel Tool Calls**
   - Group independent MCP tool calls
   - Use async patterns for concurrent operations
   - Batch database operations when possible

4. **Grounded Code Generation**
   - Always provide existing code context
   - Reference library documentation via `context7`
   - Include error messages when debugging

---

## 7. Debugging Guide

### Common Issues and Solutions

| Issue | Cause | Solution |
|:------|:------|:---------|
| `ActionType not found` | Not imported/registered | Add import to `__init__.py` |
| `InvalidTransitionError` | Wrong proposal state | Check `VALID_TRANSITIONS` map |
| `ValidationError` | Failed submission criteria | Review `submission_criteria` list |
| `Side effect not executing` | Action failed before commit | Check `apply_edits` return value |
| `MCP tool timeout` | Long-running operation | Increase timeout in config |

### Debug Command Sequence

```bash
# 1. Check action registration
python -c "from scripts.ontology.actions import action_registry; print(action_registry.list_actions())"

# 2. Inspect specific action
python -c "
from scripts.ontology.actions import action_registry
from scripts.ontology.objects import task_actions
a = action_registry.get('create_task')
print(f'Criteria: {[c.name for c in a.submission_criteria]}')
"

# 3. Test action execution
python -c "
import asyncio
from scripts.ontology.actions import ActionContext
from scripts.ontology.objects.task_actions import CreateTaskAction

async def test():
    action = CreateTaskAction()
    result = await action.execute(
        {'title': 'Test Task'},
        ActionContext.system()
    )
    print(result.to_dict())

asyncio.run(test())
"
```

---

## 8. Quick Reference Card

### ActionType Checklist

```python
@register_action
class MyAction(ActionType[MyObject]):
    # Required ClassVars
    api_name: ClassVar[str] = "my_action"           # ✅
    object_type: ClassVar[Type] = MyObject          # ✅
    requires_proposal: ClassVar[bool] = False       # ✅
    
    # Validation
    submission_criteria: ClassVar[list] = [         # ✅
        RequiredField("field_name"),
        MaxLength("field_name", 255),
    ]
    
    # Post-commit triggers
    side_effects: ClassVar[list] = [                # ✅
        LogSideEffect(),
    ]
    
    # Implementation
    async def apply_edits(self, params, context):   # ✅
        obj = MyObject(**params)
        edit = EditOperation(...)
        return obj, [edit]
```

### Proposal Workflow

```
DRAFT ──submit()──▶ PENDING ──approve()──▶ APPROVED ──execute()──▶ EXECUTED
                        │
                        └──reject()──▶ REJECTED (terminal)
```

### MCP Tools

| Tool | Purpose |
|:-----|:--------|
| `oda-ontology.list_actions` | Show registered actions |
| `oda-ontology.inspect_action` | Get action details |
| `oda-ontology.execute_action` | Run non-hazardous action |
| `oda-ontology.create_proposal` | Create proposal for hazardous action |
| `sequential-thinking.solve` | Multi-step reasoning |
| `context7.query` | Library documentation |

---

**End of Optimization Guide**
