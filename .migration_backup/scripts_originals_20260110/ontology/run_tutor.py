#!/usr/bin/env python3
"""
Orion V3.5 Learning Engine Entry Point (Phase 5)
Usage: python scripts/ontology/run_tutor.py --target <path> --user <id>

This script triggers the Adaptive Tutoring Engine.
It performs:
1. Initialization of the Cognitive Engine
2. Loading of Learner State (OSDK)
3. ZPD-based Curriculum Scoping

The output is a 'Learning Context' JSON consumed by the AI Agent.
"""

import argparse
import asyncio
import json
import socket
import sys
from pathlib import Path
from datetime import datetime
from typing import Set

# Ensure project root is on sys.path (running via file path sets sys.path[0] to this script's folder)
_PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

# Phase 5 Imports
from lib.oda.cognitive.engine import AdaptiveTutoringEngine
from lib.oda.ontology.storage.database import initialize_database

_JS_TS_EXTENSIONS = {".js", ".jsx", ".ts", ".tsx", ".mjs", ".cjs", ".mts", ".cts"}

def _filter_recommendations_for_prompt(recommendations: list[dict], allowlist: set[str], limit: int) -> list[dict]:
    if not allowlist:
        return recommendations[:limit]
    chosen: list[dict] = []
    seen: set[str] = set()
    for rec in recommendations:
        p = rec.get("file")
        if not p or p in seen:
            continue
        if p in allowlist:
            chosen.append(rec)
            seen.add(p)
        if len(chosen) >= limit:
            return chosen
    for rec in recommendations:
        p = rec.get("file")
        if not p or p in seen:
            continue
        chosen.append(rec)
        seen.add(p)
        if len(chosen) >= limit:
            break
    return chosen

def _infer_effective_role(requested: str, prompt_scope: dict | None) -> tuple[str, str | None]:
    requested_norm = (requested or "").strip().lower()
    if requested_norm and requested_norm != "auto":
        return requested_norm, "explicit"

    if not prompt_scope:
        return "general", None

    intent = prompt_scope.get("intent") or {}
    if bool(intent.get("wants_deployment")):
        return "deployment_strategist", "intent.wants_deployment=True"
    if bool(intent.get("wants_ts_js")) and not (bool(intent.get("wants_go")) or bool(intent.get("wants_python"))):
        return "fde", "intent.wants_ts_js=True"
    if bool(intent.get("wants_ts_js")) and bool(intent.get("wants_architecture")):
        return "fde", "intent.wants_architecture+ts_js=True"
    return "general", "default"

def _supports_threadsafe_wakeup() -> bool:
    """
    Returns True if asyncio's thread-safe wakeup mechanism works in this runtime.

    Some sandboxed environments block socket sends, which breaks asyncio's internal self-pipe
    (and anything that relies on it, like aiosqlite / async SQLAlchemy).
    """
    a = b = None
    try:
        a, b = socket.socketpair()
        a.send(b"\0")
        return True
    except OSError:
        return False
    finally:
        for s in (a, b):
            try:
                if s is not None:
                    s.close()
            except OSError:
                pass


def _is_entrypoint(rel_path: str, content: str) -> bool:
    ext = Path(rel_path).suffix.lower()

    if ext == ".py":
        return 'if __name__ == "__main__"' in content or 'if __name__ == "__main__":' in content

    if ext in _JS_TS_EXTENSIONS:
        first_line = content.splitlines()[0] if content else ""
        if first_line.startswith("#!") and "node" in first_line:
            return True
        if "process.argv" in content or "Deno.args" in content:
            return True
        if "createRoot(" in content or "ReactDOM.render(" in content:
            return True
        return False

    if ext == ".go":
        return ("package main" in content) and ("func main(" in content)

    return False


def _normalize_entrypoint_arg(entrypoint: str, root: Path) -> str:
    p = Path(entrypoint)
    if p.is_absolute():
        try:
            return str(p.resolve().relative_to(root))
        except ValueError:
            return entrypoint
    # Treat as relative to root first, then to CWD
    as_root_rel = (root / p).resolve()
    try:
        return str(as_root_rel.relative_to(root))
    except ValueError:
        return entrypoint


