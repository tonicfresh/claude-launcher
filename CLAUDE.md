# Claude Launcher

> Kompakte GUI zum Starten von Claude Code Sessions fuer beliebige Monorepos.

## Uebersicht
- **Ziel:** Per Knopfdruck Claude Code Sessions starten (interaktiv oder autonom)
- **Zielgruppe:** Toby (Mac + Kubuntu Webtop)
- **Status:** In Entwicklung
- **Tech:** Python 3 + tkinter (keine externen Dependencies)

## Dateien

| Datei | Beschreibung |
|-------|-------------|
| `launcher.py` | Haupt-GUI (tkinter, Canvas-basierte Buttons) |
| `config.py` | Targets, Pfade, Command-Builder |
| `terminal.py` | iTerm2 (Mac) / Konsole (Linux) Abstraktion |
| `claude-launcher.command` | macOS Doppelklick-Starter |
| `session-end-docs.sh` | SessionEnd Hook fuer Auto-Doku-Updates |

## Architektur

- `config.py` definiert Targets (Label, Subdir, CLAUDE.md-Pfad)
- `terminal.py` abstrahiert Terminal-Oeffnung (AppleScript auf Mac, Konsole auf Linux)
- `launcher.py` baut die GUI und verbindet beides
- Pfad-Erkennung: Mac vs Linux automatisch, ENV `MONOREPO_ROOT` als Override

## Installation

```bash
# Mac
alias cl="python3.12 ~/Documents/github/claude-launcher/launcher.py"

# Kubuntu Webtop: KDE Autostart .desktop Datei
```

## SessionEnd Hook

`session-end-docs.sh` wird in `.claude/hooks/` des Zielprojekts platziert und in `settings.local.json` registriert. Analysiert git diff, ruft Claude Sonnet auf, aktualisiert Doku, committed und pusht.
