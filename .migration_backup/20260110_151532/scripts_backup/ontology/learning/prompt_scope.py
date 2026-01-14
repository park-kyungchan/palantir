"""
Prompt-scoped curriculum selection for Orion's Codebase-as-Curriculum tutoring engine.

Goal: turn an "agile" user prompt into a ranked set of code artifacts (files) to study,
across a mixed-language repository (Python/TS/JS/Go).

This is intentionally heuristic (no external parsers / no network) and relies on:
- file paths
- extracted imports (metrics)
- detected domain patterns (metrics)
- dependency graph neighborhood expansion
- optional entrypoint hints
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Mapping, Sequence

from scripts.ontology.learning.engine import TutoringEngine


_TOKEN_SPLIT_RE = re.compile(r"[\s/\\._:\-+(){}\[\],;<>|!?\"'`~@#$%^&*=]+")
_KEEP_CHARS_RE = re.compile(r"[^0-9a-zA-Z가-힣]+")

# Minimal bilingual / synonym normalization so Korean prompts can steer scope.
_ALIASES: Mapping[str, str] = {
    "진입점": "entrypoint",
    "엔트리포인트": "entrypoint",
    "시작점": "entrypoint",
    "시작": "start",
    "워크플로우": "workflow",
    "흐름": "workflow",
    "아키텍처": "architecture",
    "설계": "design",
    "동적": "dynamic",
    "애자일": "agile",
    "배포": "deployment",
    "운영": "operations",
    "테스트": "testing",
    "파이썬": "python",
    "자바스크립트": "javascript",
    "타입스크립트": "typescript",
    "고": "go",
    "골랭": "go",
    "오디에이": "oda",
    "온톨로지": "ontology",
    "oda": "ontology",  # common expansion
}

# Query token -> detected pattern name(s)
_TOKEN_TO_PATTERNS: Mapping[str, tuple[str, ...]] = {
    "react": ("react_component", "react_hook"),
    "hooks": ("react_hook",),
    "blueprint": ("blueprint_ui",),
    "osdk": ("osdk_client",),
    "graphql": ("graphql",),
    "websocket": ("websocket",),
    "worker": ("worker_thread",),
    "goroutine": ("goroutine",),
    "channel": ("channel",),
    "grpc": ("grpc",),
    "http": ("http_server",),
}


@dataclass(frozen=True)
class PromptIntent:
    wants_workflow: bool
    wants_entrypoint: bool
    wants_architecture: bool
    wants_deployment: bool
    wants_testing: bool
    wants_python: bool
    wants_go: bool
    wants_ts_js: bool


def _tokenize(text: str) -> list[str]:
    """
    Tokenize user prompt into a normalized list.

    Keeps Korean characters as tokens to allow alias expansion.
    """
    cleaned = _KEEP_CHARS_RE.sub(" ", text.lower())
    raw = [t for t in _TOKEN_SPLIT_RE.split(cleaned) if t]
    tokens: list[str] = []
    for t in raw:
        if len(t) < 2 and t not in {"go", "ts", "js"}:
            continue
        tokens.append(t)
    return tokens


def _normalize_terms(tokens: Sequence[str]) -> list[str]:
    normalized: list[str] = []
    for t in tokens:
        normalized.append(t)
        alias = _ALIASES.get(t)
        if alias and alias != t:
            normalized.append(alias)
        else:
            # Korean postpositions often attach (e.g., "진입점부터"); allow substring aliasing for known terms.
            for key, value in _ALIASES.items():
                if key == t:
                    continue
                if len(key) >= 2 and key in t and value != t:
                    normalized.append(value)
    # De-dupe preserving order
    seen = set()
    out: list[str] = []
    for t in normalized:
        if t in seen:
            continue
        seen.add(t)
        out.append(t)
    return out


def _infer_intent(terms: Sequence[str]) -> PromptIntent:
    term_set = set(terms)
    wants_entrypoint = bool(term_set.intersection({"entrypoint", "start", "bootstrap", "main"}))
    wants_workflow = bool(term_set.intersection({"workflow", "flow", "pipeline"}))
    wants_architecture = bool(term_set.intersection({"architecture", "design", "system", "oda", "ontology"}))
    wants_deployment = bool(term_set.intersection({"deployment", "deploy", "k8s", "kubernetes", "helm", "terraform", "ci", "cd", "operations"}))
    wants_testing = bool(term_set.intersection({"testing", "test", "pytest", "jest", "unit", "integration", "e2e"}))
    wants_python = bool(term_set.intersection({"python", "py"}))
    wants_go = bool(term_set.intersection({"go", "golang"}))
    wants_ts_js = bool(term_set.intersection({"typescript", "javascript", "ts", "js", "node", "react"}))
    return PromptIntent(
        wants_workflow=wants_workflow,
        wants_entrypoint=wants_entrypoint,
        wants_architecture=wants_architecture,
        wants_deployment=wants_deployment,
        wants_testing=wants_testing,
        wants_python=wants_python,
        wants_go=wants_go,
        wants_ts_js=wants_ts_js,
    )


def _path_tokens(rel_path: str) -> set[str]:
    parts = _TOKEN_SPLIT_RE.split(rel_path.lower())
    return {p for p in parts if p}


def _import_tokens(imports: Iterable[str]) -> set[str]:
    tokens: set[str] = set()
    for imp in imports:
        for p in _TOKEN_SPLIT_RE.split(imp.lower()):
            if p:
                tokens.add(p)
    return tokens

def _symbol_tokens(symbols: Iterable[str]) -> set[str]:
    tokens: set[str] = set()
    for s in symbols:
        for p in _TOKEN_SPLIT_RE.split(str(s).lower()):
            if p:
                tokens.add(p)
    return tokens


def _score_file(
    *,
    rel_path: str,
    tutor: TutoringEngine,
    terms: Sequence[str],
    intent: PromptIntent,
    entrypoints: set[str],
    role: str | None,
) -> tuple[float, dict[str, list[str]]]:
    """
    Returns (raw_score, reasons).
    """
    metric = tutor.metrics.get(rel_path)
    if metric is None:
        return 0.0, {}

    terms_set = set(terms)
    ext = Path(rel_path).suffix.lower()

    reasons: dict[str, list[str]] = {}
    raw = 0.0

    ptoks = _path_tokens(rel_path)
    path_hits = sorted(t for t in terms_set if t in ptoks)
    if path_hits:
        raw += 2.0 * len(path_hits)
        reasons["path"] = path_hits

    itoks = _import_tokens(metric.imports)
    import_hits = sorted(t for t in terms_set if t in itoks)
    if import_hits:
        raw += 1.5 * len(import_hits)
        reasons["imports"] = import_hits

    stoks = _symbol_tokens(getattr(metric, "symbols", []) or [])
    symbol_hits = sorted(t for t in terms_set if t in stoks)
    if symbol_hits:
        raw += 1.8 * len(symbol_hits)
        reasons["symbols"] = symbol_hits

    patterns = set(metric.identified_patterns)
    pattern_hits: set[str] = set()
    for t in terms_set:
        mapped = _TOKEN_TO_PATTERNS.get(t)
        if not mapped:
            continue
        for p in mapped:
            if p in patterns:
                pattern_hits.add(p)
    if pattern_hits:
        raw += 2.5 * len(pattern_hits)
        reasons["patterns"] = sorted(pattern_hits)

    # Language preference boosts
    if intent.wants_python and ext == ".py":
        raw += 1.0
        reasons.setdefault("language", []).append("python")
    if intent.wants_go and ext == ".go":
        raw += 1.0
        reasons.setdefault("language", []).append("go")
    if intent.wants_ts_js and ext in {".ts", ".tsx", ".js", ".jsx", ".mjs", ".cjs", ".mts", ".cts"}:
        raw += 1.0
        reasons.setdefault("language", []).append("ts_js")

    # Entrypoint boost when user asks "start from entrypoint / workflow".
    if rel_path in entrypoints and (intent.wants_entrypoint or intent.wants_workflow):
        raw += 3.0
        reasons.setdefault("entrypoint", []).append("detected_entrypoint")

    # Role-aware boosts (keep lightweight; prompt intent is still primary).
    role_norm = (role or "").lower()
    if role_norm == "fde":
        if patterns.intersection(
            {
                "react_component",
                "react_hook",
                "blueprint_ui",
                "osdk_client",
                "graphql",
                "websocket",
                "worker_thread",
            }
        ):
            raw += 1.0
            reasons.setdefault("role", []).append("fde_frontend_boost")
    elif role_norm == "deployment_strategist":
        if ext in {".go", ".py"}:
            raw += 0.5
            reasons.setdefault("role", []).append("deploy_backend_lang_boost")
        if patterns.intersection({"grpc", "http_server", "goroutine", "channel"}):
            raw += 1.0
            reasons.setdefault("role", []).append("deploy_service_boost")
        if any(k in rel_path.lower() for k in ["deploy", "infra", "k8s", "kubernetes", "docker", "ci", "cd", "pipeline", "config"]):
            raw += 0.8
            reasons.setdefault("role", []).append("deploy_path_boost")

    return raw, reasons


def _reverse_adj(adj: Mapping[str, set[str]]) -> dict[str, set[str]]:
    rev: dict[str, set[str]] = {k: set() for k in adj}
    for src, deps in adj.items():
        for dep in deps:
            rev.setdefault(dep, set()).add(src)
    return rev


def build_prompt_scope(
    *,
    prompt: str,
    tutor: TutoringEngine,
    entrypoints: Sequence[str] | None = None,
    workflow_artifacts: Sequence[Mapping] | None = None,
    role: str | None = None,
    limit: int = 12,
    expand_hops: int = 1,
    seed_limit: int = 5,
) -> dict:
    """
    Returns a JSON-serializable dict describing a prompt-driven scope:
    - inferred intent
    - ranked relevant files with rationale
    - suggested entrypoints
    - allowlist (top scoped files)
    """
    if not prompt.strip():
        return {
            "prompt": prompt,
            "terms": [],
            "intent": PromptIntent(False, False, False, False, False, False, False, False).__dict__,
            "ranked_files": [],
            "workflow_artifact_hits": [],
            "suggested_entrypoints": [],
            "allowlist": [],
        }

    entrypoints_set = set(entrypoints or [])
    artifacts = list(workflow_artifacts or [])

    terms = _normalize_terms(_tokenize(prompt))
    intent = _infer_intent(terms)

    raw_scores: dict[str, float] = {}
    reasons_by_file: dict[str, dict[str, list[str]]] = {}

    artifact_scores: list[tuple[float, Mapping]] = []
    if artifacts:
        terms_set = set(terms)
        for a in artifacts:
            a_path = str(a.get("path") or "")
            a_cmds = a.get("commands") or []
            a_signals = set(a.get("signals") or [])

            raw = 0.0
            reasons: dict[str, list[str]] = {}

            ptoks = _path_tokens(a_path)
            path_hits = sorted(t for t in terms_set if t in ptoks)
            if path_hits:
                raw += 1.5 * len(path_hits)
                reasons["path"] = path_hits

            cmd_text = " ".join(str(c) for c in a_cmds[:10])
            cmd_toks = set(_normalize_terms(_tokenize(cmd_text)))
            cmd_hits = sorted(t for t in terms_set if t in cmd_toks)
            if cmd_hits:
                raw += 1.0 * len(cmd_hits)
                reasons["commands"] = cmd_hits

            if intent.wants_deployment and "deployment" in a_signals:
                raw += 2.0
                reasons.setdefault("signals", []).append("deployment")
            if intent.wants_testing and "testing" in a_signals:
                raw += 2.0
                reasons.setdefault("signals", []).append("testing")
            if intent.wants_workflow and ("ci" in a_signals or "build" in a_signals):
                raw += 1.0
                reasons.setdefault("signals", []).append("ci/build")

            role_norm = (role or "").lower()
            if role_norm == "deployment_strategist":
                if "deployment" in a_signals:
                    raw += 1.5
                    reasons.setdefault("role", []).append("deploy_artifact_boost")
                if "ci" in a_signals:
                    raw += 1.0
                    reasons.setdefault("role", []).append("ci_artifact_boost")
            elif role_norm == "fde":
                if a.get("type") == "package_json" or "build" in a_signals:
                    raw += 1.0
                    reasons.setdefault("role", []).append("fde_build_artifact_boost")

            if raw > 0:
                artifact_scores.append(
                    (
                        raw,
                        {
                            "type": a.get("type"),
                            "path": a_path,
                            "signals": sorted(a_signals),
                            "referenced_files": a.get("referenced_files") or [],
                            "raw_score": round(raw, 2),
                            "reasons": reasons,
                        },
                    )
                )

    for rel_path in tutor.metrics.keys():
        raw, reasons = _score_file(
            rel_path=rel_path,
            tutor=tutor,
            terms=terms,
            intent=intent,
            entrypoints=entrypoints_set,
            role=role,
        )
        if raw <= 0.0:
            continue
        raw_scores[rel_path] = raw
        reasons_by_file[rel_path] = reasons

    # If orchestration artifacts match the prompt, seed their referenced files into the scope.
    if artifact_scores:
        artifact_scores.sort(key=lambda kv: (-kv[0], str(kv[1].get("path") or "")))
        for a_raw, a in artifact_scores[:5]:
            for rf in a.get("referenced_files") or []:
                if rf in tutor.metrics:
                    raw_scores[rf] = max(raw_scores.get(rf, 0.0), a_raw * 0.75)
                    reasons_by_file.setdefault(rf, {}).setdefault("workflow_artifact", []).append(str(a.get("path") or ""))

    # Neighborhood expansion (dependencies + dependents) for the strongest seeds.
    if raw_scores and expand_hops > 0:
        adj = tutor.dependency_graph.adj_list
        rev = _reverse_adj(adj)

        seeds = sorted(raw_scores.items(), key=lambda kv: (-kv[1], kv[0]))[:seed_limit]
        for seed_path, seed_score in seeds:
            frontier = {seed_path}
            for hop in range(expand_hops):
                next_frontier: set[str] = set()
                for node in frontier:
                    for dep in adj.get(node, set()):
                        next_frontier.add(dep)
                        raw_scores[dep] = max(raw_scores.get(dep, 0.0), seed_score * 0.25)
                        reasons_by_file.setdefault(dep, {}).setdefault("dependency_of", []).append(seed_path)
                    for parent in rev.get(node, set()):
                        next_frontier.add(parent)
                        raw_scores[parent] = max(raw_scores.get(parent, 0.0), seed_score * 0.20)
                        reasons_by_file.setdefault(parent, {}).setdefault("dependent_of", []).append(seed_path)
                frontier = next_frontier

    # Suggested entrypoints are entrypoints ranked by the same scoring (even if overall scoring is empty).
    suggested_entrypoints: list[dict] = []
    if entrypoints_set:
        scored_eps: list[tuple[str, float]] = []
        for ep in sorted(entrypoints_set):
            raw, _ = _score_file(
                rel_path=ep,
                tutor=tutor,
                terms=terms,
                intent=intent,
                entrypoints=entrypoints_set,
                role=role,
            )
            if raw > 0:
                scored_eps.append((ep, raw))
        scored_eps.sort(key=lambda kv: (-kv[1], kv[0]))
        for ep, score in scored_eps[:3]:
            suggested_entrypoints.append({"file": ep, "raw_score": round(score, 2)})

    max_raw = max(raw_scores.values()) if raw_scores else 0.0

    ranked: list[dict] = []
    if max_raw > 0:
        depths = tutor.dependency_graph.calculate_depths()
        for rel_path, raw in sorted(raw_scores.items(), key=lambda kv: (-kv[1], kv[0])):
            score = tutor.scores.get(rel_path)
            metric = tutor.metrics.get(rel_path)
            ranked.append(
                {
                    "file": rel_path,
                    "relevance": round(raw / max_raw, 3),
                    "raw_score": round(raw, 2),
                    "reasons": reasons_by_file.get(rel_path, {}),
                    "dependency_depth": depths.get(rel_path, 0),
                    "tcs": round(score.total_score, 1) if score else None,
                    "patterns": metric.identified_patterns if metric else [],
                }
            )
            if len(ranked) >= limit:
                break

    allowlist = [r["file"] for r in ranked]

    return {
        "prompt": prompt,
        "terms": terms,
        "intent": intent.__dict__,
        "ranked_files": ranked,
        "workflow_artifact_hits": [a for _, a in artifact_scores[:10]] if artifact_scores else [],
        "suggested_entrypoints": suggested_entrypoints,
        "allowlist": allowlist,
    }
