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

.PHONY: help initDefectDojo update up build build-defectdojo logs logs-defectdojo ps down pdf_ASVS setup-env clean-temp clean-all purge

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

# Comando por defecto: arrancar solo la aplicación principal
.DEFAULT_GOAL := default
default: setup-env ## Arrancar solo la aplicación principal (por defecto)
	@echo "🚀 Arrancando aplicación principal..."
	@echo "   (Construyendo imágenes si es necesario...)"
	$(COMPOSE) up -d --build
	@echo ""
	@echo "✅ Aplicación principal arrancada"
	@echo "📊 Accede a la aplicación en: http://localhost:5001"

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
	@echo "  make logs           # Ver logs de la aplicación"
	@echo "  make logs-defectdojo # Ver logs de DefectDojo"
	@echo "  make ps             # Ver estado de contenedores"
	@echo "  make down           # Detener todos los servicios"
	@echo "  make clean-temp     # Limpia archivos temporales"
	@echo "  make clean-all      # Limpieza completa (DESTRUCTIVO)"
	@echo "  make purge          # Detener servicios y limpiar TODO (DESTRUCTIVO)"
	@echo ""

up: setup-env ## Levantar aplicación principal y DefectDojo vacío (sin findings)
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

initDefectDojo: setup-env ## Iniciar solo DefectDojo vacío (sin findings)
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

update: setup-env ## Levantar aplicación y DefectDojo, y actualizar flujo de findings
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

down: setup-env ## Detener todos los servicios
	@echo "🛑 Deteniendo todos los servicios..."
	@$(COMPOSE) down 2>nul || true
	@$(COMPOSE) --profile defectdojo down 2>nul || true
	@echo ""
	@echo "✅ Todos los servicios detenidos"

pdf_ASVS: ## Generar PDF del informe de seguridad ASVS con fecha
	@echo "📄 Generando PDF del informe de seguridad ASVS..."
	@echo ""
	@python scripts/generate_pdf_report.py
	@echo ""
	@echo "✅ PDF generado exitosamente en: docs/informes/"

clean-temp: ## Limpiar archivos temporales del proyecto
	@echo "🧹 Limpiando archivos temporales..."
	@bash scripts/clean_temp.sh

clean-all: ## Limpiar TODO y volver al estado como recién clonado (DESTRUCTIVO)
	@echo "⚠️  Ejecutando limpieza completa (DESTRUCTIVO)..."
	@bash scripts/clean_all.sh

purge: down clean-all ## Detener todos los servicios y limpiar TODO (DESTRUCTIVO)
	@echo ""
	@echo "✅ Purge completado"





