"""
SQL Correction Patterns

Centralized configuration for SQL error correction patterns and rules.
This serves as the single source of truth for SQL correction logic.
"""

# Common ambiguous columns that appear in multiple tables
COMMON_AMBIGUOUS_COLUMNS = ["id", "name", "created_at", "updated_at"]

# SQL aggregate functions
AGGREGATE_FUNCTIONS = ["SUM(", "COUNT(", "AVG(", "MAX(", "MIN("]

# Learned error correction patterns
# This is where we would apply patterns learned from previous errors
# Note: These patterns are currently disabled as they were too broad
# and were matching valid SQL queries unnecessarily
LEARNED_PATTERNS = [
    # TODO: Add more specific patterns based on actual error analysis
    # Example pattern structure:
    # {
    #     "pattern": r"regex_pattern",
    #     "replacement": "replacement_string",
    #     "description": "Description of the fix"
    # }
]

# SQL syntax patterns for detection and correction
SQL_PATTERNS = {
    "cast_syntax": r"CAST\(([^)]+)\)\s*AS\s+(\w+)(?=\s+FROM|\s+ORDER|\s+GROUP|\s+WHERE|\s*$)",
    "from_table": r"FROM\s+(\w+)(?:\s+(\w+))?",
    "join_table": r"JOIN\s+(\w+)(?:\s+(\w+))?",
    "join_on": r"JOIN\s+\w+\s+ON\s+(\w+\.\w+\s*=\s*\w+\.\w+)",
    "select_clause": r"SELECT\s+(.*?)\s+FROM",
    "join_id_reference": r"COUNT\(JOIN\.id\)",
    "join_reference": r"JOIN\.(\w+)",
    "bare_column": r"(?<!\w\.)\b{column}\b(?!\s*\.)",
}

# SQL correction thresholds and limits
SQL_THRESHOLDS = {"max_table_alias_length": 2, "preferred_fallback_table": "orders"}
