import logging
import re
from typing import Any



from app.chat.nl2sql.schemas import ParsedIntent, SQLQuery, DatabaseSchema
from app.chat.nl2sql.exceptions import SQLGenerationError

logger = logging.getLogger(__name__)

class SQLGenerator:
    """Generates safe parameterized SQL from parsed intent."""

    ALLOWED_OPERATIONS = {
        '=', '!=', '<>', '>', '<', '>=', '<=',
        'LIKE', 'ILIKE', 'IN', 'NOT IN',
        'IS NULL', 'IS NOT NULL', 'BETWEEN', 
    }

    ALLOWED_AGGREGATIONS = {
        'COUNT', 'SUM', 'AVG', 'MIN', 'MAX', 'COUNT DISTINCT'
    }

    def generate(self, intent: ParsedIntent, schema: DatabaseSchema) -> SQLQuery:
        """Generate parameterized SQL from intent."""
        try:
            params: dict[str, Any] = {}
            param_counter = [0]

            def next_param(prefix: str = "p") -> str:
                param_counter[0] += 1
                return f"{prefix}_{param_counter[0]}"

            select_clause = self._build_select(intent)
            from_clause = self._build_from(intent, schema)
            where_clause, where_params = self._build_where(intent, next_param)
            params.update(where_params)
            group_clause = self._build_group_by(intent)
            order_clause = self._build_order_by(intent)

            limit_clause = ""
            if intent.limit:
                limit_clause = f"LIMIT :limit"
                params["limit"] = intent.limit

            sql_parts = [f"SELECT {select_clause}", f"FROM {from_clause}"]
            if where_clause:
                sql_parts.append(f"WHERE {where_clause}")
            if group_clause:
                sql_parts.append(f"GROUP BY {group_clause}")
            if order_clause:
                sql_parts.append(f"ORDER BY {order_clause}")
            if limit_clause:
                sql_parts.append(limit_clause)

            sql = "\n".join(sql_parts)
            description = self._generate_description(intent)

            return SQLQuery(
                sql=sql,
                parameters=params,
                description=description,
                tables_used=intent.tables,
            )

        except Exception as e:
            raise SQLGenerationError(f"Failed to generate SQL: {e}")

    def _build_select(self, intent: ParsedIntent) -> str:
        """Build SELECT clause."""
        parts = []

        for col in intent.select_columns:
            safe_col = self._sanitize_identifier(col)
            parts.append(f'"{safe_col}"')

        for agg in intent.aggregations:
            func = agg.get("func", "COUNT").upper()
            col = agg.get("column", "*")
            alias = agg.get("alias", f"{func.lower()}_{col}")

            if func not in self.ALLOWED_AGGREGATIONS:
                continue

            if col == "*":
                parts.append(f'{func}(*) AS "{alias}"')
            else:
                safe_col = self._sanitize_identifier(col)
                parts.append(f'{func}("{safe_col}") AS "{alias}"')

        if not parts:
            parts.append("*")

        return ", ".join(parts)
    def _build_from(self, intent: ParsedIntent, schema: DatabaseSchema) -> str:
        """Build FROM clause with JOINs."""
        if not intent.tables:
            raise SQLGenerationError("No tables specified in intent.")

        main_table = self._sanitize_identifier(intent.tables[0])
        from_parts = [f'"{main_table}"']

        # Procesar joins explícitos del intent
        for join in intent.joins:
            t1 = self._sanitize_identifier(join.get("table1", ""))
            c1 = self._sanitize_identifier(join.get("col1", ""))
            t2 = self._sanitize_identifier(join.get("table2", ""))
            c2 = self._sanitize_identifier(join.get("col2", ""))

            if t2 and c1 and c2:
                from_parts.append(f'LEFT JOIN "{t2}" ON "{t1}"."{c1}" = "{t2}"."{c2}"')

        # Auto-detectar joins cuando hay múltiples tablas sin joins explícitos
        if len(intent.tables) > 1 and not intent.joins:
            join_builder = self._auto_detect_joins(intent.tables, schema)
            if join_builder:
                from_parts.append(join_builder)
            elif len(intent.tables) > 1:
                # Si no se pueden unir las tablas, advertir y usar solo la primera
                logger.warning(
                    f"Multiple tables ({intent.tables}) specified but no valid JOIN found. "
                    f"Using only first table: {intent.tables[0]}"
                )

        return " ".join(from_parts)

    def _auto_detect_joins(self, tables: list[str], schema: DatabaseSchema) -> str:
        """
        Auto-detect y construye JOINs para múltiples tablas en orden correcto.

        Construye los JOINs iterativamente, asegurando que cada tabla se una
        solo a tablas ya incluidas en la consulta. Maneja:
        1. FK directa entre tablas en la lista
        2. FK común a una tabla padre (ej: ambos apuntan a 'equipment')
        3. Tablas intermedias no incluidas en la lista original
        """
        if len(tables) < 2:
            return ""

        join_parts = []
        # Tablas ya incluidas en la consulta FROM/JOIN
        included_tables = {tables[0]}
        # Tablas pendientes de unir
        pending_tables = set(tables[1:])
        # Tablas adicionales que se agregaron como intermediarias
        extra_tables: set[str] = set()

        max_iterations = len(tables) + 5  # Límite para evitar loops infinitos
        iteration = 0

        while pending_tables and iteration < max_iterations:
            iteration += 1
            joined_this_iteration = False

            # Intentar unir cada tabla pendiente
            for table_name in list(pending_tables):
                join_sql = self._find_join_path(
                    table_name, included_tables | extra_tables, schema
                )
                if join_sql:
                    join_parts.append(join_sql.sql)
                    # Actualizar conjuntos de tablas
                    included_tables.add(table_name)
                    pending_tables.remove(table_name)
                    # Agregar tablas intermediarias si las hubo
                    if join_sql.intermediate_tables:
                        extra_tables.update(join_sql.intermediate_tables)
                        included_tables.update(join_sql.intermediate_tables)
                    joined_this_iteration = True
                    break

            if not joined_this_iteration:
                # No se pudo unir más tablas
                if pending_tables:
                    logger.warning(
                        f"Could not join tables: {pending_tables}. "
                        f"No valid join path to included tables: {included_tables}"
                    )
                break

        return " ".join(join_parts)

    def _find_join_path(
        self, target_table: str, valid_sources: set[str], schema: DatabaseSchema
    ) -> "_JoinSQL | None":
        """
        Encuentra cómo unir target_table a alguna tabla en valid_sources.

        Retorna un objeto _JoinSQL con el SQL del JOIN y las tablas intermediarias
        que se necesitan agregar. Busca en orden:
        1. FK directa a una tabla en valid_sources
        2. Tabla padre común que sirva de intermediario
        """
        target_info = schema.get_table(target_table)
        if not target_info:
            return None

        target_safe = self._sanitize_identifier(target_table)

        # Caso 1: FK directa a una tabla en valid_sources
        for col in target_info.columns:
            if col.is_foreign_key and col.foreign_table in valid_sources:
                source_safe = self._sanitize_identifier(col.foreign_table)
                fk_col = self._sanitize_identifier(col.foreign_column or "id")
                local_col = self._sanitize_identifier(col.name)

                return _JoinSQL(
                    sql=f'LEFT JOIN "{target_safe}" ON "{source_safe}"."{fk_col}" = "{target_safe}"."{local_col}"',
                    intermediate_tables=set(),
                )

        # Caso 2: Buscar tabla padre común que sirva de intermediario
        for source_table in valid_sources:
            source_info = schema.get_table(source_table)
            if not source_info:
                continue

            common_parent = self._find_common_parent_sorted(source_table, target_table, schema)
            if common_parent:
                parent_safe = self._sanitize_identifier(common_parent)
                join_parts = []
                extra_tables: set[str] = set()

                # Si el padre no está en valid_sources, hay que agregarlo primero
                if common_parent not in valid_sources:
                    # Unir source al padre
                    source_join = self._create_join_to_parent(source_table, common_parent, schema)
                    if source_join:
                        join_parts.append(source_join)
                        extra_tables.add(common_parent)
                    else:
                        continue  # No se pudo unir source al padre

                # Unir target al padre
                target_join = self._create_join_to_parent(target_table, common_parent, schema)
                if target_join:
                    join_parts.append(target_join)
                    return _JoinSQL(
                        sql=" ".join(join_parts),
                        intermediate_tables=extra_tables,
                    )

        return None

    def _create_join_to_parent(
        self, child_table: str, parent_table: str, schema: DatabaseSchema
    ) -> str | None:
        """
        Crea la cláusula JOIN para unir child_table a parent_table a través de su FK.
        """
        child_info = schema.get_table(child_table)
        if not child_info:
            return None

        child_safe = self._sanitize_identifier(child_table)
        parent_safe = self._sanitize_identifier(parent_table)

        for col in child_info.columns:
            if col.is_foreign_key and col.foreign_table == parent_table:
                fk_col = self._sanitize_identifier(col.foreign_column or "id")
                local_col = self._sanitize_identifier(col.name)
                return f'LEFT JOIN "{child_safe}" ON "{parent_safe}"."{fk_col}" = "{child_safe}"."{local_col}"'

        return None

    def _find_common_parent(
        self, table1: str, table2: str, schema: DatabaseSchema
    ) -> str | None:
        """
        Encuentra una tabla padre común a través de FKs.
        Nota: Usa .pop() que es no-determinista. Preferir _find_common_parent_sorted.
        """
        t1_info = schema.get_table(table1)
        t2_info = schema.get_table(table2)

        if not t1_info or not t2_info:
            return None

        t1_parents = {
            col.foreign_table for col in t1_info.columns
            if col.is_foreign_key and col.foreign_table
        }
        t2_parents = {
            col.foreign_table for col in t2_info.columns
            if col.is_foreign_key and col.foreign_table
        }

        common = t1_parents & t2_parents
        return common.pop() if common else None

    def _find_common_parent_sorted(
        self, table1: str, table2: str, schema: DatabaseSchema
    ) -> str | None:
        """
        Encuentra una tabla padre común de forma determinista.
        Retorna la primer tabla padre ordenada alfabéticamente.
        """
        t1_info = schema.get_table(table1)
        t2_info = schema.get_table(table2)

        if not t1_info or not t2_info:
            return None

        t1_parents = {
            col.foreign_table for col in t1_info.columns
            if col.is_foreign_key and col.foreign_table
        }
        t2_parents = {
            col.foreign_table for col in t2_info.columns
            if col.is_foreign_key and col.foreign_table
        }

        common = t1_parents & t2_parents
        if not common:
            return None

        # Retornar la primera tabla padre ordenada alfabéticamente (determinista)
        return min(common)

    def _build_where(
            self,
            intent: ParsedIntent,
            next_param: Any,
    ) -> tuple[str, dict]:
        """Build WHERE clause with parameters."""
        conditions = []
        params = {}

        for f in intent.filters:
            col = self._sanitize_identifier(f.get("column", ""))
            op = f.get("operator", "=").upper()
            value = f.get("value")

            if not col or op not in self.ALLOWED_OPERATIONS:
                continue

            if op in ("IS NULL", "IS NOT NULL"):
                conditions.append(f'"{col}" {op}')
            elif op == "IN" and isinstance(value, list):
                placeholders = []
                for v in value:
                    pname = next_param("in")
                    params[pname] = v
                    placeholders.append(f": {pname}")
                conditions.append(f'"{col}" IN ({", ".join(placeholders)})')
            elif op in ("LIKE", "ILIKE"):
                pname = next_param("like")
                params[pname] = value
                conditions.append(f'"{col}" {op} {pname}')
            else:
                pname = next_param("f")
                params[pname] = value
                conditions.append(f'"{col}" {op} {pname}')
        
        if intent.date_range:
            date_col = self._sanitize_identifier(getattr(intent.date_range, "column", ""))
            if date_col:
                if intent.date_range.start_date:
                    params["date_start"] = intent.date_range.start_date
                    conditions.append(f'"{date_col}" >= :date_start')
                if intent.date_range.end_date:
                    params["date_end"] = intent.date_range.end_date
                    conditions.append(f'"{date_col}" <= :date_end')

        return " AND ".join(conditions), params

    def _build_group_by(self, intent: ParsedIntent) -> str:
        """Build GROUP BY clause."""
        if not intent.group_by:
            return ""
        safe_cols = [f'"{self._sanitize_identifier(c)}"' for c in intent.group_by]
        return ", ".join(safe_cols)

    def _build_order_by(self, intent: ParsedIntent) -> str:
        """Build ORDER BY clause."""
        if not intent.order_by:
            return ""
        parts = []
        for o in intent.order_by:
            col = self._sanitize_identifier(o.get("column", ""))
            direction = o.get("direction", "DESC").upper()
            if direction not in ("ASC", "DESC"):
                direction = "DESC"
            parts.append(f'"{col}" {direction}')
        return ", ".join(parts)

    
    def _sanitize_identifier(self, name: str) -> str:
        """Sanitize SQL identifier to prevent injection."""
        return re.sub(r'[^a-zA-Z0-9_]', '', name)


    def _find_date_column(
            self,
            intent: ParsedIntent,
    ) -> str:
        """Find a date column name from the intent."""
        date_patterns = ['fecha','date','created_at','updated_at','timestamp','time']
        for col in intent.select_columns + intent.group_by:
            for pattern in date_patterns:
                if pattern in col.lower():
                    return col
        return "fecha"
    
    def _generate_description(self, intent: ParsedIntent) -> str:
        """Generate human-readable description of the query."""
        parts = []
        if intent.aggregations:
            agg_desc = ", ".join(f"{a['func']}({a.get('column', '*')})" for a in intent.aggregations)
            parts.append(f"Calculando: {agg_desc}")
        parts.append(f"De tablas: {', '.join(intent.tables)}")
        if intent.filters:
            filter_desc = ", ".join(f"{f['column']} {f['operator']} {f['value']}" for f in intent.filters)
            parts.append(f"Filtrado por: {filter_desc}")
        if intent.group_by:
            parts.append(f"Agrupado por: {', '.join(intent.group_by)}")
        if intent.date_range and intent.date_range.period_description:
            parts.append(f"Período: {intent.date_range.period_description}")
        return " | ".join(parts)


class _JoinSQL:
    """Resultado de _find_join_path con el SQL y tablas intermediarias."""
    def __init__(self, sql: str, intermediate_tables: set[str]):
        self.sql = sql
        self.intermediate_tables = intermediate_tables