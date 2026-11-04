from collections.abc import Sequence

from rekit.catalog.matcher import ApplicationMatcher
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
        preserve_sources: set[ApplicationSource] | None = None,
    ) -> list[Application]:
        discovered = list(applications)
        if any(item.source is ApplicationSource.MANUAL for item in discovered):
            raise ValueError("Discovered applications cannot use the manual source.")

        preserved_sources = preserve_sources or set()
        existing_applications = self._storage.load()
        retained_applications = [
            item
            for item in existing_applications
            if item.source is ApplicationSource.MANUAL
            or item.source in preserved_sources
        ]
        updated_applications = ApplicationMatcher().merge(
            [*retained_applications, *discovered]
        )
        self._storage.save(updated_applications)
        return updated_applications
