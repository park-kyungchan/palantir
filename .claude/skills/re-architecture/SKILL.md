---
name: re-architecture
description: |
  **파이프라인 컴포넌트 분해 및 피드백 도구** - 전체 파이프라인을 컴포넌트별로 분해하여
  각각의 세부사항에 대한 피드백을 제공합니다.

  **V2.0.0 Changes (EFL Integration):**
  - P1: Skill as Sub-Orchestrator (agent delegation for component analysis)
  - P3: General-Purpose Synthesis (L2 horizontal + L3 vertical)
  - P5: Phase 3.5 Review Gate (holistic verification before handoff)
  - P6: Agent Internal Feedback Loop (max 3 iterations)

  핵심 기능:
  - 모든 상호작용 과정을 Machine-Readable YAML 형식으로 기록
  - 설계 의도와 이슈 추적을 위한 traceability 스키마
  - 매 프롬프트마다 문서 업데이트 (incremental logging)
  - /research 스킬과 연계하여 skill-driven pipeline 지원

user-invocable: true
disable-model-invocation: false
context: inline
model: opus
version: "3.0.0"
argument-hint: "<target-path> | --resume <slug>"
allowed-tools:
  - Read
  - Grep
  - Glob
  - Task
  - Write
  - mcp__sequential-thinking__sequentialthinking
  - Edit
  - AskUserQuestion
  - mcp__sequential-thinking__sequentialthinking

# P1: Agent Delegation (Sub-Orchestrator Mode)
agent_delegation:
  enabled: true
  default_mode: true  # V1.1.0: Auto-delegation by default
  mode: "sub_orchestrator"
  description: |
    Re-architecture delegates to specialized agents for parallel component analysis.
    Main skill orchestrates the flow, agents execute analysis tasks.
  agents:
    - type: "explore"
      role: "Phase 3-A L2 Horizontal - Component structure and cross-dependency analysis"
      output_format: "L2 structured data (components, dependencies, patterns)"
    - type: "explore"
      role: "Phase 3-B L3 Vertical - Deep code analysis and risk assessment"
      output_format: "L3 verification results (code evidence, issues, recommendations)"
  max_sub_agents: 5
  delegation_strategy: "complexity-based"
  output_paths:
    l1: ".agent/prompts/{slug}/re-architecture/l1_summary.yaml"
    l2: ".agent/prompts/{slug}/re-architecture/l2_index.md"
    l3: ".agent/prompts/{slug}/re-architecture/l3_details/"
  return_format:
    l1: "Re-architecture summary with component count and risk level (≤500 tokens)"
    l2_path: ".agent/prompts/{slug}/re-architecture/l2_index.md"
    l3_path: ".agent/prompts/{slug}/re-architecture/l3_details/"
    requires_l2_read: false
    next_action_hint: "/research"

# =============================================================================
# P2: Parallel Agent Configuration
# =============================================================================
parallel_agent_config:
  enabled: true
  complexity_detection: "auto"
  agent_count_by_complexity:
    simple: 1      # Single component analysis
    moderate: 2    # 2-5 components
    complex: 3     # 6-10 components
    very_complex: 5  # 10+ components (max_sub_agents)
  synchronization_strategy: "barrier"
  aggregation_strategy: "merge"
  analysis_areas:
    - component_structure
    - dependency_mapping
    - risk_assessment
    - migration_planning

# =============================================================================
# P6: Agent Internal Feedback Loop
# =============================================================================
agent_internal_feedback_loop:
  enabled: true
  max_iterations: 3
  validation_criteria:
    completeness:
      - "All target components identified"
      - "Dependencies mapped for each component"
      - "Issues and recommendations documented"
    quality:
      - "Code evidence provided for findings"
      - "Risk severity assessed accurately"
      - "Design intent captured for each component"
    internal_consistency:
      - "L2/L3 hierarchy maintained"
      - "Traceability fields populated"
      - "Round logging incremental"

# P5: Review Gate (Phase 3.5)
review_gate:
  enabled: true
  phase: "3.5"
  criteria:
    - "requirement_alignment: Analysis covers user-specified target path"
    - "design_flow_consistency: L2/L3 structure properly separated"
    - "gap_detection: Missing components identified"
    - "conclusion_clarity: Handoff context complete for /research"
    - "traceability_complete: All rounds have design_intent"
  auto_approve: false

# P4: Selective Feedback
selective_feedback:
  enabled: true
  threshold: "MEDIUM"
  action_on_low: "log_only"
  action_on_medium_plus: "trigger_review_gate"

hooks:
  Setup:
    - type: command
      command: "/home/palantir/.claude/hooks/re-architecture-setup.sh"
      timeout: 10000
    - type: command
      command: "source /home/palantir/.claude/skills/shared/workload-files.sh"
      timeout: 5000
  Stop:
    - type: command
      command: "/home/palantir/.claude/hooks/re-architecture-finalize.sh"
      timeout: 180000
---

### Auto-Delegation Trigger (CRITICAL)

> **Reference:** `.claude/skills/shared/auto-delegation.md`
> **Behavior:** When `agent_delegation.enabled: true` AND `default_mode: true`, skill automatically operates as Sub-Orchestrator.

