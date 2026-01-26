"""
Tests de CAJA NEGRA para seguridad
Prueban headers de seguridad y redirecciones
"""
import pytest
from tests.backend.conftest import assert_success


class TestSecurityHeaders:
    """Tests de caja negra para headers de seguridad"""
    
    def test_security_headers_present(self, client):
        """Test que todos los headers de seguridad están presentes en las respuestas"""
        response = client.get('/')
        
        # Verificar headers de seguridad
        assert 'X-Frame-Options' in response.headers
        assert response.headers['X-Frame-Options'] == 'DENY'
        
        assert 'X-Content-Type-Options' in response.headers
        assert response.headers['X-Content-Type-Options'] == 'nosniff'
        
        assert 'Content-Security-Policy' in response.headers
        assert "frame-ancestors 'none'" in response.headers['Content-Security-Policy']
        
        assert 'X-XSS-Protection' in response.headers
        assert response.headers['X-XSS-Protection'] == '1; mode=block'
    
    def test_security_headers_on_api_endpoint(self, client, sample_user, auth_session):
        """Test que los headers de seguridad están presentes en endpoints de API"""
        response = client.get('/api/user')
        
        # Verificar headers de seguridad
        assert 'X-Frame-Options' in response.headers
        assert response.headers['X-Frame-Options'] == 'DENY'
        
        assert 'X-Content-Type-Options' in response.headers
        assert response.headers['X-Content-Type-Options'] == 'nosniff'
        
        assert 'Content-Security-Policy' in response.headers
        assert "frame-ancestors 'none'" in response.headers['Content-Security-Policy']
        
        assert 'X-XSS-Protection' in response.headers
        assert response.headers['X-XSS-Protection'] == '1; mode=block'
    
    def test_security_headers_on_json_response(self, client, sample_user):
        """Test que los headers de seguridad están presentes en respuestas JSON"""
        response = client.get('/api/config')
        
        # Verificar headers de seguridad
        assert 'X-Frame-Options' in response.headers
        assert 'X-Content-Type-Options' in response.headers
        assert 'Content-Security-Policy' in response.headers
        assert 'X-XSS-Protection' in response.headers
    
    def test_security_headers_on_error_response(self, client):
        """Test que los headers de seguridad están presentes en respuestas de error"""
        # Solicitud que generará un error 404
        response = client.get('/api/nonexistent')
        
        # Verificar headers de seguridad incluso en errores
        assert 'X-Frame-Options' in response.headers
        assert 'X-Content-Type-Options' in response.headers
        assert 'Content-Security-Policy' in response.headers
        assert 'X-XSS-Protection' in response.headers



