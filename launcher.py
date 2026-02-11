#!/usr/bin/env python3
"""
Claude Code Session Launcher - GUI fuer Tobys-Tool Monorepo.
"""
import os
import platform
import tkinter as tk
from tkinter import simpledialog, messagebox

from config import TARGETS, MONOREPO_ROOT, build_interactive_command, build_autonomous_command
from terminal import open_in_terminal

# Farben
BG = "#0f0f17"
SURFACE = "#1a1a2e"
BORDER = "#2a2a40"
TEXT = "#c8cad0"
TEXT_DIM = "#6b7280"
BLUE = "#3b82f6"
BLUE_HOVER = "#2563eb"
ORANGE = "#e67e22"
ORANGE_HOVER = "#d35400"
BTN_TEXT = "#ffffff"

# Platform-spezifische Anpassungen
IS_LINUX = platform.system() == "Linux"
FONT = "Sans" if IS_LINUX else "Helvetica"
BTN_H = 32 if IS_LINUX else 28
FONT_BTN = 11 if IS_LINUX else 10
FONT_TITLE = 14 if IS_LINUX else 13
FONT_SUB = 10 if IS_LINUX else 9
WIN_W = 380 if IS_LINUX else 340


class FlatButton(tk.Canvas):
    """Farbiger Button der auf macOS und Linux funktioniert (Canvas-basiert)."""

    def __init__(self, parent, text, bg_color, hover_color, command, **kw):
        super().__init__(parent, highlightthickness=0, bd=0, bg=SURFACE, **kw)
        self.bg_color = bg_color
        self.hover_color = hover_color
        self.command = command
        self.h = BTN_H
        self.configure(height=self.h)

        self.bind("<Configure>", self._draw)
        self.bind("<Enter>", lambda e: self._set_color(hover_color))
        self.bind("<Leave>", lambda e: self._set_color(bg_color))
        self.bind("<Button-1>", lambda e: self.command())
        self._text = text
        self._current_color = bg_color

    def _set_color(self, color):
        self._current_color = color
        self._draw()

    def _draw(self, event=None):
        self.delete("all")
        w = self.winfo_width()
        r = 6
        self.create_round_rect(2, 1, w - 2, self.h - 1, r, fill=self._current_color, outline="")
        self.create_text(w // 2, self.h // 2, text=self._text, fill=BTN_TEXT,
                         font=(FONT, FONT_BTN), anchor="center")

    def create_round_rect(self, x1, y1, x2, y2, r, **kw):
        self.create_arc(x1, y1, x1 + 2 * r, y1 + 2 * r, start=90, extent=90, style="pieslice", **kw)
        self.create_arc(x2 - 2 * r, y1, x2, y1 + 2 * r, start=0, extent=90, style="pieslice", **kw)
        self.create_arc(x1, y2 - 2 * r, x1 + 2 * r, y2, start=180, extent=90, style="pieslice", **kw)
        self.create_arc(x2 - 2 * r, y2 - 2 * r, x2, y2, start=270, extent=90, style="pieslice", **kw)
        self.create_rectangle(x1 + r, y1, x2 - r, y2, **kw)
        self.create_rectangle(x1, y1 + r, x1 + r, y2 - r, **kw)
        self.create_rectangle(x2 - r, y1 + r, x2, y2 - r, **kw)


