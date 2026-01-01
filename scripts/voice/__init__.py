# Orion ODA V3 - Voice Interface Module
# =====================================
# Implements ADA (Always-On Desktop Assistant) pattern from IndyDevDan

from .scratchpad import Scratchpad
from .tts import TTSEngine, TTSProvider, ElevenLabsTTS, SystemTTS
from .stt import get_stt_listener, RealtimeSTTListener, MockSTTListener, HAS_REALTIME_STT
from .ada import AlwaysOnAssistant

__all__ = [
    "Scratchpad",
    "TTSEngine", 
    "TTSProvider",
    "ElevenLabsTTS",
    "SystemTTS",
    "get_stt_listener",
    "RealtimeSTTListener",
    "MockSTTListener",
    "HAS_REALTIME_STT",
    "AlwaysOnAssistant",
]
