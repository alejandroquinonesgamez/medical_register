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


class MemoryStorage(StorageInterface):
    """Implementación de almacenamiento en memoria"""
    
    def __init__(self):
        self._users = {}  # {user_id: UserData}
        self._weight_entries = []  # List[WeightEntryData]
        self._next_entry_id = 1
    
    def get_user(self, user_id: int) -> Optional[UserData]:
        return self._users.get(user_id)
    
    def save_user(self, user: UserData) -> None:
        self._users[user.user_id] = user
    
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





