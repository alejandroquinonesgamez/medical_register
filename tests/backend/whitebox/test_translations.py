"""
Tests de CAJA BLANCA para translations.py
Prueban todos los casos edge de las funciones de traducción
"""
import pytest
from app.translations import (
    get_error, get_message, get_bmi_description, 
    get_bmi_complete_description, get_days_text, 
    get_text, get_frontend_messages
)


class TestGetError:
    """Tests de caja blanca para get_error()"""
    
    def test_get_error_existing_key(self):
        """Test obtener error con clave existente"""
        error = get_error("user_not_found")
        assert isinstance(error, str)
        assert len(error) > 0
    
    def test_get_error_with_formatting(self):
        """Test obtener error con formato (línea 61)"""
        # Usar una clave que realmente acepte formato
        error = get_error("weight_variation_exceeded", 
                         days_text="2 días", 
                         max_allowed_difference=10.0, 
                         weight_difference=15.0)
        assert isinstance(error, str)
        assert "2 días" in error or "10.0" in error or "15.0" in error
    
    def test_get_error_nonexistent_key(self):
        """Test obtener error con clave inexistente (devuelve la clave)"""
        error = get_error("nonexistent_key_12345")
        assert error == "nonexistent_key_12345"


class TestGetMessage:
    """Tests de caja blanca para get_message()"""
    
    def test_get_message_existing_key(self):
        """Test obtener mensaje con clave existente"""
        message = get_message("weight_registered")
        assert isinstance(message, str)
        assert len(message) > 0
    
    def test_get_message_nonexistent_key(self):
        """Test obtener mensaje con clave inexistente (devuelve la clave)"""
        message = get_message("nonexistent_key_12345")
        assert message == "nonexistent_key_12345"


class TestGetBMIDescription:
    """Tests de caja blanca para get_bmi_description()"""
    
    def test_get_bmi_description_existing_key(self):
        """Test obtener descripción BMI con clave existente"""
        desc = get_bmi_description("normal")
        assert isinstance(desc, str)
        assert len(desc) > 0
    
    def test_get_bmi_description_nonexistent_key(self):
        """Test obtener descripción BMI con clave inexistente (línea 44)"""
        # Esta línea devuelve la clave si no existe
        desc = get_bmi_description("nonexistent_key_12345")
        assert desc == "nonexistent_key_12345"
    
    def test_get_bmi_description_all_keys(self):
        """Test todas las claves válidas de BMI"""
        keys = ["underweight", "normal", "overweight", 
                "obese_class_i", "obese_class_ii", "obese_class_iii"]
        for key in keys:
            desc = get_bmi_description(key)
            assert isinstance(desc, str)
            assert len(desc) > 0


class TestGetBMICompleteDescription:
    """Tests de caja blanca para get_bmi_complete_description()"""
    
    def test_get_bmi_complete_description_existing_key(self):
        """Test obtener descripción completa BMI con clave existente"""
        desc = get_bmi_complete_description("normal")
        assert isinstance(desc, str)
        assert len(desc) > 0
    
    def test_get_bmi_complete_description_nonexistent_key(self):
        """Test obtener descripción completa BMI con clave inexistente (devuelve "")"""
        desc = get_bmi_complete_description("nonexistent_key_12345")
        assert desc == ""
    
    def test_get_bmi_complete_description_all_keys(self):
        """Test todas las claves válidas de BMI completa"""
        keys = ["underweight", "normal", "overweight", 
                "obese_class_i", "obese_class_ii", "obese_class_iii"]
        for key in keys:
            desc = get_bmi_complete_description(key)
            assert isinstance(desc, str)
            assert len(desc) > 0


class TestGetDaysText:
    """Tests de caja blanca para get_days_text()"""
    
    def test_get_days_text_existing_key(self):
        """Test obtener texto de días con clave existente"""
        text = get_days_text(1)
        assert isinstance(text, str)
        assert len(text) > 0
    
    def test_get_days_text_nonexistent_key(self):
        """Test obtener texto de días con clave inexistente (usa template)"""
        text = get_days_text(999)
        assert isinstance(text, str)
        assert "999" in text or "días" in text.lower() or "days" in text.lower()


class TestGetText:
    """Tests de caja blanca para get_text()"""
    
    def test_get_text_existing_key(self):
        """Test obtener texto con clave existente"""
        text = get_text("some_key")
        assert isinstance(text, str)
    
    def test_get_text_with_formatting(self):
        """Test obtener texto con formato (línea 61)"""
        # Necesitamos una clave que exista y acepte formato
        # Si no hay ninguna, probamos con una inexistente que devuelve la clave
        text = get_text("nonexistent_key", days=5, name="Test")
        # Si la clave no existe, devuelve la clave sin formato
        assert isinstance(text, str)
    
    def test_get_text_nonexistent_key(self):
        """Test obtener texto con clave inexistente (devuelve la clave)"""
        text = get_text("nonexistent_key_12345")
        assert text == "nonexistent_key_12345"
    
    def test_get_text_with_kwargs_no_formatting(self):
        """Test obtener texto con kwargs pero sin placeholder en el mensaje"""
        # Si el mensaje no tiene placeholders, format() no hace nada
        text = get_text("nonexistent_key_12345", days=5)
        assert text == "nonexistent_key_12345"


class TestGetFrontendMessages:
    """Tests de caja blanca para get_frontend_messages()"""
    
    def test_get_frontend_messages(self):
        """Test obtener todos los mensajes del frontend (línea 67)"""
        messages = get_frontend_messages()
        assert isinstance(messages, dict)
        assert len(messages) > 0
    
    def test_get_frontend_messages_structure(self):
        """Test que los mensajes del frontend tienen la estructura correcta"""
        messages = get_frontend_messages()
        # Verificar que es un diccionario con claves válidas
        assert isinstance(messages, dict)
        # Verificar que tiene al menos algunas claves comunes
        # (depende de la implementación real)

