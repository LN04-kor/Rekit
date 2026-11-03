from collections.abc import Sequence

from rekit.models.application import Application, ApplicationSource
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

    def sync_discovered_applications(
        self,
        applications: Sequence[Application],
    ) -> list[Application]:
        discovered = list(applications)
        if any(item.source is ApplicationSource.MANUAL for item in discovered):
            raise ValueError("Discovered applications cannot use the manual source.")

        manual_applications = [
            item
            for item in self._storage.load()
            if item.source is ApplicationSource.MANUAL
        ]
        updated_applications = [*manual_applications, *discovered]
        self._storage.save(updated_applications)
        return updated_applications
