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
- **DefectDojo**: Integrado para gestión de vulnerabilidades de seguridad

## Instalación Rápida

### Requisitos Previos

- Docker y docker-compose instalados
- Git (para clonar el repositorio)

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
```bash
docker-compose up -d
```

4. **Arrancar DefectDojo (opcional)**:
```bash
docker-compose --profile defectdojo up -d
./scripts/init_defectdojo.sh
```

El script `init_defectdojo.sh` ejecuta automáticamente:
- Migraciones de la base de datos
- Recolección de archivos estáticos
- Creación del usuario admin (admin/admin)

5. **Acceder a las aplicaciones**:
- **Aplicación Flask**: http://localhost:5001
- **DefectDojo**: http://localhost:8080
  - Usuario: `admin`
  - Contraseña: `admin`

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

## DefectDojo - Gestión de Vulnerabilidades

La aplicación incluye **DefectDojo** integrado, una plataforma open source para la gestión centralizada de vulnerabilidades de seguridad.

### Características de DefectDojo

- ✅ Gestión centralizada de vulnerabilidades
- ✅ Integración con más de 180 herramientas de seguridad (SAST, DAST, SCA)
- ✅ Priorización basada en riesgos
- ✅ Automatización de flujos de trabajo de seguridad
- ✅ Reportes y dashboards de seguridad

### Acceso a DefectDojo

1. **Desde la interfaz web**: Haz clic en el enlace "🔒 DefectDojo" en el header de la aplicación
2. **Acceso directo**: http://localhost:8080 (cuando los servicios estén ejecutándose)
3. **Aplicación Flask**: http://localhost:5001

### Iniciar DefectDojo

```bash
# Iniciar DefectDojo y sus dependencias
docker-compose --profile defectdojo up -d

# Inicializar DefectDojo (migraciones y usuario admin)
./scripts/init_defectdojo.sh

# Ver logs de DefectDojo
docker-compose --profile defectdojo logs -f defectdojo

# Verificar estado de los servicios
docker-compose --profile defectdojo ps
```

> **Nota**: El script `init_defectdojo.sh` solo necesita ejecutarse una vez, o cuando se necesite reinicializar la base de datos.

### Configuración

- **Puerto**: 8080 (DefectDojo), 5001 (Aplicación Flask)
- **Base de datos**: PostgreSQL 15 (puerto 5432)
- **Redis**: Puerto 6379 (cache y tareas asíncronas)
- **Datos persistentes**: Almacenados en `./data/` (directorios locales, no volúmenes Docker)
- **Credenciales DefectDojo por defecto**: 
  - Usuario: `admin`
  - Contraseña: `admin`
  - ⚠️ **Cambiar en producción**
- **Credenciales base de datos**: Ver `docker-compose.yml` (cambiar en producción)

Para más información, consulta la [documentación de integración de DefectDojo](docs/DEFECTDOJO_INTEGRATION.md).

## Coverage

<!-- Pytest Coverage Comment:Begin -->

<img src='coverage.svg' alt='Code Coverage Badge' />

<!-- Pytest Coverage Comment:End -->
