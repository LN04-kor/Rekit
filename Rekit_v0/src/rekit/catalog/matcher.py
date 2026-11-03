from collections.abc import Sequence
from typing import Literal

from rekit.models.application import Application, ApplicationSource


class ApplicationMatcher:
    def merge(self, applications: Sequence[Application]) -> list[Application]:
        groups: list[list[Application]] = []

        for application in applications:
            if application.source is ApplicationSource.MANUAL:
                groups.append([application])
                continue

            matching_group = next(
                (
                    group
                    for group in groups
                    if all(self._matches(application, member) for member in group)
                ),
                None,
            )

            if matching_group is None:
                groups.append([application])
            else:
                matching_group.append(application)

        return [self._merge_group(group) for group in groups]

    @classmethod
    def _matches(cls, first: Application, second: Application) -> bool:
        if first.source is ApplicationSource.MANUAL:
            return False

        if second.source is ApplicationSource.MANUAL:
            return False

        if cls._has_conflicting_metadata(first, second):
            return False

        first_name = cls._normalize(first.name)
        second_name = cls._normalize(second.name)

        if first_name == second_name:
            return True

        return cls._package_matches_name(first, second) or cls._package_matches_name(
            second, first
        )

    @classmethod
    def _has_conflicting_metadata(
        cls,
        first: Application,
        second: Application,
    ) -> bool:
        if first.version and second.version and first.version != second.version:
            return True

        if first.publisher and second.publisher:
            if cls._normalize(first.publisher) != cls._normalize(second.publisher):
                return True

        if first.install_location and second.install_location:
            if cls._normalize_path(first.install_location) != cls._normalize_path(
                second.install_location
            ):
                return True

        return False

    @classmethod
    def _package_matches_name(
        cls,
        package_application: Application,
        named_application: Application,
    ) -> bool:
        if not package_application.package_id or not named_application.publisher:
            return False

        package_parts = package_application.package_id.split(".")
        if len(package_parts) < 2:
            return False

        publisher_prefix = cls._normalize(package_parts[0])
        publisher_name = cls._normalize(named_application.publisher)
        if not publisher_name.startswith(publisher_prefix):
            return False

        package_name = cls._normalize("".join(package_parts[1:]))
        application_name = cls._normalize(named_application.name)
        return bool(package_name) and package_name == application_name

    @staticmethod
    def _normalize(value: str) -> str:
        return "".join(
            character for character in value.casefold() if character.isalnum()
        )

    @staticmethod
    def _normalize_path(value: str) -> str:
        return value.replace("/", "\\").rstrip("\\").casefold()

    @classmethod
    def _merge_group(cls, group: list[Application]) -> Application:
        if len(group) == 1:
            return group[0]

        preferred = max(
            group,
            key=lambda application: (
                application.source is ApplicationSource.REGISTRY,
                bool(application.publisher),
                bool(application.install_location),
            ),
        )

        return Application(
            id=preferred.id,
            name=preferred.name,
            version=cls._first_value(group, "version"),
            publisher=cls._first_value(group, "publisher"),
            package_id=cls._first_value_by_source(
                group,
                "package_id",
                ApplicationSource.WINGET,
            ),
            install_location=cls._first_value(group, "install_location"),
            source=preferred.source,
        )

    @classmethod
    def _first_value(
        cls,
        group: list[Application],
        field: Literal["version", "publisher", "install_location", "package_id"],
    ) -> str | None:
        for application in group:
            value = cls._get_value(application, field)
            if value:
                return value
        return None

    @classmethod
    def _first_value_by_source(
        cls,
        group: list[Application],
        field: Literal["version", "publisher", "install_location", "package_id"],
        source: ApplicationSource,
    ) -> str | None:
        for application in group:
            if application.source is source:
                value = cls._get_value(application, field)
                if value:
                    return value
        return cls._first_value(group, field)

    @staticmethod
    def _get_value(
        application: Application,
        field: Literal["version", "publisher", "install_location", "package_id"],
    ) -> str | None:
        if field == "version":
            return application.version
        if field == "publisher":
            return application.publisher
        if field == "install_location":
            return application.install_location
        return application.package_id
