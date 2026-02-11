"""
Konfiguration fuer den Claude Code Session Launcher.
Targets, Pfade und Command-Builder.
"""
from __future__ import annotations

import os
import platform
from dataclasses import dataclass
from typing import List


# Monorepo-Root (wird plattformabhaengig gesetzt, ENV hat Vorrang)
if os.environ.get("MONOREPO_ROOT"):
    MONOREPO_ROOT = os.environ["MONOREPO_ROOT"]
elif platform.system() == "Darwin":
    MONOREPO_ROOT = "/Users/toby/Documents/github/tobys-tool"
else:
    MONOREPO_ROOT = "/config/repos/tobys-tool"

WORKBENCH_CONTEXT = ".claude/WORKBENCH_CONTEXT.md"
WEBHOOK_URL = "https://api.fever-context.de/api/webhooks/claude-session"


@dataclass
class Target:
    """Ein Launcher-Target (App oder Monorepo-Root)."""
    label: str
    subdir: str | None  # None = Monorepo-Root


TARGETS: List[Target] = [
    Target(label="Toby's Tool (Allgemein)", subdir=None),
    Target(label="Finance App", subdir="apps/finance"),
    Target(label="Backend", subdir="apps/tool-backend"),
    Target(label="Frontend", subdir="apps/tool-web"),
    Target(label="Main Bot", subdir="apps/main-bot"),
    Target(label="Guardian Bot", subdir="apps/guardian-bot"),
    Target(label="Workbench Bot", subdir="apps/workbench-bot"),
    Target(label="AI Proxy", subdir="apps/ai-proxy"),
]


def _context_flags(target: Target) -> str:
    """Baut --append-system-prompt Flag fuer Workbench-Context.
    CLAUDE.md und README.md werden von Claude Code automatisch entdeckt."""
    flags = ""

    # Workbench-Context (global, wird nicht auto-entdeckt)
    ctx = f"{MONOREPO_ROOT}/{WORKBENCH_CONTEXT}"
    flags += f' --append-system-prompt "$([ -f {ctx} ] && cat {ctx})"'

    return flags


def _context_flags_with_greeting(target: Target) -> str:
    """Baut Context-Flags inkl. Greeting-Instruktion als System-Prompt."""
    flags = _context_flags(target)

    # Greeting-Instruktion als Teil des System-Prompts
    greeting = (
        f"Wenn der User die Session startet, begruesse ihn kurz als Toby. "
        f"Bestatige dass du den Projektkontext von {target.label} geladen hast "
        f"und fasse in 1-2 Saetzen zusammen was das Projekt macht. "
        f"Frage dann was er heute machen moechte."
    )
    flags += f' --append-system-prompt "{greeting}"'

    return flags


def build_interactive_command(target: Target) -> str:
    """Baut den Shell-Befehl fuer eine interaktive Claude Code Session."""
    parts = [
        f'cd "{MONOREPO_ROOT}"',
        "git pull --ff-only || true",
    ]

    if target.subdir:
        parts.append(f'cd "{target.subdir}"')

    claude_cmd = f'unset ANTHROPIC_API_KEY; claude{_context_flags_with_greeting(target)} "Hallo"'

    parts.append(claude_cmd)
    return " && ".join(parts)


def build_autonomous_command(target: Target, prompt: str) -> str:
    """Baut den Shell-Befehl fuer eine autonome Claude Code Session.
    Ergebnis wird per Webhook an die Leitstelle (Telegram) geschickt."""
    escaped_prompt = prompt.replace('"', '\\"')

    parts = [
        f'cd "{MONOREPO_ROOT}"',
        "git pull --ff-only || true",
    ]

    if target.subdir:
        parts.append(f'cd "{target.subdir}"')

    tmpfile = "/tmp/claude_autonomous_result.txt"
    # Claude ausfuehren, Ergebnis anzeigen und speichern
    claude_cmd = (
        f'unset ANTHROPIC_API_KEY;'
        f' echo ">>> Claude arbeitet..."; echo "";'
        f' claude --print'
        f'{_context_flags(target)}'
        f' "{escaped_prompt}"'
        f' | tee {tmpfile};'
        # Ergebnis per Python JSON-safe an Webhook senden
        f' python3 -c "'
        f"import json, urllib.request;"
        f" result=open('{tmpfile}').read();"
        f" data=json.dumps({{'target':'{target.label}','prompt':'''{escaped_prompt}''','result':result}}).encode();"
        f" req=urllib.request.Request('{WEBHOOK_URL}',data=data,headers={{'Content-Type':'application/json'}});"
        f" urllib.request.urlopen(req);"
        f" print(''); print('>>> Ergebnis an Leitstelle gesendet')"
        f'";'
        f' echo ""; echo "--- Session beendet. Enter zum Schliessen ---"; read'
    )

    parts.append(claude_cmd)
    return " && ".join(parts)
