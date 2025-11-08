"""
Tests de Caja Negra (Black Box Testing)
Prueban la funcionalidad desde la perspectiva del usuario final
sin conocer la implementación interna
"""
import pytest
import math
from tests.conftest import assert_success, assert_created, assert_bad_request, assert_not_found


class TestUserAPIBlackBox:
    """Tests de caja negra para la API de usuario"""
    
    def test_create_user_complete_flow(self, client):
        """Test de flujo completo: crear usuario y recuperarlo"""
        # Crear usuario
        payload = {
            "nombre": "Juan",
            "apellidos": "Pérez",
            "fecha_nacimiento": "1985-05-15",
            "talla_m": 1.80
        }
        response = client.post('/api/user', json=payload)
        assert_success(response)
        
        # Recuperar usuario
        response = client.get('/api/user')
        assert_success(response)
        data = response.get_json()
        assert data["nombre"] == "Juan"
        assert data["apellidos"] == "Pérez"
        assert data["fecha_nacimiento"] == "1985-05-15"
        assert math.isclose(data["talla_m"], 1.80)
    
    def test_update_user_existing(self, client):
        """Test de actualización de usuario existente"""
        # Crear usuario inicial
        client.post('/api/user', json={
            "nombre": "Ana",
            "apellidos": "García",
            "fecha_nacimiento": "1990-01-01",
            "talla_m": 1.65
        })
        
        # Actualizar usuario
        response = client.post('/api/user', json={
            "nombre": "Ana María",
            "apellidos": "García López",
            "fecha_nacimiento": "1990-01-01",
            "talla_m": 1.66
        })
        assert_success(response)
        
        # Verificar cambios
        data = client.get('/api/user').get_json()
        assert data["nombre"] == "Ana María"
        assert data["apellidos"] == "García López"
        assert math.isclose(data["talla_m"], 1.66)
    
    def test_get_user_not_found(self, client):
        """Test de usuario no encontrado"""
        response = client.get('/api/user')
        assert_not_found(response)
        assert "error" in response.get_json()


class TestWeightAPIBlackBox:
    """Tests de caja negra para la API de peso"""
    
    def test_add_weight_complete_flow(self, client):
        """Test de flujo completo: crear usuario, añadir peso, verificar"""
        # Crear usuario
        client.post('/api/user', json={
            "nombre": "Carlos",
            "apellidos": "Ruiz",
            "fecha_nacimiento": "1988-03-20",
            "talla_m": 1.75
        })
        
        # Añadir peso
        response = client.post('/api/weight', json={"peso_kg": 75.5})
        assert_created(response)
        
        # Verificar IMC
        imc_response = client.get('/api/imc')
        assert_success(imc_response)
        imc_data = imc_response.get_json()
        assert imc_data["imc"] > 0
        assert "description" in imc_data
    
    def test_add_multiple_weights(self, client):
        """Test de añadir múltiples pesos en días diferentes"""
        from datetime import datetime, timedelta
        from app.storage import WeightEntryData
        from app.config import USER_ID
        
        client.post('/api/user', json={
            "nombre": "María",
            "apellidos": "Sánchez",
            "fecha_nacimiento": "1992-07-10",
            "talla_m": 1.68
        })
        
        # Añadir pesos en días diferentes usando el storage directamente
        # para simular el comportamiento real
        with client.application.app_context():
            storage = client.application.storage
            base_date = datetime.now()
            weights_data = [
                (65.0, base_date - timedelta(days=2)),
                (66.5, base_date - timedelta(days=1)),
                (67.0, base_date)
            ]
            for weight_kg, weight_date in weights_data:
                entry = WeightEntryData(
                    entry_id=0,
                    user_id=USER_ID,
                    weight_kg=weight_kg,
                    recorded_date=weight_date
                )
                storage.add_weight_entry(entry)
        
        # Verificar estadísticas
        stats = client.get('/api/stats').get_json()
        assert stats["num_pesajes"] == 3
        assert stats["peso_max"] == 67.0
        assert stats["peso_min"] == 65.0
    
    def test_add_weight_same_day_replaces(self, client):
        """Test que múltiples pesos del mismo día reemplazan al anterior"""
        client.post('/api/user', json={
            "nombre": "Test",
            "apellidos": "User",
            "fecha_nacimiento": "1990-01-01",
            "talla_m": 1.75
        })
        
        # Añadir primer peso del día
        response1 = client.post('/api/weight', json={"peso_kg": 70.0})
        assert_created(response1)
        
        # Añadir segundo peso del mismo día (debe reemplazar al anterior)
        response2 = client.post('/api/weight', json={"peso_kg": 75.0})
        assert_created(response2)
        
        # Verificar que solo hay un registro (el último)
        stats = client.get('/api/stats').get_json()
        assert stats["num_pesajes"] == 1
        assert stats["peso_max"] == 75.0
        assert stats["peso_min"] == 75.0
        
        # Verificar que el IMC usa el último peso
        imc = client.get('/api/imc').get_json()
        # IMC con 75kg y 1.75m = 75 / (1.75^2) = 24.5
        assert imc["imc"] == 24.5
    
    def test_add_weight_without_user(self, client):
        """Test de añadir peso sin usuario configurado"""
        response = client.post('/api/weight', json={"peso_kg": 70.0})
        assert_bad_request(response)
        assert "error" in response.get_json()


