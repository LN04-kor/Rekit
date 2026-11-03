import pytest
from pydantic import ValidationError

from rekit.models.application import Application, ApplicationSource


def test_application_defaults_to_manual_source() -> None:
    application = Application(name="  Example App  ")

    assert application.name == "Example App"
    assert application.source is ApplicationSource.MANUAL
    assert application.id is not None


def test_application_rejects_empty_name() -> None:
    with pytest.raises(ValidationError):
        Application(name="   ")


def test_application_rejects_unknown_fields() -> None:
    with pytest.raises(ValidationError):
        Application(name="Example App", unexpected="value")
