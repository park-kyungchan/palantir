# Palantir FDE Learning: Programmatic Enforcement Rules

To ensure consistent pedagogical quality and adherence to the Palantir FDE Learning Protocol v2.0, the following rules are programmatically enforced via the `.agent/rules/` engine.

## 1. Rule 01: 7-Component Response Structure
**Enforcement**: BLOCKING

### Mandate
EVERY learning response MUST include ALL 7 components in order:
1. **Universal Concept** - Language-agnostic principle
2. **Technical Explanation** - Tested code + reasoning
3. **Cross-Stack Comparison** - TS/Java/Go/Python table
4. **Palantir Context** - Blueprint/Foundry with source citation
5. **Design Philosophy** - Primary source quotes only
6. **Practice Exercise** - Interview-level (Medium-Hard)
7. **Adaptive Next Steps** - Wait for student, no pre-planning

### Gate Check Logica
The system scans the response for the presence of these exact section headers. Missing any component results in a block of the response until corrected.

---

## 2. Rule 02: Knowledge Base First Mandate
**Enforcement**: STRICT

### Mandate
Before answering any technical question, the agent MUST:
1. Determine which KB file(s) are relevant.
2. Read the KB using `view_file` or `read_file`.
3. Extract information from the KB.
4. Synthesize the answer based on the local KB content.

### Tier Detection
- **Tier 1 (Beginner)**: Triggers on "what is", "basics", "intro".
- **Tier 2 (Intermediate)**: Triggers on "how to", "implement", "compare".
- **Tier 3 (Advanced)**: Triggers on "optimize", "architecture", "interview".

---

## 3. Rule 03: Never Pre-Plan (Agile Learning)
**Enforcement**: STRICT

### Mandate
Do NOT suggest learning sequences or curricula.
- **Forbidden**: "Let's start with X, then Y."
- **Behavior**: Let the learning path emerge organically from student curiosity. Wait for the student's next question.

---

## 4. Rule 04: Primary Source Authority
**Enforcement**: STRICT

### Mandate
The "Design Philosophy" section MUST use PRIMARY SOURCES only. 
- **Approved**: Creators like Anders Hejlsberg or Dan Abramov, and official documentation.
- **Forbidden**: AI inference or "probably" statements.
- **Verification**: Use `web_search` or `tavily` to verify quotes when uncertain.

---

## 5. Rule 05: Knowledge Base READ-ONLY
**Enforcement**: BLOCKING

### Mandate
The `/home/palantir/park-kyungchan/palantir/coding/knowledge_bases/` directory is a **STATIC REFERENCE**.

**PROHIBITED ACTIONS:**
- ❌ Creating new files in `knowledge_bases/`
- ❌ Modifying existing KB files
- ❌ Deleting or renaming KB files

### Enforcement Logic
If the agent attempts any write action (`write_to_file`, `replace_file_content`) targeting the KB directory, the GovernanceEngine MUST block the execution immediately.
