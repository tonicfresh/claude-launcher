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
    """Baut --append-system-prompt Flags fuer Workbench-Context, CLAUDE.md und README.md."""
    flags = ""

    # Workbench-Context (global)
    ctx = f"{MONOREPO_ROOT}/{WORKBENCH_CONTEXT}"
    flags += f' --append-system-prompt "$([ -f {ctx} ] && cat {ctx})"'

    # App-spezifische CLAUDE.md und README.md
    app_dir = f"{MONOREPO_ROOT}/{target.subdir}" if target.subdir else MONOREPO_ROOT
    for filename in ["CLAUDE.md", "README.md"]:
        path = f"{app_dir}/{filename}"
        flags += f' --append-system-prompt "$([ -f {path} ] && cat {path})"'

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
        "git pull --ff-only 2>/dev/null || true",
    ]

    if target.subdir:
        parts.append(f'cd "{target.subdir}"')

    claude_cmd = f"claude{_context_flags_with_greeting(target)}"

    parts.append(claude_cmd)
    return " && ".join(parts)


def build_autonomous_command(target: Target, prompt: str) -> str:
    """Baut den Shell-Befehl fuer eine autonome Claude Code Session (--print)."""
    escaped_prompt = prompt.replace("'", "'\\''")

    parts = [
        f'cd "{MONOREPO_ROOT}"',
        "git pull --ff-only 2>/dev/null || true",
    ]

    if target.subdir:
        parts.append(f'cd "{target.subdir}"')

    claude_cmd = (
        f"echo '{escaped_prompt}' | claude --print"
        f" --dangerously-skip-permissions"
        f"{_context_flags(target)}"
    )

    parts.append(claude_cmd)
    # Shell offen halten nach Ausfuehrung
    parts.append('echo "" && echo "--- Session beendet. Enter zum Schliessen ---" && read')
    return " && ".join(parts)
