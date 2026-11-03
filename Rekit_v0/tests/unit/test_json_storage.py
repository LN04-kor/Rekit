import json

import pytest

from rekit.models.application import Application
from rekit.storage.json_storage import JsonApplicationStorage, JsonStorageError


def test_storage_round_trip(tmp_path) -> None:
    storage = JsonApplicationStorage(tmp_path / "catalog.json")
    application = Application(name="Example App", version="1.2")

    storage.save([application])

    loaded = storage.load()
    assert loaded == [application]


def test_missing_catalog_returns_empty_list(tmp_path) -> None:
    storage = JsonApplicationStorage(tmp_path / "missing.json")

    assert storage.load() == []


def test_invalid_catalog_is_not_overwritten(tmp_path) -> None:
    path = tmp_path / "catalog.json"
    path.write_text(json.dumps({"unexpected": "object"}), encoding="utf-8")
    storage = JsonApplicationStorage(path)

    with pytest.raises(JsonStorageError):
        storage.load()

    assert json.loads(path.read_text(encoding="utf-8")) == {
        "unexpected": "object"
    }
