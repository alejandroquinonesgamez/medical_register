"""
Tests de CAJA BLANCA para métodos to_dict y from_dict de las clases DTO
Prueban la serialización y deserialización de UserData y WeightEntryData
"""
import pytest
from datetime import datetime, date
from app.storage import UserData, WeightEntryData


class TestUserDataSerialization:
    """Tests de caja blanca para serialización de UserData"""
    
    def test_user_data_to_dict(self):
        """Test que to_dict() convierte UserData a diccionario correctamente"""
        user = UserData(
            user_id=1,
            first_name="Juan",
            last_name="Pérez García",
            birth_date=date(1990, 5, 15),
            height_m=1.75
        )
        result = user.to_dict()
        
        assert isinstance(result, dict)
        assert result['user_id'] == 1
        assert result['first_name'] == "Juan"
        assert result['last_name'] == "Pérez García"
        assert result['birth_date'] == "1990-05-15"  # ISO format
        assert result['height_m'] == 1.75
    
    def test_user_data_from_dict(self):
        """Test que from_dict() crea UserData desde diccionario correctamente"""
        data = {
            'user_id': 1,
            'first_name': 'Juan',
            'last_name': 'Pérez García',
            'birth_date': '1990-05-15',
            'height_m': 1.75
        }
        user = UserData.from_dict(data)
        
        assert isinstance(user, UserData)
        assert user.user_id == 1
        assert user.first_name == "Juan"
        assert user.last_name == "Pérez García"
        assert user.birth_date == date(1990, 5, 15)
        assert user.height_m == 1.75
    
    def test_user_data_round_trip(self):
        """Test que to_dict() y from_dict() son inversos"""
        original = UserData(
            user_id=1,
            first_name="María",
            last_name="García López",
            birth_date=date(1985, 3, 20),
            height_m=1.68
        )
        
        # Convertir a dict y de vuelta
        data = original.to_dict()
        restored = UserData.from_dict(data)
        
        assert restored.user_id == original.user_id
        assert restored.first_name == original.first_name
        assert restored.last_name == original.last_name
        assert restored.birth_date == original.birth_date
        assert restored.height_m == original.height_m


class TestWeightEntryDataSerialization:
    """Tests de caja blanca para serialización de WeightEntryData"""
    
    def test_weight_entry_data_to_dict(self):
        """Test que to_dict() convierte WeightEntryData a diccionario correctamente"""
        entry = WeightEntryData(
            entry_id=1,
            user_id=1,
            weight_kg=70.5,
            recorded_date=datetime(2024, 1, 15, 10, 30, 45)
        )
        result = entry.to_dict()
        
        assert isinstance(result, dict)
        assert result['entry_id'] == 1
        assert result['user_id'] == 1
        assert result['weight_kg'] == 70.5
        assert result['recorded_date'] == "2024-01-15T10:30:45"  # ISO format
    
    def test_weight_entry_data_from_dict(self):
        """Test que from_dict() crea WeightEntryData desde diccionario correctamente"""
        data = {
            'entry_id': 1,
            'user_id': 1,
            'weight_kg': 70.5,
            'recorded_date': '2024-01-15T10:30:45'
        }
        entry = WeightEntryData.from_dict(data)
        
        assert isinstance(entry, WeightEntryData)
        assert entry.entry_id == 1
        assert entry.user_id == 1
        assert entry.weight_kg == 70.5
        assert entry.recorded_date == datetime(2024, 1, 15, 10, 30, 45)
    
    def test_weight_entry_data_round_trip(self):
        """Test que to_dict() y from_dict() son inversos"""
        original = WeightEntryData(
            entry_id=5,
            user_id=1,
            weight_kg=75.3,
            recorded_date=datetime(2024, 2, 1, 14, 20, 10)
        )
        
        # Convertir a dict y de vuelta
        data = original.to_dict()
        restored = WeightEntryData.from_dict(data)
        
        assert restored.entry_id == original.entry_id
        assert restored.user_id == original.user_id
        assert restored.weight_kg == original.weight_kg
        assert restored.recorded_date == original.recorded_date
    
    def test_weight_entry_data_from_dict_with_microseconds(self):
        """Test from_dict() con fecha que incluye microsegundos"""
        data = {
            'entry_id': 1,
            'user_id': 1,
            'weight_kg': 70.5,
            'recorded_date': '2024-01-15T10:30:45.123456'
        }
        entry = WeightEntryData.from_dict(data)
        
        assert entry.recorded_date == datetime(2024, 1, 15, 10, 30, 45, 123456)
