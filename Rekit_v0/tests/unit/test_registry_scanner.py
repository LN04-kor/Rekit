from typing import Any

from rekit.models.application import ApplicationSource
from rekit.scanners.registry_scanner import RegistryScanner


class FakeKey:
    def __init__(self, name: str, values: dict[str, Any]) -> None:
        self.name = name
        self.values = values

    def __enter__(self) -> FakeKey:
        return self

    def __exit__(
        self,
        exception_type: type[BaseException] | None,
        exception: BaseException | None,
        traceback: Any,
    ) -> None:
        return None


class FakeRegistry:
    HKEY_LOCAL_MACHINE = "HKLM"
    HKEY_CURRENT_USER = "HKCU"
    KEY_READ = 1
    KEY_WOW64_64KEY = 2
    KEY_WOW64_32KEY = 4

    def __init__(self, entries: dict[str, dict[str, Any]]) -> None:
        self.entries = entries

    def OpenKey(
        self,
        parent: str | FakeKey,
        path: str,
        reserved: int = 0,
        access: int = 0,
    ) -> FakeKey:
        if isinstance(parent, FakeKey):
            return FakeKey(path, self.entries[path])
        return FakeKey(path, {})

    def EnumKey(self, key: FakeKey, index: int) -> str:
        names = list(self.entries)
        if index >= len(names):
            raise OSError("No more entries")
        return names[index]

    def QueryValueEx(self, key: FakeKey, name: str) -> tuple[Any, int]:
        if name not in key.values:
            raise OSError("Value not found")
        return key.values[name], 1


def test_registry_scanner_reads_application_metadata(monkeypatch: Any) -> None:
    registry = FakeRegistry(
        {
            "ExampleApp": {
                "DisplayName": "Example App",
                "DisplayVersion": "2.4.1",
                "Publisher": "Example Publisher",
                "InstallLocation": r"C:\Program Files\Example",
            }
        }
    )
    monkeypatch.setattr(
        "rekit.scanners.registry_scanner.import_module",
        lambda name: registry,
    )

    result = RegistryScanner().scan()

    assert result.source is ApplicationSource.REGISTRY
    assert len(result.applications) == 4
    assert all(
        application.name == "Example App" for application in result.applications
    )
    assert all(
        application.version == "2.4.1" for application in result.applications
    )
    assert all(
        application.publisher == "Example Publisher"
        for application in result.applications
    )
    assert all(
        application.install_location == r"C:\Program Files\Example"
        for application in result.applications
    )


def test_registry_scanner_skips_entries_without_display_name(
    monkeypatch: Any,
) -> None:
    registry = FakeRegistry(
        {
            "UnnamedEntry": {
                "DisplayVersion": "1.0",
            }
        }
    )
    monkeypatch.setattr(
        "rekit.scanners.registry_scanner.import_module",
        lambda name: registry,
    )

    result = RegistryScanner().scan()

    assert result.applications == []


def test_registry_scanner_skips_system_components(monkeypatch: Any) -> None:
    registry = FakeRegistry(
        {
            "SystemComponent": {
                "DisplayName": "Internal Component",
                "SystemComponent": 1,
            }
        }
    )
    monkeypatch.setattr(
        "rekit.scanners.registry_scanner.import_module",
        lambda name: registry,
    )

    result = RegistryScanner().scan()

    assert result.applications == []


def test_registry_scanner_reports_unavailable_platform(
    monkeypatch: Any,
) -> None:
    def raise_import_error(name: str) -> Any:
        raise ImportError(name)

    monkeypatch.setattr(
        "rekit.scanners.registry_scanner.import_module",
        raise_import_error,
    )

    result = RegistryScanner().scan()

    assert result.applications == []
    assert result.errors == ["Windows Registry is only available on Windows."]
