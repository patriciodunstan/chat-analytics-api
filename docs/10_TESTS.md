# 10 - Tests y Verificación

## Archivo: `tests/test_nl2sql.py`

```python
"""Tests for NL2SQL module."""
import pytest
from unittest.mock import AsyncMock, patch

from app.chat.nl2sql.detector import QueryDetector
from app.chat.nl2sql.schemas import (
    DatabaseSchema, TableInfo, ColumnInfo,
    ParsedIntent, SQLQuery, QueryResult,
)
from app.chat.nl2sql.sql_generator import SQLGenerator
from app.chat.nl2sql.query_executor import QueryExecutor


class TestQueryDetector:
    """Tests for QueryDetector."""

    def setup_method(self):
        self.detector = QueryDetector()

    def test_heuristic_detects_data_query_spanish(self):
        """Test heuristic detection of data queries in Spanish."""
        test_cases = [
            ("¿Cuántos tickets abiertos hay?", True),
            ("Muéstrame el total de costos por categoría", True),
            ("¿Cuál es el equipo con más fallas?", True),
            ("Compara los gastos de Marketing vs Development", True),
        ]

        for message, expected in test_cases:
            is_data, confidence, _ = self.detector._heuristic_check(message)
            assert is_data == expected, f"Failed for: {message}"

    def test_heuristic_detects_chat(self):
        """Test heuristic detection of chat messages."""
        test_cases = [
            ("Hola, ¿cómo estás?", False),
            ("Gracias por tu ayuda", False),
            ("¿Qué puedes hacer?", False),
        ]

        for message, expected in test_cases:
            is_data, confidence, _ = self.detector._heuristic_check(message)
            assert is_data == expected, f"Failed for: {message}"


class TestSQLGenerator:
    """Tests for SQLGenerator."""

    def setup_method(self):
        self.generator = SQLGenerator()
        self.schema = DatabaseSchema(tables=[
            TableInfo(
                name="equipment",
                columns=[
                    ColumnInfo(name="id", data_type="integer", is_primary_key=True),
                    ColumnInfo(name="equipment_id", data_type="varchar"),
                    ColumnInfo(name="tipo_maquina", data_type="varchar"),
                ],
                row_count=50,
            ),
            TableInfo(
                name="failure_events",
                columns=[
                    ColumnInfo(name="id", data_type="integer", is_primary_key=True),
                    ColumnInfo(name="equipment_id", data_type="varchar", is_foreign_key=True,
                              foreign_table="equipment", foreign_column="equipment_id"),
                    ColumnInfo(name="descripcion_falla", data_type="text"),
                    ColumnInfo(name="costo_total", data_type="numeric"),
                ],
                row_count=3000,
            ),
        ])

    def test_generate_count_query(self):
        """Test COUNT query generation."""
        intent = ParsedIntent(
            tables=["failure_events"],
            aggregations=[{"func": "COUNT", "column": "*", "alias": "total"}],
        )

        result = self.generator.generate(intent, self.schema)

        assert "SELECT" in result.sql
        assert "COUNT(*)" in result.sql
        assert "failure_events" in result.sql

    def test_sql_injection_prevention(self):
        """Test that SQL injection is prevented."""
        intent = ParsedIntent(
            tables=["failure_events"],
            filters=[{
                "column": "descripcion_falla",
                "operator": "=",
                "value": "'; DROP TABLE failure_events; --"
            }],
        )

        result = self.generator.generate(intent, self.schema)

        assert "DROP TABLE" not in result.sql
        assert "'; DROP TABLE failure_events; --" in list(result.parameters.values())


class TestQueryExecutor:
    """Tests for QueryExecutor."""

    def setup_method(self):
        self.executor = QueryExecutor()

    def test_format_results_empty(self):
        """Test formatting empty results."""
        result = QueryResult(success=True, data=[], row_count=0, column_names=[])
        formatted = self.executor.format_results_for_llm(result)
        assert "No se encontraron datos" in formatted

    def test_format_results_with_data(self):
        """Test formatting results with data."""
        result = QueryResult(
            success=True,
            data=[
                {"tipo_maquina": "Excavadora", "total": 15000.50},
                {"tipo_maquina": "Cargador", "total": 8000.25},
            ],
            row_count=2,
            column_names=["tipo_maquina", "total"],
        )

        formatted = self.executor.format_results_for_llm(result)

        assert "tipo_maquina" in formatted
        assert "Excavadora" in formatted
```

---

## Verificación Manual

### 1. Verificar estructura de archivos

```powershell
Get-ChildItem -Path "app\chat\nl2sql" -Recurse
```

Debe mostrar:
```
__init__.py
schemas.py
exceptions.py
prompts.py
detector.py
schema_discovery.py
intent_parser.py
sql_generator.py
query_executor.py
```

### 2. Ejecutar tests

```bash
# Tests de NL2SQL
pytest tests/test_nl2sql.py -v

# Tests de chat (verificar que no se rompieron)
pytest tests/test_chat.py -v

# Todos los tests
pytest -v
```

### 3. Probar manualmente

```bash
# Iniciar servidor
uvicorn app.main:app --reload
```

### 4. Mensajes de prueba

**Equipos/Mantenimiento:**
```
"¿Cuántos equipos hay por tipo de máquina?"
"¿Cuál es el costo total de mantenimiento en 2023?"
"Muéstrame los equipos con más fallas"
"¿Cuál es la causa de falla más común?"
```

**Tickets de soporte:**
```
"¿Cuántos tickets abiertos hay por prioridad?"
"¿Cuál es el tiempo promedio de resolución?"
"¿Qué productos generan más tickets?"
"Muéstrame tickets críticos sin resolver"
```

**Chat normal (debe funcionar como antes):**
```
"Hola, ¿cómo estás?"
"¿Qué puedes hacer?"
"Gracias por tu ayuda"
```

---

## Checklist Final

- [ ] Crear carpeta `app/chat/nl2sql/`
- [ ] Crear `exceptions.py`
- [ ] Crear `schemas.py`
- [ ] Crear `prompts.py`
- [ ] Crear `detector.py`
- [ ] Crear `schema_discovery.py`
- [ ] Crear `intent_parser.py`
- [ ] Crear `sql_generator.py`
- [ ] Crear `query_executor.py`
- [ ] Crear `__init__.py`
- [ ] Agregar modelos a `app/db/models.py`
- [ ] Crear `scripts/seed_equipment.sql`
- [ ] Crear `scripts/seed_tickets.py`
- [ ] Reemplazar `app/chat/service.py`
- [ ] Crear `tests/test_nl2sql.py`
- [ ] Ejecutar seeds de datos
- [ ] Ejecutar tests
- [ ] Probar manualmente

---

## Archivos a eliminar (opcional)

| Archivo | Razón |
|---------|-------|
| `app/db/seed.py` | Reemplazado por scripts separados |

## Siguiente Paso

Una vez implementado NL2SQL, las siguientes mejoras serían:

1. **Detección de anomalías** - Alertas automáticas
2. **Predicciones** - Proyecciones de costos/fallas
3. **Multi-tenancy** - Segregación de datos por cliente
