"""
Sidebar Code Installer
One-click installer for Sidebar Code skill files targeting Claude Code Desktop App.
Copies skill .md files to ~/.claude/commands/ so they appear as slash commands.
"""

import json
import os
import platform
import shutil
import subprocess
import sys
import tkinter as tk
from tkinter import filedialog, messagebox
from pathlib import Path


def get_resource_path(relative_path: str) -> Path:
    """Get path to bundled resource, works for both dev and PyInstaller."""
    if getattr(sys, '_MEIPASS', None):
        return Path(sys._MEIPASS) / relative_path
    return Path(__file__).parent / relative_path


def get_claude_commands_dir() -> Path:
    """Return ~/.claude/commands/ expanding the home directory."""
    return Path.home() / ".claude" / "commands"


def claude_code_is_installed() -> bool:
    """Check if Claude Code CLI is available on the system."""
    try:
        if platform.system() == "Windows":
            result = subprocess.run(
                ["where", "claude"],
                capture_output=True, text=True, timeout=5
            )
        else:
            result = subprocess.run(
                ["which", "claude"],
                capture_output=True, text=True, timeout=5
            )
        return result.returncode == 0
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False


def load_config() -> dict:
    """Load installer_config.json from the bundled resources."""
    config_path = get_resource_path("installer_config.json")
    with open(config_path, "r", encoding="utf-8") as f:
        return json.load(f)


