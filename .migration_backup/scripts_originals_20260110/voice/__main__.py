"""
Orion ODA V3 - ADA Voice Interface CLI
======================================

Run ADA from command line:
    python -m scripts.voice --mock    # Mock STT (keyboard input)
    python -m scripts.voice           # Real microphone (requires RealtimeSTT)
"""

import argparse
import asyncio
import logging

from lib.oda.voice.ada import AlwaysOnAssistant


def setup_logging(verbose: bool = False):
    """Configure logging."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s | %(levelname)-7s | %(name)s | %(message)s",
        datefmt="%H:%M:%S"
    )


def main():
    """Run ADA from command line."""
    parser = argparse.ArgumentParser(
        description="ADA - Always-On Desktop Assistant"
    )
    parser.add_argument(
        "--mock", 
        action="store_true", 
        help="Use mock STT (keyboard input instead of microphone)"
    )
    parser.add_argument(
        "--tts", 
        default="auto", 
        choices=["auto", "elevenlabs", "system"],
        help="TTS provider to use"
    )
    parser.add_argument(
        "--scratchpad", 
        default="./scratchpad.md",
        help="Path to scratchpad file"
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Enable verbose logging"
    )
    
    args = parser.parse_args()
    
    setup_logging(args.verbose)
    
    ada = AlwaysOnAssistant(
        scratchpad_path=args.scratchpad,
        tts_provider=args.tts,
        use_mock_stt=args.mock,
    )
    
    try:
        asyncio.run(ada.start())
    except KeyboardInterrupt:
        print("\n👋 ADA shutdown complete")


if __name__ == "__main__":
    main()
