from importlib import import_module
from typing import Any

from rekit.models.application import Application, ApplicationSource
from rekit.models.scan_result import ScanResult


_UNINSTALL_PATH = r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall"


class RegistryScanner:
    source = ApplicationSource.REGISTRY

    def scan(self) -> ScanResult:
        try:
            registry = import_module("winreg")
        except ImportError:
            return ScanResult(
                source=self.source,
                errors=["Windows Registry is only available on Windows."],
            )

        applications: list[Application] = []
        errors: list[str] = []

        targets = [
            (
                "HKEY_LOCAL_MACHINE",
                registry.HKEY_LOCAL_MACHINE,
                registry.KEY_WOW64_64KEY,
            ),
            (
                "HKEY_LOCAL_MACHINE",
                registry.HKEY_LOCAL_MACHINE,
                registry.KEY_WOW64_32KEY,
            ),
            (
                "HKEY_CURRENT_USER",
                registry.HKEY_CURRENT_USER,
                registry.KEY_WOW64_64KEY,
            ),
            (
                "HKEY_CURRENT_USER",
                registry.HKEY_CURRENT_USER,
                registry.KEY_WOW64_32KEY,
            ),
        ]

        for hive_name, hive, view in targets:
            try:
                root_key = registry.OpenKey(
                    hive,
                    _UNINSTALL_PATH,
                    0,
                    registry.KEY_READ | view,
                )
            except OSError as exc:
                errors.append(
                    f"{hive_name} uninstall entries could not be opened: {exc}"
                )
                continue

            with root_key:
                index = 0
                while True:
                    try:
                        subkey_name = registry.EnumKey(root_key, index)
                    except OSError:
                        break

                    index += 1
                    try:
                        with registry.OpenKey(root_key, subkey_name) as subkey:
                            application = self._read_application(registry, subkey)
                    except OSError as exc:
                        errors.append(
                            f"Registry entry '{subkey_name}' could not be read: {exc}"
                        )
                        continue

                    if application is not None:
                        applications.append(application)

        return ScanResult(
            source=self.source,
            applications=applications,
            errors=errors,
        )

    @staticmethod
    def _read_application(registry: Any, key: Any) -> Application | None:
        display_name = RegistryScanner._read_value(registry, key, "DisplayName")
        if not isinstance(display_name, str) or not display_name.strip():
            return None

        system_component = RegistryScanner._read_value(
            registry,
            key,
            "SystemComponent",
        )
        if system_component == 1:
            return None

        version = RegistryScanner._read_value(registry, key, "DisplayVersion")
        publisher = RegistryScanner._read_value(registry, key, "Publisher")
        install_location = RegistryScanner._read_value(
            registry,
            key,
            "InstallLocation",
        )

        return Application(
            name=display_name,
            version=(
                version
                if isinstance(version, str) and version.strip()
                else None
            ),
            publisher=(
                publisher
                if isinstance(publisher, str) and publisher.strip()
                else None
            ),
            install_location=(
                install_location
                if isinstance(install_location, str) and install_location.strip()
                else None
            ),
            source=ApplicationSource.REGISTRY,
        )

    @staticmethod
    def _read_value(registry: Any, key: Any, name: str) -> Any | None:
        try:
            value, _ = registry.QueryValueEx(key, name)
        except OSError:
            return None
        return value
