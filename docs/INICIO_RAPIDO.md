# Inicio Rápido

Guía para descargar y usar el proyecto desde cero.

## 📋 Requisitos

- Docker y docker-compose instalados
- Git (para clonar el repositorio)

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

### 3. Arrancar la Aplicación

**Usando docker-compose:**
```bash
docker-compose up -d
```

Accede a: **http://localhost:5001**

## 🔧 Comandos Útiles

### Ver Estado de los Servicios

```bash
docker-compose ps
```

### Ver Logs

```bash
docker-compose logs -f web
```

### Detener la Aplicación

```bash
docker-compose down
```

### Reconstruir la Aplicación

```bash
docker-compose up --build -d
```

## ⚠️ Notas Importantes

1. **Modo Producción**: La aplicación está configurada para ejecutarse en modo producción (`FLASK_ENV=production`).

2. **Datos**: Los datos se almacenan en memoria (backend) y localStorage (frontend). No hay persistencia de base de datos.

3. **Puerto**: La aplicación corre en el puerto 5001 por defecto.

## 🆘 Solución de Problemas

### No puedo acceder a la aplicación

1. Verifica que el servicio esté corriendo:
   ```bash
   docker-compose ps
   ```

2. Verifica los logs:
   ```bash
   docker-compose logs web
   ```

3. Verifica que el puerto 5001 no esté en uso:
   ```bash
   # En Linux/Mac
   lsof -i :5001
   
   # En Windows
   netstat -ano | findstr :5001
   ```

