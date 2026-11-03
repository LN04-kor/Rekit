# Rekit v0 Architecture

## Goal

Rekit v0 maintains a local catalog of installed application metadata. The shared core targets Python 3.12+ and remains independent of the host operating system. Platform-specific discovery is implemented through isolated adapters.

Installing, updating, or removing software is outside this version.

## Dependency direction

```text
CLI
 |------------------|
 v                  v
Catalog services  Discovery services
 |                  |
 v                  v
JSON storage      Scanner interface
                    |
             |--------------|
             v              v
        Windows adapters  Future adapters
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

The domain model, catalog, JSON storage, and CLI use platform-neutral dependencies. Platform-specific APIs must only be imported inside their corresponding adapter modules. A platform adapter must report unavailability without preventing the shared core from loading.

## Discovery flow

1. The CLI invokes DiscoveryService with the Registry and WinGet scanners.
2. DiscoveryService invokes each configured scanner independently.
3. A scanner returns normalized records and structured scan diagnostics.
4. A scanner failure is recorded without discarding successful results from other sources.
5. Results are checked against the scanner's declared source before aggregation.
6. The catalog matcher compares all collected records using conservative rules.
7. DiscoveryResult returns merged applications together with each scanner's diagnostics.
8. The CLI replaces previous discovered records with the latest scan results and preserves manually registered records.

The Registry scanner reads uninstall metadata from the machine-wide and current-user hives, including both 32-bit and 64-bit registry views. Duplicate discoveries are handled by the catalog matching stage.

The WinGet scanner runs `winget export --include-versions` with a fixed argument list and writes the export to a temporary directory. It reads package identifiers and optional versions from the `Sources[].Packages[]` structure, supporting both the `PackageIdentifier` field and the legacy `Id` field. Since the export schema does not include a display name, the package identifier is used as the provisional application name. Packages that cannot be matched to a configured source may be omitted by WinGet and remain discoverable through the Registry scanner.

The application matcher normalizes names for case- and punctuation-insensitive comparison. Conflicting metadata prevents automatic merging, and manual entries are never automatically merged.

The scanner does not accept source agreements automatically, does not invoke installation commands, and applies a process timeout. Its subprocess runner is injectable so unit tests do not require Windows or an installed WinGet executable.

## Catalog synchronization

A scan is treated as a snapshot of discovered applications. Each scan replaces the previous Registry and WinGet records, while manual records remain untouched. Partial discovery results are persisted alongside diagnostics printed by the CLI. A non-zero CLI exit code indicates that one or more scanners reported errors; it does not mean that successful results were discarded.

## Security boundaries

- Discovery is read-only and limited to application metadata.
- No administrator elevation is requested for ordinary discovery.
- External process execution uses fixed executables and argument arrays, never shell command strings.
- External process execution must use timeouts and explicit exit-code checks.
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
