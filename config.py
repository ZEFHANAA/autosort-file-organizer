"""
AutoSort Configuration File
Defines category rules, file extension mappings, and ignored files.
"""

# File category extension mappings
FILE_CATEGORIES = {
    "Images": [
        ".jpg", ".jpeg", ".png", ".gif", ".svg", ".webp", ".bmp", ".ico", ".tiff", ".raw", ".heic"
    ],
    "Documents": [
        ".pdf", ".docx", ".doc", ".txt", ".rtf", ".odt", ".epub", ".pages", ".md"
    ],
    "Spreadsheets": [
        ".xlsx", ".xls", ".csv", ".ods", ".numbers"
    ],
    "Presentations": [
        ".pptx", ".ppt", ".key"
    ],
    "Videos": [
        ".mp4", ".mkv", ".avi", ".mov", ".wmv", ".flv", ".webm", ".m4v"
    ],
    "Audio": [
        ".mp3", ".wav", ".flac", ".aac", ".m4a", ".ogg", ".wma"
    ],
    "Archives": [
        ".zip", ".rar", ".7z", ".tar", ".gz", ".bz2", ".iso"
    ],
    "Programs": [
        ".exe", ".msi", ".bat", ".cmd", ".ps1", ".apk", ".dmg", ".deb", ".appimage"
    ],
    "Code_and_Data": [
        ".py", ".js", ".ts", ".html", ".css", ".json", ".xml", ".sql", ".java", ".cpp", ".c", ".php", ".rb"
    ]
}

# Files or folders to ignore during sorting
IGNORE_LIST = [
    "organizer.py",
    "config.py",
    "README.md",
    ".gitignore",
    ".git",
    "history.json",
    "desktop.ini",
    ".DS_Store"
]

# Fallback category for unknown extensions
FALLBACK_CATEGORY = "Others"
