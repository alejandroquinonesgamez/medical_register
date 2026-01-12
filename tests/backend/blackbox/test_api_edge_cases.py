"""
Tests adicionales de casos edge para mejorar coverage
Cubre casos específicos que pueden no estar cubiertos en otros tests
"""
import pytest
import json
from datetime import datetime, timedelta
from tests.backend.conftest import assert_success, assert_created, assert_bad_request, assert_not_found
from app.storage import WeightEntryData
from app.config import USER_ID


class TestAPIWeightVariationEdgeCases:
    """Tests adicionales para casos edge de variación de peso"""
    
    def test_weight_variation_exact_limit(self, client, sample_user):
        """Test que acepta variación exactamente en el límite permitido"""
        from datetime import timedelta
        
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
        
        # Intentar añadir un peso con variación exactamente en el límite (2 días x 5kg/día = 10kg)
        data = {'peso_kg': 80.0}  # Exactamente 10kg de diferencia
        response = client.post('/api/weight', data=json.dumps(data), content_type='application/json')
        assert_created(response)
    
    def test_weight_variation_same_day_no_validation(self, client, sample_user):
        """Test que no valida variación si es el mismo día"""
        # Añadir un peso hoy
        with client.application.app_context():
            storage = client.application.storage
            today = datetime.now()
            old_weight = WeightEntryData(
                entry_id=0,
                user_id=USER_ID,
                weight_kg=70.0,
                recorded_date=today
            )
            storage.add_weight_entry(old_weight)
        
        # Intentar añadir un peso muy diferente el mismo día (debe reemplazar, no validar variación)
        data = {'peso_kg': 100.0}  # 30kg de diferencia, pero mismo día
        response = client.post('/api/weight', data=json.dumps(data), content_type='application/json')
        assert_created(response)
    
    def test_weight_variation_one_day(self, client, sample_user):
        """Test variación de peso con 1 día de diferencia"""
        from datetime import timedelta
        
        # Añadir un peso hace 1 día
        with client.application.app_context():
            storage = client.application.storage
            one_day_ago = datetime.now() - timedelta(days=1)
            old_weight = WeightEntryData(
                entry_id=0,
                user_id=USER_ID,
                weight_kg=70.0,
                recorded_date=one_day_ago
            )
            storage.add_weight_entry(old_weight)
        
        # Intentar añadir un peso con variación permitida (1 día x 5kg/día = 5kg)
        data = {'peso_kg': 75.0}  # Exactamente 5kg de diferencia
        response = client.post('/api/weight', data=json.dumps(data), content_type='application/json')
        assert_created(response)
    
    def test_weight_variation_many_days(self, client, sample_user):
        """Test variación de peso con muchos días de diferencia"""
        from datetime import timedelta
        
        # Añadir un peso hace 10 días
        with client.application.app_context():
            storage = client.application.storage
            ten_days_ago = datetime.now() - timedelta(days=10)
            old_weight = WeightEntryData(
                entry_id=0,
                user_id=USER_ID,
                weight_kg=70.0,
                recorded_date=ten_days_ago
            )
            storage.add_weight_entry(old_weight)
        
        # Intentar añadir un peso con variación permitida (10 días x 5kg/día = 50kg)
        data = {'peso_kg': 120.0}  # Exactamente 50kg de diferencia
        response = client.post('/api/weight', data=json.dumps(data), content_type='application/json')
        assert_created(response)


