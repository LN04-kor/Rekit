from pathlib import Path

from rekit.catalog.manager import ApplicationCatalog
from rekit.cli.commands import run_command
from rekit.core.discovery_service import DiscoveryService
from rekit.models.application import Application, ApplicationSource
from rekit.models.scan_result import ScanResult
from rekit.storage.json_storage import JsonApplicationStorage


class FakeScanner:
    def __init__(
        self,
        applications: list[Application],
        errors: list[str] | None = None,
    ) -> None:
        self.source = ApplicationSource.REGISTRY
        self._applications = applications
        self._errors = errors or []

    def scan(self) -> ScanResult:
        return ScanResult(
            source=self.source,
            applications=self._applications,
            errors=self._errors,
        )


def make_catalog(tmp_path: Path) -> ApplicationCatalog:
    return ApplicationCatalog(JsonApplicationStorage(tmp_path / "applications.json"))


def test_scan_command_saves_discovered_applications(
    tmp_path: Path,
    capsys,
) -> None:
    catalog = make_catalog(tmp_path)
    manual_application = Application(name="Manual App")
    catalog.add_application(manual_application)
    discovered_application = Application(
        name="Discovered App",
        version="1.0",
        source=ApplicationSource.REGISTRY,
    )
    service = DiscoveryService([FakeScanner([discovered_application])])

    exit_code = run_command(catalog, ["scan"], service)

    saved_applications = catalog.list_applications()
    output = capsys.readouterr().out

    assert exit_code == 0
    assert saved_applications == [manual_application, discovered_application]
    assert "Discovered 1 applications." in output
    assert "Discovered App (1.0) [registry]" in output


def test_scan_command_replaces_previous_discovery_results(tmp_path: Path) -> None:
    catalog = make_catalog(tmp_path)
    old_application = Application(
        name="Old App",
        source=ApplicationSource.REGISTRY,
    )
    catalog.add_application(old_application)
    new_application = Application(
        name="New App",
        source=ApplicationSource.WINGET,
    )
    service = DiscoveryService([FakeScanner([new_application])])

    exit_code = run_command(catalog, ["scan"], service)

    assert exit_code == 0
    assert catalog.list_applications() == [new_application]


def test_scan_command_preserves_partial_results_and_reports_errors(
    tmp_path: Path,
    capsys,
) -> None:
    catalog = make_catalog(tmp_path)
    discovered_application = Application(
        name="Available App",
        source=ApplicationSource.REGISTRY,
    )
    service = DiscoveryService(
        [FakeScanner([discovered_application], ["One entry could not be read."])]
    )

    exit_code = run_command(catalog, ["scan"], service)

    output = capsys.readouterr().out

    assert exit_code == 1
    assert catalog.list_applications() == [discovered_application]
    assert "Discovered 1 applications." in output
    assert "Warning: registry: One entry could not be read." in output


def test_existing_cli_commands_remain_available(tmp_path: Path, capsys) -> None:
    catalog = make_catalog(tmp_path)

    assert run_command(catalog, ["add", "Manual App", "--version", "2.0"]) == 0
    assert run_command(catalog, ["list"]) == 0

    output = capsys.readouterr().out

    assert "Registered: Manual App" in output
    assert "Manual App (2.0) [manual]" in output
