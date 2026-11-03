# Rekit v0

Rekit is a Windows-first application inventory tool. The initial release focuses on discovering installed applications and maintaining a local catalog. It does not install, remove, or modify applications.

## Requirements

- Windows 10 or later
- Python 3.12 or later
- Git

The Registry scanner is Windows-specific. Other modules should remain importable and testable on non-Windows systems.

## Development setup

Run these commands from the `Rekit_v0` directory in PowerShell:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
```

## Validation

```powershell
python -m pytest
python -m ruff check .
python -m mypy src
```

## Current scope

- Read-only discovery of installed application metadata
- Registry and WinGet discovery adapters
- Normalized application records
- Duplicate detection with conservative matching
- Local JSON catalog
- Manual application registration

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
