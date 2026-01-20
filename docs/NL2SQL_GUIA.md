# Guía de Implementación NL2SQL

## Índice de Documentos

1. [01_ESTRUCTURA.md](./01_ESTRUCTURA.md) - Estructura de archivos y directorios
2. [02_SCHEMAS.md](./02_SCHEMAS.md) - Modelos Pydantic (schemas.py, exceptions.py)
3. [03_PROMPTS.md](./03_PROMPTS.md) - Prompts para Gemini
4. [04_DETECTOR.md](./04_DETECTOR.md) - Detector de queries
5. [05_SCHEMA_DISCOVERY.md](./05_SCHEMA_DISCOVERY.md) - Descubrimiento de esquema DB
6. [06_PARSER_GENERATOR.md](./06_PARSER_GENERATOR.md) - Parser de intención y generador SQL
7. [07_EXECUTOR.md](./07_EXECUTOR.md) - Ejecutor de queries
8. [08_INTEGRACION.md](./08_INTEGRACION.md) - Integración en chat/service.py
9. [09_MODELOS_SEED.md](./09_MODELOS_SEED.md) - Modelos de datos y seeds
10. [10_TESTS.md](./10_TESTS.md) - Tests y verificación

---

## Resumen del Proyecto

**Objetivo**: NL2SQL genérico que descubre automáticamente el esquema de cualquier PostgreSQL.

**Datasets de demo**:
- Equipment + Maintenance/Failure events (minería)
- Support Tickets (customer service)

**Flujo**:
```
Usuario pregunta → Detectar si es query → Descubrir esquema DB
→ Parsear intención → Generar SQL seguro → Ejecutar → Responder
```

---

## Orden de Implementación

```
1. Crear carpeta app/chat/nl2sql/
2. Crear schemas.py + exceptions.py
3. Crear prompts.py
4. Crear detector.py
5. Crear schema_discovery.py
6. Crear intent_parser.py
7. Crear sql_generator.py
8. Crear query_executor.py
9. Crear __init__.py
10. Modificar app/chat/service.py
11. Agregar modelos a app/db/models.py
12. Crear y ejecutar seeds
13. Tests
```