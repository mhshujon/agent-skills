#!/usr/bin/env python3
"""
Package a skill into a .skill file.

Usage:
    python scripts/package.py <skill-name>
    python scripts/package.py --list

Examples:
    python scripts/package.py wordpress-coding-standards
    python scripts/package.py --list

Output:
    <skill-name>.skill (in the repo root)

Requirements:
    Python 3.8+
    No external dependencies
"""

import argparse
import os
import sys
import zipfile
from pathlib import Path


EXCLUDE_DIRS = {
    ".git",
    "__pycache__",
    ".vscode",
    ".idea",
    "node_modules",
    "vendor",
}

EXCLUDE_FILES = {
    "README.md",
    "CONTRIBUTING.md",
    "LICENSE",
    ".gitignore",
    ".DS_Store",
    "Thumbs.db",
}

EXCLUDE_EXTENSIONS = {".pyc", ".pyo", ".pyd", ".skill", ".zip"}


def find_skills(skills_dir: Path) -> list[str]:
    """Return sorted list of skill names found in the skills directory."""
    if not skills_dir.is_dir():
        return []
    return sorted(
        d.name for d in skills_dir.iterdir()
        if d.is_dir() and not d.name.startswith(".")
    )


def package_skill(skill_name: str, skills_dir: Path, output_dir: Path) -> bool:
    skill_dir = skills_dir / skill_name
    if not skill_dir.is_dir():
        print(f"Error: skill '{skill_name}' not found in {skills_dir}")
        return False

    output_file = output_dir / f"{skill_name}.skill"

    print(f"Packaging '{skill_name}' from {skill_dir}")

    try:
        with zipfile.ZipFile(output_file, "w", zipfile.ZIP_DEFLATED) as zipf:
            for root, dirs, files in os.walk(skill_dir):
                dirs[:] = [
                    d for d in dirs
                    if d not in EXCLUDE_DIRS and not d.startswith(".")
                ]

                for file in files:
                    if file.startswith("."):
                        continue
                    if file in EXCLUDE_FILES:
                        continue
                    if Path(file).suffix in EXCLUDE_EXTENSIONS:
                        continue

                    file_path = Path(root) / file
                    arcname = f"{skill_name}/{file_path.relative_to(skill_dir)}"
                    zipf.write(file_path, arcname)
                    print(f"  + {arcname}")

        size_kb = output_file.stat().st_size / 1024
        print(f"\nOutput: {output_file}  ({size_kb:.1f} KB)")
        print("\nNext steps:")
        print("  1. Claude Desktop: Settings → Customize → Skills → + → Upload a skill")
        print("  2. Claude.ai:       Same location in claude.ai")

    except Exception as e:
        print(f"Error: {e}")
        return False

    return True


def main() -> int:
    script_dir = Path(__file__).parent
    repo_root = script_dir.parent
    skills_dir = repo_root / "skills"

    parser = argparse.ArgumentParser(
        description="Package a skill folder into a .skill file.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "skill",
        nargs="?",
        help="Name of the skill to package (subdirectory of skills/)",
    )
    parser.add_argument(
        "--list", "-l",
        action="store_true",
        help="List available skills and exit",
    )
    parser.add_argument(
        "--output", "-o",
        type=Path,
        default=repo_root,
        metavar="DIR",
        help="Directory to write the .skill file (default: repo root)",
    )

    args = parser.parse_args()

    available = find_skills(skills_dir)

    if args.list:
        if not available:
            print(f"No skills found in {skills_dir}")
        else:
            print("Available skills:")
            for name in available:
                print(f"  {name}")
        return 0

    if not args.skill:
        parser.print_help()
        if available:
            print(f"\nAvailable skills: {', '.join(available)}")
        return 1

    return 0 if package_skill(args.skill, skills_dir, args.output) else 1


if __name__ == "__main__":
    sys.exit(main())
