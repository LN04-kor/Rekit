from collections.abc import Sequence

from rekit.catalog.matcher import ApplicationMatcher
from rekit.models.discovery_result import DiscoveryResult
from rekit.models.scan_result import ScanResult
from rekit.scanners.base import ApplicationScanner


class DiscoveryService:
    def __init__(
        self,
        scanners: Sequence[ApplicationScanner],
        matcher: ApplicationMatcher | None = None,
    ) -> None:
        self._scanners = tuple(scanners)
        self._matcher = matcher or ApplicationMatcher()

    def discover(self) -> DiscoveryResult:
        scan_results: list[ScanResult] = []

        for scanner in self._scanners:
            try:
                result = scanner.scan()
                if result.source is not scanner.source:
                    result = ScanResult(
                        source=scanner.source,
                        errors=[
                            "Scanner returned a result with an unexpected source."
                        ],
                    )
            except Exception as exc:
                result = ScanResult(
                    source=scanner.source,
                    errors=[
                        f"Scanner execution failed ({type(exc).__name__}): {exc}"
                    ],
                )

            scan_results.append(result)

        applications = [
            application
            for result in scan_results
            for application in result.applications
        ]
        merged_applications = self._matcher.merge(applications)

        return DiscoveryResult(
            applications=merged_applications,
            scans=scan_results,
        )
