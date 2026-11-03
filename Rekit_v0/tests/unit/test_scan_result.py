import pytest
from pydantic import ValidationError

from rekit.models.application import Application, ApplicationSource
from rekit.models.scan_result import ScanResult


def test_scan_result_stores_applications_and_errors() -> None:
    application = Application(
        name="Example App",
        source=ApplicationSource.REGISTRY,
    )

    result = ScanResult(
        source=ApplicationSource.REGISTRY,
        applications=[application],
        errors=["One entry could not be read"],
    )

    assert result.source is ApplicationSource.REGISTRY
    assert result.applications == [application]
    assert result.errors == ["One entry could not be read"]


def test_scan_result_defaults_to_empty_collections() -> None:
    result = ScanResult(source=ApplicationSource.WINGET)

    assert result.applications == []
    assert result.errors == []


def test_scan_result_rejects_unknown_fields() -> None:
    with pytest.raises(ValidationError):
        ScanResult(source=ApplicationSource.REGISTRY, unexpected="value")
