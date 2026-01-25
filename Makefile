# Makefile simplificado para la aplicación médica
#
# Este Makefile gestiona el despliegue y operación de la aplicación médica
# y su integración con DefectDojo para gestión de vulnerabilidades.
#
# Características principales:
# - Configuración automática de Docker Compose (incluyendo .env)
# - Gestión de contenedores de la aplicación principal
# - Gestión de servicios de DefectDojo (perfil defectdojo)
# - Desactiva BuildKit automáticamente para evitar problemas de compatibilidad
# - Soluciona problemas con caracteres especiales en rutas mediante COMPOSE_PROJECT_NAME
#
# Uso: make [comando]
# Ejemplo: make help

.PHONY: help initDefectDojo update up build build-defectdojo logs logs-defectdojo ps down pdf_report setup-env ensure-proxy-network clean-temp clean-all purge sync-wstg wstg-status wstg-logs fix-containers memory db local supervisor test test-backend test-frontend

# Variables
# Cargar .env si existe para configurar COMPOSE_PROJECT_NAME
-include .env

# Configurar variables de entorno para Docker Compose
COMPOSE_DOCKER_CLI_BUILD ?= 0
DOCKER_BUILDKIT ?= 0
COMPOSE_PROJECT_NAME ?= medical_register

# Exportar variables de entorno
export COMPOSE_DOCKER_CLI_BUILD
export DOCKER_BUILDKIT
export COMPOSE_PROJECT_NAME

COMPOSE = COMPOSE_DOCKER_CLI_BUILD=$(COMPOSE_DOCKER_CLI_BUILD) DOCKER_BUILDKIT=$(DOCKER_BUILDKIT) COMPOSE_PROJECT_NAME=$(COMPOSE_PROJECT_NAME) docker-compose

# Crear .env si no existe (solo en el primer uso)
.env:
	@if [ ! -f .env ]; then \
		if [ -f docker-compose.env.example ]; then \
			cp docker-compose.env.example .env; \
			echo "✓ Archivo .env creado desde docker-compose.env.example"; \
		else \
			echo "COMPOSE_PROJECT_NAME=medical_register" > .env; \
			echo "COMPOSE_DOCKER_CLI_BUILD=0" >> .env; \
			echo "DOCKER_BUILDKIT=0" >> .env; \
			echo "✓ Archivo .env creado con configuración básica"; \
		fi \
	fi

# Crear .env automáticamente si no existe
.PHONY: setup-env
setup-env:
	@if [ ! -f .env ]; then \
		if [ -f docker-compose.env.example ]; then \
			cp docker-compose.env.example .env; \
			echo "✓ Archivo .env creado desde docker-compose.env.example"; \
		else \
			echo "COMPOSE_PROJECT_NAME=medical_register" > .env; \
			echo "COMPOSE_DOCKER_CLI_BUILD=0" >> .env; \
			echo "DOCKER_BUILDKIT=0" >> .env; \
			echo "✓ Archivo .env creado con configuración básica"; \
		fi \
	fi

# Crear red externa proxy-network si no existe
.PHONY: ensure-proxy-network
ensure-proxy-network:
	@if command -v docker >/dev/null 2>&1; then \
		if ! docker network inspect proxy-network >/dev/null 2>&1; then \
			echo "🔧 Creando red externa proxy-network..."; \
			docker network create proxy-network >/dev/null; \
			echo "   ✓ Red proxy-network creada"; \
		fi; \
	fi

# Comando por defecto: arrancar solo la aplicación principal
.DEFAULT_GOAL := default
default: setup-env ensure-proxy-network ## Arrancar solo la aplicación principal (por defecto)
	@echo "🚀 Arrancando aplicación principal..."
	@echo "   (Construyendo imágenes si es necesario...)"
	$(COMPOSE) up -d --build
	@echo ""
	@echo "✅ Aplicación principal arrancada"
	@echo "📊 Accede a la aplicación en: http://localhost:5001"

memory: setup-env ensure-proxy-network ## Arrancar con almacenamiento en memoria
	@echo "🚀 Arrancando aplicación (modo memoria)..."
	@echo "   (Construyendo imágenes si es necesario...)"
	@STORAGE_BACKEND=memory $(COMPOSE) up -d --build
	@echo ""
	@echo "✅ Aplicación principal arrancada (memory)"
	@echo "📊 Accede a la aplicación en: http://localhost:5001"

db: setup-env ensure-proxy-network ## Arrancar con base de datos (sqlite/sqlcipher)
	@echo "🚀 Arrancando aplicación (modo BD)..."
	@echo "   (Construyendo imágenes si es necesario...)"
	@STORAGE_BACKEND=sqlite $(COMPOSE) up -d --build
	@echo ""
	@echo "✅ Aplicación principal arrancada (db)"
	@echo "📊 Accede a la aplicación en: http://localhost:5001"

