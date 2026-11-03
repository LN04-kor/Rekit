import json
import os
import tempfile
from pathlib import Path

from rekit.models.application import Application


class JsonStorageError(Exception):
    pass


class JsonApplicationStorage:
    def __init__(self, path: Path) -> None:
        self._path = path

    def load(self) -> list[Application]:
        if not self._path.exists():
            return []

        try:
            payload = json.loads(self._path.read_text(encoding="utf-8"))
            if not isinstance(payload, list):
                raise ValueError("The catalog root must be a list.")
            return [Application.model_validate(item) for item in payload]
        except (OSError, UnicodeError, json.JSONDecodeError, ValueError) as error:
            raise JsonStorageError(f"Could not read catalog: {error}") from error

    def save(self, applications: list[Application]) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        payload = [item.model_dump(mode="json") for item in applications]
        temporary_path: Path | None = None

        try:
            with tempfile.NamedTemporaryFile(
                mode="w",
                encoding="utf-8",
                dir=self._path.parent,
                prefix=f".{self._path.name}.",
                suffix=".tmp",
                delete=False,
            ) as temporary_file:
                temporary_path = Path(temporary_file.name)
                json.dump(payload, temporary_file, ensure_ascii=False, indent=2)
                temporary_file.write("\n")
                temporary_file.flush()
                os.fsync(temporary_file.fileno())

            os.replace(temporary_path, self._path)
        except (OSError, TypeError, ValueError) as error:
            raise JsonStorageError(f"Could not save catalog: {error}") from error
        finally:
            if temporary_path is not None:
                temporary_path.unlink(missing_ok=True)
