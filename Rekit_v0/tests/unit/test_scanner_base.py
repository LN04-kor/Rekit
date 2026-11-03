from rekit.models.application import Application, ApplicationSource
from rekit.models.scan_result import ScanResult
from rekit.scanners.base import ApplicationScanner


class ExampleScanner:
    source = ApplicationSource.MANUAL

    def scan(self) -> ScanResult:
        return ScanResult(
            source=self.source,
            applications=[Application(name="Example App")],
        )


def test_scanner_implementation_matches_protocol() -> None:
    scanner: ApplicationScanner = ExampleScanner()

    result = scanner.scan()

    assert result.source is ApplicationSource.MANUAL
    assert [application.name for application in result.applications] == [
        "Example App"
    ]
