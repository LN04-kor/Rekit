from enum import StrEnum
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field


class ApplicationSource(StrEnum):
    MANUAL = "manual"
    REGISTRY = "registry"
    WINGET = "winget"


class Application(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    id: UUID = Field(default_factory=uuid4)
    name: str = Field(min_length=1, max_length=256)
    version: str | None = Field(default=None, max_length=128)
    publisher: str | None = Field(default=None, max_length=256)
    package_id: str | None = Field(default=None, max_length=256)
    install_location: str | None = Field(default=None, max_length=2048)
    source: ApplicationSource = ApplicationSource.MANUAL
