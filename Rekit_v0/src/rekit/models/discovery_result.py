from pydantic import BaseModel, ConfigDict, Field

from rekit.models.application import Application
from rekit.models.scan_result import ScanResult


class DiscoveryResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    applications: list[Application] = Field(default_factory=list)
    scans: list[ScanResult] = Field(default_factory=list)

    @property
    def errors(self) -> list[str]:
        return [
            f"{scan.source.value}: {error}"
            for scan in self.scans
            for error in scan.errors
        ]
