import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.config import STORAGE_CONFIG  # noqa: E402
from app.storage import MemoryStorage, SQLiteStorage, SQLCipherStorage  # noqa: E402


def main():
    backend = STORAGE_CONFIG["backend"]
    if backend == "memory":
        print("Storage backend: memory (sin base de datos).")
        return 0
    if backend == "sqlite":
        SQLiteStorage(db_path=STORAGE_CONFIG["db_path"])
        print(f"Storage backend: sqlite ({STORAGE_CONFIG['db_path']}).")
        return 0
    if backend == "sqlcipher":
        SQLCipherStorage(
            db_path=STORAGE_CONFIG["db_path"],
            db_key=STORAGE_CONFIG["db_key"],
        )
        print(f"Storage backend: sqlcipher ({STORAGE_CONFIG['db_path']}).")
        return 0
    print(f"Storage backend no soportado: {backend}", file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
