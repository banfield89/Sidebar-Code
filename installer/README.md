# Sidebar Code Installer

One-click installer for Sidebar Code skill files targeting Claude Code Desktop App.

## What It Does

Copies Sidebar Code skill `.md` files to `~/.claude/commands/` so they appear as slash commands when the user types `/` in Claude Code.

## Two Configurations

Controlled by `installer_config.json` (bundled inside the EXE):

- **Parser Trial** (`sidebar-code-install-parser-trial.exe`): Installs only `pleading-parser.md`
- **Full Litigation Suite** (`sidebar-code-install-full-suite.exe`): Installs all 4 skills + optionally places `CLAUDE_starter_template.md` in a user-chosen directory

## Building

Requirements: Python 3.10+, PyInstaller

```bash
pip install pyinstaller

# Build both configurations
python build.py all

# Build only parser trial
python build.py parser_trial

# Build only full suite
python build.py full_suite
```

Output binaries land in `installer/dist/`.

## Tech Choice

Python + tkinter + PyInstaller. Chosen because:
- tkinter is built into Python (no extra dependencies)
- PyInstaller produces a single-file EXE (~11 MB vs Electron's 100+ MB)
- Same codebase works on macOS via PyInstaller with `--windowed` (produces `.app`)
- Simple GUI requirements (welcome, progress, success screens) fit tkinter

## File Structure

```
installer/
  sidebar_code_installer.py   # Main application
  installer_config.json        # Configuration (mode selection)
  build.py                     # Build script
  skills/                      # Bundled skill files (copied during build)
  dist/                        # Built binaries (gitignored)
  build/                       # PyInstaller work directory (gitignored)
```

## macOS Build

Run `python build.py all` on a Mac. PyInstaller will produce a `.app` bundle. To create a `.dmg`, use `hdiutil` or a tool like `create-dmg`:

```bash
# On macOS after building
hdiutil create -volname "Sidebar Code Installer" -srcfolder dist/sidebar-code-install-full-suite.app -ov -format UDZO dist/sidebar-code-install-full-suite.dmg
```
