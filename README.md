# 📂 AutoSort — Smart File Organizer Script

[![Python](https://img.shields.io/badge/Python-3.8+-3776AB?style=flat&logo=python&logoColor=white)](https://python.org)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![CLI](https://img.shields.io/badge/Interface-CLI-black?style=flat&logo=windows-terminal)](https://github.com/ZEFHANAA/autosort)

**AutoSort** is an open-source Python automation tool designed to clean up messy folders (such as `Downloads` or `Desktop`) by automatically sorting files into categorized directories based on file extensions.

It includes **Dry-Run Preview Mode** (to simulate moves safely) and **Session Undo Support** (to revert any organization with a single command).

---

## ✨ Features

- 📁 **Smart File Categorization**: Automatically groups files into `Images`, `Documents`, `Spreadsheets`, `Presentations`, `Videos`, `Audio`, `Archives`, `Programs`, and `Code_and_Data`.
- ⚡ **Dry-Run Preview (`--dry-run`)**: Preview where files will be moved before making any actual file system changes.
- ↺ **Full Undo Support (`--undo`)**: Easily revert the previous organization session and restore files to their exact original locations.
- 🛡️ **Conflict Resolution**: Safely renames duplicate filenames instead of overwriting existing files.
- ⚙️ **Configurable Rules (`config.py`)**: Customize file categories, extensions, and ignore rules effortlessly.
- 🚀 **Zero External Dependencies**: Built entirely using Python's standard library (`os`, `shutil`, `argparse`, `pathlib`, `json`).

---

## 🛠️ Usage & Commands

### 1. Organize Current Folder
```bash
python organizer.py
```

### 2. Organize a Specific Folder (e.g. Downloads)
```bash
python organizer.py C:\Users\YourUsername\Downloads
```

### 3. Dry-Run Preview Mode (Simulate without moving)
```bash
python organizer.py C:\Users\YourUsername\Downloads --dry-run
```

### 4. Undo Last Organization Session
```bash
python organizer.py --undo
```

---

## 📂 Project Structure

```
autosort/
├── organizer.py      # Core CLI logic and file movement engine
├── config.py         # Category rules, extension mappings, and ignore lists
├── README.md         # Documentation
└── .gitignore        # Git ignore config
```

---

## ⚙️ Customization (`config.py`)

You can edit `config.py` to add custom file categories or extensions:

```python
FILE_CATEGORIES = {
    "Design_Files": [".psd", ".ai", ".fig", ".xd"],
    "Ebooks": [".pdf", ".epub", ".mobi"]
}
```

---

## 📄 License

Distributed under the MIT License. See `LICENSE` for details.

Built with ❤️ by **[@ZEFHANAA](https://github.com/ZEFHANAA)**