class TestIMCAPIBlackBox:
    """Tests de caja negra para la API de IMC"""
    
    def test_get_imc_without_user(self, client):
        """Test de obtener IMC sin usuario"""
        response = client.get('/api/imc')
        assert_not_found(response)
    
    def test_get_imc_without_weights(self, client):
        """Test de obtener IMC sin registros de peso"""
        client.post('/api/user', json={
            "nombre": "Luis",
            "apellidos": "Martínez",
            "fecha_nacimiento": "1985-12-05",
            "talla_m": 1.80
        })
        
        response = client.get('/api/imc')
        assert_success(response)
        data = response.get_json()
        assert data["imc"] == 0
        assert data["description"] == "Sin registros de peso"
    
    def test_get_imc_correct_calculation(self, client):
        """Test de cálculo correcto de IMC"""
        client.post('/api/user', json={
            "nombre": "Pedro",
            "apellidos": "González",
            "fecha_nacimiento": "1990-06-15",
            "talla_m": 1.70
        })
        
        # Peso 70 kg, altura 1.70 m -> IMC = 70 / (1.70^2) = 24.22
        client.post('/api/weight', json={"peso_kg": 70.0})
        
        response = client.get('/api/imc')
        assert_success(response)
        data = response.get_json()
        assert math.isclose(data["imc"], 24.22, abs_tol=0.1)
        assert data["description"] == "Peso normal"


class TestStatsAPIBlackBox:
    """Tests de caja negra para la API de estadísticas"""
    
    def test_stats_empty(self, client):
        """Test de estadísticas sin registros"""
        client.post('/api/user', json={
            "nombre": "Test",
            "apellidos": "User",
            "fecha_nacimiento": "1990-01-01",
            "talla_m": 1.75
        })
        
        response = client.get('/api/stats')
        assert_success(response)
        data = response.get_json()
        assert data["num_pesajes"] == 0
        assert data["peso_max"] == 0
        assert data["peso_min"] == 0
    
    def test_stats_single_weight(self, client):
        """Test de estadísticas con un solo peso"""
        client.post('/api/user', json={
            "nombre": "Test",
            "apellidos": "User",
            "fecha_nacimiento": "1990-01-01",
            "talla_m": 1.75
        })
        
        client.post('/api/weight', json={"peso_kg": 75.0})
        
        response = client.get('/api/stats')
        data = response.get_json()
        assert data["num_pesajes"] == 1
        assert data["peso_max"] == 75.0
        assert data["peso_min"] == 75.0
    
    def test_stats_multiple_weights(self, client):
        """Test de estadísticas con múltiples pesos en días diferentes"""
        from datetime import datetime, timedelta
        from app.storage import WeightEntryData
        from app.config import USER_ID
        
        client.post('/api/user', json={
            "nombre": "Test",
            "apellidos": "User",
            "fecha_nacimiento": "1990-01-01",
            "talla_m": 1.75
        })
        
        # Añadir pesos en días diferentes usando el storage directamente
        with client.application.app_context():
            storage = client.application.storage
            base_date = datetime.now()
            weights_data = [
                (70.0, base_date - timedelta(days=4)),
                (80.0, base_date - timedelta(days=3)),
                (75.0, base_date - timedelta(days=2)),
                (77.5, base_date - timedelta(days=1)),
                (72.0, base_date)
            ]
            for weight_kg, weight_date in weights_data:
                entry = WeightEntryData(
                    entry_id=0,
                    user_id=USER_ID,
                    weight_kg=weight_kg,
                    recorded_date=weight_date
                )
                storage.add_weight_entry(entry)
        
        response = client.get('/api/stats')
        data = response.get_json()
        assert data["num_pesajes"] == 5
        assert data["peso_max"] == 80.0
        assert data["peso_min"] == 70.0

