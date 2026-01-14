from __future__ import annotations

from datetime import datetime
from typing import Any, Mapping


def _md_escape(text: str) -> str:
    return text.replace("`", "\\`")


def render_learning_brief(context: Mapping[str, Any]) -> str:
    """
    Render an LLM-agnostic, portable learning brief from a learning context JSON.

    The brief is designed to be copy-pasted into any LLM (Claude/Codex/Gemini/…)
    while preserving a clear “what to study / why / in what order” contract.
    """
    contract = context.get("contract") or {}
    session_id = context.get("session_id") or ""
    timestamp = context.get("timestamp") or datetime.now().isoformat()
    role = context.get("role") or {}
    prompt = context.get("prompt") or ""

    codebase = context.get("codebase") or {}
    root = codebase.get("root") or ""
    entrypoints = codebase.get("entrypoints") or []
    workflow_artifacts = codebase.get("workflow_artifacts") or []

    prompt_scope = context.get("prompt_scope") or {}
    suggested_entrypoints = prompt_scope.get("suggested_entrypoints") or []
    ranked_files = prompt_scope.get("ranked_files") or []

    workflow = context.get("workflow") or {}
    workflow_path = workflow.get("path") or []

    kb_matches = context.get("kb_matches") or []
    recommendations = context.get("curriculum_recommendations") or []

    lines: list[str] = []
    lines.append("# Learning Brief (Portable)")
    lines.append("")
    lines.append("## Contract")
    lines.append(f"- name: `{_md_escape(str(contract.get('name') or ''))}`")
    lines.append(f"- version: `{_md_escape(str(contract.get('version') or ''))}`")
    lines.append(f"- schema: `{_md_escape(str(contract.get('schema_path') or ''))}`")
    lines.append(f"- spec: `{_md_escape(str(contract.get('spec_path') or ''))}`")
    lines.append("")
    lines.append("## Session")
    lines.append(f"- session_id: `{_md_escape(str(session_id))}`")
    lines.append(f"- timestamp: `{_md_escape(str(timestamp))}`")
    if role:
        lines.append(f"- role.requested: `{_md_escape(str(role.get('requested') or ''))}`")
        lines.append(f"- role.effective: `{_md_escape(str(role.get('effective') or ''))}`")
        if role.get("rationale"):
            lines.append(f"- role.rationale: {_md_escape(str(role.get('rationale')))}")
    lines.append("")
    lines.append("## Codebase")
    lines.append(f"- root: `{_md_escape(str(root))}`")
    if entrypoints:
        lines.append("- detected_entrypoints:")
        for ep in entrypoints[:10]:
            lines.append(f"  - `{_md_escape(str(ep))}`")
    if workflow_artifacts:
        lines.append("- workflow_artifacts:")
        for a in workflow_artifacts[:10]:
            path = a.get("path") or ""
            a_type = a.get("type") or ""
            signals = ", ".join(a.get("signals") or [])
            lines.append(f"  - `{_md_escape(str(path))}` ({_md_escape(str(a_type))}) signals=[{_md_escape(signals)}]")
    lines.append("")
    lines.append("## Prompt")
    lines.append(f"```text\n{prompt}\n```")
    if prompt_scope:
        terms = prompt_scope.get("terms") or []
        intent = prompt_scope.get("intent") or {}
        if terms:
            lines.append("- terms:")
            lines.append("  - " + ", ".join(f"`{_md_escape(str(t))}`" for t in terms[:40]))
        if intent:
            lines.append("- intent:")
            for k in sorted(intent.keys()):
                lines.append(f"  - `{_md_escape(str(k))}`: `{_md_escape(str(intent.get(k)))} `")
    lines.append("")
    lines.append("## Suggested Entrypoints")
    if suggested_entrypoints:
        for ep in suggested_entrypoints[:5]:
            lines.append(f"- `{_md_escape(str(ep.get('file') or ''))}` (raw_score={ep.get('raw_score')})")
    else:
        lines.append("- (none)")
    lines.append("")
    lines.append("## Workflow-First Path (if requested)")
    if workflow_path:
        for step in workflow_path[:30]:
            lines.append(f"- `{_md_escape(str(step.get('file') or ''))}` (tcs={step.get('tcs')}) deps={len(step.get('dependencies') or [])}")
    else:
        lines.append("- (no workflow path generated; run `run_tutor.py --entrypoint <file>` if needed)")
    lines.append("")
    lines.append("## Prompt-Relevant Files (Ranked)")
    if ranked_files:
        for r in ranked_files[:20]:
            reasons = r.get("reasons") or {}
            reason_keys = ", ".join(sorted(reasons.keys()))
            lines.append(f"- `{_md_escape(str(r.get('file') or ''))}` relevance={r.get('relevance')} tcs={r.get('tcs')} reasons=[{_md_escape(reason_keys)}]")
    else:
        lines.append("- (none matched)")
    lines.append("")
    lines.append("## KB Candidates")
    if isinstance(kb_matches, list) and kb_matches:
        for kb in kb_matches[:10]:
            lines.append(f"- `{_md_escape(str(kb.get('path') or ''))}` score={kb.get('score')} title={_md_escape(str(kb.get('title') or ''))}")
    else:
        lines.append("- (none)")
    lines.append("")
    lines.append("## ZPD Recommendations (Difficulty-Aware)")
    if recommendations:
        for rec in recommendations[:10]:
            lines.append(f"- `{_md_escape(str(rec.get('file') or ''))}` tcs={rec.get('tcs')} zpd={rec.get('zpd_score')} reason={_md_escape(str(rec.get('reason') or ''))}")
    else:
        lines.append("- (none)")

    lines.append("")
    lines.append("## Reproduce")
    target = root or "<CODEBASE_ROOT>"
    lines.append(f"- Context JSON: `python scripts/ontology/run_tutor.py --target {target} --user <USER> --db none --prompt \"{_md_escape(prompt)}\"`")
    lines.append("- Workflow-first: `python scripts/ontology/run_tutor.py --target <CODEBASE_ROOT> --user <USER> --db none --entrypoint <RELATIVE_ENTRYPOINT_PATH> --prompt \"<PROMPT>\"`")

    lines.append("")
    return "\n".join(lines)

