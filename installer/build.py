"""
Build script for Sidebar Code Installer.
Produces a single-file EXE (Windows) or app (macOS) via PyInstaller.

Usage:
    python build.py                  # Builds full_suite config
    python build.py parser_trial     # Builds parser_trial config
    python build.py full_suite       # Builds full_suite config
    python build.py all              # Builds both configs
"""

import json
import os
import platform
import shutil
import subprocess
import sys
from pathlib import Path

INSTALLER_DIR = Path(__file__).parent
SKILLS_SRC = (
    INSTALLER_DIR.parent
    / "Firm Prompts Content"
    / "Skills Dat Pay da Bills"
    / "General Litigation"
)

SKILL_FILES = [
    "pleading-parser.md",
    "deposition-prep.md",
    "oral-argument-prep.md",
    "motion-drafting.md",
]

TEMPLATE_SRC = (
    INSTALLER_DIR.parent
    / "Product Catalog"
    / "products"
    / "02_full_litigation_suite"
    / "_customer_deliverables"
    / "claude_md_starter"
    / "CLAUDE_starter_template.md"
)


def copy_skills_to_bundle():
    """Copy skill .md files into installer/skills/ for bundling."""
    skills_dir = INSTALLER_DIR / "skills"
    skills_dir.mkdir(exist_ok=True)

    for skill in SKILL_FILES:
        src = SKILLS_SRC / skill
        if src.exists():
            shutil.copy2(str(src), str(skills_dir / skill))
            print(f"  Copied {skill}")
        else:
            print(f"  WARNING: {skill} not found at {src}")

    # Copy CLAUDE_starter_template.md if it exists
    if TEMPLATE_SRC.exists():
        shutil.copy2(str(TEMPLATE_SRC), str(skills_dir / "CLAUDE_starter_template.md"))
        print("  Copied CLAUDE_starter_template.md")
    else:
        print(f"  NOTE: CLAUDE_starter_template.md not found at {TEMPLATE_SRC}")
        print("        Full Suite will install without the template.")


def build_exe(mode: str):
    """Run PyInstaller to produce a single-file executable."""
    print(f"\n--- Building {mode} ---")

    # Update config to set the mode
    config_path = INSTALLER_DIR / "installer_config.json"
    with open(config_path, "r", encoding="utf-8") as f:
        config = json.load(f)
    config["mode"] = mode
    with open(config_path, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2)

    exe_name = f"sidebar-code-install-{mode.replace('_', '-')}"

    sep = ";" if platform.system() == "Windows" else ":"
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--onefile",
        "--windowed",
        "--name", exe_name,
        "--add-data", f"skills{os.sep}*{sep}skills",
        "--add-data", f"installer_config.json{sep}.",
        "--clean",
        str(INSTALLER_DIR / "sidebar_code_installer.py"),
    ]

    print(f"  Running: {' '.join(cmd)}")
    result = subprocess.run(cmd, cwd=str(INSTALLER_DIR))

    if result.returncode == 0:
        dist_dir = INSTALLER_DIR / "dist"
        print(f"  SUCCESS: Binary in {dist_dir}")
        # Show file size
        for f in dist_dir.iterdir():
            if exe_name in f.name:
                size_mb = f.stat().st_size / (1024 * 1024)
                print(f"  {f.name}: {size_mb:.1f} MB")
    else:
        print(f"  FAILED with return code {result.returncode}")

    return result.returncode


if __name__ == "__main__":
    target = sys.argv[1] if len(sys.argv) > 1 else "full_suite"

    print("=== Sidebar Code Installer Build ===\n")

    print("Step 1: Copying skill files to bundle directory...")
    copy_skills_to_bundle()

    if target == "all":
        modes = ["parser_trial", "full_suite"]
    else:
        modes = [target]

    print(f"\nStep 2: Building installer(s): {modes}")
    for mode in modes:
        rc = build_exe(mode)
        if rc != 0:
            print(f"\nBuild failed for {mode}. Stopping.")
            sys.exit(1)

    print("\n=== Build Complete ===")
