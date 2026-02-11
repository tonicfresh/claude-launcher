"""
Terminal-Abstraktion fuer den Claude Code Launcher.
Mac: iTerm2 via AppleScript
Linux: Konsole
"""
import platform
import subprocess
import shlex


def open_in_terminal(command: str) -> None:
    """Oeffnet einen Shell-Befehl in einem neuen Terminal-Fenster."""
    system = platform.system()
    if system == "Darwin":
        _open_iterm2(command)
    elif system == "Linux":
        _open_konsole(command)
    else:
        raise RuntimeError(f"Nicht unterstuetztes OS: {system}")


def _open_iterm2(command: str) -> None:
    """Oeffnet iTerm2 mit AppleScript und fuehrt den Befehl aus."""
    # AppleScript: Neues Fenster in iTerm2
    escaped = command.replace("\\", "\\\\").replace('"', '\\"')
    applescript = f'''
    tell application "iTerm2"
        activate
        set newWindow to (create window with default profile)
        tell current session of newWindow
            write text "{escaped}"
        end tell
    end tell
    '''
    subprocess.Popen(
        ["osascript", "-e", applescript],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )


def _open_konsole(command: str) -> None:
    """Oeffnet Konsole (KDE) mit dem Befehl. Login-Shell fuer volle Umgebung."""
    # Deutsche Tastatur setzen, dann Befehl ausfuehren
    wrapped = f'setxkbmap de; {command}'
    subprocess.Popen(
        ["konsole", "-e", "bash", "-lc", wrapped],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
