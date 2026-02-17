"""
Tests de Caja Blanca (White Box Testing)
Tests de límites y equivalencia para validaciones de la API
"""
import pytest
import json
from datetime import datetime, date, timedelta
from app.config import VALIDATION_LIMITS
from tests.backend.conftest import assert_success, assert_created, assert_bad_request, assert_not_found, client, sample_user, auth_headers


class TestBoundaryValuesAPI:
    """Tests de valores límite para validaciones de la API"""
    
    def test_talla_minimo_valido(self, client, auth_session):
        """Límite inferior válido"""
        data = {
            'nombre': 'Test',
            'apellidos': 'User',
            'fecha_nacimiento': '1990-01-01',
            'talla_m': VALIDATION_LIMITS['height_min']
        }
        response = client.post('/api/user', data=json.dumps(data), headers=auth_headers(auth_session["access_token"]), content_type='application/json')
        assert_success(response)
    
    def test_talla_maximo_valido(self, client, auth_session):
        """Límite superior válido"""
        data = {
            'nombre': 'Test',
            'apellidos': 'User',
            'fecha_nacimiento': '1990-01-01',
            'talla_m': VALIDATION_LIMITS['height_max']
        }
        response = client.post('/api/user', data=json.dumps(data), headers=auth_headers(auth_session["access_token"]), content_type='application/json')
        assert_success(response)
    
    def test_talla_justo_bajo_minimo(self, client, auth_session):
        """Límite inferior inválido (justo debajo del mínimo)"""
        data = {
            'nombre': 'Test',
            'apellidos': 'User',
            'fecha_nacimiento': '1990-01-01',
            'talla_m': VALIDATION_LIMITS['height_min'] - 0.01
        }
        response = client.post('/api/user', data=json.dumps(data), headers=auth_headers(auth_session["access_token"]), content_type='application/json')
        assert_bad_request(response)
    
    def test_talla_justo_sobre_maximo(self, client, auth_session):
        """Límite superior inválido (justo sobre el máximo)"""
        data = {
            'nombre': 'Test',
            'apellidos': 'User',
            'fecha_nacimiento': '1990-01-01',
            'talla_m': VALIDATION_LIMITS['height_max'] + 0.01
        }
        response = client.post('/api/user', data=json.dumps(data), headers=auth_headers(auth_session["access_token"]), content_type='application/json')
        assert_bad_request(response)
    
    def test_peso_minimo_valido(self, client, sample_user, auth_session):
        """Límite inferior válido"""
        data = {'peso_kg': VALIDATION_LIMITS['weight_min']}
        response = client.post('/api/weight', data=json.dumps(data), headers=auth_headers(auth_session["access_token"]), content_type='application/json')
        assert_created(response)
    
    def test_peso_maximo_valido(self, client, sample_user, auth_session):
        """Límite superior válido"""
        data = {'peso_kg': VALIDATION_LIMITS['weight_max']}
        response = client.post('/api/weight', data=json.dumps(data), headers=auth_headers(auth_session["access_token"]), content_type='application/json')
        assert_created(response)
    
    def test_peso_justo_bajo_minimo(self, client, sample_user, auth_session):
        """Límite inferior inválido (justo debajo del mínimo)"""
        data = {'peso_kg': VALIDATION_LIMITS['weight_min'] - 0.1}
        response = client.post('/api/weight', data=json.dumps(data), headers=auth_headers(auth_session["access_token"]), content_type='application/json')
        assert_bad_request(response)
    
    def test_peso_justo_sobre_maximo(self, client, sample_user, auth_session):
        """Límite superior inválido (justo sobre el máximo)"""
        data = {'peso_kg': VALIDATION_LIMITS['weight_max'] + 0.1}
        response = client.post('/api/weight', data=json.dumps(data), headers=auth_headers(auth_session["access_token"]), content_type='application/json')
        assert_bad_request(response)
    
    def test_fecha_minimo_valido(self, client, auth_session):
        """Límite inferior válido"""
        data = {
            'nombre': 'Test',
            'apellidos': 'User',
            'fecha_nacimiento': VALIDATION_LIMITS['birth_date_min'].isoformat(),
            'talla_m': 1.75
        }
        response = client.post('/api/user', data=json.dumps(data), headers=auth_headers(auth_session["access_token"]), content_type='application/json')
        assert_success(response)
    
    def test_fecha_maximo_valido(self, client, auth_session):
        """Límite superior válido: hoy"""
        hoy = datetime.now().date().isoformat()
        data = {
            'nombre': 'Test',
            'apellidos': 'User',
            'fecha_nacimiento': hoy,
            'talla_m': 1.75
        }
        response = client.post('/api/user', data=json.dumps(data), headers=auth_headers(auth_session["access_token"]), content_type='application/json')
        assert_success(response)
    
    def test_fecha_justo_bajo_minimo(self, client, auth_session):
        """Límite inferior inválido (justo debajo del mínimo)"""
        fecha_invalida = (VALIDATION_LIMITS['birth_date_min'] - timedelta(days=1)).isoformat()
        data = {
            'nombre': 'Test',
            'apellidos': 'User',
            'fecha_nacimiento': fecha_invalida,
            'talla_m': 1.75
        }
        response = client.post('/api/user', data=json.dumps(data), headers=auth_headers(auth_session["access_token"]), content_type='application/json')
        assert_bad_request(response)
    
    def test_fecha_justo_sobre_maximo(self, client, auth_session):
        """Límite superior inválido: mañana"""
        mañana = (datetime.now() + timedelta(days=1)).date().isoformat()
        data = {
            'nombre': 'Test',
            'apellidos': 'User',
            'fecha_nacimiento': mañana,
            'talla_m': 1.75
        }
        response = client.post('/api/user', data=json.dumps(data), headers=auth_headers(auth_session["access_token"]), content_type='application/json')
        assert_bad_request(response)


