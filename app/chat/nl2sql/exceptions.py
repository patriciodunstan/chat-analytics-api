class NL2QLError(Exception):
    """Base exception for NL2QL errors."""
    pass

class SchemaDiscoveryError(NL2QLError):
    """Exception raised for errors in schema discovery."""
    pass

class QueryDetectionError(NL2QLError):
    """Exception raised for errors in query detection."""
    pass

class IntentParsingError(NL2QLError):
    """Error parsing user intent."""
    pass

class SQLGenerationError(NL2QLError):
    """Exception raised for errors in SQL generation."""
    pass

class QueryExecutionError(NL2QLError):
    """Exception raised for errors in query execution."""
    pass

class UnsupportedDatabaseError(NL2QLError):
    """Exception raised for unsupported database types."""
    pass