local: setup-env ## Arrancar solo frontend en modo local (simula offline)
	@echo "🧪 Arrancando frontend en modo local (sin backend)..."
	@echo "   (Asegúrate de que el puerto 5001 esté libre)"
	@$(COMPOSE) --profile local up -d --build frontend-local
	@echo ""
	@echo "✅ Frontend local arrancado"
	@echo "📊 Accede a la aplicación en: http://localhost:5001"
	@echo "ℹ️  Modo local: la comunicación con el backend se simula como offline"

supervisor: setup-env ensure-proxy-network ## Arrancar supervisor (dev)
	@echo "🧭 Arrancando Supervisor (modo desarrollo)..."
	@APP_SUPERVISOR=1 FLASK_ENV=development $(COMPOSE) up -d --build
	@echo ""
	@echo "✅ Supervisor activo"
	@echo "📊 App: http://localhost:5001"
	@echo "🧭 Supervisor: http://localhost:5001/supervisor"

help: ## Mostrar esta ayuda
	@echo "Comandos disponibles:"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2}'
	@echo ""
	@echo "Ejemplos:"
	@echo "  make                # Muestra la ayuda"
	@echo "  make default        # Arranca la aplicación principal"
	@echo "  make up             # Arranca aplicación principal + DefectDojo vacío"
	@echo "  make initDefectDojo # Inicia solo DefectDojo vacío"
	@echo "  make update         # Despliegue completo y actualización"
	@echo "  make memory         # Arranca sin BD (memory)"
	@echo "  make db             # Arranca con BD (sqlite/sqlcipher)"
	@echo "  make local          # Arranca solo frontend (simula offline)"
	@echo "  make supervisor     # Arranca supervisor (dev)"
	@echo "  make build          # Construir imágenes de la aplicación"
	@echo "  make test           # Ejecutar todos los tests"
	@echo "  make test-backend   # Ejecutar tests backend en contenedor"
	@echo "  make test-frontend  # Ejecutar tests frontend en contenedor"
	@echo "  make logs           # Ver logs de la aplicación"
	@echo "  make logs-defectdojo # Ver logs de DefectDojo"
	@echo "  make ps             # Ver estado de contenedores"
	@echo "  make down           # Detener todos los servicios"
	@echo "  make clean-temp     # Limpia archivos temporales"
	@echo "  make clean-all      # Limpieza completa (DESTRUCTIVO)"
	@echo "  make purge          # Detener servicios y limpiar TODO (DESTRUCTIVO)"
	@echo ""

up: setup-env ensure-proxy-network ## Levantar aplicación principal y DefectDojo vacío (sin findings)
	@echo "🚀 Arrancando aplicación principal y DefectDojo vacío..."
	@echo ""
	@echo "Paso 1/3: Arrancando aplicación principal..."
	@echo "   (Construyendo imágenes si es necesario...)"
	@$(COMPOSE) up -d --build
	@echo "   ✓ Aplicación principal arrancada"
	@echo ""
	@echo "Paso 2/3: Arrancando servicios de DefectDojo..."
	@DD_SKIP_FINDINGS=True $(COMPOSE) --profile defectdojo up -d --build
	@echo ""
	@echo "⏳ Esperando 60 segundos a que DefectDojo esté listo..."
	@echo "   (Esto puede tardar en la primera ejecución...)"
	@powershell -Command "Start-Sleep -Seconds 60" 2>nul || sleep 60
	@echo ""
	@echo "Paso 3/3: Inicializando DefectDojo sin crear findings..."
	@echo "   (Solo migraciones, admin user y archivos estáticos)"
	@docker cp scripts/init_defectdojo_empty.py defectdojo:/tmp/init_defectdojo_empty.py 2>nul || \
		(echo "   Reintentando..." && powershell -Command "Start-Sleep -Seconds 5" 2>nul || sleep 5 && docker cp scripts/init_defectdojo_empty.py defectdojo:/tmp/init_defectdojo_empty.py)
	@$(COMPOSE) --profile defectdojo exec -T defectdojo python3 /tmp/init_defectdojo_empty.py 2>&1 || \
		(echo "" && echo "   ℹ️  DefectDojo puede estar ya inicializado (esto es normal)")
	@echo ""
	@echo "✅ Aplicación principal y DefectDojo vacío arrancados"
	@echo ""
	@echo "📊 Accede a:"
	@echo "   Aplicación: http://localhost:5001"
	@echo "   DefectDojo: http://localhost:8080"
	@echo "   Usuario: admin | Contraseña: admin"

