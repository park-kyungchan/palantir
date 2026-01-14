"""
Orion ODA V3 - Tools Module Entry Point
========================================

Run with: python -m scripts.tools [command]

Examples:
    python -m scripts.tools sps list
    python -m scripts.tools yt transcribe video.mp4
"""

from scripts.tools.cli import main

if __name__ == "__main__":
    main()
