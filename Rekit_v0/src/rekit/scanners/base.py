from typing import Protocol

from rekit.models.application import ApplicationSource
from rekit.models.scan_result import ScanResult


class ApplicationScanner(Protocol):
    source: ApplicationSource

    def scan(self) -> ScanResult:
        ...
