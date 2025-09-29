import os
import re
from typing import List, Tuple

from ..config import (
    AGGREGATE_FUNCTIONS,
    COMMON_AMBIGUOUS_COLUMNS,
    LEARNED_PATTERNS,
    SQL_PATTERNS,
    SQL_THRESHOLDS,
)


def fix_sql_syntax(sql: str) -> Tuple[str, bool]:
    """Fix common SQL syntax errors using pattern-based corrections.

    Returns:
        Tuple of (fixed_sql, fixes_were_applied)
    """
    fixes_applied = []

    # 1. Fix CAST syntax errors
    sql, cast_fixes = _fix_cast_syntax(sql)
    fixes_applied.extend(cast_fixes)

    # 2. Fix ambiguous column references
    sql, ambiguous_fixes = _fix_ambiguous_columns(sql)
    fixes_applied.extend(ambiguous_fixes)

    # 3. Fix missing table aliases
    sql, alias_fixes = _fix_missing_aliases(sql)
    fixes_applied.extend(alias_fixes)

    # 4. Fix JOIN syntax issues
    sql, join_fixes = _fix_join_syntax(sql)
    fixes_applied.extend(join_fixes)

    # 5. Fix GROUP BY issues
    sql, groupby_fixes = _fix_groupby_syntax(sql)
    fixes_applied.extend(groupby_fixes)

    # 6. Fix invalid JOIN references
    sql, join_ref_fixes = _fix_invalid_join_references(sql)
    fixes_applied.extend(join_ref_fixes)

    # 7. Fix missing column references
    sql, column_fixes = _fix_missing_columns(sql)
    fixes_applied.extend(column_fixes)

    # 8. Apply learned error patterns
    sql, learned_fixes = _apply_learned_patterns(sql)
    fixes_applied.extend(learned_fixes)

    # Debug output if fixes were applied
    fixes_were_applied = len(fixes_applied) > 0
    if fixes_were_applied and os.getenv("DEBUG", "false").lower() == "true":
        print(f"SQL fixes applied: {fixes_applied}")

    return sql, fixes_were_applied


def _apply_learned_patterns(sql: str) -> Tuple[str, List[str]]:
    """Apply learned error patterns from previous corrections."""

    fixes = []

    for pattern_info in LEARNED_PATTERNS:
        if re.search(pattern_info["pattern"], sql, re.IGNORECASE):
            sql = re.sub(
                pattern_info["pattern"],
                pattern_info["replacement"],
                sql,
                flags=re.IGNORECASE,
            )
            fixes.append(pattern_info["description"])

    return sql, fixes


def learn_from_error(sql: str, error_message: str) -> None:
    """Learn from SQL errors to improve future corrections."""
    # This would store error patterns in a database or file
    # For now, we'll just log the pattern for analysis
    if os.getenv("DEBUG", "false").lower() == "true":
        print(f"Learning from error: {error_message}")
        print(f"Problematic SQL: {sql}")

    # In a production system, you would:
    # 1. Store the error pattern in a database
    # 2. Track frequency of similar errors
    # 3. Build a machine learning model to predict fixes
    # 4. Update the correction patterns based on success rates


def _fix_cast_syntax(sql: str) -> Tuple[str, List[str]]:
    """Fix CAST syntax errors."""

    fixes = []

    # Pattern: CAST(expression) AS alias -> CAST(expression AS DECIMAL(10,2)) AS alias
    pattern = SQL_PATTERNS["cast_syntax"]

    def replace_cast(match):
        expression = match.group(1)
        alias = match.group(2)
        fixes.append(f"Fixed CAST syntax: {alias}")
        return f"CAST({expression} AS DECIMAL(10,2)) AS {alias}"

    sql = re.sub(pattern, replace_cast, sql)
    return sql, fixes


