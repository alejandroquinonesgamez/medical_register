# Makefile simplificado para la aplicación médica
#
# Este Makefile gestiona el despliegue y operación de la aplicación médica
# en modo producción.
#
# Características principales:
# - Configuración automática de Docker Compose (incluyendo .env)
# - Gestión de contenedores de la aplicación principal
# - Desactiva BuildKit automáticamente para evitar problemas de compatibilidad
# - Soluciona problemas con caracteres especiales en rutas mediante COMPOSE_PROJECT_NAME
#
# Uso: make [comando]
# Ejemplo: make help

.PHONY: help build logs ps down setup-env clean-temp clean-all purge fix-containers memory db test test-backend test-frontend

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

memory: setup-env ## Arrancar con almacenamiento en memoria
	@echo "🚀 Arrancando aplicación (modo memoria)..."
	@echo "   (Construyendo imágenes si es necesario...)"
	@STORAGE_BACKEND=memory $(COMPOSE) up -d --build
	@echo ""
	@echo "✅ Aplicación principal arrancada (memory)"
	@echo "📊 Accede a la aplicación en: http://localhost:5001"

db: setup-env ## Arrancar con base de datos (sqlite/sqlcipher)
	@echo "🚀 Arrancando aplicación (modo BD)..."
	@echo "   (Construyendo imágenes si es necesario...)"
	@STORAGE_BACKEND=sqlite $(COMPOSE) up -d --build
	@echo ""
	@echo "✅ Aplicación principal arrancada (db)"
	@echo "📊 Accede a la aplicación en: http://localhost:5001"

help: ## Mostrar esta ayuda
	@echo "Comandos disponibles:"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2}'
	@echo ""
	@echo "Ejemplos:"
	@echo "  make                # Muestra la ayuda"
	@echo "  make default        # Arranca la aplicación principal"
	@echo "  make memory         # Arranca sin BD (memory)"
	@echo "  make db             # Arranca con BD (sqlite/sqlcipher)"
	@echo "  make build          # Construir imágenes de la aplicación"
	@echo "  make test           # Ejecutar todos los tests"
	@echo "  make test-backend   # Ejecutar tests backend en contenedor"
	@echo "  make test-frontend  # Ejecutar tests frontend en contenedor"
	@echo "  make logs           # Ver logs de la aplicación"
	@echo "  make ps             # Ver estado de contenedores"
	@echo "  make down           # Detener todos los servicios"
	@echo "  make clean-temp     # Limpia archivos temporales"
	@echo "  make clean-all      # Limpieza completa (DESTRUCTIVO)"
	@echo "  make purge          # Detener servicios y limpiar TODO (DESTRUCTIVO)"
	@echo ""

logs: setup-env ## Ver logs de la aplicación principal
	@echo "📋 Logs de la aplicación principal (Ctrl+C para salir)..."
	@$(COMPOSE) logs -f web

ps: setup-env ## Ver estado de todos los contenedores
	@echo "📊 Estado de los contenedores:"
	@$(COMPOSE) ps

build: setup-env ## Construir imágenes de la aplicación principal
	@echo "🔨 Construyendo imágenes de la aplicación principal..."
	@$(COMPOSE) build
	@echo ""
	@echo "✅ Imágenes construidas"

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
	@echo ""
	@echo "✅ Todos los servicios detenidos"

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
	@echo "✅ Problema solucionado. Ahora ejecuta: make default"

clean-all: ## Limpiar TODO y volver al estado como recién clonado (DESTRUCTIVO)
	@echo "⚠️  Ejecutando limpieza completa (DESTRUCTIVO)..."
	@bash scripts/clean_all.sh

purge: down clean-all ## Detener todos los servicios y limpiar TODO (DESTRUCTIVO)
	@echo ""
	@echo "✅ Purge completado"