```javascript
// AUTO-DELEGATION CHECK - Execute at skill invocation
// If complex task detected, triggers: analyze → delegate → collect
const delegationDecision = checkAutoDelegation(SKILL_CONFIG, userRequest)
if (delegationDecision.shouldDelegate) {
  const complexity = analyzeTaskComplexity(taskDescription, SKILL_CONFIG)
  return executeDelegation(taskDescription, complexity, SKILL_CONFIG)
}
// Simple tasks execute directly without delegation overhead
```


# /re-architecture - Pipeline Component Analysis & Feedback (EFL V3.0.0)

> **Version:** 3.0.0 (EFL Pattern)
> **Role:** Sub-Orchestrator for pipeline component analysis + traceability-focused feedback
> **Core Principle:** Machine-Readable YAML 로그 → Traceability 유지
> **Access Pattern:** P1 (User-Only) - 사용자 명시적 호출만 허용
> **Downstream:** `/research` 스킬과 연계
> **EFL Features:** P1 Sub-Orchestrator, P3 General-Purpose Synthesis, P5 Review Gate, P6 Internal Loop

---

## CRITICAL REQUIREMENTS

### Language Requirement
**모든 출력은 한국어로 작성해야 합니다.**
- All prompts, explanations, and interactions MUST be in Korean
- User-facing text MUST be in Korean
- YAML field names can use English but descriptions should be in Korean

### Complete Traceability Logging
**모든 상호작용은 YAML 로그에 기록됩니다.**
- 설계 의도(design_intent) 필수 기록
- 이슈 추적을 위한 structured schema
- Incremental update: 매 라운드마다 문서 업데이트
- Workload-scoped output: `.agent/prompts/{slug}/re-architecture-log.yaml`

### Decision Support
**컴포넌트별 피드백을 통한 의사결정 지원**
- 각 컴포넌트에 대해 findings, recommendations, issues 제공
- 사용자의 명확한 의도와 요구사항 기록
- 판단근거(rationale) 명시

---

## 1. Purpose

**Re-Architecture Sub-Orchestrator** (P1) that:
1. **Orchestration**: Delegates component analysis to specialized agents (not direct execution)
2. **Phase 3-A (L2 Horizontal)**: Cross-component consistency and dependency mapping (P3)
3. **Phase 3-B (L3 Vertical)**: Deep code analysis and risk assessment (P3)
4. **Phase 3.5 Review Gate**: Holistic verification before /research handoff (P5)
5. **Internal Feedback Loop**: Agent self-validation with max 3 iterations (P6)
6. **Traceability**: Machine-readable YAML logging with design intent tracking

### Enhanced Feedback Loop (EFL) Integration

| Pattern | Implementation |
|---------|----------------|
| **P1: Sub-Orchestrator** | Skill conducts agents, doesn't execute directly |
| **P3: General-Purpose** | Phase 3-A/3-B structure (L2 horizontal + L3 vertical) |
| **P5: Review Gate** | Phase 3.5 holistic verification before handoff |
| **P6: Internal Loop** | Agent self-validation (max 3 iterations) |
| **P4: Selective Feedback** | Severity-based threshold (MEDIUM+) |

---

## 2. Execution Protocol (EFL Pattern)

### Overview: Sub-Orchestrator Flow

```
/re-architecture (Main Skill - Orchestrator)
    │
    ├─▶ Phase 0: Setup & Workload Detection (Hook-based)
    │
    ├─▶ Phase 1: Agent Delegation (P1)
    │   ├─▶ Agent 1 (Explore): Phase 3-A L2 Horizontal
    │   │   └─▶ Internal Loop (P6): Self-validate, max 3 iterations
    │   └─▶ Agent 2 (Explore): Phase 3-B L3 Vertical
    │       └─▶ Internal Loop (P6): Self-validate, max 3 iterations
    │
    ├─▶ Phase 2: Aggregate L2/L3 Results (P3)
    │   └─▶ Merge component findings, deduplicate
    │
    ├─▶ Phase 3: Interactive Component Review
    │   └─▶ AskUserQuestion for each component (existing behavior)
    │
    ├─▶ Phase 3.5: Review Gate (P5)
    │   └─▶ Holistic verification (requirement_alignment, etc.)
    │
    └─▶ Phase 4: Generate L1 Report & Handoff Context
        └─▶ Return to user with L1 summary + L2 path
```

### 2.1 Argument Parsing

```bash
# $ARGUMENTS 파싱
if [[ "$ARGUMENTS" == --resume* ]]; then
    RESUME_MODE=true
    SLUG="${ARGUMENTS#--resume }"
    LOG_PATH=".agent/prompts/${SLUG}/re-architecture-log.yaml"
else
    RESUME_MODE=false
    TARGET_PATH="$ARGUMENTS"
fi
```

### 2.2 Phase 0: Setup & Workload Detection (Hook-based)

```bash
# Hook-based initialization via re-architecture-setup.sh
# - detect_workload_staleness()
# - ensure_active_workload()
# - Source validation-feedback-loop.sh for P4/P5/P6

# Source helper functions
source /home/palantir/.claude/skills/shared/slug-generator.sh
source /home/palantir/.claude/skills/shared/workload-tracker.sh
source /home/palantir/.claude/skills/shared/validation-feedback-loop.sh

# Generate unique session
SLUG=$(generate_slug "re-arch" "$TARGET_PATH")
WORKLOAD_DIR=".agent/prompts/${SLUG}"
LOG_PATH="${WORKLOAD_DIR}/re-architecture-log.yaml"

# Create workload directory and YAML log
mkdir -p "${WORKLOAD_DIR}"
yaml_init_architecture_log "$LOG_PATH" "$TARGET_PATH"
```