class TestEquivalencePartitionsAPI:
    """Tests de particiones de equivalencia para validaciones de la API"""
    
    def test_talla_particion_invalida_baja(self, client, auth_session):
        """Partición 1: talla < height_min (inválido)"""
        casos = [
            VALIDATION_LIMITS['height_min'] - 0.3,
            VALIDATION_LIMITS['height_min'] - 0.1,
            VALIDATION_LIMITS['height_min'] - 0.01,
            -1.0,
            0
        ]
        for talla in casos:
            data = {
                'nombre': 'Test',
                'apellidos': 'User',
                'fecha_nacimiento': '1990-01-01',
                'talla_m': talla
            }
            response = client.post('/api/user', data=json.dumps(data), headers=auth_headers(auth_session["access_token"]), content_type='application/json')
            assert_bad_request(response)
    
    def test_talla_particion_valida(self, client, auth_session):
        """Partición 2: height_min <= talla <= height_max (válido)"""
        casos = [
            VALIDATION_LIMITS['height_min'],
            (VALIDATION_LIMITS['height_min'] + VALIDATION_LIMITS['height_max']) / 2,
            1.75,
            2.0,
            VALIDATION_LIMITS['height_max']
        ]
        for talla in casos:
            data = {
                'nombre': 'Test',
                'apellidos': 'User',
                'fecha_nacimiento': '1990-01-01',
                'talla_m': talla
            }
            response = client.post('/api/user', data=json.dumps(data), headers=auth_headers(auth_session["access_token"]), content_type='application/json')
            assert_success(response)
    
    def test_talla_particion_invalida_alta(self, client, auth_session):
        """Partición 3: talla > height_max (inválido)"""
        casos = [
            VALIDATION_LIMITS['height_max'] + 0.01,
            VALIDATION_LIMITS['height_max'] + 0.28,
            3.0,
            5.0,
            10.0
        ]
        for talla in casos:
            data = {
                'nombre': 'Test',
                'apellidos': 'User',
                'fecha_nacimiento': '1990-01-01',
                'talla_m': talla
            }
            response = client.post('/api/user', data=json.dumps(data), headers=auth_headers(auth_session["access_token"]), content_type='application/json')
            assert_bad_request(response)
    
    def test_peso_particion_invalido_bajo(self, client, sample_user, auth_session):
        """Partición 1: peso < weight_min (inválido)"""
        casos = [
            0,
            0.5,
            1.0,
            VALIDATION_LIMITS['weight_min'] - 0.1,
            -10
        ]
        for peso in casos:
            data = {'peso_kg': peso}
            response = client.post('/api/weight', data=json.dumps(data), headers=auth_headers(auth_session["access_token"]), content_type='application/json')
            assert_bad_request(response)
    
    def test_peso_particion_valido(self, client, sample_user, auth_session):
        """Partición 2: weight_min <= peso <= weight_max (válido)"""
        casos = [
            VALIDATION_LIMITS['weight_min'],
            50.0,
            70.0,
            100.0,
            200.0,
            500.0,
            VALIDATION_LIMITS['weight_max']
        ]
        for peso in casos:
            data = {'peso_kg': peso}
            response = client.post('/api/weight', data=json.dumps(data), headers=auth_headers(auth_session["access_token"]), content_type='application/json')
            assert_created(response)
    
    def test_peso_particion_invalido_alto(self, client, sample_user, auth_session):
        """Partición 3: peso > weight_max (inválido)"""
        casos = [
            VALIDATION_LIMITS['weight_max'] + 0.1,
            700.0,
            1000.0
        ]
        for peso in casos:
            data = {'peso_kg': peso}
            response = client.post('/api/weight', data=json.dumps(data), headers=auth_headers(auth_session["access_token"]), content_type='application/json')
            assert_bad_request(response)
    
    def test_fecha_particion_invalida_antigua(self, client, auth_session):
        """Partición 1: fecha < birth_date_min (inválido)"""
        casos = [
            (VALIDATION_LIMITS['birth_date_min'] - timedelta(days=1)).isoformat(),
            (VALIDATION_LIMITS['birth_date_min'] - timedelta(days=36500)).isoformat(),
            '1000-01-01'
        ]
        for fecha in casos:
            data = {
                'nombre': 'Test',
                'apellidos': 'User',
                'fecha_nacimiento': fecha,
                'talla_m': 1.75
            }
            response = client.post('/api/user', data=json.dumps(data), headers=auth_headers(auth_session["access_token"]), content_type='application/json')
            assert_bad_request(response)
    
    def test_fecha_particion_valida(self, client, auth_session):
        """Partición 2: birth_date_min <= fecha <= hoy (válido)"""
        casos = [
            VALIDATION_LIMITS['birth_date_min'].isoformat(),
            '1950-06-15',
            '1990-05-15',
            date.today().isoformat()
        ]
        for fecha in casos:
            data = {
                'nombre': 'Test',
                'apellidos': 'User',
                'fecha_nacimiento': fecha,
                'talla_m': 1.75
            }
            response = client.post('/api/user', data=json.dumps(data), headers=auth_headers(auth_session["access_token"]), content_type='application/json')
            assert_success(response)
    
    def test_fecha_particion_invalida_futura(self, client, auth_session):
        """Partición 3: fecha > hoy (inválido)"""
        mañana = (date.today() + timedelta(days=1)).isoformat()
        futuro = (date.today() + timedelta(days=365)).isoformat()
        casos = [mañana, futuro, '2100-01-01']
        for fecha in casos:
            data = {
                'nombre': 'Test',
                'apellidos': 'User',
                'fecha_nacimiento': fecha,
                'talla_m': 1.75
            }
            response = client.post('/api/user', data=json.dumps(data), headers=auth_headers(auth_session["access_token"]), content_type='application/json')
            assert_bad_request(response)

