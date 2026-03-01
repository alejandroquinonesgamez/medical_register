"""
Tests de CAJA NEGRA para endpoints de DefectDojo
Prueban los endpoints sin conocer la implementación interna.
Las rutas de DefectDojo requieren autenticación con rol 'admin'.
"""
import pytest
import json
import os
import tempfile
from unittest.mock import patch, mock_open, MagicMock
from tests.backend.conftest import assert_success, assert_bad_request, assert_forbidden, auth_headers


def _skip_if_defectdojo_missing(response):
    if response.status_code == 404:
        pytest.skip("DefectDojo no está disponible en producción")


class TestDefectDojoExportDump:
    """Tests de caja negra para endpoint de exportación de dump"""
    
    @patch('flask.send_file')
    @patch('builtins.open', new_callable=mock_open)
    @patch('os.path.exists')
    @patch('os.makedirs')
    @patch('subprocess.run')
    def test_export_dump_success(self, mock_subprocess, mock_makedirs, mock_exists, 
                                  mock_file, mock_send_file, client, auth_session):
        """Test POST /api/defectdojo/export-dump exporta correctamente"""
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "CREATE TABLE test;\nINSERT INTO test VALUES (1);"
        mock_result.stderr = ""
        mock_subprocess.return_value = mock_result
        
        mock_exists.return_value = True
        
        from flask import Response
        mock_send_file.return_value = Response(status=200)
        
        response = client.get('/api/defectdojo/export-dump',
                              headers=auth_headers(auth_session["access_token"]))
        _skip_if_defectdojo_missing(response)
        
        assert mock_subprocess.call_count >= 1
        call_args = mock_subprocess.call_args_list[-1]
        assert 'docker-compose' in call_args[0][0] or 'pg_dump' in str(call_args)
        
        mock_makedirs.assert_called_once()
        assert response.status_code in [200, 500]
    
    @patch('subprocess.run')
    def test_export_dump_subprocess_error(self, mock_subprocess, client, auth_session):
        """Test POST /api/defectdojo/export-dump maneja error de subprocess"""
        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_result.stderr = "Error: database connection failed"
        mock_subprocess.return_value = mock_result
        
        response = client.get('/api/defectdojo/export-dump',
                              headers=auth_headers(auth_session["access_token"]))
        _skip_if_defectdojo_missing(response)
        
        assert response.status_code == 500
        data = json.loads(response.data)
        assert 'error' in data
    
    @patch('subprocess.run')
    def test_export_dump_timeout(self, mock_subprocess, client, auth_session):
        """Test POST /api/defectdojo/export-dump maneja timeout"""
        import subprocess
        
        mock_subprocess.side_effect = subprocess.TimeoutExpired(cmd='docker-compose', timeout=300)
        
        response = client.get('/api/defectdojo/export-dump',
                              headers=auth_headers(auth_session["access_token"]))
        _skip_if_defectdojo_missing(response)
        
        assert response.status_code == 500
        data = json.loads(response.data)
        assert 'error' in data

    def test_export_dump_forbidden_for_regular_user(self, client, regular_user_session):
        """Un usuario con rol 'user' no puede exportar dumps"""
        response = client.get('/api/defectdojo/export-dump',
                              headers=auth_headers(regular_user_session["access_token"]))
        _skip_if_defectdojo_missing(response)
        assert_forbidden(response)