### 2.3 Phase 1: Agent Delegation (P1 - Sub-Orchestrator Pattern)

```python
# P1: Skill as Sub-Orchestrator - Delegates to agents instead of direct execution
async def delegate_analysis(target_path, workload_slug):
    print("🎯 P1: Delegating analysis to specialized agents...")

    # Source validation-feedback-loop.sh
    await Bash({
        command: 'source /home/palantir/.claude/skills/shared/validation-feedback-loop.sh',
        description: 'Load P4/P5/P6 feedback loop functions'
    })

    # Detect complexity for agent count
    complexity = detect_analysis_complexity(target_path)
    agent_count = get_agent_count_by_complexity(complexity)

    print(f"\n📊 Complexity: {complexity}, Agents: {agent_count}")

    # Phase 3-A: L2 Horizontal Analysis (Cross-component consistency)
    print("\n📊 Phase 3-A: L2 Horizontal Analysis (컴포넌트 구조 분석)")
    l2_horizontal_result = await delegate_to_agent({
        agent_type: 'explore',
        task: 'phase3a_l2_horizontal',
        prompt: generate_phase3a_prompt(target_path, workload_slug),
        validation_criteria: {
            required_sections: ['components', 'dependencies', 'patterns'],
            completeness_checks: ['all_files_scanned', 'dependencies_mapped'],
            quality_thresholds: { 'component_count': 1 }
        }
    })

    # Phase 3-B: L3 Vertical Analysis (Deep code analysis)
    print("\n🔍 Phase 3-B: L3 Vertical Analysis (심층 코드 분석)")
    l3_vertical_result = await delegate_to_agent({
        agent_type: 'explore',
        task: 'phase3b_l3_vertical',
        prompt: generate_phase3b_prompt(target_path, l2_horizontal_result),
        validation_criteria: {
            required_sections: ['code_evidence', 'risks', 'recommendations'],
            completeness_checks: ['issues_identified', 'rationale_provided'],
            quality_thresholds: { 'evidence_count': 1 }
        }
    })

    return {
        l2_horizontal: l2_horizontal_result,
        l3_vertical: l3_vertical_result
    }
```

### 2.4 Agent Delegation Helper (P6 Internal Loop)

```python
# Delegate to agent with P6 internal feedback loop
async def delegate_to_agent(config):
    agent_type = config['agent_type']
    task = config['task']
    prompt = config['prompt']
    validation_criteria = config['validation_criteria']

    print(f"  🤖 Spawning {agent_type} agent for {task}...")

    # P6: Generate agent prompt with internal loop instructions
    agent_prompt_with_loop = await Bash({
        command: f'''source /home/palantir/.claude/skills/shared/validation-feedback-loop.sh && \\
                  generate_agent_prompt_with_internal_loop "{agent_type}" '{json.dumps(validation_criteria)}' ''',
        description: 'Generate agent prompt with P6 internal loop'
    })

    # Combine task prompt with internal loop instructions
    full_prompt = f"{agent_prompt_with_loop}\n\n---\n\n{prompt}"

    # Launch agent via Task tool
    agent_result = await Task({
        subagent_type: agent_type,
        description: f"{task} with internal loop",
        prompt: full_prompt,
        model: 'opus'  # Use opus for comprehensive analysis
    })

    # Extract internal loop metadata
    loop_metadata = extract_internal_loop_metadata(agent_result)

    print(f"  ✅ Agent completed: {loop_metadata['iterations_used']} iterations")

    return {
        task: task,
        result: agent_result,
        internal_loop: loop_metadata
    }
```

### 2.5 Phase 3-A Prompt Generator (L2 Horizontal)

```python
def generate_phase3a_prompt(target_path, workload_slug):
    return f'''# Phase 3-A: L2 Horizontal Analysis (컴포넌트 구조 분석)

**Objective:** Analyze component structure and cross-dependencies.

**Target Path:** {target_path}
**Workload:** {workload_slug}

**Tasks:**
1. Scan target directory for components:
   - Files: *.py, *.ts, *.js, *.sh, *.md
   - Directories: modules, packages, services

2. For each component, extract:
   - Component name and type (stage|module|service|utility)
   - File path
   - Dependencies (imports, references)
   - Upstream/downstream relationships

3. Cross-component analysis:
   - Identify shared patterns
   - Map dependency graph
   - Detect potential circular dependencies

**Output Format (L2 Structured Data):**
```yaml
l2_horizontal:
  pipeline_structure: |
    {{diagram}}

  components:
    - id: "comp-001"
      name: "{{component_name}}"
      path: "{{file_path}}"
      type: "{{stage|module|service|utility}}"
      dependencies:
        upstream: []
        downstream: []

  patterns:
    - name: "{{pattern_name}}"
      files: []
      description: "{{pattern_description}}"

  dependency_graph: |
    {{graph}}
```
'''
```