class InstallerApp:
    """Main installer GUI application."""

    # Colors
    BG = "#1a1a2e"
    BG_CARD = "#16213e"
    ACCENT = "#e94560"
    ACCENT_HOVER = "#ff6b81"
    TEXT = "#eaeaea"
    TEXT_DIM = "#a0a0b0"
    SUCCESS_GREEN = "#2ecc71"

    # Dimensions
    WIDTH = 580
    HEIGHT = 480

    def __init__(self):
        self.config = load_config()
        self.mode_key = self.config["mode"]
        self.mode = self.config["modes"][self.mode_key]

        self.root = tk.Tk()
        self.root.title("Sidebar Code Installer")
        self.root.geometry(f"{self.WIDTH}x{self.HEIGHT}")
        self.root.resizable(False, False)
        self.root.configure(bg=self.BG)

        # Center window on screen
        self.root.update_idletasks()
        x = (self.root.winfo_screenwidth() - self.WIDTH) // 2
        y = (self.root.winfo_screenheight() - self.HEIGHT) // 2
        self.root.geometry(f"+{x}+{y}")

        self._show_welcome()

    def _clear(self):
        """Remove all widgets from the root window."""
        for widget in self.root.winfo_children():
            widget.destroy()

    def _make_button(self, parent, text, command, bg=None, fg=None, width=20):
        """Create a styled button."""
        bg = bg or self.ACCENT
        fg = fg or self.TEXT
        btn = tk.Button(
            parent, text=text, command=command,
            bg=bg, fg=fg, activebackground=self.ACCENT_HOVER,
            activeforeground=self.TEXT, font=("Segoe UI", 12, "bold"),
            relief="flat", cursor="hand2", width=width, pady=8
        )
        return btn

    # ---- SCREEN 1: Welcome ----

    def _show_welcome(self):
        self._clear()
        frame = tk.Frame(self.root, bg=self.BG)
        frame.place(relx=0.5, rely=0.5, anchor="center")

        tk.Label(
            frame, text="Sidebar Code", font=("Segoe UI", 28, "bold"),
            fg=self.ACCENT, bg=self.BG
        ).pack(pady=(0, 4))

        tk.Label(
            frame, text="Installer", font=("Segoe UI", 18),
            fg=self.TEXT, bg=self.BG
        ).pack(pady=(0, 24))

        tk.Label(
            frame, text=self.mode["label"], font=("Segoe UI", 13),
            fg=self.TEXT_DIM, bg=self.BG
        ).pack(pady=(0, 4))

        tk.Label(
            frame, text=self.mode["description"],
            font=("Segoe UI", 10), fg=self.TEXT_DIM, bg=self.BG,
            wraplength=440
        ).pack(pady=(0, 30))

        skills_text = "Skills to install:  " + ", ".join(
            s.replace(".md", "") for s in self.mode["skills"]
        )
        tk.Label(
            frame, text=skills_text, font=("Segoe UI", 9),
            fg=self.TEXT_DIM, bg=self.BG, wraplength=440
        ).pack(pady=(0, 30))

        self._make_button(frame, "Install", self._run_install).pack()

    # ---- SCREEN 2: Installing / Result ----

    def _run_install(self):
        # Check Claude Code installation
        if not claude_code_is_installed():
            self._show_not_installed()
            return

        errors = []
        installed_files = []

        # Ensure ~/.claude/commands/ exists
        commands_dir = get_claude_commands_dir()
        try:
            commands_dir.mkdir(parents=True, exist_ok=True)
        except OSError as e:
            self._show_error(f"Could not create {commands_dir}:\n{e}")
            return

        # Copy skill files
        skills_source = get_resource_path("skills")
        for skill_file in self.mode["skills"]:
            src = skills_source / skill_file
            dst = commands_dir / skill_file
            try:
                shutil.copy2(str(src), str(dst))
                installed_files.append(skill_file)
            except Exception as e:
                errors.append(f"{skill_file}: {e}")

        # For Full Suite: handle CLAUDE_starter_template.md
        template_dest = None
        if self.mode.get("include_claude_template"):
            template_src = get_resource_path("skills") / "CLAUDE_starter_template.md"
            if template_src.exists():
                template_dest = self._ask_template_location(template_src)

        if errors:
            self._show_error("Some files failed to install:\n" + "\n".join(errors))
        else:
            self._show_success(installed_files, template_dest)

    def _ask_template_location(self, template_src: Path) -> str | None:
        """Prompt user for where to save the CLAUDE.md starter template."""
        dest_dir = filedialog.askdirectory(
            title="Choose a folder for CLAUDE_starter_template.md",
            initialdir=str(Path.home())
        )
        if not dest_dir:
            return None
        try:
            dst = Path(dest_dir) / "CLAUDE_starter_template.md"
            shutil.copy2(str(template_src), str(dst))
            return str(dst)
        except Exception:
            return None

    # ---- SCREEN: Claude Code Not Installed ----

    def _show_not_installed(self):
        self._clear()
        frame = tk.Frame(self.root, bg=self.BG)
        frame.place(relx=0.5, rely=0.5, anchor="center")

        tk.Label(
            frame, text="Claude Code Not Found",
            font=("Segoe UI", 22, "bold"), fg=self.ACCENT, bg=self.BG
        ).pack(pady=(0, 20))

        msg = (
            "Claude Code Desktop App was not detected on this machine.\n\n"
            "Please install Claude Code first, then run this installer again."
        )
        tk.Label(
            frame, text=msg, font=("Segoe UI", 11),
            fg=self.TEXT, bg=self.BG, wraplength=440, justify="center"
        ).pack(pady=(0, 20))

        link = "https://claude.ai/download"
        link_label = tk.Label(
            frame, text=link, font=("Segoe UI", 11, "underline"),
            fg="#5dade2", bg=self.BG, cursor="hand2"
        )
        link_label.pack(pady=(0, 30))
        link_label.bind("<Button-1>", lambda e: self._open_url(link))

        self._make_button(frame, "Close", self.root.destroy, bg="#444").pack()

    # ---- SCREEN: Success ----

    def _show_success(self, installed: list, template_dest: str | None):
        self._clear()
        frame = tk.Frame(self.root, bg=self.BG)
        frame.place(relx=0.5, rely=0.5, anchor="center")

        tk.Label(
            frame, text="Installation Complete",
            font=("Segoe UI", 24, "bold"), fg=self.SUCCESS_GREEN, bg=self.BG
        ).pack(pady=(0, 20))

        files_str = "\n".join(f"  {f}" for f in installed)
        tk.Label(
            frame, text=f"Installed to ~/.claude/commands/:\n{files_str}",
            font=("Segoe UI", 10), fg=self.TEXT_DIM, bg=self.BG,
            justify="left"
        ).pack(pady=(0, 12))

        if template_dest:
            tk.Label(
                frame, text=f"CLAUDE template saved to:\n  {template_dest}",
                font=("Segoe UI", 10), fg=self.TEXT_DIM, bg=self.BG,
                justify="left"
            ).pack(pady=(0, 12))

        tk.Label(
            frame,
            text='Open Claude Code and type  /  to see your new commands.',
            font=("Segoe UI", 12), fg=self.TEXT, bg=self.BG, wraplength=440
        ).pack(pady=(0, 30))

        self._make_button(
            frame, "Done", self.root.destroy,
            bg=self.SUCCESS_GREEN, fg="#1a1a2e"
        ).pack()

    # ---- SCREEN: Error ----

    def _show_error(self, message: str):
        self._clear()
        frame = tk.Frame(self.root, bg=self.BG)
        frame.place(relx=0.5, rely=0.5, anchor="center")

        tk.Label(
            frame, text="Installation Failed",
            font=("Segoe UI", 22, "bold"), fg=self.ACCENT, bg=self.BG
        ).pack(pady=(0, 20))

        tk.Label(
            frame, text=message, font=("Segoe UI", 10),
            fg=self.TEXT, bg=self.BG, wraplength=440, justify="left"
        ).pack(pady=(0, 30))

        self._make_button(frame, "Close", self.root.destroy, bg="#444").pack()

    @staticmethod
    def _open_url(url: str):
        """Open a URL in the default browser."""
        import webbrowser
        webbrowser.open(url)

    def run(self):
        self.root.mainloop()


if __name__ == "__main__":
    app = InstallerApp()
    app.run()
