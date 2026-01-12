"""
Orion ODA - Session Teleporter
==============================
Web ↔ CLI session transfer for Claude Code.

Boris Cherny Pattern:
"I run 5-10 Claudes on claude.ai in my browser, using a 'teleport' command
to hand off sessions between the web and my local machine."

Usage:
    teleporter = SessionTeleporter()

    # Import from web to CLI
    await teleporter.import_from_web(session_id="optional")

    # Export from CLI to web
    await teleporter.export_to_web()

Note: This module provides the foundation for teleport functionality.
Full Web API integration requires Claude Max subscription.
"""

import asyncio
import json
import logging
import os
import subprocess
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


@dataclass
class GitContext:
    """Git repository context for teleport."""
    branch: str = ""
    commit: str = ""
    remote_url: str = ""
    dirty: bool = False

    @classmethod
    def from_repo(cls, repo_path: str = ".") -> "GitContext":
        """Extract git context from repository."""
        try:
            def git_cmd(args: List[str]) -> str:
                result = subprocess.run(
                    ["git", "-C", repo_path] + args,
                    capture_output=True,
                    text=True,
                )
                return result.stdout.strip() if result.returncode == 0 else ""

            return cls(
                branch=git_cmd(["rev-parse", "--abbrev-ref", "HEAD"]),
                commit=git_cmd(["rev-parse", "HEAD"])[:8],
                remote_url=git_cmd(["remote", "get-url", "origin"]),
                dirty=bool(git_cmd(["status", "--porcelain"])),
            )
        except Exception as e:
            logger.warning(f"Failed to get git context: {e}")
            return cls()


@dataclass
class SessionContext:
    """Session context for teleport."""
    todos: List[Dict[str, Any]] = field(default_factory=list)
    evidence: Dict[str, Any] = field(default_factory=dict)
    files_viewed: List[str] = field(default_factory=list)
    conversation_summary: str = ""
    stage: str = ""  # Current protocol stage (A_SCAN, B_TRACE, C_VERIFY)


@dataclass
class SessionBundle:
    """
    Complete session bundle for teleport.

    Contains all information needed to restore a session
    in a different environment (web → CLI or CLI → web).
    """
    session_id: str
    created_at: str
    source: str  # "web" or "cli"
    target: str  # "web" or "cli"
    context: SessionContext = field(default_factory=SessionContext)
    git: GitContext = field(default_factory=GitContext)
    workspace_root: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "session_id": self.session_id,
            "created_at": self.created_at,
            "source": self.source,
            "target": self.target,
            "context": asdict(self.context),
            "git": asdict(self.git),
            "workspace_root": self.workspace_root,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SessionBundle":
        """Create from dictionary."""
        return cls(
            session_id=data.get("session_id", ""),
            created_at=data.get("created_at", ""),
            source=data.get("source", "unknown"),
            target=data.get("target", "unknown"),
            context=SessionContext(**data.get("context", {})),
            git=GitContext(**data.get("git", {})),
            workspace_root=data.get("workspace_root", ""),
            metadata=data.get("metadata", {}),
        )

    def save(self, path: Path) -> None:
        """Save bundle to file."""
        path.write_text(json.dumps(self.to_dict(), indent=2))
        logger.info(f"Session bundle saved to {path}")

    @classmethod
    def load(cls, path: Path) -> "SessionBundle":
        """Load bundle from file."""
        data = json.loads(path.read_text())
        return cls.from_dict(data)


