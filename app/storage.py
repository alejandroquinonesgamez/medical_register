"""
Sistema de almacenamiento abstracto

Este módulo define la interfaz abstracta y las clases de datos (DTOs) para el sistema
de almacenamiento de la aplicación. Proporciona:

1. Clases de datos (DTOs):
   - UserData: Representa los datos de un usuario (nombre, apellidos, fecha de nacimiento, altura)
   - WeightEntryData: Representa una entrada de peso con fecha y hora

2. Interfaz abstracta StorageInterface:
   - Define los métodos que debe implementar cualquier almacenamiento (memoria, base de datos, etc.)

3. Implementación concreta MemoryStorage:
   - Almacenamiento en memoria (diccionarios Python)
   - Los datos se pierden al reiniciar el servidor
   - Útil para desarrollo y pruebas

El sistema está diseñado para ser extensible, permitiendo implementar almacenamiento
persistente (base de datos, archivos, etc.) sin cambiar el código que lo usa.
"""
from abc import ABC, abstractmethod
from datetime import datetime, date
from typing import Optional
import os
import sqlite3
try:
    from .config import STORAGE_CONFIG
except ImportError:
    STORAGE_CONFIG = {
        "backend": os.environ.get("STORAGE_BACKEND", "sqlite"),
        "db_path": os.environ.get("SQLITE_DB_PATH", os.path.join(os.getcwd(), "data", "app.db")),
        "db_key": os.environ.get("SQLCIPHER_KEY", ""),
    }

try:
    from pysqlcipher3 import dbapi2 as sqlcipher
except ImportError:
    sqlcipher = None


class UserData:
    """Clase de datos para usuario (DTO)"""
    def __init__(self, user_id: int, first_name: str, last_name: str, 
                 birth_date: date, height_m: float):
        self.user_id = user_id
        self.first_name = first_name
        self.last_name = last_name
        self.birth_date = birth_date
        self.height_m = height_m
    
    def to_dict(self):
        """Convierte a diccionario para serialización JSON"""
        return {
            'user_id': self.user_id,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'birth_date': self.birth_date.isoformat(),
            'height_m': self.height_m
        }
    
    @classmethod
    def from_dict(cls, data):
        """Crea desde diccionario"""
        return cls(
            user_id=data['user_id'],
            first_name=data['first_name'],
            last_name=data['last_name'],
            birth_date=date.fromisoformat(data['birth_date']),
            height_m=data['height_m']
        )


class WeightEntryData:
    """Clase de datos para entrada de peso (DTO)"""
    def __init__(self, entry_id: int, user_id: int, weight_kg: float, 
                 recorded_date: datetime):
        self.entry_id = entry_id
        self.user_id = user_id
        self.weight_kg = weight_kg
        self.recorded_date = recorded_date
    
    def to_dict(self):
        """Convierte a diccionario para serialización JSON"""
        return {
            'entry_id': self.entry_id,
            'user_id': self.user_id,
            'weight_kg': self.weight_kg,
            'recorded_date': self.recorded_date.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data):
        """Crea desde diccionario"""
        return cls(
            entry_id=data['entry_id'],
            user_id=data['user_id'],
            weight_kg=data['weight_kg'],
            recorded_date=datetime.fromisoformat(data['recorded_date'])
        )


class AuthUserData:
    """Clase de datos para autenticación de usuario"""
    def __init__(self, user_id: int, username: str, password_hash: str,
                 created_at: datetime, role: str = "user"):
        self.user_id = user_id
        self.username = username
        self.password_hash = password_hash
        self.created_at = created_at
        self.role = role


