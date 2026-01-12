# Aplicación Médica - Registro de Peso e IMC

Aplicación web monousuario para el registro personal de peso, talla y cálculo del Índice de Masa Corporal (IMC).

## Características

- ✅ Registro de datos personales (nombre, apellidos, fecha de nacimiento, talla)
- ✅ Registro de peso con fecha y hora
- ✅ Cálculo automático de IMC con descripción detallada
- ✅ Estadísticas históricas (número de pesajes, peso máximo, peso mínimo)
- ✅ Sincronización bidireccional entre frontend y backend
- ✅ Validaciones defensivas en múltiples capas
- ✅ Modo offline (funciona sin conexión al servidor)
- ✅ Internacionalización (i18n)

## Arquitectura

- **Backend**: Flask (Python) con API REST
- **Frontend**: JavaScript vanilla con localStorage
- **Almacenamiento**: Memoria (backend) + localStorage (frontend)
- **Tests**: 86 tests backend (pytest) + ~66 tests frontend (Jest)

## Instalación Rápida

### Requisitos Previos

- Docker y docker-compose instalados
- Git (para clonar el repositorio)
- Make (opcional, para usar comandos simplificados)

### Pasos de Instalación

1. **Clonar el repositorio**:
```bash
git clone <url-del-repositorio>
cd medical_register
```

2. **Ejecutar el script de configuración**:
```bash
./scripts/setup.sh
```

Este script:
- Crea los directorios necesarios para datos persistentes
- Verifica que Docker esté instalado
- Construye la imagen de la aplicación

3. **Arrancar la aplicación principal**:

**Opción A - Usando Make (recomendado)**:
```bash
make up
```

**Opción B - Usando docker-compose directamente**:
```bash
docker-compose up -d
```

4. **Acceder a la aplicación**:
- **Aplicación Flask**: http://localhost:5001

## Validaciones Defensivas

La aplicación implementa validaciones defensivas en múltiples capas para garantizar la integridad de los datos:

### Backend
- Validación de límites antes de guardar datos (altura: 0.4-2.72m, peso: 2-650kg)
- Validación de variación de peso por día (máximo 5kg/día)
- **Validación defensiva antes de calcular IMC**: Verifica que los datos almacenados estén dentro de los límites antes de ejecutar funciones helper

### Frontend
- Validación en formularios antes de enviar datos
- **Validación defensiva antes de calcular IMC**: Verifica que los datos locales estén dentro de los límites antes de calcular
- Validación de variación de peso en tiempo real

## Comandos Disponibles

### Docker Compose

```bash
# Arrancar la aplicación
docker-compose up -d

# Ver logs
docker-compose logs -f web

# Detener la aplicación
docker-compose down

# Reconstruir la aplicación
docker-compose up --build -d
```

### Configuración

- **Puerto**: 5001 (Aplicación Flask)
- **Modo**: Producción (`FLASK_ENV=production`)
- **Datos**: Almacenados en memoria (backend) y localStorage (frontend)

## Coverage

<!-- Pytest Coverage Comment:Begin -->

<img src='coverage.svg' alt='Code Coverage Badge' />

<!-- Pytest Coverage Comment:End -->
