# Rekit v0

Rekit is a Python 3.12+ application inventory tool. Its core is designed to be cross-platform, while operating-system-specific discovery features are isolated in scanner adapters.

The initial release maintains a local catalog of application metadata. It does not install, remove, update, or modify applications.

## Requirements

- Python 3.12 or later
- Git

Windows-specific discovery adapters will require Windows. The core catalog, JSON storage, and CLI are platform-independent.

## Development setup

Run these commands from the `Rekit_v0` directory.

### Windows PowerShell

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
```

### Linux or macOS

```bash
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
```

## Usage

```bash
rekit add "Example App" --version 1.0 --publisher Example
rekit list
```

The catalog is stored at `~/.rekit/applications.json`.

## Validation

```bash
python -m pytest
python -m ruff check .
python -m mypy src
```

## Current scope

- Cross-platform application data model
- Shared scanner protocol and scan result model
- Read-only Windows Registry application discovery
- Read-only WinGet package discovery through JSON export
- Conservative application matching and metadata merging across discovery sources
- Scanner orchestration with isolated failures and combined discovery results
- Manual application registration
- Local JSON catalog with atomic replacement
- CLI for adding and listing catalog entries

The WinGet scanner uses `winget export --include-versions`. WinGet package identifiers are used as provisional application names because the export schema does not include display names. Applications that cannot be matched to a configured WinGet source may not appear in the export and remain discoverable through the Registry scanner.

Application installation, cloud synchronization, account management, and GUI workflows are out of scope for this version.

## Security principles

- Discovery must be read-only.
- Do not require administrator privileges for ordinary scans.
- Never execute commands assembled from untrusted input.
- Use argument lists with subprocess APIs; do not enable shell execution.
- Apply timeouts and validate external command output.
- Do not collect credentials, browser data, documents, or unrelated personal files.
- Preserve existing catalog data when parsing or writing fails.

See [docs/architecture.md](docs/architecture.md) for module boundaries and data flow.
