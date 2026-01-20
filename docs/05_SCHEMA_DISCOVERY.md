# 05 - Schema Discovery

## Archivo: `app/chat/nl2sql/schema_discovery.py`

```python
"""Schema discovery - automatic database introspection."""
import logging
from datetime import datetime, timedelta
from typing import Optional

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.chat.nl2sql.schemas import DatabaseSchema, TableInfo, ColumnInfo
from app.chat.nl2sql.exceptions import SchemaDiscoveryError

logger = logging.getLogger(__name__)


class SchemaDiscovery:
    """Discovers database schema automatically."""

    _cache: dict[str, tuple[DatabaseSchema, datetime]] = {}
    _cache_ttl: int = 3600  # 1 hora

    SYSTEM_TABLES = {"alembic_version", "pg_stat_statements", "spatial_ref_sys"}
    APP_INTERNAL_TABLES = {"users", "conversations", "messages", "reports"}

    def __init__(self, include_internal_tables: bool = False):
        self.include_internal_tables = include_internal_tables

    async def discover(
        self,
        db: AsyncSession,
        force_refresh: bool = False
    ) -> DatabaseSchema:
        """Discover database schema with caching."""
        cache_key = "default"

        if not force_refresh and cache_key in self._cache:
            schema, cached_at = self._cache[cache_key]
            if datetime.utcnow() - cached_at < timedelta(seconds=self._cache_ttl):
                logger.debug("Using cached schema")
                return schema

        try:
            schema = await self._discover_schema(db)
            self._cache[cache_key] = (schema, datetime.utcnow())
            return schema
        except Exception as e:
            raise SchemaDiscoveryError(f"Failed to discover schema: {e}")

    async def _discover_schema(self, db: AsyncSession) -> DatabaseSchema:
        """Perform actual schema discovery."""
        tables = []

        tables_query = """
            SELECT
                t.table_name,
                c.column_name,
                c.data_type,
                c.is_nullable,
                CASE WHEN pk.column_name IS NOT NULL THEN true ELSE false END as is_pk,
                fk.foreign_table_name,
                fk.foreign_column_name
            FROM information_schema.tables t
            JOIN information_schema.columns c
                ON t.table_name = c.table_name AND t.table_schema = c.table_schema
            LEFT JOIN (
                SELECT ku.table_name, ku.column_name
                FROM information_schema.table_constraints tc
                JOIN information_schema.key_column_usage ku
                    ON tc.constraint_name = ku.constraint_name
                WHERE tc.constraint_type = 'PRIMARY KEY'
            ) pk ON c.table_name = pk.table_name AND c.column_name = pk.column_name
            LEFT JOIN (
                SELECT
                    kcu.table_name,
                    kcu.column_name,
                    ccu.table_name AS foreign_table_name,
                    ccu.column_name AS foreign_column_name
                FROM information_schema.table_constraints tc
                JOIN information_schema.key_column_usage kcu
                    ON tc.constraint_name = kcu.constraint_name
                JOIN information_schema.constraint_column_usage ccu
                    ON tc.constraint_name = ccu.constraint_name
                WHERE tc.constraint_type = 'FOREIGN KEY'
            ) fk ON c.table_name = fk.table_name AND c.column_name = fk.column_name
            WHERE t.table_schema = 'public' AND t.table_type = 'BASE TABLE'
            ORDER BY t.table_name, c.ordinal_position
        """

        result = await db.execute(text(tables_query))
        rows = result.fetchall()

        current_table: Optional[str] = None
        current_columns: list[ColumnInfo] = []

        for row in rows:
            table_name = row[0]

            if table_name in self.SYSTEM_TABLES:
                continue
            if not self.include_internal_tables and table_name in self.APP_INTERNAL_TABLES:
                continue

            if table_name != current_table:
                if current_table is not None:
                    tables.append(TableInfo(name=current_table, columns=current_columns))
                current_table = table_name
                current_columns = []

            current_columns.append(ColumnInfo(
                name=row[1],
                data_type=row[2],
                is_nullable=row[3] == 'YES',
                is_primary_key=row[4],
                is_foreign_key=row[5] is not None,
                foreign_table=row[5],
                foreign_column=row[6],
            ))

        if current_table is not None:
            tables.append(TableInfo(name=current_table, columns=current_columns))

        for table in tables:
            await self._enrich_table_info(db, table)

        return DatabaseSchema(tables=tables)

    async def _enrich_table_info(self, db: AsyncSession, table: TableInfo):
        """Enrich table with row count and sample values."""
        try:
            count_result = await db.execute(text(f'SELECT COUNT(*) FROM "{table.name}"'))
            table.row_count = count_result.scalar() or 0

            for col in table.columns:
                if col.data_type in ('character varying', 'text', 'varchar'):
                    try:
                        sample_query = f'''
                            SELECT DISTINCT "{col.name}"
                            FROM "{table.name}"
                            WHERE "{col.name}" IS NOT NULL
                            LIMIT 20
                        '''
                        sample_result = await db.execute(text(sample_query))
                        col.sample_values = [str(r[0]) for r in sample_result.fetchall()]
                    except Exception:
                        pass
        except Exception as e:
            logger.warning(f"Error enriching table {table.name}: {e}")

    def get_schema_prompt(self, schema: DatabaseSchema) -> str:
        """Generate schema description for Gemini prompt."""
        lines = []

        for table in schema.tables:
            lines.append(f"\nTabla: {table.name} ({table.row_count:,} registros)")
            lines.append("-" * 50)

            for col in table.columns:
                type_info = col.data_type
                if col.is_primary_key:
                    type_info += ", PK"
                if col.is_foreign_key:
                    type_info += f", FK → {col.foreign_table}.{col.foreign_column}"
                if not col.is_nullable:
                    type_info += ", NOT NULL"

                line = f"  - {col.name} ({type_info})"

                if col.sample_values:
                    examples = col.sample_values[:5]
                    line += f" - valores: {', '.join(repr(v) for v in examples)}"

                lines.append(line)

        lines.append("\nRelaciones detectadas:")
        for table in schema.tables:
            for col in table.columns:
                if col.is_foreign_key:
                    lines.append(f"  - {table.name}.{col.name} → {col.foreign_table}.{col.foreign_column}")

        return "\n".join(lines)

    def clear_cache(self):
        """Clear the schema cache."""
        self._cache.clear()
```
