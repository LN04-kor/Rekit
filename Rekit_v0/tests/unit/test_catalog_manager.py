from rekit.catalog.manager import ApplicationCatalog
from rekit.models.application import Application
from rekit.storage.json_storage import JsonApplicationStorage


def test_catalog_add_and_list(tmp_path) -> None:
    catalog = ApplicationCatalog(
        JsonApplicationStorage(tmp_path / "catalog.json")
    )
    application = Application(name="Example App")

    catalog.add_application(application)

    assert catalog.list_applications() == [application]
