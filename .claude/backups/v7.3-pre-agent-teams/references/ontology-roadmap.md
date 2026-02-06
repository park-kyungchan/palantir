# ODA (Ontology-Driven-Architecture) Skill Roadmap

> **Version:** 1.0.0
> **Created:** 2026-01-25
> **Status:** Planning

---

## Skill Roadmap

```
┌─────────────────────────────────────────────────────────────────┐
│                    ODA SKILL SUITE                              │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Phase 1: /ontology-core           [COMPLETED] ✅               │
│  ──────────────────────────────────────────────                 │
│  • ObjectType validation                                        │
│  • LinkType validation                                          │
│  • ActionType validation                                        │
│  • PropertyDefinition validation                                │
│  • Scaffold generation                                          │
│  • Cross-link consistency check                                 │
│                                                                 │
│  Phase 2: /ontology-extended       [PLANNED]                    │
│  ──────────────────────────────────────────────                 │
│  • Interface validation                                         │
│  • ValueType validation                                         │
│  • StructType validation                                        │
│  • SharedProperty validation                                    │
│  • FunctionType validation                                      │
│  • Automation validation                                        │
│  • Rules Engine validation                                      │
│  • Writeback validation                                         │
│                                                                 │
│  Phase 3: /ontology-migration      [PLANNED]                    │
│  ──────────────────────────────────────────────                 │
│  • Existing code analysis                                       │
│  • Domain model extraction                                      │
│  • ODA migration plan generation                                │
│  • Step-by-step migration guide                                 │
│  • Validation after migration                                   │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## Phase 2: /ontology-extended Details

### Scope

| Type | Key Validations |
|------|-----------------|
| Interface | Property requirements, action definitions |
| ValueType | Base type, constraints, display formatting |
| StructType | Field definitions, nested validation |
| SharedProperty | Semantic type, cross-ObjectType consistency |
| FunctionType | Decorator type (@Function/@Query/@OntologyEditFunction), @Edits |
| Automation | Condition types (TIME/OBJECT_SET), effects |
| Rules Engine | Logic boards, input sources, outputs |
| Writeback | Webhooks, exports, dataset config |

### Trigger

User request: "Create /ontology-extended skill"

---

## Phase 3: /ontology-migration Details

### Capabilities

1. **Analysis Mode**
   - Scan existing codebase
   - Identify domain entities (classes, data models)
   - Map relationships between entities
   - Detect existing patterns (SQLAlchemy, Django ORM, etc.)

2. **Planning Mode**
   - Generate ODA migration roadmap
   - Prioritize by dependency order
   - Estimate complexity per entity
   - Identify breaking changes

3. **Guided Migration Mode**
   - Step-by-step conversion guide
   - Before/after code examples
   - Validation checkpoints
   - Rollback instructions

### Trigger

User request: "Create /ontology-migration skill"

---

## Integration with ontology-definition Package

All ODA skills use the `ontology-definition` package:

```
/home/palantir/park-kyungchan/palantir/Ontology-Definition/
├── ontology_definition/
│   ├── types/           # Type definitions
│   ├── core/            # Enums, base classes
│   ├── versioning/      # Schema change tracking
│   └── export/          # Foundry JSON export
```

---

## Notes

- Phase 2 and Phase 3 are placeholders for future implementation
- User explicitly requested to be reminded when ready
- Each phase builds on the previous

---

**Last Updated:** 2026-01-25
