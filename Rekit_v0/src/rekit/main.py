from rekit.catalog.manager import ApplicationCatalog
from rekit.cli.commands import run_command
from rekit.config.settings import default_catalog_path
from rekit.storage.json_storage import JsonApplicationStorage


def main() -> int:
    storage = JsonApplicationStorage(default_catalog_path())
    catalog = ApplicationCatalog(storage)
    return run_command(catalog)


if __name__ == "__main__":
    raise SystemExit(main())
