"""
UCLP Reference API 사용 예제
uclp-reference.json을 조회하는 API 함수들
"""

import json
from typing import Dict, List, Optional


class UCLPReference:
    """UCLP Tier-2 참조 문서 조회 클래스"""

    def __init__(self, json_path: str = "uclp-reference.json"):
        with open(json_path, 'r', encoding='utf-8') as f:
            self.data = json.load(f)

    def get_example(self, concept_id: str, language: str) -> Optional[Dict]:
        """
        특정 개념의 언어별 예제 조회

        Args:
            concept_id: 'variable_declaration', 'error_handling', 'concurrency'
            language: 'go', 'python', 'swift', 'typescript'

        Returns:
            {"syntax": "...", "design_decision": "...", "sources": [...]}
        """
        examples = self.data.get("examples", {})
        concept = examples.get(concept_id, {})
        return concept.get(language)

    def get_required_axes(self, category: str) -> List[str]:
        """
        카테고리별 필수 비교 축 조회

        Args:
            category: 'basics', 'functions', 'data_structures', 'error_handling',
                     'concurrency', 'abstraction', 'modules', 'memory'

        Returns:
            ["syntax", "type_system", "default_value", ...]
        """
        categories = self.data["comparison_framework"]["categories"]
        cat_data = categories.get(category, {})
        return cat_data.get("required_axes", [])

    def get_axis_definition(self, axis_id: str) -> Optional[Dict]:
        """
        축 정의 조회

        Args:
            axis_id: 'syntax', 'philosophy', 'tradeoff', etc.

        Returns:
            {"name": "Syntax", "description": "Concrete notation differences"}
        """
        axes = self.data["comparison_framework"]["axes"]
        return axes.get(axis_id)

    def get_validation_command(self, language: str, mode: str = "light") -> Optional[str]:
        """
        코드 검증 명령어 조회

        Args:
            language: 'go', 'python', 'swift', 'typescript'
            mode: 'light' (기본) 또는 'strict'

        Returns:
            "gofmt -e {file}"
        """
        langs = self.data["code_validation"]["languages"]
        lang_data = langs.get(language, {})
        mode_data = lang_data.get(mode, {})
        return mode_data.get("command")

    def get_sources(self, language: str) -> List[Dict]:
        """
        언어별 공식 문서 목록 조회

        Args:
            language: 'go', 'python', 'swift', 'typescript'

        Returns:
            [{"title": "...", "url": "...", "type": "official_doc", ...}, ...]
        """
        sources = self.data.get("sources", {})
        return sources.get(language, [])

    def get_idiomatic_patterns(self, language: str) -> List[Dict]:
        """
        언어별 관용구 패턴 조회

        Args:
            language: 'go', 'python', 'swift', 'typescript'

        Returns:
            [{"pattern": "...", "usage": "...", "philosophy": "..."}, ...]
        """
        patterns = self.data["comparison_framework"]["idiomatic_patterns"]
        return patterns.get(language, [])

    def get_concepts_by_category(self, category: str) -> List[Dict]:
        """
        카테고리별 개념 목록 조회

        Args:
            category: 'basics', 'functions', etc.

        Returns:
            [{"id": "variable_declaration", "name": "...", "prerequisites": [...], ...}, ...]
        """
        categories = self.data["comparison_framework"]["categories"]
        cat_data = categories.get(category, {})
        return cat_data.get("concepts", [])

    def detect_depth_level(self, query: str) -> str:
        """
        질문에서 깊이 레벨 자동 감지

        Args:
            query: 사용자 질문

        Returns:
            'beginner', 'intermediate', 'advanced'
        """
        query_lower = query.lower()
        indicators = self.data["depth_selection"]["indicators"]

        # 우선순위: advanced → intermediate → beginner
        for keyword in indicators["advanced"]:
            if keyword in query_lower:
                return "advanced"

        for keyword in indicators["intermediate"]:
            if keyword in query_lower:
                return "intermediate"

        for keyword in indicators["beginner"]:
            if keyword in query_lower:
                return "beginner"

        return self.data["depth_selection"]["default_level"]


# 사용 예제
if __name__ == "__main__":
    ref = UCLPReference("/home/palantir/math/uclp-reference.json")

    print("=== 예제 1: Go의 error_handling 예제 조회 ===")
    example = ref.get_example("error_handling", "go")
    if example:
        print(f"Syntax: {example['syntax']}")
        print(f"Design Decision: {example['design_decision']}")
        print(f"Sources: {len(example['sources'])}개")

    print("\n=== 예제 2: basics 카테고리의 필수 축 조회 ===")
    axes = ref.get_required_axes("basics")
    print(f"Required axes: {axes}")

    print("\n=== 예제 3: Python light 검증 명령어 조회 ===")
    cmd = ref.get_validation_command("python", "light")
    print(f"Command: {cmd}")

    print("\n=== 예제 4: Swift 공식 문서 조회 ===")
    sources = ref.get_sources("swift")
    for src in sources:
        print(f"- {src['title']}: {src['url']}")

    print("\n=== 예제 5: TypeScript 관용구 패턴 조회 ===")
    patterns = ref.get_idiomatic_patterns("typescript")
    for p in patterns[:2]:  # 처음 2개만 출력
        print(f"- {p['pattern']}: {p['usage']}")

    print("\n=== 예제 6: 깊이 레벨 자동 감지 ===")
    queries = [
        "What is a variable in Go?",
        "Why does Swift use optionals?",
        "How does the compiler optimize goroutine scheduling?"
    ]
    for q in queries:
        level = ref.detect_depth_level(q)
        print(f"Query: '{q}' → Level: {level}")