class TestAPIUserValidationEdgeCases:
    """Tests adicionales para casos edge de validación de usuario"""
    
    def test_create_user_name_min_length(self, client):
        """Test nombre con longitud mínima (1 carácter)"""
        data = {
            'nombre': 'A',  # 1 carácter
            'apellidos': 'User',
            'fecha_nacimiento': '1990-01-01',
            'talla_m': 1.75
        }
        response = client.post('/api/user', data=json.dumps(data), content_type='application/json')
        assert_success(response)
    
    def test_create_user_name_max_length(self, client):
        """Test nombre con longitud máxima (100 caracteres)"""
        long_name = 'A' * 100
        data = {
            'nombre': long_name,
            'apellidos': 'User',
            'fecha_nacimiento': '1990-01-01',
            'talla_m': 1.75
        }
        response = client.post('/api/user', data=json.dumps(data), content_type='application/json')
        assert_success(response)
    
    def test_create_user_name_too_long(self, client):
        """Test error cuando nombre excede longitud máxima"""
        long_name = 'A' * 101  # 101 caracteres
        data = {
            'nombre': long_name,
            'apellidos': 'User',
            'fecha_nacimiento': '1990-01-01',
            'talla_m': 1.75
        }
        response = client.post('/api/user', data=json.dumps(data), content_type='application/json')
        assert_bad_request(response)
    
    def test_create_user_name_empty(self, client):
        """Test error cuando nombre está vacío"""
        data = {
            'nombre': '',
            'apellidos': 'User',
            'fecha_nacimiento': '1990-01-01',
            'talla_m': 1.75
        }
        response = client.post('/api/user', data=json.dumps(data), content_type='application/json')
        assert_bad_request(response)
    
    def test_create_user_last_name_empty(self, client):
        """Test error cuando apellidos están vacíos"""
        data = {
            'nombre': 'Test',
            'apellidos': '',
            'fecha_nacimiento': '1990-01-01',
            'talla_m': 1.75
        }
        response = client.post('/api/user', data=json.dumps(data), content_type='application/json')
        assert_bad_request(response)
    
    def test_create_user_name_with_dangerous_chars(self, client):
        """Test que se sanitizan caracteres peligrosos en nombre"""
        data = {
            'nombre': 'Test<>User',  # Caracteres peligrosos
            'apellidos': 'Last',
            'fecha_nacimiento': '1990-01-01',
            'talla_m': 1.75
        }
        response = client.post('/api/user', data=json.dumps(data), content_type='application/json')
        # Debe aceptar pero sanitizar
        assert_success(response)
        # Verificar que se guardó sanitizado
        user_response = client.get('/api/user')
        user_data = user_response.get_json()
        assert '<' not in user_data['nombre']
        assert '>' not in user_data['nombre']
    
    def test_create_user_birth_date_today(self, client):
        """Test fecha de nacimiento igual a hoy (límite superior)"""
        today = datetime.now().strftime('%Y-%m-%d')
        data = {
            'nombre': 'Test',
            'apellidos': 'User',
            'fecha_nacimiento': today,
            'talla_m': 1.75
        }
        response = client.post('/api/user', data=json.dumps(data), content_type='application/json')
        assert_success(response)
    
    def test_create_user_birth_date_min(self, client):
        """Test fecha de nacimiento en el límite mínimo (1900-01-01)"""
        data = {
            'nombre': 'Test',
            'apellidos': 'User',
            'fecha_nacimiento': '1900-01-01',
            'talla_m': 1.75
        }
        response = client.post('/api/user', data=json.dumps(data), content_type='application/json')
        assert_success(response)


class TestAPIIMCEdgeCases:
    """Tests adicionales para casos edge de IMC"""
    
    def test_get_imc_no_weights_returns_zero(self, client, sample_user):
        """Test que IMC retorna 0 cuando no hay pesos"""
        response = client.get('/api/imc')
        assert_success(response)
        data = response.get_json()
        assert data['imc'] == 0
        assert 'Sin registros' in data['description'] or 'no_weight_records' in data.get('description', '')
    
    def test_get_imc_with_zero_height(self, client):
        """Test IMC con altura cero (caso edge)"""
        from app.storage import UserData, WeightEntryData
        from app.config import USER_ID
        
        # Crear usuario con altura cero (aunque no debería pasar en producción)
        with client.application.app_context():
            storage = client.application.storage
            invalid_user = UserData(
                user_id=USER_ID,
                first_name='Test',
                last_name='User',
                birth_date=datetime(1990, 1, 1).date(),
                height_m=0  # Altura cero
            )
            storage.save_user(invalid_user)
            
            # Añadir un peso
            weight = WeightEntryData(
                entry_id=0,
                user_id=USER_ID,
                weight_kg=70.0,
                recorded_date=datetime.now()
            )
            storage.add_weight_entry(weight)
        
        # El cálculo de IMC debería retornar 0 cuando altura es 0
        response = client.get('/api/imc')
        # Puede retornar error o 0, dependiendo de validaciones
        # Verificamos que no crashea
        assert response.status_code in [200, 400]


class TestAPIStatsEdgeCases:
    """Tests adicionales para casos edge de estadísticas"""
    
    def test_stats_no_user(self, client):
        """Test estadísticas sin usuario (debe funcionar)"""
        response = client.get('/api/stats')
        assert_success(response)
        data = response.get_json()
        assert data['num_pesajes'] == 0
        assert data['peso_max'] == 0
        assert data['peso_min'] == 0
    
    def test_stats_single_entry(self, client, sample_user):
        """Test estadísticas con una sola entrada"""
        client.post('/api/weight', json={'peso_kg': 75.0})
        
        response = client.get('/api/stats')
        assert_success(response)
        data = response.get_json()
        assert data['num_pesajes'] == 1
        assert data['peso_max'] == 75.0
        assert data['peso_min'] == 75.0
