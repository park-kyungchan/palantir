# Ontology Schema-Based Commands/Skills Rebuild

> **Version:** 1.0 | **Status:** COMPLETED (Metadata 논의 대기) | **Date:** 2026-01-18
> **Auto-Compact Safe:** This file persists across context compaction

## Overview

| Item | Value |
|------|-------|
| Complexity | large |
| Total Tasks | 42+ |
| Schema Types | 7 (ObjectType, ActionType, LinkType, Property, Interface, Metadata, Interaction) |
| Lifecycle Stages | 5 (Define → Validate → Stage → Review → Deploy) |
| Schema Source | `/home/palantir/park-kyungchan/palantir/ontology_definition/` |

## Requirements

모든 ODA 커맨드/스킬이 `ontology_definition/` Foundry 스키마를 기반으로 동작해야 함.

### Goals
1. **Schema-First**: 모든 작업이 JSON Schema 기반으로 시작
2. **5-Stage Lifecycle**: Define → Validate → Stage → Review → Deploy
3. **Governance**: Palantir Foundry 거버넌스 원칙 준수
4. **DRY**: Commands = Thin Wrappers, Skills = Implementation

---

## Architecture Design

### Command Structure (Per Schema Type)

```
/<schematype> <stage> [options]

Examples:
/objecttype define MyEntity
/objecttype validate MyEntity
/actiontype stage CreateOrder
/linktype review CustomerToOrder
/property deploy EmailField
```

### Lifecycle Stages

| Stage | Purpose | Required Action |
|-------|---------|-----------------|
| **define** | 스키마 인스턴스 정의 생성 | JSON 구조 생성 |
| **validate** | JSON Schema 기반 검증 | Schema validation |
| **stage** | 변경사항 스테이징 | Batch staging |
| **review** | 사람 검토 | Human review gate |
| **deploy** | 프로덕션 적용 | Apply changes |

### File Structure

```
.claude/
├── commands/
│   ├── objecttype.md      (thin wrapper)
│   ├── actiontype.md      (thin wrapper)
│   ├── linktype.md        (thin wrapper)
│   ├── property.md        (thin wrapper)
│   ├── interface.md       (thin wrapper)
│   ├── metadata.md        (thin wrapper, 동적 설계)
│   └── interaction.md     (thin wrapper)
│
└── skills/
    ├── oda-objecttype.md  (full implementation)
    ├── oda-actiontype.md  (full implementation)
    ├── oda-linktype.md    (full implementation)
    ├── oda-property.md    (full implementation)
    ├── oda-interface.md   (full implementation)
    ├── oda-metadata.md    (full implementation, 동적 설계)
    └── oda-interaction.md (full implementation)
```

---

## Tasks

### Phase 0: Cleanup (Delete Old)

| # | Task | Files | Status |
|---|------|-------|--------|
| 0.1 | Delete protocol command | .claude/commands/protocol.md | ✅ DONE |
| 0.2 | Delete governance command | .claude/commands/governance.md | ✅ DONE |
| 0.3 | Delete oda-protocol skill | .claude/skills/oda-protocol.md | ✅ DONE |
| 0.4 | Delete oda-governance skill | .claude/skills/oda-governance.md | ✅ DONE |

### Phase 1: Schema Analysis