def _build_workflow_path(entrypoint_rel: str, tutor) -> dict:
    depths = tutor.dependency_graph.calculate_depths()
    visited: Set[str] = set()

    def dfs(node: str) -> None:
        if node in visited:
            return
        visited.add(node)
        for dep in tutor.dependency_graph.adj_list.get(node, set()):
            dfs(dep)

    dfs(entrypoint_rel)

    def sort_key(path: str) -> tuple:
        score = tutor.scores.get(path)
        tcs = score.total_score if score else 0.0
        return (depths.get(path, 0), tcs, path)

    ordered = sorted(visited, key=sort_key)
    if entrypoint_rel in ordered:
        ordered.remove(entrypoint_rel)
        ordered.append(entrypoint_rel)

    path_details = []
    for p in ordered:
        score = tutor.scores.get(p)
        metric = tutor.metrics.get(p)
        deps = sorted(tutor.dependency_graph.adj_list.get(p, set()))
        path_details.append({
            "file": p,
            "tcs": round(score.total_score, 1) if score else None,
            "tcs_breakdown": score.model_dump() if score else None,
            "metrics": metric.model_dump(exclude={"imports"}) if metric else None,
            "dependencies": deps,
        })

    return {"entrypoint": entrypoint_rel, "path": path_details}


async def run_session_generation(
    target_path: str,
    user_id: str,
    db_mode: str,
    limit: int,
    theta: float,
    role: str,
    entrypoint: str | None,
    prompt: str | None,
    prompt_limit: int,
    brief: bool,
    brief_path: str | None,
):
    print(f"🚀 Initializing Orion Adaptive Tutor (Phase 5) for user: {user_id}")
    
    effective_db_mode = db_mode
    if effective_db_mode != "none" and not _supports_threadsafe_wakeup():
        print("⚠️  Async DB disabled (thread-safe wakeup not permitted). Running without persistence.")
        effective_db_mode = "none"

    if effective_db_mode == "oda":
        # 0. Initialize DB (Required for OSDK-backed learner persistence)
        await initialize_database()

        # 1. Initialize Engine
        engine = AdaptiveTutoringEngine(target_path)

        # 2. Start Session (Load State + Scope)
        print("   • Scanning Codebase & Loading Learner State...")
        session_data = await engine.initialize_session(user_id)
        recommendations = session_data["recommendations"]
        learner = session_data["learner"]
        tutor = engine.core_engine
    else:
        # No DB / no persistence: static scoping over the target codebase.
        from lib.oda.ontology.learning.engine import TutoringEngine
        from lib.oda.ontology.learning.scoping import ScopingEngine
        from lib.oda.ontology.learning.types import LearnerState

        print("   • Scanning Codebase (no persistence)...")
        tutor = TutoringEngine(target_path)
        tutor.scan_codebase()
        tutor.calculate_scores()

        learner_state = LearnerState(user_id=user_id, theta=theta)
        scoper = ScopingEngine(tutor)
        recommendations = scoper.recommend_next_files(learner_state, limit=limit)
        learner = learner_state.model_dump()

    # Lightweight entrypoint detection for workflow-oriented study.
    entrypoints = []
    for rel_path in tutor.metrics.keys():
        full_path = tutor.root / rel_path
        try:
            content = full_path.read_text(encoding="utf-8")
        except OSError:
            continue
        if _is_entrypoint(rel_path, content):
            entrypoints.append(rel_path)
    entrypoints.sort()

    # Orchestration files (CI/build/deploy) for cross-language workflow tracing.
    try:
        from lib.oda.ontology.learning.workflow_artifacts import scan_workflow_artifacts

        workflow_artifacts = scan_workflow_artifacts(tutor.root)
    except Exception:
        workflow_artifacts = []

    prompt_scope = None
    kb_matches = None
    allowlist: set[str] = set()
    requested_role_norm = (role or "auto").strip().lower()
    effective_role_default, rationale_default = _infer_effective_role(requested_role_norm, None)
    role_info = {"requested": requested_role_norm, "effective": effective_role_default, "rationale": rationale_default}
    if prompt:
        from lib.oda.ontology.learning.prompt_scope import build_prompt_scope

        role_for_scoring = requested_role_norm if requested_role_norm != "auto" else None

        prompt_scope = build_prompt_scope(
            prompt=prompt,
            tutor=tutor,
            entrypoints=entrypoints,
            workflow_artifacts=workflow_artifacts,
            role=role_for_scoring,
            limit=max(prompt_limit, 1),
        )
        effective_role, rationale = _infer_effective_role(requested_role_norm, prompt_scope)
        role_info = {"requested": requested_role_norm, "effective": effective_role, "rationale": rationale}

        # If role is auto, rebuild prompt scope with the inferred effective role to stabilize weighting.
        if requested_role_norm == "auto" and effective_role != role_for_scoring:
            prompt_scope = build_prompt_scope(
                prompt=prompt,
                tutor=tutor,
                entrypoints=entrypoints,
                workflow_artifacts=workflow_artifacts,
                role=effective_role,
                limit=max(prompt_limit, 1),
            )
        allowlist = set(prompt_scope.get("allowlist", []))

        # If we can re-scope locally (no-db mode), prefer prompt-scoped recommendations.
        if effective_db_mode != "oda":
            from lib.oda.ontology.learning.scoping import ScopingEngine
            from lib.oda.ontology.learning.types import LearnerState

            learner_state = LearnerState(user_id=user_id, theta=learner.get("theta", theta))
            scoper = ScopingEngine(tutor)
            prompt_recs = scoper.recommend_next_files(learner_state, limit=limit, allowlist=allowlist or None)
            if prompt_recs:
                recommendations = prompt_recs
        else:
            recommendations = _filter_recommendations_for_prompt(recommendations, allowlist, limit)

        # Map the prompt scope to relevant KB documents (offline index + matcher).
        try:
            from lib.oda.ontology.kb import load_or_build_kb_index, match_kbs

            kb_index = load_or_build_kb_index(
                kb_root=Path("coding/knowledge_bases"),
                cache_path=Path(".agent/kb_index.json"),
            )
            kb_matches = match_kbs(prompt_scope=prompt_scope, kb_index=kb_index, role=role_info["effective"], limit=6)
        except Exception as e:
            kb_matches = {"error": str(e)}

    # Enrich recommendations with metrics/breakdowns for explainability.
    enriched_recommendations = []
    for rec in recommendations:
        file_path = rec["file"]
        score = tutor.scores.get(file_path)
        metric = tutor.metrics.get(file_path)
        deps = sorted(tutor.dependency_graph.adj_list.get(file_path, set()))

        enriched_recommendations.append({
            **rec,
            "tcs_breakdown": score.model_dump() if score else None,
            "metrics": metric.model_dump(exclude={"imports"}) if metric else None,
            "dependencies": deps,
        })

    entrypoint_details = []
    for ep in entrypoints:
        score = tutor.scores.get(ep)
        metric = tutor.metrics.get(ep)
        deps = sorted(tutor.dependency_graph.adj_list.get(ep, set()))
        entrypoint_details.append({
            "file": ep,
            "tcs": round(score.total_score, 1) if score else None,
            "tcs_breakdown": score.model_dump() if score else None,
            "metrics": metric.model_dump(exclude={"imports"}) if metric else None,
            "dependencies": deps,
        })

    # Optional: entrypoint-driven workflow path for "start from the entrypoint" learning.
    workflow = None
    if entrypoint:
        entrypoint_rel = _normalize_entrypoint_arg(entrypoint, tutor.root)
        if entrypoint_rel in tutor.metrics:
            workflow = _build_workflow_path(entrypoint_rel, tutor)
        else:
            workflow = {"entrypoint": entrypoint_rel, "error": "Entry point not found in scanned files"}

    extension_counts: dict[str, int] = {}
    for rel_path in tutor.metrics.keys():
        ext = Path(rel_path).suffix.lower() or "<noext>"
        extension_counts[ext] = extension_counts.get(ext, 0) + 1
    
    # 3. Construct Context Payload
    output_dir = Path(".agent/learning")
    output_dir.mkdir(parents=True, exist_ok=True)
    session_id = datetime.now().strftime("learn_%Y%m%d_%H%M%S")
    output_file = output_dir / f"{session_id}.json"
    output_brief = None
    if brief:
        if brief_path:
            output_brief = Path(brief_path)
        else:
            output_brief = output_dir / f"{session_id}_brief.md"
    
    context = {
        "contract": {
            "name": "orion_learning_context",
            "version": "1.0",
            "schema_path": "scripts/ontology/schemas/learning_context_v1.schema.json",
            "spec_path": "coding/LLM_CONTRACT.md",
        },
        "session_id": session_id,
        "user_id": user_id,
        "timestamp": datetime.now().isoformat(),
        "db_mode": effective_db_mode,
        "role": role_info,
        "prompt": prompt,
        "prompt_scope": prompt_scope,
        "kb_matches": kb_matches,
        "codebase": {
            "root": str(Path(target_path).resolve()),
            "files_scanned": len(tutor.metrics),
            "extension_counts": dict(sorted(extension_counts.items(), key=lambda x: (-x[1], x[0]))),
            "entrypoints": entrypoints,
            "entrypoint_details": entrypoint_details,
            "workflow_artifacts": workflow_artifacts,
        },
        "learner_stats": {
            "theta": learner["theta"],
            # "mastered_concepts": len(learner["knowledge_components"]) # dict
        },
        "curriculum_recommendations": enriched_recommendations,
        "workflow": workflow,
        "outputs": {
            "context_json": str(output_file),
            "learning_brief_md": str(output_brief) if output_brief else None,
        },
        "instruction": (
            "Agent: Use the 'curriculum_recommendations' to guide the user. "
            "For each recommended file, use 'tcs_breakdown', 'metrics', and 'dependencies' to explain WHY it was chosen. "
            "If the user asks about workflow/entrypoints, start from 'codebase.entrypoints' and trace dependencies. "
            "If 'workflow' is present, use workflow.path as the entrypoint-first learning sequence."
        )
    }

    if output_brief:
        from lib.oda.ontology.learning.brief import render_learning_brief

        try:
            output_brief.parent.mkdir(parents=True, exist_ok=True)
            output_brief.write_text(render_learning_brief(context), encoding="utf-8")
        except Exception as e:
            # Don't fail the whole run for brief generation; mark it as unavailable.
            context["outputs"]["learning_brief_md"] = None

    with open(output_file, "w") as f:
        json.dump(context, f, indent=2)
        
    print(f"\n✅ Learning Session Context Generated: {output_file}")
    print(f"==================================================")
    if recommendations:
        top = recommendations[0]
        print(f"📚 Top Recommendation: {top['file']}")
        print(f"   - Score: {top['tcs']} (ZPD: {top['zpd_score']})")
    else:
        print("📚 No suitable lessons found in ZPD.")
    print(f"🧠 Learner Theta: {learner['theta']}")
    print(f"==================================================")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Orion Adaptive Tutor")
    parser.add_argument("--target", required=True, help="Path to codebase")
    parser.add_argument("--user", default="default_user", help="User ID")
    parser.add_argument(
        "--db",
        default="oda",
        choices=["oda", "none"],
        help="Persistence mode (default: oda). Use 'none' in restricted environments.",
    )
    parser.add_argument("--limit", type=int, default=3, help="Max recommendations (default: 3)")
    parser.add_argument("--theta", type=float, default=0.0, help="Initial learner theta (no-db mode only)")
    parser.add_argument(
        "--entrypoint",
        default=None,
        help="Optional entrypoint file (relative to target root) to generate a workflow-first learning path",
    )
    parser.add_argument(
        "--role",
        default="auto",
        choices=["auto", "fde", "deployment_strategist"],
        help="Role lens for scoping (default: auto)",
    )
    parser.add_argument(
        "--prompt",
        default=None,
        help="Optional user prompt to scope recommendations to relevant code artifacts (agile prompt-driven mode)",
    )
    parser.add_argument(
        "--prompt-limit",
        type=int,
        default=12,
        help="Max files to include in prompt_scope (default: 12)",
    )
    parser.add_argument(
        "--brief",
        action="store_true",
        help="Generate a portable markdown learning brief alongside the context JSON",
    )
    parser.add_argument(
        "--brief-path",
        default=None,
        help="Optional output path for the learning brief markdown (default: .agent/learning/<session>_brief.md)",
    )
    
    args = parser.parse_args()
    
    try:
        asyncio.run(
            run_session_generation(
                args.target,
                args.user,
                args.db,
                args.limit,
                args.theta,
                args.role,
                args.entrypoint,
                args.prompt,
                args.prompt_limit,
                args.brief,
                args.brief_path,
            )
        )
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
