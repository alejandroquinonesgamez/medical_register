"""
Tests de caja blanca para backends de almacenamiento (sqlite/sqlcipher)
"""
from datetime import datetime, date, timedelta
import pytest

import app.storage as storage_mod
from app.storage import SQLiteStorage, SQLCipherStorage, UserData, WeightEntryData


def _seed_storage(storage):
    auth_user = storage.create_auth_user("usuario_db", "hash_dummy")
    storage.save_user(UserData(
        user_id=auth_user.user_id,
        first_name="Test",
        last_name="Usuario",
        birth_date=date(1990, 1, 1),
        height_m=1.7,
    ))

    now = datetime.now()
    entries = [
        WeightEntryData(entry_id=0, user_id=auth_user.user_id, weight_kg=70.0, recorded_date=now - timedelta(days=2)),
        WeightEntryData(entry_id=0, user_id=auth_user.user_id, weight_kg=71.5, recorded_date=now - timedelta(days=1)),
    ]
    for entry in entries:
        storage.add_weight_entry(entry)

    return auth_user, entries


def test_sqlite_storage_crud(tmp_path):
    db_path = tmp_path / "app.db"
    storage = SQLiteStorage(db_path=str(db_path))

    auth_user, entries = _seed_storage(storage)

    fetched = storage.get_auth_user_by_username("usuario_db")
    assert fetched is not None
    assert fetched.user_id == auth_user.user_id

    user = storage.get_user(auth_user.user_id)
    assert user is not None
    assert user.first_name == "Test"

    last = storage.get_last_weight_entry(auth_user.user_id)
    assert last is not None
    assert last.weight_kg == entries[1].weight_kg

    assert storage.get_weight_count(auth_user.user_id) == 2
    assert storage.get_max_weight(auth_user.user_id) == 71.5
    assert storage.get_min_weight(auth_user.user_id) == 70.0

    all_entries = storage.get_all_weight_entries(auth_user.user_id)
    assert len(all_entries) == 2


def test_sqlcipher_storage_requires_key(tmp_path):
    if storage_mod.sqlcipher is None:
        pytest.skip("SQLCipher no está disponible")
    db_path = tmp_path / "secure.db"
    with pytest.raises(RuntimeError):
        SQLCipherStorage(db_path=str(db_path), db_key="")


def test_sqlcipher_storage_crud(tmp_path):
    if storage_mod.sqlcipher is None:
        pytest.skip("SQLCipher no está disponible")
    db_path = tmp_path / "secure.db"
    storage = SQLCipherStorage(db_path=str(db_path), db_key="clave_secreta")

    auth_user, _ = _seed_storage(storage)
    assert db_path.exists()

    fetched = storage.get_auth_user_by_id(auth_user.user_id)
    assert fetched is not None
    assert fetched.username == "usuario_db"