### 2.6 Phase 3-B Prompt Generator (L3 Vertical)

```python
def generate_phase3b_prompt(target_path, l2_result):
    components = extract_components_from_l2(l2_result)

    return f'''# Phase 3-B: L3 Vertical Analysis (심층 코드 분석)

**Objective:** Deep code analysis for risks, issues, and recommendations.

**Context from Phase 3-A (L2):**
- Components identified: {len(components)}

**Tasks:**
1. For each component, analyze:
   - Code structure and patterns
   - Error handling
   - Tech debt indicators
   - Security considerations

2. Risk assessment:
   - Severity: critical|high|medium|low
   - Evidence: file path, line number, code snippet

3. Recommendations:
   - Priority: high|medium|low
   - Rationale (판단근거)
   - Effort estimate: small|medium|large

**Components to Analyze:**
{chr(10).join([f"- {c['name']} ({c['path']})" for c in components])}

**Output Format (L3 Verification Data):**
```yaml
l3_vertical:
  findings:
    - id: "find-001"
      component_id: "comp-001"
      type: "pattern|issue|opportunity"
      severity: "info|warning|critical"
      description: "{{description_in_korean}}"
      evidence:
        file: "{{file_path}}"
        line: "{{line_number}}"
        snippet: "{{code_snippet}}"

  recommendations:
    - id: "rec-001"
      component_id: "comp-001"
      priority: "high|medium|low"
      description: "{{description_in_korean}}"
      rationale: "{{rationale}}"
      effort_estimate: "small|medium|large"

  issues:
    - id: "issue-001"
      component_id: "comp-001"
      type: "bug|debt|risk|improvement"
      severity: "critical|high|medium|low"
      description: "{{description_in_korean}}"
      suggested_action: "{{action}}"
      blocking: false

  risk_summary:
    total_findings: {{count}}
    critical: {{count}}
    high: {{count}}
    medium: {{count}}
    low: {{count}}
```
'''
```

### 2.7 Phase 2: Aggregate L2/L3 Results (P3)

```python
# P3: Aggregate Phase 3-A (L2 Horizontal) and Phase 3-B (L3 Vertical) results
async def aggregate_l2_l3_results(delegation_result):
    print("\n📦 P3: Aggregating L2/L3 results...")

    l2_horizontal = delegation_result['l2_horizontal']
    l3_vertical = delegation_result['l3_vertical']

    # Parse agent results
    l2_data = parse_agent_result(l2_horizontal['result'], 'l2_horizontal')
    l3_data = parse_agent_result(l3_vertical['result'], 'l3_vertical')

    # Merge into unified structure
    aggregated = {
        # From L2 Horizontal
        'pipeline_structure': l2_data.get('pipeline_structure', ''),
        'components': l2_data.get('components', []),
        'patterns': l2_data.get('patterns', []),
        'dependency_graph': l2_data.get('dependency_graph', ''),

        # From L3 Vertical
        'findings': l3_data.get('findings', []),
        'recommendations': l3_data.get('recommendations', []),
        'issues': l3_data.get('issues', []),
        'risk_summary': l3_data.get('risk_summary', {}),

        # Metadata
        'internal_loop_metadata': {
            'l2_iterations': l2_horizontal['internal_loop']['iterations_used'],
            'l3_iterations': l3_vertical['internal_loop']['iterations_used']
        }
    }

    # Validate aggregation
    if len(aggregated['components']) == 0:
        print("  ⚠️  Warning: No components found in L2 analysis")

    print(f"  ✅ Aggregated: {len(aggregated['components'])} components, {len(aggregated['findings'])} findings")

    return aggregated
```

### 2.8 Phase 3: Interactive Component Review

