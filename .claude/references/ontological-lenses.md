# Ontological Lenses Reference v1.0

> Referenced by: agent-catalog.md (INFRA Quality category), INFRA analyst .md files
> Source Decisions: D-010 (Ontological Lenses Design), D-005 (Agent Decomposition)

## 1. The Four Lenses

The ontological lens framework provides four complementary perspectives for analyzing
any system component. Each lens reveals different aspects of the same subject.

### ARE Lens (Static/Structural)
**Question:** "What IS this thing? What are its properties?"
**Focus:** Identity, configuration, schema, naming, type definitions, constraints
**Palantir Alignment:** Object Types, Property Types, shared property types
**INFRA Analyst:** `infra-static-analyst`

### RELATE Lens (Relational/Dependency)
**Question:** "How does this connect to other things?"
**Focus:** Dependencies, coupling, references, import/export, cardinality
**Palantir Alignment:** Link Types, interface objects, relation cardinality
**INFRA Analyst:** `infra-relational-analyst`

### DO Lens (Behavioral/Lifecycle)
**Question:** "What does this thing DO? When and how?"
**Focus:** Actions, lifecycles, state transitions, protocol compliance, tool usage
**Palantir Alignment:** Action Types, webhooks, Functions, rules/logic
**INFRA Analyst:** `infra-behavioral-analyst`

### IMPACT Lens (Change/Ripple)
**Question:** "What happens when this changes?"
**Focus:** Change propagation, cascade effects, blast radius, regression risk
**Palantir Alignment:** Cross-cutting concerns, derived properties, computed values
**INFRA Analyst:** `infra-impact-analyst`

## 2. Application Matrix

Which lenses apply to which agent categories:

| Category | Primary Lens | Secondary Lens | Why |
|----------|:---:|:---:|-----|
| Research | ARE | RELATE | Discover what exists and how it connects |
| Verification | ARE + DO | RELATE | Verify claims match reality |
| Architecture | RELATE | IMPACT | Design connections, assess change risk |
| Planning | DO | ARE | Plan actions on known structures |
| Review | DO | IMPACT | Evaluate behavior and change safety |
| Implementation | DO | ARE | Execute changes on structures |
| Testing | DO | RELATE | Test behaviors across connections |
| INFRA Quality | ALL | ALL | Each analyst owns one lens |
| Monitoring | DO | IMPACT | Observe behavior, detect drift |

## 3. Lens-Specific Analysis Patterns

### ARE Analysis Checklist
- [ ] Name follows conventions?
- [ ] Schema/type definition correct?
- [ ] Required properties present?
- [ ] Constraints satisfied?
- [ ] Configuration valid?

### RELATE Analysis Checklist
- [ ] All dependencies declared?
- [ ] No circular dependencies?
- [ ] Cardinality correct (1:1, 1:N, N:M)?
- [ ] Interface contracts honored?
- [ ] Coupling appropriate (not too tight/loose)?

### DO Analysis Checklist
- [ ] Lifecycle states well-defined?
- [ ] State transitions valid?
- [ ] Actions have preconditions/postconditions?
- [ ] Protocol compliance verified?
- [ ] Tool permissions correct?

### IMPACT Analysis Checklist
- [ ] Change blast radius mapped?
- [ ] Cascade effects identified?
- [ ] Backward compatibility assessed?
- [ ] Rollback strategy exists?
- [ ] Dependent components notified?

## 4. Coordinator Synthesis Protocol

When a coordinator consolidates multi-lens results (especially INFRA Quality):

1. **Collect** per-lens findings from each analyst
2. **Cross-reference** findings across lenses:
   - ARE finding + RELATE finding → structural coupling issue
   - DO finding + IMPACT finding → behavioral risk
   - ARE finding + DO finding → configuration-behavior mismatch
3. **Prioritize** by cross-lens severity:
   - Finding appears in 3+ lenses → CRITICAL
   - Finding appears in 2 lenses → HIGH
   - Single-lens finding → severity from that lens
4. **Synthesize** into unified recommendation with cross-lens evidence

## 5. Honest Mapping Assessment

The four-lens model achieves approximately **80% clean fit** with real-world analysis.
The remaining 20% involves:

- **Cross-cutting concerns** that span multiple lenses (e.g., security touches ARE+DO+IMPACT)
- **Emergent properties** that arise from lens interactions
- **Gray zones** where primary/secondary lens assignment is debatable

**Resolution:** When in doubt, assign a primary lens (strongest fit) and note the secondary
lens involvement. The coordinator synthesis step resolves cross-lens interactions.
