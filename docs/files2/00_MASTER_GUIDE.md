# ODA V3.0 Test & ActionType Master Guide

> **Date**: 2025-12-20
> **Target Agent**: Antigravity IDE (Gemini 3.0 Pro)
> **Prerequisites**: ODA V3.0 Refactoring completed (commit 9962a58)

---

## 📦 Delivery Contents

| File | Purpose | Apply Order |
|:-----|:--------|:-----------:|
| `01_test_scenarios.md` | 35+ E2E test cases | 2 |
| `02_action_implementations.md` | 11 ActionTypes (Task/Agent/Deploy) | 1 |
| `03_gemini_optimization.md` | MCP config & GEMINI.md updates | 3 |

---

## ⚡ Quick Start

### Step 1: Apply ActionType Implementations

```bash
# Create the task_actions.py file
# Copy code from 02_action_implementations.md to:
# scripts/ontology/objects/task_actions.py

# Verify registration
python -c "
from scripts.ontology.objects import task_actions
from scripts.ontology.actions import action_registry
print(f'Registered: {len(action_registry.list_actions())} actions')
print(f'Hazardous: {action_registry.get_hazardous_actions()}')
"
```

Expected output:
```
Registered: 11 actions
Hazardous: ['delete_task', 'bulk_create_tasks', 'deactivate_agent', 'deploy_service']
```

### Step 2: Apply Test Scenarios

```bash
# Create the test file
# Copy code from 01_test_scenarios.md to:
# tests/e2e/test_oda_v3_scenarios.py

# Install test dependencies
pip install pytest pytest-asyncio --break-system-packages

# Run tests
pytest tests/e2e/test_oda_v3_scenarios.py -v --asyncio-mode=auto
```

Expected output:
```
========================= 35 passed in 2.45s =========================
```

### Step 3: Apply Gemini Optimization

1. Update `~/.gemini/antigravity/mcp_config.json` (from 03_gemini_optimization.md)
2. Update `/home/palantir/.gemini/GEMINI.md` with new sections
3. Create `scripts/mcp/ontology_server.py` for ODA MCP integration

---

## 🎯 ActionType Summary

### Task Actions

| API Name | Hazardous | Description |
|:---------|:---------:|:------------|
| `create_task` | ❌ | Create new task |
| `update_task` | ❌ | Modify existing task |
| `delete_task` | ✅ | Soft-delete task |
| `assign_task` | ❌ | Assign to agent |
| `unassign_task` | ❌ | Remove assignment |
| `complete_task` | ❌ | Mark completed |
| `archive_task` | ❌ | Archive task |
| `bulk_create_tasks` | ✅ | Batch create (max 100) |

### Agent Actions

| API Name | Hazardous | Description |
|:---------|:---------:|:------------|
| `create_agent` | ❌ | Create new agent |
| `deactivate_agent` | ✅ | Deactivate agent |

### Infrastructure Actions

| API Name | Hazardous | Description |
|:---------|:---------:|:------------|
| `deploy_service` | ✅ | Deploy to staging/production |

---

## 🧪 Test Coverage

### Scenario Categories

| Category | Tests | Coverage |
|:---------|------:|:---------|
| OntologyObject Lifecycle | 5 | UUID, audit, touch, delete, archive |
| LinkType Definition | 3 | Cardinality, validation, types |
| Proposal State Machine | 12 | All transitions, guards, audit |
| SubmissionCriteria | 8 | Required, allowed, length, custom |
| Action Execution | 4 | Success, failure, side effects |
| ActionRegistry | 3 | Register, list, hazardous filter |
| HybridRouter | 7 | Local, relay, keywords, markers |
| RouterConfig | 4 | Defaults, file load, validation |
| OllamaClient | 2 | Health, generate (mocked) |
| Concurrent Operations | 2 | Parallel proposals, objects |
| Full Integration | 1 | Complete governance workflow |

**Total: 35+ test cases**

---

## 🔧 Gemini 3.0 Pro Features Used

| Feature | Application |
|:--------|:------------|
| **Structured Output** | Pydantic models for ActionResult, RoutingDecision |
| **Long Context** | Full codebase awareness for refactoring |
| **Async Execution** | Concurrent test execution, Ollama client |
| **MCP Integration** | Custom ODA ontology server |
| **Grounded Generation** | Context7 for library APIs |
| **Sequential Thinking** | Multi-step proposal workflows |

---

## 📋 Verification Checklist

After applying all snippets:

- [ ] 11 ActionTypes registered in `action_registry`
- [ ] 4 hazardous actions identified
- [ ] 35+ tests passing
- [ ] MCP config updated with `oda-ontology` server
- [ ] GEMINI.md contains `<registry_lock>` section
- [ ] Proposal state machine enforces valid transitions
- [ ] HybridRouter correctly classifies critical keywords

---

## 🚨 Troubleshooting

### Import Errors

```bash
# If module not found
export PYTHONPATH=/home/palantir/orion-orchestrator-v2:$PYTHONPATH
```

### Test Failures

```bash
# Run with verbose output
pytest tests/e2e/test_oda_v3_scenarios.py -v -s --tb=long

# Run single test
pytest tests/e2e/test_oda_v3_scenarios.py::TestProposalStateMachine::test_valid_transition_draft_to_pending -v
```

### MCP Server Issues

```bash
# Test MCP server standalone
python -m scripts.mcp.ontology_server

# Check MCP config syntax
python -c "import json; json.load(open('~/.gemini/antigravity/mcp_config.json'))"
```

---

## 🎓 Next Steps

After successful application:

1. **Extend ActionTypes** - Add domain-specific actions for your use case
2. **Integrate Storage** - Connect EditOperations to persistent database
3. **Add Webhooks** - Configure real Slack/webhook URLs in side effects
4. **CI/CD Pipeline** - Add test execution to GitHub Actions

---

**End of Master Guide**
