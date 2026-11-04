from enum import StrEnum
from uuid import UUID, uuid4, uuid5

from pydantic import BaseModel, ConfigDict, Field, model_validator

_SOURCE_ID_NAMESPACE = UUID("c83d8a9e-7f2d-4d3a-9c51-5e2a0a8b6f41")


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
    source_id: str | None = Field(default=None, min_length=1, max_length=512)

    @model_validator(mode="before")
    @classmethod
    def assign_source_based_id(cls, values: object) -> object:
        if not isinstance(values, dict):
            return values

        source_id = values.get("source_id")
        if source_id and "id" not in values:
            source = values.get("source", ApplicationSource.MANUAL)
            values = {
                **values,
                "id": uuid5(_SOURCE_ID_NAMESPACE, f"{source}:{source_id}"),
            }

        return values
