from pydantic import BaseModel, ConfigDict, Field

from rekit.models.application import Application, ApplicationSource


class ScanResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    source: ApplicationSource
    applications: list[Application] = Field(default_factory=list)
    errors: list[str] = Field(default_factory=list)
