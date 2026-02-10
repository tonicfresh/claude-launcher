# Claude Code Launcher

Kompakte GUI zum Starten von Claude Code Sessions fuer Monorepos.

## Features

- **Interaktive Sessions** — Oeffnet Claude Code im Terminal (iTerm2/Konsole)
- **Autonome Sessions** — Prompt eingeben, Claude arbeitet selbststaendig
- **Auto git pull** — Holt den neuesten Stand vor jeder Session
- **SessionEnd Hook** — Aktualisiert Doku automatisch nach jeder Session
- **Cross-Platform** — Mac (iTerm2) + Linux/Kubuntu (Konsole)

## Quick Start

```bash
# Mac
python3.12 launcher.py

# Oder als Alias
alias cl="python3.12 /pfad/zu/claude-launcher/launcher.py"
cl
```

## Voraussetzungen

- Python 3.9+ mit tkinter
- macOS: `brew install python-tk@3.12`
- Linux: `apt install python3-tk`
- Claude Code CLI (`claude`) installiert

## Konfiguration

Targets werden in `config.py` definiert. Jedes Target hat:

```python
Target(
    label="Mein Projekt",        # Button-Text
    subdir="apps/mein-projekt",  # Unterverzeichnis (None = Root)
    claude_md="apps/.../CLAUDE.md",  # Zusaetzliche --read Datei
)
```

Monorepo-Root wird automatisch erkannt (Mac/Linux) oder via `MONOREPO_ROOT` ENV gesetzt.

## SessionEnd Hook

`session-end-docs.sh` aktualisiert Dokumentation automatisch nach Code-Aenderungen:

1. In `.claude/hooks/` des Projekts kopieren
2. In `.claude/settings.local.json` registrieren:

```json
{
  "hooks": {
    "SessionEnd": [{
      "matcher": "",
      "hooks": [{
        "type": "command",
        "command": "\"$CLAUDE_PROJECT_DIR\"/.claude/hooks/session-end-docs.sh",
        "timeout": 120
      }]
    }]
  }
}
```

## Lizenz

MIT
