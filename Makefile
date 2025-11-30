# Makefile simplificado para la aplicación médica
# Desactiva BuildKit automáticamente para evitar errores

.PHONY: help initDefectDojo update logs logs-defectdojo ps down pdf_ASVS

# Variables
COMPOSE = COMPOSE_DOCKER_CLI_BUILD=0 DOCKER_BUILDKIT=0 docker-compose

# Comando por defecto: arrancar solo la aplicación principal
.DEFAULT_GOAL := default
default: ## Arrancar solo la aplicación principal (por defecto)
	@echo "🚀 Arrancando aplicación principal..."
	$(COMPOSE) up -d
	@echo ""
	@echo "✅ Aplicación principal arrancada"
	@echo "📊 Accede a la aplicación en: http://localhost:5001"

help: ## Mostrar esta ayuda
	@echo "Comandos disponibles:"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2}'
	@echo ""

initDefectDojo: ## Iniciar DefectDojo vacío (sin findings)
	@echo "🔧 Iniciando DefectDojo vacío (sin findings)..."
	@echo ""
	@echo "ℹ️  Nota: Se iniciará DefectDojo pero sin crear findings automáticamente"
	@echo ""
	@echo "Paso 1/2: Arrancando servicios de DefectDojo..."
	@DD_SKIP_FINDINGS=True $(COMPOSE) --profile defectdojo up -d
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

update: ## Levantar aplicación y DefectDojo, y actualizar flujo de findings
	@echo "🔄 Actualizando aplicación y flujo de findings..."
	@echo ""
	@echo "Paso 1/3: Verificando aplicación principal..."
	@$(COMPOSE) ps web 2>nul | findstr /C:"Up" >nul 2>&1 || $(COMPOSE) ps web | grep -q "Up" || \
		(echo "   Arrancando aplicación principal..." && $(COMPOSE) up -d web)
	@echo "   ✓ Aplicación principal lista"
	@echo ""
	@echo "Paso 2/3: Verificando DefectDojo..."
	@$(COMPOSE) --profile defectdojo ps defectdojo 2>nul | findstr /C:"Up" >nul 2>&1 || $(COMPOSE) --profile defectdojo ps defectdojo | grep -q "Up" || \
		(echo "   Arrancando DefectDojo..." && $(COMPOSE) --profile defectdojo up -d && \
		echo "   ⏳ Esperando 60 segundos..." && \
		(powershell -Command "Start-Sleep -Seconds 60" 2>nul || sleep 60))
	@echo "   ✓ DefectDojo listo"
	@echo ""
	@echo "Paso 3/3: Actualizando flujo de findings con fechas históricas..."
	@bash scripts/mark_findings_resolved_with_dates.sh || \
		(echo "" && echo "⚠️  Si el script falla, espera unos segundos más y vuelve a ejecutar: make update")
	@echo ""
	@echo "✅ Actualización completada"
	@echo ""
	@echo "📊 Accede a:"
	@echo "   Aplicación: http://localhost:5001"
	@echo "   DefectDojo: http://localhost:8080/engagement/1/"

logs: ## Ver logs de la aplicación principal
	@echo "📋 Logs de la aplicación principal (Ctrl+C para salir)..."
	@$(COMPOSE) logs -f web

logs-defectdojo: ## Ver logs de DefectDojo
	@echo "📋 Logs de DefectDojo (Ctrl+C para salir)..."
	@$(COMPOSE) --profile defectdojo logs -f defectdojo

ps: ## Ver estado de todos los contenedores
	@echo "📊 Estado de los contenedores:"
	@echo ""
	@echo "=== Aplicación Principal ==="
	@$(COMPOSE) ps
	@echo ""
	@echo "=== DefectDojo ==="
	@$(COMPOSE) --profile defectdojo ps

down: ## Detener todos los servicios
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