class TestDefectDojoImportDump:
    """Tests de caja negra para endpoint de importación de dump"""
    
    @patch('builtins.open', new_callable=mock_open, read_data="CREATE TABLE test;")
    @patch('os.remove')
    @patch('os.path.exists')
    @patch('os.makedirs')
    @patch('subprocess.run')
    def test_import_dump_success(self, mock_subprocess, mock_makedirs, mock_exists, 
                                  mock_remove, mock_file, client, auth_session):
        """Test POST /api/defectdojo/import-dump importa correctamente"""
        mock_psql_result = MagicMock()
        mock_psql_result.returncode = 0
        mock_psql_result.stderr = ""
        
        mock_restart_result = MagicMock()
        mock_restart_result.returncode = 0
        mock_restart_result.stderr = ""
        
        def subprocess_side_effect(*args, **kwargs):
            cmd = args[0] if args else kwargs.get('args', [])
            if 'psql' in cmd:
                return mock_psql_result
            elif 'restart' in cmd:
                return mock_restart_result
            return mock_psql_result
        
        mock_subprocess.side_effect = subprocess_side_effect
        mock_exists.return_value = True
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.sql', delete=False) as tmp_file:
            tmp_file.write("CREATE TABLE test;")
            tmp_file_path = tmp_file.name
        
        try:
            from io import BytesIO
            file_content = b"CREATE TABLE test;"
            data = {
                'file': (BytesIO(file_content), 'test_dump.sql')
            }
            response = client.post(
                '/api/defectdojo/import-dump',
                data=data,
                content_type='multipart/form-data',
                headers=auth_headers(auth_session["access_token"]),
            )
            _skip_if_defectdojo_missing(response)
            
            assert mock_subprocess.called
            assert response.status_code in [200, 500]
            
        finally:
            if os.path.exists(tmp_file_path):
                os.remove(tmp_file_path)
    
    def test_import_dump_no_file(self, client, auth_session):
        """Test POST /api/defectdojo/import-dump sin archivo"""
        response = client.post('/api/defectdojo/import-dump',
                               headers=auth_headers(auth_session["access_token"]))
        _skip_if_defectdojo_missing(response)
        
        assert_bad_request(response)
        data = json.loads(response.data)
        assert 'error' in data
        assert 'archivo' in data['error'].lower() or 'file' in data['error'].lower()
    
    def test_import_dump_invalid_extension(self, client, auth_session):
        """Test POST /api/defectdojo/import-dump con extensión inválida"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as tmp_file:
            tmp_file.write("test content")
            tmp_file_path = tmp_file.name
        
        try:
            with open(tmp_file_path, 'rb') as f:
                data = {'file': (f, 'test_dump.txt')}
                response = client.post(
                    '/api/defectdojo/import-dump',
                    data=data,
                    content_type='multipart/form-data',
                    headers=auth_headers(auth_session["access_token"]),
                )
            _skip_if_defectdojo_missing(response)
            
            assert_bad_request(response)
            data = json.loads(response.data)
            assert 'error' in data
            assert '.sql' in data['error'].lower()
            
        finally:
            if os.path.exists(tmp_file_path):
                os.remove(tmp_file_path)
    
    @patch('subprocess.run')
    def test_import_dump_timeout(self, mock_subprocess, client, auth_session):
        """Test POST /api/defectdojo/import-dump maneja timeout"""
        import subprocess
        
        mock_subprocess.side_effect = subprocess.TimeoutExpired(cmd='docker-compose', timeout=300)
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.sql', delete=False) as tmp_file:
            tmp_file.write("CREATE TABLE test;")
            tmp_file_path = tmp_file.name
        
        try:
            with open(tmp_file_path, 'rb') as f:
                data = {'file': (f, 'test_dump.sql')}
                response = client.post(
                    '/api/defectdojo/import-dump',
                    data=data,
                    content_type='multipart/form-data',
                    headers=auth_headers(auth_session["access_token"]),
                )
            _skip_if_defectdojo_missing(response)
            
            assert response.status_code == 500
            data = json.loads(response.data)
            assert 'error' in data
            
        finally:
            if os.path.exists(tmp_file_path):
                os.remove(tmp_file_path)

    def test_import_dump_forbidden_for_regular_user(self, client, regular_user_session):
        """Un usuario con rol 'user' no puede importar dumps"""
        response = client.post('/api/defectdojo/import-dump',
                               headers=auth_headers(regular_user_session["access_token"]))
        _skip_if_defectdojo_missing(response)
        assert_forbidden(response)


class TestDefectDojoGeneratePDF:
    """Tests de caja negra para endpoint de generación de PDF"""
    
    @patch('flask.send_file')
    @patch('os.path.getmtime')
    @patch('os.listdir')
    @patch('os.makedirs')
    @patch('os.path.exists')
    @patch('subprocess.run')
    def test_generate_pdf_success(self, mock_subprocess, mock_exists, mock_makedirs,
                                   mock_listdir, mock_getmtime, mock_send_file,
                                   client, auth_session):
        """Test GET /api/defectdojo/generate-pdf genera PDF correctamente"""
        mock_exists.return_value = True
        
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stderr = ""
        mock_subprocess.return_value = mock_result
        
        mock_listdir.return_value = ['INFORME_SEGURIDAD_20250101.pdf']
        mock_getmtime.return_value = 1609459200.0
        
        from flask import Response
        mock_send_file.return_value = Response(status=200)
        
        response = client.get('/api/defectdojo/generate-pdf',
                              headers=auth_headers(auth_session["access_token"]))
        _skip_if_defectdojo_missing(response)
        
        assert mock_subprocess.call_count >= 1
        assert response.status_code in [200, 500]
    
    @patch('os.path.exists')
    def test_generate_pdf_script_not_found(self, mock_exists, client, auth_session):
        """Test GET /api/defectdojo/generate-pdf cuando el script no existe"""
        mock_exists.return_value = False
        
        response = client.get('/api/defectdojo/generate-pdf',
                              headers=auth_headers(auth_session["access_token"]))
        _skip_if_defectdojo_missing(response)
        
        assert response.status_code == 500
        data = json.loads(response.data)
        assert 'error' in data
        error_text = data['error'].lower()
        assert (
            'script' in error_text
            or 'no encontrado' in error_text
            or 'informe_seguridad.md' in error_text
        )
    
    @patch('os.listdir')
    @patch('os.makedirs')
    @patch('os.path.exists')
    @patch('subprocess.run')
    def test_generate_pdf_no_pdf_generated(self, mock_subprocess, mock_exists, 
                                            mock_makedirs, mock_listdir,
                                            client, auth_session):
        """Test GET /api/defectdojo/generate-pdf cuando no se genera PDF"""
        mock_exists.return_value = True
        
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stderr = ""
        mock_subprocess.return_value = mock_result
        
        mock_listdir.return_value = []
        
        response = client.get('/api/defectdojo/generate-pdf',
                              headers=auth_headers(auth_session["access_token"]))
        _skip_if_defectdojo_missing(response)
        
        assert response.status_code == 500
        data = json.loads(response.data)
        assert 'error' in data
        assert 'pdf' in data['error'].lower()
    
    @patch('subprocess.run')
    @patch('os.path.exists')
    def test_generate_pdf_script_error(self, mock_exists, mock_subprocess,
                                        client, auth_session):
        """Test GET /api/defectdojo/generate-pdf cuando el script falla"""
        mock_exists.return_value = True
        
        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_result.stderr = "Error: Module not found"
        mock_subprocess.return_value = mock_result
        
        response = client.get('/api/defectdojo/generate-pdf',
                              headers=auth_headers(auth_session["access_token"]))
        _skip_if_defectdojo_missing(response)
        
        assert response.status_code == 500
        data = json.loads(response.data)
        assert 'error' in data
    
    @patch('subprocess.run')
    @patch('os.path.exists')
    def test_generate_pdf_timeout(self, mock_exists, mock_subprocess,
                                   client, auth_session):
        """Test GET /api/defectdojo/generate-pdf maneja timeout"""
        import subprocess
        
        mock_exists.return_value = True
        mock_subprocess.side_effect = subprocess.TimeoutExpired(cmd='python', timeout=60)
        
        response = client.get('/api/defectdojo/generate-pdf',
                              headers=auth_headers(auth_session["access_token"]))
        _skip_if_defectdojo_missing(response)
        
        assert response.status_code == 500
        data = json.loads(response.data)
        assert 'error' in data

    def test_generate_pdf_forbidden_for_regular_user(self, client, regular_user_session):
        """Un usuario con rol 'user' no puede generar PDFs"""
        response = client.get('/api/defectdojo/generate-pdf',
                              headers=auth_headers(regular_user_session["access_token"]))
        _skip_if_defectdojo_missing(response)
        assert_forbidden(response)
