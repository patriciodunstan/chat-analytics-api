"""NL2SQL module for natural language database queries."""
from app.chat.nl2sql.detector import QueryDetector
from app.chat.nl2sql.schema_discovery import SchemaDiscovery
from app.chat.nl2sql.intent_parser import IntentParser
from app.chat.nl2sql.sql_generator import SQLGenerator
from app.chat.nl2sql.query_executor import QueryExecutor
from app.chat.nl2sql.schemas import (
    DatabaseSchema,
    TableInfo,
    ColumnInfo,
    ParsedIntent,
    SQLQuery,
    QueryResult,
    NL2SQLResponse,
)

__all__ = [
    "QueryDetector",
    "SchemaDiscovery",
    "IntentParser",
    "SQLGenerator",
    "QueryExecutor",
    "DatabaseSchema",
    "TableInfo",
    "ColumnInfo",
    "ParsedIntent",
    "SQLQuery",
    "QueryResult",
    "NL2SQLResponse",
]