initDefectDojo: setup-env ensure-proxy-network ## Iniciar solo DefectDojo vacío (sin findings)
	@echo "🔧 Iniciando DefectDojo vacío (sin findings)..."
	@echo ""
	@echo "ℹ️  Nota: Se iniciará DefectDojo pero sin crear findings automáticamente"
	@echo ""
	@echo "Paso 1/2: Arrancando servicios de DefectDojo..."
	@echo "   (Construyendo imágenes si es necesario...)"
	@DD_SKIP_FINDINGS=True $(COMPOSE) --profile defectdojo up -d --build
	@echo ""
	@echo "⏳ Esperando 60 segundos a que DefectDojo esté listo..."
	@echo "   (Esto puede tardar en la primera ejecución...)"
	@powershell -Command "Start-Sleep -Seconds 60" 2>nul || sleep 60
	@echo ""
	@echo "Paso 2/2: Inicializando DefectDojo sin crear findings..."
	@echo "   (Solo migraciones, admin user y archivos estáticos)"
	@docker cp scripts/init_defectdojo_empty.py defectdojo:/tmp/init_defectdojo_empty.py 2>nul || \
		(echo "   Reintentando..." && powershell -Command "Start-Sleep -Seconds 5" 2>nul || sleep 5 && docker cp scripts/init_defectdojo_empty.py defectdojo:/tmp/init_defectdojo_empty.py)
	@$(COMPOSE) --profile defectdojo exec -T defectdojo python3 /tmp/init_defectdojo_empty.py 2>&1 || \
		(echo "" && echo "   ℹ️  DefectDojo puede estar ya inicializado (esto es normal)")
	@echo ""
	@echo "✅ DefectDojo vacío iniciado (sin findings creados)"
	@echo ""
	@echo "📊 Accede a DefectDojo en: http://localhost:8080"
	@echo "   Usuario: admin | Contraseña: admin"

update: setup-env ensure-proxy-network ## Levantar aplicación y DefectDojo, y actualizar flujo de findings
	@echo "🔄 Actualizando aplicación y flujo de findings..."
	@echo ""
	@echo "Paso 1/3: Verificando aplicación principal..."
	@$(COMPOSE) ps web 2>nul | findstr /C:"Up" >nul 2>&1 || $(COMPOSE) ps web | grep -q "Up" || \
		(echo "   Arrancando aplicación principal..." && echo "   (Construyendo imágenes si es necesario...)" && $(COMPOSE) up -d --build web)
	@echo "   ✓ Aplicación principal lista"
	@echo ""
	@echo "Paso 2/3: Verificando DefectDojo..."
	@$(COMPOSE) --profile defectdojo ps defectdojo 2>nul | findstr /C:"Up" >nul 2>&1 || $(COMPOSE) --profile defectdojo ps defectdojo | grep -q "Up" || \
		(echo "   Arrancando DefectDojo..." && echo "   (Construyendo imágenes si es necesario...)" && $(COMPOSE) --profile defectdojo up -d --build && \
		echo "   ⏳ Esperando 60 segundos..." && \
		(powershell -Command "Start-Sleep -Seconds 60" 2>nul || sleep 60))
	@echo "   ✓ DefectDojo listo"
	@echo ""
	@echo "Paso 3/3: Actualizando flujo de findings con fechas históricas..."
	@$(COMPOSE) --profile defectdojo exec -T defectdojo python3 /app/manage_findings.py || \
		(echo "" && echo "⚠️  Si el script falla, espera unos segundos más y vuelve a ejecutar: make update")
	@echo ""
	@echo "✅ Actualización completada"
	@echo ""
	@echo "📊 Accede a:"
	@echo "   Aplicación: http://localhost:5001"
	@echo "   DefectDojo: http://localhost:8080/engagement/1/"

logs: setup-env ## Ver logs de la aplicación principal
	@echo "📋 Logs de la aplicación principal (Ctrl+C para salir)..."
	@$(COMPOSE) logs -f web

logs-defectdojo: setup-env ## Ver logs de DefectDojo
	@echo "📋 Logs de DefectDojo (Ctrl+C para salir)..."
	@$(COMPOSE) --profile defectdojo logs -f defectdojo

ps: setup-env ## Ver estado de todos los contenedores
	@echo "📊 Estado de los contenedores:"
	@echo ""
	@echo "=== Aplicación Principal ==="
	@$(COMPOSE) ps
	@echo ""
	@echo "=== DefectDojo ==="
	@$(COMPOSE) --profile defectdojo ps

build: setup-env ## Construir imágenes de la aplicación principal
	@echo "🔨 Construyendo imágenes de la aplicación principal..."
	@$(COMPOSE) build
	@echo ""
	@echo "✅ Imágenes construidas"

