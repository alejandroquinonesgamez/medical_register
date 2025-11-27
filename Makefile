# Makefile para facilitar el uso de Docker Compose
# Desactiva BuildKit automáticamente para evitar errores

.PHONY: help up down build start stop restart logs ps shell test clean

# Variables
COMPOSE = COMPOSE_DOCKER_CLI_BUILD=0 DOCKER_BUILDKIT=0 docker-compose

help: ## Mostrar esta ayuda
	@echo "Comandos disponibles:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}'

up: ## Arrancar la aplicación principal
	$(COMPOSE) up -d

up-defectdojo: ## Arrancar DefectDojo
	$(COMPOSE) --profile defectdojo up -d

up-all: ## Arrancar todo (aplicación + DefectDojo)
	$(COMPOSE) up -d
	$(COMPOSE) --profile defectdojo up -d

down: ## Detener todos los contenedores
	$(COMPOSE) down
	$(COMPOSE) --profile defectdojo down

down-all: ## Detener todo y eliminar volúmenes
	$(COMPOSE) down -v
	$(COMPOSE) --profile defectdojo down -v

build: ## Construir las imágenes
	$(COMPOSE) build

build-defectdojo: ## Construir solo DefectDojo (si aplica)
	$(COMPOSE) --profile defectdojo build

start: ## Iniciar contenedores existentes
	$(COMPOSE) start

stop: ## Detener contenedores sin eliminarlos
	$(COMPOSE) stop
	$(COMPOSE) --profile defectdojo stop

restart: ## Reiniciar contenedores
	$(COMPOSE) restart
	$(COMPOSE) --profile defectdojo restart

logs: ## Ver logs de la aplicación
	$(COMPOSE) logs -f web

logs-defectdojo: ## Ver logs de DefectDojo
	$(COMPOSE) --profile defectdojo logs -f defectdojo

logs-all: ## Ver logs de todos los servicios
	$(COMPOSE) logs -f
	$(COMPOSE) --profile defectdojo logs -f

ps: ## Ver estado de los contenedores
	$(COMPOSE) ps
	$(COMPOSE) --profile defectdojo ps

shell: ## Abrir shell en el contenedor web
	$(COMPOSE) exec web /bin/bash

test: ## Ejecutar tests
	$(COMPOSE) run --rm frontend-tests

clean: ## Limpiar contenedores, imágenes y volúmenes no utilizados
	$(COMPOSE) down -v --remove-orphans
	$(COMPOSE) --profile defectdojo down -v --remove-orphans
	docker system prune -f


