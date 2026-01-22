# Phase 1: ODA 고도화 - Palantir Foundry Alignment

> **Version:** 1.0 | **Status:** IN_PROGRESS | **Date:** 2026-01-17
> **Auto-Compact Safe:** This file persists across context compaction
> **Target:** 78% → 95%+ Palantir Foundry Alignment

---

## Overview

| Item | Value |
|------|-------|
| Complexity | large |
| Total Tasks | 5 phases, 15+ subtasks |
| Files Affected | 8 (3 new, 5 modified) |
| Estimated Effort | 5-7 days |

## Requirements (from Reference Documents)

Based on two Palantir Foundry architecture documents:

1. **Restricted Views (RV)** - Row-level security pattern
   - Dynamic row filtering based on user/agent markings
   - RV-backed object types for security-critical data
   - Integration with existing 4-layer RBAC

2. **Mandatory Control Property** - Security marking enforcement
   - Properties that MUST be explicitly assigned (no defaults)
   - System prevents saving without explicit assignment
   - Audit trail for all marking assignments

3. **Ontology Schema JSON Export** - Foundry interoperability
   - Top-level `"ontology"` key wrapper
   - RID format for resource identifiers
   - Import/export capability

---

## Tasks

| # | Phase | Task | Status | File |
|---|-------|------|--------|------|
| 1.1 | Mandatory Control | Add `is_mandatory_control` to PropertyConstraint | pending | `property_types.py:174` |
| 1.2 | Mandatory Control | Create SecurityMarkingValidator | pending | `security_marking.py` (new) |
| 1.3 | Mandatory Control | Integrate with schema_validator | pending | `schema_validator.py` |
| 2.1 | Schema Export | Create FoundrySchemaExporter class | pending | `schema_export.py` (new) |
| 2.2 | Schema Export | Create FoundrySchemaImporter class | pending | `schema_export.py` |
| 2.3 | Schema Export | Add registry integration | pending | `registry.py:994` |
| 3.1 | Restricted Views | Create RestrictedViewPolicy model | pending | `restricted_views.py` (new) |
| 3.2 | Restricted Views | Create RestrictedViewEngine | pending | `restricted_views.py` |
| 3.3 | Restricted Views | Hook into repository layer | pending | `repositories.py` |
| 3.4 | Restricted Views | Integrate with permission_resolver | pending | `permission_resolver.py:358` |
| 4.1 | MCP Tools | Add RV tools to ontology_server | pending | `ontology_server.py` |
| 4.2 | MCP Tools | Add export/import tools | pending | `ontology_server.py` |
| 5.1 | Testing | Unit tests for control property | pending | `test_control_property.py` |
| 5.2 | Testing | Unit tests for schema export | pending | `test_schema_export.py` |
| 5.3 | Testing | Integration tests for RV+RBAC | pending | `test_rv_with_rbac.py` |

---

## Progress Tracking

| Phase | Tasks | Completed | Status |
|-------|-------|-----------|--------|
| 1. Mandatory Control Property | 3 | 0 | pending |
| 2. Schema JSON Export | 3 | 0 | pending |
| 3. Restricted Views | 4 | 0 | pending |
| 4. MCP Tools Enhancement | 2 | 0 | pending |
| 5. Testing & Validation | 3 | 0 | pending |

---

## Quick Resume After Auto-Compact

If context is compacted, resume by:

1. Read this file: `.agent/plans/phase1_oda_enhancement.md`
2. Check TodoWrite for current task status
3. Continue from first PENDING task in sequence
4. Use subagent delegation pattern from "Execution Strategy" section

---

## Execution Strategy

### Phase Order (Dependencies)

```
Phase 1: Mandatory Control Property
    │
    ├── No dependencies, foundational
    │
    ▼
Phase 2: Schema JSON Export ──────────────┐
    │                                      │
    ├── Parallel with Phase 3              │
    │                                      │
    ▼                                      ▼
Phase 3: Restricted Views ◄──── Depends on Phase 1 (control properties)
    │
    ▼
Phase 4: MCP Tools Enhancement
    │
    ▼
Phase 5: Testing & Validation
```