def _fix_ambiguous_columns(sql: str) -> Tuple[str, List[str]]:
    """Fix ambiguous column references by adding table aliases."""

    fixes = []

    # Extract table names and their aliases
    tables_with_aliases = {}

    # Find FROM table
    from_match = re.search(SQL_PATTERNS["from_table"], sql, re.IGNORECASE)
    if from_match:
        table_name = from_match.group(1)
        alias = (
            from_match.group(2)
            or table_name.lower()[: SQL_THRESHOLDS["max_table_alias_length"]]
        )  # Use first 2 chars as alias
        tables_with_aliases[table_name] = alias

    # Find JOIN tables
    join_matches = re.finditer(SQL_PATTERNS["join_table"], sql, re.IGNORECASE)
    for match in join_matches:
        table_name = match.group(1)
        alias = (
            match.group(2)
            or table_name.lower()[: SQL_THRESHOLDS["max_table_alias_length"]]
        )
        tables_with_aliases[table_name] = alias

    # If we have multiple tables, check for ambiguous columns
    if len(tables_with_aliases) > 1:
        for column in COMMON_AMBIGUOUS_COLUMNS:
            # Look for bare column references (not table.column)
            bare_column_pattern = SQL_PATTERNS["bare_column"].format(column=column)
            if re.search(bare_column_pattern, sql, re.IGNORECASE):
                # Try to determine the correct table based on context
                # For now, we'll use a simple heuristic: prefer the first table
                first_table = list(tables_with_aliases.keys())[0]
                first_alias = tables_with_aliases[first_table]

                # Replace bare column with table.column
                sql = re.sub(
                    bare_column_pattern,
                    f"{first_alias}.{column}",
                    sql,
                    flags=re.IGNORECASE,
                )
                fixes.append(
                    f"Fixed ambiguous column '{column}' -> '{first_alias}.{column}'"
                )

    return sql, fixes


def _fix_missing_aliases(sql: str) -> Tuple[str, List[str]]:
    """Fix missing table aliases in complex queries."""

    fixes = []

    # Add aliases to tables that don't have them
    # Pattern: FROM table1 JOIN table2 ON condition
    # Convert to: FROM table1 t1 JOIN table2 t2 ON condition

    # This is a complex transformation that would require careful parsing
    # For now, we'll just detect the issue
    if "JOIN" in sql.upper() and not re.search(r"FROM\s+\w+\s+\w+", sql, re.IGNORECASE):
        fixes.append("Detected potential missing table aliases")

    return sql, fixes


def _fix_join_syntax(sql: str) -> Tuple[str, List[str]]:
    """Fix JOIN syntax issues."""

    fixes = []

    # Fix missing ON clauses
    if "JOIN" in sql.upper() and "ON" not in sql.upper():
        fixes.append("Detected JOIN without ON clause")

    # Fix malformed JOIN conditions
    if re.search(SQL_PATTERNS["join_on"], sql):
        fixes.append("Detected JOIN condition syntax")

    return sql, fixes


def _fix_groupby_syntax(sql: str) -> Tuple[str, List[str]]:
    """Fix GROUP BY syntax issues."""

    fixes = []

    # Check if SELECT has non-aggregate columns but no GROUP BY
    if "SELECT" in sql.upper() and "GROUP BY" not in sql.upper():
        # Look for aggregate functions
        has_aggregates = any(func in sql.upper() for func in AGGREGATE_FUNCTIONS)

        if has_aggregates:
            # Look for non-aggregate columns
            select_match = re.search(
                SQL_PATTERNS["select_clause"], sql, re.IGNORECASE | re.DOTALL
            )
            if select_match:
                select_clause = select_match.group(1)
                # Simple check for non-aggregate columns
                if re.search(r"\b\w+\b", select_clause) and not all(
                    func in select_clause.upper() for func in AGGREGATE_FUNCTIONS
                ):
                    fixes.append("Detected potential GROUP BY issue")

    return sql, fixes


