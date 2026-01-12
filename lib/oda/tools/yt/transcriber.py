"""
Orion ODA V3 - YouTube Automation - Transcriber
================================================
Audio/video transcription using Whisper.

Maps to IndyDevDan's idt yt transcribe command.
"""

import asyncio
import logging
import tempfile
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

# Whisper is optional
try:
    import whisper
    HAS_WHISPER = True
except ImportError:
    HAS_WHISPER = False
    logger.debug("openai-whisper not installed. Transcription disabled.")


class Transcriber:
    """
    Audio/video transcription.
    
    Maps to IndyDevDan's idt yt transcribe functionality.
    
    Supports:
        - Local files (mp3, mp4, wav)
        - YouTube URLs (via yt-dlp)
    
    Usage:
        transcriber = Transcriber()
        text = await transcriber.transcribe("video.mp4")
    """
    
    def __init__(self, model: str = "base"):
        self.model_name = model
        self._whisper = None
    
    def _get_whisper(self):
        """Lazy load Whisper model."""
        if not HAS_WHISPER:
            raise ImportError(
                "openai-whisper not installed. "
                "Run: pip install openai-whisper"
            )
        
        if self._whisper is None:
            logger.info(f"Loading Whisper model: {self.model_name}")
            self._whisper = whisper.load_model(self.model_name)
            logger.info("Whisper model loaded")
        
        return self._whisper
    
    async def transcribe(
        self,
        source: str,
        language: str = "en",
        output_format: str = "text",
    ) -> str:
        """
        Transcribe audio/video.
        
        Args:
            source: File path or YouTube URL
            language: Target language code
            output_format: 'text', 'srt', or 'vtt'
            
        Returns:
            Transcription text
        """
        # Download if YouTube URL
        if source.startswith(("http://", "https://")):
            logger.info(f"Downloading audio from: {source}")
            audio_path = await self._download_audio(source)
        else:
            audio_path = source
        
        # Verify file exists
        if not Path(audio_path).exists():
            raise FileNotFoundError(f"Audio file not found: {audio_path}")
        
        # Transcribe
        logger.info(f"Transcribing: {audio_path}")
        result = await self._transcribe_file(audio_path, language)
        
        # Format output
        if output_format == "text":
            return result["text"]
        elif output_format == "srt":
            return self._to_srt(result.get("segments", []))
        elif output_format == "vtt":
            return self._to_vtt(result.get("segments", []))
        else:
            raise ValueError(f"Unknown format: {output_format}")
    
    async def _download_audio(self, url: str) -> str:
        """Download audio from YouTube."""
        output_path = Path(tempfile.gettempdir()) / "yt_audio.mp3"
        
        cmd = [
            "yt-dlp",
            "-x",  # Extract audio
            "--audio-format", "mp3",
            "-o", str(output_path),
            "--no-playlist",
            url,
        ]
        
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await process.communicate()
        
        if process.returncode != 0:
            raise RuntimeError(f"yt-dlp failed: {stderr.decode()}")
        
        logger.info(f"Downloaded audio to: {output_path}")
        return str(output_path)
    
    async def _transcribe_file(self, path: str, language: str) -> dict:
        """Transcribe audio file."""
        whisper_model = self._get_whisper()
        
        result = await asyncio.get_event_loop().run_in_executor(
            None,
            lambda: whisper_model.transcribe(
                path,
                language=language,
                verbose=False,
            )
        )
        
        logger.info(f"Transcription complete: {len(result['text'])} chars")
        return result
    
    def _to_srt(self, segments: list) -> str:
        """Convert to SRT format."""
        lines = []
        for i, seg in enumerate(segments, 1):
            start = self._format_time_srt(seg["start"])
            end = self._format_time_srt(seg["end"])
            text = seg["text"].strip()
            lines.append(f"{i}\n{start} --> {end}\n{text}\n")
        return "\n".join(lines)
    
    def _to_vtt(self, segments: list) -> str:
        """Convert to VTT format."""
        lines = ["WEBVTT\n"]
        for seg in segments:
            start = self._format_time_vtt(seg["start"])
            end = self._format_time_vtt(seg["end"])
            text = seg["text"].strip()
            lines.append(f"{start} --> {end}\n{text}\n")
        return "\n".join(lines)
    
    @staticmethod
    def _format_time_srt(seconds: float) -> str:
        """Format seconds to SRT timestamp (HH:MM:SS,mmm)."""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        ms = int((seconds % 1) * 1000)
        return f"{hours:02d}:{minutes:02d}:{secs:02d},{ms:03d}"
    
    @staticmethod
    def _format_time_vtt(seconds: float) -> str:
        """Format seconds to VTT timestamp (HH:MM:SS.mmm)."""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        ms = int((seconds % 1) * 1000)
        return f"{hours:02d}:{minutes:02d}:{secs:02d}.{ms:03d}"