```python
# Preserve existing interactive review behavior
for component in aggregated['components']:
    # =========================================================================
    # Step 1: 컴포넌트 심층 분석 (from aggregated L3 data)
    # =========================================================================
    component_findings = [f for f in aggregated['findings'] if f.get('component_id') == component['id']]
    component_recommendations = [r for r in aggregated['recommendations'] if r.get('component_id') == component['id']]
    component_issues = [i for i in aggregated['issues'] if i.get('component_id') == component['id']]

    # =========================================================================
    # Step 2: YAML 로그 기록 (분석 전)
    # =========================================================================
    yaml_append_round(
        log_path=LOG_PATH,
        round_num=ROUND_NUM,
        phase="analysis",
        component_id=component['id'],
        input={"prompt": f"Analyzing {component['name']}", "context": component['path']},
        traceability={
            "design_intent": f"{component['name']} 컴포넌트의 구조와 역할 파악",
            "parent_round": ROUND_NUM - 1 if ROUND_NUM > 1 else None
        }
    )

    # =========================================================================
    # Step 3: 피드백 생성 (from aggregated data)
    # =========================================================================
    feedback = {
        'findings': component_findings,
        'recommendations': component_recommendations,
        'issues': component_issues
    }

    # =========================================================================
    # Step 4: 사용자에게 피드백 제시 + 의사결정 지원
    # =========================================================================
    options = [
        {
            "label": "피드백 승인",
            "description": "이 컴포넌트 분석을 승인하고 다음으로 진행",
            "rationale": f"{len(component_findings)}개 발견사항, {len(component_recommendations)}개 권장사항 확인됨"
        },
        {
            "label": "추가 분석 요청",
            "description": "특정 영역에 대해 더 깊은 분석 진행",
            "rationale": "현재 분석이 충분하지 않다고 판단될 경우"
        },
        {
            "label": "이슈 등록",
            "description": "발견된 문제를 이슈로 등록",
            "rationale": f"{len(component_issues)}개 잠재적 이슈가 감지됨"
        },
        {
            "label": "건너뛰기",
            "description": "이 컴포넌트를 건너뛰고 다음으로",
            "rationale": "우선순위가 낮거나 이미 충분히 파악됨"
        }
    ]

    response = AskUserQuestion(
        questions=[{
            "question": f"{component['name']} 컴포넌트 분석 결과입니다. 어떻게 진행하시겠습니까?",
            "header": f"컴포넌트 #{component_index}",
            "options": [{"label": o["label"], "description": f"{o['description']}\n📋 근거: {o['rationale']}"} for o in options],
            "multiSelect": False
        }]
    )

    # =========================================================================
    # Step 5: YAML 로그 업데이트 (응답 후)
    # =========================================================================
    yaml_update_round(LOG_PATH, ROUND_NUM, {
        "analysis": feedback,
        "output": {
            "options_presented": options,
            "user_selection": response
        },
        "traceability": {
            "decision_rationale": f"사용자가 '{response}'를 선택함"
        }
    })

    # =========================================================================
    # Step 6: 컴포넌트 피드백 저장
    # =========================================================================
    yaml_save_component_feedback(LOG_PATH, component['id'], feedback)

    ROUND_NUM += 1
```

### 2.9 Phase 3.5: Review Gate (P5)

```python
# P5: Execute Phase 3.5 Review Gate - Holistic verification before handoff
async def execute_review_gate(aggregated, log_path):
    print("\n🚪 P5: Executing Phase 3.5 Review Gate...")

    # Prepare review input
    review_input = {
        'components': aggregated['components'],
        'findings': aggregated['findings'],
        'recommendations': aggregated['recommendations'],
        'issues': aggregated['issues'],
        'metadata': {
            'complexity': len(aggregated['components']) > 5 and 'complex' or 'moderate',
            'risk_level': aggregated['risk_summary'].get('critical', 0) > 0 and 'HIGH' or 'MEDIUM'
        }
    }

    # Call review_gate from validation-feedback-loop.sh
    review_result = await Bash({
        command: f'''source /home/palantir/.claude/skills/shared/validation-feedback-loop.sh && \\
                  review_gate "re-architecture" '{json.dumps(review_input)}' "false" ''',
        description: 'P5: Execute review gate'
    })

    review = json.loads(review_result)

    print(f"  📋 Review result: {'✅ APPROVED' if review['approved'] else '❌ NEEDS REVIEW'}")

    # Check criteria
    criteria_checks = {
        'requirement_alignment': check_requirement_alignment(aggregated),
        'design_flow_consistency': check_l2_l3_separation(aggregated),
        'gap_detection': len(aggregated['issues']) > 0 and 'issues_identified' or 'no_issues',
        'conclusion_clarity': len(aggregated['recommendations']) > 0,
        'traceability_complete': check_traceability(log_path)
    }

    print(f"\n  📊 Review Criteria:")
    for criterion, status in criteria_checks.items():
        print(f"     - {criterion}: {status}")

    if review['warnings']:
        print(f"\n  ⚠️  Warnings:")
        for w in review['warnings']:
            print(f"     - {w}")

    return {
        'approved': review['approved'],
        'criteria_checks': criteria_checks,
        'review': review
    }
```

### 2.10 Phase 4: Generate L1 Report & Handoff Context

