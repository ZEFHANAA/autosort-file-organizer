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

class Color:
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    RED = "\033[91m"
    BLUE = "\033[94m"
    CYAN = "\033[96m"
    BOLD = "\033[1m"
    RESET = "\033[0m"

def get_category_for_extension(ext):
    """Determine category name based on file extension."""
    ext = ext.lower()
    for category, extensions in FILE_CATEGORIES.items():
        if ext in extensions:
            return category
    return FALLBACK_CATEGORY

def get_unique_path(destination_dir, filename):
    """Ensure unique destination path to avoid overwriting existing files."""
    name, ext = os.path.splitext(filename)
    counter = 1
    target_path = destination_dir / filename
    while target_path.exists():
        target_path = destination_dir / f"{name}_{counter}{ext}"
        counter += 1
    return target_path

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

def organize(target_path, dry_run=False):
    """Main organization logic."""
    target_dir = Path(target_path).resolve()

    if not target_dir.exists() or not target_dir.is_dir():
        print(f"{Color.RED}Error: Directory '{target_path}' does not exist!{Color.RESET}")
        return 0

    print(f"\n{Color.BOLD}{Color.CYAN}[AutoSort] — Smart File Organizer{Color.RESET}")
    print(f"Target Directory: {Color.YELLOW}{target_dir}{Color.RESET}")
    if dry_run:
        print(f"{Color.YELLOW}⚡ DRY RUN MODE ACTIVE (No files will actually be moved){Color.RESET}\n")

    moved_count = 0
    skipped_count = 0
    history = []
    category_summary = {}

    for item in target_dir.iterdir():
        # Ignore subdirectories and items in IGNORE_LIST
        if item.is_dir() or item.name in IGNORE_LIST or item.name.startswith("."):
            skipped_count += 1
            continue

        category = get_category_for_extension(item.suffix)
        category_dir = target_dir / category
        destination_path = get_unique_path(category_dir, item.name)

        category_summary[category] = category_summary.get(category, 0) + 1

        if dry_run:
            print(f" {Color.BLUE}[WOULD MOVE]{Color.RESET} {item.name} -> {category}/{destination_path.name}")
        else:
            category_dir.mkdir(exist_ok=True)
            shutil.move(str(item), str(destination_path))
            print(f" {Color.GREEN}[MOVED]{Color.RESET} {item.name} -> {category}/{destination_path.name}")
            
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
    
    if category_summary:
        print(f"\n{Color.BOLD}Category Breakdown:{Color.RESET}")
        for cat, cnt in category_summary.items():
            print(f"  * {cat:<15}: {cnt} file(s)")

    if not dry_run and history:
        all_history = load_history()
        all_history.append({
            "session_date": datetime.now().isoformat(),
            "target_dir": str(target_dir),
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


def watch(target_path, dry_run=False, interval=5):
    """Watch a folder and auto-organize whenever new files appear."""
    target_dir = Path(target_path).resolve()

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
        current = set(target_dir.iterdir())
        new_items = current - known

        if not new_items:
            continue

        new_files = [
            p for p in new_items
            if p.is_file() and p.name not in IGNORE_LIST and not p.name.startswith(".")
        ]
        if new_files:
            names = ", ".join(f.name for f in new_files)
            print(f"{Color.BLUE}[DETECTED]{Color.RESET} {len(new_files)} new file(s): {names}")
            organize(target_dir, dry_run=dry_run)

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

    args = parser.parse_args()

    if args.undo:
        undo_last()
    elif args.watch:
        try:
            watch(args.path, dry_run=args.dry_run, interval=args.interval)
        except KeyboardInterrupt:
            print(f"\n{Color.CYAN}✓ Watch stopped by user.{Color.RESET}")
    else:
        organize(args.path, dry_run=args.dry_run)

if __name__ == "__main__":
    main()
