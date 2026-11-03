import json
from collections.abc import Callable
from pathlib import Path
from subprocess import CompletedProcess, TimeoutExpired
from typing import Any

from rekit.models.application import ApplicationSource
from rekit.scanners.winget_scanner import WinGetScanner


def make_runner(
    export_data: Any,
    returncode: int = 0,
    stderr: str = "",
) -> Callable[..., CompletedProcess[str]]:
    def runner(command: list[str], **kwargs: Any) -> CompletedProcess[str]:
        output_path = Path(command[command.index("--output") + 1])
        output_path.write_text(json.dumps(export_data), encoding="utf-8")
        return CompletedProcess(
            args=command,
            returncode=returncode,
            stdout="",
            stderr=stderr,
        )

    return runner


def test_winget_scanner_reads_package_metadata() -> None:
    export_data = {
        "WinGetVersion": "1.10.0",
        "Sources": [
            {
                "SourceDetails": {
                    "Name": "winget",
                    "Identifier": "Microsoft.Winget.Source_8wekyb3d8bbwe",
                    "Argument": "https://cdn.winget.microsoft.com/cache",
                    "Type": "Microsoft.PreIndexed.Package",
                },
                "Packages": [
                    {"Id": "Example.App", "Version": "2.4.1"},
                    {"Id": "Example.Tool"},
                ],
            }
        ],
    }

    result = WinGetScanner(runner=make_runner(export_data)).scan()

    assert result.source is ApplicationSource.WINGET
    assert len(result.applications) == 2
    assert result.applications[0].name == "Example.App"
    assert result.applications[0].package_id == "Example.App"
    assert result.applications[0].version == "2.4.1"
    assert result.applications[0].source is ApplicationSource.WINGET
    assert result.applications[1].version is None
    assert result.errors == []


def test_winget_scanner_reads_current_package_identifier_field() -> None:
    export_data = {
        "Sources": [
            {
                "Packages": [
                    {"PackageIdentifier": "Example.Current", "Version": "3.2.1"}
                ]
            }
        ]
    }

    result = WinGetScanner(runner=make_runner(export_data)).scan()

    assert len(result.applications) == 1
    assert result.applications[0].package_id == "Example.Current"
    assert result.applications[0].version == "3.2.1"
    assert result.errors == []


def test_winget_scanner_uses_safe_noninteractive_command() -> None:
    export_data = {"Sources": []}
    captured: dict[str, Any] = {}

    def runner(command: list[str], **kwargs: Any) -> CompletedProcess[str]:
        captured["command"] = command
        captured.update(kwargs)
        output_path = Path(command[command.index("--output") + 1])
        output_path.write_text(json.dumps(export_data), encoding="utf-8")
        return CompletedProcess(command, 0, "", "")

    WinGetScanner(timeout=45.0, runner=runner).scan()

    assert captured["command"][:2] == ["winget", "export"]
    assert "--include-versions" in captured["command"]
    assert "--disable-interactivity" in captured["command"]
    assert captured["shell"] is False
    assert captured["timeout"] == 45.0
    assert captured["check"] is False


def test_winget_scanner_reports_missing_cli() -> None:
    def runner(command: list[str], **kwargs: Any) -> CompletedProcess[str]:
        raise FileNotFoundError("winget")

    result = WinGetScanner(runner=runner).scan()

    assert result.applications == []
    assert result.errors == ["WinGet CLI is not available on this system."]


def test_winget_scanner_reports_timeout() -> None:
    def runner(command: list[str], **kwargs: Any) -> CompletedProcess[str]:
        raise TimeoutExpired(command, timeout=60.0)

    result = WinGetScanner(runner=runner).scan()

    assert result.applications == []
    assert result.errors == ["WinGet export timed out after 60.0 seconds."]


def test_winget_scanner_reports_command_failure() -> None:
    runner = make_runner({"Sources": []}, returncode=1, stderr="Source unavailable")

    result = WinGetScanner(runner=runner).scan()

    assert result.applications == []
    assert result.errors == [
        "WinGet export command failed. Source unavailable"
    ]


def test_winget_scanner_reports_invalid_json() -> None:
    def runner(command: list[str], **kwargs: Any) -> CompletedProcess[str]:
        output_path = Path(command[command.index("--output") + 1])
        output_path.write_text("{", encoding="utf-8")
        return CompletedProcess(command, 0, "", "")

    result = WinGetScanner(runner=runner).scan()

    assert result.applications == []
    assert len(result.errors) == 1
    assert result.errors[0].startswith("WinGet export file could not be read:")


def test_winget_scanner_skips_invalid_package_entries() -> None:
    export_data = {
        "Sources": [
            {
                "Packages": [
                    {"Id": "Valid.App", "Version": "1.0"},
                    {"Version": "2.0"},
                    None,
                ]
            }
        ]
    }

    result = WinGetScanner(runner=make_runner(export_data)).scan()

    assert len(result.applications) == 1
    assert result.applications[0].package_id == "Valid.App"
    assert len(result.errors) == 2


def test_winget_scanner_accepts_empty_sources() -> None:
    result = WinGetScanner(runner=make_runner({"Sources": []})).scan()

    assert result.applications == []
    assert result.errors == []