```python
# Generate L1 (summary) and prepare handoff for /research
async def generate_l1_report_and_handoff(aggregated, review_gate_result, workload_slug, log_path):
    print("\n📝 Generating L1 report and handoff context...")

    timestamp = datetime.now().isoformat()

    # Calculate summary metrics
    total_components = len(aggregated['components'])
    total_findings = len(aggregated['findings'])
    total_issues = len(aggregated['issues'])
    risk_level = aggregated['risk_summary'].get('critical', 0) > 0 and 'CRITICAL' or \
                 aggregated['risk_summary'].get('high', 0) > 0 and 'HIGH' or \
                 aggregated['risk_summary'].get('medium', 0) > 0 and 'MEDIUM' or 'LOW'

    # Update handoff context in YAML log
    key_findings = [f['description'] for f in aggregated['findings'][:5]]
    priority_components = [c['name'] for c in aggregated['components'] if any(
        i['component_id'] == c['id'] and i['severity'] in ['critical', 'high']
        for i in aggregated['issues']
    )]
    recommended_focus = [r['description'] for r in aggregated['recommendations'][:3]]

    yaml_update_handoff(
        log_path,
        summary=f"{total_components}개 컴포넌트 분석 완료, {total_findings}개 발견사항, 리스크 수준: {risk_level}",
        key_findings=','.join(key_findings),
        priority_comps=','.join(priority_components),
        focus_areas=','.join(recommended_focus)
    )

    # L1 Summary (returned to user)
    l1_summary = f'''# Re-Architecture 분석 요약 (L1)

**Workload:** {workload_slug}
**리스크 수준:** {risk_level}
**검토:** {'✅ 승인됨' if review_gate_result['approved'] else '⚠️ 검토 필요'}

## 주요 지표
- 컴포넌트: {total_components}개
- 발견사항: {total_findings}개
- 이슈: {total_issues}개
- 권장사항: {len(aggregated['recommendations'])}개

## 상태
{'✅ 분석 완료. /research 진행 준비됨.' if review_gate_result['approved']
 else f"⚠️ 검토 필요: {len(review_gate_result['review'].get('warnings', []))}개 경고"}

## L2 상세 내용
참조: `.agent/prompts/{workload_slug}/re-architecture-log.yaml`

*Generated by /re-architecture v2.0.0 (EFL Pattern) at {timestamp}*
'''

    # Final user prompt
    response = AskUserQuestion(
        questions=[{
            "question": "분석이 완료되었습니다. /research로 진행하시겠습니까?",
            "header": "핸드오프",
            "options": [
                {"label": "/research로 진행 (권장)", "description": f"분석 결과를 바탕으로 심층 연구 시작\n📋 근거: {total_findings}개 주요 발견사항이 추가 연구 필요"},
                {"label": "분석 결과만 저장", "description": "나중에 수동으로 /research 호출\n📋 근거: 현재 결과만으로 충분하거나 다른 작업 우선"},
                {"label": "추가 분석 진행", "description": "놓친 컴포넌트 추가 분석\n📋 근거: 일부 영역이 충분히 분석되지 않음"}
            ],
            "multiSelect": False
        }]
    )

    print(f"\n  ✅ L1 summary generated ({len(l1_summary)} chars)")
    print(f"  📁 L2 log: {log_path}")

    return {
        'l1_summary': l1_summary,
        'l2_log_path': log_path,
        'user_selection': response,
        'risk_level': risk_level,
        'review_approved': review_gate_result['approved'],
        'next_action_hint': f"/research --clarify-slug {workload_slug}"
    }
```

---

## 3. YAML Log Schema (Traceability Focus)

### 3.1 Full Schema

```yaml
# .agent/prompts/{slug}/re-architecture-log.yaml

metadata:
  id: "{slug}"
  version: "2.0.0"
  created_at: "2026-01-26T21:10:00Z"
  updated_at: "2026-01-26T21:15:00Z"
  status: "in_progress"  # in_progress | completed | paused
  target_path: "{분석 대상 경로}"

# 세션 상태 추적
state:
  current_phase: "decomposition"  # decomposition | analysis | feedback | handoff
  current_component: null
  round: 1
  total_components: 0
  analyzed_components: 0

# 사용자 의도 및 요구사항 (CRITICAL for traceability)
user_intent:
  original_request: |
    {사용자 원본 요청}
  clarified_goals: []    # 명확화된 목표들
  constraints: []        # 제약 조건
  priorities: []         # 우선순위

# 컴포넌트 분해 결과 (L2 Horizontal)
decomposition:
  pipeline_structure: |
    {파이프라인 구조 다이어그램}
  components:
    - id: "comp-001"
      name: "{컴포넌트명}"
      path: "{파일/디렉토리 경로}"
      type: "stage|module|service|utility"
      dependencies:
        upstream: []
        downstream: []
      status: "pending"  # pending | analyzing | completed

# 상호작용 라운드 기록 (Incremental)
rounds:
  - round: 1
    timestamp: "2026-01-26T21:11:00Z"
    phase: "decomposition"
    component_id: null

    # 입력
    input:
      prompt: "{사용자/시스템 입력}"
      context: "{관련 컨텍스트}"

    # 분석 결과 (L3 Vertical)
    analysis:
      findings: []           # 발견사항
      recommendations: []    # 권장사항
      issues: []             # 잠재적 이슈
      code_evidence: []      # 코드 근거

    # 출력
    output:
      feedback: |
        {생성된 피드백}
      options_presented:     # 제시된 선택지
        - label: "{선택지}"
          rationale: "{판단근거}"
      user_selection: null   # 사용자 선택

    # 추적성 필드 (CRITICAL)
    traceability:
      design_intent: |
        {이 라운드의 설계 의도}
      decision_rationale: |
        {결정 판단근거}
      related_components: []
      parent_round: null     # 이전 라운드 참조
      issue_refs: []         # 관련 이슈 ID

# 컴포넌트별 피드백 결과
component_feedback:
  "comp-001":
    analyzed_at: "2026-01-26T21:12:00Z"
    summary: "{컴포넌트 요약}"

    findings:
      - id: "find-001"
        type: "pattern|issue|opportunity"
        severity: "info|warning|critical"
        description: "{발견사항 상세}"
        evidence:
          file: "{파일 경로}"
          line: "{라인 번호}"
          snippet: "{코드 스니펫}"

    recommendations:
      - id: "rec-001"
        priority: "high|medium|low"
        description: "{권장사항}"
        rationale: "{판단근거}"
        effort_estimate: "small|medium|large"

    issues:
      - id: "issue-001"
        type: "bug|debt|risk|improvement"
        severity: "critical|high|medium|low"
        description: "{이슈 설명}"
        suggested_action: "{권장 조치}"
        blocking: false

# 핸드오프 정보 (/research 연계)
handoff:
  ready_for_research: false
  research_context:
    summary: "{분석 요약}"
    key_findings: []
    priority_components: []
    recommended_focus: []
  next_action_hint: "/research --clarify-slug {slug}"

# EFL 메타데이터 (V2.0.0)
efl_metadata:
  version: "2.0.0"
  patterns_applied:
    - "P1: Sub-Orchestrator"
    - "P3: L2/L3 structure"
    - "P5: Review Gate"
    - "P6: Internal Loop"
  agent_delegation:
    phase_3a_l2_horizontal:
      iterations: 1
      status: "completed"
    phase_3b_l3_vertical:
      iterations: 1
      status: "completed"
  review_gate:
    approved: false
    criteria_met: 0

# 파이프라인 통합
pipeline:
  downstream_skills: []
  context_hash: null
  decision_trace: []
```

