"""
Tests de CAJA BLANCA para validate_and_sanitize_name() en helpers.py
Prueban todos los casos edge de validación y sanitización de nombres
"""
import pytest
from app.helpers import validate_and_sanitize_name


class TestValidateAndSanitizeName:
    """Tests de caja blanca para validate_and_sanitize_name()"""
    
    def test_valid_name_normal(self):
        """Test nombre válido normal"""
        is_valid, sanitized, error = validate_and_sanitize_name("Juan")
        assert is_valid is True
        assert sanitized == "Juan"
        assert error is None
    
    def test_valid_name_with_accent(self):
        """Test nombre válido con acentos"""
        is_valid, sanitized, error = validate_and_sanitize_name("José")
        assert is_valid is True
        assert sanitized == "José"
        assert error is None
    
    def test_valid_name_with_hyphen(self):
        """Test nombre válido con guión"""
        is_valid, sanitized, error = validate_and_sanitize_name("María-José")
        assert is_valid is True
        assert sanitized == "María-José"
        assert error is None
    
    def test_valid_name_with_apostrophe(self):
        """Test nombre válido con apóstrofe
        
        NOTA: El apóstrofe se elimina porque está en la lista de caracteres peligrosos.
        Esto es intencional para seguridad (CWE-20).
        """
        is_valid, sanitized, error = validate_and_sanitize_name("O'Brien")
        assert is_valid is True
        assert sanitized == "OBrien"  # El apóstrofe se elimina por seguridad
        assert error is None
    
    def test_valid_name_multiple_words(self):
        """Test nombre válido con múltiples palabras"""
        is_valid, sanitized, error = validate_and_sanitize_name("Juan Carlos")
        assert is_valid is True
        assert sanitized == "Juan Carlos"
        assert error is None
    
    def test_name_not_string(self):
        """Test cuando name no es un string (línea 67)"""
        is_valid, sanitized, error = validate_and_sanitize_name(123)
        assert is_valid is False
        assert sanitized == ""
        assert error == "invalid_name"
    
    def test_name_not_string_none(self):
        """Test cuando name es None"""
        is_valid, sanitized, error = validate_and_sanitize_name(None)
        assert is_valid is False
        assert sanitized == ""
        assert error == "invalid_name"
    
    def test_name_not_string_list(self):
        """Test cuando name es una lista"""
        is_valid, sanitized, error = validate_and_sanitize_name(["Juan"])
        assert is_valid is False
        assert sanitized == ""
        assert error == "invalid_name"
    
    def test_name_empty_after_strip(self):
        """Test nombre vacío después de strip (línea 74)"""
        is_valid, sanitized, error = validate_and_sanitize_name("   ")
        assert is_valid is False
        assert sanitized == ""
        assert error == "name_empty"
    
    def test_name_empty_string(self):
        """Test nombre vacío"""
        is_valid, sanitized, error = validate_and_sanitize_name("")
        assert is_valid is False
        assert sanitized == ""
        assert error == "name_empty"
    
    def test_name_too_long(self):
        """Test nombre demasiado largo (línea 78)"""
        long_name = "A" * 101  # 101 caracteres, máximo es 100
        is_valid, sanitized, error = validate_and_sanitize_name(long_name)
        assert is_valid is False
        assert sanitized == ""
        assert error == "name_too_long"
    
    def test_name_exactly_max_length(self):
        """Test nombre exactamente en el límite máximo"""
        long_name = "A" * 100  # 100 caracteres, exactamente el máximo
        is_valid, sanitized, error = validate_and_sanitize_name(long_name)
        assert is_valid is True
        assert sanitized == long_name
        assert error is None
    
    def test_name_too_short(self):
        """Test nombre demasiado corto (línea 80) - usando min_length personalizado"""
        # Usar un nombre de un solo carácter cuando min_length=2
        # (no usar "" porque eso se detecta como name_empty primero)
        is_valid, sanitized, error = validate_and_sanitize_name("A", min_length=2)
        assert is_valid is False
        assert sanitized == ""
        assert error == "invalid_name"
    
    def test_name_too_short_single_char(self):
        """Test nombre de un solo carácter cuando min_length=2"""
        is_valid, sanitized, error = validate_and_sanitize_name("A", min_length=2)
        assert is_valid is False
        assert sanitized == ""
        assert error == "invalid_name"
    
    def test_name_with_dangerous_chars_removed(self):
        """Test que se eliminan caracteres peligrosos"""
        is_valid, sanitized, error = validate_and_sanitize_name("Juan<>Carlos")
        assert is_valid is True
        assert sanitized == "JuanCarlos"
        assert error is None
    
    def test_name_with_quotes_removed(self):
        """Test que se eliminan comillas"""
        is_valid, sanitized, error = validate_and_sanitize_name('Juan"Carlos')
        assert is_valid is True
        assert sanitized == "JuanCarlos"
        assert error is None
    
    def test_name_with_single_quotes_removed(self):
        """Test que se eliminan comillas simples"""
        is_valid, sanitized, error = validate_and_sanitize_name("Juan'Carlos")
        assert is_valid is True
        assert sanitized == "JuanCarlos"
        assert error is None
    
    def test_name_with_multiple_spaces_normalized(self):
        """Test que se normalizan espacios múltiples"""
        is_valid, sanitized, error = validate_and_sanitize_name("Juan    Carlos")
        assert is_valid is True
        assert sanitized == "Juan Carlos"
        assert error is None
    
    def test_name_with_tabs_normalized(self):
        """Test que se normalizan tabs"""
        is_valid, sanitized, error = validate_and_sanitize_name("Juan\tCarlos")
        assert is_valid is True
        assert sanitized == "Juan Carlos"
        assert error is None
    
    def test_name_stripped(self):
        """Test que se eliminan espacios al inicio y final"""
        is_valid, sanitized, error = validate_and_sanitize_name("  Juan  ")
        assert is_valid is True
        assert sanitized == "Juan"
        assert error is None
    
    def test_name_with_invalid_characters(self):
        """Test nombre con caracteres no permitidos (línea 96)"""
        is_valid, sanitized, error = validate_and_sanitize_name("Juan123")
        assert is_valid is False
        assert sanitized == ""
        assert error == "invalid_name"
    
    def test_name_with_special_chars(self):
        """Test nombre con caracteres especiales no permitidos"""
        is_valid, sanitized, error = validate_and_sanitize_name("Juan@Carlos")
        assert is_valid is False
        assert sanitized == ""
        assert error == "invalid_name"
    
    def test_name_with_dots(self):
        """Test nombre con puntos"""
        is_valid, sanitized, error = validate_and_sanitize_name("Juan.Carlos")
        assert is_valid is False
        assert sanitized == ""
        assert error == "invalid_name"
    
    def test_name_only_spaces_after_sanitization(self):
        """Test nombre que solo tiene espacios después de sanitización (línea 100)"""
        # Crear un caso donde después de eliminar caracteres peligrosos solo queden espacios
        # Por ejemplo: solo caracteres peligrosos que se eliminan
        is_valid, sanitized, error = validate_and_sanitize_name("<>\"'")
        assert is_valid is False
        assert sanitized == ""
        assert error == "invalid_name"
    
    def test_name_only_spaces_after_removing_invalid_chars(self):
        """Test nombre que después de eliminar caracteres inválidos solo tiene espacios"""
        # Un nombre que tiene caracteres inválidos mezclados con espacios
        # Después de eliminar los caracteres inválidos, solo quedan espacios
        is_valid, sanitized, error = validate_and_sanitize_name("123  456")
        assert is_valid is False
        assert sanitized == ""
        assert error == "invalid_name"
    
    def test_name_with_unicode_characters(self):
        """Test nombre con caracteres Unicode válidos"""
        is_valid, sanitized, error = validate_and_sanitize_name("José María")
        assert is_valid is True
        assert sanitized == "José María"
        assert error is None
    
    def test_name_complex_valid(self):
        """Test nombre complejo pero válido
        
        NOTA: El apóstrofe se elimina porque está en la lista de caracteres peligrosos.
        """
        is_valid, sanitized, error = validate_and_sanitize_name("  María-José  O'Brien  ")
        assert is_valid is True
        assert sanitized == "María-José OBrien"  # El apóstrofe se elimina por seguridad
        assert error is None
    
    def test_name_custom_min_max_length(self):
        """Test con límites personalizados"""
        # Nombre válido con límites personalizados
        is_valid, sanitized, error = validate_and_sanitize_name("AB", min_length=2, max_length=5)
        assert is_valid is True
        assert sanitized == "AB"
        assert error is None
        
        # Nombre demasiado corto con límites personalizados
        is_valid, sanitized, error = validate_and_sanitize_name("A", min_length=2, max_length=5)
        assert is_valid is False
        assert sanitized == ""
        assert error == "invalid_name"
        
        # Nombre demasiado largo con límites personalizados
        is_valid, sanitized, error = validate_and_sanitize_name("ABCDEF", min_length=2, max_length=5)
        assert is_valid is False
        assert sanitized == ""
        assert error == "name_too_long"

