# 02 - Schemas y Exceptions

## Archivo: `app/chat/nl2sql/exceptions.py`

```python
"""Custom exceptions for NL2SQL module."""


class NL2SQLError(Exception):
    """Base exception for NL2SQL errors."""
    pass


class SchemaDiscoveryError(NL2SQLError):
    """Error during schema discovery."""
    pass


class QueryDetectionError(NL2SQLError):
    """Error during query detection."""
    pass


class IntentParsingError(NL2SQLError):
    """Error parsing user intent."""
    pass


class SQLGenerationError(NL2SQLError):
    """Error generating SQL query."""
    pass


class QueryExecutionError(NL2SQLError):
    """Error executing database query."""
    pass


class UnsupportedQueryError(NL2SQLError):
    """Query type not supported."""
    pass
```

---

## Archivo: `app/chat/nl2sql/schemas.py`

```python
"""Pydantic schemas for NL2SQL module."""
from datetime import datetime
from typing import Optional, Any
from pydantic import BaseModel, Field


class ColumnInfo(BaseModel):
    """Information about a database column."""
    name: str
    data_type: str
    is_nullable: bool = True
    is_primary_key: bool = False
    is_foreign_key: bool = False
    foreign_table: Optional[str] = None
    foreign_column: Optional[str] = None
    sample_values: list[str] = Field(default_factory=list)


class TableInfo(BaseModel):
    """Information about a database table."""
    name: str
    columns: list[ColumnInfo] = Field(default_factory=list)
    row_count: int = 0
    description: Optional[str] = None


class DatabaseSchema(BaseModel):
    """Complete database schema information."""
    tables: list[TableInfo] = Field(default_factory=list)
    discovered_at: datetime = Field(default_factory=datetime.utcnow)

    def get_table(self, name: str) -> Optional[TableInfo]:
        """Get table by name (case-insensitive)."""
        for table in self.tables:
            if table.name.lower() == name.lower():
                return table
        return None

    def get_table_names(self) -> list[str]:
        """Get list of all table names."""
        return [t.name for t in self.tables]


class DateRange(BaseModel):
    """Parsed date range from user query."""
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    period_description: str = ""


class ParsedIntent(BaseModel):
    """Parsed intent from natural language query."""
    tables: list[str] = Field(default_factory=list)
    select_columns: list[str] = Field(default_factory=list)
    aggregations: list[dict] = Field(default_factory=list)
    filters: list[dict] = Field(default_factory=list)
    joins: list[dict] = Field(default_factory=list)
    group_by: list[str] = Field(default_factory=list)
    order_by: list[dict] = Field(default_factory=list)
    limit: Optional[int] = None
    date_range: Optional[DateRange] = None
    confidence: float = 0.0
    reasoning: str = ""
    original_message: str = ""


class SQLQuery(BaseModel):
    """Generated SQL query with parameters."""
    sql: str
    parameters: dict[str, Any] = Field(default_factory=dict)
    description: str = ""
    tables_used: list[str] = Field(default_factory=list)


class QueryResult(BaseModel):
    """Result from query execution."""
    success: bool
    data: list[dict[str, Any]] = Field(default_factory=list)
    row_count: int = 0
    column_names: list[str] = Field(default_factory=list)
    execution_time_ms: float = 0.0
    error_message: Optional[str] = None


class NL2SQLResponse(BaseModel):
    """Complete NL2SQL processing response."""
    is_data_query: bool = False
    intent: Optional[ParsedIntent] = None
    sql_query: Optional[SQLQuery] = None
    result: Optional[QueryResult] = None
    natural_response: str = ""
    used_nl2sql: bool = False
```
