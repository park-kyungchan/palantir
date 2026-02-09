"""Session-based file storage for COW pipeline results."""

import json
from datetime import datetime, timezone
from pathlib import Path

from cow_mcp.models.common import SessionInfo

SESSIONS_DIR = Path.home() / ".cow" / "sessions"


class SessionStorage:
    """Filesystem-based session storage."""

    def __init__(self, base_dir: Path | None = None):
        self.base_dir = base_dir or SESSIONS_DIR
        self.base_dir.mkdir(parents=True, exist_ok=True)

    async def save_result(self, session_id: str, stage: str, data: dict) -> str:
        """Save stage result as JSON. Returns file path."""
        session_dir = self.base_dir / session_id
        session_dir.mkdir(parents=True, exist_ok=True)
        path = session_dir / f"{stage}.json"
        path.write_text(json.dumps(data, ensure_ascii=False, indent=2))
        return str(path)

    async def load_result(self, session_id: str, stage: str) -> dict | None:
        """Load stage result. Returns None if not found."""
        path = self.base_dir / session_id / f"{stage}.json"
        if not path.exists():
            return None
        return json.loads(path.read_text())

    async def list_sessions(self) -> list[dict]:
        """List all sessions with metadata."""
        sessions = []
        if not self.base_dir.exists():
            return sessions
        for session_dir in sorted(self.base_dir.iterdir()):
            if session_dir.is_dir():
                meta_path = session_dir / "metadata.json"
                if meta_path.exists():
                    meta = json.loads(meta_path.read_text())
                    sessions.append(meta)
                else:
                    # Build basic metadata from directory contents
                    stages = [
                        f.stem for f in session_dir.glob("*.json")
                        if f.stem != "metadata"
                    ]
                    sessions.append({
                        "session_id": session_dir.name,
                        "stages": stages,
                        "file_count": len(stages),
                    })
        return sessions

    async def create_session(
        self, session_id: str, source_path: str, source_type: str, page_count: int = 1
    ) -> SessionInfo:
        """Create a new session with metadata."""
        session_dir = self.base_dir / session_id
        session_dir.mkdir(parents=True, exist_ok=True)

        info = SessionInfo(
            session_id=session_id,
            created_at=datetime.now(timezone.utc).isoformat(),
            source_path=source_path,
            source_type=source_type,
            page_count=page_count,
        )

        meta_path = session_dir / "metadata.json"
        meta_path.write_text(info.model_dump_json(indent=2))
        return info
