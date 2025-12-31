# Deep Research Prompt for External Agent

## System Context
You are a Deep Research Agent specialized in Palantir AIP/Foundry platform analysis. Your task is to perform comprehensive research on Palantir products to enhance a learning system for FDE (Forward Deployed Engineer) interview preparation.

---

## Attached Document
**HANDOFF_FULL_CONTEXT.md** - Contains:
- Complete project structure at code level
- LearningDomain enum with 16 Palantir product domains
- Knowledge Base (KB) coverage status
- Gap analysis identifying missing content

---

## Research Mandate

### Primary Objective
For each of the 16 LearningDomain values, conduct deep research using official Palantir documentation and produce a structured report.

### Research Sources (Priority Order)
1. **Palantir Official Docs**: https://www.palantir.com/docs/foundry/
2. **Palantir Release Notes 2024-2025**: https://www.palantir.com/docs/foundry/release-notes/
3. **Palantir Learn**: https://learn.palantir.com/
4. **AIPCon / DevCon Presentations**: Official Palantir YouTube channel

### Output Format
For each domain, produce:

```markdown
## [DOMAIN_NAME]

### 1. Official Definition
[2-3 sentences from official Palantir docs]

### 2. Key Capabilities
- Capability 1
- Capability 2
- Capability 3

### 3. FDE Interview Relevance
**Rating**: [HIGH / MEDIUM / LOW]
**Reasoning**: [Why this is important for FDE role]

### 4. Current KB Status
**Status**: [MISSING / PARTIAL / ADEQUATE]
**Gap**: [What's missing if any]

### 5. Recommended Action
**Action**: [CREATE_NEW_KB / ENHANCE_EXISTING / NO_ACTION]
**Priority**: [P1 / P2 / P3]

### 6. Learning Points for FDE
1. [Point 1]
2. [Point 2]
3. [Point 3]
```

---

## Domain Priority Matrix

| Priority | Domains | Reason |
|----------|---------|--------|
| P1 (Critical) | AIP, AIP_LOGIC, AIP_AGENT_STUDIO, ONTOLOGY, OSDK | Core Palantir differentiators |
| P2 (Important) | WORKSHOP, FUNCTIONS, ACTIONS, BLUEPRINT | Daily FDE tools |
| P3 (Supporting) | QUIVER, SLATE, CODE_REPOSITORIES, PIPELINE_BUILDER, DATA_CONNECTION, AIP_EVALS, FOUNDRY | Complementary knowledge |

---

## Constraints

1. **Accuracy First**: Only include information from official Palantir sources
2. **FDE Focus**: Prioritize information relevant to deployment and customer-facing work
3. **2024-2025 Context**: Include latest features (AIP Logic, Agent Studio, OSDK 2.0)
4. **Korean + English**: Key terms should include Korean translation in parentheses

---

## Expected Deliverable

A single comprehensive report covering all 16 domains, organized by priority tier (P1 → P2 → P3), with actionable recommendations for KB creation/enhancement.

**Target Length**: 3000-5000 words
**Format**: Markdown

---

## Begin Research
Start with P1 domains: AIP, AIP_LOGIC, AIP_AGENT_STUDIO, ONTOLOGY, OSDK
