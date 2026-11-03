import argparse
from collections.abc import Sequence

from rekit.catalog.manager import ApplicationCatalog
from rekit.core.discovery_service import DiscoveryService
from rekit.models.application import Application, ApplicationSource
from rekit.scanners.registry_scanner import RegistryScanner
from rekit.scanners.winget_scanner import WinGetScanner


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="rekit")
    commands = parser.add_subparsers(dest="command", required=True)

    commands.add_parser("list", help="List saved applications")
    commands.add_parser("scan", help="Discover installed applications")

    add_parser = commands.add_parser("add", help="Register an application manually")
    add_parser.add_argument("name")
    add_parser.add_argument("--version")
    add_parser.add_argument("--publisher")

    return parser


def run_command(
    catalog: ApplicationCatalog,
    arguments: Sequence[str] | None = None,
    discovery_service: DiscoveryService | None = None,
) -> int:
    parsed = build_parser().parse_args(arguments)

    if parsed.command == "list":
        applications = catalog.list_applications()
        if not applications:
            print("No applications registered.")
            return 0

        for application in applications:
            version = f" ({application.version})" if application.version else ""
            print(f"{application.name}{version} [{application.source.value}]")
        return 0

    if parsed.command == "scan":
        service = discovery_service or DiscoveryService(
            [RegistryScanner(), WinGetScanner()]
        )
        result = service.discover()
        catalog.sync_discovered_applications(result.applications)

        print(f"Discovered {len(result.applications)} applications.")
        for application in result.applications:
            version = f" ({application.version})" if application.version else ""
            print(f"{application.name}{version} [{application.source.value}]")

        for error in result.errors:
            print(f"Warning: {error}")

        return 1 if result.errors else 0

    application = Application(
        name=parsed.name,
        version=parsed.version,
        publisher=parsed.publisher,
        source=ApplicationSource.MANUAL,
    )
    catalog.add_application(application)
    print(f"Registered: {application.name}")
    return 0
