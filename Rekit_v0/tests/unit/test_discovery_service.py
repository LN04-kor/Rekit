from rekit.core.discovery_service import DiscoveryService
from rekit.models.application import Application, ApplicationSource
from rekit.models.scan_result import ScanResult


class FakeScanner:
    def __init__(
        self,
        source: ApplicationSource,
        applications: list[Application] | None = None,
        errors: list[str] | None = None,
    ) -> None:
        self.source = source
        self.applications = applications or []
        self.errors = errors or []

    def scan(self) -> ScanResult:
        return ScanResult(
            source=self.source,
            applications=self.applications,
            errors=self.errors,
        )


class FailingScanner:
    source = ApplicationSource.WINGET

    def scan(self) -> ScanResult:
        raise RuntimeError("Scanner failure")


def make_application(
    name: str,
    source: ApplicationSource,
    version: str | None = None,
    publisher: str | None = None,
    package_id: str | None = None,
) -> Application:
    return Application(
        name=name,
        source=source,
        version=version,
        publisher=publisher,
        package_id=package_id,
    )


def test_discovery_service_runs_all_scanners() -> None:
    registry_application = make_application(
        "Example App",
        ApplicationSource.REGISTRY,
        version="1.0",
        publisher="Example Publisher",
    )
    winget_application = make_application(
        "Example.App",
        ApplicationSource.WINGET,
        version="1.0",
        package_id="Example.App",
    )
    service = DiscoveryService(
        [
            FakeScanner(
                ApplicationSource.REGISTRY,
                [registry_application],
            ),
            FakeScanner(
                ApplicationSource.WINGET,
                [winget_application],
            ),
        ]
    )

    result = service.discover()

    assert len(result.scans) == 2
    assert len(result.applications) == 1
    assert result.applications[0].name == "Example App"
    assert result.applications[0].package_id == "Example.App"
    assert result.errors == []


def test_discovery_service_continues_after_scanner_failure() -> None:
    registry_application = make_application(
        "Example App",
        ApplicationSource.REGISTRY,
    )
    service = DiscoveryService(
        [
            FailingScanner(),
            FakeScanner(
                ApplicationSource.REGISTRY,
                [registry_application],
            ),
        ]
    )

    result = service.discover()

    assert len(result.scans) == 2
    assert len(result.applications) == 1
    assert result.applications[0].name == "Example App"
    assert len(result.errors) == 1
    assert "RuntimeError" in result.errors[0]


def test_discovery_service_preserves_scanner_errors() -> None:
    service = DiscoveryService(
        [
            FakeScanner(
                ApplicationSource.REGISTRY,
                errors=["Registry access denied."],
            ),
            FakeScanner(ApplicationSource.WINGET),
        ]
    )

    result = service.discover()

    assert result.applications == []
    assert result.errors == ["registry: Registry access denied."]


def test_discovery_service_handles_empty_scanner_list() -> None:
    result = DiscoveryService([]).discover()

    assert result.applications == []
    assert result.scans == []
    assert result.errors == []


def test_discovery_service_rejects_mismatched_result_source() -> None:
    class MismatchedScanner:
        source = ApplicationSource.REGISTRY

        def scan(self) -> ScanResult:
            return ScanResult(source=ApplicationSource.WINGET)

    result = DiscoveryService([MismatchedScanner()]).discover()

    assert result.applications == []
    assert result.errors == [
        "registry: Scanner returned a result with an unexpected source."
    ]


def test_discovery_service_preserves_results_when_one_scanner_has_errors() -> None:
    application = make_application(
        "Example App",
        ApplicationSource.REGISTRY,
    )
    service = DiscoveryService(
        [
            FakeScanner(
                ApplicationSource.REGISTRY,
                [application],
                ["One registry entry could not be read."],
            ),
            FakeScanner(
                ApplicationSource.WINGET,
                errors=["WinGet source unavailable."],
            ),
        ]
    )

    result = service.discover()

    assert result.applications == [application]
    assert len(result.errors) == 2
