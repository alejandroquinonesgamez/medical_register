"""
Tests adicionales de CAJA NEGRA para endpoints que faltaban
Estos tests mejoran el coverage de la aplicación
"""
import pytest
import json
import math
from datetime import datetime, timedelta
from tests.backend.conftest import assert_success, assert_created, assert_bad_request, assert_not_found, assert_unauthorized
from app.storage import WeightEntryData


class TestAPIWeightsRecent:
    """Tests de caja negra para endpoint GET /api/weights/recent"""
    
    def test_get_recent_weights_success(self, client, sample_user, sample_weights, auth_session):
        """Test GET /api/weights/recent retorna los últimos 5 pesos"""
        response = client.get('/api/weights/recent')
        assert_success(response)
        data = json.loads(response.data)
        assert 'weights' in data
        assert isinstance(data['weights'], list)
        # sample_weights tiene 3 pesos, debe retornar 3
        assert len(data['weights']) == 3
    
    def test_get_recent_weights_empty(self, client, sample_user, auth_session):
        """Test GET /api/weights/recent retorna lista vacía cuando no hay pesos"""
        response = client.get('/api/weights/recent')
        assert_success(response)
        data = json.loads(response.data)
        assert 'weights' in data
        assert isinstance(data['weights'], list)
        assert len(data['weights']) == 0
    
    def test_get_recent_weights_limit_five(self, client, sample_user, auth_session):
        """Test GET /api/weights/recent limita a 5 pesos"""
        from app.storage import WeightEntryData
        
        # Añadir más de 5 pesos
        with client.application.app_context():
            storage = client.application.storage
            base_date = datetime.now()
            for i in range(7):
                weight = WeightEntryData(
                    entry_id=0,
                    user_id=sample_user.user_id,
                    weight_kg=70.0 + i,
                    recorded_date=base_date - timedelta(days=i)
                )
                storage.add_weight_entry(weight)
        
        response = client.get('/api/weights/recent')
        assert_success(response)
        data = json.loads(response.data)
        assert len(data['weights']) == 5  # Debe limitar a 5
    
    def test_get_recent_weights_format(self, client, sample_user, sample_weights, auth_session):
        """Test que los pesos recientes tienen el formato correcto"""
        response = client.get('/api/weights/recent')
        assert_success(response)
        data = json.loads(response.data)
        weights = data['weights']
        
        if len(weights) > 0:
            for weight in weights:
                assert 'id' in weight
                assert 'peso_kg' in weight
                assert 'fecha_registro' in weight
                assert isinstance(weight['id'], int)
                assert isinstance(weight['peso_kg'], (int, float))
                assert isinstance(weight['fecha_registro'], str)


class TestAPIMessages:
    """Tests de caja negra para endpoint GET /api/messages"""
    
    def test_get_messages_success(self, client):
        """Test GET /api/messages retorna todos los mensajes"""
        response = client.get('/api/messages')
        assert_success(response)
        data = json.loads(response.data)
        assert isinstance(data, dict)
        assert len(data) > 0
    
    def test_get_messages_structure(self, client):
        """Test que los mensajes tienen estructura válida"""
        response = client.get('/api/messages')
        assert_success(response)
        data = json.loads(response.data)
        # Verificar que es un diccionario con claves de string
        for key, value in data.items():
            assert isinstance(key, str)
            assert isinstance(value, (str, dict)), "Mensajes pueden anidar descripciones"


