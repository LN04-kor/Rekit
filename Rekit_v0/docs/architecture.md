# Rekit v0 Architecture

## Goal

Rekit v0 maintains a local catalog of installed application metadata. The shared core targets Python 3.12+ and remains independent of the host operating system. Platform-specific discovery is implemented through isolated adapters.

Installing, updating, or removing software is outside this version.

## Dependency direction

```text
CLI
 |
 v
Catalog services
 |
 v
Storage interface
 |
 v
JSON storage adapter

Discovery services
 |
 v
Scanner interface
 |
 |----------------------|
 v                      v
Windows adapters     Future platform adapters
```

Domain models are shared by services, scanners, catalog, and storage. Low-level adapters must not depend on the CLI.

## Module responsibilities

- `models/`: validated domain records and scan result types.
- `scanners/`: read-only platform-specific discovery adapters.
- `core/`: orchestration and application-level use cases.
- `catalog/`: normalization, matching, deduplication, and catalog operations.
- `storage/`: persistence interfaces and local JSON implementation.
- `cli/`: command-line input and output only.
- `config/`: application paths and configuration defaults.

## Portability boundary

The domain model, catalog, JSON storage, and CLI use the Python standard library and platform-neutral dependencies. Platform-specific APIs must only be imported inside their corresponding adapter modules. A platform adapter must report unavailability without preventing the shared core from loading.

## Discovery flow

1. Core invokes each available scanner independently.
2. A scanner returns normalized records and structured scan diagnostics.
3. A scanner failure is recorded without discarding successful results from other sources.
4. The catalog matcher compares records using conservative rules.
5. Ambiguous matches remain separate or require user confirmation.
6. The catalog is persisted only after validation succeeds.

Registry and WinGet are independent sources. A Registry display name must not be treated as proof of a WinGet package identifier.

The Registry scanner reads uninstall metadata from the machine-wide and current-user hives, including both 32-bit and 64-bit registry views. Duplicate discoveries are retained at the scanner boundary and are handled by the catalog matching stage.

## Data model principles

- Rekit record IDs are distinct from external package identifiers.
- Source information is retained for traceability.
- Optional metadata remains optional; unknown values are not fabricated.
- Matching confidence and match rationale should be explicit.
- Installed state and saved catalog membership are separate concepts.

## Security boundaries

- Discovery is read-only and limited to application metadata.
- No administrator elevation is requested for ordinary discovery.
- External process execution uses fixed executables and argument arrays, never shell command strings.
- External process execution must use timeouts, bounded output handling, and explicit exit-code checks.
- Package identifiers and paths are treated as untrusted data and validated before use.
- JSON writes use a temporary file in the destination directory followed by atomic replacement where supported.
- Invalid or corrupted catalog data must not be silently overwritten.
- Local inventory files may reveal installed software; they must not be committed to source control by default.

## Error handling

Scanner errors are isolated by source. A missing platform tool must not prevent other scanners from running. Individual malformed entries should be skipped with diagnostics. Storage errors must be surfaced and must never trigger a destructive fallback.

## Testing strategy

- Unit tests use temporary directories and mocked operating-system or subprocess interfaces.
- Platform-specific behavior is isolated so tests can run on non-Windows hosts.
- Integration tests validate orchestration and partial scanner failures.
- Tests must not install, remove, or modify software on the host machine.

## Version boundary

The v0 implementation is local-only. Cloud APIs, authentication, desktop UI, and application installation are future concerns and must not leak into the local discovery core.
