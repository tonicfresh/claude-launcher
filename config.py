"""
Konfiguration fuer den Claude Code Session Launcher.
Targets, Pfade und Command-Builder.
"""
from __future__ import annotations

import os
import platform
from dataclasses import dataclass
from typing import Optional, List


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
    claude_md: str | None  # Zusaetzliche CLAUDE.md (relativ zum Monorepo-Root)


TARGETS: List[Target] = [
    Target(
        label="Toby's Tool (Allgemein)",
        subdir=None,
        claude_md=None,
    ),
    Target(
        label="Finance App",
        subdir="apps/finance",
        claude_md="apps/finance/CLAUDE.md",
    ),
    Target(
        label="Backend",
        subdir="apps/tool-backend",
        claude_md="apps/tool-backend/CLAUDE.md",
    ),
    Target(
        label="Frontend",
        subdir="apps/tool-web",
        claude_md="apps/tool-web/CLAUDE.md",
    ),
    Target(
        label="Main Bot",
        subdir="apps/main-bot",
        claude_md="apps/main-bot/CLAUDE.md",
    ),
    Target(
        label="Guardian Bot",
        subdir="apps/guardian-bot",
        claude_md="apps/guardian-bot/CLAUDE.md",
    ),
    Target(
        label="Workbench Bot",
        subdir="apps/workbench-bot",
        claude_md="apps/workbench-bot/CLAUDE.md",
    ),
    Target(
        label="AI Proxy",
        subdir="apps/ai-proxy",
        claude_md="apps/ai-proxy/CLAUDE.md",
    ),
]


def build_interactive_command(target: Target) -> str:
    """Baut den Shell-Befehl fuer eine interaktive Claude Code Session."""
    parts = [
        f'cd "{MONOREPO_ROOT}"',
        "git pull --ff-only 2>/dev/null || true",
    ]

    if target.subdir:
        parts.append(f'cd "{target.subdir}"')

    # Claude-Befehl mit --read Flags
    claude_cmd = "claude"
    claude_cmd += f' --read "{MONOREPO_ROOT}/{WORKBENCH_CONTEXT}"'
    if target.claude_md:
        claude_cmd += f' --read "{MONOREPO_ROOT}/{target.claude_md}"'

    parts.append(claude_cmd)
    return " && ".join(parts)


def build_autonomous_command(target: Target, prompt: str) -> str:
    """Baut den Shell-Befehl fuer eine autonome Claude Code Session (--print)."""
    # Prompt escapen fuer Shell
    escaped_prompt = prompt.replace("'", "'\\''")

    parts = [
        f'cd "{MONOREPO_ROOT}"',
        "git pull --ff-only 2>/dev/null || true",
    ]

    if target.subdir:
        parts.append(f'cd "{target.subdir}"')

    # Claude-Befehl mit --print und --dangerously-skip-permissions
    read_flags = f'--read "{MONOREPO_ROOT}/{WORKBENCH_CONTEXT}"'
    if target.claude_md:
        read_flags += f' --read "{MONOREPO_ROOT}/{target.claude_md}"'

    claude_cmd = (
        f"echo '{escaped_prompt}' | claude --print "
        f"--dangerously-skip-permissions {read_flags}"
    )

    parts.append(claude_cmd)
    # Shell offen halten nach Ausfuehrung
    parts.append('echo "" && echo "--- Session beendet. Enter zum Schliessen ---" && read')
    return " && ".join(parts)
