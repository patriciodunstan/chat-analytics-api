import logging
import time
from typing import Any

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.chat.nl2sql.schemas import SQLQuery, QueryResult

logger = logging.getLogger(__name__)


class QueryExecutor:
    """Executes parameterized SQL queries safely."""

    MAX_ROWS = 1000
    QUERY_TIMEOUT = 30

    async def execute(
            self,
            db: AsyncSession,
            query: SQLQuery
    ) -> QueryResult:
        """Execute a parameterized SQL query."""

        start_time = time.time()
        try:
            logger.info(f"Executing NL2SQL: {query.description}")
            logger.debug(f"SQL: {query.sql}")
            logger.debug(f"Parameters: {query.parameters}")

            result = await db.execute(text(query.sql), query.parameters)
            rows = result.fetchall()
            columns = list(result.keys()) if result.keys() else []

            data = [
                {col: self._serialize_value(row[idx]) for idx, col in enumerate(columns)}
                for row in rows[:self.MAX_ROWS]
            ]

            execution_time = (time.time() - start_time) * 1000
            logger.info(f"Query returned {len(data)} rows in {execution_time:.2f} ms")

            return QueryResult(
                success=True,
                data=data,
                row_count=len(data),
                column_names=columns,
                execution_time_ms=execution_time
            )
        except Exception as e:
            logger.error(f"Error executing query: {e}")
            execution_time = (time.time() - start_time) * 1000
            return QueryResult(
                data=[],
                row_count=0,
                column_names=[],
                success=False,
                error_message=str(e),
                execution_time_ms=execution_time
            )

    def _serialize_value(self, value: Any) -> Any:
        """Serialize value for JSON compatibility."""
        if value is None:
            return None
        if isinstance(value, (int, float, str, bool)):
            return value
        return str(value)
    
    def format_results_for_llm(self, result: QueryResult) -> str:
        """Format query results for LLM consumption."""
        if not result.success:
            return f"Error en la consulta: {result.error_message}"
        if result.row_count == 0:
            return "No se encontraron datos para los criterios especificados."
        lines = []

        if result.column_names:
            lines.append(" | ".join(result.column_names))
            lines.append("-" * len(lines[0]))
        
        for row in result.data[:50]:
            values = []
            for col in result.column_names:
                val = row.get(col, "")
                if isinstance(val, float):
                    val = f"{val:,.2f}" if val != int(val) else f"{int(val):,}"
                elif isinstance(val, int):
                    val = f"{val:,}"
                values.append(str(val) if val is not None else "NULL")
            lines.append(" |".join(values))
        
        if result.row_count > 50:
            lines.append(f"... y {result.row_count - 50} filas más.")
    
        return "\n".join(lines)
    
    def format_results_as_markdown_table(self, result: QueryResult) -> str:
        """Format results as markdown table."""
        if not result.success or result.row_count == 0:
            return self.format_results_for_llm(result)

        lines = []

        lines.append("| " + " | ".join(result.column_names) + " |")
        lines.append("|" + "|".join(["---"] * len(result.column_names)) + "|")

        for row in result.data[:30]:
            values = []
            for col in result.column_names:
                val = row.get(col, "")
                if isinstance(val, float):
                    val = f"{val:,.2f}"
                elif isinstance(val, int):
                    val = f"{val:,}"
                values.append(str(val) if val is not None else "-")
            lines.append("| " + " | ".join(values) + " |")

        if result.row_count > 30:
            lines.append(f"\n*Mostrando 30 de {result.row_count} resultados*")

        return "\n".join(lines)