"""
Orion ODA V3 - Slash Command Handler
=====================================
Handles slash commands for agentic workflows.

Maps to IndyDevDan's .claude/commands/ pattern.
"""

import logging
from pathlib import Path
from typing import Any, Dict

from lib.oda.layer.subagent_manager import SubAgentManager

logger = logging.getLogger(__name__)


class SlashCommandHandler:
    """
    Handles slash commands for agentic workflows.
    
    Maps to IndyDevDan's .claude/commands/ pattern.
    
    Built-in commands:
        /infinite <spec> <output> <count>
        /spawn <count> <task>
        /status
    
    Usage:
        handler = SlashCommandHandler(marshaler)
        result = await handler.handle("spawn", "3 Write tests", context)
    """
    
    def __init__(self, marshaler=None):
        self.marshaler = marshaler
        self._commands: Dict[str, callable] = {}
        self._managers: Dict[str, SubAgentManager] = {}
        self._register_commands()
    
    def _register_commands(self) -> None:
        """Register built-in slash commands."""
        self._commands["infinite"] = self._cmd_infinite
        self._commands["spawn"] = self._cmd_spawn
        self._commands["status"] = self._cmd_status
        self._commands["help"] = self._cmd_help
    
    def register(self, name: str, handler: callable) -> None:
        """Register a custom command."""
        self._commands[name] = handler
        logger.info(f"Registered command: /{name}")
    
    async def handle(
        self,
        command: str,
        args: str,
        context = None,
    ) -> Dict[str, Any]:
        """
        Handle a slash command.
        
        Args:
            command: Command name (without /)
            args: Command arguments
            context: Execution context (ActionContext)
        """
        if command not in self._commands:
            return {
                "error": f"Unknown command: /{command}",
                "available": list(self._commands.keys()),
            }
        
        try:
            return await self._commands[command](args, context)
        except Exception as e:
            logger.error(f"Command /{command} failed: {e}")
            return {"error": str(e)}
    
    def parse_command(self, text: str) -> tuple[str, str]:
        """
        Parse command from text.
        
        Returns:
            (command_name, args) or (None, None) if not a command
        """
        if not text.startswith("/"):
            return None, None
        
        parts = text[1:].split(maxsplit=1)
        command = parts[0] if parts else ""
        args = parts[1] if len(parts) > 1 else ""
        
        return command, args
    
    async def _cmd_infinite(
        self,
        args: str,
        context,
    ) -> Dict[str, Any]:
        """
        Handle /infinite command.
        
        Usage: /infinite <spec_file> <output_dir> <count>
        
        Examples:
            /infinite specs/blog.md posts 5
            /infinite specs/test.md tests infinite
        """
        parts = args.split()
        if len(parts) < 3:
            return {
                "error": "Usage: /infinite <spec_file> <output_dir> <count>",
                "examples": [
                    "/infinite specs/blog.md posts 5",
                    "/infinite specs/test.md tests infinite",
                ],
            }
        
        spec_file = parts[0]
        output_dir = parts[1]
        count = parts[2]
        
        # Validate spec exists
        if not Path(spec_file).exists():
            return {"error": f"Spec file not found: {spec_file}"}
        
        # Get or create manager
        session_id = str(context.actor_id if context else "default")
        if session_id not in self._managers:
            self._managers[session_id] = SubAgentManager()
        
        manager = self._managers[session_id]
        
        waves = await manager.run_infinite_loop(
            spec=spec_file,
            output_dir=output_dir,
            count=count,
        )
        
        return {
            "command": "infinite",
            "status": manager.get_status(),
            "waves_completed": len(waves),
        }
    
    async def _cmd_spawn(
        self,
        args: str,
        context,
    ) -> Dict[str, Any]:
        """
        Handle /spawn command.
        
        Usage: /spawn <count> <task_description>
        """
        parts = args.split(maxsplit=1)
        if len(parts) < 2:
            return {"error": "Usage: /spawn <count> <task_description>"}
        
        try:
            count = int(parts[0])
        except ValueError:
            return {"error": f"Invalid count: {parts[0]}"}
        
        task = parts[1]
        
        # Get or create manager
        session_id = str(context.actor_id if context else "default")
        if session_id not in self._managers:
            self._managers[session_id] = SubAgentManager()
        
        manager = self._managers[session_id]
        
        tasks = [f"{task} (instance {i+1})" for i in range(count)]
        wave = await manager.spawn_agents(tasks)
        
        return {
            "command": "spawn",
            "wave": wave.number,
            "agents_spawned": len(wave.agents),
            "completed": wave.success_count,
            "failed": wave.failure_count,
        }
    
    async def _cmd_status(
        self,
        args: str,
        context,
    ) -> Dict[str, Any]:
        """
        Handle /status command.
        
        Returns current orchestration status.
        """
        session_id = str(context.actor_id if context else "default")
        
        if session_id in self._managers:
            manager = self._managers[session_id]
            return {
                "command": "status",
                "status": manager.get_status(),
            }
        else:
            return {
                "command": "status",
                "status": "No active sessions",
            }
    
    async def _cmd_help(
        self,
        args: str,
        context,
    ) -> Dict[str, Any]:
        """
        Handle /help command.
        
        Lists available commands.
        """
        return {
            "command": "help",
            "commands": {
                "/infinite": "/infinite <spec> <output_dir> <count> - Run infinite loop",
                "/spawn": "/spawn <count> <task> - Spawn parallel agents",
                "/status": "/status - Get orchestration status",
                "/help": "/help - Show this help",
            },
        }
