#!/usr/bin/env python3
"""
Memory Sync Bridge: Syncs system prompt save_memory facts to Orion Semantic Memory.
Source: ORION_SYSTEM_PROMPT (defaults to ~/.gemini/GEMINI.md)
Target: .agent/memory/system_facts.md
"""
import re
import os
from pathlib import Path

WORKSPACE_ROOT = Path(os.environ.get("ORION_WORKSPACE_ROOT", "/home/palantir"))
SYSTEM_PROMPT = Path(os.environ.get("ORION_SYSTEM_PROMPT", WORKSPACE_ROOT / ".gemini" / "GEMINI.md"))
ORION_MEMORY = Path("/home/palantir/park-kyungchan/palantir/.agent/memory/system_facts.md")

def extract_memories(content: str) -> list[str]:
    """Extract facts from ## Added Memories section."""
    pattern = r"## (?:Gemini )?Added Memories\n(.*?)(?:\n##|\Z)"
    match = re.search(pattern, content, re.DOTALL)
    if not match:
        return []
    facts = [line.strip("- ").strip() for line in match.group(1).strip().split("\n") if line.strip().startswith("-")]
    return facts

def sync_memories() -> int:
    """Sync memories from the active system prompt to Orion."""
    if not SYSTEM_PROMPT.exists():
        print(f"Source not found: {SYSTEM_PROMPT}")
        return 0
    
    content = SYSTEM_PROMPT.read_text()
    facts = extract_memories(content)
    
    if not facts:
        print("No memories to sync")
        return 0
    
    # Write to Orion memory
    ORION_MEMORY.parent.mkdir(parents=True, exist_ok=True)
    output = "# Added Memories (Synced)\n\n" + "\n".join(f"- {fact}" for fact in facts)
    ORION_MEMORY.write_text(output)
    
    print(f"Synced {len(facts)} memories to {ORION_MEMORY}")
    return len(facts)

if __name__ == "__main__":
    sync_memories()