class StorageInterface(ABC):
    """Interfaz abstracta para el almacenamiento"""
    
    @abstractmethod
    def get_user(self, user_id: int) -> Optional[UserData]:
        """Obtiene un usuario por ID"""
        pass
    
    @abstractmethod
    def save_user(self, user: UserData) -> None:
        """Guarda o actualiza un usuario"""
        pass

    @abstractmethod
    def create_auth_user(self, username: str, password_hash: str) -> AuthUserData:
        """Crea un usuario autenticable"""
        pass

    @abstractmethod
    def get_auth_user_by_username(self, username: str) -> Optional[AuthUserData]:
        """Obtiene usuario por username"""
        pass

    @abstractmethod
    def get_auth_user_by_id(self, user_id: int) -> Optional[AuthUserData]:
        """Obtiene usuario por ID (auth)"""
        pass

    @abstractmethod
    def update_password_hash(self, user_id: int, password_hash: str) -> None:
        """Actualiza el hash de contraseña"""
        pass

    @abstractmethod
    def save_api_token(self, user_id: int, token_hash: str, expires_at: datetime) -> None:
        """Guarda un token API"""
        pass

    @abstractmethod
    def get_user_id_by_token_hash(self, token_hash: str) -> Optional[int]:
        """Obtiene user_id por token hash"""
        pass

    @abstractmethod
    def revoke_api_token(self, token_hash: str) -> None:
        """Revoca un token API"""
        pass
    
    @abstractmethod
    def get_last_weight_entry(self, user_id: int) -> Optional[WeightEntryData]:
        """Obtiene la última entrada de peso de un usuario"""
        pass
    
    @abstractmethod
    def get_last_weight_entry_from_different_date(self, user_id: int, reference_date: date) -> Optional[WeightEntryData]:
        """Obtiene la última entrada de peso de un usuario de una fecha diferente a la referencia"""
        pass
    
    @abstractmethod
    def add_weight_entry(self, entry: WeightEntryData) -> None:
        """Añade una nueva entrada de peso. Si ya existe una entrada del mismo día, la reemplaza"""
        pass
    
    @abstractmethod
    def get_weight_count(self, user_id: int) -> int:
        """Obtiene el número de entradas de peso de un usuario"""
        pass
    
    @abstractmethod
    def get_max_weight(self, user_id: int) -> Optional[float]:
        """Obtiene el peso máximo de un usuario"""
        pass
    
    @abstractmethod
    def get_min_weight(self, user_id: int) -> Optional[float]:
        """Obtiene el peso mínimo de un usuario"""
        pass

    @abstractmethod
    def get_all_weight_entries(self, user_id: int) -> list:
        """Obtiene todas las entradas de peso de un usuario"""
        pass

    @abstractmethod
    def blacklist_token(self, jti: str, expires_at: datetime) -> None:
        """Añade un JTI (JWT ID) a la blacklist para revocar el token"""
        pass

    @abstractmethod
    def is_token_blacklisted(self, jti: str) -> bool:
        """Comprueba si un JTI (JWT ID) está en la blacklist"""
        pass

    @abstractmethod
    def cleanup_expired_blacklist(self) -> int:
        """Elimina entradas expiradas de la blacklist. Retorna nº de entradas eliminadas."""
        pass

    @abstractmethod
    def count_auth_users(self) -> int:
        """Cuenta el número total de usuarios registrados (para asignar rol admin al primero)."""
        pass

    @abstractmethod
    def update_user_role(self, user_id: int, role: str) -> bool:
        """Actualiza el rol de un usuario. Devuelve True si se actualizó."""
        pass


