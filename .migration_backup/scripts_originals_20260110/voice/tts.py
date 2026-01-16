"""
Orion ODA V3 - Text-to-Speech Engine
====================================
Provider-based TTS with fallback.

Maps to IndyDevDan's ADA Actuator (Mouth) component.
"""

import asyncio
import logging
import os
from abc import ABC, abstractmethod
from typing import Optional

logger = logging.getLogger(__name__)


class TTSProvider(ABC):
    """Base class for TTS providers."""
    
    @abstractmethod
    async def speak(self, text: str) -> None:
        """Speak the given text."""
        ...
    
    @abstractmethod
    def is_available(self) -> bool:
        """Check if provider is available."""
        ...


class ElevenLabsTTS(TTSProvider):
    """
    ElevenLabs TTS provider.
    
    Requires:
        pip install elevenlabs
        export ELEVEN_API_KEY=your_key
    """
    
    def __init__(
        self,
        voice_id: str = "21m00Tcm4TlvDq8ikWAM",  # Rachel
        model_id: str = "eleven_monolingual_v1",
    ):
        self.voice_id = voice_id
        self.model_id = model_id
        self._client = None
    
    def _get_client(self):
        if self._client is None:
            try:
                from elevenlabs.client import ElevenLabs
                self._client = ElevenLabs(
                    api_key=os.getenv("ELEVEN_API_KEY")
                )
            except ImportError:
                logger.debug("elevenlabs package not installed")
        return self._client
    
    def is_available(self) -> bool:
        return (
            self._get_client() is not None and
            os.getenv("ELEVEN_API_KEY") is not None
        )
    
    async def speak(self, text: str) -> None:
        """Speak using ElevenLabs API."""
        client = self._get_client()
        if not client:
            logger.error("ElevenLabs client not available")
            return
        
        try:
            # Generate audio
            audio_generator = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: client.generate(
                    text=text,
                    voice=self.voice_id,
                    model=self.model_id,
                )
            )
            
            # Play audio
            await self._play_audio(audio_generator)
            
        except Exception as e:
            logger.error(f"ElevenLabs TTS error: {e}")
    
    async def _play_audio(self, audio_bytes):
        """Play audio bytes."""
        try:
            from elevenlabs import play
            await asyncio.get_event_loop().run_in_executor(
                None, play, audio_bytes
            )
        except ImportError:
            logger.warning("Audio playback not available")


class SystemTTS(TTSProvider):
    """
    System TTS fallback using pyttsx3 or say command.
    
    Works on: macOS (say), Linux (espeak), Windows (SAPI)
    """
    
    def __init__(self):
        self._engine = None
    
    def _get_engine(self):
        if self._engine is None:
            try:
                import pyttsx3
                self._engine = pyttsx3.init()
                # Adjust speech rate
                self._engine.setProperty('rate', 175)
            except Exception as e:
                logger.debug(f"pyttsx3 not available: {e}")
        return self._engine
    
    def is_available(self) -> bool:
        return self._get_engine() is not None
    
    async def speak(self, text: str) -> None:
        """Speak using system TTS."""
        engine = self._get_engine()
        
        if engine:
            await asyncio.get_event_loop().run_in_executor(
                None,
                self._speak_sync,
                text,
            )
        else:
            # Fallback to say command on macOS/Linux
            await self._speak_cli(text)
    
    def _speak_sync(self, text: str):
        """Synchronous speak."""
        if self._engine:
            self._engine.say(text)
            self._engine.runAndWait()
    
    async def _speak_cli(self, text: str):
        """Use macOS 'say' command or Linux 'espeak'."""
        import subprocess
        import platform
        
        if platform.system() == "Darwin":
            cmd = ["say", text]
        elif platform.system() == "Linux":
            cmd = ["espeak", text]
        else:
            logger.warning("No system TTS available")
            return
        
        try:
            await asyncio.create_subprocess_exec(*cmd)
        except FileNotFoundError:
            logger.warning(f"TTS command not found: {cmd[0]}")


class PrintTTS(TTSProvider):
    """
    Fallback TTS that just prints to console.
    Always available for testing.
    """
    
    def is_available(self) -> bool:
        return True
    
    async def speak(self, text: str) -> None:
        """Print text to console."""
        print(f"🔊 [TTS]: {text}")


class TTSEngine:
    """
    Unified TTS engine with provider fallback.
    
    Maps to IndyDevDan's ADA Actuator (Mouth) component.
    
    Usage:
        tts = TTSEngine()
        await tts.speak("Hello, world!")
    """
    
    def __init__(self, provider: str = "auto"):
        self.providers: list[TTSProvider] = []
        
        if provider in ["auto", "elevenlabs"]:
            self.providers.append(ElevenLabsTTS())
        
        if provider in ["auto", "system"]:
            self.providers.append(SystemTTS())
        
        # Always add print fallback
        self.providers.append(PrintTTS())
    
    async def speak(self, text: str) -> bool:
        """
        Speak text using best available provider.
        
        Returns:
            True if speech succeeded
        """
        for provider in self.providers:
            if provider.is_available():
                logger.info(f"🔊 Speaking via {provider.__class__.__name__}")
                await provider.speak(text)
                return True
        
        logger.warning("No TTS provider available")
        return False