### 3.2 Schema Design Rationale

| Section | Purpose | Traceability Value |
|---------|---------|-------------------|
| `metadata` | 세션 메타데이터 | 시간/버전 추적 |
| `state` | 현재 진행 상태 | 재개 지원 |
| `user_intent` | 사용자 의도/요구사항 | **의사결정 근거** |
| `decomposition` | 컴포넌트 분해 (L2) | 구조 파악 |
| `rounds` | 상호작용 기록 | **전체 이력 추적** |
| `component_feedback` | 컴포넌트별 결과 (L3) | 상세 분석 |
| `handoff` | /research 연계 | 파이프라인 연결 |
| `efl_metadata` | EFL 패턴 추적 | **피드백 루프 검증** |

---

## 4. Output Format (L1/L2/L3)

### 4.1 L1 Return Summary (Concise)

```yaml
taskId: re-arch-{slug}
status: success
summary: "{n}개 컴포넌트 분석 완료, {findings}개 발견사항, {risk_level} 리스크"

logPath: .agent/prompts/{slug}/re-architecture-log.yaml
handoffReady: true
nextActionHint: "/research --clarify-slug {slug}"

efl_metadata:
  version: "2.0.0"
  agent_delegation: true
  internal_iterations: {total}
  review_gate_approved: true
```

### 4.2 L2 Detailed Log (Full YAML)

See Section 3.1 for full schema.

### 4.3 L3 Code Evidence (Within Rounds)

```yaml
# Within rounds[].analysis.code_evidence
code_evidence:
  - file: "/path/to/file.py"
    line: 42
    snippet: |
      def process_data(input):
          # TODO: Add validation
          return transform(input)
    finding_id: "find-001"
    description: "입력 검증 누락"
```

---

## 5. Integration Points

### 5.1 Pipeline Position

```
/clarify (optional)
    │
    │ clarify_slug (optional)
    ▼
/re-architecture  ◄── THIS SKILL (V2.0.0)
    │
    │ re-architecture-log.yaml
    ▼
/research                    심층 연구 (선택적)
    │
    ▼
/planning                    구현 계획 수립
```

### 5.2 /research Handoff Contract

| Field | Type | Description |
|-------|------|-------------|
| `handoff.summary` | string | 분석 요약 |
| `handoff.key_findings` | array | 주요 발견사항 |
| `handoff.priority_components` | array | 우선 분석 컴포넌트 |
| `handoff.recommended_focus` | array | 권장 연구 영역 |

---

## 6. Error Handling

| Error | Detection | Recovery |
|-------|-----------|----------|
| Target path not found | File/dir not exists | Prompt for correct path |
| YAML write failure | I/O error | Memory fallback + warning |
| Component analysis timeout | >5min | Save partial, allow resume |
| User session timeout | No response | Auto-save, resume later |
| Agent delegation failure | Task tool error | Fallback to direct analysis |
| Review gate failure | P5 criteria not met | Show warnings, allow override |

---

## 7. Testing Checklist

### Core Functionality
- [ ] `/re-architecture <path>` 기본 실행
- [ ] `/re-architecture --resume {slug}` 재개 테스트
- [ ] YAML 로그 스키마 검증
- [ ] Incremental update 동작 확인
- [ ] 컴포넌트 분해 정확성
- [ ] 피드백 생성 품질
- [ ] /research 핸드오프 연계
- [ ] traceability 필드 기록 확인
- [ ] 한국어 출력 검증
- [ ] Stop hook 트리거 확인

### EFL Pattern Tests (V2.0.0)

**P1: Sub-Orchestrator (Agent Delegation)**
- [ ] Agent delegation to Phase 3-A (L2 Horizontal)
- [ ] Agent delegation to Phase 3-B (L3 Vertical)
- [ ] Complexity-based agent count selection
- [ ] Fallback to direct analysis when delegation fails

**P3: General-Purpose Synthesis (L2/L3 Structure)**
- [ ] Phase 3-A extracts component structure (L2)
- [ ] Phase 3-B performs deep analysis (L3)
- [ ] L2/L3 properly separated in YAML log
- [ ] L1 summary concise (<500 tokens)

**P4: Selective Feedback**
- [ ] Severity-based feedback check (MEDIUM+ threshold)
- [ ] LOW severity → log only
- [ ] MEDIUM+ severity → trigger review

