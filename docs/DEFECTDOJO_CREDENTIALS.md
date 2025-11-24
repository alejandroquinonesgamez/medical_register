# Credenciales de DefectDojo

## Usuario Administrador

El proceso de inicialización crea un usuario **monousuario** para acceder a la consola:

- **Usuario**: `admin`
- **Email**: `admin@example.com`
- **Contraseña inicial**: `admin` (creada automáticamente con `createsuperuser --noinput`)

> ⚠️ **Importante**: Cambia la contraseña en el primer inicio de sesión.

## Actualizar la Contraseña del Administrador

```bash
docker-compose exec defectdojo python manage.py changepassword admin
```

Introduce la nueva contraseña dos veces cuando el comando lo solicite.

## Alternativa: Crear Nuevo Superusuario

Si prefieres registrar otro usuario (por ejemplo, para entornos de pruebas vs. producción) ejecuta:

```bash
docker-compose exec defectdojo python manage.py createsuperuser
```

Te pedirá:
- Username
- Email address
- Password (dos veces)

Para automatizar la creación (útil en CI/CD) puedes usar:

```bash
docker-compose exec defectdojo /bin/sh -c \
  "DJANGO_SUPERUSER_USERNAME=nuevo_admin \
   DJANGO_SUPERUSER_EMAIL=nuevo@ejemplo.com \
   DJANGO_SUPERUSER_PASSWORD=contraseña_segura \
   python manage.py createsuperuser --noinput"
```

## Acceso Inicial

1. Abre DefectDojo en http://localhost/defectdojo/
2. Inicia sesión con `admin / admin` (o las credenciales que hayas configurado)
3. Cambia la contraseña inmediatamente desde la interfaz o con `changepassword`

## Nota sobre las Credenciales del docker-compose.yml

Las credenciales en `docker-compose.yml` (`defectdojo_password`) son **SOLO para la base de datos PostgreSQL**, NO para acceder a la interfaz web de DefectDojo.

Las credenciales de la interfaz web son independientes y se crean durante la inicialización de DefectDojo.

