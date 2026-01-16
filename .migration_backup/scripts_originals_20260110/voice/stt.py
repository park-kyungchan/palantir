"""
Orion ODA V3 - Speech-to-Text Listener
======================================
VAD-enabled speech recognition with fallback.

Maps to IndyDevDan's ADA Sensor (Ears) component.
"""

import asyncio
import logging
from typing import AsyncGenerator, Callable, Optional

logger = logging.getLogger(__name__)

# RealtimeSTT is optional - graceful fallback
try:
    from RealtimeSTT import AudioToTextRecorder
    HAS_REALTIME_STT = True
except ImportError:
    HAS_REALTIME_STT = False
    logger.debug("RealtimeSTT not installed. Voice input disabled.")


class RealtimeSTTListener:
    """
    Real-time speech-to-text with Voice Activity Detection.
    
    Maps to IndyDevDan's ADA Sensor (Ears) component.
    
    Requirements:
        pip install RealtimeSTT
        
    Note:
        Requires microphone access and PyAudio dependencies.
    """
    
    def __init__(
        self,
        vad_enabled: bool = True,
        model: str = "tiny.en",  # Whisper model
        language: str = "en",
        on_realtime_transcript: Callable[[str], None] = None,
    ):
        self.vad_enabled = vad_enabled
        self.model = model
        self.language = language
        self.on_realtime_transcript = on_realtime_transcript
        self._recorder: Optional["AudioToTextRecorder"] = None
        self._is_listening = False
    
    def _create_recorder(self) -> Optional["AudioToTextRecorder"]:
        """Create the STT recorder instance."""
        if not HAS_REALTIME_STT:
            return None
        
        return AudioToTextRecorder(
            model=self.model,
            language=self.language,
            spinner=False,
            enable_realtime_transcription=True,
            realtime_processing_pause=0.1,
            on_realtime_transcription_update=self._on_realtime_update,
            silero_sensitivity=0.4 if self.vad_enabled else 0.0,
        )
    
    def _on_realtime_update(self, text: str):
        """Callback for real-time transcript updates."""
        if self.on_realtime_transcript:
            self.on_realtime_transcript(text)
    
    async def stream(self) -> AsyncGenerator[str, None]:
        """
        Stream transcribed text as it's detected.
        
        Yields:
            Transcribed text segments
        """
        if not HAS_REALTIME_STT:
            logger.error("RealtimeSTT not available")
            return
        
        self._recorder = self._create_recorder()
        self._is_listening = True
        
        logger.info("🎤 Listening for voice input...")
        
        try:
            while self._is_listening:
                # Run blocking recorder in thread pool
                text = await asyncio.get_event_loop().run_in_executor(
                    None,
                    self._recorder.text
                )
                
                if text and text.strip():
                    logger.info(f"📝 Transcribed: {text[:50]}...")
                    yield text.strip()
                
                await asyncio.sleep(0.1)
                
        except Exception as e:
            logger.error(f"STT error: {e}")
            raise
        finally:
            self.stop()
    
    def stop(self):
        """Stop listening."""
        self._is_listening = False
        if self._recorder:
            try:
                self._recorder.stop()
            except Exception:
                pass


class MockSTTListener:
    """
    Mock STT for testing without microphone.
    
    Reads from stdin or predefined prompts.
    """
    
    def __init__(self, prompts: list[str] = None):
        self.prompts = prompts or []
        self._index = 0
        self._running = True
    
    async def stream(self) -> AsyncGenerator[str, None]:
        """Stream mock transcripts."""
        if self.prompts:
            for prompt in self.prompts:
                if not self._running:
                    break
                yield prompt
                await asyncio.sleep(1)
        else:
            # Interactive mode
            print("\n🎤 Mock STT Mode - Type your input (type 'quit' to exit):\n")
            while self._running:
                try:
                    text = await asyncio.get_event_loop().run_in_executor(
                        None,
                        lambda: input("🎤 Say: ")
                    )
                    if text.lower() in ["quit", "exit", "q"]:
                        break
                    if text.strip():
                        yield text
                except EOFError:
                    break
    
    def stop(self):
        """Stop listening."""
        self._running = False


def get_stt_listener(mock: bool = False, prompts: list[str] = None):
    """
    Factory function to get appropriate STT listener.
    
    Args:
        mock: Force mock mode
        prompts: Predefined prompts for mock mode
        
    Returns:
        STT listener instance
    """
    if mock or not HAS_REALTIME_STT:
        logger.info("Using MockSTTListener")
        return MockSTTListener(prompts)
    else:
        logger.info("Using RealtimeSTTListener")
        return RealtimeSTTListener()
