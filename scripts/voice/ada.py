"""
Orion ODA V3 - ADA (Always-On Desktop Assistant)
================================================
Voice-first interface for Orion ODA.

Maps to IndyDevDan's ADA architecture:
- Sensor (Ears): RealtimeSTT
- Processor (Brain): InstructorClient
- Actuator (Mouth): TTSEngine
- Effector (Body): ToolMarshaler
- Memory: Scratchpad
"""

import asyncio
import logging
from typing import Optional, Dict, Any

from scripts.voice.stt import get_stt_listener, HAS_REALTIME_STT
from scripts.voice.tts import TTSEngine
from scripts.voice.scratchpad import Scratchpad

logger = logging.getLogger(__name__)


class AlwaysOnAssistant:
    """
    ADA - Always-On Desktop Assistant.
    
    Voice-first interface for Orion ODA.
    Maps to IndyDevDan's ADA architecture.
    
    Components:
        - Sensor: STT listener (voice input)
        - Processor: LLM reasoning
        - Actuator: TTS engine (voice output)
        - Effector: ToolMarshaler (action execution)
        - Memory: Scratchpad (shared state)
        
    Usage:
        ada = AlwaysOnAssistant()
        await ada.start()
    """
    
    def __init__(
        self,
        scratchpad_path: str = "./scratchpad.md",
        tts_provider: str = "auto",
        use_mock_stt: bool = False,
    ):
        # Components
        self.stt = get_stt_listener(mock=use_mock_stt)
        self.tts = TTSEngine(provider=tts_provider)
        self.scratchpad = Scratchpad(scratchpad_path)
        
        # Lazy-loaded components (optional deps)
        self._llm = None
        self._marshaler = None
        
        # State
        self._running = False
    
    @property
    def llm(self):
        """Lazy-load InstructorClient."""
        if self._llm is None:
            try:
                from scripts.llm.instructor_client import InstructorClient
                self._llm = InstructorClient()
            except ImportError:
                logger.warning("InstructorClient not available")
        return self._llm
    
    @property
    def marshaler(self):
        """Lazy-load ToolMarshaler."""
        if self._marshaler is None:
            try:
                from scripts.runtime.marshaler import ToolMarshaler
                from scripts.ontology.actions import action_registry
                self._marshaler = ToolMarshaler(action_registry)
            except ImportError:
                logger.warning("ToolMarshaler not available")
        return self._marshaler
    
    async def start(self):
        """
        Start the always-on listening loop.
        
        This is the main entry point for ADA.
        """
        self._running = True
        
        # Greeting
        await self.tts.speak("Ada online. How can I help?")
        self.scratchpad.append_agent_status(
            "Session Started", 
            "Listening for voice input..."
        )
        
        logger.info("🟢 ADA started - listening...")
        print("\n" + "="*50)
        print("  ADA - Always-On Desktop Assistant")
        print("  Type 'quit' to exit")
        print("="*50 + "\n")
        
        try:
            async for transcript in self.stt.stream():
                if not self._running:
                    break
                
                await self._process_input(transcript)
                
        except asyncio.CancelledError:
            logger.info("ADA cancelled")
        except KeyboardInterrupt:
            logger.info("ADA interrupted by user")
        finally:
            await self.stop()
    
    async def _process_input(self, transcript: str):
        """
        Process voice input.
        
        Flow:
        1. Append to scratchpad
        2. Get context
        3. Send to LLM
        4. Execute actions or respond
        5. Speak response
        6. Update scratchpad
        """
        logger.info(f"Processing: {transcript[:50]}...")
        
        # 1. Append user intent
        self.scratchpad.append_user_intent(transcript)
        
        # 2. Get context
        context = self.scratchpad.get_recent_context(50)
        
        # 3. Send to LLM
        self.scratchpad.append_thinking("Analyzing request...")
        
        try:
            response = await self._get_llm_response(transcript, context)
            
            # 4. Execute actions if any
            if response.get("action"):
                await self._execute_action(
                    response["action"], 
                    response.get("params", {})
                )
            
            # 5. Speak response
            message = response.get(
                "message", 
                "I'm not sure how to help with that."
            )
            await self.tts.speak(message)
            
            # 6. Update scratchpad
            self.scratchpad.append_agent_status(
                "Responded",
                f"Said: {message[:100]}..."
            )
            
        except Exception as e:
            logger.error(f"Processing error: {e}")
            await self.tts.speak("Sorry, I encountered an error.")
            self.scratchpad.append_agent_status("Error", str(e))
    
    async def _get_llm_response(
        self, 
        prompt: str, 
        context: str
    ) -> Dict[str, Any]:
        """
        Get LLM response for the input.
        
        Returns:
            Dict with 'message' and optional 'action' and 'params'
        """
        # If no LLM available, return simple echo
        if self.llm is None:
            return {
                "message": f"I heard: {prompt}. LLM not configured."
            }
        
        system_prompt = """You are ADA, an always-on voice assistant.
        
You can:
- Answer questions
- Execute actions (save_insight, save_pattern, etc.)
- Help with coding tasks

Keep responses brief and conversational (spoken aloud).

If an action is needed, return JSON with:
{
    "message": "Brief spoken response",
    "action": "action_name",
    "params": {...}
}

If no action, just return:
{
    "message": "Your response"
}
"""
        
        full_prompt = f"""Context from scratchpad:
{context}

User said: {prompt}

Respond as ADA."""
        
        try:
            result = await self.llm.generate_json(
                prompt=full_prompt,
                system=system_prompt,
            )
            return result
        except Exception as e:
            logger.error(f"LLM error: {e}")
            return {"message": f"I heard: {prompt}"}
    
    async def _execute_action(
        self, 
        action_name: str, 
        params: Dict[str, Any]
    ):
        """Execute an action via ToolMarshaler."""
        logger.info(f"Executing action: {action_name}")
        
        if self.marshaler is None:
            self.scratchpad.append_action_result(
                action=action_name,
                success=False,
                result="ToolMarshaler not available"
            )
            return
        
        try:
            from scripts.ontology.actions import ActionContext
            context = ActionContext(actor_id="ada")
            
            result = await self.marshaler.execute_action(
                action_name=action_name,
                params=params,
                context=context,
            )
            
            self.scratchpad.append_action_result(
                action=action_name,
                success=result.success,
                result=str(result.data) if result.data else result.error,
            )
        except Exception as e:
            logger.error(f"Action error: {e}")
            self.scratchpad.append_action_result(
                action=action_name,
                success=False,
                result=str(e)
            )
    
    async def stop(self):
        """Stop ADA."""
        self._running = False
        self.stt.stop()
        
        await self.tts.speak("Goodbye!")
        self.scratchpad.append_agent_status("Session Ended")
        
        logger.info("🔴 ADA stopped")