class TestAPIUserEdgeCases:
    """Tests adicionales de casos edge para /api/user POST"""
    
    def test_create_user_height_nan(self, client, auth_session):
        """Test error cuando altura es NaN"""
        import math
        data = {
            'nombre': 'Test',
            'apellidos': 'User',
            'fecha_nacimiento': '1990-01-01',
            'talla_m': float('nan')
        }
        response = client.post('/api/user', data=json.dumps(data), headers={"X-CSRF-Token": auth_session["csrf_token"]}, content_type='application/json')
        assert_bad_request(response)
    
    def test_create_user_height_infinity(self, client, auth_session):
        """Test error cuando altura es Infinity"""
        import math
        data = {
            'nombre': 'Test',
            'apellidos': 'User',
            'fecha_nacimiento': '1990-01-01',
            'talla_m': float('inf')
        }
        response = client.post('/api/user', data=json.dumps(data), headers={"X-CSRF-Token": auth_session["csrf_token"]}, content_type='application/json')
        assert_bad_request(response)
    
    def test_create_user_height_negative_infinity(self, client, auth_session):
        """Test error cuando altura es -Infinity"""
        import math
        data = {
            'nombre': 'Test',
            'apellidos': 'User',
            'fecha_nacimiento': '1990-01-01',
            'talla_m': float('-inf')
        }
        response = client.post('/api/user', data=json.dumps(data), headers={"X-CSRF-Token": auth_session["csrf_token"]}, content_type='application/json')
        assert_bad_request(response)
    
    def test_create_user_height_list_type(self, client, auth_session):
        """Test error cuando altura es una lista (tipo no convertible)"""
        data = {
            'nombre': 'Test',
            'apellidos': 'User',
            'fecha_nacimiento': '1990-01-01',
            'talla_m': [1.75]  # Lista en lugar de número
        }
        response = client.post('/api/user', data=json.dumps(data), headers={"X-CSRF-Token": auth_session["csrf_token"]}, content_type='application/json')
        assert_bad_request(response)
    
    def test_create_user_height_dict_type(self, client, auth_session):
        """Test error cuando altura es un diccionario (tipo no convertible)"""
        data = {
            'nombre': 'Test',
            'apellidos': 'User',
            'fecha_nacimiento': '1990-01-01',
            'talla_m': {'value': 1.75}  # Diccionario en lugar de número
        }
        response = client.post('/api/user', data=json.dumps(data), headers={"X-CSRF-Token": auth_session["csrf_token"]}, content_type='application/json')
        assert_bad_request(response)
    
    def test_create_user_birth_date_before_min(self, client, auth_session):
        """Test error cuando fecha de nacimiento es anterior al mínimo"""
        data = {
            'nombre': 'Test',
            'apellidos': 'User',
            'fecha_nacimiento': '1899-12-31',  # Antes de 1900-01-01
            'talla_m': 1.75
        }
        response = client.post('/api/user', data=json.dumps(data), headers={"X-CSRF-Token": auth_session["csrf_token"]}, content_type='application/json')
        assert_bad_request(response)
    
    def test_create_user_birth_date_future(self, client, auth_session):
        """Test error cuando fecha de nacimiento es futura"""
        from datetime import datetime, timedelta
        future_date = (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')
        data = {
            'nombre': 'Test',
            'apellidos': 'User',
            'fecha_nacimiento': future_date,
            'talla_m': 1.75
        }
        response = client.post('/api/user', data=json.dumps(data), headers={"X-CSRF-Token": auth_session["csrf_token"]}, content_type='application/json')
        assert_bad_request(response)
    
    def test_create_user_height_min_boundary(self, client, auth_session):
        """Test altura en el límite mínimo (0.4)"""
        data = {
            'nombre': 'Test',
            'apellidos': 'User',
            'fecha_nacimiento': '1990-01-01',
            'talla_m': 0.4
        }
        response = client.post('/api/user', data=json.dumps(data), headers={"X-CSRF-Token": auth_session["csrf_token"]}, content_type='application/json')
        assert_success(response)
    
    def test_create_user_height_max_boundary(self, client, auth_session):
        """Test altura en el límite máximo (2.72)"""
        data = {
            'nombre': 'Test',
            'apellidos': 'User',
            'fecha_nacimiento': '1990-01-01',
            'talla_m': 2.72
        }
        response = client.post('/api/user', data=json.dumps(data), headers={"X-CSRF-Token": auth_session["csrf_token"]}, content_type='application/json')
        assert_success(response)
    
    def test_create_user_height_below_min(self, client, auth_session):
        """Test error cuando altura está por debajo del mínimo"""
        data = {
            'nombre': 'Test',
            'apellidos': 'User',
            'fecha_nacimiento': '1990-01-01',
            'talla_m': 0.39  # Por debajo de 0.4
        }
        response = client.post('/api/user', data=json.dumps(data), headers={"X-CSRF-Token": auth_session["csrf_token"]}, content_type='application/json')
        assert_bad_request(response)
    
    def test_create_user_height_above_max(self, client, auth_session):
        """Test error cuando altura está por encima del máximo"""
        data = {
            'nombre': 'Test',
            'apellidos': 'User',
            'fecha_nacimiento': '1990-01-01',
            'talla_m': 2.73  # Por encima de 2.72
        }
        response = client.post('/api/user', data=json.dumps(data), headers={"X-CSRF-Token": auth_session["csrf_token"]}, content_type='application/json')
        assert_bad_request(response)


class TestAPIWeightEdgeCases:
    """Tests adicionales de casos edge para /api/weight POST"""
    
    def test_add_weight_nan(self, client, sample_user, auth_session):
        """Test error cuando peso es NaN"""
        import math
        data = {'peso_kg': float('nan')}
        response = client.post('/api/weight', data=json.dumps(data), headers={"X-CSRF-Token": auth_session["csrf_token"]}, content_type='application/json')
        assert_bad_request(response)
    
    def test_add_weight_infinity(self, client, sample_user, auth_session):
        """Test error cuando peso es Infinity"""
        import math
        data = {'peso_kg': float('inf')}
        response = client.post('/api/weight', data=json.dumps(data), headers={"X-CSRF-Token": auth_session["csrf_token"]}, content_type='application/json')
        assert_bad_request(response)
    
    def test_add_weight_negative_infinity(self, client, sample_user, auth_session):
        """Test error cuando peso es -Infinity"""
        import math
        data = {'peso_kg': float('-inf')}
        response = client.post('/api/weight', data=json.dumps(data), headers={"X-CSRF-Token": auth_session["csrf_token"]}, content_type='application/json')
        assert_bad_request(response)
    
    def test_add_weight_list_type(self, client, sample_user, auth_session):
        """Test error cuando peso es una lista (tipo no convertible)"""
        data = {'peso_kg': [70.0]}  # Lista en lugar de número
        response = client.post('/api/weight', data=json.dumps(data), headers={"X-CSRF-Token": auth_session["csrf_token"]}, content_type='application/json')
        assert_bad_request(response)
    
    def test_add_weight_dict_type(self, client, sample_user, auth_session):
        """Test error cuando peso es un diccionario (tipo no convertible)"""
        data = {'peso_kg': {'value': 70.0}}  # Diccionario en lugar de número
        response = client.post('/api/weight', data=json.dumps(data), headers={"X-CSRF-Token": auth_session["csrf_token"]}, content_type='application/json')
        assert_bad_request(response)
    
    def test_add_weight_min_boundary(self, client, sample_user, auth_session):
        """Test peso en el límite mínimo (2)"""
        data = {'peso_kg': 2}
        response = client.post('/api/weight', data=json.dumps(data), headers={"X-CSRF-Token": auth_session["csrf_token"]}, content_type='application/json')
        assert_created(response)
    
    def test_add_weight_max_boundary(self, client, sample_user, auth_session):
        """Test peso en el límite máximo (650)"""
        data = {'peso_kg': 650}
        response = client.post('/api/weight', data=json.dumps(data), headers={"X-CSRF-Token": auth_session["csrf_token"]}, content_type='application/json')
        assert_created(response)
    
    def test_add_weight_below_min(self, client, sample_user, auth_session):
        """Test error cuando peso está por debajo del mínimo"""
        data = {'peso_kg': 1.9}  # Por debajo de 2
        response = client.post('/api/weight', data=json.dumps(data), headers={"X-CSRF-Token": auth_session["csrf_token"]}, content_type='application/json')
        assert_bad_request(response)
    
    def test_add_weight_above_max(self, client, sample_user, auth_session):
        """Test error cuando peso está por encima del máximo"""
        data = {'peso_kg': 651}  # Por encima de 650
        response = client.post('/api/weight', data=json.dumps(data), headers={"X-CSRF-Token": auth_session["csrf_token"]}, content_type='application/json')
        assert_bad_request(response)
    
    def test_add_weight_string_number(self, client, sample_user, auth_session):
        """Test que acepta peso como string numérico"""
        data = {'peso_kg': '70.5'}  # String numérico
        response = client.post('/api/weight', data=json.dumps(data), headers={"X-CSRF-Token": auth_session["csrf_token"]}, content_type='application/json')
        assert_created(response)
    
    def test_add_weight_integer(self, client, sample_user, auth_session):
        """Test que acepta peso como entero"""
        data = {'peso_kg': 70}  # Entero
        response = client.post('/api/weight', data=json.dumps(data), headers={"X-CSRF-Token": auth_session["csrf_token"]}, content_type='application/json')
        assert_created(response)
