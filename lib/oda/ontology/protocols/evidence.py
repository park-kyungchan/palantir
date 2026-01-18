"""
Evidence helpers for ODA 3-Stage Protocols.

Protocols should be evidence-driven (anti-hallucination). This module provides
small, deterministic utilities for collecting filesystem-backed evidence that
is compatible with both:
- ODA ProtocolContext (files_viewed / lines_referenced)
- ClaudeProtocolRunner EvidenceTracker (via ODAProtocolAdapter sync)
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Sequence

from lib.oda.ontology.protocols.base import ProtocolContext


@dataclass(frozen=True)
class Snippet:
    file: str
    start_line: int
    end_line: int
    content: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "file": self.file,
            "lines": [self.start_line, self.end_line],
            "content": self.content,
        }


def _safe_read_text(path: Path, max_bytes: int = 200_000) -> str:
    try:
        data = path.read_bytes()
    except Exception:
        return ""
    if len(data) > max_bytes:
        data = data[:max_bytes]
    return data.decode("utf-8", errors="ignore")


def discover_files(
    target_path: str,
    patterns: Sequence[str] = ("**/*.py", "**/*.md"),
    *,
    skip_dirs: Sequence[str] = (
        ".git",
        ".venv",
        ".agent",
        "__pycache__",
        "node_modules",
    ),
    limit: int = 50,
) -> List[Path]:
    base = Path(target_path)
    if not base.exists():
        return []

    if base.is_file():
        return [base]

    files: List[Path] = []
    for pattern in patterns:
        for p in sorted(base.glob(pattern)):
            if not p.is_file():
                continue
            if any(part in skip_dirs for part in p.parts):
                continue
            files.append(p)
            if len(files) >= limit:
                return files
    return files


def add_files_evidence(context: ProtocolContext, files: Iterable[Path]) -> None:
    for p in files:
        context.add_file_evidence(str(p))


def add_line_evidence(
    context: ProtocolContext,
    files: Sequence[Path],
    *,
    min_total_lines: int,
    prefer_prefixes: Sequence[str] = ("import ", "from ", "def ", "class "),
) -> int:
    """
    Add line references across files until at least min_total_lines are collected.

    Returns:
        Total number of line references added (approx).
    """
    added = 0
    for p in files:
        if added >= min_total_lines:
            break

        content = _safe_read_text(p)
        if not content:
            continue

        preferred: List[int] = []
        fallback: List[int] = []
        for i, line in enumerate(content.splitlines(), 1):
            if not line.strip():
                continue
            if any(line.lstrip().startswith(prefix) for prefix in prefer_prefixes):
                preferred.append(i)
            else:
                fallback.append(i)

        # Take preferred lines first, then fallback
        chosen: List[int] = []
        for bucket in (preferred, fallback):
            for ln in bucket:
                if added + len(chosen) >= min_total_lines:
                    break
                chosen.append(ln)
            if added + len(chosen) >= min_total_lines:
                break

        if chosen:
            context.add_file_evidence(str(p), chosen)
            added += len(chosen)

    return added


def collect_snippets(
    files: Sequence[Path],
    *,
    count: int,
    max_lines: int = 30,
) -> List[Snippet]:
    snippets: List[Snippet] = []
    for p in files:
        if len(snippets) >= count:
            break
        content = _safe_read_text(p)
        if not content:
            continue
        lines = content.splitlines()
        if not lines:
            continue
        end = min(max_lines, len(lines))
        snippets.append(
            Snippet(
                file=str(p),
                start_line=1,
                end_line=end,
                content="\n".join(lines[:end]),
            )
        )
    return snippets