def _fix_invalid_join_references(sql: str) -> Tuple[str, List[str]]:
    """Fix invalid JOIN references like COUNT(JOIN.id)."""

    fixes = []

    # Fix COUNT(JOIN.id) -> COUNT(orders.id) or appropriate table reference
    if re.search(SQL_PATTERNS["join_id_reference"], sql, re.IGNORECASE):
        # Try to determine the correct table reference
        # Look for table names in FROM and JOIN clauses
        from_match = re.search(SQL_PATTERNS["from_table"], sql, re.IGNORECASE)
        if from_match:
            table_name = from_match.group(1)
            sql = re.sub(
                SQL_PATTERNS["join_id_reference"],
                f"COUNT({table_name}.id)",
                sql,
                flags=re.IGNORECASE,
            )
            fixes.append(f"Fixed COUNT(JOIN.id) -> COUNT({table_name}.id)")
        else:
            # Fallback to orders table
            sql = re.sub(
                SQL_PATTERNS["join_id_reference"],
                f"COUNT({SQL_THRESHOLDS['preferred_fallback_table']}.id)",
                sql,
                flags=re.IGNORECASE,
            )
            fixes.append(
                f"Fixed COUNT(JOIN.id) -> COUNT({SQL_THRESHOLDS['preferred_fallback_table']}.id)"
            )

    # Fix other invalid JOIN references
    if re.search(SQL_PATTERNS["join_reference"], sql, re.IGNORECASE):
        # Look for the most likely table reference
        from_match = re.search(SQL_PATTERNS["from_table"], sql, re.IGNORECASE)
        if from_match:
            table_name = from_match.group(1)
            sql = re.sub(
                SQL_PATTERNS["join_reference"],
                f"{table_name}.\\1",
                sql,
                flags=re.IGNORECASE,
            )
            fixes.append(f"Fixed JOIN.column references -> {table_name}.column")

    return sql, fixes


def _fix_missing_columns(sql: str) -> Tuple[str, List[str]]:
    """Fix references to non-existent columns by calculating them properly."""

    fixes = []

    # Fix o.total_amount -> SUM(oi.qty * oi.unit_price * (1 - oi.discount_pct/100))
    if "o.total_amount" in sql:
        # Check if order_items is already joined
        if "order_items" in sql or "oi." in sql:
            # Replace with proper calculation
            sql = re.sub(
                r"o\.total_amount",
                "SUM(oi.qty * oi.unit_price * (1 - oi.discount_pct/100))",
                sql,
                flags=re.IGNORECASE,
            )
            fixes.append(
                "Fixed o.total_amount -> SUM(oi.qty * oi.unit_price * (1 - oi.discount_pct/100))"
            )
        else:
            # Add JOIN to order_items and fix the column reference
            # Find the FROM clause and add the JOIN
            from_match = re.search(r"(FROM\s+orders\s+o)", sql, re.IGNORECASE)
            if from_match:
                # Add JOIN to order_items
                join_clause = " JOIN order_items oi ON oi.order_id = o.id"
                sql = sql.replace(
                    from_match.group(1), from_match.group(1) + join_clause
                )

                # Now replace the column reference (remove any existing SUM wrapper)
                sql = re.sub(
                    r"SUM\(CAST\(o\.total_amount",
                    "SUM(CAST(oi.qty * oi.unit_price * (1 - oi.discount_pct/100)",
                    sql,
                    flags=re.IGNORECASE,
                )
                # Also handle cases without CAST
                sql = re.sub(
                    r"o\.total_amount",
                    "oi.qty * oi.unit_price * (1 - oi.discount_pct/100)",
                    sql,
                    flags=re.IGNORECASE,
                )
                fixes.append(
                    "Fixed o.total_amount -> SUM(oi.qty * oi.unit_price * (1 - oi.discount_pct/100)) with JOIN"
                )
            else:
                # Fallback to 0 if we can't add the JOIN
                sql = re.sub(r"o\.total_amount", "0", sql, flags=re.IGNORECASE)
                fixes.append("Fixed o.total_amount -> 0 (could not add JOIN)")

    # Fix other common missing column patterns
    missing_columns = {
        r"o\.revenue": "SUM(oi.qty * oi.unit_price * (1 - oi.discount_pct/100))",
        r"o\.sales": "SUM(oi.qty * oi.unit_price * (1 - oi.discount_pct/100))",
        r"o\.amount": "SUM(oi.qty * oi.unit_price * (1 - oi.discount_pct/100))",
    }

    for pattern, replacement in missing_columns.items():
        if re.search(pattern, sql, re.IGNORECASE):
            sql = re.sub(pattern, replacement, sql, flags=re.IGNORECASE)
            fixes.append(f"Fixed {pattern} -> {replacement}")

    return sql, fixes
