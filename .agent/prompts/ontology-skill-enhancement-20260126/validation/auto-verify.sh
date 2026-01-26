#!/bin/bash
# =============================================================================
# Auto-Verification Script for Ontology Skill Enhancement
# =============================================================================
# Workload: ontology-skill-enhancement-20260126
# Purpose: Task #1, #2 완료물에 대한 자동 검증
# Usage: bash auto-verify.sh [task1|task2|all]
# =============================================================================

set -e

SKILL_DIR="/home/palantir/.claude/skills"
OBJECTTYPE_SKILL="$SKILL_DIR/ontology-objecttype/SKILL.md"
WHY_SKILL="$SKILL_DIR/ontology-why/SKILL.md"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Counters
PASS=0
FAIL=0
WARN=0

check() {
    local description="$1"
    local command="$2"
    local expected="$3"

    result=$(eval "$command" 2>/dev/null || echo "0")

    if [[ "$result" -ge "$expected" ]]; then
        echo -e "${GREEN}✅ PASS${NC}: $description (found: $result, expected: >=$expected)"
        ((PASS++))
    else
        echo -e "${RED}❌ FAIL${NC}: $description (found: $result, expected: >=$expected)"
        ((FAIL++))
    fi
}

warn_check() {
    local description="$1"
    local command="$2"
    local expected="$3"

    result=$(eval "$command" 2>/dev/null || echo "0")

    if [[ "$result" -ge "$expected" ]]; then
        echo -e "${GREEN}✅ PASS${NC}: $description (found: $result)"
        ((PASS++))
    else
        echo -e "${YELLOW}⚠️ WARN${NC}: $description (found: $result, recommended: >=$expected)"
        ((WARN++))
    fi
}

# =============================================================================
# Task #1 Verification: /ontology-objecttype
# =============================================================================
verify_task1() {
    echo ""
    echo "═══════════════════════════════════════════════════════════════"
    echo "  Task #1 Verification: /ontology-objecttype 워크플로우 재설계"
    echo "═══════════════════════════════════════════════════════════════"
    echo ""

    if [[ ! -f "$OBJECTTYPE_SKILL" ]]; then
        echo -e "${RED}ERROR: $OBJECTTYPE_SKILL not found${NC}"
        return 1
    fi

    echo "📋 1.1 Phase Workflow 구현"
    echo "-----------------------------------------------------------"
    check "Phase 1 구현" "grep -c 'Phase 1' $OBJECTTYPE_SKILL" 1
    check "Phase 2 구현" "grep -c 'Phase 2' $OBJECTTYPE_SKILL" 1
    check "Phase 3 구현" "grep -c 'Phase 3' $OBJECTTYPE_SKILL" 1
    check "Phase 4 구현" "grep -c 'Phase 4' $OBJECTTYPE_SKILL" 1

    echo ""
    echo "📋 1.2 AskUserQuestion 구현"
    echo "-----------------------------------------------------------"
    check "AskUserQuestion 호출 (4개 이상)" "grep -c 'AskUserQuestion' $OBJECTTYPE_SKILL" 4

    echo ""
    echo "📋 1.3 Primary Key Strategy"
    echo "-----------------------------------------------------------"
    check "single_column 옵션" "grep -c 'single_column' $OBJECTTYPE_SKILL" 1
    check "composite 옵션" "grep -c 'composite' $OBJECTTYPE_SKILL" 1
    check "composite_hashed 옵션" "grep -c 'composite_hashed' $OBJECTTYPE_SKILL" 1

    echo ""
    echo "📋 1.4 Cardinality Decision Tree"
    echo "-----------------------------------------------------------"
    check "ONE_TO_ONE 가이드" "grep -ci 'one.to.one\|1:1' $OBJECTTYPE_SKILL" 1
    check "MANY_TO_ONE 가이드" "grep -ci 'many.to.one\|N:1' $OBJECTTYPE_SKILL" 1
    check "MANY_TO_MANY 가이드" "grep -ci 'many.to.many\|M:N\|N:N' $OBJECTTYPE_SKILL" 1

    echo ""
    echo "📋 1.5 DataType 매핑 (20개)"
    echo "-----------------------------------------------------------"
    warn_check "STRING 타입" "grep -c 'STRING' $OBJECTTYPE_SKILL" 1
    warn_check "INTEGER 타입" "grep -c 'INTEGER' $OBJECTTYPE_SKILL" 1
    warn_check "TIMESTAMP 타입" "grep -c 'TIMESTAMP' $OBJECTTYPE_SKILL" 1
    warn_check "ARRAY 타입" "grep -c 'ARRAY' $OBJECTTYPE_SKILL" 1
    warn_check "VECTOR 타입" "grep -c 'VECTOR' $OBJECTTYPE_SKILL" 1

    echo ""
    echo "📋 1.6 Output Format (YAML)"
    echo "-----------------------------------------------------------"
    check "YAML 출력 명세" "grep -ci 'yaml' $OBJECTTYPE_SKILL" 1

    echo ""
}

