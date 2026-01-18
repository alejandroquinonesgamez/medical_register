"""
Tests de CAJA NEGRA para la API
Prueban los endpoints sin conocer la implementación interna
"""
import pytest
import json
from datetime import datetime
from tests.backend.conftest import assert_success, assert_created, assert_bad_request, assert_not_found, assert_unauthorized, assert_forbidden



class TestAPIWeight:
    """Tests de caja negra para endpoints de peso"""
    
    
    def test_add_weight_success(self, client, sample_user, auth_session):
        """Test POST /api/weight registro exitoso"""
        data = {'peso_kg': 70.5}
        response = client.post(
            '/api/weight',
            data=json.dumps(data),
            headers={"X-CSRF-Token": auth_session["csrf_token"]},
            content_type='application/json'
        )
        assert_created(response)
        data_resp = json.loads(response.data)
        assert data_resp['message'] == 'Peso Registrado'
    
    def test_add_weight_multiple(self, client, sample_user, auth_session):
        """Test múltiples registros de peso"""
        pesos = [70.0, 72.5, 75.0]
        for peso in pesos:
            data = {'peso_kg': peso}
            response = client.post(
                '/api/weight',
                data=json.dumps(data),
                headers={"X-CSRF-Token": auth_session["csrf_token"]},
                content_type='application/json'
            )
            assert_created(response)


class TestAPIErrorHandling:
    """Tests de caja negra para manejo de errores en la API"""
    
    def test_create_user_invalid_height_type(self, client, auth_session):
        """Test error al convertir talla_m a float"""
        data = {
            'nombre': 'Test',
            'apellidos': 'User',
            'fecha_nacimiento': '1990-01-01',
            'talla_m': 'not_a_number'
        }
        response = client.post('/api/user', data=json.dumps(data), headers={"X-CSRF-Token": auth_session["csrf_token"]}, content_type='application/json')
        assert_bad_request(response)
        error_msg = response.get_json()['error'].lower()
        assert 'altura' in error_msg or 'talla' in error_msg or 'inválid' in error_msg
    
    def test_create_user_missing_talla(self, client, auth_session):
        """Test error cuando falta talla_m"""
        data = {
            'nombre': 'Test',
            'apellidos': 'User',
            'fecha_nacimiento': '1990-01-01'
        }
        response = client.post('/api/user', data=json.dumps(data), headers={"X-CSRF-Token": auth_session["csrf_token"]}, content_type='application/json')
        assert_bad_request(response)
    
    def test_create_user_invalid_birth_date_format(self, client, auth_session):
        """Test error al parsear fecha de nacimiento"""
        data = {
            'nombre': 'Test',
            'apellidos': 'User',
            'fecha_nacimiento': 'invalid-date',
            'talla_m': 1.75
        }
        response = client.post('/api/user', data=json.dumps(data), headers={"X-CSRF-Token": auth_session["csrf_token"]}, content_type='application/json')
        assert_bad_request(response)
        error_msg = response.get_json()['error'].lower()
        assert 'fecha' in error_msg or 'inválid' in error_msg
    
    def test_create_user_missing_birth_date(self, client, auth_session):
        """Test error cuando falta fecha_nacimiento"""
        data = {
            'nombre': 'Test',
            'apellidos': 'User',
            'talla_m': 1.75
        }
        response = client.post('/api/user', data=json.dumps(data), headers={"X-CSRF-Token": auth_session["csrf_token"]}, content_type='application/json')
        assert_bad_request(response)
    
    def test_add_weight_invalid_weight_type(self, client, sample_user, auth_session):
        """Test error al convertir peso_kg a float"""
        data = {'peso_kg': 'not_a_number'}
        response = client.post('/api/weight', data=json.dumps(data), headers={"X-CSRF-Token": auth_session["csrf_token"]}, content_type='application/json')
        assert_bad_request(response)
        error_msg = response.get_json()['error'].lower()
        assert 'peso' in error_msg or 'inválid' in error_msg
    
    def test_add_weight_missing_weight(self, client, sample_user, auth_session):
        """Test error cuando falta peso_kg"""
        data = {}
        response = client.post('/api/weight', data=json.dumps(data), headers={"X-CSRF-Token": auth_session["csrf_token"]}, content_type='application/json')
        assert_bad_request(response)
    
    def test_weight_variation_exceeded(self, client, sample_user, auth_session):
        """Test validación de variación de peso excedida"""
        from datetime import timedelta
        from app.storage import WeightEntryData
        
        # Añadir un peso hace 2 días
        with client.application.app_context():
            storage = client.application.storage
            two_days_ago = datetime.now() - timedelta(days=2)
            old_weight = WeightEntryData(
                entry_id=0,
                user_id=auth_session["user_id"],
                weight_kg=70.0,
                recorded_date=two_days_ago
            )
            storage.add_weight_entry(old_weight)
        
        # Intentar añadir un peso con variación excesiva (más de 10kg en 2 días)
        data = {'peso_kg': 85.0}  # 15kg de diferencia, máximo permitido: 10kg (2 días x 5kg/día)
        response = client.post('/api/weight', data=json.dumps(data), headers={"X-CSRF-Token": auth_session["csrf_token"]}, content_type='application/json')
        assert_bad_request(response)
        error_msg = response.get_json()['error'].lower()
        assert 'variation' in error_msg or 'variación' in error_msg