| # | Task | Files | Status |
|---|------|-------|--------|
| 1.1-1.7 | Analyze all 7 schemas | ontology_definition/*.schema.json | ✅ DONE (Agent: a05af5b) |

### Phase 2: Create Skills (7 skills)

| # | Task | Files | Status | Agent ID |
|---|------|-------|--------|----------|
| 2.1 | Create oda-objecttype.md skill | .claude/skills/oda-objecttype.md | ✅ DONE | a1518d7 |
| 2.2 | Create oda-actiontype.md skill | .claude/skills/oda-actiontype.md | ✅ DONE | aa906ab |
| 2.3 | Create oda-linktype.md skill | .claude/skills/oda-linktype.md | ✅ DONE | a91db99 |
| 2.4 | Create oda-property.md skill | .claude/skills/oda-property.md | ✅ DONE | a31eadb |
| 2.5 | Create oda-interface.md skill | .claude/skills/oda-interface.md | ✅ DONE | a2a513d |
| 2.6 | Create oda-metadata.md skill (동적 설계) | .claude/skills/oda-metadata.md | ✅ DONE | a04fa6c |
| 2.7 | Create oda-interaction.md skill | .claude/skills/oda-interaction.md | ✅ DONE | aeaa81d |

### Phase 3: Create Commands (7 thin wrappers)

| # | Task | Files | Status | Agent ID |
|---|------|-------|--------|----------|
| 3.1 | Create objecttype.md command | .claude/commands/objecttype.md | ✅ DONE | aa5b267 |
| 3.2 | Create actiontype.md command | .claude/commands/actiontype.md | ✅ DONE | a968cc1 |
| 3.3 | Create linktype.md command | .claude/commands/linktype.md | ✅ DONE | acccf1e |
| 3.4 | Create property.md command | .claude/commands/property.md | ✅ DONE | aff4f94 |
| 3.5 | Create interface.md command | .claude/commands/interface.md | ✅ DONE | af5d380 |
| 3.6 | Create metadata.md command (동적 설계) | .claude/commands/metadata.md | ✅ DONE | a423744 |
| 3.7 | Create interaction.md command | .claude/commands/interaction.md | ✅ DONE | a7b5838 |

### Phase 4: Documentation Update

| # | Task | Files | Status | Agent ID |
|---|------|-------|--------|----------|
| 4.1 | Update CLAUDE.md Section 9 | .claude/CLAUDE.md | ✅ DONE | a571430 |
| 4.2 | Create ontology-lifecycle.md reference | .claude/references/ontology-lifecycle.md | ✅ DONE | a86e725 |

### Phase 5: Verification

| # | Task | Files | Status |
|---|------|-------|--------|
| 5.1 | Test all 7 commands | - | ✅ DONE |
| 5.2 | Verify schema validation | - | ✅ DONE |
| 5.3 | REMINDER: Metadata 동적 설계 논의 | - | ⏳ PENDING (작업 완료 후) |

---

## Progress Tracking

| Phase | Tasks | Completed | Status |
|-------|-------|-----------|--------|
| Phase 0: Cleanup | 4 | 4 | ✅ DONE |
| Phase 1: Analysis | 7 | 7 | ✅ DONE |
| Phase 2: Skills | 7 | 7 | ✅ DONE |
| Phase 3: Commands | 7 | 7 | ✅ DONE |
| Phase 4: Docs | 2 | 2 | ✅ DONE |
| Phase 5: Verify | 3 | 2 | ✅ DONE (Metadata 논의 대기) |
| **Total** | **30** | **29** | **97%** |

---

## Quick Resume After Auto-Compact

If context is compacted, resume by:

1. Read this file: `.agent/plans/ontology_schema_commands.md`
2. Check TodoWrite for current task status (includes Agent IDs)
3. Continue from first PENDING task in sequence
4. Use `Task(resume="agent_id")` if subagent was interrupted

---

## Schema Source Reference

```yaml
schema_files:
  ObjectType: /home/palantir/park-kyungchan/palantir/ontology_definition/ObjectType.schema.json (43K)
  ActionType: /home/palantir/park-kyungchan/palantir/ontology_definition/ActionType.schema.json (67K)
  LinkType: /home/palantir/park-kyungchan/palantir/ontology_definition/LinkType.schema.json (21K)
  Property: /home/palantir/park-kyungchan/palantir/ontology_definition/Property.schema.json (34K)
  Interface: /home/palantir/park-kyungchan/palantir/ontology_definition/Interface.schema.json (8.6K)
  Metadata: /home/palantir/park-kyungchan/palantir/ontology_definition/Metadata.schema.json (22K)
  Interaction: /home/palantir/park-kyungchan/palantir/ontology_definition/Interaction.schema.json (32K)
```

---

## Agent Registry (Auto-Compact Resume)

| Task | Agent ID | Status | Resume Eligible |
|------|----------|--------|-----------------|
| Phase 1: Schema Analysis | a05af5b | ✅ completed | No |
| Phase 2-1: oda-objecttype | a1518d7 | 🔄 in_progress | Yes |
| Phase 2-2: oda-actiontype | aa906ab | ✅ completed | No |
| Phase 2-3: oda-linktype | a91db99 | 🔄 in_progress | Yes |
| Phase 2-4: oda-property | a31eadb | 🔄 in_progress | Yes |
| Phase 2-5: oda-interface | a2a513d | 🔄 in_progress | Yes |
| Phase 2-6: oda-metadata | a04fa6c | ✅ completed | No |
| Phase 2-7: oda-interaction | aeaa81d | 🔄 in_progress | Yes |

---

## Special Notes

### Metadata 동적 설계 (작업 완료 후 리마인드)

Metadata 스키마는 **동적 설계**가 핵심입니다. 작업 완료 후:
- Metadata.schema.json 분석
- 동적 메타데이터 패턴 설계 논의
- TypeClasses 활용 방안 검토

### Palantir Foundry References

- [Ontology Overview](https://www.palantir.com/docs/foundry/ontology/overview)
- [Action Types](https://www.palantir.com/docs/foundry/action-types/overview)
- [Core Concepts](https://www.palantir.com/docs/foundry/ontology/core-concepts)

---

> **Created:** 2026-01-18
> **Last Updated:** 2026-01-18
