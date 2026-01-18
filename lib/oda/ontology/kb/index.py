from __future__ import annotations

import json
import re
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

_TOKEN_SPLIT_RE = re.compile(r"[\s/\\._:\-+(){}\[\],;<>|!?\"'`~@#$%^&*=]+")
_KEEP_CHARS_RE = re.compile(r"[^0-9a-zA-Z가-힣]+")
_CODE_FENCE_RE = re.compile(r"(?m)^```(\w+)\s*$")

_LANG_ALIASES = {
    "ts": "typescript",
    "tsx": "typescript",
    "typescript": "typescript",
    "js": "javascript",
    "jsx": "javascript",
    "javascript": "javascript",
    "py": "python",
    "python": "python",
    "go": "go",
    "golang": "go",
    "bash": "bash",
    "sh": "bash",
    "zsh": "bash",
    "yaml": "yaml",
    "yml": "yaml",
    "json": "json",
}


def _tokenize(text: str) -> list[str]:
    cleaned = _KEEP_CHARS_RE.sub(" ", text.lower())
    tokens = [t for t in _TOKEN_SPLIT_RE.split(cleaned) if t]
    # Keep short language tokens.
    out: list[str] = []
    for t in tokens:
        if len(t) < 2 and t not in {"go", "ts", "js"}:
            continue
        out.append(t)
    return out


def _extract_title(md_text: str, fallback: str) -> str:
    for line in md_text.splitlines():
        s = line.strip()
        if s.startswith("# "):
            return s[2:].strip()
    return fallback


def _extract_headings(md_text: str) -> list[str]:
    headings: list[str] = []
    for line in md_text.splitlines():
        s = line.strip()
        if s.startswith("#"):
            headings.append(s.lstrip("#").strip())
    return headings


def _extract_fenced_languages(md_text: str) -> list[str]:
    langs: list[str] = []
    for m in _CODE_FENCE_RE.finditer(md_text):
        raw = m.group(1).lower()
        norm = _LANG_ALIASES.get(raw)
        if norm:
            langs.append(norm)
    # De-dupe preserving order
    seen = set()
    out: list[str] = []
    for l in langs:
        if l in seen:
            continue
        seen.add(l)
        out.append(l)
    return out


@dataclass(frozen=True)
class KBDocument:
    path: str
    title: str
    tokens: list[str]
    languages: list[str]


def build_kb_index(kb_root: Path) -> dict:
    kb_root = kb_root.resolve()
    # Default: store paths relative to the repo root (../.. from coding/knowledge_bases).
    repo_root = kb_root.parent.parent
    docs: list[dict] = []

    for md in sorted(kb_root.glob("*.md")):
        try:
            text = md.read_text(encoding="utf-8")
        except OSError:
            continue

        title = _extract_title(text, fallback=md.stem)
        headings = _extract_headings(text)
        langs = _extract_fenced_languages(text)

        tokens: list[str] = []
        tokens.extend(_tokenize(md.stem))
        tokens.extend(_tokenize(title))
        for h in headings[:50]:
            tokens.extend(_tokenize(h))

        # De-dupe preserving order, cap for size.
        seen = set()
        uniq: list[str] = []
        for t in tokens:
            if t in seen:
                continue
            seen.add(t)
            uniq.append(t)
            if len(uniq) >= 400:
                break

        docs.append(
            KBDocument(
                path=_safe_relpath(md, repo_root),
                title=title,
                tokens=uniq,
                languages=langs,
            ).__dict__
        )

    return {
        "generated_at": datetime.now().isoformat(),
        "kb_root": str(kb_root),
        "documents": docs,
    }


def _safe_relpath(path: Path, base: Path) -> str:
    try:
        return str(path.relative_to(base))
    except ValueError:
        return str(path)


def load_or_build_kb_index(*, kb_root: Path, cache_path: Path) -> dict:
    """
    Loads a cached KB index when fresh; otherwise rebuilds it.
    """
    kb_root = kb_root.resolve()
    cache_path = cache_path.resolve()

    latest_kb_mtime = 0.0
    for md in kb_root.glob("*.md"):
        try:
            latest_kb_mtime = max(latest_kb_mtime, md.stat().st_mtime)
        except OSError:
            continue

    if cache_path.exists():
        try:
            if cache_path.stat().st_mtime >= latest_kb_mtime:
                return json.loads(cache_path.read_text(encoding="utf-8"))
        except Exception:
            # Ignore cache issues and rebuild.
            pass

    index = build_kb_index(kb_root)
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    cache_path.write_text(json.dumps(index, indent=2), encoding="utf-8")
    return index