class TestAPIIMC:
    """Tests de caja negra para endpoint de IMC"""
    
    
    def test_get_imc_with_weights(self, client, sample_user, sample_weights, auth_session):
        """Test GET /api/imc con registros de peso"""
        response = client.get('/api/imc')
        assert_success(response)
        data = json.loads(response.data)
        assert 'imc' in data
        assert 'description' in data
        assert data['imc'] > 0
        # IMC = 75 / (1.75^2) = 24.5 (último peso registrado)
        assert data['imc'] == 24.5
        assert 'Peso Normal' in data['description']
        # Verificar que la descripción no está vacía (se devuelve algo)
        assert len(data['description']) > len('Peso Normal')
    
    def test_get_imc_with_invalid_weight(self, client, sample_user, auth_session):
        """Test GET /api/imc con peso fuera de rango (validación defensiva)"""
        from app.storage import WeightEntryData
        from app.config import VALIDATION_LIMITS
        
        # Añadir un peso fuera de rango directamente al storage
        with client.application.app_context():
            storage = client.application.storage
            invalid_weight = WeightEntryData(
                entry_id=0,
                user_id=auth_session["user_id"],
                weight_kg=VALIDATION_LIMITS["weight_max"] + 100,  # Fuera de rango
                recorded_date=datetime.now()
            )
            storage.add_weight_entry(invalid_weight)
        
        response = client.get('/api/imc')
        assert_bad_request(response)
        data = json.loads(response.data)
        assert 'error' in data
        error_msg = data['error'].lower()
        assert 'peso' in error_msg or 'weight' in error_msg or 'rango' in error_msg
    
    def test_get_imc_with_invalid_height(self, client, auth_session):
        """Test GET /api/imc con talla fuera de rango (validación defensiva)"""
        from app.storage import UserData, WeightEntryData
        from app.config import VALIDATION_LIMITS
        
        # Crear usuario con talla fuera de rango
        with client.application.app_context():
            storage = client.application.storage
            invalid_user = UserData(
                user_id=auth_session["user_id"],
                first_name='Test',
                last_name='User',
                birth_date=datetime(1990, 1, 1).date(),
                height_m=VALIDATION_LIMITS["height_max"] + 1  # Fuera de rango
            )
            storage.save_user(invalid_user)
            
            # Añadir un peso válido
            valid_weight = WeightEntryData(
                entry_id=0,
                user_id=auth_session["user_id"],
                weight_kg=70.0,
                recorded_date=datetime.now()
            )
            storage.add_weight_entry(valid_weight)
        
        response = client.get('/api/imc')
        assert_bad_request(response)
        data = json.loads(response.data)
        assert 'error' in data
        error_msg = data['error'].lower()
        assert 'talla' in error_msg or 'altura' in error_msg or 'height' in error_msg or 'rango' in error_msg


