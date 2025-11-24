# Enlaces Rápidos a DefectDojo

## Acceso Directo a Findings

### Auditoría de Seguridad CWE-699
- **Engagement (RECOMENDADO)**: [http://localhost/defectdojo/engagement/1/](http://localhost/defectdojo/engagement/1/)
  - Desde aquí puedes ver todos los tests y findings del engagement
  - Muestra el engagement "Auditoría de Seguridad CWE-699" con toda su información

### Rutas Alternativas
- **Test**: [http://localhost/defectdojo/test/1/](http://localhost/defectdojo/test/1/)
- **Findings del test**: [http://localhost/defectdojo/test/1/findings](http://localhost/defectdojo/test/1/findings)
- **Producto**: [http://localhost/defectdojo/product/1/](http://localhost/defectdojo/product/1/)

## Estructura

```
Aplicación Médica (Producto)
└── Auditoría de Seguridad CWE-699 (Engagement)
    └── Revisión de Seguridad - Análisis CWE-699 (Test)
        └── Findings:
            - CWE-20: Validación de entrada (RESUELTO)
            - CWE-1287: Validación de tipo (RESUELTO)
            - CWE-843: Confusión de tipos (RESUELTO)
            - CWE-1021: Clickjacking (RESUELTO)
            - CWE-703: Manejo de excepciones (RESUELTO)
            - CWE-942: CORS permisivo (Aceptado temporalmente)
```

## Recomendación

**Usa la ruta del engagement**: `http://localhost/defectdojo/engagement/1/`

Esta es la ruta más descriptiva porque:
- El engagement se llama "Auditoría de Seguridad CWE-699" (nombre descriptivo)
- Muestra todos los tests y findings del engagement en una sola vista
- Es más fácil de recordar y compartir que `/test/1/findings`

## Nota

DefectDojo usa IDs numéricos en las URLs por defecto. Aunque la URL es `/engagement/1/`, la interfaz muestra el nombre descriptivo "Auditoría de Seguridad CWE-699".