build-defectdojo: setup-env ## Construir imágenes de DefectDojo
	@echo "🔨 Construyendo imágenes de DefectDojo..."
	@$(COMPOSE) --profile defectdojo build
	@echo ""
	@echo "✅ Imágenes de DefectDojo construidas"
test: test-backend test-frontend ## Ejecutar todos los tests

test-backend: ## Ejecutar tests backend dentro del contenedor
	@echo "🧪 Ejecutando tests en contenedor (backend)..."
	@$(COMPOSE) run --rm web python -m pytest

test-frontend: ## Ejecutar tests frontend dentro del contenedor
	@echo "🧪 Ejecutando tests en contenedor (frontend)..."
	@$(COMPOSE) run --rm frontend-tests

down: setup-env ## Detener todos los servicios
	@echo "🛑 Deteniendo todos los servicios..."
	@$(COMPOSE) down 2>nul || true
	@$(COMPOSE) --profile defectdojo down 2>nul || true
	@echo ""
	@echo "✅ Todos los servicios detenidos"

pdf_report: setup-env ## Generar PDF del informe de seguridad (ASVS + WSTG) con fecha
	@echo "📄 Generando informe de seguridad (ASVS + WSTG) y PDF..."
	@echo ""
	@echo "Paso 1/3: Generando informe Markdown desde DefectDojo + análisis de código..."
	@if docker-compose ps defectdojo | grep -q "Up"; then \
		echo "   ℹ️  Ejecutando desde contenedor de DefectDojo para acceso a benchmarks ASVS..."; \
		docker-compose exec -T defectdojo python /app/scripts/generate_asvs_report.py; \
	else \
		echo "   ⚠️  DefectDojo no está corriendo, ejecutando localmente (sin datos de DefectDojo)..."; \
		python3 scripts/generate_asvs_report.py; \
	fi
	@echo ""
	@echo "Paso 2/3: Generando PDF desde Markdown..."
	@python3 scripts/generate_pdf_report.py
	@echo ""
	@echo "✅ PDF generado exitosamente en: docs/informes/"

clean-temp: ## Limpiar archivos temporales del proyecto
	@echo "🧹 Limpiando archivos temporales..."
	@bash scripts/clean_temp.sh

fix-containers: ## Solucionar problemas de contenedores (ContainerConfig error)
	@echo "🔧 Solucionando problemas de contenedores..."
	@echo ""
	@echo "Paso 1/3: Deteniendo y eliminando contenedores..."
	@$(COMPOSE) down -v 2>/dev/null || true
	@echo "   ✓ Contenedores eliminados"
	@echo ""
	@echo "Paso 2/3: Limpiando contenedores huérfanos..."
	@docker container prune -f 2>/dev/null || true
	@echo "   ✓ Limpieza completada"
	@echo ""
	@echo "Paso 3/3: Reconstruyendo imágenes..."
	@$(COMPOSE) build --no-cache web
	@echo "   ✓ Imágenes reconstruidas"
	@echo ""
	@echo "✅ Problema solucionado. Ahora ejecuta: make up"
clean-all: ## Limpiar TODO y volver al estado como recién clonado (DESTRUCTIVO)
	@echo "⚠️  Ejecutando limpieza completa (DESTRUCTIVO)..."
	@bash scripts/clean_all.sh

purge: down clean-all ## Detener todos los servicios y limpiar TODO (DESTRUCTIVO)
	@echo ""
	@echo "✅ Purge completado"

# Sincronización WSTG
sync-wstg: setup-env ## Sincronizar todos los findings WSTG (una vez)
	@echo "🔄 Sincronizando findings WSTG..."
	@$(COMPOSE) --profile defectdojo exec wstg-sync python /app/wstg_sync_service.py --once || \
	 $(COMPOSE) --profile defectdojo run --rm wstg-sync python /app/wstg_sync_service.py --once || \
	 echo "⚠️  Servicio wstg-sync no está corriendo. Ejecuta 'make up' o 'make initDefectDojo' primero."
	@echo "✅ Sincronización completada"

wstg-status: setup-env ## Obtener estado de sincronización WSTG
	@echo "📊 Estado de sincronización WSTG:"
	@curl -s http://localhost:5001/api/wstg/status | python3 -m json.tool || echo "⚠️  Error obteniendo estado. Verifica que la aplicación esté corriendo."

wstg-logs: setup-env ## Ver logs del servicio de sincronización WSTG
	@echo "📋 Logs del servicio WSTG:"
	@$(COMPOSE) --profile defectdojo logs --tail=50 wstg-sync || echo "⚠️  Servicio wstg-sync no está corriendo."





