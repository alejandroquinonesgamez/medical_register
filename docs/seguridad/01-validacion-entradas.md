# Validación y sanitización de entradas

- **Nombres y apellidos**: validación de longitud y caracteres permitidos (solo letras, espacios, guiones y apóstrofes). Se eliminan caracteres peligrosos y se normalizan espacios. Implementado en `app/helpers.py` (`validate_and_sanitize_name`).
- **Peso, altura y fecha de nacimiento**: validación de tipo y rango en backend (`/api/user`, `/api/weight`) con límites centralizados en `app/config.py`.
- **Validación defensiva**: cálculo de IMC solo si los datos están dentro de rango (backend y frontend).

[← Índice de seguridad](../SEGURIDAD.md)