**P5: Phase 3.5 Review Gate**
- [ ] Review gate executes before handoff
- [ ] Review criteria checked (requirement_alignment, etc.)
- [ ] Approved result allows /research handoff
- [ ] Failed review shows warnings

**P6: Agent Internal Feedback Loop**
- [ ] Agent prompts include internal loop instructions
- [ ] Internal loop metadata extracted from agent results
- [ ] Max 3 iterations enforced per agent
- [ ] Iteration count tracked in efl_metadata

---

## 8. Parameter Module Compatibility (V2.1.0)

| Module | Status | Notes |
|--------|--------|-------|
| `model-selection.md` | ✅ | `opus` for comprehensive analysis |
| `context-mode.md` | ✅ | `fork` for isolated execution |
| `tool-config.md` | ✅ | Read, Grep, Glob, Task, Write, Edit, AskUserQuestion, MCP |
| `hook-config.md` | ✅ | Setup + Stop hooks, 180000ms timeout |
| `permission-mode.md` | N/A | Skill-specific |
| `task-params.md` | ✅ | Explore delegation for structure analysis |
| `feedback-loop.md` | ✅ | P6: Internal feedback loop for analysis |
| `selective-feedback.md` | ✅ | P4: Severity-based filtering |

---

## Version History

| Version | Change |
|---------|--------|
| 1.0.0 | Initial /re-architecture skill implementation |
| 2.0.0 | **EFL Integration**: P1 (Sub-Orchestrator), P3 (L2/L3 structure), P5 (Review Gate), P6 (Internal Loop) |

### V2.0.0 Detailed Changes

**Enhanced Feedback Loop (EFL) Patterns:**
- **P1: Skill as Sub-Orchestrator** - Delegates to specialized agents instead of direct execution
- **P3: General-Purpose Synthesis** - Phase 3-A (L2 horizontal) + Phase 3-B (L3 vertical) structure
- **P5: Phase 3.5 Review Gate** - Holistic verification before /research handoff
- **P6: Agent Internal Feedback Loop** - Agent self-validation with max 3 iterations
- **P4: Selective Feedback** - Severity-based threshold (MEDIUM+)

**New Frontmatter Config:**
- `agent_delegation` config
- `agent_internal_feedback_loop` config with validation criteria
- `review_gate` config with Phase 3.5 criteria
- `selective_feedback` config with severity thresholds
- Setup hook: `shared/validation-feedback-loop.sh`

**Modified Execution Flow:**
1. Phase 0: Workload detection (unchanged, hook-based)
2. Phase 1: Agent delegation (NEW) - Replaces direct component scan
3. Phase 2: Aggregate L2/L3 results (NEW) - Structured synthesis
4. Phase 3: Interactive component review (ENHANCED) - Uses aggregated data
5. Phase 3.5: Review gate (NEW) - P5 verification
6. Phase 4: Generate L1 report & handoff (ENHANCED) - Separated output layers

**Backward Compatibility:**
- `--resume` flag still works
- Existing YAML log schema extended (not replaced)
- Korean language output maintained
- helpers.sh functions unchanged
- Hook scripts unchanged

---

## 10. Standalone Execution (V2.1.0)

> /re-architecture는 /clarify 대신 **기존 아키텍처 분석**을 위한 진입점으로 독립 실행 가능

### 10.1 독립 실행 모드

```bash
# 독립 실행 (upstream 없이)
/re-architecture src/components/

# 기존 분석 재개
/re-architecture --resume arch-analysis-20260128-143022
```

### 10.2 Workload Context Resolution

```javascript
// skill-standalone.sh 사용
source /home/palantir/.claude/skills/shared/skill-standalone.sh

// Workload 감지 우선순위:
// 1. --resume 인자의 slug
// 2. Active workload (_active_workload.yaml)
// 3. 새 workload 생성 (target path 기반)

const context = init_skill_context("re-architecture", ARGUMENTS, TARGET_PATH)
const { workload_id, slug, workload_dir, is_standalone } = context
```

---

## 11. Handoff Contract (V2.1.0)

> /re-architecture → /research → /planning 파이프라인 경로

### 11.1 Handoff 매핑

| Status | Next Skill | Arguments |
|--------|------------|-----------|
| `completed` | `/research` | `--re-architecture-slug {slug}` |

### 11.2 Handoff YAML 출력

```yaml
handoff:
  skill: "re-architecture"
  workload_slug: "{slug}"
  status: "completed"
  timestamp: "2026-01-28T14:35:00Z"
  next_action:
    skill: "/research"
    arguments: "--re-architecture-slug {slug}"
    required: true
    reason: "Architecture analysis complete, ready for deep research"
```

### 11.3 Upstream/Downstream

```
[독립 진입점]
    │
    ▼
/re-architecture ──▶ /research ──▶ /planning ──▶ /orchestrate
    │
    └── Output: .agent/prompts/{slug}/re-architecture.yaml
```

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 2.1.0 | 2026-01-28 | Standalone Execution + Handoff Contract |
| 2.0.0 | 2026-01-28 | EFL Pattern Integration (P1/P3/P5/P6) |
| 1.0.0 | 2026-01-26 | Initial implementation |

---

*Created by /build skill | 2026-01-26*
*Updated to V2.1.0 (Standalone + Handoff) | 2026-01-28*
