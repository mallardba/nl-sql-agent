"""
Enumerations for the SQL Agent System

Defines standardized enums for various system states and sources.
"""

from enum import Enum


class SQLSource(Enum):
    """Enumeration for SQL query sources."""

    AI = "ai"
    HEURISTIC = "heuristic"
    HEURISTIC_FALLBACK = "heuristic_fallback"
    CACHE = "cache"
    ERROR = "error"


class QueryCategory(Enum):
    """Enumeration for query categories."""

    ANALYTICS = "analytics"
    REPORTING = "reporting"
    EXPLORATION = "exploration"
    REVENUE = "revenue"
    CUSTOMER = "customer"
    PRODUCT = "product"
    TIME_SERIES = "time_series"
    UNKNOWN = "unknown"


class ChartType(Enum):
    """Enumeration for chart types."""

    BAR = "bar"
    LINE = "line"
    PIE = "pie"
    SCATTER = "scatter"
    AREA = "area"


class ErrorType(Enum):
    """Enumeration for error types."""

    AI_GENERATION_EXCEPTION = "ai_generation_exception"
    SQL_EXECUTION_ERROR = "sql_execution_error"
    COMPLETE_FAILURE = "complete_failure"
    VALIDATION_ERROR = "validation_error"
