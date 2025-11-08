"""
Tests de CAJA BLANCA para helpers.py
Prueban la lógica interna de las funciones de cálculo de IMC
"""
import pytest
from app.helpers import calculate_bmi, get_bmi_description


class TestCalculateBMI:
    """Tests de caja blanca para calculate_bmi()"""
    
    def test_calculate_bmi_normal(self):
        """Test caso normal: peso y talla válidos"""
        assert calculate_bmi(70, 1.75) == 22.9
        assert calculate_bmi(60, 1.70) == 20.8
        assert calculate_bmi(80, 1.80) == 24.7
    
    def test_calculate_bmi_boundary_talla_cero(self):
        """Test valor límite: talla = 0 (debe retornar 0)"""
        assert calculate_bmi(70, 0) == 0
    
    def test_calculate_bmi_boundary_talla_negativa(self):
        """Test valor límite: talla negativa (debe retornar 0)"""
        assert calculate_bmi(70, -1) == 0
        assert calculate_bmi(70, -0.1) == 0
    
    def test_calculate_bmi_boundary_talla_pequeña(self):
        """Test valor límite: talla muy pequeña pero positiva"""
        assert calculate_bmi(10, 0.5) == 40.0
        assert calculate_bmi(5, 0.1) == 500.0
    
    def test_calculate_bmi_boundary_talla_grande(self):
        """Test valor límite: talla grande"""
        assert calculate_bmi(100, 2.5) == 16.0
    
    def test_calculate_bmi_precision(self):
        """Test que el resultado se redondea a 1 decimal"""
        # 70 / (1.75^2) = 70 / 3.0625 = 22.857...
        assert calculate_bmi(70, 1.75) == 22.9
    
    def test_calculate_bmi_peso_cero(self):
        """Test valor límite: peso = 0"""
        assert calculate_bmi(0, 1.75) == 0.0
    
    def test_calculate_bmi_peso_negativo(self):
        """Test valor límite: peso negativo (caso edge)"""
        # Aunque no debería pasar en producción, probamos el comportamiento
        assert calculate_bmi(-10, 1.75) == -3.3


class TestGetBMIDescription:
    """Tests de caja blanca para get_bmi_description() con valores límite y particiones"""
    
    # ========== PARTICIONES DE EQUIVALENCIA ==========
    # Partición 1: IMC < 18.5 -> "Bajo peso"
    # Partición 2: 18.5 <= IMC < 25 -> "Peso normal"
    # Partición 3: 25 <= IMC < 30 -> "Sobrepeso"
    # Partición 4: IMC >= 30 -> "Obesidad"
    
    def test_bajo_peso_particion_1(self):
        """Partición 1: IMC < 18.5"""
        assert get_bmi_description(15.0) == "Bajo peso"
        assert get_bmi_description(18.0) == "Bajo peso"
        assert get_bmi_description(10.5) == "Bajo peso"
    
    def test_bajo_peso_boundary_inferior(self):
        """Valor límite inferior: IMC = 0"""
        assert get_bmi_description(0) == "Bajo peso"
    
    def test_bajo_peso_boundary_superior(self):
        """Valor límite superior: IMC = 18.4 (justo antes del límite)"""
        assert get_bmi_description(18.4) == "Bajo peso"
    
    def test_peso_normal_particion_2(self):
        """Partición 2: 18.5 <= IMC < 25"""
        assert get_bmi_description(18.5) == "Peso normal"
        assert get_bmi_description(20.0) == "Peso normal"
        assert get_bmi_description(24.9) == "Peso normal"
    
    def test_peso_normal_boundary_inferior(self):
        """Valor límite inferior: IMC = 18.5 (límite exacto)"""
        assert get_bmi_description(18.5) == "Peso normal"
    
    def test_peso_normal_boundary_superior(self):
        """Valor límite superior: IMC = 24.9 (justo antes del límite)"""
        assert get_bmi_description(24.9) == "Peso normal"
    
    def test_sobrepeso_particion_3(self):
        """Partición 3: 25 <= IMC < 30"""
        assert get_bmi_description(25.0) == "Sobrepeso"
        assert get_bmi_description(27.5) == "Sobrepeso"
        assert get_bmi_description(29.9) == "Sobrepeso"
    
    def test_sobrepeso_boundary_inferior(self):
        """Valor límite inferior: IMC = 25.0 (límite exacto)"""
        assert get_bmi_description(25.0) == "Sobrepeso"
    
    def test_sobrepeso_boundary_superior(self):
        """Valor límite superior: IMC = 29.9 (justo antes del límite)"""
        assert get_bmi_description(29.9) == "Sobrepeso"
    
    def test_obesidad_particion_4(self):
        """Partición 4: IMC >= 30"""
        assert get_bmi_description(30.0) == "Obesidad"
        assert get_bmi_description(35.0) == "Obesidad"
        assert get_bmi_description(40.0) == "Obesidad"
        assert get_bmi_description(50.0) == "Obesidad"
    
    def test_obesidad_boundary_inferior(self):
        """Valor límite inferior: IMC = 30.0 (límite exacto)"""
        assert get_bmi_description(30.0) == "Obesidad"
    
    def test_obesidad_valores_extremos(self):
        """Valores límite extremos: IMC muy alto"""
        assert get_bmi_description(100.0) == "Obesidad"
        assert get_bmi_description(200.0) == "Obesidad"
    
    def test_transiciones_limite(self):
        """Tests de transición entre particiones (valores límite críticos)"""
        # Transición Bajo peso -> Peso normal
        assert get_bmi_description(18.49) == "Bajo peso"
        assert get_bmi_description(18.5) == "Peso normal"
        
        # Transición Peso normal -> Sobrepeso
        assert get_bmi_description(24.99) == "Peso normal"
        assert get_bmi_description(25.0) == "Sobrepeso"
        
        # Transición Sobrepeso -> Obesidad
        assert get_bmi_description(29.99) == "Sobrepeso"
        assert get_bmi_description(30.0) == "Obesidad"