# =============================================================================
# Task #2 Verification: /ontology-why
# =============================================================================
verify_task2() {
    echo ""
    echo "═══════════════════════════════════════════════════════════════"
    echo "  Task #2 Verification: /ontology-why Integrity 분석 강화"
    echo "═══════════════════════════════════════════════════════════════"
    echo ""

    if [[ ! -f "$WHY_SKILL" ]]; then
        echo -e "${RED}ERROR: $WHY_SKILL not found${NC}"
        return 1
    fi

    echo "📋 2.1 5가지 Integrity 관점"
    echo "-----------------------------------------------------------"
    check "Immutability (불변성)" "grep -c 'Immutability' $WHY_SKILL" 1
    check "Determinism (결정성)" "grep -c 'Determinism' $WHY_SKILL" 1
    check "Referential Integrity" "grep -c 'Referential Integrity' $WHY_SKILL" 1
    check "Semantic Consistency" "grep -c 'Semantic Consistency' $WHY_SKILL" 1
    check "Lifecycle Management" "grep -c 'Lifecycle' $WHY_SKILL" 1

    echo ""
    echo "📋 2.2 외부 검색 통합"
    echo "-----------------------------------------------------------"
    check "WebSearch 통합" "grep -c 'WebSearch' $WHY_SKILL" 1
    warn_check "Context7 MCP" "grep -c 'context7\|Context7' $WHY_SKILL" 1

    echo ""
    echo "📋 2.3 출력 형식"
    echo "-----------------------------------------------------------"
    check "Palantir URL 참조" "grep -c 'palantir.com' $WHY_SKILL" 1

    echo ""
}

# =============================================================================
# Summary
# =============================================================================
print_summary() {
    echo "═══════════════════════════════════════════════════════════════"
    echo "  Verification Summary"
    echo "═══════════════════════════════════════════════════════════════"
    echo ""
    echo -e "  ${GREEN}PASS${NC}: $PASS"
    echo -e "  ${RED}FAIL${NC}: $FAIL"
    echo -e "  ${YELLOW}WARN${NC}: $WARN"
    echo ""

    if [[ $FAIL -eq 0 ]]; then
        echo -e "${GREEN}✅ All critical checks passed!${NC}"
        return 0
    else
        echo -e "${RED}❌ Some checks failed. Review required.${NC}"
        return 1
    fi
}

# =============================================================================
# Main
# =============================================================================
main() {
    echo "═══════════════════════════════════════════════════════════════"
    echo "  Ontology Skill Enhancement - Auto Verification"
    echo "  Workload: ontology-skill-enhancement-20260126"
    echo "  Date: $(date '+%Y-%m-%d %H:%M:%S')"
    echo "═══════════════════════════════════════════════════════════════"

    case "${1:-all}" in
        task1)
            verify_task1
            ;;
        task2)
            verify_task2
            ;;
        all)
            verify_task1
            verify_task2
            ;;
        *)
            echo "Usage: $0 [task1|task2|all]"
            exit 1
            ;;
    esac

    print_summary
}

main "$@"
