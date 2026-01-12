# Instrucciones para Ejecutar la Aplicación en Producción

## Cambios Realizados

La aplicación ha sido limpiada para producción:

✅ **Eliminado:**
- Herramientas de desarrollo (`dev-tools.js`)
- Sidebar OWASP ASVS
- Funcionalidad DefectDojo (exportar/importar dumps, generar PDF)
- Rutas API de DefectDojo/WSTG
- Servicios Docker de DefectDojo
- Referencias a ASVS/OWASP en el código

✅ **Configuración:**
- `FLASK_ENV=production` en docker-compose.yml
- Modo debug desactivado en producción
- Redes Docker simplificadas

## Ejecutar la Aplicación

### Opción 1: Usando Docker Compose (Recomendado)

1. **Asegúrate de que Docker esté corriendo:**
   ```bash
   docker ps
   ```

2. **Construir y ejecutar la aplicación:**
   ```bash
   docker-compose up --build
   ```

3. **Acceder a la aplicación:**
   - Abre tu navegador en: `http://localhost:5001`

### Opción 2: Ejecutar en segundo plano

```bash
docker-compose up -d --build
```

### Ver logs

```bash
docker-compose logs -f web
```

### Detener la aplicación

```bash
docker-compose down
```

## Verificar Funcionalidad

Una vez que la aplicación esté corriendo, verifica:

1. **Página principal:** Debe cargar sin errores en la consola del navegador
2. **Registro de usuario:** Debe aparecer el modal para configurar perfil
3. **Registro de peso:** Debe permitir registrar pesos
4. **Cálculo de IMC:** Debe calcular y mostrar el IMC correctamente
5. **Estadísticas:** Debe mostrar número de pesajes, peso máximo y mínimo
6. **Últimos registros:** Debe mostrar los últimos 5 registros de peso

## Estructura Limpia

La aplicación ahora solo incluye:
- Servicio web Flask (puerto 5001)
- Frontend sin herramientas de desarrollo
- API REST para funcionalidad médica básica
- Sin dependencias de DefectDojo/ASVS/OWASP

## Notas

- La aplicación está configurada para producción (`FLASK_ENV=production`)
- No hay modo debug activado
- Todos los servicios de desarrollo han sido eliminados
- La aplicación es completamente funcional para uso en producción

