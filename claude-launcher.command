#!/bin/bash
# macOS Doppelklick-Starter fuer den Claude Code Launcher
# In Dock ziehen oder per Finder starten
cd "$(dirname "$0")"
# Homebrew Python (3.12) wegen tkinter-Kompatibilitaet auf macOS
python3.12 launcher.py 2>/dev/null || python3 launcher.py