class TestAPIWeights:
    """Tests de caja negra para endpoint GET /api/weights"""
    
    def test_get_weights_success(self, client, sample_user, sample_weights, auth_session):
        """Test GET /api/weights retorna todos los pesos"""
        response = client.get('/api/weights')
        assert_success(response)
        data = json.loads(response.data)
        assert 'weights' in data
        assert isinstance(data['weights'], list)
        assert len(data['weights']) == 3  # sample_weights tiene 3 pesos
    
    def test_get_weights_empty(self, client, sample_user, auth_session):
        """Test GET /api/weights retorna lista vacía cuando no hay pesos"""
        response = client.get('/api/weights')
        assert_success(response)
        data = json.loads(response.data)
        assert 'weights' in data
        assert isinstance(data['weights'], list)
        assert len(data['weights']) == 0
    
    def test_get_weights_no_user(self, client):
        """Test GET /api/weights retorna 401 cuando no hay sesión"""
        response = client.get('/api/weights')
        assert_unauthorized(response)
        data = json.loads(response.data)
        assert 'error' in data
    
    def test_get_weights_format(self, client, sample_user, sample_weights, auth_session):
        """Test que los pesos tienen el formato correcto"""
        response = client.get('/api/weights')
        assert_success(response)
        data = json.loads(response.data)
        weights = data['weights']
        
        # Verificar que hay pesos
        assert len(weights) > 0
        
        # Verificar formato de cada peso
        for weight in weights:
            assert 'id' in weight
            assert 'peso_kg' in weight
            assert 'fecha_registro' in weight
            assert isinstance(weight['id'], int)
            assert isinstance(weight['peso_kg'], (int, float))
            assert isinstance(weight['fecha_registro'], str)
    
    def test_get_weights_ordered(self, client, sample_user, auth_session):
        """Test que los pesos están ordenados por fecha descendente"""
        from datetime import datetime, timedelta
        from app.storage import WeightEntryData
        
        # Añadir pesos en orden no cronológico
        with client.application.app_context():
            storage = client.application.storage
            base_date = datetime.now()
            
            # Añadir peso más antiguo
            old_weight = WeightEntryData(
                entry_id=0,
                user_id=auth_session["user_id"],
                weight_kg=70.0,
                recorded_date=base_date - timedelta(days=10)
            )
            storage.add_weight_entry(old_weight)
            
            # Añadir peso más reciente
            new_weight = WeightEntryData(
                entry_id=0,
                user_id=auth_session["user_id"],
                weight_kg=75.0,
                recorded_date=base_date
            )
            storage.add_weight_entry(new_weight)
            
            # Añadir peso intermedio
            mid_weight = WeightEntryData(
                entry_id=0,
                user_id=auth_session["user_id"],
                weight_kg=72.5,
                recorded_date=base_date - timedelta(days=5)
            )
            storage.add_weight_entry(mid_weight)
        
        # Verificar que están ordenados por fecha descendente
        response = client.get('/api/weights')
        assert_success(response)
        data = json.loads(response.data)
        weights = data['weights']
        
        assert len(weights) == 3
        
        # Verificar orden descendente (más reciente primero)
        dates = [datetime.fromisoformat(w['fecha_registro']) for w in weights]
        for i in range(len(dates) - 1):
            assert dates[i] >= dates[i + 1], "Los pesos deben estar ordenados por fecha descendente"


class TestAPIConfig:
    """Tests de caja negra para endpoint GET /api/config"""
    
    def test_get_config_success(self, client):
        """Test GET /api/config retorna configuración de validación"""
        response = client.get('/api/config')
        assert_success(response)
        data = json.loads(response.data)
        assert 'validation_limits' in data
        
        limits = data['validation_limits']
        assert 'height_min' in limits
        assert 'height_max' in limits
        assert 'weight_min' in limits
        assert 'weight_max' in limits
        assert 'birth_date_min' in limits
        assert 'weight_variation_per_day' in limits
        
        # Verificar que los valores son correctos
        assert limits['height_min'] == 0.4
        assert limits['height_max'] == 2.72
        assert limits['weight_min'] == 2
        assert limits['weight_max'] == 650
        assert limits['weight_variation_per_day'] == 5
    
    def test_get_config_format(self, client):
        """Test que la configuración tiene el formato correcto"""
        response = client.get('/api/config')
        assert_success(response)
        data = json.loads(response.data)
        
        limits = data['validation_limits']
        assert isinstance(limits['height_min'], (int, float))
        assert isinstance(limits['height_max'], (int, float))
        assert isinstance(limits['weight_min'], (int, float))
        assert isinstance(limits['weight_max'], (int, float))
        assert isinstance(limits['birth_date_min'], str)  # ISO format string
        assert isinstance(limits['weight_variation_per_day'], (int, float))


class TestAPIIndex:
    """Tests de caja negra para endpoint raíz"""
    
    def test_index_route(self, client):
        """Test GET / devuelve HTML"""
        response = client.get('/')
        assert_success(response)
        assert 'text/html' in response.content_type

