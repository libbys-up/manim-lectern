"""The `lectern` command.

    lectern init [FOLDER]     set up a course folder (default: the current folder)
    lectern where             print where lectern's conventions, extras, and examples are
"""

import argparse
import shutil
import sys
from pathlib import Path

PACKAGE = Path(__file__).resolve().parent
TEMPLATE = PACKAGE / "templates" / "course"
FOLDERS = ["scripts", "lectures"]


def init(folder, force=False):
    """Copy the course template into `folder` and create scripts/ and lectures/.
    Existing files are left alone unless `force` is set."""
    folder = Path(folder)
    folder.mkdir(parents=True, exist_ok=True)
    created, skipped = [], []
    for src in sorted(TEMPLATE.iterdir()):
        dest = folder / src.name
        if dest.exists() and not force:
            skipped.append(src.name)
            continue
        shutil.copy2(src, dest)
        created.append(src.name)
    for name in FOLDERS:
        d = folder / name
        if not d.exists():
            d.mkdir()
            created.append(name + "/")
    if created:
        print(f"Created in {folder}: {', '.join(created)}")
    if skipped:
        print(f"Already there, left alone: {', '.join(skipped)} (use --force to replace them)")
    print("Next: write your course's rules in COURSE_CONVENTIONS.md, then a script in scripts/.")
    print("AGENTS.md tells an AI agent how to turn scripts into lectures.")


def where():
    """Print the paths an author or agent needs."""
    rows = [("lectern package", PACKAGE),
            ("script markup", PACKAGE / "conventions" / "SCRIPT_CONVENTIONS.md"),
            ("house style", PACKAGE / "conventions" / "STYLE.md")]
    for conv in sorted((PACKAGE / "extras").glob("**/CONVENTIONS.md")):
        rows.append(("extra " + conv.parent.relative_to(PACKAGE / "extras").as_posix(), conv))
    examples = PACKAGE.parent.parent / "examples"  # present in a clone of the repository
    if examples.is_dir():
        rows.append(("examples", examples))
    width = max(len(label) for label, _ in rows) + 2
    for label, path in rows:
        print(f"{label + ':':{width}s}{path}")


def main(argv=None):
    ap = argparse.ArgumentParser(prog="lectern", description="Animated lecture slides from plain-text scripts.")
    sub = ap.add_subparsers(dest="command", required=True)
    p = sub.add_parser("init", help="set up a course folder")
    p.add_argument("folder", nargs="?", default=".")
    p.add_argument("--force", action="store_true", help="replace template files that already exist")
    sub.add_parser("where", help="print where the conventions and extras are")
    args = ap.parse_args(argv)
    if args.command == "init":
        init(args.folder, args.force)
    elif args.command == "where":
        where()
    return 0


if __name__ == "__main__":
    sys.exit(main())
