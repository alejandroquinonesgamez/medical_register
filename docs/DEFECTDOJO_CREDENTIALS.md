# Credenciales de DefectDojo

## Usuario Administrador

Se ha creado automáticamente un usuario administrador durante la inicialización:

- **Usuario**: `admin`
- **Email**: `admin@localhost`
- **Contraseña**: Se debe establecer manualmente (ver abajo)

## Establecer Contraseña del Administrador

Para establecer la contraseña del usuario `admin`, ejecuta:

```bash
docker-compose exec defectdojo python manage.py changepassword admin
```

Te pedirá que ingreses la nueva contraseña dos veces.

## Alternativa: Crear Nuevo Superusuario

Si prefieres crear un nuevo usuario administrador:

```bash
docker-compose exec defectdojo python manage.py createsuperuser
```

Te pedirá:
- Username
- Email address
- Password (dos veces)

## Acceso Inicial

1. Abre DefectDojo en http://localhost:8080
2. Inicia sesión con el usuario `admin` y la contraseña que hayas configurado
3. Después del primer acceso, cambia la contraseña por razones de seguridad

## Nota sobre las Credenciales del docker-compose.yml

Las credenciales en `docker-compose.yml` (`defectdojo_password`) son **SOLO para la base de datos PostgreSQL**, NO para acceder a la interfaz web de DefectDojo.

Las credenciales de la interfaz web son independientes y se crean durante la inicialización de DefectDojo.

