# 01 - Estructura de Archivos

## Crear Carpetas

```powershell
mkdir "app\chat\nl2sql"
mkdir "scripts"
mkdir "docs"
```

## Estructura Final

```
app/
├── chat/
│   ├── nl2sql/                    # NUEVO
│   │   ├── __init__.py
│   │   ├── schemas.py
│   │   ├── exceptions.py
│   │   ├── prompts.py
│   │   ├── detector.py
│   │   ├── schema_discovery.py
│   │   ├── intent_parser.py
│   │   ├── sql_generator.py
│   │   └── query_executor.py
│   ├── llm/
│   │   └── gemini_client.py       # SIN CAMBIOS
│   ├── router.py                  # SIN CAMBIOS
│   ├── service.py                 # MODIFICAR
│   └── schemas.py                 # SIN CAMBIOS
├── db/
│   ├── models.py                  # MODIFICAR (agregar modelos)
│   └── ...
scripts/
├── seed_equipment.sql             # NUEVO
└── seed_tickets.py                # NUEVO
docs/
└── *.md                           # Documentación
```

## Archivos a Crear (en orden)

| # | Archivo | Descripción |
|---|---------|-------------|
| 1 | `app/chat/nl2sql/schemas.py` | Modelos Pydantic |
| 2 | `app/chat/nl2sql/exceptions.py` | Excepciones |
| 3 | `app/chat/nl2sql/prompts.py` | Prompts Gemini |
| 4 | `app/chat/nl2sql/detector.py` | Detecta si es query |
| 5 | `app/chat/nl2sql/schema_discovery.py` | Descubre esquema DB |
| 6 | `app/chat/nl2sql/intent_parser.py` | Parsea intención |
| 7 | `app/chat/nl2sql/sql_generator.py` | Genera SQL seguro |
| 8 | `app/chat/nl2sql/query_executor.py` | Ejecuta queries |
| 9 | `app/chat/nl2sql/__init__.py` | Exports |

## Archivos a Modificar

| Archivo | Cambio |
|---------|--------|
| `app/chat/service.py` | Agregar lógica NL2SQL |
| `app/db/models.py` | Agregar Equipment, Tickets |
