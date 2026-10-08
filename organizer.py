import os
import sys
import time
import shutil
import json
import argparse
from pathlib import Path
from datetime import datetime

# Configure UTF-8 encoding for Windows terminals
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

from config import FILE_CATEGORIES, IGNORE_LIST, FALLBACK_CATEGORY

HISTORY_FILE = "history.json"

def load_custom_config(path):
    """Load a user-supplied JSON config with custom categories.

    Accepted shape (all keys optional, unknown keys ignored):
        {
          "categories": {"MyCategory": [".foo", ".bar"]},
          "ignore": ["sample.txt"],
          "fallback": "Misc"
        }

    Custom categories are merged on top of the defaults, so a small
    config only needs to declare what it wants to add or override.
    Returns (file_categories, ignore_list, fallback).
    """
    categories = {k: list(v) for k, v in FILE_CATEGORIES.items()}
    ignore_list = list(IGNORE_LIST)
    fallback = FALLBACK_CATEGORY

    cfg_path = Path(path)
    if not cfg_path.exists():
        print(f"{Color.RED}Error: Config file not found: '{path}'{Color.RESET}")
        sys.exit(2)

    try:
        with open(cfg_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        print(f"{Color.RED}Error: Config file is not valid JSON: {e}{Color.RESET}")
        sys.exit(2)

    if not isinstance(data, dict):
        print(f"{Color.RED}Error: Config root must be a JSON object.{{Color.RESET}}")
        sys.exit(2)

    custom_categories = data.get("categories")
    if custom_categories is not None:
        if not isinstance(custom_categories, dict):
            print(f"{Color.RED}Error: 'categories' must be an object of name -> extension list.{Color.RESET}")
            sys.exit(2)
        for name, extensions in custom_categories.items():
            if not isinstance(extensions, list) or not all(
                isinstance(x, str) for x in extensions
            ):
                print(f"{Color.RED}Error: Category '{name}' must map to a list of extension strings.{Color.RESET}")
                sys.exit(2)
            normalized = [
                x if x.startswith(".") else f".{x}" for x in
                (str(e).lower() for e in extensions)
            ]
            categories[str(name)] = normalized

    custom_ignore = data.get("ignore")
    if custom_ignore is not None:
        if not isinstance(custom_ignore, list) or not all(isinstance(x, str) for x in custom_ignore):
            print(f"{Color.RED}Error: 'ignore' must be a list of strings.{Color.RESET}")
            sys.exit(2)
        ignore_list.extend(custom_ignore)

    custom_fallback = data.get("fallback")
    if custom_fallback is not None:
        if not isinstance(custom_fallback, str):
            print(f"{Color.RED}Error: 'fallback' must be a string.{Color.RESET}")
            sys.exit(2)
        fallback = custom_fallback

    return categories, ignore_list, fallback

class Color:
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    RED = "\033[91m"
    BLUE = "\033[94m"
    CYAN = "\033[96m"
    BOLD = "\033[1m"
    RESET = "\033[0m"

def custom_rules_used(categories, ignore_list, fallback):
    """Check whether a loaded config differs from the built-in defaults."""
    return (
        categories is not FILE_CATEGORIES
        or ignore_list is not IGNORE_LIST
        or fallback != FALLBACK_CATEGORY
    )

def get_category_for_extension(ext, categories=None, fallback=None):
    """Determine category name based on file extension."""
    categories = categories if categories is not None else FILE_CATEGORIES
    fallback = fallback if fallback is not None else FALLBACK_CATEGORY
    ext = ext.lower()
    for category, extensions in categories.items():
        if ext in extensions:
            return category
    return fallback

def human_size(num_bytes):
    """Convert bytes to a human-readable string."""
    size = float(num_bytes)
    for unit in ("B", "KB", "MB", "GB"):
        if size < 1024 or unit == "GB":
            return f"{size:.1f}{unit}" if unit != "B" else f"{int(size)}B"
        size /= 1024

def get_date_subfolder(mtime_ts, fmt="%Y-%m"):
    """Return a date subfolder name from a modification timestamp."""
    return datetime.fromtimestamp(mtime_ts).strftime(fmt)

def get_unique_path(destination_dir, filename):
    """Ensure unique destination path to avoid overwriting existing files."""
    name, ext = os.path.splitext(filename)
    counter = 1
    target_path = destination_dir / filename
    while target_path.exists():
        target_path = destination_dir / f"{name}_{counter}{ext}"
        counter += 1
    return target_path

def _looks_like_date_folder(name):
    """True for YYYY-MM folders created by --sort-by date."""
    return (
        len(name) == 7 and name[4] == "-"
        and name[:4].isdigit() and name[5:7].isdigit()
    )

def iter_target_files(target_dir, ignore_list=None, categories=None,
                      fallback=None, recursive=False, exclude_patterns=None):
    """Yield the files to organize.

    Default: only files directly inside target_dir.
    With recursive=True: every file in the tree, except files that already
    sit inside destination folders (category / YYYY-MM dirs at the top
    level), so repeated runs do not shuffle files back out of place.

    exclude_patterns: fnmatch-style patterns matched against file names
    (e.g. "*.tmp", "report_*.pdf"). Matching files are skipped.
    """
    import fnmatch
    ignore_list = ignore_list if ignore_list is not None else IGNORE_LIST
    exclude_patterns = list(exclude_patterns or [])

    def _excluded(name):
        return any(fnmatch.fnmatch(name, p) for p in exclude_patterns)

    if not recursive:
        for item in target_dir.iterdir():
            if item.is_file() and item.name not in ignore_list \
                    and not item.name.startswith(".") \
                    and not _excluded(item.name):
                yield item
        return

    destinations = set(categories if categories is not None else FILE_CATEGORIES)
    if fallback:
        destinations.add(fallback)
    for dirpath, dirnames, filenames in os.walk(target_dir):
        if Path(dirpath) == target_dir:
            dirnames[:] = [
                d for d in dirnames
                if not d.startswith(".")
                and d not in destinations
                and not _looks_like_date_folder(d)
            ]
        else:
            dirnames[:] = [d for d in dirnames if not d.startswith(".")]
        for name in filenames:
            if name in ignore_list or name.startswith(".") or _excluded(name):
                continue
            yield Path(dirpath) / name

def load_history():
    """Load transaction history for undo functionality."""
    if os.path.exists(HISTORY_FILE):
        try:
            with open(HISTORY_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return []
    return []

def save_history(history_data):
    """Save transaction history to JSON."""
    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(history_data, f, indent=2)

def organize(target_path, dry_run=False, sort_by="category", categories=None,
             ignore_list=None, fallback=None, recursive=False,
             exclude_patterns=None, quiet=False):
    """Main organization logic."""
    # In quiet mode, capture verbose prints and keep only the summary lines.
    import io
    import contextlib

    # Quiet mode: run the implementation with stdout captured and only
    # echo the summary lines back to the real stdout.
    if quiet:
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            result = _organize_impl(target_path, dry_run, sort_by, categories,
                                    ignore_list, fallback, recursive,
                                    exclude_patterns)
        for line in buf.getvalue().splitlines():
            if ("SUMMARY" in line or "Total" in line or "Category Breakdown" in line
                    or line.lstrip().startswith("*") or "Session saved" in line):
                print(line)
        return result
    return _organize_impl(target_path, dry_run, sort_by, categories,
                          ignore_list, fallback, recursive, exclude_patterns)


def _organize_impl(target_path, dry_run=False, sort_by="category", categories=None,
                   ignore_list=None, fallback=None, recursive=False,
                   exclude_patterns=None):
    """Implementation of organize(); see organize() for public signature."""
    target_dir = Path(target_path).resolve()
    categories = categories if categories is not None else FILE_CATEGORIES
    ignore_list = ignore_list if ignore_list is not None else IGNORE_LIST
    fallback = fallback if fallback is not None else FALLBACK_CATEGORY

    if not target_dir.exists() or not target_dir.is_dir():
        print(f"{Color.RED}Error: Directory '{target_path}' does not exist!{Color.RESET}")
        return 0

    print(f"\n{Color.BOLD}{Color.CYAN}[AutoSort] — Smart File Organizer{Color.RESET}")
    print(f"Target Directory: {Color.YELLOW}{target_dir}{Color.RESET}")
    print(f"Sort Mode      : {sort_by}")
    if custom_rules_used(categories, ignore_list, fallback):
        print(f"Config         : {Color.CYAN}custom rules active{Color.RESET}")
    if dry_run:
        print(f"{Color.YELLOW}⚡ DRY RUN MODE ACTIVE (No files will actually be moved){Color.RESET}\n")

    moved_count = 0
    skipped_count = 0
    history = []
    category_summary = {}
    total_bytes = 0

    if recursive:
        print(f"{Color.CYAN}Recursive      : yes (subfolders included){Color.RESET}")

    files = list(iter_target_files(target_dir, ignore_list, categories,
                                   fallback, recursive=recursive,
                                   exclude_patterns=exclude_patterns))
    if not recursive:
        skipped_count = sum(
            1 for item in target_dir.iterdir()
            if item.is_dir() or item.name in ignore_list or item.name.startswith(".")
        )

    for item in files:
        if sort_by == "date":
            rel_destination = get_date_subfolder(item.stat().st_mtime)
            destination_dir = target_dir / rel_destination
        else:
            category = get_category_for_extension(item.suffix, categories, fallback)
            rel_destination = category
            destination_dir = target_dir / category

        destination_path = get_unique_path(destination_dir, item.name)

        category_summary[rel_destination] = category_summary.get(rel_destination, 0) + 1
        try:
            total_bytes += item.stat().st_size
        except OSError:
            pass

        if dry_run:
            print(f" {Color.BLUE}[WOULD MOVE]{Color.RESET} {item.name} -> {rel_destination}/{destination_path.name}")
        else:
            destination_dir.mkdir(parents=True, exist_ok=True)
            shutil.move(str(item), str(destination_path))
            print(f" {Color.GREEN}[MOVED]{Color.RESET} {item.name} -> {rel_destination}/{destination_path.name}")

            history.append({
                "original": str(item),
                "moved_to": str(destination_path),
                "timestamp": datetime.now().isoformat()
            })

        moved_count += 1

    # Print Summary
    print(f"\n{Color.BOLD}---------------- SUMMARY ----------------{Color.RESET}")
    print(f"Total Processed : {moved_count + skipped_count}")
    print(f"Total Moved     : {Color.GREEN}{moved_count}{Color.RESET}")
    print(f"Total Skipped   : {skipped_count}")
    if moved_count:
        print(f"Total Size      : {human_size(total_bytes)}")

    if category_summary:
        print(f"\n{Color.BOLD}Category Breakdown:{Color.RESET}")
        for cat, cnt in category_summary.items():
            print(f"  * {cat:<15}: {cnt} file(s)")

    if not dry_run and history:
        all_history = load_history()
        all_history.append({
            "session_date": datetime.now().isoformat(),
            "target_dir": str(target_dir),
            "sort_by": sort_by,
            "moves": history
        })
        save_history(all_history)
        print(f"\n{Color.CYAN}✓ Session saved to history.json (Use '--undo' to revert){Color.RESET}")

def undo_last():
    """Undo the most recent organization session."""
    all_history = load_history()
    if not all_history:
        print(f"{Color.YELLOW}No history found to undo.{Color.RESET}")
        return

    last_session = all_history.pop()
    moves = last_session.get("moves", [])

    print(f"\n{Color.BOLD}{Color.YELLOW}↺ Reverting Last Session ({last_session.get('session_date')}){Color.RESET}")
    
    reverted = 0
    for record in reversed(moves):
        current_path = Path(record["moved_to"])
        original_path = Path(record["original"])

        if current_path.exists():
            original_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(current_path), str(original_path))
            print(f" {Color.GREEN}[RESTORED]{Color.RESET} {current_path.name} -> {original_path}")
            reverted += 1
        else:
            print(f" {Color.RED}[MISSING]{Color.RESET} Could not find {current_path}")

    save_history(all_history)
    print(f"\n{Color.GREEN}✓ Reverted {reverted} file(s) successfully.{Color.RESET}")


def clean_empty(target_path, dry_run=False):
    """Remove empty directories left behind by organize/undo."""
    target_dir = Path(target_path).resolve()

    if not target_dir.exists() or not target_dir.is_dir():
        print(f"{Color.RED}Error: Directory '{target_path}' does not exist!{Color.RESET}")
        return

    print(f"\n{Color.BOLD}{Color.CYAN}[AutoSort] — Clean Empty Folders{Color.RESET}")
    print(f"Target Directory: {Color.YELLOW}{target_dir}{Color.RESET}")
    if dry_run:
        print(f"{Color.YELLOW}⚡ DRY RUN MODE ACTIVE (No folders will be removed){Color.RESET}\n")

    removed = 0
    # Walk bottom-up so nested empty dirs are caught after their children.
    for dirpath, dirnames, _filenames in os.walk(str(target_dir), topdown=False):
        d = Path(dirpath)
        if d == target_dir:
            continue
        try:
            if not any(d.iterdir()):
                if dry_run:
                    print(f" {Color.BLUE}[WOULD REMOVE]{Color.RESET} {d.relative_to(target_dir)}/")
                else:
                    d.rmdir()
                    print(f" {Color.GREEN}[REMOVED]{Color.RESET} {d.relative_to(target_dir)}/")
                removed += 1
        except OSError:
            pass

    print(f"\n{Color.GREEN}✓ Removed {removed} empty folder(s).{Color.RESET}")


def watch(target_path, dry_run=False, interval=5, sort_by="category",
          categories=None, ignore_list=None, fallback=None, recursive=False,
          exclude_patterns=None, quiet=False):
    """Watch a folder and auto-organize whenever new files appear."""
    target_dir = Path(target_path).resolve()
    ignore_filter = ignore_list if ignore_list is not None else IGNORE_LIST

    if not target_dir.exists() or not target_dir.is_dir():
        print(f"{Color.RED}Error: Directory '{target_path}' does not exist!{Color.RESET}")
        return

    print(f"{Color.BOLD}{Color.CYAN}AutoSort Watch Mode{Color.RESET}")
    print(f"Watching: {Color.YELLOW}{target_dir}{Color.RESET}")
    print(f"Interval: {interval}s (press Ctrl+C to stop)")
    if dry_run:
        print(f"{Color.YELLOW}⚡ DRY RUN — no files will be moved{Color.RESET}")
    print()

    known = set(target_dir.iterdir())
    print(f"{Color.CYAN}✓ Initialized. {len(known)} items already present.{Color.RESET}")

    while True:
        time.sleep(interval)
        try:
            current = set(target_dir.iterdir())
        except FileNotFoundError:
            print(f"\n{Color.RED}Error: Watched folder was removed: {target_dir}{Color.RESET}")
            print(f"{Color.YELLOW}Stopping watch mode.{Color.RESET}")
            return
        new_items = current - known

        if not new_items:
            continue

        new_files = [
            p for p in new_items
            if p.is_file() and p.name not in ignore_filter and not p.name.startswith(".")
        ]
        if new_files:
            names = ", ".join(f.name for f in new_files)
            print(f"{Color.BLUE}[DETECTED]{Color.RESET} {len(new_files)} new file(s): {names}")
            organize(target_dir, dry_run=dry_run, sort_by=sort_by,
                     categories=categories, ignore_list=ignore_list,
                     fallback=fallback, recursive=recursive,
                     exclude_patterns=exclude_patterns, quiet=quiet)

        known = current


def main():
    parser = argparse.ArgumentParser(
        description="AutoSort — Smart File Organizer for Downloads & Messy Folders"
    )
    parser.add_argument(
        "path",
        nargs="?",
        default=".",
        help="Path to folder to organize (default: current directory)"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview file moves without modifying files"
    )
    parser.add_argument(
        "--undo",
        action="store_true",
        help="Undo the last organize session"
    )
    parser.add_argument(
        "--clean-empty",
        action="store_true",
        help="Remove empty category/date folders left behind (safe with --dry-run)"
    )
    parser.add_argument(
        "--watch",
        action="store_true",
        help="Continuously watch the folder and auto-organize new files"
    )
    parser.add_argument(
        "--interval",
        type=int,
        default=5,
        metavar="SECONDS",
        help="Polling interval for --watch mode (default: 5 seconds)"
    )
    parser.add_argument(
        "--sort-by",
        choices=["category", "date"],
        default="category",
        help="Organize by file category (default) or modification date (YYYY-MM)"
    )
    parser.add_argument(
        "--recursive",
        action="store_true",
        help="Also organize files inside subfolders (category folders are left alone)"
    )
    parser.add_argument(
        "--exclude",
        action="append",
        default=[],
        metavar="PATTERN",
        help="Skip files matching a glob pattern, e.g. --exclude '*.tmp' (repeatable)"
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Only print the final summary (no per-file output)"
    )
    parser.add_argument(
        "--config",
        metavar="FILE",
        default=None,
        help="Path to a JSON config with custom category rules, ignore list, and fallback"
    )

    args = parser.parse_args()

    categories = ignore_list = fallback = None
    if args.config:
        categories, ignore_list, fallback = load_custom_config(args.config)

    if args.undo:
        undo_last()
    elif args.clean_empty:
        clean_empty(args.path, dry_run=args.dry_run)
    elif args.watch:
        try:
            watch(args.path, dry_run=args.dry_run, interval=args.interval,
                  sort_by=args.sort_by, categories=categories,
                  ignore_list=ignore_list, fallback=fallback,
                  recursive=args.recursive, exclude_patterns=args.exclude,
                  quiet=args.quiet)
        except KeyboardInterrupt:
            print(f"\n{Color.CYAN}✓ Watch stopped by user.{Color.RESET}")
    else:
        organize(args.path, dry_run=args.dry_run, sort_by=args.sort_by,
                 categories=categories, ignore_list=ignore_list,
                 fallback=fallback, recursive=args.recursive,
                 exclude_patterns=args.exclude, quiet=args.quiet)

if __name__ == "__main__":
    main()
