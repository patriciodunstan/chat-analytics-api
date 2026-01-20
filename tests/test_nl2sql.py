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

    def test_multiple_unrelated_tables_falls_back_to_first(self):
        """Test that unrelated tables fall back to using only the first table."""
        # Schema con tablas sin relación directa
        schema = DatabaseSchema(tables=[
            TableInfo(
                name="support_tickets",
                columns=[
                    ColumnInfo(name="id", data_type="integer", is_primary_key=True),
                    ColumnInfo(name="ticket_subject", data_type="varchar"),
                    ColumnInfo(name="ticket_status", data_type="varchar"),
                ],
                row_count=8000,
            ),
            TableInfo(
                name="failure_events",
                columns=[
                    ColumnInfo(name="id", data_type="integer", is_primary_key=True),
                    ColumnInfo(name="equipment_id", data_type="varchar", is_foreign_key=True,
                              foreign_table="equipment", foreign_column="equipment_id"),
                    ColumnInfo(name="descripcion_falla", data_type="text"),
                ],
                row_count=3000,
            ),
        ])

        # Intent con múltiples tablas no relacionadas
        intent = ParsedIntent(
            tables=["support_tickets", "failure_events"],
            aggregations=[{"func": "COUNT", "column": "*", "alias": "total"}],
        )

        result = self.generator.generate(intent, schema)

        # Debería generar SQL válido sin JOINs inválidos
        assert "SELECT" in result.sql
        assert "support_tickets" in result.sql
        # No debería tener JOIN inválido
        assert "LEFT JOIN" not in result.sql or result.sql.count("LEFT JOIN") == 0

    def test_tables_with_common_parent_auto_joins(self):
        """Test that tables with a common parent table get auto-joined."""
        schema = DatabaseSchema(tables=[
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
                ],
                row_count=3000,
            ),
            TableInfo(
                name="maintenance_events",
                columns=[
                    ColumnInfo(name="id", data_type="integer", is_primary_key=True),
                    ColumnInfo(name="equipment_id", data_type="varchar", is_foreign_key=True,
                              foreign_table="equipment", foreign_column="equipment_id"),
                    ColumnInfo(name="tipo_intervencion", data_type="varchar"),
                ],
                row_count=5000,
            ),
        ])

        # Intent con tablas que comparten un padre común (equipment)
        intent = ParsedIntent(
            tables=["failure_events", "maintenance_events"],
            select_columns=["failure_events.descripcion_falla", "maintenance_events.tipo_intervencion"],
        )

        result = self.generator.generate(intent, schema)

        # Debería generar JOINs válidos a través de equipment
        assert "SELECT" in result.sql
        assert "LEFT JOIN" in result.sql
        assert "equipment" in result.sql

    def test_three_tables_with_intermediate_parent(self):
        """Test JOIN generation with 3 tables where parent acts as intermediate."""
        schema = DatabaseSchema(tables=[
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
            TableInfo(
                name="maintenance_events",
                columns=[
                    ColumnInfo(name="id", data_type="integer", is_primary_key=True),
                    ColumnInfo(name="equipment_id", data_type="varchar", is_foreign_key=True,
                              foreign_table="equipment", foreign_column="equipment_id"),
                    ColumnInfo(name="tipo_intervencion", data_type="varchar"),
                    ColumnInfo(name="costo_total", data_type="numeric"),
                ],
                row_count=5000,
            ),
        ])

        # Intent con 3 tablas: failure_events, equipment, maintenance_events
        # equipment está explícitamente en la lista
        intent = ParsedIntent(
            tables=["failure_events", "equipment", "maintenance_events"],
            select_columns=["equipment.tipo_maquina", "failure_events.descripcion_falla", "maintenance_events.tipo_intervencion"],
        )

        result = self.generator.generate(intent, schema)

        # Verificar SQL válido - debe tener 2 LEFT JOINs
        assert "SELECT" in result.sql
        assert "LEFT JOIN" in result.sql
        assert result.sql.count("LEFT JOIN") == 2

        # Verificar que las 3 tablas están en el SQL
        assert '"failure_events"' in result.sql
        assert '"equipment"' in result.sql
        assert '"maintenance_events"' in result.sql

        # Verificar que los JOINs son válidos (no referencian tablas inexistentes)
        # El SQL debe ser algo como:
        # FROM "failure_events"
        # LEFT JOIN "equipment" ON "equipment"."equipment_id" = "failure_events"."equipment_id"
        # LEFT JOIN "maintenance_events" ON "equipment"."equipment_id" = "maintenance_events"."equipment_id"
        assert "ON" in result.sql
        # Verificar que no hay errores de sintaxis comunes
        assert not result.sql.endswith("JOIN")
        assert not result.sql.endswith("ON")

    def test_three_tables_implicit_parent(self):
        """Test JOIN with 3 tables where parent is NOT in the original list."""
        schema = DatabaseSchema(tables=[
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
                ],
                row_count=3000,
            ),
            TableInfo(
                name="maintenance_events",
                columns=[
                    ColumnInfo(name="id", data_type="integer", is_primary_key=True),
                    ColumnInfo(name="equipment_id", data_type="varchar", is_foreign_key=True,
                              foreign_table="equipment", foreign_column="equipment_id"),
                    ColumnInfo(name="tipo_intervencion", data_type="varchar"),
                ],
                row_count=5000,
            ),
        ])

        # Solo failure_events y maintenance_events, equipment NO está en la lista
        intent = ParsedIntent(
            tables=["failure_events", "maintenance_events"],
            select_columns=["failure_events.descripcion_falla", "maintenance_events.tipo_intervencion"],
        )

        result = self.generator.generate(intent, schema)

        # Debería agregar automáticamente equipment como intermediaria
        assert "SELECT" in result.sql
        assert "LEFT JOIN" in result.sql
        assert '"equipment"' in result.sql
        # Debe haber 2 JOINs (failure -> equipment, maintenance -> equipment)
        assert result.sql.count("LEFT JOIN") == 2


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