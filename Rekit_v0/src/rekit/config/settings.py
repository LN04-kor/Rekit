from pathlib import Path


def default_catalog_path() -> Path:
    return Path.home() / ".rekit" / "applications.json"
