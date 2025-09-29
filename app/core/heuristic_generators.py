import re


def _generate_revenue_query(q: str) -> str:
    """Generate revenue-based queries."""
    n = _months_from_question(q, default=3)
    limit = _extract_limit(q, default=10)

    return (
        "SELECT p.name AS product, "
        "CAST(SUM(oi.qty * oi.unit_price * (1 - oi.discount_pct/100)) AS DECIMAL(10,2)) AS revenue "
        "FROM order_items oi "
        "JOIN products p ON p.id = oi.product_id "
        "JOIN orders o ON o.id = oi.order_id "
        "WHERE o.status <> 'CANCELLED' AND "
        f"o.order_date >= DATE_SUB(CURDATE(), INTERVAL {n} MONTH) "
        "GROUP BY p.name ORDER BY revenue DESC LIMIT {limit};"
    ).format(limit=limit)


def _generate_monthly_sales_query(q: str) -> str:
    """Generate monthly sales queries."""
    n = _months_from_question(q, default=6)

    return (
        "SELECT DATE_FORMAT(o.order_date, '%Y-%m') AS month, "
        "CAST(SUM(oi.qty * oi.unit_price * (1 - oi.discount_pct/100)) AS DECIMAL(10,2)) AS total_sales "
        "FROM orders o "
        "JOIN order_items oi ON oi.order_id = o.id "
        "WHERE o.status <> 'CANCELLED' AND "
        f"o.order_date >= DATE_SUB(CURDATE(), INTERVAL {n} MONTH) "
        "GROUP BY month ORDER BY month;"
    )


def _generate_quarterly_sales_query(q: str) -> str:
    """Generate quarterly sales queries."""
    n = _months_from_question(q, default=12)  # Default to 12 months for quarterly data

    return (
        "SELECT CONCAT(YEAR(o.order_date), '-Q', QUARTER(o.order_date)) AS quarter, "
        "CAST(SUM(oi.qty * oi.unit_price * (1 - oi.discount_pct/100)) AS DECIMAL(10,2)) AS total_sales "
        "FROM orders o "
        "JOIN order_items oi ON oi.order_id = o.id "
        "WHERE o.status <> 'CANCELLED' AND "
        f"o.order_date >= DATE_SUB(CURDATE(), INTERVAL {n} MONTH) "
        "GROUP BY YEAR(o.order_date), QUARTER(o.order_date) "
        "ORDER BY YEAR(o.order_date), QUARTER(o.order_date);"
    )


def _generate_customer_query(q: str) -> str:
    """Generate customer-based queries."""
    limit = _extract_limit(q, default=10)

    return (
        "SELECT c.name AS customer, "
        "CAST(SUM(oi.qty * oi.unit_price * (1 - oi.discount_pct/100)) AS DECIMAL(10,2)) AS total_value, "
        "COUNT(DISTINCT o.id) AS order_count "
        "FROM customers c "
        "JOIN orders o ON o.customer_id = c.id "
        "JOIN order_items oi ON oi.order_id = o.id "
        "WHERE o.status <> 'CANCELLED' "
        "GROUP BY c.id, c.name "
        "ORDER BY total_value DESC LIMIT {limit};"
    ).format(limit=limit)


def _generate_new_customer_query(q: str) -> str:
    """Generate new customer queries."""
    n = _months_from_question(q, default=1)

    return (
        "SELECT c.name AS customer, c.email, o.order_date AS first_order "
        "FROM customers c "
        "JOIN orders o ON o.customer_id = c.id "
        f"WHERE o.order_date >= DATE_SUB(CURDATE(), INTERVAL {n} MONTH) "
        "GROUP BY c.id, c.name, c.email "
        "ORDER BY first_order DESC;"
    )


def _generate_inventory_query(q: str) -> str:
    """Generate inventory-related queries."""
    return (
        "SELECT p.name AS product, p.stock_quantity, c.name AS category "
        "FROM products p "
        "JOIN categories c ON c.id = p.category_id "
        "WHERE p.stock_quantity < 50 "
        "ORDER BY p.stock_quantity ASC;"
    )


def _generate_category_query(q: str) -> str:
    """Generate category-based queries."""
    return (
        "SELECT c.name AS category, "
        "COUNT(p.id) AS product_count, "
        "CAST(AVG(p.price) AS DECIMAL(10,2)) AS avg_price "
        "FROM categories c "
        "LEFT JOIN products p ON p.category_id = c.id "
        "GROUP BY c.id, c.name "
        "ORDER BY product_count DESC;"
    )


def _generate_order_status_query(q: str) -> str:
    """Generate order status queries."""
    return (
        "SELECT status, COUNT(*) AS order_count, "
        "CAST(AVG(total_amount) AS DECIMAL(10,2)) AS avg_amount "
        "FROM orders "
        "GROUP BY status "
        "ORDER BY order_count DESC;"
    )


def _generate_recent_orders_query(q: str) -> str:
    """Generate recent orders queries."""
    limit = _extract_limit(q, default=10)

    return (
        "SELECT o.id, c.name AS customer, o.order_date, o.status, "
        "CAST(o.total_amount AS DECIMAL(10,2)) AS total_amount "
        "FROM orders o "
        "JOIN customers c ON c.id = o.customer_id "
        "ORDER BY o.order_date DESC LIMIT {limit};"
    ).format(limit=limit)


def _extract_limit(q: str, default: int = 10) -> int:
    """Extract limit number from question."""

    # Look for patterns like "top 5", "best 10", "first 3"
    patterns = [
        r"top\s+(\d+)",
        r"best\s+(\d+)",
        r"first\s+(\d+)",
        r"last\s+(\d+)",
        r"(\d+)\s+products?",
        r"(\d+)\s+customers?",
    ]

    for pattern in patterns:
        match = re.search(pattern, q)
        if match:
            return int(match.group(1))

    return default


def _months_from_question(q: str, default=3):
    """Extract number of months from question text."""
    if not q or not isinstance(q, str):
        return default

    q_lower = q.lower()

    # Handle specific time periods
    if "last year" in q_lower or "past year" in q_lower:
        return 12
    elif "last quarter" in q_lower or "past quarter" in q_lower:
        return 3
    elif "last month" in q_lower or "past month" in q_lower:
        return 1
    elif "last 6 months" in q_lower or "past 6 months" in q_lower:
        return 6

    # Handle "last X months" pattern
    m = re.search(r"\blast\s+(\d{1,2})\s+months?\b", q_lower)
    n = int(m.group(1)) if m else default
    return max(1, min(n, 24))  # clamp 1..24
