# Contributing to AutoSort

Thanks for your interest in improving AutoSort! 🎉

AutoSort is intentionally **zero-dependency** — everything runs on the Python standard library. Please keep it that way.

## Getting Started

1. **Fork & clone**

   ```bash
   git clone https://github.com/<your-username>/autosort-file-organizer.git
   cd autosort-file-organizer
   ```

2. **Create a branch** for your change

   ```bash
   git checkout -b feat/my-feature
   ```

## Making Changes

A few conventions to follow:

- **One feature per PR.** Small, focused pull requests get reviewed and merged faster.
- **Branch naming**: `feat/...`, `fix/...`, `docs/...`, `test/...`, `ci/...`
- **Commit messages**: conventional style — `feat: ...`, `fix: ...`, `docs: ...`, `test: ...`
- **stdlib only.** Do not add runtime dependencies to `pyproject.toml`. If a feature genuinely needs a third-party library, open an issue first to discuss it.
- **Python 3.9+ compatible.** Avoid syntax or stdlib modules introduced after 3.9 (e.g. no `match` statements, no `tomllib`).
- **Windows-friendly paths.** Use `pathlib` / `os.path` rather than hardcoded `/` separators, and avoid Unix-only calls. AutoSort should work on Linux, macOS, and Windows.

## Testing

Before opening a PR, run the test suite:

```bash
python -m unittest tests/test_autosort.py -v
```

**New features and bug fixes must come with tests.** The suite is stdlib `unittest` — add test cases to `tests/test_autosort.py`, following the existing `AutosortTestCase` pattern (each test gets its own temp directory automatically).

CI runs the same suite on every push and pull request, so a red check means the PR is not ready.

## Pull Request Checklist

- [ ] Tests pass locally: `python -m unittest tests/test_autosort.py -v`
- [ ] New behavior is covered by tests
- [ ] No new runtime dependencies
- [ ] Works on Python 3.9+
- [ ] README updated if you added/changed a user-facing option
- [ ] Commit messages follow the conventional style

## Reporting Bugs & Suggesting Features

Open an issue with:

- What you did (exact command)
- What you expected
- What actually happened (paste the output)
- OS + Python version

## License

By contributing, you agree that your contributions will be licensed under the [MIT License](LICENSE).
