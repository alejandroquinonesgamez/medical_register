# Directorio de Datos Persistentes

Este directorio contiene datos locales usados por la aplicación en producción.

## Contenido esperado

```
data/
├── common_passwords_fallback.txt  # Lista local de contraseñas comunes (fallback HIBP)
└── app_secure.db                  # Base de datos SQLCipher si se habilita
```

## Importante

- **`common_passwords_fallback.txt`** está versionado y se usa como fallback si HIBP no responde.
- La base de datos `app_secure.db` se crea automáticamente cuando se activa SQLCipher.
- Los datos locales están pensados para producción y no dependen de DefectDojo.



