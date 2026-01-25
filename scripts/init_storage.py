import sys

from app.config import STORAGE_CONFIG
from app.storage import MemoryStorage, SQLiteStorage, SQLCipherStorage


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
