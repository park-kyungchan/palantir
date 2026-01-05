#!/usr/bin/env python3
"""
Memory Sync Bridge: Syncs Gemini CLI save_memory facts to Orion Semantic Memory.
Source: ~/.gemini/GEMINI.md (## Gemini Added Memories section)
Target: .agent/memory/gemini_facts.md
"""
import re
from pathlib import Path

GEMINI_MD = Path.home() / ".gemini" / "GEMINI.md"
ORION_MEMORY = Path("/home/palantir/park-kyungchan/palantir/.agent/memory/gemini_facts.md")

def extract_memories(content: str) -> list[str]:
    """Extract facts from ## Gemini Added Memories section."""
    pattern = r"## Gemini Added Memories\n(.*?)(?:\n##|\Z)"
    match = re.search(pattern, content, re.DOTALL)
    if not match:
        return []
    facts = [line.strip("- ").strip() for line in match.group(1).strip().split("\n") if line.strip().startswith("-")]
    return facts

def sync_memories() -> int:
    """Sync memories from GEMINI.md to Orion."""
    if not GEMINI_MD.exists():
        print(f"Source not found: {GEMINI_MD}")
        return 0
    
    content = GEMINI_MD.read_text()
    facts = extract_memories(content)
    
    if not facts:
        print("No memories to sync")
        return 0
    
    # Write to Orion memory
    ORION_MEMORY.parent.mkdir(parents=True, exist_ok=True)
    output = "# Gemini Added Memories (Synced)\n\n" + "\n".join(f"- {fact}" for fact in facts)
    ORION_MEMORY.write_text(output)
    
    print(f"Synced {len(facts)} memories to {ORION_MEMORY}")
    return len(facts)

if __name__ == "__main__":
    sync_memories()
