from datetime import datetime
from typing import Optional, Any
from pydantic import BaseModel, Field


class ColumnInfo(BaseModel):
    name: str
    data_type: str
    is_nullable: bool = True
    is_primary_key: bool = False
    is_foreign_key: bool = False
    foreign_table: Optional[str] = None
    foreign_column: Optional[str] = None
    sample_values: list[str] = Field(default_factory=list)


class TableInfo(BaseModel):
    name: str
    columns: list[ColumnInfo] = Field(default_factory=list)
    row_count: int = 0
    description: Optional[str] = None


class DatabaseSchema(BaseModel):
    tables: list[TableInfo] = Field(default_factory=list)
    discovered_at: datetime = Field(default_factory=datetime.utcnow)

    def get_table(self, name: str) -> Optional[TableInfo]:
        for table in self.tables:
            if table.name == name:
                return table
        return None
    
    def get_table_names(self) -> list[str]:
        return [table.name for table in self.tables]
    

class DateRange(BaseModel):
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    period_description: str = ""

class ParsedIntent(BaseModel):
    tables: list[str] = Field(default_factory=list)
    select_columns: list[str] = Field(default_factory=list)
    aggregations: list[dict] = Field(default_factory=list)
    filters: list[dict] = Field(default_factory=list)
    joins: list[dict] = Field(default_factory=list)
    group_by: list[str] = Field(default_factory=list)
    order_by: list[dict] = Field(default_factory=list)
    limit : Optional[int] = None
    date_range: Optional[DateRange] = None
    confidence: float = 0.0
    reasoning: str = ""
    original_message: str = ""


class SQLQuery(BaseModel):
    sql: str
    parameters: dict[str, Any] = Field(default_factory=dict)
    description: str = ""
    tables_used: list[str] = Field(default_factory=list)

class QueryResult(BaseModel):
    success: bool
    data: list[dict[str, Any]] = Field(default_factory=list)
    row_count: int = 0
    column_names: list[str] = Field(default_factory=list)
    execution_time_ms: float = 0.0
    error_message: Optional[str] = None

class NL2SQLResponse(BaseModel):
    is_data_query: bool = False
    intent: Optional[ParsedIntent] = None
    sql_query: Optional[SQLQuery] = None
    result: Optional[QueryResult] = None
    natural_response: str = ""
    used_nl2sql: bool = False


