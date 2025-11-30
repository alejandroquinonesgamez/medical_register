# Inicio Rápido

Guía para descargar y usar el proyecto desde cero.

## 📋 Requisitos

- Docker y docker-compose instalados
- Git (para clonar el repositorio)
- ~5GB de espacio en disco (para DefectDojo)

## 🚀 Instalación en 3 Pasos

### 1. Clonar el Repositorio

```bash
git clone <url-del-repositorio>
cd medical_register
```

### 2. Configurar el Proyecto

**En Linux/Mac o Git Bash (Windows):**
```bash
./scripts/setup.sh
```

**En PowerShell (Windows):**
```powershell
.\scripts\setup.ps1
```

Este script:
- ✅ Crea los directorios necesarios (`data/`)
- ✅ Configura automáticamente el archivo `.env` para Docker Compose (soluciona problemas con caracteres especiales)
- ✅ Verifica que Docker esté instalado
- ✅ Construye la imagen de la aplicación

> **Nota**: Si no ejecutas el script de setup, el archivo `.env` se creará automáticamente la primera vez que uses `make` o `make.ps1`. Esto soluciona problemas con rutas que contienen caracteres especiales.

### 3. Arrancar los Servicios

#### Opción A: Usando Make/make.ps1 (Recomendado)

**En Linux/Mac o Git Bash (Windows):**
```bash
# Solo la aplicación principal (por defecto)
make
# o explícitamente:
make default

# Iniciar DefectDojo vacío (sin findings)
make initDefectDojo

# Despliegue completo con actualización de findings
make update

# Ver ayuda con todos los comandos
make help
```

**En PowerShell (Windows):**
```powershell
# Solo la aplicación principal (por defecto)
.\make.ps1
# o explícitamente:
.\make.ps1 default

# Iniciar DefectDojo vacío (sin findings)
.\make.ps1 initDefectDojo

# Despliegue completo con actualización de findings
.\make.ps1 update

# Ver ayuda con todos los comandos
.\make.ps1 help
```

#### Opción B: Usando docker-compose directamente

**Solo la Aplicación Principal:**
```bash
docker-compose up -d
```

Accede a: **http://localhost:5001**

**Con DefectDojo (Gestión de Vulnerabilidades):**
```bash
# Arrancar DefectDojo y dependencias
docker-compose --profile defectdojo up -d
```

**La inicialización es automática**: Al arrancar, DefectDojo ejecuta automáticamente:
- ✅ Migraciones de la base de datos
- ✅ Recolección de archivos estáticos  
- ✅ Creación del usuario admin (admin/admin)

Accede a:
- **Aplicación Flask**: http://localhost:5001
- **DefectDojo**: http://localhost:8080
  - Usuario: `admin`
  - Contraseña: `admin`

## 📁 Estructura de Datos

Los datos persistentes se almacenan en directorios locales (no volúmenes Docker):

```
data/
├── postgres/          # Base de datos PostgreSQL
├── redis/             # Datos de Redis
└── defectdojo/
    ├── media/         # Archivos multimedia
    └── static/        # Archivos estáticos
```

Estos directorios se crean automáticamente y están en `.gitignore` (no se suben al repositorio).

## 🔧 Comandos Útiles

### Comandos Disponibles (Make/make.ps1)

#### Comandos Principales

| Comando | Descripción |
|---------|-------------|
| `make` / `.\make.ps1` | Arrancar solo la aplicación principal (por defecto) |
| `make default` / `.\make.ps1 default` | Arrancar solo la aplicación principal |
| `make initDefectDojo` / `.\make.ps1 initDefectDojo` | Iniciar DefectDojo vacío (sin findings) |
| `make update` / `.\make.ps1 update` | Levantar aplicación y DefectDojo, y actualizar flujo de findings |
| `make pdf_ASVS` / `.\make.ps1 pdf_ASVS` | Generar PDF del informe de seguridad ASVS con fecha |

#### Comandos de Gestión

| Comando | Descripción |
|---------|-------------|
| `make logs` / `.\make.ps1 logs` | Ver logs de la aplicación principal |
| `make logs-defectdojo` / `.\make.ps1 logs-defectdojo` | Ver logs de DefectDojo |
| `make ps` / `.\make.ps1 ps` | Ver estado de todos los contenedores |
| `make down` / `.\make.ps1 down` | Detener todos los servicios |
| `make check` / `.\make.ps1 check` | Verificar requisitos previos (Docker, Docker Compose) |
| `make help` / `.\make.ps1 help` | Mostrar ayuda con todos los comandos |

### Usando docker-compose directamente

#### Ver Estado de los Servicios

```bash
# Solo aplicación principal
docker-compose ps

# Con DefectDojo
docker-compose --profile defectdojo ps
```

#### Ver Logs

```bash
# Aplicación principal
docker-compose logs -f web

# DefectDojo
docker-compose --profile defectdojo logs -f defectdojo
```

#### Detener Servicios

```bash
# Solo aplicación principal
docker-compose down

# Con DefectDojo
docker-compose --profile defectdojo down
```

#### Reinicializar DefectDojo

Si necesitas empezar de cero con DefectDojo:

```bash
# Detener servicios
docker-compose --profile defectdojo down

# Eliminar datos (¡CUIDADO! Esto borra todo)
# En Linux/Mac:
rm -rf data/postgres/* data/redis/* data/defectdojo/*
# En PowerShell (Windows):
Remove-Item -Path "data\postgres\*", "data\redis\*", "data\defectdojo\*" -Recurse -Force

# Arrancar de nuevo
docker-compose --profile defectdojo up -d
./scripts/reset_defectdojo.sh
```

## ⚠️ Notas Importantes

1. **Inicialización automática**: La inicialización de DefectDojo (migraciones, estáticos, usuario admin) se ejecuta automáticamente al arrancar el contenedor. No necesitas ejecutar scripts manualmente.

2. **Tiempo de inicio**: DefectDojo puede tardar varios minutos en iniciar la primera vez (descarga de imágenes, migraciones, etc.).

3. **Credenciales**: Las credenciales por defecto (`admin/admin`) son solo para desarrollo. **Cambia las contraseñas en producción**.

4. **Raspberry Pi**: Si estás usando Raspberry Pi, DefectDojo puede requerir emulación QEMU y será más lento. Consulta `docs/RASPBERRY_PI_SETUP.md` para más información.

## 🆘 Solución de Problemas

### El script `reset_defectdojo.sh` falla

Asegúrate de que los servicios estén arrancados:

```bash
docker-compose --profile defectdojo ps
```

Si algún servicio no está "healthy", espera unos minutos y vuelve a intentar.

### No puedo acceder a DefectDojo

1. Verifica que el servicio esté corriendo:
   ```bash
   docker-compose --profile defectdojo ps defectdojo-nginx
   ```

2. Verifica los logs:
   ```bash
   docker-compose --profile defectdojo logs defectdojo
   ```

3. La inicialización es automática, pero puedes ejecutar `reset_defectdojo.sh` si hay problemas

### La base de datos está vacía

Ejecuta las migraciones manualmente:

```bash
docker-compose --profile defectdojo exec defectdojo python manage.py migrate
```

## 📚 Más Información

- [Uso de Docker Compose](DOCKER_COMPOSE_USO.md)
- [Configuración de DefectDojo](defectdojo/DEFECTDOJO_CONFIGURACION.md)
- [Credenciales de DefectDojo](defectdojo/DEFECTDOJO_CREDENTIALS.md)
- [Integración de DefectDojo](defectdojo/DEFECTDOJO_INTEGRATION.md)
- [Configuración para Raspberry Pi](RASPBERRY_PI_SETUP.md)

