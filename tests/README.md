# Tests del Proyecto

Estructura organizada de tests para backend y frontend.

## Estructura General

```
tests/
├── backend/                 # Tests del backend (Python)
│   ├── blackbox/           # Tests de caja negra
│   ├── whitebox/           # Tests de caja blanca
│   └── conftest.py         # Fixtures compartidas
├── frontend/               # Tests del frontend (JavaScript)
│   ├── test_whitebox_helpers.test.js
│   ├── test_blackbox_storage.test.js
│   ├── test_whitebox_validation.test.js
│   ├── test_blackbox_sync.test.js
│   └── setup.js
└── README.md               # Este archivo
```

## Tests del Backend

Ver [tests/backend/README.md](backend/README.md) para más detalles.

**Total**: 86 tests

### Ejecutar (contenedor)
```bash
docker-compose exec web pytest tests/backend/ -v
```

## Tests del Frontend

Ver [tests/frontend/README.md](frontend/README.md) para más detalles.

**Total**: ~66 tests

### Ejecutar (contenedor)
```bash
docker-compose run --rm frontend-tests
```

## Ejecutar todos los tests

```bash
# Backend
docker-compose exec web pytest tests/backend/ -v

# Frontend
docker-compose run --rm frontend-tests

# Ambos
docker-compose exec web pytest tests/backend/ -v && docker-compose run --rm frontend-tests
```

## Ejecutar tests en Docker

### Backend (contenedor principal)

```bash
docker-compose exec web pytest tests/backend/ -v
```

### Frontend (contenedor separado)

```bash
docker-compose run --rm frontend-tests
```

## Notas

- Los tests del backend se ejecutan dentro del contenedor `web`
- Los tests del frontend se ejecutan con el servicio `frontend-tests`
- El Dockerfile principal solo incluye Python (para el backend)
- Para frontend en Docker, usa el servicio `frontend-tests` en `docker-compose`