class LauncherApp:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("Claude Code Launcher")
        self.root.configure(bg=BG)

        self._build_header()
        sep = tk.Frame(self.root, bg=BORDER, height=1)
        sep.pack(fill="x", padx=12)
        self._build_section("Interaktiv", BLUE, BLUE_HOVER, self._start_interactive)
        sep2 = tk.Frame(self.root, bg=BORDER, height=1)
        sep2.pack(fill="x", padx=12)
        self._build_section("Autonom", ORANGE, ORANGE_HOVER, self._start_autonomous)
        # Bottom-Padding
        tk.Frame(self.root, bg=BG, height=10).pack()

        self.root.update_idletasks()
        h = self.root.winfo_reqheight()
        self.root.geometry(f"{WIN_W}x{h}")
        self.root.minsize(WIN_W, h)
        self.root.resizable(False, False)
        self._center()

    def _build_header(self) -> None:
        f = tk.Frame(self.root, bg=BG, pady=10)
        f.pack(fill="x")
        tk.Label(f, text="Session Launcher", font=(FONT, FONT_TITLE, "bold"),
                 fg=TEXT, bg=BG).pack()
        tk.Label(f, text=os.path.basename(MONOREPO_ROOT), font=(FONT, FONT_SUB),
                 fg=TEXT_DIM, bg=BG).pack()

    def _build_section(self, title, color, hover, on_click) -> None:
        frame = tk.Frame(self.root, bg=BG, padx=12, pady=8)
        frame.pack(fill="x")

        tk.Label(frame, text=title, font=(FONT, FONT_SUB, "bold"), fg=color,
                 bg=BG, anchor="w").pack(fill="x", pady=(0, 4))

        for target in TARGETS:
            btn = FlatButton(
                frame, target.label, color, hover,
                command=lambda t=target: on_click(t),
            )
            btn.pack(fill="x", pady=1)

    def _start_interactive(self, target) -> None:
        try:
            open_in_terminal(build_interactive_command(target))
        except Exception as e:
            messagebox.showerror("Fehler", str(e))

    def _start_autonomous(self, target) -> None:
        prompt = self._ask_prompt(target)
        if not prompt:
            return
        try:
            open_in_terminal(build_autonomous_command(target, prompt))
        except Exception as e:
            messagebox.showerror("Fehler", str(e))

    def _ask_prompt(self, target) -> str | None:
        """Eigener Prompt-Dialog im Launcher-Style."""
        dlg = tk.Toplevel(self.root)
        dlg.title(f"Prompt - {target.label}")
        dlg.configure(bg=BG)
        dlg.resizable(False, False)

        result = [None]

        tk.Label(dlg, text=f"Prompt fuer {target.label}:",
                 font=(FONT, FONT_SUB, "bold"), fg=ORANGE, bg=BG,
                 anchor="w").pack(fill="x", padx=16, pady=(16, 6))

        entry = tk.Text(dlg, height=4, width=40, font=(FONT, FONT_BTN),
                        bg=SURFACE, fg=TEXT, insertbackground=TEXT,
                        relief="flat", bd=0, wrap="word",
                        highlightthickness=1, highlightcolor=ORANGE,
                        highlightbackground=BORDER)
        entry.pack(fill="x", padx=16, pady=(0, 10))

        def submit():
            result[0] = entry.get("1.0", "end-1c").strip()
            dlg.destroy()

        def on_key(e):
            if e.keysym == "Return" and not e.state & 0x1:  # Enter ohne Shift
                submit()
                return "break"

        entry.bind("<Key>", on_key)

        btn_frame = tk.Frame(dlg, bg=BG)
        btn_frame.pack(fill="x", padx=16, pady=(0, 16))

        cancel_btn = FlatButton(btn_frame, "Abbrechen", BORDER, "#3a3a50",
                                command=dlg.destroy, width=100)
        cancel_btn.pack(side="left", fill="x", expand=True, padx=(0, 4))

        send_btn = FlatButton(btn_frame, "Starten", ORANGE, ORANGE_HOVER,
                              command=submit, width=100)
        send_btn.pack(side="right", fill="x", expand=True, padx=(4, 0))

        dlg.transient(self.root)

        # Zentrieren
        dlg.update_idletasks()
        x = self.root.winfo_x() + (self.root.winfo_width() - dlg.winfo_reqwidth()) // 2
        y = self.root.winfo_y() + 50
        dlg.geometry(f"+{x}+{y}")

        dlg.deiconify()
        dlg.wait_visibility()
        dlg.grab_set()
        entry.focus_set()

        self.root.wait_window(dlg)
        return result[0]

    def _center(self) -> None:
        self.root.update_idletasks()
        w, h = self.root.winfo_width(), self.root.winfo_height()
        x = (self.root.winfo_screenwidth() // 2) - (w // 2)
        y = (self.root.winfo_screenheight() // 3) - (h // 2)
        self.root.geometry(f"{w}x{h}+{x}+{y}")


if __name__ == "__main__":
    root = tk.Tk()
    LauncherApp(root)
    root.mainloop()
