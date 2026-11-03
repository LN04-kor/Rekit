# Rekit v0 Architecture

## Goal

Rekit v0 discovers installed application metadata on a Windows computer and stores a normalized local inventory. Discovery is read-only. Installing, updating, or removing software is explicitly outside this version.

## Dependency direction

The intended dependency direction is:

```text
CLI
 |
 v
Core services
 |-------------------|
 v                   v
Scanners           Catalog
                     |
                     v
                  Storage
```

Domain models are shared by services, scanners, catalog, and storage. Low-level adapters must not depend on the CLI.

## Module responsibilities

- `models/`: validated domain records and scan result types.
- `scanners/`: read-only adapters for Windows Registry and WinGet.
- `core/`: orchestration and application-level use cases.
- `catalog/`: normalization, matching, deduplication, and catalog operations.
- `storage/`: persistence interfaces and local JSON implementation.
- `cli/`: command-line input and output only.
- `config/`: application paths and configuration defaults.

## Discovery flow

1. Core invokes each available scanner independently.
2. A scanner returns normalized records and structured scan diagnostics.
3. A scanner failure is recorded without discarding successful results from other scanners.
4. The catalog matcher compares records using conservative rules.
5. Ambiguous matches remain separate or require user confirmation.
6. The catalog is persisted only after validation succeeds.

Registry and WinGet are independent sources. A Registry display name must not be treated as proof of a WinGet package identifier.

## Data model principles

- Rekit record IDs are distinct from external package identifiers.
- Source information is retained for traceability.
- Optional metadata remains optional; unknown values are not fabricated.
- Matching confidence and match rationale should be explicit.
- Installed state and saved catalog membership are separate concepts.

## Security boundaries

- Registry access is read-only and limited to uninstall metadata locations.
- No administrator elevation is requested for ordinary discovery.
- WinGet is invoked with a fixed executable and argument arrays, never with shell command strings.
- External process execution must use timeouts, bounded output handling, and explicit exit-code checks.
- Package identifiers and paths are treated as untrusted data and validated before use.
- JSON writes use a temporary file in the destination directory followed by an atomic replacement where supported.
- Invalid or corrupted catalog data must not be silently overwritten.
- Local inventory files may reveal installed software; they must not be committed to source control by default.

## Error handling

Scanner errors are isolated by source. A missing WinGet executable must not prevent Registry discovery. Individual malformed Registry entries should be skipped with diagnostics. Storage errors must be surfaced and must never trigger a destructive fallback.

## Testing strategy

- Unit tests use temporary directories and mocked operating-system or subprocess interfaces.
- Registry-specific behavior is isolated so tests can run on non-Windows hosts.
- Integration tests validate orchestration and partial scanner failures.
- Tests must not install, remove, or modify software on the host machine.

## Version boundary

The v0 implementation is local-only. Cloud APIs, authentication, desktop UI, application installation, and cross-platform scanners are future concerns and must not leak into the local discovery core.
