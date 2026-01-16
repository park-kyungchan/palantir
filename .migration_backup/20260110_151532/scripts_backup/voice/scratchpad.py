"""
Orion ODA V3 - Scratchpad
========================
File-based shared memory between Human and Agent.

Maps to IndyDevDan's scratchpad.md pattern from ADA architecture.
"""

import logging
from datetime import datetime
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


class Scratchpad:
    """
    File-based shared memory between Human and Agent.
    
    Maps to IndyDevDan's scratchpad.md pattern.
    
    The scratchpad maintains conversation context and state
    in a human-readable markdown file.
    
    Usage:
        sp = Scratchpad("./scratchpad.md")
        sp.append_user_intent("Create a new task")
        sp.append_agent_status("Processing", "Analyzing request...")
        context = sp.get_recent_context(50)
    """
    
    def __init__(self, path: str = "./scratchpad.md"):
        self.path = Path(path)
        self._ensure_exists()
    
    def _ensure_exists(self) -> None:
        """Ensure scratchpad file exists."""
        if not self.path.exists():
            self.path.parent.mkdir(parents=True, exist_ok=True)
            self.path.write_text(self._initial_content())
            logger.info(f"Created scratchpad at {self.path}")
    
    def _initial_content(self) -> str:
        """Generate initial scratchpad content."""
        return f"""# Scratchpad

> Shared memory between Human and Agent
> Created: {datetime.now().isoformat()}

---

## Session Log

"""

    def read(self) -> str:
        """Read entire scratchpad content."""
        return self.path.read_text() if self.path.exists() else ""
    
    def append_user_intent(self, intent: str) -> None:
        """
        Append user intent to scratchpad.
        
        Args:
            intent: What the user wants to do
        """
        timestamp = datetime.now().strftime("%H:%M:%S")
        entry = f"\n### 🎯 User Intent [{timestamp}]\n\n{intent}\n"
        
        with self.path.open("a") as f:
            f.write(entry)
        
        logger.debug(f"Appended user intent: {intent[:50]}...")
    
    def append_agent_status(self, status: str, details: str = "") -> None:
        """
        Append agent status update.
        
        Args:
            status: Brief status message
            details: Optional detailed explanation
        """
        timestamp = datetime.now().strftime("%H:%M:%S")
        entry = f"\n### 🤖 Agent Status [{timestamp}]\n\n**{status}**\n"
        
        if details:
            entry += f"\n{details}\n"
        
        with self.path.open("a") as f:
            f.write(entry)
    
    def append_action_result(
        self, 
        action: str, 
        success: bool, 
        result: Optional[str] = None
    ) -> None:
        """
        Append action execution result.
        
        Args:
            action: Action that was executed
            success: Whether it succeeded
            result: Optional result details
        """
        timestamp = datetime.now().strftime("%H:%M:%S")
        status_emoji = "✅" if success else "❌"
        
        entry = f"\n### {status_emoji} Action [{timestamp}]\n\n"
        entry += f"**Action**: `{action}`\n"
        entry += f"**Result**: {'Success' if success else 'Failed'}\n"
        
        if result:
            entry += f"\n```\n{result}\n```\n"
        
        with self.path.open("a") as f:
            f.write(entry)
    
    def append_thinking(self, thought: str) -> None:
        """
        Append agent thinking process.
        
        Args:
            thought: What the agent is thinking
        """
        timestamp = datetime.now().strftime("%H:%M:%S")
        entry = f"\n### 💭 Thinking [{timestamp}]\n\n> {thought}\n"
        
        with self.path.open("a") as f:
            f.write(entry)
    
    def clear(self) -> None:
        """Clear scratchpad and reinitialize."""
        self.path.write_text(self._initial_content())
        logger.info("Scratchpad cleared")
    
    def get_recent_context(self, lines: int = 50) -> str:
        """
        Get recent context for LLM prompting.
        
        Args:
            lines: Number of recent lines to include
            
        Returns:
            Recent scratchpad content
        """
        content = self.read()
        lines_list = content.split("\n")
        
        if len(lines_list) <= lines:
            return content
        
        return "\n".join(lines_list[-lines:])
