"""
Tests de CAJA NEGRA para la API
Prueban los endpoints sin conocer la implementación interna
"""
import pytest
import json
from datetime import datetime
from tests.conftest import assert_success, assert_created, assert_bad_request


class TestAPIUser:
    """Tests de caja negra para endpoints de usuario"""
    
    
    def test_create_user_success(self, client):
        """Test POST /api/user creación exitosa"""
        data = {
            'nombre': 'Juan',
            'apellidos': 'Pérez García',
            'fecha_nacimiento': '1990-05-15',
            'talla_m': 1.75
        }
        response = client.post(
            '/api/user',
            data=json.dumps(data),
            content_type='application/json'
        )
        assert_success(response)
        data_resp = json.loads(response.data)
        assert data_resp['message'] == 'Usuario guardado'
    
    def test_get_user_after_creation(self, client):
        """Test GET /api/user después de crear usuario"""
        # Crear usuario primero
        data = {
            'nombre': 'Juan',
            'apellidos': 'Pérez García',
            'fecha_nacimiento': '1990-05-15',
            'talla_m': 1.75
        }
        client.post('/api/user', data=json.dumps(data), content_type='application/json')
        
        # Obtener usuario
        response = client.get('/api/user')
        assert_success(response)
        data_resp = json.loads(response.data)
        assert data_resp['nombre'] == 'Juan'
        assert data_resp['apellidos'] == 'Pérez García'
        assert data_resp['talla_m'] == 1.75
    


class TestAPIWeight:
    """Tests de caja negra para endpoints de peso"""
    
    
    def test_add_weight_success(self, client, sample_user):
        """Test POST /api/weight registro exitoso"""
        data = {'peso_kg': 70.5}
        response = client.post(
            '/api/weight',
            data=json.dumps(data),
            content_type='application/json'
        )
        assert_created(response)
        data_resp = json.loads(response.data)
        assert data_resp['message'] == 'Peso registrado'
    
    def test_add_weight_multiple(self, client, sample_user):
        """Test múltiples registros de peso"""
        pesos = [70.0, 72.5, 75.0]
        for peso in pesos:
            data = {'peso_kg': peso}
            response = client.post(
                '/api/weight',
                data=json.dumps(data),
                content_type='application/json'
            )
            assert_created(response)


class TestAPIErrorHandling:
    """Tests de caja negra para manejo de errores en la API"""
    
    def test_create_user_invalid_height_type(self, client):
        """Test error al convertir talla_m a float"""
        data = {
            'nombre': 'Test',
            'apellidos': 'User',
            'fecha_nacimiento': '1990-01-01',
            'talla_m': 'not_a_number'
        }
        response = client.post('/api/user', data=json.dumps(data), content_type='application/json')
        assert_bad_request(response)
        error_msg = response.get_json()['error'].lower()
        assert 'altura' in error_msg or 'talla' in error_msg or 'inválid' in error_msg
    
    def test_create_user_missing_talla(self, client):
        """Test error cuando falta talla_m"""
        data = {
            'nombre': 'Test',
            'apellidos': 'User',
            'fecha_nacimiento': '1990-01-01'
        }
        response = client.post('/api/user', data=json.dumps(data), content_type='application/json')
        assert_bad_request(response)
    
    def test_create_user_invalid_birth_date_format(self, client):
        """Test error al parsear fecha de nacimiento"""
        data = {
            'nombre': 'Test',
            'apellidos': 'User',
            'fecha_nacimiento': 'invalid-date',
            'talla_m': 1.75
        }
        response = client.post('/api/user', data=json.dumps(data), content_type='application/json')
        assert_bad_request(response)
        error_msg = response.get_json()['error'].lower()
        assert 'fecha' in error_msg or 'inválid' in error_msg
    
    def test_create_user_missing_birth_date(self, client):
        """Test error cuando falta fecha_nacimiento"""
        data = {
            'nombre': 'Test',
            'apellidos': 'User',
            'talla_m': 1.75
        }
        response = client.post('/api/user', data=json.dumps(data), content_type='application/json')
        assert_bad_request(response)
    
    def test_add_weight_invalid_weight_type(self, client, sample_user):
        """Test error al convertir peso_kg a float"""
        data = {'peso_kg': 'not_a_number'}
        response = client.post('/api/weight', data=json.dumps(data), content_type='application/json')
        assert_bad_request(response)
        error_msg = response.get_json()['error'].lower()
        assert 'peso' in error_msg or 'inválid' in error_msg
    
    def test_add_weight_missing_weight(self, client, sample_user):
        """Test error cuando falta peso_kg"""
        data = {}
        response = client.post('/api/weight', data=json.dumps(data), content_type='application/json')
        assert_bad_request(response)
    
    def test_weight_variation_exceeded(self, client, sample_user):
        """Test validación de variación de peso excedida"""
        from datetime import timedelta
        from app.storage import WeightEntryData
        from app.config import USER_ID
        
        # Añadir un peso hace 2 días
        with client.application.app_context():
            storage = client.application.storage
            two_days_ago = datetime.now() - timedelta(days=2)
            old_weight = WeightEntryData(
                entry_id=0,
                user_id=USER_ID,
                weight_kg=70.0,
                recorded_date=two_days_ago
            )
            storage.add_weight_entry(old_weight)
        
        # Intentar añadir un peso con variación excesiva (más de 10kg en 2 días)
        data = {'peso_kg': 85.0}  # 15kg de diferencia, máximo permitido: 10kg (2 días x 5kg/día)
        response = client.post('/api/weight', data=json.dumps(data), content_type='application/json')
        assert_bad_request(response)
        error_msg = response.get_json()['error'].lower()
        assert 'variation' in error_msg or 'variación' in error_msg


class TestAPIIMC:
    """Tests de caja negra para endpoint de IMC"""
    
    
    def test_get_imc_with_weights(self, client, sample_user, sample_weights):
        """Test GET /api/imc con registros de peso"""
        response = client.get('/api/imc')
        assert_success(response)
        data = json.loads(response.data)
        assert 'imc' in data
        assert 'description' in data
        assert data['imc'] > 0
        # IMC = 75 / (1.75^2) = 24.5 (último peso registrado)
        assert data['imc'] == 24.5
        assert data['description'] == 'Peso normal'


class TestAPIIndex:
    """Tests de caja negra para endpoint raíz"""
    
    def test_index_route(self, client):
        """Test GET / devuelve HTML"""
        response = client.get('/')
        assert_success(response)
        assert 'text/html' in response.content_type