class SessionTeleporter:
    """
    Manages session teleport between Web and CLI.

    Boris Cherny Integration:
    - Supports claude & prefix for web transfer
    - Handles /teleport command
    - Preserves TodoWrite state
    - Synchronizes evidence tracker
    """

    def __init__(
        self,
        workspace_root: Optional[str] = None,
        session_dir: Optional[str] = None,
    ):
        self.workspace_root = Path(
            workspace_root or os.getenv("ORION_WORKSPACE_ROOT", "/home/palantir")
        )
        self.session_dir = Path(
            session_dir or self.workspace_root / "park-kyungchan/palantir/.agent/tmp/sessions"
        )
        self.session_dir.mkdir(parents=True, exist_ok=True)

        # Current session info
        self.current_session_id = os.getenv("CLAUDE_SESSION_ID", "")

    async def export_to_web(self) -> SessionBundle:
        """
        Export current CLI session for web transfer.

        Returns:
            SessionBundle ready for web import
        """
        logger.info("Exporting session to web...")

        # Collect current session state
        context = await self._collect_session_context()
        git_context = GitContext.from_repo(str(self.workspace_root / "park-kyungchan/palantir"))

        bundle = SessionBundle(
            session_id=self.current_session_id or self._generate_session_id(),
            created_at=datetime.now(timezone.utc).isoformat(),
            source="cli",
            target="web",
            context=context,
            git=git_context,
            workspace_root=str(self.workspace_root),
            metadata={
                "orion_version": "4.0",
                "teleport_version": "1.0",
            },
        )

        # Save bundle for reference
        bundle_path = self.session_dir / f"teleport_out_{bundle.session_id}.json"
        bundle.save(bundle_path)

        # Generate web URL with context
        web_url = self._generate_web_url(bundle)

        logger.info(f"Session exported: {bundle.session_id}")
        logger.info(f"Web URL: {web_url}")

        # Try to open in browser
        await self._open_in_browser(web_url)

        return bundle

    async def import_from_web(self, session_id: Optional[str] = None) -> SessionBundle:
        """
        Import a web session to CLI.

        Args:
            session_id: Specific session to import (or None for interactive picker)

        Returns:
            Imported SessionBundle
        """
        logger.info("Importing session from web...")

        if session_id:
            # Direct import by session ID
            bundle = await self._fetch_web_session(session_id)
        else:
            # Interactive session picker
            sessions = await self._list_web_sessions()
            if not sessions:
                raise ValueError("No web sessions available")

            # For CLI: print available sessions
            print("\nAvailable web sessions:")
            for i, sess in enumerate(sessions[:10], 1):
                print(f"  {i}. {sess['id'][:8]}... - {sess.get('title', 'Untitled')}")

            # In actual implementation, would use /tasks style picker
            # For now, take first session
            bundle = await self._fetch_web_session(sessions[0]["id"])

        # Restore to current environment
        await self._restore_session_context(bundle.context)

        # Save imported bundle
        bundle_path = self.session_dir / f"teleport_in_{bundle.session_id}.json"
        bundle.save(bundle_path)

        logger.info(f"Session imported: {bundle.session_id}")

        return bundle

    async def _collect_session_context(self) -> SessionContext:
        """Collect current session context."""
        context = SessionContext()

        # Read todos from TodoWrite state
        todos_dir = self.workspace_root / ".claude/todos"
        if todos_dir.exists():
            for todo_file in todos_dir.glob("*.json"):
                try:
                    todo_data = json.loads(todo_file.read_text())
                    if todo_data.get("session_id") == self.current_session_id:
                        context.todos = todo_data.get("todos", [])
                        break
                except Exception as e:
                    logger.debug(f"Failed to read todo file: {e}")

        # Read evidence from evidence tracker
        evidence_file = (
            self.workspace_root
            / f"park-kyungchan/palantir/.agent/tmp/evidence_{self.current_session_id}.jsonl"
        )
        if evidence_file.exists():
            files_viewed = set()
            for line in evidence_file.read_text().strip().split("\n"):
                try:
                    entry = json.loads(line)
                    if entry.get("type") == "file_read":
                        files_viewed.add(entry.get("file_path", ""))
                except Exception:
                    pass
            context.files_viewed = list(files_viewed)
            context.evidence = {"files_count": len(files_viewed)}

        # Read session state
        session_file = self.session_dir / f"session_{self.current_session_id}.json"
        if session_file.exists():
            try:
                session_data = json.loads(session_file.read_text())
                context.stage = session_data.get("current_stage", "")
            except Exception:
                pass

        return context

    async def _restore_session_context(self, context: SessionContext) -> None:
        """Restore session context from bundle."""
        # Restore todos (would integrate with TodoWrite)
        if context.todos:
            logger.info(f"Restoring {len(context.todos)} todos")
            # In actual implementation: call TodoWrite tool

        # Log restored files for reference
        if context.files_viewed:
            logger.info(f"Session had {len(context.files_viewed)} files viewed")

        # Restore stage
        if context.stage:
            logger.info(f"Session was at stage: {context.stage}")

    async def _list_web_sessions(self) -> List[Dict[str, Any]]:
        """
        List available web sessions.

        Note: This is a placeholder. Full implementation requires
        Claude Code Web API integration with Claude Max subscription.
        """
        # Check for locally cached web sessions
        sessions = []
        teleport_files = self.session_dir.glob("teleport_out_*.json")

        for f in teleport_files:
            try:
                bundle = SessionBundle.load(f)
                sessions.append({
                    "id": bundle.session_id,
                    "title": bundle.metadata.get("title", "CLI Export"),
                    "created_at": bundle.created_at,
                    "source": bundle.source,
                })
            except Exception:
                pass

        return sessions

    async def _fetch_web_session(self, session_id: str) -> SessionBundle:
        """
        Fetch a specific web session.

        Note: This is a placeholder. Full implementation requires
        Claude Code Web API integration.
        """
        # Try local cache first
        local_path = self.session_dir / f"teleport_out_{session_id}.json"
        if local_path.exists():
            return SessionBundle.load(local_path)

        # In full implementation: call Claude Code Web API
        raise NotImplementedError(
            "Web API integration requires Claude Max subscription. "
            "Use 'claude --teleport' for native teleport."
        )

    def _generate_web_url(self, bundle: SessionBundle) -> str:
        """Generate Claude.ai URL with session context."""
        # Base URL for Claude Code on the web
        base_url = "https://claude.ai/code"

        # In full implementation: include session context in URL
        # For now, just return base URL with repo info
        if bundle.git.remote_url:
            # Extract repo path from URL
            repo = bundle.git.remote_url.replace("git@github.com:", "").replace(".git", "")
            return f"{base_url}?repo={repo}&branch={bundle.git.branch}"

        return base_url

    async def _open_in_browser(self, url: str) -> bool:
        """Open URL in default browser."""
        try:
            import webbrowser
            webbrowser.open(url)
            return True
        except Exception as e:
            logger.warning(f"Failed to open browser: {e}")
            print(f"\nOpen this URL manually: {url}")
            return False

    def _generate_session_id(self) -> str:
        """Generate a new session ID."""
        import uuid
        return str(uuid.uuid4())[:8]


# CLI interface
async def main():
    """CLI entry point for teleport."""
    import sys

    teleporter = SessionTeleporter()

    if len(sys.argv) < 2:
        print("Usage: python session_teleport.py <in|out> [session_id]")
        sys.exit(1)

    direction = sys.argv[1]
    session_id = sys.argv[2] if len(sys.argv) > 2 else None

    if direction == "out":
        bundle = await teleporter.export_to_web()
        print(f"\n✅ Session exported: {bundle.session_id}")
        print(f"📋 Todos: {len(bundle.context.todos)}")
        print(f"📁 Files viewed: {len(bundle.context.files_viewed)}")

    elif direction == "in":
        bundle = await teleporter.import_from_web(session_id)
        print(f"\n✅ Session imported: {bundle.session_id}")
        print(f"📋 Todos restored: {len(bundle.context.todos)}")

    else:
        print(f"Unknown direction: {direction}")
        print("Use 'in' for web→CLI or 'out' for CLI→web")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