class MemoryStorage(StorageInterface):
    """Implementación de almacenamiento en memoria"""
    
    def __init__(self):
        self._users = {}  # {user_id: UserData}
        self._auth_users = {}  # {user_id: AuthUserData}
        self._auth_users_by_username = {}  # {username: AuthUserData}
        self._api_tokens = {}  # {token_hash: (user_id, expires_at)}
        self._token_blacklist = {}  # {jti: expires_at}
        self._weight_entries = []  # List[WeightEntryData]
        self._next_entry_id = 1
        self._next_user_id = 1
    
    def get_user(self, user_id: int) -> Optional[UserData]:
        return self._users.get(user_id)
    
    def save_user(self, user: UserData) -> None:
        self._users[user.user_id] = user

    def create_auth_user(self, username: str, password_hash: str,
                         role: str = "user") -> AuthUserData:
        user = AuthUserData(
            user_id=self._next_user_id,
            username=username,
            password_hash=password_hash,
            created_at=datetime.now(),
            role=role,
        )
        self._next_user_id += 1
        self._auth_users[user.user_id] = user
        self._auth_users_by_username[username] = user
        return user

    def get_auth_user_by_username(self, username: str) -> Optional[AuthUserData]:
        return self._auth_users_by_username.get(username)

    def get_auth_user_by_id(self, user_id: int) -> Optional[AuthUserData]:
        return self._auth_users.get(user_id)

    def update_password_hash(self, user_id: int, password_hash: str) -> None:
        user = self._auth_users.get(user_id)
        if user:
            user.password_hash = password_hash

    def save_api_token(self, user_id: int, token_hash: str, expires_at: datetime) -> None:
        self._api_tokens[token_hash] = (user_id, expires_at)

    def get_user_id_by_token_hash(self, token_hash: str) -> Optional[int]:
        token_data = self._api_tokens.get(token_hash)
        if not token_data:
            return None
        user_id, expires_at = token_data
        if expires_at < datetime.now():
            self._api_tokens.pop(token_hash, None)
            return None
        return user_id

    def revoke_api_token(self, token_hash: str) -> None:
        self._api_tokens.pop(token_hash, None)
    
    def get_last_weight_entry(self, user_id: int) -> Optional[WeightEntryData]:
        user_entries = [e for e in self._weight_entries if e.user_id == user_id]
        if not user_entries:
            return None
        return max(user_entries, key=lambda e: e.recorded_date)
    
    def get_last_weight_entry_from_different_date(self, user_id: int, reference_date: date) -> Optional[WeightEntryData]:
        """Obtiene la última entrada de peso de un día diferente a la fecha de referencia"""
        user_entries = [e for e in self._weight_entries if e.user_id == user_id]
        if not user_entries:
            return None
        
        # Filtrar entradas de fechas diferentes a la referencia
        different_date_entries = [
            e for e in user_entries 
            if e.recorded_date.date() != reference_date
        ]
        
        if not different_date_entries:
            return None
        
        return max(different_date_entries, key=lambda e: e.recorded_date)
    
    def add_weight_entry(self, entry: WeightEntryData) -> None:
        entry_date = entry.recorded_date.date()
        
        # Eliminar entradas del mismo día para el mismo usuario
        self._weight_entries = [
            e for e in self._weight_entries 
            if not (e.user_id == entry.user_id and e.recorded_date.date() == entry_date)
        ]
        
        # Añadir la nueva entrada
        entry.entry_id = self._next_entry_id
        self._next_entry_id += 1
        self._weight_entries.append(entry)
    
    def get_weight_count(self, user_id: int) -> int:
        return len([e for e in self._weight_entries if e.user_id == user_id])
    
    def get_max_weight(self, user_id: int) -> Optional[float]:
        user_entries = [e for e in self._weight_entries if e.user_id == user_id]
        if not user_entries:
            return None
        return max(e.weight_kg for e in user_entries)
    
    def get_min_weight(self, user_id: int) -> Optional[float]:
        user_entries = [e for e in self._weight_entries if e.user_id == user_id]
        if not user_entries:
            return None
        return min(e.weight_kg for e in user_entries)
    
    def get_all_weight_entries(self, user_id: int) -> list:
        """Obtiene todas las entradas de peso de un usuario, ordenadas por fecha descendente"""
        user_entries = [e for e in self._weight_entries if e.user_id == user_id]
        return sorted(user_entries, key=lambda e: e.recorded_date, reverse=True)

    def blacklist_token(self, jti: str, expires_at: datetime) -> None:
        self._token_blacklist[jti] = expires_at

    def is_token_blacklisted(self, jti: str) -> bool:
        expires_at = self._token_blacklist.get(jti)
        if expires_at is None:
            return False
        if expires_at < datetime.now():
            self._token_blacklist.pop(jti, None)
            return False
        return True

    def cleanup_expired_blacklist(self) -> int:
        now = datetime.now()
        expired = [jti for jti, exp in self._token_blacklist.items() if exp < now]
        for jti in expired:
            del self._token_blacklist[jti]
        return len(expired)

    def count_auth_users(self) -> int:
        return len(self._auth_users)

    def update_user_role(self, user_id: int, role: str) -> bool:
        user = self._auth_users.get(user_id)
        if not user:
            return False
        user.role = role
        return True


