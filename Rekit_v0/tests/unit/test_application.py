from uuid import UUID

import pytest
from pydantic import ValidationError

from rekit.models.application import Application, ApplicationSource


def test_application_defaults_to_manual_source() -> None:
    application = Application(name="  Example App  ")

    assert application.name == "Example App"
    assert application.source is ApplicationSource.MANUAL
    assert application.id is not None


def test_source_identity_produces_stable_application_id() -> None:
    first = Application(
        name="Example App",
        source=ApplicationSource.WINGET,
        source_id="Example.Publisher.App",
    )
    second = Application(
        name="Example App",
        version="2.0",
        source=ApplicationSource.WINGET,
        source_id="Example.Publisher.App",
    )

    assert first.id == second.id


def test_different_source_id_produces_different_application_id() -> None:
    first = Application(
        name="Example App",
        source=ApplicationSource.WINGET,
        source_id="Example.Publisher.App",
    )
    second = Application(
        name="Example App",
        source=ApplicationSource.WINGET,
        source_id="Example.Publisher.OtherApp",
    )

    assert first.id != second.id


def test_legacy_application_keeps_existing_id_without_source_id() -> None:
    existing_id = UUID("12345678-1234-5678-1234-567812345678")

    application = Application.model_validate(
        {
            "id": str(existing_id),
            "name": "Example App",
            "source": "registry",
        }
    )

    assert application.id == existing_id
    assert application.source_id is None


def test_application_rejects_empty_name() -> None:
    with pytest.raises(ValidationError):
        Application(name="   ")


def test_application_rejects_unknown_fields() -> None:
    with pytest.raises(ValidationError):
        Application(name="Example App", unexpected="value")
