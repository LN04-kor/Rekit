from rekit.models.application import Application
from rekit.storage.json_storage import JsonApplicationStorage


class ApplicationCatalog:
    def __init__(self, storage: JsonApplicationStorage) -> None:
        self._storage = storage

    def list_applications(self) -> list[Application]:
        return self._storage.load()

    def add_application(self, application: Application) -> Application:
        applications = self._storage.load()
        if any(item.id == application.id for item in applications):
            raise ValueError(f"Application already exists: {application.id}")
        applications.append(application)
        self._storage.save(applications)
        return application