class SQLCipherStorage(StorageInterface):
    """Almacenamiento persistente cifrado con SQLCipher"""

    def __init__(self, db_path: Optional[str] = None, db_key: Optional[str] = None):
        if sqlcipher is None:
            raise RuntimeError("SQLCipher no está disponible. Instala pysqlcipher3.")
        self._db_path = db_path or STORAGE_CONFIG["db_path"]
        self._db_key = db_key or STORAGE_CONFIG["db_key"]
        if not self._db_key:
            raise RuntimeError("SQLCIPHER_KEY no configurada.")
        os.makedirs(os.path.dirname(self._db_path), exist_ok=True)
        self._init_db()

    def _connect(self):
        conn = sqlcipher.connect(self._db_path)
        escaped_key = self._db_key.replace("'", "''")
        conn.execute(f"PRAGMA key = '{escaped_key}'")
        conn.execute("PRAGMA foreign_keys = ON;")
        conn.execute("PRAGMA journal_mode = WAL;")
        conn.execute("PRAGMA cipher_memory_security = ON;")
        conn.row_factory = sqlcipher.Row
        return conn

    def _init_db(self):
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE NOT NULL,
                    password_hash TEXT NOT NULL,
                    role TEXT NOT NULL DEFAULT 'user',
                    first_name TEXT,
                    last_name TEXT,
                    birth_date TEXT,
                    height_m REAL,
                    created_at TEXT NOT NULL
                )
                """
            )
            # Migración: añadir columna role si no existe (BD anteriores)
            try:
                conn.execute("ALTER TABLE users ADD COLUMN role TEXT NOT NULL DEFAULT 'user'")
            except Exception:
                pass
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS weights (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    weight_kg REAL NOT NULL,
                    recorded_date TEXT NOT NULL,
                    FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS api_tokens (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    token_hash TEXT NOT NULL UNIQUE,
                    expires_at TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS token_blacklist (
                    jti TEXT PRIMARY KEY NOT NULL,
                    expires_at TEXT NOT NULL
                )
                """
            )

    def get_user(self, user_id: int) -> Optional[UserData]:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT id, first_name, last_name, birth_date, height_m FROM users WHERE id = ?",
                (user_id,),
            ).fetchone()
            if not row or row["birth_date"] is None:
                return None
            return UserData(
                user_id=row["id"],
                first_name=row["first_name"],
                last_name=row["last_name"],
                birth_date=date.fromisoformat(row["birth_date"]),
                height_m=row["height_m"],
            )

    def save_user(self, user: UserData) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                UPDATE users
                SET first_name = ?, last_name = ?, birth_date = ?, height_m = ?
                WHERE id = ?
                """,
                (
                    user.first_name,
                    user.last_name,
                    user.birth_date.isoformat(),
                    user.height_m,
                    user.user_id,
                ),
            )

    def create_auth_user(self, username: str, password_hash: str,
                         role: str = "user") -> AuthUserData:
        now = datetime.now().isoformat()
        with self._connect() as conn:
            cursor = conn.execute(
                "INSERT INTO users (username, password_hash, role, created_at) VALUES (?, ?, ?, ?)",
                (username, password_hash, role, now),
            )
            user_id = cursor.lastrowid
        return AuthUserData(
            user_id=user_id,
            username=username,
            password_hash=password_hash,
            created_at=datetime.fromisoformat(now),
            role=role,
        )

    def get_auth_user_by_username(self, username: str) -> Optional[AuthUserData]:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT id, username, password_hash, role, created_at FROM users WHERE username = ?",
                (username,),
            ).fetchone()
            if not row:
                return None
            return AuthUserData(
                user_id=row["id"],
                username=row["username"],
                password_hash=row["password_hash"],
                created_at=datetime.fromisoformat(row["created_at"]),
                role=row["role"],
            )

    def get_auth_user_by_id(self, user_id: int) -> Optional[AuthUserData]:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT id, username, password_hash, role, created_at FROM users WHERE id = ?",
                (user_id,),
            ).fetchone()
            if not row:
                return None
            return AuthUserData(
                user_id=row["id"],
                username=row["username"],
                password_hash=row["password_hash"],
                created_at=datetime.fromisoformat(row["created_at"]),
                role=row["role"],
            )

    def update_password_hash(self, user_id: int, password_hash: str) -> None:
        with self._connect() as conn:
            conn.execute(
                "UPDATE users SET password_hash = ? WHERE id = ?",
                (password_hash, user_id),
            )

    def save_api_token(self, user_id: int, token_hash: str, expires_at: datetime) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO api_tokens (user_id, token_hash, expires_at, created_at)
                VALUES (?, ?, ?, ?)
                """,
                (user_id, token_hash, expires_at.isoformat(), datetime.now().isoformat()),
            )

    def get_user_id_by_token_hash(self, token_hash: str) -> Optional[int]:
        now = datetime.now().isoformat()
        with self._connect() as conn:
            row = conn.execute(
                "SELECT user_id FROM api_tokens WHERE token_hash = ? AND expires_at > ?",
                (token_hash, now),
            ).fetchone()
            if not row:
                return None
            return row["user_id"]

    def revoke_api_token(self, token_hash: str) -> None:
        with self._connect() as conn:
            conn.execute("DELETE FROM api_tokens WHERE token_hash = ?", (token_hash,))

    def blacklist_token(self, jti: str, expires_at: datetime) -> None:
        with self._connect() as conn:
            conn.execute(
                "INSERT OR REPLACE INTO token_blacklist (jti, expires_at) VALUES (?, ?)",
                (jti, expires_at.isoformat()),
            )

    def is_token_blacklisted(self, jti: str) -> bool:
        now = datetime.now().isoformat()
        with self._connect() as conn:
            row = conn.execute(
                "SELECT 1 FROM token_blacklist WHERE jti = ? AND expires_at > ?",
                (jti, now),
            ).fetchone()
            return row is not None

    def cleanup_expired_blacklist(self) -> int:
        now = datetime.now().isoformat()
        with self._connect() as conn:
            cursor = conn.execute(
                "DELETE FROM token_blacklist WHERE expires_at <= ?", (now,)
            )
            return cursor.rowcount

    def count_auth_users(self) -> int:
        with self._connect() as conn:
            row = conn.execute("SELECT COUNT(*) AS count FROM users").fetchone()
            return int(row["count"]) if row else 0

    def update_user_role(self, user_id: int, role: str) -> bool:
        with self._connect() as conn:
            cursor = conn.execute(
                "UPDATE users SET role = ? WHERE id = ?", (role, user_id)
            )
            return cursor.rowcount > 0

    def get_last_weight_entry(self, user_id: int) -> Optional[WeightEntryData]:
        with self._connect() as conn:
            row = conn.execute(
                """
                SELECT id, user_id, weight_kg, recorded_date
                FROM weights WHERE user_id = ?
                ORDER BY recorded_date DESC LIMIT 1
                """,
                (user_id,),
            ).fetchone()
            if not row:
                return None
            return WeightEntryData(
                entry_id=row["id"],
                user_id=row["user_id"],
                weight_kg=row["weight_kg"],
                recorded_date=datetime.fromisoformat(row["recorded_date"]),
            )

    def get_last_weight_entry_from_different_date(self, user_id: int, reference_date: date) -> Optional[WeightEntryData]:
        with self._connect() as conn:
            row = conn.execute(
                """
                SELECT id, user_id, weight_kg, recorded_date
                FROM weights
                WHERE user_id = ? AND date(recorded_date) != date(?)
                ORDER BY recorded_date DESC LIMIT 1
                """,
                (user_id, reference_date.isoformat()),
            ).fetchone()
            if not row:
                return None
            return WeightEntryData(
                entry_id=row["id"],
                user_id=row["user_id"],
                weight_kg=row["weight_kg"],
                recorded_date=datetime.fromisoformat(row["recorded_date"]),
            )

    def add_weight_entry(self, entry: WeightEntryData) -> None:
        with self._connect() as conn:
            conn.execute(
                "DELETE FROM weights WHERE user_id = ? AND date(recorded_date) = date(?)",
                (entry.user_id, entry.recorded_date.isoformat()),
            )
            cursor = conn.execute(
                "INSERT INTO weights (user_id, weight_kg, recorded_date) VALUES (?, ?, ?)",
                (entry.user_id, entry.weight_kg, entry.recorded_date.isoformat()),
            )
            entry.entry_id = cursor.lastrowid

    def get_weight_count(self, user_id: int) -> int:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT COUNT(*) AS count FROM weights WHERE user_id = ?",
                (user_id,),
            ).fetchone()
            return int(row["count"]) if row else 0

    def get_max_weight(self, user_id: int) -> Optional[float]:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT MAX(weight_kg) AS max_weight FROM weights WHERE user_id = ?",
                (user_id,),
            ).fetchone()
            return row["max_weight"] if row and row["max_weight"] is not None else None

    def get_min_weight(self, user_id: int) -> Optional[float]:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT MIN(weight_kg) AS min_weight FROM weights WHERE user_id = ?",
                (user_id,),
            ).fetchone()
            return row["min_weight"] if row and row["min_weight"] is not None else None

    def get_all_weight_entries(self, user_id: int) -> list:
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT id, user_id, weight_kg, recorded_date
                FROM weights WHERE user_id = ?
                ORDER BY recorded_date DESC
                """,
                (user_id,),
            ).fetchall()
            return [
                WeightEntryData(
                    entry_id=row["id"],
                    user_id=row["user_id"],
                    weight_kg=row["weight_kg"],
                    recorded_date=datetime.fromisoformat(row["recorded_date"]),
                )
                for row in rows
            ]


class SQLiteStorage(StorageInterface):
    """Almacenamiento persistente con SQLite (sin cifrado)"""

    def __init__(self, db_path: Optional[str] = None):
        self._db_path = db_path or STORAGE_CONFIG["db_path"]
        os.makedirs(os.path.dirname(self._db_path), exist_ok=True)
        self._init_db()

    def _connect(self):
        conn = sqlite3.connect(self._db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON;")
        conn.execute("PRAGMA journal_mode = WAL;")
        return conn

    def _init_db(self):
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE NOT NULL,
                    password_hash TEXT NOT NULL,
                    role TEXT NOT NULL DEFAULT 'user',
                    first_name TEXT,
                    last_name TEXT,
                    birth_date TEXT,
                    height_m REAL,
                    created_at TEXT NOT NULL
                )
                """
            )
            # Migración: añadir columna role si no existe (BD anteriores)
            try:
                conn.execute("ALTER TABLE users ADD COLUMN role TEXT NOT NULL DEFAULT 'user'")
            except Exception:
                pass
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS weights (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    weight_kg REAL NOT NULL,
                    recorded_date TEXT NOT NULL,
                    FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS api_tokens (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    token_hash TEXT NOT NULL UNIQUE,
                    expires_at TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS token_blacklist (
                    jti TEXT PRIMARY KEY NOT NULL,
                    expires_at TEXT NOT NULL
                )
                """
            )

    def get_user(self, user_id: int) -> Optional[UserData]:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT id, first_name, last_name, birth_date, height_m FROM users WHERE id = ?",
                (user_id,),
            ).fetchone()
            if not row or row["birth_date"] is None:
                return None
            return UserData(
                user_id=row["id"],
                first_name=row["first_name"],
                last_name=row["last_name"],
                birth_date=date.fromisoformat(row["birth_date"]),
                height_m=row["height_m"],
            )

    def save_user(self, user: UserData) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                UPDATE users
                SET first_name = ?, last_name = ?, birth_date = ?, height_m = ?
                WHERE id = ?
                """,
                (
                    user.first_name,
                    user.last_name,
                    user.birth_date.isoformat(),
                    user.height_m,
                    user.user_id,
                ),
            )

    def create_auth_user(self, username: str, password_hash: str,
                         role: str = "user") -> AuthUserData:
        now = datetime.now().isoformat()
        with self._connect() as conn:
            cursor = conn.execute(
                "INSERT INTO users (username, password_hash, role, created_at) VALUES (?, ?, ?, ?)",
                (username, password_hash, role, now),
            )
            user_id = cursor.lastrowid
        return AuthUserData(
            user_id=user_id,
            username=username,
            password_hash=password_hash,
            created_at=datetime.fromisoformat(now),
            role=role,
        )

    def get_auth_user_by_username(self, username: str) -> Optional[AuthUserData]:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT id, username, password_hash, role, created_at FROM users WHERE username = ?",
                (username,),
            ).fetchone()
            if not row:
                return None
            return AuthUserData(
                user_id=row["id"],
                username=row["username"],
                password_hash=row["password_hash"],
                created_at=datetime.fromisoformat(row["created_at"]),
                role=row["role"],
            )

    def get_auth_user_by_id(self, user_id: int) -> Optional[AuthUserData]:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT id, username, password_hash, role, created_at FROM users WHERE id = ?",
                (user_id,),
            ).fetchone()
            if not row:
                return None
            return AuthUserData(
                user_id=row["id"],
                username=row["username"],
                password_hash=row["password_hash"],
                created_at=datetime.fromisoformat(row["created_at"]),
                role=row["role"],
            )

    def update_password_hash(self, user_id: int, password_hash: str) -> None:
        with self._connect() as conn:
            conn.execute(
                "UPDATE users SET password_hash = ? WHERE id = ?",
                (password_hash, user_id),
            )

    def save_api_token(self, user_id: int, token_hash: str, expires_at: datetime) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO api_tokens (user_id, token_hash, expires_at, created_at)
                VALUES (?, ?, ?, ?)
                """,
                (user_id, token_hash, expires_at.isoformat(), datetime.now().isoformat()),
            )

    def get_user_id_by_token_hash(self, token_hash: str) -> Optional[int]:
        now = datetime.now().isoformat()
        with self._connect() as conn:
            row = conn.execute(
                "SELECT user_id FROM api_tokens WHERE token_hash = ? AND expires_at > ?",
                (token_hash, now),
            ).fetchone()
            if not row:
                return None
            return row["user_id"]

    def revoke_api_token(self, token_hash: str) -> None:
        with self._connect() as conn:
            conn.execute("DELETE FROM api_tokens WHERE token_hash = ?", (token_hash,))

    def blacklist_token(self, jti: str, expires_at: datetime) -> None:
        with self._connect() as conn:
            conn.execute(
                "INSERT OR REPLACE INTO token_blacklist (jti, expires_at) VALUES (?, ?)",
                (jti, expires_at.isoformat()),
            )

    def is_token_blacklisted(self, jti: str) -> bool:
        now = datetime.now().isoformat()
        with self._connect() as conn:
            row = conn.execute(
                "SELECT 1 FROM token_blacklist WHERE jti = ? AND expires_at > ?",
                (jti, now),
            ).fetchone()
            return row is not None

    def cleanup_expired_blacklist(self) -> int:
        now = datetime.now().isoformat()
        with self._connect() as conn:
            cursor = conn.execute(
                "DELETE FROM token_blacklist WHERE expires_at <= ?", (now,)
            )
            return cursor.rowcount

    def count_auth_users(self) -> int:
        with self._connect() as conn:
            row = conn.execute("SELECT COUNT(*) AS count FROM users").fetchone()
            return int(row["count"]) if row else 0

    def update_user_role(self, user_id: int, role: str) -> bool:
        with self._connect() as conn:
            cursor = conn.execute(
                "UPDATE users SET role = ? WHERE id = ?", (role, user_id)
            )
            return cursor.rowcount > 0

    def get_last_weight_entry(self, user_id: int) -> Optional[WeightEntryData]:
        with self._connect() as conn:
            row = conn.execute(
                """
                SELECT id, user_id, weight_kg, recorded_date
                FROM weights WHERE user_id = ?
                ORDER BY recorded_date DESC LIMIT 1
                """,
                (user_id,),
            ).fetchone()
            if not row:
                return None
            return WeightEntryData(
                entry_id=row["id"],
                user_id=row["user_id"],
                weight_kg=row["weight_kg"],
                recorded_date=datetime.fromisoformat(row["recorded_date"]),
            )

    def get_last_weight_entry_from_different_date(self, user_id: int, reference_date: date) -> Optional[WeightEntryData]:
        with self._connect() as conn:
            row = conn.execute(
                """
                SELECT id, user_id, weight_kg, recorded_date
                FROM weights
                WHERE user_id = ? AND date(recorded_date) != date(?)
                ORDER BY recorded_date DESC LIMIT 1
                """,
                (user_id, reference_date.isoformat()),
            ).fetchone()
            if not row:
                return None
            return WeightEntryData(
                entry_id=row["id"],
                user_id=row["user_id"],
                weight_kg=row["weight_kg"],
                recorded_date=datetime.fromisoformat(row["recorded_date"]),
            )

    def add_weight_entry(self, entry: WeightEntryData) -> None:
        with self._connect() as conn:
            conn.execute(
                "DELETE FROM weights WHERE user_id = ? AND date(recorded_date) = date(?)",
                (entry.user_id, entry.recorded_date.isoformat()),
            )
            cursor = conn.execute(
                "INSERT INTO weights (user_id, weight_kg, recorded_date) VALUES (?, ?, ?)",
                (entry.user_id, entry.weight_kg, entry.recorded_date.isoformat()),
            )
            entry.entry_id = cursor.lastrowid

    def get_weight_count(self, user_id: int) -> int:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT COUNT(*) AS count FROM weights WHERE user_id = ?",
                (user_id,),
            ).fetchone()
            return int(row["count"]) if row else 0

    def get_max_weight(self, user_id: int) -> Optional[float]:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT MAX(weight_kg) AS max_weight FROM weights WHERE user_id = ?",
                (user_id,),
            ).fetchone()
            return row["max_weight"] if row and row["max_weight"] is not None else None

    def get_min_weight(self, user_id: int) -> Optional[float]:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT MIN(weight_kg) AS min_weight FROM weights WHERE user_id = ?",
                (user_id,),
            ).fetchone()
            return row["min_weight"] if row and row["min_weight"] is not None else None

    def get_all_weight_entries(self, user_id: int) -> list:
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT id, user_id, weight_kg, recorded_date
                FROM weights WHERE user_id = ?
                ORDER BY recorded_date DESC
                """,
                (user_id,),
            ).fetchall()
            return [
                WeightEntryData(
                    entry_id=row["id"],
                    user_id=row["user_id"],
                    weight_kg=row["weight_kg"],
                    recorded_date=datetime.fromisoformat(row["recorded_date"]),
                )
                for row in rows
            ]

