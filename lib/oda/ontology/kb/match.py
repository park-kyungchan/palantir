from __future__ import annotations

from typing import Iterable, Mapping


def _as_set(items: Iterable[str]) -> set[str]:
    return {str(x).lower() for x in items if str(x).strip()}


def _doc_tokens(doc: Mapping) -> set[str]:
    return _as_set(doc.get("tokens", []))


def _doc_languages(doc: Mapping) -> set[str]:
    return _as_set(doc.get("languages", []))


def _intent_terms(prompt_scope: Mapping) -> set[str]:
    intent = prompt_scope.get("intent") or {}
    wants_deployment = bool(intent.get("wants_deployment"))
    wants_testing = bool(intent.get("wants_testing"))
    wants_architecture = bool(intent.get("wants_architecture"))
    extra: set[str] = set()
    if wants_deployment:
        extra.update({"deployment", "deploy", "ci", "cd", "kubernetes", "k8s"})
    if wants_testing:
        extra.update({"testing", "test", "pytest", "jest"})
    if wants_architecture:
        extra.update({"architecture", "design", "ontology"})
    return extra


def match_kbs(
    *,
    prompt_scope: Mapping,
    kb_index: Mapping,
    role: str | None = None,
    limit: int = 6,
) -> list[dict]:
    """
    Rank KB markdown documents relevant to a prompt scope.

    Returns a list of dicts: {path, title, score, matched_terms, languages}.
    """
    terms = _as_set(prompt_scope.get("terms", []))
    terms |= _intent_terms(prompt_scope)

    # Fold in detected patterns from scoped files as additional query terms.
    for r in prompt_scope.get("ranked_files", [])[:12]:
        for p in r.get("patterns", []) or []:
            terms.add(str(p).lower())

    if not terms:
        return []

    intent = prompt_scope.get("intent") or {}
    wants_python = bool(intent.get("wants_python"))
    wants_go = bool(intent.get("wants_go"))
    wants_ts_js = bool(intent.get("wants_ts_js"))
    role_norm = (role or "").lower()

    scored: list[tuple[float, dict]] = []
    for doc in kb_index.get("documents", []):
        dtoks = _doc_tokens(doc)
        if not dtoks:
            continue

        hits = sorted(t for t in terms if t in dtoks)
        score = float(len(hits))

        langs = _doc_languages(doc)
        if wants_python and "python" in langs:
            score += 1.5
        if wants_go and "go" in langs:
            score += 1.5
        if wants_ts_js and (("typescript" in langs) or ("javascript" in langs)):
            score += 1.0

        if role_norm == "deployment_strategist":
            deploy_terms = {
                "deployment",
                "deploy",
                "ci",
                "cd",
                "docker",
                "kubernetes",
                "k8s",
                "helm",
                "terraform",
                "release",
                "observability",
                "monitoring",
                "operations",
                "sre",
            }
            if dtoks.intersection(deploy_terms):
                score += 1.0
        elif role_norm == "fde":
            fde_terms = {
                "react",
                "typescript",
                "javascript",
                "frontend",
                "ui",
                "graphql",
                "websocket",
                "blueprint",
                "osdk",
                "testing",
                "webpack",
                "vite",
            }
            score += min(len(dtoks.intersection(fde_terms)), 3) * 0.4

        if score <= 0:
            continue

        scored.append(
            (
                score,
                {
                    "path": doc.get("path"),
                    "title": doc.get("title"),
                    "score": round(score, 2),
                    "matched_terms": hits[:20],
                    "languages": sorted(langs),
                },
            )
        )

    scored.sort(key=lambda kv: (-kv[0], str(kv[1].get("path") or "")))
    return [d for _, d in scored[:limit]]
