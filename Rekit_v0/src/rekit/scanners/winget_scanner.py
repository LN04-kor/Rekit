import json
from collections.abc import Callable
from pathlib import Path
from subprocess import CompletedProcess, TimeoutExpired, run
from tempfile import TemporaryDirectory
from typing import Any

from pydantic import ValidationError

from rekit.models.application import Application, ApplicationSource
from rekit.models.scan_result import ScanResult


class WinGetScanner:
    source = ApplicationSource.WINGET

    def __init__(
        self,
        timeout: float = 60.0,
        runner: Callable[..., CompletedProcess[str]] = run,
    ) -> None:
        self.timeout = timeout
        self._runner = runner

    def scan(self) -> ScanResult:
        try:
            with TemporaryDirectory() as temporary_directory:
                output_path = Path(temporary_directory) / "winget-export.json"
                result = self._runner(
                    [
                        "winget",
                        "export",
                        "--output",
                        str(output_path),
                        "--include-versions",
                        "--disable-interactivity",
                    ],
                    capture_output=True,
                    text=True,
                    timeout=self.timeout,
                    check=False,
                    shell=False,
                )

                if result.returncode != 0:
                    detail = (result.stderr or "").strip()[:500]
                    message = "WinGet export command failed."
                    if detail:
                        message = f"{message} {detail}"
                    return ScanResult(source=self.source, errors=[message])

                try:
                    export_data = json.loads(output_path.read_text(encoding="utf-8"))
                except FileNotFoundError:
                    return ScanResult(
                        source=self.source,
                        errors=["WinGet did not create an export file."],
                    )
                except (OSError, json.JSONDecodeError) as exc:
                    return ScanResult(
                        source=self.source,
                        errors=[f"WinGet export file could not be read: {exc}"],
                    )

        except FileNotFoundError:
            return ScanResult(
                source=self.source,
                errors=["WinGet CLI is not available on this system."],
            )
        except TimeoutExpired:
            return ScanResult(
                source=self.source,
                errors=[f"WinGet export timed out after {self.timeout} seconds."],
            )
        except OSError as exc:
            return ScanResult(
                source=self.source,
                errors=[f"WinGet could not be executed: {exc}"],
            )

        return self._parse_export(export_data)

    @classmethod
    def _parse_export(cls, export_data: Any) -> ScanResult:
        if not isinstance(export_data, dict):
            return ScanResult(
                source=cls.source,
                errors=["WinGet export data must be a JSON object."],
            )

        sources = export_data.get("Sources")
        if not isinstance(sources, list):
            return ScanResult(
                source=cls.source,
                errors=["WinGet export data does not contain a valid Sources list."],
            )

        applications: list[Application] = []
        errors: list[str] = []

        for source_index, source_data in enumerate(sources):
            if not isinstance(source_data, dict):
                errors.append(f"WinGet source entry {source_index} is invalid.")
                continue

            packages = source_data.get("Packages")
            if not isinstance(packages, list):
                errors.append(
                    f"WinGet source entry {source_index} has no valid Packages list."
                )
                continue

            for package_index, package_data in enumerate(packages):
                if not isinstance(package_data, dict):
                    errors.append(
                        f"WinGet package entry {source_index}:{package_index} "
                        "is invalid."
                    )
                    continue

                package_id = package_data.get("PackageIdentifier")
                if not isinstance(package_id, str) or not package_id.strip():
                    package_id = package_data.get("Id")

                if not isinstance(package_id, str) or not package_id.strip():
                    errors.append(
                        f"WinGet package entry {source_index}:{package_index} "
                        "has no valid package identifier."
                    )
                    continue

                version = package_data.get("Version")
                if not isinstance(version, str) or not version.strip():
                    version = None

                try:
                    applications.append(
                        Application(
                            name=package_id,
                            package_id=package_id,
                            version=version,
                            source=cls.source,
                        )
                    )
                except ValidationError as exc:
                    errors.append(
                        f"WinGet package '{package_id}' could not be converted: {exc}"
                    )

        return ScanResult(
            source=cls.source,
            applications=applications,
            errors=errors,
        )
