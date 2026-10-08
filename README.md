# 📂 AutoSort — Smart File Organizer Script

[![Python](https://img.shields.io/badge/Python-3.9+-3776AB?style=flat&logo=python&logoColor=white)](https://python.org)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Tests](https://github.com/ZEFHANAA/autosort-file-organizer/actions/workflows/tests.yml/badge.svg)](https://github.com/ZEFHANAA/autosort-file-organizer/actions/workflows/tests.yml)

**AutoSort** is an open-source Python automation tool designed to clean up messy folders (such as `Downloads` or `Desktop`) by automatically sorting files into categorized directories based on file extensions.

It includes **Dry-Run Preview Mode** (to simulate moves safely) and **Session Undo Support** (to revert any organization with a single command).

---

## ✨ Features

- 📁 **Smart File Categorization**: Automatically groups files into `Images`, `Documents`, `Spreadsheets`, `Presentations`, `Videos`, `Audio`, `Archives`, `Programs`, and `Code_and_Data`.
- ⚡ **Dry-Run Preview (`--dry-run`)**: Preview where files will be moved before making any actual file system changes.
- ↺ **Full Undo Support (`--undo`)**: Easily revert the previous organization session and restore files to their exact original locations.
- 🛡️ **Conflict Resolution**: Safely renames duplicate filenames instead of overwriting existing files.
- 📅 **Sort by Date (`--sort-by date`)**: Group files into `YYYY-MM` folders by modification time instead of category.
- 👀 **Watch Mode (`--watch`)**: Continuously monitor a folder and auto-organize new files as they appear.
- 🌳 **Recursive Mode (`--recursive`)**: Also organize files inside subfolders (already-sorted category folders are left alone, so re-runs stay idempotent).
- 🚫 **Exclusions (`--exclude`)**: Skip files matching glob patterns like `*.tmp` or `draft_*` (repeatable).
- 🤫 **Quiet Mode (`--quiet`)**: Print only the final summary — ideal for cron jobs and scripts.
- ⚙️ **Custom Rules (`--config`)**: Load category rules, ignore lists, and a custom fallback from a JSON file, without editing `config.py`.
- 🧹 **Clean Empty (`--clean-empty`)**: Remove empty category/date folders left behind by organize or undo.
- 📋 **List Categories (`--list-categories`)**: Inspect the active category → extension mapping (including custom rules) before you run.
- 🚀 **Zero External Dependencies**: Built entirely using Python's standard library (`os`, `shutil`, `argparse`, `pathlib`, `json`, `fnmatch`).

---

## 📦 Installation

Run it directly (no install needed):

```bash
python organizer.py --help
```

Or install as a CLI command:

```bash
pip install .
autosort --help
```

---

## 🛠️ Usage & Commands

### 1. Organize Current Folder
```bash
python organizer.py
```

### 2. Organize a Specific Folder (e.g. Downloads)
```bash
python organizer.py ~/Downloads
```

### 3. Dry-Run Preview Mode (Simulate without moving)
```bash
python organizer.py ~/Downloads --dry-run
```

### 4. Undo Last Organization Session
```bash
python organizer.py --undo
```

### 5. Sort by Modification Date (`YYYY-MM` folders)
```bash
python organizer.py ~/Downloads --sort-by date
```

### 6. Include Subfolders (Recursive)
```bash
python organizer.py ~/Downloads --recursive
```

### 7. Exclude Files by Pattern
```bash
python organizer.py ~/Downloads --exclude '*.tmp' --exclude 'draft_*'
```

### 8. Summary-Only Output (Quiet)
```bash
python organizer.py ~/Downloads --quiet
```

### 9. Watch a Folder for New Files
```bash
python organizer.py ~/Downloads --watch --interval 10
```

### 10. Use a Custom Rules File
```bash
python organizer.py ~/Downloads --config rules.json
```

### 11. Preview Active Categories
```bash
python organizer.py --list-categories
python organizer.py --config rules.json --list-categories
```

### 12. Remove Empty Leftover Folders
```bash
python organizer.py ~/Downloads --clean-empty
```

### 13. Show Version
```bash
python organizer.py --version
```

All flags can be combined, e.g. `python organizer.py ~/Downloads --recursive --exclude '*.crdownload' --dry-run`.

---

## ⚙️ Custom Rules (`--config`)

Instead of editing `config.py`, pass a JSON file with only what you want to add or override:

```json
{
  "categories": {
    "Design_Files": [".psd", ".ai", ".fig"],
    "Ebooks": [".epub", ".mobi"]
  },
  "ignore": ["sample.txt"],
  "fallback": "Misc"
}
```

Custom categories are merged on top of the built-in defaults. Verify the result first with `--list-categories`.

---

## 🧪 Tests

AutoSort ships with a standard-library-only unit test suite (33 tests):

```bash
python -m unittest tests/test_autosort.py -v
```

The suite also runs automatically on every push and pull request via GitHub Actions.

---

## 📂 Project Structure

```
autosort-file-organizer/
├── organizer.py             # Core CLI logic and file movement engine
├── config.py                # Category rules, extension mappings, and ignore lists
├── tests/
│   └── test_autosort.py     # Stdlib unittest suite
├── .github/workflows/
│   └── tests.yml            # CI: run the test suite on every push/PR
├── pyproject.toml           # Packaging (installable as 'autosort' CLI)
├── README.md                # Documentation
└── LICENSE                  # MIT
```

---

## 📄 License

Distributed under the MIT License. See `LICENSE` for details.

Built with ❤️ by **[@ZEFHANAA](https://github.com/ZEFHANAA)**
