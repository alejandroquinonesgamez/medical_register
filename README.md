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
- **Almacenamiento Backend**: Configurable entre:
  - Memoria (volátil, para pruebas)
  - SQLite (persistente, por defecto)
  - SQLCipher (persistente y cifrado)
- **Almacenamiento Frontend**: localStorage (persistente en el navegador)
- **Tests**: 86 tests backend (pytest) + ~66 tests frontend (Jest)

## Ramas del Repositorio

Este repositorio contiene dos ramas principales:

- **`main`** - Versión de producción (recomendada)
  - Sin herramientas de desarrollo
  - Configurada para producción (`FLASK_ENV=production`)
  - Lista para despliegue en producción

- **`dev`** - Versión de desarrollo
  - Incluye herramientas de desarrollo
  - Configurada para desarrollo (`FLASK_ENV=development`)
  - Para desarrollo y testing

## Instalación Rápida

### Requisitos Previos

- Docker y docker-compose instalados
- Git (para clonar el repositorio)
- Make (opcional, para usar comandos simplificados)

### Pasos de Instalación

1. **Clonar el repositorio**:

**Para producción (recomendado - rama main):**
```bash
git clone https://github.com/alejandroquinonesgamez/medical_register.git
cd medical_register
```

**Para desarrollo (rama dev):**
```bash
git clone -b dev https://github.com/alejandroquinonesgamez/medical_register.git
cd medical_register
```

**Clonar solo la rama main (más rápido):**
```bash
git clone --single-branch --branch main https://github.com/alejandroquinonesgamez/medical_register.git
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

3. **Arrancar la aplicación**:

El proyecto ofrece múltiples opciones de arranque según tus necesidades:

#### Opciones de Arranque Básicas

**Aplicación principal (por defecto)**:
```bash
make default
# o simplemente
make
```
Arranca la aplicación principal con el backend de almacenamiento configurado por defecto (SQLite).

**Aplicación con almacenamiento en memoria**:
```bash
make memory
```
Arranca la aplicación sin base de datos persistente. Los datos se pierden al detener el contenedor. Útil para pruebas rápidas.

**Aplicación con base de datos persistente**:
```bash
make db
```
Arranca la aplicación con base de datos SQLite (o SQLCipher si está configurado). Los datos persisten entre reinicios.

#### Opciones con Docker Compose

Si prefieres usar `docker-compose` directamente:
```bash
# Aplicación principal (por defecto)
docker-compose up -d

# Con almacenamiento en memoria
STORAGE_BACKEND=memory docker-compose up -d

# Con base de datos
STORAGE_BACKEND=sqlite docker-compose up -d
```

> **Nota**: El proyecto incluye un `Makefile` que desactiva automáticamente BuildKit para evitar errores de gRPC. Se recomienda usar `make` para mayor compatibilidad.

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

### Backends de Almacenamiento

La aplicación soporta tres backends de almacenamiento configurable mediante la variable de entorno `STORAGE_BACKEND`:

- **`memory`**: Almacenamiento en memoria (por defecto en tests). Los datos se pierden al reiniciar.
- **`sqlite`**: Base de datos SQLite persistente (por defecto en producción). Los datos se guardan en `data/app.db`.
- **`sqlcipher`**: Base de datos SQLite cifrada con SQLCipher. Requiere configurar `SQLCIPHER_KEY` o usar `PASSWORD_PEPPER` como clave.

Para cambiar el backend, usa la variable de entorno:
```bash
STORAGE_BACKEND=sqlite make db
STORAGE_BACKEND=sqlcipher make db
STORAGE_BACKEND=memory make memory
```

## Comandos Disponibles

El proyecto incluye un `Makefile` con comandos útiles. Para ver todos los comandos disponibles:

```bash
make help
```

#### Comandos de Arranque
- `make` o `make default` - Arrancar la aplicación principal (por defecto)
- `make memory` - Arrancar sin BD (almacenamiento en memoria)
- `make db` - Arrancar con BD (sqlite/sqlcipher)

#### Comandos de Gestión
- `make down` - Detener todos los contenedores
- `make logs` - Ver logs de la aplicación
- `make ps` - Ver estado de los contenedores
- `make build` - Construir imágenes de la aplicación

#### Comandos de Testing
- `make test` - Ejecutar todos los tests
- `make test-backend` - Ejecutar tests backend en contenedor
- `make test-frontend` - Ejecutar tests frontend en contenedor

#### Comandos de Limpieza
- `make clean-temp` - Limpiar archivos temporales
- `make clean-all` - Limpiar TODO (DESTRUCTIVO)
- `make purge` - Detener servicios y limpiar TODO (DESTRUCTIVO)

Para ver todos los comandos disponibles: `make help`

### Configuración

- **Puerto**: 5001 (Aplicación Flask)
- **Modo**: Producción (`FLASK_ENV=production`)
- **Backend de almacenamiento**: Configurable mediante `STORAGE_BACKEND` (memory, sqlite, sqlcipher)
- **Datos persistentes**: Almacenados en `./data/` (directorios locales, no volúmenes Docker)

## Coverage

<!-- Pytest Coverage Comment:Begin -->

<img src='coverage.svg' alt='Code Coverage Badge' />

<!-- Pytest Coverage Comment:End -->