### Parallel Execution Groups

| Group | Tasks | Can Parallelize |
|-------|-------|-----------------|
| A | Phase 1 (all) | Sequential (dependencies) |
| B | Phase 2 + Phase 3.1-3.2 | Yes (after Phase 1) |
| C | Phase 3.3-3.4 + Phase 4 | Sequential |
| D | Phase 5 (all) | Yes (after all implementation) |

### Subagent Delegation

| Task Group | Subagent Type | Context | Budget |
|------------|---------------|---------|--------|
| Phase 1 Implementation | general-purpose | fork | 15K |
| Phase 2 Implementation | general-purpose | fork | 15K |
| Phase 3 Implementation | general-purpose | fork | 15K |
| Phase 4 Implementation | general-purpose | fork | 10K |
| Phase 5 Testing | general-purpose | fork | 10K |

---

## Critical File Paths

```yaml
# Files to MODIFY
property_types: lib/oda/ontology/types/property_types.py
permission_resolver: lib/oda/agent/permission_resolver.py
registry: lib/oda/ontology/registry.py
repositories: lib/oda/ontology/storage/repositories.py
ontology_server: lib/oda/mcp/ontology_server.py

# Files to CREATE
security_marking: lib/oda/agent/security_marking.py
schema_export: lib/oda/foundry_mimic/schema_export.py
restricted_views: lib/oda/agent/restricted_views.py

# Test files to CREATE
test_control_property: tests/oda/ontology/types/test_control_property.py
test_schema_export: tests/oda/foundry_mimic/test_schema_export.py
test_rv_with_rbac: tests/integration/test_rv_with_rbac.py
```

---

## Implementation Details

### Phase 1: Mandatory Control Property

**Key Integration Points:**

```python
# property_types.py:174 - Add after 'unique' field
class PropertyConstraint(BaseModel):
    required: bool = False
    unique: bool = False
    is_mandatory_control: bool = False  # NEW

    @model_validator(mode="after")
    def validate_control_property(self) -> "PropertyConstraint":
        if self.is_mandatory_control:
            if self.default_value is not None:
                raise ValueError("Control properties cannot have defaults")
            object.__setattr__(self, 'required', True)
        return self
```

### Phase 2: Schema JSON Export

**Foundry Format Target:**

```json
{
    "ontology": {
        "rid": "ri.ontology.main.ontology.xxx",
        "displayName": "...",
        "objectTypes": [...],
        "linkTypes": [...],
        "actionTypes": [...]
    },
    "metadata": {
        "exportedAt": "...",
        "version": "..."
    }
}
```

### Phase 3: Restricted Views

**Integration with Permission Resolver:**

```python
# permission_resolver.py:358 - After instance permission grant
def _check_instance_permission(self, ...) -> Optional[ResolvedPermission]:
    # ... existing logic ...
    if granted:
        # NEW: Apply RV filtering
        filtered = self._apply_rv_filters(agent_id, object_type, instance_id)
        return ResolvedPermission(..., rv_filtered=filtered)
```

---

## Agent Registry (Auto-Compact Resume)

| Task | Agent ID | Status | Resume Eligible |
|------|----------|--------|-----------------|
| Plan Analysis | ae1a1c4 | completed | No |
| Explore Analysis | ab304a9 | completed | No |

---

## Risk Assessment

| Risk | Impact | Mitigation |
|------|--------|------------|
| Breaking existing RBAC | HIGH | Additive changes only, no modification to resolution chain |
| Performance impact from RV filtering | MEDIUM | Lazy evaluation, caching policy results |
| Schema migration needed | LOW | New fields have defaults, backward compatible |

---

## Success Criteria

- [ ] All 3 Critical Gaps implemented
- [ ] Unit test coverage > 80%
- [ ] Integration tests pass
- [ ] No regression in existing RBAC functionality
- [ ] Palantir Foundry alignment score: 95%+

---

*Generated by ODA /plan command v2.1.7*
