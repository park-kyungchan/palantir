"""
Evidence Tracker for Anti-Hallucination Compliance

Tracks file reads, line references, and code snippets during analysis
to ensure all claims are backed by verifiable evidence.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Set


@dataclass
class FileEvidence:
    """Evidence from a file read operation."""
    path: str
    timestamp: str
    lines_read: Optional[List[int]] = None
    purpose: Optional[str] = None


@dataclass
class LineReference:
    """Reference to a specific line in a file."""
    line: int
    content: str
    claim: Optional[str] = None


@dataclass
class CodeSnippet:
    """Captured code snippet for evidence."""
    id: str
    file: str
    start_line: int
    end_line: int
    content: str
    relevance: Optional[str] = None


@dataclass
class EvidenceContext:
    """
    Container for all evidence collected during an operation.

    Maps to ODA ProtocolContext.evidence structure.
    """
    session_id: str
    actor_id: str = "claude_code_agent"
    started_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())

    files_viewed: List[FileEvidence] = field(default_factory=list)
    lines_referenced: Dict[str, List[LineReference]] = field(default_factory=dict)
    code_snippets: List[CodeSnippet] = field(default_factory=list)

    # Quick lookup sets
    _file_paths: Set[str] = field(default_factory=set)
    _snippet_counter: int = field(default=0)

    def to_dict(self) -> Dict[str, Any]:
        """Export evidence to dictionary (compatible with StageResult.evidence)."""
        return {
            "files_viewed": [f.path for f in self.files_viewed],
            "lines_referenced": {
                path: [ref.line for ref in refs]
                for path, refs in self.lines_referenced.items()
            },
            "code_snippets": [
                {
                    "id": s.id,
                    "file": s.file,
                    "lines": [s.start_line, s.end_line],
                    "content": s.content,
                }
                for s in self.code_snippets
            ],
            "session_id": self.session_id,
            "actor_id": self.actor_id,
            "timestamp": self.started_at,
        }

    def to_json(self) -> str:
        """Export evidence as JSON string."""
        return json.dumps(self.to_dict(), indent=2)


class EvidenceTracker:
    """
    Tracks evidence for anti-hallucination compliance.

    Usage:
        tracker = EvidenceTracker(session_id="abc123")

        # Track file read
        tracker.track_file_read("scripts/ontology/registry.py")

        # Track line reference
        tracker.track_line_reference(
            "scripts/ontology/registry.py",
            line=41,
            content="class OntologyRegistry:",
            claim="Registry is a class"
        )

        # Capture snippet
        tracker.capture_snippet(
            "scripts/ontology/registry.py",
            start_line=41,
            end_line=55,
            content="class OntologyRegistry:...",
            relevance="Shows registry initialization"
        )

        # Validate evidence
        tracker.validate(stage="B_TRACE")

        # Export
        evidence = tracker.get_evidence()
    """

    def __init__(
        self,
        session_id: str,
        actor_id: str = "claude_code_agent",
        storage_path: Optional[Path] = None,
    ):
        self.context = EvidenceContext(
            session_id=session_id,
            actor_id=actor_id,
        )
        self.storage_path = storage_path or Path(".agent/tmp")

    def track_file_read(
        self,
        file_path: str,
        lines: Optional[List[int]] = None,
        purpose: Optional[str] = None,
    ) -> None:
        """
        Track a file read operation.

        Args:
            file_path: Path to the file that was read
            lines: Optional line range [start, end]
            purpose: Optional description of why file was read
        """
        # Normalize path
        normalized = str(Path(file_path).resolve())

        # Avoid duplicates
        if normalized in self.context._file_paths:
            return

        self.context._file_paths.add(normalized)
        self.context.files_viewed.append(FileEvidence(
            path=normalized,
            timestamp=datetime.utcnow().isoformat(),
            lines_read=lines,
            purpose=purpose,
        ))

    def track_line_reference(
        self,
        file_path: str,
        line: int,
        content: str,
        claim: Optional[str] = None,
    ) -> None:
        """
        Track a reference to a specific line.

        Args:
            file_path: Path to the file
            line: Line number (1-indexed)
            content: Content of the line
            claim: Optional claim this line supports
        """
        normalized = str(Path(file_path).resolve())

        if normalized not in self.context.lines_referenced:
            self.context.lines_referenced[normalized] = []

        self.context.lines_referenced[normalized].append(LineReference(
            line=line,
            content=content.strip(),
            claim=claim,
        ))

        # Also track file if not already tracked
        self.track_file_read(normalized)

    def capture_snippet(
        self,
        file_path: str,
        start_line: int,
        end_line: int,
        content: str,
        relevance: Optional[str] = None,
    ) -> str:
        """
        Capture a code snippet for evidence.

        Args:
            file_path: Path to the file
            start_line: Start line number
            end_line: End line number
            content: Snippet content
            relevance: Why this snippet is relevant

        Returns:
            Snippet ID
        """
        self.context._snippet_counter += 1
        snippet_id = f"snippet_{self.context._snippet_counter:03d}"

        normalized = str(Path(file_path).resolve())

        self.context.code_snippets.append(CodeSnippet(
            id=snippet_id,
            file=normalized,
            start_line=start_line,
            end_line=end_line,
            content=content,
            relevance=relevance,
        ))

        # Track file and lines
        self.track_file_read(normalized, lines=[start_line, end_line])
        for line_num in range(start_line, end_line + 1):
            # Only add first and last lines to avoid bloat
            if line_num in (start_line, end_line):
                lines = content.split('\n')
                idx = line_num - start_line
                if 0 <= idx < len(lines):
                    self.track_line_reference(
                        normalized,
                        line_num,
                        lines[idx],
                    )

        return snippet_id

    def validate(
        self,
        stage: str = "A_SCAN",
        strict: bool = False,
    ) -> Dict[str, Any]:
        """
        Validate evidence meets requirements for the stage.

        Args:
            stage: Protocol stage (A_SCAN, B_TRACE, C_VERIFY)
            strict: Raise exception on failure

        Returns:
            Validation result
        """
        result = {
            "valid": True,
            "stage": stage,
            "checks": [],
            "errors": [],
        }

        # Stage A: Minimum file requirements
        files_count = len(self.context.files_viewed)
        min_files = {"A_SCAN": 1, "B_TRACE": 3, "C_VERIFY": 5}.get(stage, 1)

        if files_count >= min_files:
            result["checks"].append({
                "name": "minimum_files",
                "status": "PASS",
                "details": f"{files_count} files viewed (min: {min_files})",
            })
        else:
            result["valid"] = False
            result["checks"].append({
                "name": "minimum_files",
                "status": "FAIL",
                "details": f"{files_count} files viewed (min: {min_files})",
            })
            result["errors"].append(
                f"Insufficient files: {files_count} < {min_files}"
            )

        # Stage B+: Line references required
        if stage in ("B_TRACE", "C_VERIFY"):
            refs_count = sum(
                len(refs) for refs in self.context.lines_referenced.values()
            )
            min_refs = {"B_TRACE": 5, "C_VERIFY": 10}.get(stage, 5)

            if refs_count >= min_refs:
                result["checks"].append({
                    "name": "line_references",
                    "status": "PASS",
                    "details": f"{refs_count} line references (min: {min_refs})",
                })
            else:
                result["valid"] = False
                result["checks"].append({
                    "name": "line_references",
                    "status": "FAIL",
                    "details": f"{refs_count} line references (min: {min_refs})",
                })
                result["errors"].append(
                    f"Insufficient line references: {refs_count} < {min_refs}"
                )

        # Stage C: Code snippets required
        if stage == "C_VERIFY":
            snippets_count = len(self.context.code_snippets)
            min_snippets = 2

            if snippets_count >= min_snippets:
                result["checks"].append({
                    "name": "code_snippets",
                    "status": "PASS",
                    "details": f"{snippets_count} snippets (min: {min_snippets})",
                })
            else:
                result["valid"] = False
                result["checks"].append({
                    "name": "code_snippets",
                    "status": "FAIL",
                    "details": f"{snippets_count} snippets (min: {min_snippets})",
                })
                result["errors"].append(
                    f"Insufficient snippets: {snippets_count} < {min_snippets}"
                )

        if strict and not result["valid"]:
            raise AntiHallucinationError(
                stage=stage,
                errors=result["errors"],
            )

        return result

    def get_evidence(self) -> EvidenceContext:
        """Get the evidence context."""
        return self.context

    def export(self) -> Dict[str, Any]:
        """Export evidence as dictionary."""
        return self.context.to_dict()

    def save(self, filename: Optional[str] = None) -> Path:
        """
        Save evidence to file.

        Args:
            filename: Optional filename (default: evidence_{session_id}.json)

        Returns:
            Path to saved file
        """
        if filename is None:
            filename = f"evidence_{self.context.session_id}.json"

        self.storage_path.mkdir(parents=True, exist_ok=True)
        path = self.storage_path / filename

        path.write_text(self.context.to_json())
        return path

    @classmethod
    def load(cls, path: Path) -> "EvidenceTracker":
        """Load evidence tracker from file."""
        data = json.loads(path.read_text())

        tracker = cls(
            session_id=data.get("session_id", "unknown"),
            actor_id=data.get("actor_id", "unknown"),
        )

        # Restore files
        for file_path in data.get("files_viewed", []):
            tracker.track_file_read(file_path)

        # Restore line references
        for file_path, lines in data.get("lines_referenced", {}).items():
            for line in lines:
                tracker.track_line_reference(file_path, line, "")

        return tracker


class AntiHallucinationError(Exception):
    """Raised when evidence requirements are not met."""

    def __init__(self, stage: str, errors: List[str]):
        self.stage = stage
        self.errors = errors
        super().__init__(
            f"Anti-hallucination check failed for stage {stage}: {'; '.join(errors)}"
        )


# CLI interface for hook integration
if __name__ == "__main__":
    import sys

    def main():
        if len(sys.argv) < 2:
            print("Usage: python evidence_tracker.py <command> [args]")
            print("Commands: track, validate, export")
            sys.exit(1)

        command = sys.argv[1]
        session_id = sys.argv[2] if len(sys.argv) > 2 else "cli_session"

        tracker = EvidenceTracker(session_id=session_id)

        if command == "track":
            # Read file path from stdin or arg
            file_path = sys.argv[3] if len(sys.argv) > 3 else sys.stdin.readline().strip()
            tracker.track_file_read(file_path)
            print(json.dumps({"tracked": file_path}))

        elif command == "validate":
            stage = sys.argv[3] if len(sys.argv) > 3 else "A_SCAN"
            result = tracker.validate(stage=stage)
            print(json.dumps(result))

        elif command == "export":
            print(tracker.context.to_json())

    main()
